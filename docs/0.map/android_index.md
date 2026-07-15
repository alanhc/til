---
title: Android / Pixel 系列文章索引
sidebar_label: Android 系列索引
sidebar_position: 0
---

# Android / Pixel 系列文章索引

本頁整理知識庫中所有 Android、AOSP、Pixel 相關筆記，依主題分類。
名詞定義請參考 [Android 名詞表](android_glossary.md)。

---

## 一、入門與總覽

| 文章 | 內容 |
|---|---|
| [Android 平台架構](../android.md) | Android 五層架構圖、kernel 位置、booting 參考資料 |
| [Android 知識整理摘要](../分析/android-summary.md) | 跨筆記的總整理：架構、boot flow、AOSP 環境、ADB、Root |
| [Learning Pixel / Android 學習路線](../android_pixel_learning.md) | Step 1~5 學習規劃：從 Cuttlefish 編譯 → BeagleBone/RPi bring-up → GKI → MTE 除錯 → 效能對標 |

---

## 二、開機流程與 Bootloader

| 文章 | 內容 |
|---|---|
| [Android Boot Flow](../android_boot_flow.md) | 完整開機流程：Boot ROM → Bootloader → Kernel → Init → Zygote → System Server → Launcher，含 partition 結構與除錯方法 |
| [Bootloader](../bootloader.md) | Little Kernel (LK)、Aboot、PBL/SBL 兩階段 bootloader、SoC 廠商生態 |
| [ARM Trusted Firmware (ATF)](../atf.md) | BL1~BL33 各階段、Exception Level (EL0~EL3)、TrustZone、OP-TEE、Secure/Normal World、CCA 演進時間軸 |
| [ARM Trusted Firmware 元件](../arm_trust_firmware.md) | TF-A 主要元件：PSCI、SMC Dispatcher、SiP service、Root of Trust |

---

## 三、AOSP 建置

| 文章 | 內容 |
|---|---|
| [Pixel 8 AOSP 完整工作流程](../aosp_pixel_full_workflow.md) | **主線教學**：build ID ↔ AOSP tag ↔ vendor driver 三者對齊 → repo sync → vendor blob → lunch/m → fastboot flashall，含常見錯誤與救磚 |
| [Pixel 8 AOSP Full Workflow (EN)](../aosp_pixel_full_workflow_EN.md) | 上篇的英文版 |
| [Android Build Project](../android_build_project.md) | 環境套件安裝、repo init/sync、Cuttlefish 虛擬機建置、詞彙表（ACK、GKI、VNDK） |
| [AOSP Codebase](../aosp_codebase.md) | `.repo/manifests/default.xml` 查目前 branch revision |
| [Android Build Number 解析](../Android_build_number.md) | `BP4A.251205.006` 各欄位含義（代號／分支／日期／patch） |

---

## 四、Pixel 硬體與刷機

| 文章 | 內容 |
|---|---|
| [Pixel 硬體代號](../pixel_hardware.md) | `zuma` = Tensor G3 SoC、`shiba` = Pixel 8、kernel 分支 `android-gs-zuma-*` |
| [Pixel Study](../pixel_study.md) | 實作全紀錄：ADB 安裝、開發者模式、repo sync、lunch、flashall log、anti-rollback 錯誤、`flash-all.sh` 救磚 |
| [Pixel Fastboot Deep Dive](../pixel_fastboot_deepdive.md) | `fastboot flashall -w` 完整輸出逐行紀錄 |
| [Pixel Image 來源對照](../pixel_img.md) | 哪些 image 是 `m` build 出來的、哪些是 vendor blob、哪些是 Google 原廠 binary |
| [Pixel Flash Debug](../pixel_flash_debug.md) | `Failed to find AVB_MAGIC at offset: 0` 根因分析——不該加 `--disable-verity`，含成功 flash 紀錄 |
| [用 Android Flash Tool 刷不同版本](../pixel_flash_another_version.md) | 網頁版 flash.android.com 操作重點 |
| [Pixel Driver](../pixel_driver.md) | Root 權限與 kernel module 載入前置作業 |

---

## 五、Root 與權限

| 文章 | 內容 |
|---|---|
| [Pixel Root](../pixel_root.md) | Magisk（user-space，patch `init_boot.img`）vs KernelSU（kernel-space，改 `boot.img`）比較 |
| [Pixel 無法 adb root](../pixel_can_not_run_as_root.md) | `adbd cannot run as root in production builds` 的解法：Magisk patch init_boot，含 `/sys/class/` 節點列表 |

---

## 六、工具與除錯

| 文章 | 內容 |
|---|---|
| [adb（Android Debug Bridge）](../android_adb.md) | 常用指令速查、多裝置 `-s`、`adb root`/`remount`、無線除錯 |
| [Android SEPolicy / SELinux](../android_sepolicy.md) | 速查：Security context、`.te` 檔、`allow`/`neverallow`、AVC denied 判讀、`audit2allow` |
| [SELinux 是什麼？為什麼 Android 韌體工程師必須懂它](../selinux.md) | **深入版**：MAC vs DAC、LSM hooks / AVC / selinuxfs 元件、Treble 後的 sepolicy 四層架構、從 denial 反推 owner 的四種方法、為何是 CTS/GMS 出貨硬條件 |
| [效能實驗：Codec 判讀](../performance_experient.md) | YouTube debug overlay 判讀硬解／軟解、`[exo2]` vs `[plat]`、VP9 Profile 2 HDR fallback、掉幀分析 |

---

## 七、AI 與工作流

| 文章 | 內容 |
|---|---|
| [韌體開發與 Agentic AI](../android_firmware_development_and_agentic_ai.md) | 把 AOSP build pipeline 封裝成 AI Agent Skill、AI/人的介入邊界設計、三個真實踩坑紀錄 |
| [Android 工程師 Agent Skills 規劃](../android_engineer_skills.md) | 10 個適合系統整合團隊的 skill 提案（build 對齊、error triage、flash rescue、bring-up checklist、log analyzer 等） |

---

## 八、周邊

| 文章 | 內容 |
|---|---|
| [工程機](../工程機.md) | 高通工程機相關影片筆記 |

---

## 建議閱讀順序

**想從零 build 一個 Pixel ROM：**

```
Android Build Number 解析
   → Pixel 硬體代號
   → Pixel 8 AOSP 完整工作流程   ← 主線
   → Pixel Flash Debug（遇到 AVB 錯誤時）
   → Pixel Study（對照實作 log）
```

**想理解系統怎麼跑起來：**

```
Android 平台架構
   → Bootloader
   → ARM Trusted Firmware (ATF)
   → Android Boot Flow
   → Android SEPolicy
```
