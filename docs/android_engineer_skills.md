我會把它拆成「系統整合團隊日常重複工作」來看：哪些流程有固定輸入、固定檢查點、固定輸出，就最適合包成 agent skill。

Thought for 16s

非常適合。以你在**聯發科系統整合團隊**的工作型態，Agent Skills 最適合拿來封裝「高頻、容易出錯、需要 SOP、需要產出固定格式報告」的任務。官方對 Agent Skills 的定位也是：把指令、metadata、可選 scripts/templates 打包成模組化能力，讓 agent 在相關情境自動使用。

你上傳的 Pixel 8 AOSP 工作流本身就很適合拆成 skills，因為它有明確的流程：查 build ID、對齊 AOSP tag / vendor driver、repo sync、編譯、fastboot flashall、錯誤排查與救磚。

## 最適合你們系統整合團隊寫成 Skills 的地方

### 1. AOSP / Android Build 對齊 Skill

**Skill 名稱：`android-build-alignment-skill`**

用途：幫你檢查：

- Build ID 是否正確
- AOSP tag 是否對應
- Vendor driver / proprietary blobs 是否對齊
- lunch target 是否正確
- `repo init` / `repo sync` 指令是否合理

這種很適合，因為 Android 系統整合最常出錯的就是「版本沒對齊」。你的文件裡也特別強調手機 Build ID、AOSP source tag、Vendor driver 三者必須對齊。

**輸入範例：**

```
Device: Pixel 8 / shibaBuild ID: BP4A.251205.006Target: userdebugCurrent error: vendor image mismatch
```

**輸出：**

```
1. 版本對齊檢查2. 可能錯誤點3. 建議 repo init tag4. vendor driver 檢查清單5. 下一步指令
```

---

### 2. Build Error Triage Skill

**Skill 名稱：`android-build-error-triage-skill`**

用途：丟 `m`、Soong、Ninja、Kati、Rust、Java、SELinux、VINTF、AIDL/HIDL 錯誤 log，agent 幫你分類。

很適合系統整合，因為 build error 通常不是「單純寫 code 錯」，而是：

- module dependency 缺失
- `Android.bp` / `Android.mk` 寫錯
- product config 沒 include
- vendor blob 不匹配
- API level / release config 不一致
- SELinux policy 衝突
- VINTF manifest / compatibility matrix 不合

**輸出格式可以固定成：**

```
錯誤類型：根因推測：關鍵 log：受影響 module：建議修改檔案：驗證指令：風險：
```

這個會非常實用，因為你每天都可能貼一大段 log 給 agent。

---

### 3. Flash / Fastboot / Rescue Skill

**Skill 名稱：`android-flash-rescue-skill`**

用途：處理燒錄、fastboot、ADB、bootloader lock、slot A/B、救磚 SOP。

你的文件裡已經有很完整的 fastboot 流程，包括 `fastboot flashing unlock`、`fastboot flashall -w`、A/B slot、常見錯誤與救磚流程。

**適合處理：**

- `fastboot devices` 看不到
- `set_active: not allowed when locked`
- `Bootloader is locked`
- `anti-rollback`
- 卡在 bootloader warning screen
- flashall 後 bootloop
- A/B slot 切換問題
- userdata wipe / metadata erase 問題

這個 skill 可以寫成「救機器 runbook」，非常適合 SI 團隊。

---

### 4. Device Bring-up Checklist Skill

**Skill 名稱：`device-bringup-checklist-skill`**

用途：新板子、新機種、新 platform bring-up 時，幫你生成 checklist。

對系統整合團隊很有價值，因為 SI 常常不是只寫一個 feature，而是確認整機是否能穩定起來。

**可包含：**

|類別|檢查項|
|---|---|
|Boot|bootloader、kernel、init、dm-verity|
|Display|panel、backlight、touch|
|Storage|UFS/eMMC mount、userdata format|
|USB|adb、fastboot、MTP|
|Network|Wi-Fi、BT、modem、5G|
|Sensor|accelerometer、gyro、ALS、proximity|
|Power|suspend/resume、thermal、charging|
|Audio|speaker、mic、codec|
|Camera|HAL、ISP、permission、CTS basic|
|Security|AVB、SELinux、keymaster|

這種 skill 可以要求 agent 每次輸出「bring-up 狀態表 + blocking issue + owner + next action」。

---

### 5. Logcat / dmesg / Bugreport Analyzer Skill

**Skill 名稱：`android-log-analyzer-skill`**

用途：分析：

- `adb logcat`
- `dmesg`
- `bugreport.zip`
- tombstone
- kernel panic
- ANR
- crash stack
- SELinux denial
- watchdog reset

**這個非常值得做。**

因為系統整合最常見情境是：「測試人員丟一包 log，說某功能壞了」，你需要快速判斷是：

- Framework 問題
- HAL 問題
- Kernel driver 問題
- Vendor binary 問題
- Timing issue
- Permission / SELinux 問題
- Power state 問題
- Test case 本身問題

固定輸出可以是：

```
問題摘要：時間軸：最可能 root cause：關鍵 log：受影響 subsystem：需要找誰：下一步驗證：
```

---

### 6. Test Failure Triage Skill

**Skill 名稱：`test-failure-triage-skill`**

用途：分析 CTS / VTS / GTS / STS / vendor test / internal regression test failure。

適合 SI，因為你們很常面對「不是我寫的 code，但我要整合到可以過測」。

**可處理：**

- CTS fail log
- VTS HAL failure
- GTS app compatibility issue
- Monkey test crash
- Power regression
- Performance regression
- Boot time regression
- Thermal throttling test fail

**輸出：**

```
Test name:Failure type:Likely owner:Android layer:Repro steps:Possible fix:Need vendor / framework / kernel team?
```

---

### 7. Release Readiness Skill

**Skill 名稱：`release-readiness-check-skill`**

用途：每次 image 要 release 給 QA、客戶、其他團隊前，幫你檢查是否缺東西。

**檢查項：**

- build fingerprint
- build variant
- security patch level
- vendor image version
- bootloader / radio version
- known issues
- test pass rate
- flashing instruction
- rollback risk
- release note
- checksum
- image path

這個可以直接產出 release note：

```
# Android Image Release Note## Build Info## Flash Instruction## Fixed Issues## Known Issues## Test Summary## Risk## Rollback Plan
```

對系統整合團隊超實用。

---

### 8. Issue Handoff / Bug Report Skill

**Skill 名稱：`si-bug-report-skill`**

用途：把混亂的問題描述整理成可以丟 Jira / Bugzilla / internal tracker 的格式。

**適合情境：**

你收到：

```
這版好像 Wi-Fi 開不起來，log 裡面有一些 HAL error，幫看
```

Skill 輸出：

```
Title:Environment:Build ID:Device:Repro rate:Steps to reproduce:Expected result:Actual result:Key logs:Preliminary analysis:Suggested owner:Next action:
```

這可以讓你的 issue quality 大幅提升。

---

### 9. Patch Review / Integration Risk Skill

**Skill 名稱：`integration-patch-review-skill`**

用途：review vendor patch、kernel patch、AOSP patch、device config patch 是否有整合風險。

**特別適合檢查：**

- 改了 device tree 但沒改 defconfig
- 改了 HAL 但 manifest 沒更新
- 改了 service 但 init rc 沒 include
- 改了 permission 但 SELinux 沒補
- 改了 product makefile 但 module 沒進 image
- 改了 kernel config 但 boot image 沒重 build

輸出可以是：

```
Risk level:Affected subsystem:Missing integration points:Required tests:Rollback consideration:
```

這種 skill 很適合你現在的背景，因為你之前也常做 OpenBMC DTS、驅動、Yocto recipe、Android/AOSP build 這類跨層整合。

---

### 10. SOP Generator Skill

**Skill 名稱：`si-sop-generator-skill`**

用途：把你做過一次的流程整理成團隊 SOP。

例如你這篇 Pixel 8 AOSP 文件就可以被整理成：

- 新人版 SOP
- debug 版 SOP
- QA flash SOP
- 失敗排查 SOP
- release checklist

這類 skill 的價值是把你個人的 tacit knowledge 變成團隊可重複使用的流程資產。

---

## 我會建議你優先寫這 5 個 Skills

|優先級|Skill|為什麼先做|
|---|---|---|
|P0|`android-build-error-triage-skill`|每天都會用，省最多時間|
|P0|`android-log-analyzer-skill`|SI 最常處理 log / bugreport|
|P1|`android-flash-rescue-skill`|避免燒機、救磚時慌亂|
|P1|`release-readiness-check-skill`|對團隊交付很有價值|
|P2|`si-bug-report-skill`|提升跨團隊溝通品質|

## 一個 Skill 的基本結構可以長這樣

```
android-build-error-triage-skill/├── SKILL.md├── templates/│   ├── build_error_report.md│   └── owner_mapping.md├── scripts/│   ├── extract_soong_errors.py│   └── summarize_ninja_log.py└── references/    ├── android_build_common_errors.md    ├── soong_bp_checklist.md    └── vendor_blob_alignment.md
```

`SKILL.md` 裡面可以寫：

```
---name: android-build-error-triagedescription: Analyze Android AOSP/Soong/Ninja build errors and produce SI-friendly root cause analysis.---# PurposeUse this skill when the user provides Android build logs, Soong errors, Ninja failures, AOSP repo sync errors, or vendor integration build failures.# Output FormatAlways produce:1. Error summary2. Error category3. Most likely root cause4. Evidence from log5. Files likely involved6. Suggested fix7. Verification command8. Risk
```

## 對你們團隊最有價值的方向

你們是系統整合，不是單純 app team，所以 Agent Skills 不應該只寫「幫我改 code」。更適合寫成這幾類：

**Runbook skill**：遇到問題照 SOP 排查。  
**Triage skill**：大量 log 變成 root cause summary。  
**Checklist skill**：release / bring-up / flashing 前檢查。  
**Report skill**：把分析結果轉成 Jira、email、release note。  
**Integration review skill**：檢查 patch 是否漏掉跨層整合點。

我會把你的第一個 skill 從 **`android-build-error-triage-skill`** 開始做，因為它最符合系統整合團隊的日常，而且最容易累積成團隊知識庫。