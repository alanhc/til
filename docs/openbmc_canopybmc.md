https://canopybmc.org/blog/qemu-to-hardware-testing-approach/

**Canopy OpenBMC**（正式名稱 **Canopy**）是一個**建立在 OpenBMC 之上的企業級 OpenBMC 發行版（distribution）**，目標是讓 OpenBMC 更適合產品化，而不只是開發平台。它是由 **BlindSpot Software GmbH** 發起並維護的專案。([Canopy][1])

你可以把它想成：

> **Linux Kernel → Ubuntu / Debian**
>
> **OpenBMC → Canopy**

也就是說，它不是重新發明一套 BMC，而是在 **OpenBMC upstream** 的基礎上，加上更多工程化能力。

---

## 為什麼會有 Canopy？

OpenBMC 官方本身主要是開源社群專案，重點在：

* 新功能
* 支援更多平台
* 社群協作

但如果是企業要出貨 Server，還需要很多東西，例如：

* 長期維護（LTS）
* Regression Testing
* Hardware CI
* Security Patch
* Release Management
* 穩定版本

Canopy 就是專門補這些。([Canopy][2])

---

## Canopy 的特色

官方列出幾個核心理念：

### 1. Upstream-first

每週都會同步（rebase）OpenBMC 最新版本，而不是自己維護一個分叉很多年的版本。

好處：

* 不容易跟 upstream 脫節
* Bug 可以回饋社群
* 新功能可以快速取得

---

### 2. Hardware CI

這也是你剛剛翻譯那篇文章提到的重點。

不是只跑：

```
bitbake
unit test
```

而是：

```
Commit
    ↓
Build Firmware
    ↓
Flash 到 Coffee Lake 主機
    ↓
Power On
    ↓
Boot
    ↓
測試 IPMI
測試 Redfish
測試 Sensor
測試 GPIO
...
```

每個 commit 都真的跑在實體機器。

官方稱為 **Hardware-tested**。([Canopy][1])

---

### 3. LTS

例如：

```
2026.06   LTS
2026.12
2027.06
2027.12
2028.06   LTS
```

LTS 版本提供：

* Security Patch
* Bug Fix
* 長期維護

不像 upstream 只是不斷往前。

---

### 4. 預編譯 Binary

對支援的平台直接提供：

```
image-bmc
kernel
u-boot
```

不用每次自己 bitbake 幾個小時。

---

### 5. Developer Enablement

包括：

* 更好的文件
* 更好的工具
* 更容易設定 machine
* CI/CD

目的就是讓 OpenBMC 開發更順暢。

---

## HPE 也在合作

目前官方網站已公開宣布：

> Canopy 正與 **HPE** 合作，將 OpenBMC 帶到 **ProLiant Gen11** 平台。([Canopy][1])

代表它不只是個研究專案，而是開始被真正的 Server 廠商採用。

---

## 跟你現在做的 OpenBMC 有什麼關係？

你之前做過：

* AST2600
* Yocto
* OpenBMC
* DTS
* PMBus Driver
* FRU
* IPMI
* Redfish
* Server ODM

如果進入像 NVIDIA、Meta、Google、HPE、AMD 等公司的 BMC 團隊，未來很可能會接觸到類似 Canopy 的開發流程：

```
Developer
      │
      ▼
Gerrit Review
      │
      ▼
+2 Approved
      │
      ▼
Hardware CI
      │
      ▼
Coffee Lake
AST2600
NPCM845
...
      │
      ▼
Regression Test
      │
      ▼
Merge
```

這比傳統「自己 build、自己燒板、自己測」更成熟、更自動化。

---

## 它和 OpenBMC 的關係

```text
                Linux Foundation
                       │
                 OpenBMC upstream
                       │
          --------------------------
          │                        │
      Meta OpenBMC            Canopy OpenBMC
                                   │
                          Weekly Rebase
                                   │
                         Hardware CI
                         LTS Support
                         Enterprise Release
                         Developer Tools
```

**一句話總結：**

**Canopy OpenBMC 是一個以 OpenBMC 為基礎、採用「upstream-first」策略的企業級 OpenBMC 發行版，重點放在實體 Hardware CI、長期維護（LTS）、穩定發布與開發者體驗，非常符合現代資料中心與伺服器韌體的開發流程。** ([Canopy][1])

[1]: https://canopybmc.org/?utm_source=chatgpt.com "Open. Stable. Ready. | Canopy"
[2]: https://canopybmc.org/philosophy/?utm_source=chatgpt.com "Philosophy & Approach | Canopy"
