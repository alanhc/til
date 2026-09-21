---
title: "Android Generic Bootloader（GBL）介紹：用 UEFI 統一 Android 開機流程"
date: 2026-09-21
tags: [android, bootloader, uefi, edk2, gbl, avb, rust]
---

# Android Generic Bootloader（GBL）介紹：用 UEFI 統一 Android 開機流程

> TL;DR：GBL 是 Google 在 AOSP 開源、用 Rust 寫的 **UEFI application**。它把「Android 專屬的開機邏輯」（A/B slot、AVB、fastboot、kernel/DTB/bootconfig 組裝）從各家 SoC 的 bootloader 抽出來統一維護；SoC 廠商只需在底層韌體提供一組 UEFI protocol。Android 16 起，Google 建議 ARM64 裝置導入 Google 認證版本的 GBL。

---

## 1. 背景：Android bootloader 為什麼這麼碎

一台 Android 手機從上電到 kernel 起來，大致會經過：

```
BootROM → 早期 loader（SPL / Preloader / XBL…）→ TF-A (BL31) / TEE
        → 「Android bootloader」→ Linux kernel
```

最後那一段「Android bootloader」負責的事情跟 Android 高度綁定：

- 讀 misc / boot control 決定走哪個 **A/B slot**、是否進 recovery
- 用 **libavb** 驗證 `boot` / `vendor_boot` / `init_boot` / `vbmeta`，處理 rollback index
- 組裝 kernel cmdline、**bootconfig**、合併 DTB / DTBO
- 實作 **fastboot**

問題是，這一段歷來由各 SoC 廠商各自實作，而且底層框架也不同：

| 陣營 | Android bootloader 實作 |
|---|---|
| Qualcomm | ABL，一支基於 EDK2 的 UEFI app（早期為 LK） |
| MediaTek | LK（Little Kernel）系 |
| Intel x86 Android | kernelflinger（UEFI app） |
| 多數開發板 / Cuttlefish | U-Boot |

Google 在 LPC 2024 Android MC 的簡報中把痛點講得很直接 [3]：

- 韌體在各生態系碎片化，而 Android 的開機需求又變動頻繁
- 「Bootloader release cycle == ABL release cycle」——Android 的開機新功能要等每家廠商的 bootloader 釋出週期才能落地
- 每家廠商重複實作同樣的東西，且只有文件、缺少參考實作

## 2. GBL 是什麼

依官方文件 [1] 與 README [4]，GBL 是：

- 一個 **標準化、可更新的 bootloader**，目標是取代各家自行維護的 Android 開機邏輯
- **no_std Rust** 寫成的 **UEFI application**（`.efi`），由底層韌體載入執行
- 靜態連結可信任的共用元件，如 **libavb、libfdt、libufdt** [3]
- 支援架構：**x86_64、x86_32、aarch64、riscv64** [4]
- 用 **Bazel** 建置，原始碼位於 AOSP `platform/bootable/libbootloader` 的 `gbl/` 目錄 [4][5]

官方把 GBL 分成四塊 [1]：

1. **Core Android boot logic**：主迴圈、boot mode 判斷、kernel 載入
2. **Fastboot**
3. **Vendor extensions**：廠商自訂的 protocol 擴充
4. **UEFI protocol handlers**：block I/O、記憶體配置、RNG，以及 AVB / fastboot / slot 選擇等 Android 專屬 protocol

### 為什麼選 UEFI

簡報給的理由 [3]：

- 已經有量產裝置在用（例如 Qualcomm 的 XBL/ABL）
- UEFI 的 protocol 機制很適合拿來掛廠商特定邏輯
- 介面穩定（規格長年向後相容）
- 與 Arm **SystemReady** 方向一致

換句話說：**GBL 不在乎你底層是 EDK2 還是 U-Boot，只要你講 UEFI 就好**。

## 3. 架構：GBL 與韌體的分工

```
┌───────────────────────────────────────────┐
│ GBL (UEFI app, Rust, Google 維護/簽章)     │
│  - A/B slot 決策、AVB 驗證、fastboot        │
│  - 組 cmdline / bootconfig / DTB           │
└──────────────▲────────────────────────────┘
               │ UEFI Boot Services + GBL_EFI_* protocols
┌──────────────┴────────────────────────────┐
│ SoC 韌體（EDK2 / U-Boot EFI / 其他 UEFI 實作）│
│  - 儲存裝置、USB、RNG、secure storage        │
│  - 提供 public key、rollback index、slot metadata │
└───────────────────────────────────────────┘
```

### 韌體必須提供的 protocol

依「Deploy GBL」文件 [2]：

| Protocol | 用途 |
|---|---|
| `EFI_BLOCK_IO_PROTOCOL` / `EFI_BLOCK_IO2_PROTOCOL` | 從磁碟讀 boot image 與 pvmfw image |
| `EFI_RNG_PROTOCOL` | stack canary、KASLR seed、RNG seed |
| `EFI_SIMPLE_TEXT_OUTPUT_PROTOCOL` | log 輸出 |
| `GBL_EFI_AVB_PROTOCOL` | 取得 public key 與 rollback index，用於驗證 boot image |
| `GBL_EFI_BOOT_CONTROL_PROTOCOL` | 取得 slot metadata 與 boot reason |
| `GBL_EFI_AVF_PROTOCOL` | 從 DICE chain 產生 AVF（Android Virtualization Framework）設定資料 |
| Memory Allocation Services | AVB 與 DICE 計算用的暫存記憶體 |

GBL repo 的 `docs/` 目錄另外還有這些 protocol 的規格文件 [5]：`GBL_EFI_AB_SLOT_PROTOCOL`、`GBL_EFI_FASTBOOT_PROTOCOL`、`GBL_EFI_FASTBOOT_USB_PROTOCOL`、`GBL_EFI_IMAGE_LOADING_PROTOCOL`、`GBL_EFI_OS_CONFIGURATION_PROTOCOL`（讓廠商修改 DT / kernel cmdline / bootconfig [3]）。

> 注意：官方部署文件與 repo 文件對 slot 相關 protocol 的命名不完全一致（`BOOT_CONTROL` vs `AB_SLOT`），實作時以你所用 GBL release branch 的程式碼為準。

這個分工的設計重點是：**「政策」在 GBL，「機制」在韌體**。例如 AVB 的驗證流程由 GBL（libavb）做，但 key 放在哪、rollback index 存在 RPMB 還是 fuse，由韌體透過 `GBL_EFI_AVB_PROTOCOL` 回答。

## 4. 部署需求

依 [2]：

**分割區**

- 兩個 FAT 分割區：`android_esp_a`、`android_esp_b`，各至少 8 MB
- Partition type GUID 為標準 ESP：`C12A7328-F81F-11D2-BA4B-00A0C93EC93B`
- GBL 放在 `/EFI/BOOT/BOOTAA64.EFI`
- 兩個分割區都要有，才能支援 OTA 與 rollback

**簽章與更新**

- 量產要用對應 release branch 的 **Google 認證 production build**
- 保留 GBL 的憑證，不得在 binary 前加 header
- Developer build 只能用於開發
- OTA 必須整個分割區更新，不支援只更新 GBL

**韌體變數**

- 韌體要提供 UEFI 變數 `gbl_fw_api_level`（vendor GUID `5a6d92f3-a2d0-4083-91a1-a50f6c3d9830`），值要與 `ro.board.api_level` 一致

**時程**

- 自 Android 16 起，ARM64 裝置 **should** 部署最新的 Google 認證 GBL [1][2]。官方措辭是 "should"，不是硬性強制。

## 5. 動手玩

取得原始碼並建置 [2][4]：

```bash
repo init -u https://android.googlesource.com/kernel/manifest -b uefi-gbl-mainline
repo sync -j16
./tools/bazel run //bootable/libbootloader:gbl_efi_dist --extra_toolchains=@gbl//toolchain:all
```

在 QEMU x86_64 + OVMF 上跑，就是把產出的 EFI 放到 ESP 的預設路徑 [4]：

```bash
mkdir -p /tmp/esp/EFI/BOOT
cp <path to EFI image> /tmp/esp/EFI/BOOT/bootx64.efi
```

aarch64 用 AAVMF、riscv64 用 U-Boot。Cuttlefish 可直接指定 [4]：

```bash
cvd start --android_efi_loader=<path to EFI image>
```

## 6. 觀察與推論

> 以下是我的推論，不是官方說法。

- **對 Qualcomm 來說負擔最小**：本來就是 XBL (UEFI) + ABL (UEFI app)，某種程度上是把 ABL 換成 GBL。
- **對 LK / U-Boot 系的 SoC 負擔較大**：需要在現有韌體上補齊 UEFI 相容層，以及實作 `GBL_EFI_*` protocol。U-Boot 本身已有 EFI loader 子系統，是一條可能的路線；BayLibre 就發表過在 U-Boot 上跑 GBL 的實驗 [6]。
- **Bootloader 開始走向 GKI 模式**：跟 GKI 把 kernel 核心與廠商 module 分開很像，GBL 把 Android 開機政策收回 Google 手上，廠商只保留硬體相關的部分。未來 Android 的開機新功能（例如 AVF / pvmfw、DICE 相關需求）可以直接透過 GBL 更新推到生態系，不必再等各家 bootloader。
- **對工程師的意義**：以後讀開機問題的 log，可能要同時懂「韌體 UEFI 層」和「GBL 的 Rust 程式碼」兩邊。熟悉 UEFI protocol 的邊界會越來越重要。

## 參考資料

1. [Generic Bootloader (GBL) overview — AOSP](https://source.android.com/docs/core/architecture/bootloader/generic-bootloader)
2. [Deploy GBL — AOSP](https://source.android.com/docs/core/architecture/bootloader/generic-bootloader/gbl-dev)
3. Dmitrii Merkurev, [Android Generic Boot Loader](https://lpc.events/event/18/contributions/1704/attachments/1550/3231/Android%20Generic%20Boot%20Loader.pdf), Linux Plumbers Conference 2024, Android MC
4. [Generic Bootloader Library README](https://android.googlesource.com/platform/bootable/libbootloader/+/refs/heads/main/gbl/README.md)
5. [GBL docs 目錄（EFI protocols、A/B boot flow、fastboot 等）](https://android.googlesource.com/platform/bootable/libbootloader/+/refs/heads/main/gbl/docs/)
6. [Android bootflow: experiments with U-Boot and GBL — BayLibre](https://baylibre.com/android-bootflow-experiments-with-u-boot-and-gbl/)
