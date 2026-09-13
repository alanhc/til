# 高通與聯發科 Android 開機流程深度解析

> 給 BSP / 嵌入式工程師的架構對照筆記
>
> 本文內容均整理自各家公開技術文件與公開規格，僅討論架構層級的設計取捨，不涉及任何廠商的內部實作細節、未公開參數或安全性弱點。

---

## 前言：為什麼要搞懂兩家的開機鏈

如果你只寫 Android Framework 或 App，開機流程對你來說大概就是「開機動畫跑完就進系統」。但只要踏進 BSP、kernel、bootloader 這一層，第一天就會撞上這個問題：**同樣一支 Android 手機，換個晶片供應商，開機前半段幾乎是兩套不同的世界。**

高通（Qualcomm）跟聯發科（MediaTek，以下簡稱 MTK）在 Linux kernel 跑起來之後，行為高度一致 —— 都是標準 AOSP，`init` 讀 `.rc`、`zygote` 起來、`SystemServer` 接手。但在 kernel 之前那段，兩家的差異大到會影響整個 debug 方法論：

- DRAM 初始化失敗，該看哪一段 log？
- Verified Boot 過不了，簽章是誰驗的？
- 想改開機參數、加一個開機階段的 driver，改哪一份 code？
- 換平台時，哪些既有經驗可以帶著走，哪些得從零學？

這篇文章會把兩家的開機鏈逐階段拆開，對照它們在架構、分割區與除錯路徑上的差別。

---

## 一、共通的地基：ARM 的 BL 分層模型

在談差異之前，先建立共同語言。ARMv8-A 定義了一套通用的開機階段模型（Trusted Firmware-A 的分層），兩家其實都遵守這個骨架，只是各自用不同名字實作：

| 通用階段 | 執行等級 | 職責 | 高通對應 | 聯發科對應 |
|---|---|---|---|---|
| **BL1** | EL3 | 晶片內 ROM，不可改寫，信任根 | PBL | BootROM |
| **BL2** | EL3/EL1 | 初始化 DRAM、載入後續 image 並驗簽 | XBL_Loader | Preloader |
| **BL31** | EL3 | Secure Monitor、PSCI、SMC 分派 | TZ / XBL_SEC | ATF BL31 |
| **BL32** | S-EL1 | Trusted OS (TEE) | QTEE | OP-TEE / 專案指定 TEE |
| **Hypervisor** | EL2 | 虛擬化與記憶體隔離 | Gunyah（前身 QHEE） | GenieZone |
| **BL33** | EL1 (Non-secure) | 一般世界的 bootloader，fastboot、AVB | ABL（+ GBL） | LK / LK2 |
| **OS** | EL1 | Linux kernel | 相同 | 相同 |

看懂這張表就抓到重點了：**兩家的階段語意是對得上的，差別在實作技術棧與工程慣例。**高通往 UEFI 靠攏，MTK 維持輕量的 LK 路線；DRAM 初始化的落點也不同。理解這個對應關係，跨平台移植時就不會迷路。

---

## 二、高通的開機鏈：一條逐漸 UEFI 化的路

### 2.1 PBL — 固化在矽晶片裡的信任根

Primary Boot Loader 位於 SoC 內部的 Mask ROM，出廠即固化、無法更新。它做的事情非常精簡：

1. 讀取 boot config 決定開機介質（UFS / eMMC）
2. 判斷是否需要進入原廠的下載模式
3. 從 boot partition 讀出 XBL，依據晶片內熔絲（QFPROM）中的 root key hash 驗證簽章
4. 驗過就跳過去執行

PBL 的關鍵在於**它是整條信任鏈的錨點**。一旦 secure boot 相關熔絲被燒錄，從這一刻起所有後續 image 都必須帶有對應私鑰簽出來的簽章，否則開機流程不會往下走。

### 2.2 XBL — 從 SBL1 演化來的核心階段

XBL（eXtensible Boot Loader）取代了舊世代的 SBL1，從 SDM845 世代開始全面 UEFI 化。它不是一個單體，公開資料中至少可分成三塊：

**XBL_SEC**
跑在 EL3，是所有 TrustZone image 的信任根。負責 provisioning TrustZone、設定安全世界的記憶體區域，並提供後續階段的驗簽服務。

**XBL_Loader**
真正做粗活的部分：

- **DDR training / calibration** —— 高通最關鍵的一步。訓練結果會被快取，下次開機沿用以縮短開機時間
- 初始化 PMIC、clock、基本 GPIO
- 讀 `xbl_config` 取得平台配置（CDT，Configuration Data Table）
- 依序載入並驗證 `tz`、`hyp`、`aop`、`devcfg`、`cmnlib` / `cmnlib64`、`keymaster` 等 image

**XBL_Core**
UEFI 的 DXE 環境，提供 UEFI protocol 與 UEFI variable services，供 ABL 這個 UEFI application 使用。

### 2.3 TZ / Hypervisor — 安全世界起床

`tz` 是高通版本的 BL31 + Trusted OS 組合。它建立 SMC handler、PSCI（CPU 上下電、休眠喚醒的入口），並載入 QTEE。Keymaster / KeyMint、生物辨識、DRM、Secure Camera 這類服務都跑在這裡。

Hypervisor 部分，高通從 QHEE 演進到 **Gunyah**（已開源）。它跑在 EL2，主要做 Stage-2 記憶體隔離 —— 例如把某段記憶體從 Non-secure kernel 的視野中移除，交給安全服務獨占使用。

### 2.4 AOP — 永遠醒著的小 CPU

`aop`（Always-On Processor，取代舊平台的 `rpm`）是一顆獨立的小核，負責電源域管理、時脈投票、低功耗狀態機。它在 XBL 階段就被載入啟動，之後整台機器的 power resource 投票都會經過它。

> **實務要點**：AOP 沒起來 → clock / regulator 拿不到 → 後面任何 driver probe 都會 timeout。這種問題在 kernel log 裡看起來像「一堆莫名其妙的 device probe 失敗」，實際根因在 XBL 階段。跨階段追根因的意識很重要。

### 2.5 ABL — 一般世界的門面

ABL（`abl.elf`）跑在 EL1 Non-secure。它源自 LK（Little Kernel），但現在已被包成一個 **UEFI application** —— 外層看是 ELF，用 UEFI 分析工具拆開會看到完整的 UEFI FV 結構。

ABL 的職責：

- 實作 **fastboot** 協定
- 執行 **Android Verified Boot 2.0（AVB）**：驗證 `vbmeta`，計算 boot / dtbo / vendor_boot 的 hash，決定 boot state（GREEN / YELLOW / ORANGE / RED）
- 依 `qcom,msm-id`（SoC ID + revision）與 `qcom,board-id`（platform ID + subtype）從 `dtbo` 分割區挑出正確的 device tree overlay，與 base DTB 合併
- 組出 kernel command line，設定 `androidboot.*` 參數
- 載入 `boot.img` / `vendor_boot.img`，跳進 kernel

### 2.6 架構趨勢：GBL 帶來的兩段式 BL33

值得關注的近期演進是 **GBL（Generic Bootloader）**。從搭載較新 Android 版本出貨的裝置開始，高通的 ABL 會嘗試從獨立分割區載入 GBL —— 一個 Google 主導、跨廠商通用的 UEFI application，目的是把「載入 kernel + 驗證 + 傳參數」這段從各家 vendor bootloader 抽出來標準化。

這代表高通的 BL33 正在變成**兩段式**：ABL（vendor 專屬，做硬體初始化與 fastboot）→ GBL（通用，做 AVB 與 kernel 載入）。

從架構設計的角度，這個趨勢有一個通用的啟示值得記下來：**每新增一個 bootloader 交接點，就多一個需要明確定義驗證責任歸屬的介面。**「誰負責驗誰」在多段式開機鏈中必須是設計階段就寫清楚的合約，而不是留給實作各自解讀 —— 這對任何平台都成立。

### 2.7 高通分割區速查

| 分割區 | 內容 |
|---|---|
| `xbl` / `xbl_config` | XBL 主體與平台配置（CDT） |
| `tz` | TrustZone / Secure Monitor |
| `hyp` | Hypervisor |
| `aop` | Always-On Processor firmware |
| `devcfg` | Device configuration，安全世界的裝置權限設定 |
| `cmnlib` / `cmnlib64` | TZ 共用函式庫 |
| `keymaster` | Keymaster / KeyMint TA |
| `abl` | Application Bootloader |
| `modem` / `dsp` | 各協處理器韌體（由 kernel 的 remoteproc / PIL 載入） |
| `dtbo` | Device tree overlay |
| `vbmeta` / `vbmeta_system` | AVB metadata |

---

## 三、聯發科的開機鏈：務實的 LK 路線

### 3.1 BootROM

與 PBL 同樣固化在矽晶片裡，是信任鏈的起點。開機時它會依 boot config 決定開機來源，從儲存裝置的 boot 區讀出 **Preloader**，並依熔絲設定決定是否執行簽章驗證，驗過後跳入 Preloader。

BootROM 同時也是原廠工程與產線工具的接入點；相關協定與工具屬於原廠釋出範圍，不在本文討論。

### 3.2 Preloader — MTK 的 BL2

Preloader 體積小、跑在 SRAM 上（此時 DRAM 尚未初始化），對應高通的 XBL_Loader。依公開文件，它負責：

- **EMI / DRAM calibration** —— MTK 版本的 DRAM 訓練，校準參數會保存供後續開機沿用
- 初始化 PMIC、charger（低電量時的充電顯示就是這階段判斷的）
- 讀取 GPT，載入並驗證 `lk`、`tee`、`gz` 等分割區進 DRAM
- 交棒給 ATF BL31

> **實務要點**：Preloader 位於儲存裝置的 boot 硬體分割區，一般 fastboot 觸及不到，屬於整條鏈上最需要謹慎對待的一塊。平台開機異常時，UART log 是最前線的資訊來源。

### 3.3 ATF BL31 + TEE + GenieZone

MTK 這一段的技術棧相對貼近上游 —— 直接採用 **ARM Trusted Firmware-A** 的 BL31。

- **BL31**：Secure Monitor、PSCI、SMC 分派。初始化完成後跳回 BL2 繼續流程，再由 BL2 交棒給 BL33
- **BL32 (`tee`)**：Trusted OS。依專案不同可能是 **OP-TEE**（MTK IoT / Yocto BSP 的公開預設）或專案指定的其他 TEE
- **`gz` (GenieZone)**：MTK 的 hypervisor，跑在 EL2

用上游 ATF 的好處是：BL31 這一層的行為對照 ARM 官方文件即可理解，PSCI 相關問題也能直接參考上游社群的討論，這對新進工程師的學習曲線是實質的幫助。

### 3.4 LK / LK2 — 輕量的 BL33

MTK 的 BL33 是 **LK（Little Kernel）**，不走 UEFI。這是兩家最顯著的架構分歧。

LK 的職責與高通 ABL 高度重疊：

- fastboot 協定
- AVB 2.0 驗證，決定 boot state
- 依 `mediatek,mtXXXX` compatible 與專案定義的 board 資訊做 DTBO 匹配與合併
- 顯示開機 logo、處理組合鍵進入 recovery / fastboot
- 載入部分協處理器韌體（哪些韌體在哪一階段載入，各專案配置不同）
- 組 cmdline，載入 `boot.img`，跳 kernel

程式碼規模上，LK 遠小於 ABL 加上整套 UEFI 環境。**這是設計取捨：換得的是較短的開機時間與較低的維護複雜度，代價是缺少 UEFI 那層標準化介面與現成的擴充生態。**兩種路線各有適用情境，沒有絕對優劣。

### 3.5 聯發科分割區速查

> 下表整理自公開可見的資訊：社群維護的 MTK device tree（LineageOS / TWRP）與網路上流傳的 scatter file。**只列各機種共通的分割區名稱與用途，不含任何專案專屬的配置、位址或大小。**

| 分割區 | 內容 |
|---|---|
| `preloader` | Preloader（位於儲存裝置 boot 硬體分割區） |
| `tee1` / `tee2` | ATF BL31 + Trusted OS（A/B 兩份） |
| `gz1` / `gz2` | GenieZone hypervisor |
| `lk` / `lk2` | Little Kernel bootloader |
| `logo` | 開機 logo 資源 |
| `scp` | System Co-Processor 韌體 |
| `sspm` | 系統電源 / 安全相關管理處理器韌體 |
| `mcupm` | MCUSYS 電源管理韌體 |
| `spmfw` / `dpm` | 電源管理相關微碼 |
| `md1img` | Modem 韌體（由 kernel 的 ccci 相關 driver 載入） |
| `dtbo` / `vbmeta` | 同 AOSP 標準 |
| 校準 / 廠測資料區 | 射頻校準值、廠測參數等**每台機器獨一無二**的資料 |

> **通用警告（兩家皆適用）**：上表最後一類「每台機器獨一無二」的校準資料區，是刷機作業中最需要保護的部分。這類資料在產線寫入、與該台裝置的硬體綁定，一旦被整區覆蓋就無法用另一台機器的備份還原。高通平台也有性質相同的對應區域。**任何刷機流程都應該先確認這些區域是否在覆蓋範圍內。**

---

## 四、核心差異總整理

### 差異一：UEFI vs LK —— 最根本的分歧

高通自 SDM845 世代起，XBL_Core 與 ABL 全面 UEFI 化，帶來 DXE driver model、UEFI protocol、UEFI variable、GPT 原生支援這一整套標準化基礎設施。好處是與 PC 生態接軌、可用成熟的 UEFI 工具分析、廠商間介面較一致；代價是 image 較大、開機時間增加、學習曲線較陡。

MTK 維持 LK 路線，程式碼直觀、build 快、開機快，但每個功能都得自己實作，缺乏標準介面。當你需要在 bootloader 階段新增複雜功能（例如網路開機、複雜的儲存裝置支援），UEFI 環境會省下不少工。反之，若專案訴求是最短開機時間與最小 footprint，LK 的優勢就很明顯。

**這是典型的「標準化 vs 輕量化」取捨，兩條路線都有其合理性。**

### 差異二：DRAM 初始化的落點

| | 高通 | 聯發科 |
|---|---|---|
| 執行階段 | XBL_Loader | Preloader |
| 常見稱呼 | DDR training | EMI calibration |
| Log 來源 | XBL UART log | Preloader UART log |
| 典型症狀 | 卡在 XBL 階段 | 卡在 Preloader 階段 |

這是**跨平台 debug 時最需要換腦袋的一點**。同樣是「開機卡住、螢幕沒亮」，兩邊要挖的 log 來源、格式與輸出時機完全不同。

### 差異三：映像檔格式與簽章機制

**高通**採用 ELF 容器搭配 hash table segment 與簽章（`.mbn` / `.elf`）。驗證時先驗簽章，再逐段比對 hash。信任根是晶片熔絲中燒錄的 root key hash 與 OEM / Model 識別資訊。

**聯發科**在 raw binary 前附加自訂的 image header，簽章與憑證鏈以原廠定義的結構附加，信任根同樣落在晶片熔絲。

兩家都支援 **Anti-Rollback**（防止刷回舊版韌體），透過熔絲中的版本計數器實作。

> **實務要點**：Anti-Rollback 是不可逆的。一旦升版並觸發計數器遞增，就無法降回舊版。這在 OTA 驗證、送測樣機、開發板重複燒錄等情境下都要事先規劃清楚，避免測試機被鎖死在某個版本。

### 差異四：協處理器的載入方式

高通用 **PIL / remoteproc** 框架，在 Linux kernel 起來之後才載入 modem、DSP 等子系統韌體。好處是統一框架、支援 subsystem restart（SSR）—— 子系統掛掉可以單獨重啟而不必重開機。

MTK 則較為分散：部分協處理器韌體在 LK 或早期 kernel 階段載入，modem 由 kernel 中對應的 driver 負責。兩種做法在啟動時序與失效隔離上各有取捨。

### 差異五：Device Tree 匹配策略

兩家都用 AOSP 標準的 DTBO 機制，但匹配鍵不同：

- **高通**：`qcom,msm-id`（SoC ID + hardware revision）配 `qcom,board-id`（platform ID + subtype），ABL 在 runtime 掃 `dtbo` 分割區裡所有 overlay，挑出匹配度最高的
- **聯發科**：以 `mediatek,mtXXXX` compatible 加上專案定義的 board 資訊匹配

實務上高通的匹配規則欄位較多、組合較複雜 —— 新板子的 board-id 沒填對，開機會直接卡在 ABL 找不到對應 DTB。這是新平台 bring-up 初期的高頻踩雷點。

### 差異六：原廠下載模式

兩家都提供 SoC 層級的原廠下載 / 回復機制，供產線燒錄與工程回復使用，且都要求對應的執行元件經過簽章。

- **高通**：QFIL / QPST 為主要的原廠工具鏈
- **聯發科**：SP Flash Tool 為主要的原廠工具鏈

兩者在協定設計、簽章要求與產線整合方式上有各自的做法，**細節屬於各廠商的原廠文件範圍，取得管道與授權依合作關係而定，這裡不展開。**工程上需要知道的是：這兩套工具鏈完全不通用，產線治具與燒錄站軟體無法沿用，換平台時必須重新導入。

### 差異七：除錯基礎設施

**高通**：
- `ramdump` 機制，異常時可將 DRAM 內容導出
- 搭配原廠工具與 Trace32 等除錯器分析
- `pstore` / `ramoops` 保留 kernel log 跨重開機

**聯發科**：
- **AEE（Android Exception Engine）** —— 例外收集框架，會產生含 kernel log、backtrace 與記憶體快照的除錯檔
- Preloader / LK 的 UART log 是最前線的資訊源
- 對應的記憶體 dump 機制供深入分析使用

兩套工具鏈的檔案格式與分析流程各自獨立，**跨平台工程師需要同時熟悉兩套**，這是實務上的隱性學習成本，值得在專案排程時預留時間。

---

## 五、實戰：卡在哪一段？該看哪裡？

這張表是本文最有日常實用價值的部分：

| 症狀 | 高通 —— 該查 | 聯發科 —— 該查 |
|---|---|---|
| 螢幕不亮、無限重開 | XBL UART log，看 DDR training | Preloader UART log，看 EMI calibration |
| 有 logo 但進不了系統 | ABL log，檢查 AVB 與 DTBO 匹配 | LK log，檢查 AVB 與 DTBO 匹配 |
| Verified Boot 警告畫面 | vbmeta 驗證失敗 | 同左 |
| kernel 起來但大量 probe 失敗 | AOP 沒起來，clock / regulator 拿不到 | 對應的電源 / 協處理器韌體載入失敗 |
| TEE 服務異常、安全功能不可用 | `tz` / `keymaster` / `cmnlib` 版本不匹配 | `tee` 與 `gz` 版本不匹配 |
| 射頻表現異常 | 校準資料區狀態確認 | 校準資料區狀態確認 |

**一個通則**：兩家平台都有「韌體套件必須整組匹配」的特性。你不能只更新 `tz` 而不動 `cmnlib`，也不能只換 `lk` 而不管 `tee` —— 這些 image 之間存在 ABI 依賴，混版是最常見的開機失敗原因。做版本更新時請以原廠釋出的完整韌體套件為單位，不要單檔抽換。

---

## 六、跨平台移植的心理準備

如果專案要在兩家之間切換，以下是實際會痛的地方：

**幾乎不用改的**：Linux kernel 中與平台無關的 driver、HAL 之上的所有東西、AOSP framework 修改、SELinux policy 的大部分。

**要整個重寫的**：bootloader 階段的客製（開機 logo、充電顯示、組合鍵行為、工程模式入口）、DTS 的 SoC 相關部分、電源管理策略、camera / display 的 vendor HAL。

**最容易被低估的**：**生產線流程**。兩家的燒錄工具、治具介面、燒錄站軟體、產測流程、校準資料寫入方式完全不同。工廠端的切換成本經常比軟體端還高，在專案評估階段務必納入 —— 這是很多專案排程失準的真正原因。

---

## 七、小結

把兩家攤開來看，可以歸納成幾句話：

**高通**走的是**標準化路線** —— UEFI 化的 bootloader、與 PC 生態接軌的介面模型、正在往兩段式 BL33 演進。優點是架構清晰、工具成熟；代價是體積與開機時間。

**聯發科**走的是**輕量務實路線** —— LK 搭配上游 ATF、精簡的 Preloader。優點是開機快、程式碼直觀、BL31 層可直接參照 ARM 官方文件；代價是缺少 UEFI 那層現成的標準化基礎設施。

**兩者是不同的工程取捨，服務的是不同的產品定位與成本結構，並沒有誰對誰錯。**而在 kernel 之後，兩者殊途同歸，都是同一套 AOSP。

真正該記住的是那條**共通的 BL1 → BL2 → BL31 → BL33 → Kernel 骨架**。名字會變、實作會變、廠商會變，但這個分層邏輯是穩定的。抓住骨架，換平台時你只需要重新對應「這一段在這家叫什麼、log 在哪裡、誰負責驗簽」，而不是從零學起。

---

## 參考資料

- [Qualcomm Linux Boot Guide — Boot loader](https://docs.qualcomm.com/bundle/publicresource/topics/80-70014-4/bootloader.html)
- [Secure Boot and Image Authentication Technical Overview (Qualcomm)](https://www.qualcomm.com/content/dam/qcomm-martech/dm-assets/documents/secure-boot-and-image-authentication-version_final.pdf)
- [MediaTek IoT Yocto — BSP & Boot Architecture](https://mediatek.gitlab.io/aiot/doc/aiot-dev-guide/master/sw/yocto/boot.html)
- [MediaTek IoT Yocto — Secure Boot](https://mediatek.gitlab.io/aiot/doc/aiot-dev-guide/master/sw/yocto/secure-boot.html)
- [ARM Trusted Firmware-A Documentation](https://trustedfirmware-a.readthedocs.io/)
- [Android Verified Boot 2.0 — AOSP Documentation](https://source.android.com/docs/security/features/verifiedboot)
- [Gunyah Hypervisor](https://github.com/quic/gunyah-hypervisor)

---

*本文為個人技術筆記，內容整理自上述公開文件，不代表任何雇主立場，亦不包含任何未公開資訊。*
