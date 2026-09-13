# 在自己的筆電上開機 NVIDIA GB200 NVL 的 BMC firmware

## 這篇在做什麼

OpenBMC 的原始碼樹裡有一個 `meta-nvidia` 層，裡面是 NVIDIA 資料中心平台的真實 BMC 設定 ——
包括 GB200 NVL 機櫃。而 QEMU 從 10.1 起內建了 `gb200nvl-bmc` 這個 machine，
是 NVIDIA 自己送進 upstream 的。

也就是說：**你不需要一台價值數百萬的 GB200 機櫃，就能 build 並開機它的 BMC firmware。**

這篇記錄完整流程與三個會卡住的地方。所有輸出都是實際跑出來的。環境：

- Ubuntu 24.04.4,30 GB RAM,32 核
- OpenBMC master(`meta-nvidia` 已在樹內)
- QEMU 11.0.2(自己 build，原因見下)

---

## 一、meta-nvidia 裡有什麼

```bash
cd openbmc
. setup        # 不給參數會列出所有可用 machine
```

清單裡有：

```
gb200nvl-obmc      NVIDIA GB200 NVL 機櫃的 BMC
nvl32-obmc         NVIDIA NVL32
qcom-bmc-ast2600   Qualcomm 的 AST2600 BMC
```

看 `gb200nvl-obmc` 的 machine conf：

```
KMACHINE = "aspeed"
KERNEL_DEVICETREE = "aspeed/aspeed-bmc-nvidia-gb200nvl-bmc.dtb"
UBOOT_MACHINE = "ast2600_openbmc_spl_defconfig"

require conf/machine/include/ast2600.inc
require conf/distro/include/pldm.inc      ← 平台原生就含 PLDM
require conf/machine/include/nvidia.inc

FLASH_UBOOT_OFFSET = "0"
FLASH_KERNEL_OFFSET = "1024"
FLASH_ROFS_OFFSET = "10240"
FLASH_RWFS_OFFSET = "65532"
FLASH_SIZE = "65536"                      ← 64 MB

QB_MACHINE = "-machine gb200nvl-bmc"      ← 直接告訴你 QEMU 怎麼開
```

兩件事值得注意：

**`require conf/distro/include/pldm.inc`** —— PLDM 是平台自帶的，不必自己加
`IMAGE_INSTALL`。而 `pldm.inc` 本身又 require 了 `mctp.inc`，所以 MCTP 也一起進來。

**rootfs 分割是 10240K–65532K，約 55 MB。** 對照一般 32 MB flash 的板子（例如 romulus）
rootfs 只有 23 MB、連 pldm 都塞不下，這裡空間非常寬裕。

---

## 二、坑 1：你的 QEMU 大概沒有這個 machine

```bash
qemu-system-arm -M help | grep -i gb200
# (沒有輸出)
```

`gb200nvl-bmc` 由 NVIDIA 的 `etanous@nvidia.com` 在 2025 年 7 月送進 upstream QEMU 的
`aspeed-next`,model 基於 OpenBMC kernel 樹裡的 `aspeed-bmc-nvidia-gb200nvl-bmc.dts`
—— 跟你 build 出來的 image 用的是同一份 device tree。

**需要 QEMU ≥ 10.1。** QEMU 10.1.0 的發布公告（2025-08-26）ARM 段落寫著：

> ARM: support for new board/machine models 'max78000fthr', 'ast2700fc'，
> 'catalina-bmc', **'gb200-bmc'**, and 'ast2700a0-evb'

**注意命名不一致**：公告與 patch series 用的是 `gb200-bmc`，但實際註冊的 machine 名稱是
`gb200nvl-bmc` —— 照公告的字去 `-M help` 裡找會找不到。

Ubuntu 24.04 給的是 8.2.2，差三個大版本。本文實測的是 11.0.2；
10.1 到 10.x 之間我沒有實際測過。

### 不要急著自己編 QEMU

從原始碼編需要 `libpixman-1-dev` 和 `libslirp-dev`。沒有 pixman 編不出 system emulation，
沒有 slirp 就沒有 user networking(等於沒有 SSH port forward)。這兩個都要 `sudo apt`。

**更省事的做法是讓 Yocto 編。** OpenBMC 樹裡的 oe-core 帶的就是 QEMU 11.0.2，
而且 `meta-phosphor/recipes-devtools/qemu/qemu-system-native_%.bbappend` 的內容只有一行：

```
PACKAGECONFIG:append:df-mctp = " usb-redir"
```

**沒有任何 machine patch** —— 這反過來證明 `gb200nvl-bmc` 確實已經在 upstream。
而 recipe 的 `DEPENDS` 帶 `pixman-native`、`PACKAGECONFIG` 含 `slirp pixman`，
Yocto 會自己把相依全部編出來，**完全不需要 sudo**：

```bash
bash -c '. setup evb-ast2600 >/dev/null 2>&1 && exec bitbake qemu-system-native'
```

---

## 三、坑 2：編出來的 QEMU 執行會失敗（但它沒壞)

```
qemu-system-arm: /lib/x86_64-linux-gnu/libslirp.so.0: version `SLIRP_4.9' not found
```

看起來像 build 壞了。實際上 **binary 和它需要的函式庫不在同一個目錄**：

| | 路徑 |
|---|---|
| binary | `tmp/sysroots-components/x86_64/qemu-system-native/usr/bin/` |
| 函式庫 | `tmp/work/x86_64-linux/qemu-system-native/11.0.2/recipe-sysroot-native/usr/lib/` |

直接執行時 loader 找不到 Yocto 編的 `libslirp.so.0`，退回去載系統那顆舊的，版本對不上。
設好 `LD_LIBRARY_PATH` 就正常了：

```bash
T=~/firmware-p0/openbmc/build/evb-ast2600/tmp
Q=$T/sysroots-components/x86_64/qemu-system-native/usr/bin/qemu-system-arm
LIB=$T/work/x86_64-linux/qemu-system-native/11.0.2/recipe-sysroot-native/usr/lib

LD_LIBRARY_PATH="$LIB" "$Q" -M help | grep -iE 'gb200|ast2600'
```

```
ast2600-evb          Aspeed AST2600 EVB (Cortex-A7)
gb200nvl-bmc         Nvidia GB200NVL BMC (Cortex-A7)
```

有了。

---

## 四、坑 3:30 GB RAM 撐不住預設的平行度

第一次 build 我設 `BB_NUMBER_THREADS = "16"` 配 `PARALLEL_MAKE = "-j 16"`，結果：

```
arm-openbmc-linux-gnueabi-g++: fatal error: Killed signal terminated program cc1plus
```

`Killed signal terminated program cc1plus` 就是 OOM killer 砍掉編譯器。
最壞情況同時 256 個編譯行程，而 `openbmc-phosphor` distro 的 C++20 recipe
(`telemetry`、`phosphor-fan`、`dbus-sensors`)每個 `cc1plus` 吃 1–2 GB。

改成：

```
BB_NUMBER_THREADS = "6"
PARALLEL_MAKE = "-j 6"
BB_PRESSURE_MAX_MEMORY = "5000"
```

`BB_PRESSURE_MAX_MEMORY` 是 Yocto 依 Linux PSI(pressure stall information)自動節流的機制 ——
記憶體吃緊時暫停派發新 task。加上之後，6749 個 task 零 OOM 通過。

> 值得一提：同一台機器上 `romulus` 用 `-j 16` 是能過的。
> 因為它走 `openbmc-openpower` distro，重量級 C++ recipe 少很多。
> **能過一次不代表設定是安全的。**

---

## 五、Build 與開機

```bash
. setup gb200nvl-obmc
bitbake obmc-phosphor-image
```

產出 64 MB 的 `obmc-phosphor-image-gb200nvl-obmc.static.mtd`，剛好對應 `FLASH_SIZE = "65536"`，
不需要 padding。

開機腳本：

```bash
#!/bin/bash
T=/path/to/openbmc/build/evb-ast2600/tmp
Q=$T/sysroots-components/x86_64/qemu-system-native/usr/bin/qemu-system-arm
LIB=$T/work/x86_64-linux/qemu-system-native/11.0.2/recipe-sysroot-native/usr/lib
IMG=/path/to/openbmc/build/gb200nvl-obmc/tmp/deploy/images/gb200nvl-obmc/obmc-phosphor-image-gb200nvl-obmc.static.mtd

exec env LD_LIBRARY_PATH="$LIB" "$Q" -m 1G -M gb200nvl-bmc -nographic \
  -drive file="$IMG",format=raw,if=mtd \
  -net nic -net user,hostfwd=tcp::2224-:22,hostname=qemu
```

實際開機序列：

```
qemu-system-arm: warning: nic ftgmac100.1 has no peer
qemu-system-arm: warning: nic ftgmac100.2 has no peer
qemu-system-arm: warning: nic ftgmac100.3 has no peer

U-Boot SPL 2019.04 (Jun 02 2026 - 01:44:00 +0000)
Trying to boot from RAM

U-Boot 2019.04 (Jun 02 2026 - 01:44:00 +0000)
...
Phosphor OpenBMC (Phosphor OpenBMC Project Reference Distro) 3.1.0-dev gb200nvl-obmc ttyS4

gb200nvl-obmc login:
```

登入 `root` / `0penBmc`。

```
[   34.253091] ftgmac100 1e670000.ethernet eth1: NCSI: No channel found to configure!
```

這行是預期的 —— QEMU 裡沒有 NC-SI 對端。

---

## 六、驗證：一次完整的 PLDM 交握

```bash
zcat /proc/config.gz | grep '^CONFIG_MCTP'
```

```
CONFIG_MCTP=y
CONFIG_MCTP_FLOWS=y
CONFIG_MCTP_SERIAL=y
CONFIG_MCTP_TRANSPORT_I2C=y
CONFIG_MCTP_TRANSPORT_I3C=y
CONFIG_MCTP_TRANSPORT_USB=y
```

daemon 都在跑：

```bash
systemctl is-active mctpd pldmd
# active
# active
```

### 關鍵：不需要 host 端也能有 responder

很多人（包括我一開始）會以為 QEMU 裡沒有 host、沒有真的 endpoint，
所以 `pldmtool` 送出去不會有人回應。**這是錯的** —— `pldmd` 自己就是 responder。

在 loopback 上指派一個 EID 就行：

```bash
mctp addr add 8 dev lo
mctp addr show
# eid 8 net 1 dev lo

pldmtool base GetPLDMTypes
```

```json
{
    "CompletionCode": "SUCCESS",
    "PLDMTypes": [
        { "PLDM Type": "base",     "PLDM Type Code": 0 },
        { "PLDM Type": "platform", "PLDM Type Code": 2 },
        { "PLDM Type": "bios",     "PLDM Type Code": 3 },
        { "PLDM Type": "fru",      "PLDM Type Code": 4 }
    ]
}
```

看 wire 上的位元組：

```bash
pldmtool raw -d 0x80 0x00 0x04
```

```
pldmtool: Tx: 80 00 04
pldmtool: Rx: 00 00 04 00 1d 00 00 00 00 00 00 00
```

對照 DSP0240 的 message header 拆解：

| byte | 值 | 意義 |
|---|---|---|
| 0 | `0x80` | Rq=1(request),InstanceID=0 |
| 1 | `0x00` | HdrVer=0,PLDMType=0(Base) |
| 2 | `0x04` | GetPLDMTypes |

回應：

| byte | 值 | 意義 |
|---|---|---|
| 0 | `0x00` | Rq=0(response) |
| 3 | `0x00` | CompletionCode = SUCCESS |
| 4–11 | `1d 00 …` | 8 bytes bitfield,64 bit 對應 PLDM type 0..63 |

**`0x1d` = `0b0001_1101` = bit 0、2、3、4** —— 正好是 base / platform / bios / fru，
跟上面 JSON 完全一致。你可以自己從位元組推回去，不必信工具的翻譯。

`pldmd` 的 log 會有這行：

```
Failed to open remote terminus EID file at path '/usr/share/pldm/host_eid'
```

那只代表沒有**遠端** host terminus，不影響本地交握。

---

## 七、與一般 Aspeed 評估板的差異

同樣的流程也可以跑 `evb-ast2600`(AST2600 官方評估板)。兩者對照：

| | evb-ast2600 | gb200nvl-obmc |
|---|---|---|
| distro 版本 | `nodistro.0` | `3.1.0-dev` |
| MCTP transport | SERIAL / I2C / USB | SERIAL / I2C / **I3C** / USB |
| PLDM 來源 | 要自己加 `IMAGE_INSTALL` | 平台 `require pldm.inc` |
| QEMU machine | 8.2.2 內建 | 需要 ≥ 10.1 |

`CONFIG_MCTP_TRANSPORT_I3C=y` 只出現在 NVIDIA 平台。共用的 `mctp.cfg` fragment
兩邊都要求 I3C，但 evb 的 kernel 沒有 —— 我推測是 I3C 匯流排支援在 aspeed 通用 defconfig
沒開、導致該 transport 被丟棄，而 NVIDIA 平台 config 有開。
**這點我沒有實際追進 defconfig 驗證，列為觀察而非結論。**

I3C 是 GPU 與加速器底板上 MCTP 常走的匯流排，出現在這裡是合理的。

---

## 八、這證明了什麼，又沒證明什麼

誠實劃線很重要，因為這件事很容易被講得比實際大。

**這確實證明：** 你能從原始碼組出一份真實資料中心平台的 BMC firmware、
理解它的 flash 分割與 distro 組成、把它開機到 userspace、
並在上面跑通一次符合 DMTF 規格的 PLDM 交握。

**這不能證明：** 你碰過真的 GB200 硬體。QEMU 裡沒有 GPU、沒有 NC-SI 對端、
沒有真正的 host terminus,I2C/I3C 上也沒有任何真實裝置。
平台專屬的感測、電源時序、韌體更新流程都沒有被實際驗證。

換句話說，這是一個**紮實的軟體側練習**，不是硬體 bring-up 經驗。
引用這份紀錄時要說清楚邊界 —— 說清楚反而比含糊更有說服力。

---

## 小結

1. `meta-nvidia` 在 OpenBMC 樹內，`gb200nvl-obmc` 平台原生含 PLDM/MCTP
2. `gb200nvl-bmc` machine 需要 QEMU ≥ 10.1，由 NVIDIA 送進 upstream
3. 不必自己編 QEMU 也不必 sudo —— `bitbake qemu-system-native` 給你 11.0.2
4. 編出來的 QEMU 要設 `LD_LIBRARY_PATH`，否則會載到系統舊版 `libslirp` 而失敗
5. 30 GB RAM 請把 `BB_NUMBER_THREADS` / `PARALLEL_MAKE` 降到 6 並開 `BB_PRESSURE_MAX_MEMORY`
6. `pldmd` 自己就是 responder，不需要 host 也能完成完整的 PLDM 交握
