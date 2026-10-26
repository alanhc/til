# 在 BeagleBone Black 上寫一個最小的 platform driver

[U-Boot 練習](./bbb-uboot-bringup.md)裡用 `md`/`mw` 直接戳 GPIO1 暫存器點亮 USR LED。這次把同一件事交給 kernel：寫一個 platform driver，靠 device tree 找到 LED，先用自己的 sysfs 屬性控制，再改成標準的 LED class。

## 整條路長什麼樣

```text
DT 的 usr-led node（compatible = "bringup,usr-led"）
  └→ platform bus 比對 compatible，呼叫 probe()
      └→ devm_gpiod_get(dev, "led", ...)：gpiolib 解析 led-gpios = <&gpio1 24 ...>
          └→ gpio-omap 寫 GPIO1_OE bit24 = 0、DATAOUT bit24 = 1
              └→ pad conf_gpmc_a8 = 0x27（GPIO 模式）
                  └→ USR3 亮
```

U-Boot 那四步（時脈 → pinmux → 方向 → 輸出值），在這裡分別是 PM runtime、pinctrl、gpiolib、gpio-omap 在做。

完整檔案：[`usr_led_sysfs.c`](https://github.com/alanhc/til/blob/main/static/bbb/usr_led_sysfs.c)（第一版）、[`usr_led.c`](https://github.com/alanhc/til/blob/main/static/bbb/usr_led.c)（LED class 版）、[`am335x-boneblack-usrled.dts`](https://github.com/alanhc/til/blob/main/static/bbb/am335x-boneblack-usrled.dts)、[`Makefile`](https://github.com/alanhc/til/blob/main/static/bbb/Makefile)、[`test-on-board.sh`](https://github.com/alanhc/til/blob/main/static/bbb/test-on-board.sh)、讀暫存器用的 [`regs.py`](https://github.com/alanhc/til/blob/main/static/bbb/regs.py)。

先看原本 DT 裡 LED 怎麼寫：

```bash
grep -n "leds" -A40 arch/arm/boot/dts/ti/omap/am335x-bone-common.dtsi    # led2..led5 = gpio1 21..24
grep -n "user_leds_s0" -A6 arch/arm/boot/dts/ti/omap/am335x-bone-common.dtsi
```

## Device tree：把 USR3 從 gpio-leds 讓出來

USR0–3 原本在 `am335x-bone-common.dtsi` 的 `leds` node 底下，由 `gpio-leds` 控制，四根腳的 pinmux（`user_leds_s0`）也掛在 `leds` node 上。另寫一個 dts include 原本的板子，刪掉 `led5`，給自己的 node：

```dts
#include "am335x-boneblack.dts"

/ {
	leds {
		/delete-node/ led5;
	};

	usr-led {
		compatible = "bringup,usr-led";
		led-gpios = <&gpio1 24 GPIO_ACTIVE_HIGH>;
	};
};
```

dts 放在 kernel 樹外面，就照 kernel 的方式自己跑 `cpp -nostdinc -I <dts 目錄> -I include -undef -D__DTS__ -x assembler-with-cpp`，再丟給 `scripts/dtc/dtc`：

```bash
K=~/bbb-bringup/linux
cpp -nostdinc -I $K/arch/arm/boot/dts/ti/omap -I $K/include -undef -D__DTS__ \
    -x assembler-with-cpp am335x-boneblack-usrled.dts -o usrled.tmp
~/bbb-bringup/build-arm/scripts/dtc/dtc -I dts -O dtb -i $K/arch/arm/boot/dts/ti/omap \
    -o am335x-boneblack-usrled.dtb usrled.tmp
# 反編譯回來確認：usr-led 在、led5 不見了
dtc -I dtb -O dts am335x-boneblack-usrled.dtb | grep -nE 'usr-led \{|bringup,usr-led|led-gpios|usr3'
```

dtc 會吐一串 `unit_address_vs_reg`、`simple_bus_reg` 的 warning，那是上游 `am33xx-l4.dtsi` 本來就有的，kernel 自己的 build 會用 `-Wno-...` 關掉。

## 第一版：自己的 sysfs 屬性

核心只有幾樣東西：

- `of_match_table` + `MODULE_DEVICE_TABLE(of, ...)`：比對 `compatible`；後者讓 module 帶上 `of:N*T*Cbringup,usr-led` alias，udev 才知道要自動載入它。
- `devm_gpiod_get(dev, "led", GPIOD_OUT_HIGH)`：讀 `led-gpios`、要 GPIO、設成輸出並拉高。名字 `"led"` 對應屬性名的前半。
- `DEVICE_ATTR_RW(on)` + `.dev_groups`：在 `/sys/bus/platform/devices/usr-led/on` 讀寫 0/1，輸入用 `kstrtobool` 檢查。
- `remove`：把燈關掉；GPIO 和記憶體由 `devm_*` 自動釋放。

out-of-tree module 要對著編好的 kernel 樹建：`make -C <kernel> O=<build> M=$PWD modules`。build 目錄裡要有 `Module.symvers`，所以 kernel 那邊至少要跑過一次 `make modules`；`modinfo` 的 `vermagic` 要和板子上跑的 kernel 完全一樣，否則 `insmod` 會拒絕。

```bash
# kernel 樹要乾淨：之前為了 debug 加的 Makefile hack 會讓版本變成 -dirty，先還原
git -C ~/bbb-bringup/linux checkout arch/arm/boot/compressed/Makefile
cd ~/bbb-bringup/linux
make ARCH=arm CROSS_COMPILE=arm-linux-gnueabihf- O=../build-arm -j28 zImage modules
cat ../build-arm/include/config/kernel.release              # 7.3.0-rc7-bringup
grep -E '^CONFIG_(LEDS_GPIO|LEDS_CLASS)=' ../build-arm/.config   # 兩個都是 =m，後面會用到

cd ~/bbb-bringup/drivers/usr-led && make                    # 編 usr_led.ko 和 dtb
modinfo usr_led.ko | grep -E 'vermagic|alias|depends'
#   vermagic: 7.3.0-rc7-bringup ...      ← 要和板子上的 uname -r 一致
#   alias:    of:N*T*Cbringup,usr-led    ← MODULE_DEVICE_TABLE 產生的
```

上板：用新 dtb TFTP 開機，module 拷到 `/var/tmp`（不是 `/dev/shm`，原因見下面的坑）：

```bash
cp ../../build-arm/arch/arm/boot/zImage ~/bbb-bringup/tftp/zImage-usrled
cp am335x-boneblack-usrled.dtb ~/bbb-bringup/tftp/
touch ~/bbb-bringup/logs/break.flag
KERNEL=zImage-usrled DTB=am335x-boneblack-usrled.dtb INITRD= \
  BOOTARGS='console=ttyS0,115200n8 root=/dev/mmcblk0p3 ro rootfstype=ext4 rootwait earlycon net.ifnames=0' \
  ~/bbb-bringup/tftpboot.sh                          # 然後拔電插回
scp usr_led.ko debian@192.168.10.242:/var/tmp/
```

板子上：

```bash
ls /sys/firmware/devicetree/base/ | grep -E 'usr-led|leds'   # 新 dtb 生效了才看得到 usr-led
sudo insmod /var/tmp/usr_led.ko
dmesg | tail -3        # parsed 'led-gpios' property of node '/usr-led[0]' ... probed, LED on
P=/sys/bus/platform/devices/usr-led
cat $P/on; echo 0 | sudo tee $P/on; echo 1 | sudo tee $P/on
echo maybe | sudo tee $P/on            # kstrtobool 拒絕，值不變
sudo cat /sys/kernel/debug/gpio | grep usr3    # gpio-24 ([usr3 led] | led) out hi
sudo rmmod usr_led; dmesg | tail -1    # removed, LED off
```

## 第二版：改用 LED class

| | sysfs 版 | LED class 版 |
|---|---|---|
| 介面 | 自己的 `.../usr-led/on` | 標準的 `/sys/class/leds/<name>/{brightness,trigger}` |
| 自動閃 | 自己寫迴圈 | 掛 trigger（heartbeat、timer、mmc0…）就會閃 |
| `remove` | 自己關燈 | 不用寫 |
| 取回自己的資料 | `dev_get_drvdata()` | `container_of()` |
| 依賴 | 無 | `led-class.ko` |

幾個重點：

- **把 `struct led_classdev` 直接嵌進自己的結構**。LED core 呼叫 callback 時只給 `led_classdev *`，用 `container_of()` 退回 `struct usr_led` 拿 GPIO。
- **`brightness_set` 還是 `brightness_set_blocking`**：heartbeat trigger 從 timer 呼叫 callback，那時不能睡。SoC 內部的 GPIO 只是寫暫存器，用 `brightness_set` + `gpiod_set_value()`；接在 I2C/SPI expander 上的 GPIO 會睡，要用 `brightness_set_blocking` + `gpiod_set_value_cansleep()`，由 LED core 丟到 workqueue。用 `gpiod_cansleep()` 決定，和 `drivers/leds/leds-gpio.c` 一樣。
- **`max_brightness = 1`**：告訴 LED core 這是只有亮滅的 LED。
- **不用寫 `remove`**：`led_classdev_unregister()` 在沒設 `LED_RETAIN_AT_SHUTDOWN` 時會自己 `led_set_brightness(LED_OFF)`；`devm` 依註冊相反的順序收尾，先 unregister LED 再放掉 GPIO。
- 名字照 `裝置:顏色:功能` 的慣例，可以用 DT 的 `label` 覆寫。

LED class 版的 `modinfo` 會多出 `depends: led-class`，載入順序要照依賴：

```bash
scp usr_led.ko ~/bbb-bringup/build-arm/drivers/leds/led-class.ko \
    ~/bbb-bringup/build-arm/drivers/leds/trigger/ledtrig-heartbeat.ko debian@192.168.10.242:/var/tmp/

# 板子上
sudo rmmod usr_led                       # 先卸下 sysfs 版
sudo insmod /var/tmp/led-class.ko
sudo insmod /var/tmp/usr_led.ko          # registered as bringup:green:usr3
L=/sys/class/leds/bringup:green:usr3
cat $L/max_brightness $L/brightness      # 1 / 0
echo 1 | sudo tee $L/brightness; echo 0 | sudo tee $L/brightness
cat $L/trigger                           # [none] ... cpu cpu0 mmc0 mmc1（沒有 timer、heartbeat：它們是 module）
sudo insmod /var/tmp/ledtrig-heartbeat.ko
echo heartbeat | sudo tee $L/trigger     # 開始心跳
sudo rmmod usr_led
ls /sys/class/leds/                      # 空了
```

`rmmod` 後實測：`/sys/class/leds/` 清空、`GPIO1_OE` bit24 回到 1（輸入）、`/sys/kernel/debug/gpio` 裡 gpio-24 的 consumer 消失。

## 踩到的坑

- **`CONFIG_LEDS_GPIO=m`、`CONFIG_LEDS_CLASS=m`**：omap2plus 把 `gpio-leds`、LED class、各個 trigger 都編成 module。rootfs 裡沒有對應版本的 modules 時，USR LED 根本沒有 driver 在管，`trigger` 清單裡也只看得到編進 kernel 的（`cpu`、`mmc0`…）。用 `modinfo ... | grep depends` 看依賴，`insmod` 要照順序：`led-class.ko` → 自己的 driver → `ledtrig-heartbeat.ko`。
- **pinctrl 跟著 device 走**：`user_leds_s0` 掛在 `leds` node 上，要等 `gpio-leds` probe 才會套用。`gpio-leds` 沒載入時，GPIO 還能動只是因為 U-Boot 已經把那幾根腳設成 `0x27`。自己的 node 正確的做法是帶自己的 `pinctrl-0`。
- **燈沒亮時先讀暫存器**：透過 `/dev/mem` 讀 `conf_gpmc_a8`、`GPIO1_OE`、`GPIO1_DATAOUT`、`GPIO1_DATAIN`（`sudo python3 regs.py`，insmod 前後各讀一次）：

  ```text
                     insmod 前       insmod 後
  conf_gpmc_a8       0x00000027      0x00000027      mode 7 = GPIO
  GPIO1_OE   bit24   1（輸入）        0（輸出）
  GPIO1_DATAOUT bit24 0              1
  GPIO1_DATAIN bit24  0              1               腳位真的被拉高
  ```

  `DATAIN` 跟著翻轉就代表電位真的到了 pad 上，問題不在 driver。那次「燈沒亮」其實有兩個原因疊在一起：第一次 serial 線鬆了，根本沒攔到 U-Boot、測試沒跑；第二次閃爍只排了 30 秒，看的時候已經結束了。之後請人看 LED 都讓目標那顆持續閃，用「會閃的那顆」辨認，不靠描述位置：

  ```bash
  sudo systemd-run --unit=usrled-blink sh -c \
    'for i in $(seq 1 60); do echo 1 > /sys/bus/platform/devices/usr-led/on; sleep 1;
                              echo 0 > /sys/bus/platform/devices/usr-led/on; sleep 1; done'
  ```
- **板子上 `/dev/shm` 的檔案在 SSH 登出時會被 systemd-logind（`RemoveIPC`）清掉**，跨 session 要用的檔案放 `/var/tmp`；背景長跑的東西用 `sudo systemd-run`。

## 延伸練習

- 給 `usr-led` node 加上自己的 `pinctrl-0`，讓它不依賴 `gpio-leds`。
- 從 DT 讀 `linux,default-trigger`，填進 `led_classdev.default_trigger`。
- 把 module 裝進 rootfs 的 `/lib/modules/<版本>/` 並 `depmod`，驗證開機時 udev 會依 DT 自動載入它。
