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

dts 放在 kernel 樹外面，就照 kernel 的方式自己跑 `cpp -nostdinc -I <dts 目錄> -I include -undef -D__DTS__ -x assembler-with-cpp`，再丟給 `scripts/dtc/dtc`。

## 第一版：自己的 sysfs 屬性

核心只有幾樣東西：

- `of_match_table` + `MODULE_DEVICE_TABLE(of, ...)`：比對 `compatible`；後者讓 module 帶上 `of:N*T*Cbringup,usr-led` alias，udev 才知道要自動載入它。
- `devm_gpiod_get(dev, "led", GPIOD_OUT_HIGH)`：讀 `led-gpios`、要 GPIO、設成輸出並拉高。名字 `"led"` 對應屬性名的前半。
- `DEVICE_ATTR_RW(on)` + `.dev_groups`：在 `/sys/bus/platform/devices/usr-led/on` 讀寫 0/1，輸入用 `kstrtobool` 檢查。
- `remove`：把燈關掉；GPIO 和記憶體由 `devm_*` 自動釋放。

out-of-tree module 要對著編好的 kernel 樹建：`make -C <kernel> O=<build> M=$PWD modules`。build 目錄裡要有 `Module.symvers`，所以 kernel 那邊至少要跑過一次 `make modules`；`modinfo` 的 `vermagic` 要和板子上跑的 kernel 完全一樣，否則 `insmod` 會拒絕。

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

`rmmod` 後實測：`/sys/class/leds/` 清空、`GPIO1_OE` bit24 回到 1（輸入）、`/sys/kernel/debug/gpio` 裡 gpio-24 的 consumer 消失。

## 踩到的坑

- **`CONFIG_LEDS_GPIO=m`、`CONFIG_LEDS_CLASS=m`**：omap2plus 把 `gpio-leds`、LED class、各個 trigger 都編成 module。rootfs 裡沒有對應版本的 modules 時，USR LED 根本沒有 driver 在管，`trigger` 清單裡也只看得到編進 kernel 的（`cpu`、`mmc0`…）。用 `modinfo ... | grep depends` 看依賴，`insmod` 要照順序：`led-class.ko` → 自己的 driver → `ledtrig-heartbeat.ko`。
- **pinctrl 跟著 device 走**：`user_leds_s0` 掛在 `leds` node 上，要等 `gpio-leds` probe 才會套用。`gpio-leds` 沒載入時，GPIO 還能動只是因為 U-Boot 已經把那幾根腳設成 `0x27`。自己的 node 正確的做法是帶自己的 `pinctrl-0`。
- **燈沒亮時先讀暫存器**：透過 `/dev/mem` 讀 `conf_gpmc_a8`、`GPIO1_OE`、`GPIO1_DATAOUT`、`GPIO1_DATAIN`。`DATAIN` 跟著翻轉就代表電位真的到了 pad 上，問題不在 driver。那次「燈沒亮」其實有兩個原因疊在一起：第一次 serial 線鬆了，根本沒攔到 U-Boot、測試沒跑；第二次閃爍只排了 30 秒，看的時候已經結束了。之後請人看 LED 都讓目標那顆持續閃，用「會閃的那顆」辨認，不靠描述位置。
- **板子上 `/dev/shm` 的檔案在 SSH 登出時會被 systemd-logind（`RemoveIPC`）清掉**，跨 session 要用的檔案放 `/var/tmp`；背景長跑的東西用 `sudo systemd-run`。

## 延伸練習

- 給 `usr-led` node 加上自己的 `pinctrl-0`，讓它不依賴 `gpio-leds`。
- 從 DT 讀 `linux,default-trigger`，填進 `led_classdev.default_trigger`。
- 把 module 裝進 rootfs 的 `/lib/modules/<版本>/` 並 `depmod`，驗證開機時 udev 會依 DT 自動載入它。
