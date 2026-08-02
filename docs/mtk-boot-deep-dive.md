# MTK Boot 深入筆記:Preloader/DRAM Init 與 LK/AVB

> 通用架構說明,實際檔名、暫存器與流程細節會隨 SoC 世代(MT6xxx)與 Android 版本而異,請以自家 codebase 為準。

## 來源與可信度說明

文末有完整參考連結。內文標記代表該段落的依據強度:

| 標記 | 意義 |
|---|---|
| **[規範]** | 有官方規範或開源實作可查證(AOSP、TF-A、JEDEC、coreboot) |
| **[社群]** | 來自公開逆向分析、開源工具或社群文件,方向可信但非官方 |
| **[推論]** | 我依通用工程原理歸納,**未經查證**,請務必用你手上的官方文件核對 |

**MTK Preloader 與 LK 的原始碼並未完整公開**,因此 Part 1 的細節多為 [社群] 或 [推論]。唯一的例外是 **coreboot 專案裡有 MediaTek 官方貢獻的、完整開源的 DRAM calibration 程式碼**(MT8173 / MT8183 / MT8186 等 Chromebook 用 SoC)— 這是目前公開世界裡最接近 MTK 真實 DRAM init 的東西,強烈建議拿來對照學習[參考 8][參考 9]。

---

# Part 1 — Preloader 與 DRAM Init

## 1.1 Preloader 的執行環境

Preloader 是 MTK 特有的 BL2。它的處境很特殊:

- **跑在 SRAM**,不是 DRAM(DRAM 還沒起來)。SRAM 通常只有幾百 KB,所以 preloader 的 binary size 被壓得很緊 — 這也是為什麼 preloader code 幾乎不用 malloc、不用大型 library。**[社群]** 有人逆向 MT6765 得出 preloader 載入到 SRAM offset `0x200f10`、entry `0x201000`,且 CPU 此時仍在 **AArch32** 模式[參考 6]。
- 由 BootROM 從 boot region(eMMC 的 `boot0`,或 UFS 的 boot LU)載入並驗簽 **[社群]**[參考 6][參考 7]。
- 執行完的目標:把 DRAM 弄起來,接著**把 `lk`、`tee`(ATF)、`gz`(GenieZone)等 image 載入 DRAM 並驗章**,再跳過去 **[社群]**[參考 6]。
- 註:開機 logo 與充電動畫**不一定在 LK**,逆向資料指出部分機種是由 Preloader 負責[參考 6]。實際由哪一級畫,請以自家 code 為準。

### 主要職責 **[推論]**

任何 BL2 級的 loader 大致都要做完下面這些事,順序在各家實作會有出入。以下是我依**通用 BL2 職責**歸納的心智模型,不對應任何特定廠商的程式碼結構:

```
進入點 (assembly)
  → 關 watchdog / 設定 stack
  → 平台初始化
      ├─ watchdog          判斷上次是否為 WDT reset
      ├─ UART              log 從這裡開始噴
      ├─ PLL / clock       把 CPU/BUS 從開機預設頻率拉上來
      ├─ PMIC              ★ 上電順序、各 rail 電壓
      ├─ RTC               開機原因(power key / charger / alarm)
      ├─ DRAM init         ★★ calibration,最耗時也最容易出事
      ├─ boot device       eMMC / UFS
      ├─ partition table   讀 GPT 或廠商自訂的分區表
      └─ 載入下一階段 → jump
```

上面打星號的 **PMIC 上電**與 **DRAM 初始化**這兩步,是 bring-up 階段絕大多數問題的來源。

## 1.2 DRAM Init 到底在做什麼

LPDDR4X / LPDDR5 的訊號速率很高(LPDDR5 可到 6400 Mbps/pin),PCB 走線長度、封裝寄生、溫度、電壓都會讓 DQ/DQS 之間的時序偏移。**Calibration 就是在找每一條資料線的「安全取樣點」**。

### Step 0:DRAM Discovery

先用低速、保守的時序把 DRAM 叫醒,讀 Mode Register:

| MR | 內容 |
|---|---|
| MR5 | Manufacturer ID(Samsung / Micron / Hynix / Nanya…) |
| MR6 / MR7 | Revision ID |
| MR8 | Density、IO width(x16/x8)、type |

依讀到的結果選對應的 EMI/DRAMC setting table。這就是為什麼同一顆 SoC 都要維護一份 memory 支援清單 — 每個 part number 的參數不同,清單沒涵蓋到的顆粒就開不起來。coreboot 的 MediaTek port 可以看到這份清單長什麼樣子[參考 8]。

### Step 1~N:Calibration 項目 **[規範/社群]**

概念與 JEDEC LPDDR4 規範一致[參考 10][參考 11];**實際順序與命名以 coreboot 的 MediaTek 實作為準**[參考 8][參考 9] — 那裡的 `dramc_pi_calibration_api.c` 就是真的 MTK calibration 流程,可以直接讀。

依序大致如下(名稱各家略有差異):

1. **ZQ Calibration** — 校準 driver strength / ODT 阻抗,對抗製程與溫度漂移。
2. **CA Training**(Command/Address training)— 校 CA bus 對 CK 的時序。CA 錯了後面全錯。
3. **Write Leveling** — 校 DQS 對 CK 的相位。因為 fly-by 走線,每個 byte lane 到達時間不同。
4. **Gating / DQS Gating Window** — 讀取時,controller 要知道「什麼時候打開 DQS 接收窗」。這一步在找 gating 的中心點,是最容易因為 layout 不良而失敗的項目之一。
5. **RX DQ / DQS(Read Eye)** — 掃描讀取的 data eye,per-bit 調 delay,找出眼圖中心。
6. **TX(Write Eye)** — 同上,但方向是寫入。
7. **RX DATLAT**(Read Latency)— 決定 read data 回來要等幾個 cycle 取樣。
8. **Write DBI / Read DBI、TX OE** 等細部項目(視世代)。

每一步的輸出是一組 delay 值。**Log 裡會印出每個 lane 找到的 window 起訖與寬度** — 這個「window 寬度」就是 margin,是判斷板子好壞的關鍵數字。

### Full-K vs Fast-K **[社群]**

這個機制在 coreboot 的 MediaTek port 有對應實作 — MT8186 有一筆 commit 標題就叫 "Support DRAM fast calibration using blob",且有 `dramc_param.c` 專門處理 calibration 參數的序列化[參考 9][參考 12]。以下描述方向可信,細節請對照 code。

完整跑一遍 calibration 要數百 ms 到數秒,每次開機都跑會拖慢開機時間。所以:

- **Full-K**:第一次開機(或偵測到 DRAM 換了、參數版本變了)跑完整校正,結果序列化後寫進 flash 的保留區。
- **Fast-K**:之後開機直接讀回上次結果套用,只做最小驗證。

如果你改了 DRAM 相關 code 卻沒看到行為改變,**先確認是不是走了 Fast-K 吃到舊的 calibration 結果** — 這是新人最常踩的坑。清掉那塊資料或改版本號才會重跑。

## 1.3 常見失敗與判讀

| 症狀 | 可能原因 |
|---|---|
| UART 停在 PMIC log 之後、沒有任何 DRAM log | DRAM 完全沒回應 — 硬體沒焊好、電源沒上、CS/CK 沒到 |
| Calibration 某一步 fail,log 印 `window not found` | 該 lane 時序 margin 不足 — layout、阻抗、電壓 |
| 開機不穩定,有時過有時卡 | Marginal calibration — window 太窄。需要看 shmoo |
| 冷機開不了、熱機正常(或反之) | 溫度相關的 margin 不足,或 Fast-K 資料是在另一個溫度下校的 |
| 換了另一批 DRAM 就掛 | Memory 支援清單沒涵蓋該 part number,或 MR 讀取判斷邏輯有洞 |

### Debug 手法

- **UART log 是主戰場。** 這一階段的 log 通常會用 prefix 區分子系統(平台／記憶體控制器等),實際字串以你手上的實機 log 為準。把 log level 開到最大,把每個 lane 的 window 值抓出來。
- **看 window 寬度而不是只看 pass/fail。** 過了但只剩幾個 delay step 的 margin,等於是不定時炸彈。
- **Shmoo test**:掃 Vcore / VDDQ / VDD2 電壓 × 頻率,畫出 pass/fail 圖。看形狀就知道是電壓不足、時序偏移還是雜訊。
- **和 hardware/layout team 一起看。** DRAM calibration 失敗經常不是 software bug,而是 PCB 走線等長、阻抗匹配、去耦電容的問題。這是 SW/HW 交界最密集的地方。
- **對照 golden board。** 手上永遠留一片已知良好的板子,新板子的 window 明顯窄就是硬體差異。

### 可以打開來讀的 code

Preloader 本身不公開,所以這裡不談它的目錄結構 — 手上有 BSP 的人自己 grep `dram` / `calib` / `pmic` 就找得到。下面列的是**公開、可以馬上 clone 下來讀的對照組** **[規範]**:

```
coreboot/src/soc/mediatek/mt8183/
  dramc_pi_calibration_api.c   ← RX DQS gating、各項 calibration
  dramc_pi_basic_api.c
  dramc_init_setting.c
  dramc_param.c                ← calibration 參數序列化(對應 fast-K)
coreboot/src/soc/mediatek/mt8173/dramc_pi_calibration_api.c
coreboot/src/soc/mediatek/mt8186/  ← 有 fast calibration blob 支援
```

MT8183/MT8186 是 Chromebook 用的 MTK SoC,coreboot 需要開源,所以 MediaTek 把 DRAM init 貢獻進了上游[參考 8][參考 9]。手機端的 preloader 雖然不是同一份 code,但**架構、術語與 calibration 步驟高度相似** — 這是目前公開世界裡最好的學習材料。

---

# Part 2 — LK 與 AVB(Android Verified Boot)

## 2.1 LK 的角色

LK(Little Kernel)是 MTK 的 BL33,對應 AOSP 的 bootloader / 高通的 ABL。職責:

- 進 **fastboot mode**(音量鍵組合 / `adb reboot bootloader`)
- 顯示開機 logo、充電畫面
- 讀 `misc` partition 決定進 recovery / fastbootd / normal
- **A/B slot 選擇**
- **AVB 驗證**
- 組 kernel cmdline,載入 `boot` / `vendor_boot` / `dtbo` / `init_boot`,跳進 kernel

## 2.2 完整的驗證鏈

Part 2 的 AVB 內容**幾乎全部有官方文件與開源實作可查證** **[規範]**,可信度遠高於 Part 1。核心參考是 AOSP `external/avb` 的 README[參考 1] 與 AOSP Verified Boot 文件[參考 3][參考 4]。ARM 的 BL1→BL2→BL3x 驗證鏈定義在 TF-A 的 Trusted Board Boot 文件[參考 5]。

這是面試最常被問的一條線:

```
BootROM
  └─ 用 eFuse 裡燒死的 public key hash 驗 Preloader 簽章
        (MTK Secure Boot,SBC key)
Preloader
  └─ 驗 ATF / TEE / LK 的簽章
LK
  └─ AVB 2.0:用 OEM public key 驗 vbmeta
        vbmeta 裡的 descriptor 再往下涵蓋所有分區
```

**信任的起點是 eFuse**(一次性燒錄,不可改)。整條鏈是「上一級驗下一級」,任何一環沒驗就是整條斷掉 — 這是 review 時要抓的重點。

## 2.3 AVB 2.0 的結構

`vbmeta` partition 是核心。它本身被 RSA 私鑰簽名,內容包含:

| Descriptor | 用途 |
|---|---|
| **Hash descriptor** | 針對小分區(boot, dtbo, vendor_boot, init_boot)存整個 image 的 hash。載入時一次算完比對。 |
| **Hashtree descriptor** | 針對大分區(system, vendor, product)存 dm-verity Merkle tree 的 root hash + salt。**不是開機時全算**,而是 runtime 每讀一個 block 才驗一次。 |
| **Chain partition descriptor** | 把某個分區的驗證委派給另一把 key(例如 `vbmeta_system` 由 GSI/system 的 key 簽),讓 SoC vendor 和 OEM 可以各簽各的。 |
| **Kernel cmdline descriptor** | 由 AVB 注入 cmdline,例如 dm-verity 的 mapping 參數。 |
| **Rollback index** | 防降級。 |

### 為什麼分 hash 和 hashtree

`boot.img` 只有幾十 MB,開機時算完 hash 成本可接受。`system.img` 幾 GB,開機時全算會讓開機時間爆炸 — 所以用 hashtree,把驗證成本攤到 runtime 的每次 I/O。代價是 dm-verity 有持續的效能開銷,以及一旦 flash 某個 block 壞掉,讀到才會 verity 錯誤(不是開機就抓到)。

### Rollback Protection

vbmeta 裡有 rollback index(單調遞增)。裝置端把「看過的最大值」存成 `stored_rollback_index[n]`,規則是:**除非 `rollback_index[n] >= stored_rollback_index[n]` 對所有 n 成立,否則拒絕該 image**;同時裝置會隨時間把 `stored_rollback_index[n]` 往上推[參考 1]。

AVB 規範要求用**防竄改儲存(tamper-evident storage)**來存 rollback index、驗證用的 key、以及裝置的 LOCKED/UNLOCKED 狀態[參考 1]。常見實作是 eMMC/UFS 的 **RPMB**,由 TEE(如 OP-TEE)持有金鑰存取[參考 13]。AVB 1.1 之後還加了 named persistent values,可以存任意 key-value[參考 1]。

這擋的是:攻擊者拿一個**簽章合法但有已知漏洞的舊版 image** 來刷。簽章驗得過,但 rollback index 擋下來。AOSP 對此的說法是「防止漏洞利用變成持久化」[參考 3]。

## 2.4 Boot State(四種顏色)

依 AOSP Verified Boot 文件[參考 3][參考 4]:

| State | 條件 | 行為 |
|---|---|---|
| **GREEN** | LOCKED,未使用使用者自訂 root of trust | 完整信任鏈,正常開機無警告 |
| **YELLOW** | LOCKED,但使用**使用者自行燒入的 root of trust** 且 image 由該 key 簽 | 每次開機顯示警告畫面,**10 秒後自動消失** |
| **ORANGE** | **UNLOCKED** | 每次開機顯示警告,**10 秒後自動消失**並繼續開機 |
| **RED** | 驗證失敗 | 警告畫面**不能由軟體自動關掉,必須使用者按實體鍵**才繼續 |

狀態透過 cmdline 傳下去:

```
androidboot.verifiedbootstate=green
androidboot.veritymode=enforcing
androidboot.vbmeta.digest=<hash>
```

這幾個值不只是給人看的:

- **Keymaster / KeyMint** 用 verified boot state 和 vbmeta digest 去**衍生金鑰、簽 attestation**。所以 unlock 過的裝置產生的 key attestation 會帶 ORANGE,遠端服務可以識別。
- **Play Integrity / SafetyNet** 依此判斷裝置完整性 — 這是「解鎖後銀行 App 不能用」的技術原因。

## 2.5 A/B Slot

介面定義在 AOSP 的 `boot_control.h`,行為規範見 A/B updates 文件[參考 14][參考 15]。

`misc` partition 裡的 `bootloader_message_ab` 結構存 slot metadata:

- `priority`(0–15)— 越大越優先
- `tries_remaining` — 剩餘嘗試次數
- `successful_boot` — 這個 slot 是否曾成功開機到底

LK 的選擇邏輯:挑 priority 最高、且(successful 或 tries > 0)的 slot;每次嘗試就把 tries 減一。開機成功後由 `update_verifier` / `boot_control` HAL 標記 `successful`。全部 slot 都用光就進 recovery。

選定後傳 `androidboot.slot_suffix=_a`,kernel 和 init 依此掛對應分區。

**AVB 和 A/B 是正交的**:每個 slot 有自己的 vbmeta,各驗各的。

## 2.6 Unlock 流程

```
Settings → 開發者選項 → OEM unlocking(寫 get_unlock_ability=1)
  ↓
fastboot flashing unlock
  ↓
LK 檢查 unlock ability → 顯示確認畫面 → 使用者按音量鍵確認
  ↓
強制 wipe userdata(這是規範要求,防止繞過鎖屏讀資料)
  ↓
狀態變 ORANGE
```

`get_unlock_ability` 這個 bit 存在防竄改區,就是為了防止「撿到別人手機直接 unlock 拿資料」。

## 2.7 常見問題與 Debug

| 症狀 | 方向 |
|---|---|
| `vbmeta verification failed` | 刷的 image 和 vbmeta 不匹配 — 常見於只刷 boot 沒刷 vbmeta |
| 刷了自編 kernel 就開不了 | vbmeta 的 hash descriptor 對不上;開發時用 `--disable-verity --disable-verification` 刷 vbmeta |
| 開機到一半 dm-verity error | hashtree 對不上,或 flash block 壞了 |
| Rollback index 錯誤,刷不回舊版 | 正常保護行為。已燒進 RPMB 的值降不回去 |
| 解鎖後某些 App 拒絕執行 | Attestation 帶 ORANGE,由 App 端判定 |

### 實用工具

```bash
# 看 vbmeta 內容與所有 descriptor
avbtool info_image --image vbmeta.img

# 看 boot.img 的 hash descriptor
avbtool info_image --image boot.img

# 開發用:關掉驗證
fastboot --disable-verity --disable-verification flash vbmeta vbmeta.img

# 查目前狀態
fastboot getvar unlocked
adb shell getprop ro.boot.verifiedbootstate
```

### 可以打開來讀的 code

LK 各家的 fork 不公開,但 AVB 那一段是共通的 — 廠商呼叫的就是下面這套參考實作,對著讀就能知道自家的 code 在做什麼 **[規範]**:

```
AOSP  external/avb/           ← libavb 參考實作 + avbtool + README(規範本體)
U-Boot doc/android/avb2.rst   ← 另一份獨立的 AVB 2.0 實作,可對照理解
```

`external/avb/README.md` 就是 AVB 2.0 的事實規範文件,值得從頭讀一遍[參考 1]。U-Boot 也有一套獨立的 AVB 2.0 實作與文件,拿來對照特別有助於分清「規範要求」與「某家的實作選擇」[參考 2][參考 13]。

---

# 學習路徑建議

1. **先把一次完整開機的 UART log 從頭到尾抓下來**,標出每一段是哪個階段、每段花多少時間。這一份 log 會變成你之後所有 debug 的基準。
2. **在 LK 加一行 print 並成功開機。** 走完 build → sign → flash → 看到自己的 log,整條 toolchain 就通了。
3. **讀 `avbtool info_image` 的輸出**,對照本文的 descriptor 表,把每個欄位對上。
4. **Preloader 部分先讀 log 再讀 code。** 先能看懂 calibration log 的 window 數字,再回頭看產生這些數字的 code,學習曲線會平緩很多。
5. **搞清楚簽章金鑰的管理流程長什麼樣** — 誰持有簽章 key、debug key 與 production key 怎麼分開。這是做任何 secure boot 相關工作前的前提知識,各家做法不同,以你所在專案的規定為準。

---

# 參考資料

## Android Verified Boot(規範等級)

1. [Android Verified Boot 2.0 — external/avb README](https://android.googlesource.com/platform/external/avb/+/master/README.md) — **AVB 2.0 的事實規範文件**。vbmeta 結構、三種 descriptor、rollback index、tamper-evident storage 要求全在這裡。優先讀這份。
2. [platform/external/avb — Git at Google](https://android.googlesource.com/platform/external/avb/) — libavb 參考實作與 `avbtool` 原始碼。
3. [Verified Boot | Android Open Source Project](https://source.android.com/docs/security/features/verifiedboot) — AOSP 官方 Verified Boot 總覽,含 rollback protection 說明。
4. [Boot flow | Android Open Source Project](https://source.android.com/docs/security/features/verifiedboot/boot-flow) — 四種 boot state 的判定條件與畫面行為(10 秒自動消失 vs 需按實體鍵)。
5. [Trusted Board Boot — Trusted Firmware-A docs](https://trustedfirmware-a.readthedocs.io/en/latest/design/firmware-design.html) / [trusted-board-boot.rst](https://github.com/ARM-software/arm-trusted-firmware/blob/master/docs/design/trusted-board-boot.rst) — BL1→BL2→BL3x 的驗證鏈、ROTPK、content certificate 的官方定義。

## MediaTek Boot 流程(社群 / 逆向)

6. [Rabbit R1 boot notes(MT6765)— DavidBuchanan314](https://github.com/DavidBuchanan314/rabbit_r1_boot_notes/) — **目前公開最清楚的一份 MTK 開機流程逆向筆記**。BROM → Preloader(SRAM 位址、AArch32)→ 載入並驗 lk/tee/gz 的流程都有。
7. [mtkclient — bkerler](https://github.com/bkerler/mtkclient) — 開源 MTK flash/repair 工具。想理解 BROM / Preloader download mode 的協定,讀這份 code 最快。

## MediaTek DRAM Init(★ 真正開源的 MTK 程式碼)

8. [coreboot/src/soc/mediatek/mt8183](https://github.com/coreboot/coreboot/tree/master/src/soc/mediatek/mt8183) — `dramc_pi_calibration_api.c`、`dramc_pi_basic_api.c`、`dramc_init_setting.c`、`dramc_param.c`。**MediaTek 官方貢獻的開源 DRAM calibration 實作。**
9. [coreboot/src/soc/mediatek/mt8173/dramc_pi_calibration_api.c](https://github.com/coreboot/coreboot/blob/master/src/soc/mediatek/mt8173/dramc_pi_calibration_api.c) — 較舊世代,程式碼較短,適合先看這份建立概念。
12. [coreboot gerrit: "soc/mediatek/mt8186: Support DRAM fast calibration using blob"](https://mail.coreboot.org/hyperkitty/list/coreboot-gerrit@coreboot.org/thread/MG4SQKVPRF6LM5E7A5TSKDNTXWVLZPES/) — Fast-K 機制的公開實作討論串。

## DRAM Training 原理

10. [LPDDR4 Workshop 2014: Training & Calibration | JEDEC](https://www.jedec.org/node/2817) — 官方 workshop 材料,涵蓋 write leveling、DQS2DQ training、tDQSCK drift。規範本體是 JESD209-4。
11. [Maximizing Mobile Performance with LPDDR4 SoC RAM | Synopsys](https://www.synopsys.com/blogs/chip-design/maximizing-mobile-performance-lpddr4-ram.html) — IP 廠角度的 LPDDR4 training 概觀,好讀。
    - 補充:[AN5723 — Guidelines for DDR configuration on STM32MP2(ST)](https://www.st.com/resource/en/application_note/an5723-guidelines-for-ddr-configuration-on-stm32mp2-mpus-stmicroelectronics.pdf) 是另一家 SoC 的 DDR 設定 application note,把 calibration 各步驟講得比多數資料清楚,概念可以橫向借用。

## 其他實作與對照

13. [Android Verified Boot 2.0 — Das U-Boot documentation](https://docs.u-boot.org/en/v2021.04/android/avb2.html) — U-Boot 的獨立 AVB 2.0 實作,含 RPMB / OP-TEE 的說明。
    - 搭配 [HKG18-124: Android Verified Boot 2.0 and U-Boot(Linaro)](https://static.linaro.org/connect/hkg18/presentations/hkg18-124.pdf) 這份簡報,圖解很清楚。
14. [A/B (seamless) system updates | AOSP](https://source.android.com/docs/core/ota/ab) — slot、priority、tries_remaining、successful 的定義。
15. [Implement A/B updates | AOSP](https://source.android.com/docs/core/ota/ab/ab_implement) — bootloader 端的實作要求與 fastboot slot 變數。
16. [Ramdisk partitions | AOSP](https://source.android.com/docs/core/architecture/partitions/ramdisk-partitions) — first-stage / second-stage init 與 ramdisk 的官方說明。

## 免責

除上列連結外,本文其餘內容(尤其 Part 1 標為 [推論] 的流程順序)是我依通用工程原理歸納的心智模型,**未經任何官方文件核對**,也不對應任何特定廠商的實際程式碼結構。本文不含任何非公開的原始碼路徑、參數或設計細節;要動手時請一律以你手上的官方文件與實機 log 為準。
