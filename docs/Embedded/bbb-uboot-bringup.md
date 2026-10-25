# BeagleBone Black bring-up 練習：從 UART 到手動 bootz

用 BeagleBone Black（AM335x）練 bring-up 的第一天紀錄：接 debug UART、錄完整開機 log、在 U-Boot 裡直接戳 GPIO 暫存器點 LED，最後不靠 `bootcmd`，自己一步步把 Linux 開起來。

## 接線

- Debug UART 在板子上的 6-pin **J1**：pin 1 GND、pin 4 RX（BBB 收）、pin 5 TX（BBB 送），接 3.3V 的 USB-TTL（我用 CP2102）。VCC 不接，TX/RX 交叉。
- 參數 115200 8N1，不開 flow control。
- 板子 mini-USB 另外會出一個 `/dev/ttyACM0`，那是 Linux 起來後才有的 USB gadget serial，**看不到 ROM/SPL/U-Boot**，bring-up 一定要用 J1。

| 裝置 | USB ID | 用途 |
|---|---|---|
| `/dev/ttyUSB0` | `10c4:ea60` CP2102 | J1 debug UART，開機全程 |
| `/dev/ttyACM0` | `1d6b:0104` BeagleBone gadget | Linux 起來後的 console |

踩到的坑：CP2102 和 BBB 插在同一顆 USB hub 上，BBB 上電瞬間整顆 hub 重新列舉，`ttyUSB0` 掉線約 2 秒，SPL 那段 log 剛好就在這 2 秒內印完而漏錄。錄 log 的程式要能斷線自動重連；想錄到 SPL，UART 轉接器要插主機板直連埠，或 BBB 改用 DC 供電。

## 正常開機長什麼樣

先錄一份原廠完整開機 log 當對照組，之後弄壞東西時才知道哪裡不一樣。

| 階段 | 看到什麼 |
|---|---|
| U-Boot | `U-Boot 2019.04`、`DRAM: 512 MiB`、從 EEPROM 讀到 `board_name=A335BNLT` |
| 找開機設定 | 依序找 `/uEnv.txt`、`/boot.scr`，最後在 SD 的 `/boot/uEnv.txt` 找到，跑 `uname_boot` |
| 載入 | vmlinuz → dtb → initrd，`bootz 0x82000000 0x88080000:size 0x88000000` |
| kernel 早期 | `OF: fdt: Machine model`、`earlycon: omap8250 at MMIO 0x44e09000`（UART0） |
| 儲存 | `mmcblk0` = SD、`mmcblk1` = eMMC |
| rootfs → systemd → login | 約 50 秒到 login |

正常板子也會印的無害訊息：btrfs superblock checksum（U-Boot 在試探檔案系統類型）、`ti-sysc ... error -16`、`l3-aon-clkctrl failed to disable`、`tps65217 Failed to locate of_node`。

## 中斷 autoboot

這塊板子 `bootdelay=0`，`Press SPACE to abort autoboot in 0 seconds` 幾乎沒時間按。解法是上電前就開始每 20ms 送一個空白，看到 `=> ` 才停。U-Boot 在 `bootdelay=0` 時仍會檢查一次 UART 有沒有輸入。

## bdinfo / printenv 看到的東西

- DRAM 在 `0x8000_0000`，大小 `0x2000_0000`（512 MiB）。
- `relocaddr = 0x9ff59000`：U-Boot 會把自己搬到 DRAM 頂端，把低位址讓給 kernel。
- `bootcmd` = `findfdt` → `init_console` → `envboot` → `distro_bootcmd`。
- `findfdt` 用 EEPROM 的 `board_name` / `board_rev` 決定 `fdtfile`，這就是 U-Boot 判斷「這是哪塊板子」的地方。
- 原廠 `boot` 腳本裡穿插 `gpio set 53..56`，那四個 GPIO 就是 USR0–3 LED，拿來當**開機進度條**。

## 用 md/mw 點 USR LED

USR0–3 接在 GPIO1 的 bit 21–24，GPIO1 基底 `0x4804_C000`。

先讀、不寫，確認前置條件：

```text
=> md.l 0x44e000ac 1     # CM_PER_GPIO1_CLKCTRL = 0x2：時脈開著、IDLEST=0
=> md.l 0x44e10854 4     # conf_gpmc_a5..a8 = 0x27：mode 7 (GPIO)、receiver on
=> md.l 0x4804c134 1     # GPIO_OE = 0xffffffff：全部是輸入！
=> md.l 0x4804c13c 1     # GPIO_DATAOUT = 0
```

再寫：

```text
=> mw.l 0x4804c134 0xfe1fffff   # OE 清 bit 21–24 → 輸出
=> mw.l 0x4804c194 0x01e00000   # SETDATAOUT：四顆全亮
=> mw.l 0x4804c190 0x00200000   # CLEARDATAOUT：只關 USR0
```

| 清掉的 bit | DATAOUT 讀回 | LED |
|---|---|---|
| 21 | `0x01c00000` | USR0 |
| 22 | `0x01800000` | USR1 |
| 23 | `0x01000000` | USR2 |
| 24 | `0x00000000` | USR3 |

學到的順序，也是 Linux `gpio-omap` + DTS `pinctrl` / `gpio-leds` 幫你做掉的事：

1. **時脈**：模組沒開 clock，讀寫暫存器會拿到垃圾或直接 data abort。
2. **pinmux**：pin 要切到 GPIO mode，不然接的是別的周邊。
3. **方向**：OE 清 0 才是輸出。「暫存器寫了 LED 不亮」最常見就是忘了這步。
4. **輸出值**：用 SET/CLEARDATAOUT，寫 1 的 bit 才有作用，不用 read-modify-write，也不會和別人搶。

## 手動 load + bootz

```text
=> part list mmc 0     # p1 FAT 36MB、p2 swap、p3 ext4 rootfs
=> ls mmc 0:3 /boot    # kernel / initrd / dtbs / uEnv.txt 都在 rootfs 的 /boot

=> load mmc 0:3 ${loadaddr} /boot/vmlinuz-6.12.45-bone34                  # 0x82000000
=> load mmc 0:3 ${fdtaddr}  /boot/dtbs/6.12.45-bone34/am335x-boneblack.dtb # 0x88000000
=> load mmc 0:3 ${rdaddr}   /boot/initrd.img-6.12.45-bone34                # 0x88080000
=> setenv rdsize ${filesize}    # filesize 每次 load 都會被覆蓋，要馬上存
```

載完先驗 header：

- `md.l ${loadaddr}`：`MZ`（EFI stub）+ 一串 ARM NOP `e1a00000`，offset 0x24 是 zImage magic **`016f2818`**。
- `md.b ${fdtaddr}`：**`d0 0d fe ed`**，FDT magic。
- 檢查三塊不重疊：kernel 8.8MB 到 `0x82876200` < dtb `0x88000000`；dtb 99KB 到 `0x88018493` < initrd `0x88080000`。很多 bring-up 失敗就是 kernel 變大蓋掉了 dtb。

```text
=> fdt addr ${fdtaddr}; fdt print / model    # "TI AM335x BeagleBone Black"
=> setenv bootargs console=ttyS0,115200n8 root=/dev/mmcblk0p3 ro rootfstype=ext4 rootwait earlycon bringup.manual=alan
=> bootz ${loadaddr} ${rdaddr}:${rdsize} ${fdtaddr}
   Loading Ramdisk to 8f5ee000 ...
   Loading Device Tree to 8f5d2000 ...
Starting kernel ...
```

- 在 bootargs 塞一個自己的標記（`bringup.manual=alan`），kernel 的 `Kernel command line:` 印出來就能證明這次是自己的參數，不是 `bootcmd`。
- `bootz` 會把 initrd 和 DTB 再搬到 DRAM 頂端附近，真正交給 kernel 的是新位址（DTB 位址放在 `r2`）。
- 原廠 bootargs 裡的 `fsck.repair=yes`、`lpj=`、`rng_core.default_quality=` 拿掉照樣開得起來，不是必要參數。
- `setenv` 沒有 `saveenv` 就只活在這次開機，重開又回到原廠流程，可以放心亂試。

## 改走 TFTP

把 kernel / dtb / initrd 放到 PC 上的 TFTP root，U-Boot 從網路載，之後換自己 build 的 kernel 就不用再拔 SD 卡。

```text
=> setenv ipaddr 192.168.10.242; setenv serverip 192.168.10.154
=> ping ${serverip}
=> tftp ${loadaddr} zImage                  # 8.8MB, 5.8 MiB/s
=> tftp ${fdtaddr}  am335x-boneblack.dtb
=> tftp ${rdaddr}   initrd.img
=> setenv rdsize ${filesize}
=> setenv bootargs console=ttyS0,115200n8 root=/dev/mmcblk0p3 ro rootfstype=ext4 rootwait earlycon bringup.boot=tftp
=> bootz ${loadaddr} ${rdaddr}:${rdsize} ${fdtaddr}
```

PC 端沒有現成 TFTP server，用系統的 dnsmasq 只開 TFTP（`--port=0` 關掉 DNS、不開 DHCP），並用 `--interface` + `--bind-interfaces` 只綁接板子的那張網卡。

### 踩坑：封包有到，回覆卻從 Tailscale 出去

U-Boot `ping` 失敗、`tftp` 一直印 `T`（timeout）。在 PC 上 `tcpdump -ni enp5s0 host 192.168.10.242` 看得到板子的 ARP、ICMP echo request、TFTP RRQ，但**完全沒有回覆**。

```text
$ ip route get 192.168.10.242
192.168.10.242 dev tailscale0 table 52 src 100.69.80.97
```

tailnet 裡有節點宣告了 `192.168.10.0/24` 的 subnet route，而 Tailscale 的 policy rule（priority 5270，`lookup 52`）排在 main table（32766）前面，所以回給板子的封包全被送進 `tailscale0`。修法是加一條更前面的 rule，讓本地 LAN 走 main table：

```bash
sudo ip rule add to 192.168.10.0/24 lookup main priority 2500
```

教訓：「request 有到、reply 不見」時，先 `ip route get <對方 IP>` 看回程真正走哪張網卡，別先懷疑防火牆或板子。

## 自己 build kernel 走 TFTP 開機

```bash
sudo apt install gcc-arm-linux-gnueabihf
git -C linux worktree add --detach ../bbb-linux v7.3-rc7     # 不動原本的開發分支
cd bbb-linux
M="make ARCH=arm CROSS_COMPILE=arm-linux-gnueabihf- O=../build-arm"
$M omap2plus_defconfig
scripts/config --file ../build-arm/.config --set-str LOCALVERSION "-bringup"
$M olddefconfig
$M -j28 zImage ti/omap/am335x-boneblack.dtb      # 28 核約 2 分鐘
```

- 新版 kernel 的 BBB dts 在 `arch/arm/boot/dts/ti/omap/`，make target 要寫 `ti/omap/am335x-boneblack.dtb`。
- `omap2plus_defconfig` 把 `MMC_OMAP_HS`、`EXT4_FS`、`SERIAL_8250_OMAP`、`TI_CPSW_SWITCHDEV` 都編成 built-in，所以**不帶 initrd** 也能直接掛 SD 上的 rootfs：`bootz ${loadaddr} - ${fdtaddr}`。SD 上的 initrd 和 `/lib/modules` 是 6.12 的，配 7.3 kernel 本來就不能用。
- 開機 log 第一行 `Linux version 7.3.0-rc7-bringup (alanhc@alanhc-14700)` 證明跑的是自己編的。

和原廠 6.12 + initrd 比：

| | 原廠 6.12 + initrd | 自編 7.3，無 initrd |
|---|---|---|
| rootfs 掛上 | 12.6 s | 4.5 s |
| 到 login | 約 56 s | 約 45 s |
| 網路 | eth0 拿到 IP | **沒 IP** |

預期中的失敗：`Failed to find module 'autofs4'`、`bb-usb-gadgets.service` 失敗（沒有 libcomposite 等 module）、`iwd.service` 失敗。都是 rootfs 裡沒有 7.3 的 modules。

不在預期內的：網路沒起來。log 裡有一行

```text
cpsw-switch 4a100000.switch end0: renamed from eth0
```

原廠 bootargs 有 `net.ifnames=0`，我手動精簡 bootargs 時拿掉了，systemd 就把網卡改名成 `end0`，而 rootfs 的網路設定寫的是 `eth0`，於是拿不到 IP。之前用原廠 kernel 手動 bootz 沒發現，是因為那時沒人去看網路有沒有起來。教訓：**刪 bootargs 參數前先確認它在管什麼**，「開得到 login」不代表沒壞東西。

補回 `net.ifnames=0` 再開一次，自編 7.3 kernel 的 log 出現 `cpsw-switch 4a100000.switch eth0: Link is Up - 100Mbps/Full`，開到 login 後 1 秒內 ping 得到。回頭翻 log 才發現，稍早用原廠 6.12 走 TFTP 開機那幾次也有 `end0: renamed from eth0`，網路其實一樣是壞的，只是當時沒去檢查。

最後 SSH 進板子確認：`uname -r` 是 `7.3.0-rc7-bringup`，`/proc/cmdline` 是自己設的那串，`eth0` 拿到 `192.168.10.242`，`systemctl --failed` 只剩 `bb-usb-gadgets` 和 `iwd`，都是缺 7.3 modules 的預期結果。

## 下一步

- 追原廠 6.12 軟重開卡死：`systemctl reboot` 後停在 `Stopped serial-getty@ttyGS0` 就沒有輸出，網路還活著，可重現。從 `journalctl -b -1` 或 `systemd.log_level=debug` 下手。
- 刻意弄壞：拿掉 dtb、改壞 `console=`、`root=` 指錯，看各自停在哪。
- 按住 S2 開機，驗證目前的 U-Boot 2019.04 是不是來自 eMMC。
