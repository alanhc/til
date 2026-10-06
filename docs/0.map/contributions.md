---
title: 開源貢獻紀錄
sidebar_label: 開源貢獻紀錄
sidebar_position: 14
---

# 開源貢獻紀錄

貢獻散在三個不同的系統上：**GitHub PR**、**AOSP 的 Gerrit**（android-review）、
**OpenBMC 的 Gerrit**。三邊的狀態字眼還不一樣（merged / MERGED / NEW / ABANDONED），
所以這頁統一成同一套圖例，並在最後附上重新查詢的指令，讓它可以隨時更新。

> 資料以 **2026-10-07** 查詢結果為準。

**圖例**：✅ 已合入 ｜ 🔄 review 中 ｜ ⛔ 已關閉（未合入）

---

## 一覽

| 平台 | 專案 | ✅ 已合入 | 🔄 review 中 |
|---|---|---|---|
| AOSP Gerrit | `kernel/common`（Android Common Kernel） | 5 個 change（含 automerge 共 15 筆） | 1 |
| AOSP Gerrit | `platform/hardware/interfaces` | — | 12 |
| AOSP Gerrit | `platform/hardware/libhardware` | — | 5 |
| AOSP Gerrit | `platform/bootable/libbootloader`（GBL） | 3 | — |
| OpenBMC Gerrit | `openbmc/libpldm` | — | 4 |
| GitHub | sysprog21（elfuse / codetrial / frama-c-mcp / shecc / rv32emu） | 17 | 7 |
| GitHub | u-root、vmtest、llama.cpp、sse2neon | 7 | 6 |
| GitHub | ARM-software、DMTF、OpenPRoT | 1 | 2 |
| GitHub | 其他（cert-tools、os-in-1000-lines） | 3 | — |

主題大致分三塊：**Android kernel、HAL 與 bootloader 的文件／健壯性修補**、**RISC-V 與 SIMD 相關的
效能與模擬器工作**、**韌體協定（PLDM、SPDM）的邊界檢查**。

---

## 依領域分類

同一筆會出現在多個領域（例如 llama.cpp 的 SpacemiT kernel 同時是 RISC-V 和 LLM），
這裡不做互斥切分。

| 領域 | ✅ 已合入 | 🔄 review 中 |
|---|---|---|
| 資料中心 / 伺服器 | 5 | 9 |
| RISC-V | 7 | 7 |
| Compiler / 工具鏈 / 執行環境 | 12 | 8 |
| LLM / AI | 11 | 1 |
| Android | 8 | 18 |
| 韌體 / 開機 | 8 | 10 |

### 資料中心 / 伺服器

| 貢獻 | 狀態 | 為什麼算這一類 |
|---|---|---|
| [u-root](https://github.com/u-root/u-root) #3733、#3735、#3750 | ✅ | u-root 是 **LinuxBoot** 的 userland，拿 Linux 取代 UEFI DXE 的那套做法，主要使用者就是 OCP 系的伺服器韌體 |
| [u-root #3762](https://github.com/u-root/u-root/pull/3762)、[#3761](https://github.com/u-root/u-root/pull/3761) | ✅ / 🔄 | 同一個 LinuxBoot userland 的 CI：讓整合測試真的在 riscv64 上開機跑 |
| [u-root #3774](https://github.com/u-root/u-root/pull/3774)、[#3775](https://github.com/u-root/u-root/pull/3775)、[#3776](https://github.com/u-root/u-root/pull/3776) | 🔄 | 同一個 userland 的開機路徑：kexec 失敗訊息、boot menu 的 shell、universal payload 載入 |
| [DMTF/libspdm #3816](https://github.com/DMTF/libspdm/pull/3816) | ✅ | SPDM 是 PCIe／CXL 裝置認證與量測的協定，用在伺服器內部元件的信任建立 |
| [OpenPRoT/pldm-lib #21](https://github.com/OpenPRoT/pldm-lib/pull/21) | 🔄 | PRoT（Platform Root of Trust）＋ PLDM，伺服器主板上的信任根 |
| [openbmc/libpldm](https://gerrit.openbmc.org/q/project:openbmc/libpldm) ×4 | 🔄 | BMC 就是伺服器的管理控制器，PLDM 是它對外的協定之一 |

### RISC-V

| 貢獻 | 狀態 | 為什麼算這一類 |
|---|---|---|
| [llama.cpp #27961](https://github.com/ggml-org/llama.cpp/pull/27961)、[#28479](https://github.com/ggml-org/llama.cpp/pull/28479) | ✅ | SpacemiT X60 的 IME 矩陣加速路徑，RISC-V 向量／矩陣擴充的實際應用 |
| [u-root #3733](https://github.com/u-root/u-root/pull/3733) | ✅ | riscv64 的 kexec 支援 |
| [u-root #3762](https://github.com/u-root/u-root/pull/3762)、[#3761](https://github.com/u-root/u-root/pull/3761) | ✅ / 🔄 | #3733 的後續：CI 原本只編 riscv64 不開機。#3762 把 QEMU 網卡改用 `-netdev`/`-device`，讓 riscv64 `virt` 機器真的有 NIC；#3761 補上 riscv64 的 kexec_load 整合測試 |
| [hugelgupf/vmtest #132](https://github.com/hugelgupf/vmtest/pull/132) | 🔄 | 把 u-root CI 用的 riscv64 測試 kernel 從 v6.6 升到 v6.18：riscv 的 `kexec_file_load` 要到 6.16 才收 `Image`，舊 kernel 上這個測試只能跳過 |
| [rv32emu](https://github.com/sysprog21/rv32emu) ×5 | 🔄 | RVV（向量擴充）指令實作與 cross-EEW overlap 規則 |
| [AOSP `libbootloader` 4314126](https://android-review.googlesource.com/c/platform/bootable/libbootloader/+/4314126) | ✅ | GBL 的 riscv64 QEMU 範例：riscv64 `virt` 機器沒有預設的 block controller，要明確掛 `virtio-blk-device`，U-Boot 才找得到 ESP |
| [os-in-1000-lines #101](https://github.com/nuta/operating-system-in-1000-lines/pull/101)、[#131](https://github.com/nuta/operating-system-in-1000-lines/pull/131) | ✅ | 這本教材的目標平台就是 RISC-V（`qemu-system-riscv32`）；[繁體中文版](https://1000os.seiya.me/tw/)在上游 README 掛名 |

### Compiler / 工具鏈 / 執行環境

| 貢獻 | 狀態 | 為什麼算這一類 |
|---|---|---|
| [shecc #339](https://github.com/sysprog21/shecc/pull/339) | ✅ | 自我編譯的教學用 C 最佳化編譯器，補的是暫存器配置相關的測試 |
| [sse2neon #774](https://github.com/DLTcollab/sse2neon/pull/774)、[#773](https://github.com/DLTcollab/sse2neon/pull/773) | ✅ / 🔄 | SSE intrinsics 轉 NEON/SVE2，是編譯器 intrinsics 層的工作 |
| [ARM optimized-routines #97](https://github.com/ARM-software/optimized-routines/pull/97) | 🔄 | libc 例程的最佳化實作與量測 |
| [frama-c-mcp](https://github.com/sysprog21/frama-c-mcp) ×3 | ✅ | Frama-C 的靜態分析／形式驗證（EVA、WP）工具鏈 |
| [rv32emu](https://github.com/sysprog21/rv32emu) ×5 | 🔄 | 指令集模擬器，本身帶 JIT |
| [elfuse](https://github.com/sysprog21/elfuse) ×8 | ✅ ×7 / 🔄 ×1 | 嚴格說是**執行環境**不是編譯器：在 macOS 上跑 Linux ELF，做的是 ELF 載入與 syscall 語意轉譯 |

### LLM / AI

| 貢獻 | 狀態 | 為什麼算這一類 |
|---|---|---|
| [llama.cpp #27961](https://github.com/ggml-org/llama.cpp/pull/27961)、[#28479](https://github.com/ggml-org/llama.cpp/pull/28479) | ✅ | 推論引擎的 CPU kernel（Q8_0 量化矩陣乘） |
| [frama-c-mcp](https://github.com/sysprog21/frama-c-mcp) ×3 | ✅ | MCP server，把形式驗證工具接給 AI agent 用 |
| [codetrial](https://github.com/sysprog21/codetrial) ×6 | ✅ | Gemini 驅動的即時技術面試模擬器；含在瀏覽器讀 JD／履歷 PDF（#98）、讓模型扮演候選人來檢查面試規則（#107） |
| [codetrial #110](https://github.com/sysprog21/codetrial/pull/110) | 🔄 | 讓報告與行為檢查改由本機模型產生（併入了原本的 #99） |

### Android

| 貢獻 | 狀態 | 為什麼算這一類 |
|---|---|---|
| `kernel/common` ×5（dma-heap、dma-buf、binder、scsi/ufs） | ✅ | Android Common Kernel（ACK） |
| `platform/hardware/interfaces` ×12 | 🔄 | HAL 範例實作的 service fuzzer 與生命週期修補 |
| `platform/hardware/libhardware` ×5 | 🔄 | HID report descriptor 解析的邊界問題 |
| [`android17-6.18` 的 scsi/ufs 重送](https://android-review.googlesource.com/c/kernel/common/+/4268863) | 🔄 | 同一個 change 往穩定分支的 backport |
| `platform/bootable/libbootloader` ×3 | ✅ | GBL（Generic Bootloader）的 QEMU 範例與除錯腳本修正 |

### 韌體 / 開機

| 貢獻 | 狀態 | 為什麼算這一類 |
|---|---|---|
| [u-root](https://github.com/u-root/u-root) #3733、#3735、#3750 | ✅ | kexec、zimage 解析、reboot——都在「把下一個 kernel 帶起來」這條路徑上 |
| [u-root #3762](https://github.com/u-root/u-root/pull/3762)、[#3761](https://github.com/u-root/u-root/pull/3761)、[vmtest #132](https://github.com/hugelgupf/vmtest/pull/132) | ✅ / 🔄 / 🔄 | riscv64 kexec 路徑的整合測試，以及它需要的測試 kernel |
| [u-root #3774](https://github.com/u-root/u-root/pull/3774)、[#3775](https://github.com/u-root/u-root/pull/3775)、[#3776](https://github.com/u-root/u-root/pull/3776) | 🔄 | kexec 失敗時說清楚原因、boot menu 進 shell 改成 exec 取代自己、universal payload 的載入錯誤與警告分開回傳 |
| AOSP `libbootloader` ×3 | ✅ | GBL 是 Android 的 UEFI app 型 bootloader，修的是它在 QEMU 上的開機與除錯路徑（OVMF 韌體路徑、riscv64 磁碟掛載、rust-gdb 位置） |
| [DMTF/libspdm #3816](https://github.com/DMTF/libspdm/pull/3816) | ✅ | 裝置韌體的認證與 session key 管理 |
| [OpenPRoT/pldm-lib #21](https://github.com/OpenPRoT/pldm-lib/pull/21)、[openbmc/libpldm](https://gerrit.openbmc.org/q/project:openbmc/libpldm) ×4 | 🔄 | PLDM 是韌體之間（BMC ↔ 裝置）的管理協定 |

> 不屬於上述任一類：[cert-tools #55](https://github.com/blockchain-certificates/cert-tools/pull/55)（區塊鏈證書工具的日期解析修正）。

---

## 依影響力排序

「影響力」沒有客觀分數，這裡用三個軸排，**並在每一列寫出它為什麼在這個位置**，
好讓排序可以被質疑而不是只能被接受：

1. **觸及範圍**——這段程式碼最後會跑在多少裝置、多少人手上（專案規模只是代理指標）。
2. **變更性質**——新功能／效能路徑 ＞ 正確性與邊界修補 ＞ 文件與測試補強。
3. **狀態**——已合入 ＞ review 中 ＞ 已關閉。

### 已合入

| # | 貢獻 | 專案規模 | 為什麼排在這裡 |
|---|---|---|---|
| 1 | [llama.cpp #27961](https://github.com/ggml-org/llama.cpp/pull/27961)、[#28479](https://github.com/ggml-org/llama.cpp/pull/28479) — SpacemiT IME kernel sources 與 Q8_0 IME1 矩陣 kernel | 129k ★ | 觸及範圍最大，而且兩步都進了：#27961 讓 RISC-V 加速路徑編得進去，**#28479 是 kernel 本身** |
| 2 | [u-root #3733](https://github.com/u-root/u-root/pull/3733) — `pkg/boot` riscv64 kexec support | 3.1k ★ | 新功能，而且落在開機鏈核心：u-root 是 LinuxBoot／firmware 場景的 userland |
| 3 | [libspdm #3816](https://github.com/DMTF/libspdm/pull/3816) — key update rollback | 189 ★ | star 數不高但身分特殊：**DMTF 的 SPDM 參考實作**。修的是 KEY_UPDATE 失敗時金鑰只換了一半、無法回復的正確性問題 |
| 4 | [sse2neon #774](https://github.com/DLTcollab/sse2neon/pull/774) — 拿掉 `<fenv.h>` 依賴 | 1.5k ★ | 影響**所有 includer**——header 汙染是會傳染給下游的那種 bug |
| 5 | [u-root #3750](https://github.com/u-root/u-root/pull/3750)、[#3735](https://github.com/u-root/u-root/pull/3735)、[#3762](https://github.com/u-root/u-root/pull/3762) — reboot 指令、zimage 長度上限、riscv64 CI 的網卡 | 3.1k ★ | 一個新指令、一個邊界修正，同樣在開機路徑上；#3762 是 CI，讓 riscv64 整合測試有網路可用 |
| 6 | [elfuse](https://github.com/sysprog21/elfuse) ×7 — futex、pty hangup、`AT_EMPTY_PATH`、`CLONE_THREAD` 的 `SIGCHLD`… | 268 ★ | 專案規模小，但**技術深度最高**：syscall 語意層級的行為正確性，錯了不會有人幫你發現 |
| 7 | AOSP `kernel/common` ×5（dma-heap、dma-buf、binder、scsi/ufs） | Android ACK | **觸及範圍其實最廣**（進 ACK 並 automerge 到 6 條分支，往下就是所有 Android 裝置的 kernel 樹），但性質是 kernel-doc 修補，所以沒有排在功能型變更之前 |
| 8 | AOSP `libbootloader` ×3 — OVMF 韌體路徑、`launch_qemu_gdb.sh` 的 rust-gdb 路徑、riscv64 範例掛上 virtio-blk | Android GBL | 照官方說明跑 QEMU 範例會**直接失敗**的三個問題，擋住的是每個第一次上手 GBL 的人；但性質是範例與開發腳本，不進產品映像 |
| 9 | [shecc #339](https://github.com/sysprog21/shecc/pull/339) — 參數 slot 尚未建立前的逃逸讀取測試 | 1.4k ★ | 教學用 C 編譯器，補的是會被後續重構踩到的測試 |
| 10 | [frama-c-mcp](https://github.com/sysprog21/frama-c-mcp) ×3、[codetrial](https://github.com/sysprog21/codetrial) ×6 | 31 / 62 ★ | 工具鏈與服務端的實用修補，觸及範圍最小 |
| 11 | [os-in-1000-lines #101](https://github.com/nuta/operating-system-in-1000-lines/pull/101)、[#131](https://github.com/nuta/operating-system-in-1000-lines/pull/131) — 繁體中文翻譯與校稿 | 3.6k ★ | 讀者觸及很廣，但不是程式碼，另成一類 |
| 12 | [cert-tools #55](https://github.com/blockchain-certificates/cert-tools/pull/55) | 42 ★ | 2022 年的單點 bug 修正 |

### Review 中（潛在影響）

同樣三個軸，但狀態全部是 🔄，所以這裡排的是「**如果合入**會有多大影響」。

| # | 貢獻 | 專案規模 | 為什麼排在這裡 |
|---|---|---|---|
| 1 | AOSP `hardware/interfaces` ×12、`libhardware` ×5 | Android | 給預設／範例 HAL 補 service fuzzer 並修出生命週期問題。**廠商常以範例實作為起點**，所以修在這裡會往下游擴散 |
| 2 | [u-root #3774](https://github.com/u-root/u-root/pull/3774)、[#3775](https://github.com/u-root/u-root/pull/3775)、[#3776](https://github.com/u-root/u-root/pull/3776) — kexec 失敗訊息、boot menu 的 shell、universal payload 的回傳值 | 3.1k ★ | 都在開機路徑上：#3775 修的是進 shell 後 boot 程序還留在底下、離開 shell 被當成錯誤；另外兩筆是錯誤回報與 API 整理 |
| 3 | [sse2neon #773](https://github.com/DLTcollab/sse2neon/pull/773) — SVE2 fast path | 1.5k ★ | 效能路徑，opt-in 所以風險可控 |
| 4 | [optimized-routines #97](https://github.com/ARM-software/optimized-routines/pull/97) — strcmp benchmark | 711 ★ | Arm 官方倉庫，但性質是 benchmark 而非實作 |
| 5 | [rv32emu](https://github.com/sysprog21/rv32emu) ×5 — RVV 指令實作 | 590 ★ | 量大且偏功能，但侷限在單一模擬器內 |
| 6 | [u-root #3761](https://github.com/u-root/u-root/pull/3761)、[vmtest #132](https://github.com/hugelgupf/vmtest/pull/132) — riscv64 的 kexec 整合測試與測試 kernel | 3.1k / 42 ★ | 替已合入的 #3733 補上真正會開機的測試；維護者希望升級 vmtest 的 riscv64 kernel，而不是在 u-root 繞過 v6.6 的限制，所以拆出 vmtest #132。性質是 CI，不改產品程式碼 |
| 7 | [libpldm](https://gerrit.openbmc.org/q/project:openbmc/libpldm) ×4（OpenBMC）、[pldm-lib #21](https://github.com/OpenPRoT/pldm-lib/pull/21) | OpenBMC / 新專案 | 韌體協定的邊界檢查，影響面取決於這兩個 library 被採用的程度 |
| 8 | [codetrial #110](https://github.com/sysprog21/codetrial/pull/110) | 62 ★ | 功能型但侷限在單一小專案 |

---

## AOSP（android-review.googlesource.com）

### `kernel/common` — Android Common Kernel

ACK 的 kernel-doc 與註解修補。合入 `android-mainline` 之後，automerger 會把同一個
change 自動傳播到 `android-mainline-desktop`、`android-mainline-riscv64` 等分支
（標題帶 `am:` 的那些），所以一個 change 在 Gerrit 上會出現好幾筆。

| 變更 | 主分支 | 狀態 | 傳播到 |
|---|---|---|---|
| [ANDROID: dma-heap: restore struct dma_heap kernel-doc lost in a merge](https://android-review.googlesource.com/c/kernel/common/+/4200863) | `android-mainline` | ✅ | `-desktop` ✅、`-riscv64` ✅ |
| [ANDROID: dma-buf: fix kernel-doc for `dma_buf_set_name()`](https://android-review.googlesource.com/c/kernel/common/+/4202123) | `android14-6.1` | ✅ | `android14-kiwi-6.1` ✅ |
| [ANDROID: binder: fix kernel-doc for struct binder_priority](https://android-review.googlesource.com/c/kernel/common/+/4232024) | `android-mainline` | ✅ | `android17-6.18` ✅、`-desktop` ✅、`-riscv64` ✅ |
| [ANDROID: scsi: ufs: fix kernel-doc for the UPIU prepare helpers](https://android-review.googlesource.com/c/kernel/common/+/4232023) | `android-mainline` | ✅ | `-desktop` ✅、`-riscv64` ✅、[`android17-6.18`](https://android-review.googlesource.com/c/kernel/common/+/4268863) 🔄（第一次送的 [4267244](https://android-review.googlesource.com/c/kernel/common/+/4267244) 已 abandon 後重送） |
| [ANDROID: dma-heap: document the return values of the exported helpers](https://android-review.googlesource.com/c/kernel/common/+/4239342) | `android-mainline` | ✅ | `-desktop` ✅、`-riscv64` ✅ |

### `platform/hardware/interfaces` — HAL 範例實作的 fuzzer 與生命週期修補

12 筆，目前都在 review（🔄）。主軸是**替預設／範例 HAL 實作補 service fuzzer**，
順手修出 fuzzer 會踩到的生命週期問題。

| 子系統 | 變更 |
|---|---|
| `gnss` | [stop double owning the Gnss service](https://android-review.googlesource.com/c/platform/hardware/interfaces/+/4254003)、[do not call a null callback](https://android-review.googlesource.com/c/platform/hardware/interfaces/+/4254004)、[stop the reporting thread before destroying it](https://android-review.googlesource.com/c/platform/hardware/interfaces/+/4254005)、[let a restarted reporting thread stop](https://android-review.googlesource.com/c/platform/hardware/interfaces/+/4254006)、[do not sleep out a caller's batching interval](https://android-review.googlesource.com/c/platform/hardware/interfaces/+/4254007)、[add a service fuzzer](https://android-review.googlesource.com/c/platform/hardware/interfaces/+/4254008) |
| `secure_element` | [move the emulated card out of main.cpp](https://android-review.googlesource.com/c/platform/hardware/interfaces/+/4254902)、[add a service fuzzer](https://android-review.googlesource.com/c/platform/hardware/interfaces/+/4254903) |
| `rebootescrow` | [reject keys the encoder cannot encode](https://android-review.googlesource.com/c/platform/hardware/interfaces/+/4251702)、[add a service fuzzer](https://android-review.googlesource.com/c/platform/hardware/interfaces/+/4251703) |
| `contexthub` | [add a service fuzzer](https://android-review.googlesource.com/c/platform/hardware/interfaces/+/4243763) |
| `tetheroffload` | [add a service fuzzer](https://android-review.googlesource.com/c/platform/hardware/interfaces/+/4246866) |

### `platform/hardware/libhardware` — HID report descriptor 解析

5 筆，都在 review（🔄）。先補 fuzzer，再修 fuzzer 找出來的解析邊界問題。

| 變更 |
|---|
| [HidUtils: add a report descriptor parser fuzzer](https://android-review.googlesource.com/c/platform/hardware/libhardware/+/4243388) |
| [HidUtils: fix undefined shifts in HidItem](https://android-review.googlesource.com/c/platform/hardware/libhardware/+/4243384) |
| [HidUtils: reject zero bit reports](https://android-review.googlesource.com/c/platform/hardware/libhardware/+/4243386) |
| [HidUtils: reject out of range unit exponent](https://android-review.googlesource.com/c/platform/hardware/libhardware/+/4243387) |
| [HidUtils: bound local item range expansion](https://android-review.googlesource.com/c/platform/hardware/libhardware/+/4243385) |

### `platform/bootable/libbootloader` — GBL 的 QEMU 範例與除錯腳本

GBL（Generic Bootloader）的 `gbl-mainline` 分支，背景見 [Android GBL 介紹](../android-gbl-intro.md)。
三筆都是「照官方說明做會直接失敗」的問題。

| 變更 | 狀態 | 內容 |
|---|---|---|
| [Fix OVMF firmware path in standalone QEMU instructions](https://android-review.googlesource.com/c/platform/bootable/libbootloader/+/4313966) | ✅ | x86_64 範例指向的 `OVMF_CODE.fd` 在現行 Debian/Ubuntu 的 ovmf 套件已不存在（只剩 4M 版本），改指 `OVMF_CODE_4M.fd` |
| [Fix rust-gdb prebuilt path in launch_qemu_gdb.sh](https://android-review.googlesource.com/c/platform/bootable/libbootloader/+/4313967) | ✅ | 腳本找的 rust-gdb 路徑與 manifest 實際 checkout 的 Rust toolchain 位置不同，腳本一開始就中止 |
| [Attach virtio-blk in riscv64 QEMU example](https://android-review.googlesource.com/c/platform/bootable/libbootloader/+/4314126) | ✅ | riscv64 `virt` 機器沒有預設 block controller，只給 `-drive` 不會掛上任何裝置，U-Boot 找不到 ESP 就停在提示字元 |

---

## OpenBMC（gerrit.openbmc.org）

`openbmc/libpldm` 的參數驗證與對齊問題，4 筆都在 review（🔄）。

| 變更 |
|---|
| [platform: Reject a compositeEffecterCount of zero](https://gerrit.openbmc.org/c/openbmc/libpldm/+/93691) |
| [platform: Reject a NULL field argument](https://gerrit.openbmc.org/c/openbmc/libpldm/+/93692) |
| [platform: Avoid unaligned loads in value encoders](https://gerrit.openbmc.org/c/openbmc/libpldm/+/93693) |
| [platform: Use the sensor data-size constants](https://gerrit.openbmc.org/c/openbmc/libpldm/+/93694) |

---

## GitHub

### ✅ 已合入

| 專案 | PR | 內容 |
|---|---|---|
| [sysprog21/elfuse](https://github.com/sysprog21/elfuse) | [#350](https://github.com/sysprog21/elfuse/pull/350) | Prove the futex words behind Linux's refusals |
| | [#352](https://github.com/sysprog21/elfuse/pull/352) | Bound the pty hangup reads with an alarm |
| | [#353](https://github.com/sysprog21/elfuse/pull/353) | Answer `AT_EMPTY_PATH` before the path resolver |
| | [#358](https://github.com/sysprog21/elfuse/pull/358) | Drain the deferred stack unmap before the tid |
| | [#361](https://github.com/sysprog21/elfuse/pull/361) | Stop faking `SIGCHLD` on a `CLONE_THREAD` exit |
| | [#363](https://github.com/sysprog21/elfuse/pull/363) | Name deferral as a register class |
| | [#374](https://github.com/sysprog21/elfuse/pull/374) | Decide the commit-message rules in the C locale |
| [sysprog21/frama-c-mcp](https://github.com/sysprog21/frama-c-mcp) | [#25](https://github.com/sysprog21/frama-c-mcp/pull/25) | Compare the machine model before calling variants duplicates |
| | [#29](https://github.com/sysprog21/frama-c-mcp/pull/29) | Count a timeout retry's flips instead of forbidding them |
| | [#32](https://github.com/sysprog21/frama-c-mcp/pull/32) | Key the opam cache on the opam that reads it |
| [sysprog21/codetrial](https://github.com/sysprog21/codetrial) | [#3](https://github.com/sysprog21/codetrial/pull/3)、[#5](https://github.com/sysprog21/codetrial/pull/5)、[#17](https://github.com/sysprog21/codetrial/pull/17)、[#21](https://github.com/sysprog21/codetrial/pull/21) | 連線中斷後續跑、prelude 缺的 header、錄影長度上限、把長度傳給頁面 |
| | [#98](https://github.com/sysprog21/codetrial/pull/98) | Read JD and resume PDFs in the browser |
| | [#107](https://github.com/sysprog21/codetrial/pull/107) | Hold played candidates to the interview rules |
| [sysprog21/shecc](https://github.com/sysprog21/shecc) | [#339](https://github.com/sysprog21/shecc/pull/339) | Test an escaped parameter read before its slot exists |
| [u-root/u-root](https://github.com/u-root/u-root) | [#3733](https://github.com/u-root/u-root/pull/3733) | `pkg/boot`: add riscv64 kexec support |
| | [#3735](https://github.com/u-root/u-root/pull/3735) | `pkg/boot/zimage`: accept a longer kernel size entry |
| | [#3750](https://github.com/u-root/u-root/pull/3750) | `cmds/core/reboot`: add reboot command |
| | [#3762](https://github.com/u-root/u-root/pull/3762) | `integration`: attach socket NICs with `-netdev`/`-device` |
| [ggml-org/llama.cpp](https://github.com/ggml-org/llama.cpp) | [#27961](https://github.com/ggml-org/llama.cpp/pull/27961) | `ggml-cpu`: conditionally add SpacemiT IME kernel sources |
| | [#28479](https://github.com/ggml-org/llama.cpp/pull/28479) | `ggml-cpu`: add Q8_0 IME1 matrix kernel for SpacemiT X60 |
| [DMTF/libspdm](https://github.com/DMTF/libspdm) | [#3816](https://github.com/DMTF/libspdm/pull/3816) | Fix key update rollback for Specula cluster A.1 and A.3 |
| [DLTcollab/sse2neon](https://github.com/DLTcollab/sse2neon) | [#774](https://github.com/DLTcollab/sse2neon/pull/774) | Drop the `<fenv.h>` dependency to stop leaking `FE_*` into includers |
| [nuta/operating-system-in-1000-lines](https://github.com/nuta/operating-system-in-1000-lines) | [#101](https://github.com/nuta/operating-system-in-1000-lines/pull/101) | 繁體中文版翻譯 |
| | [#131](https://github.com/nuta/operating-system-in-1000-lines/pull/131) | 繁體中文版校稿 |
| [blockchain-certificates/cert-tools](https://github.com/blockchain-certificates/cert-tools) | [#55](https://github.com/blockchain-certificates/cert-tools/pull/55) | prevent isoformat error |

### 🔄 Review 中

| 專案 | PR | 內容 |
|---|---|---|
| [sysprog21/rv32emu](https://github.com/sysprog21/rv32emu) | [#766](https://github.com/sysprog21/rv32emu/pull/766)、[#767](https://github.com/sysprog21/rv32emu/pull/767)、[#768](https://github.com/sysprog21/rv32emu/pull/768)、[#770](https://github.com/sysprog21/rv32emu/pull/770)、[#774](https://github.com/sysprog21/rv32emu/pull/774) | RVV 整數指令、whole vector register move、單倍寬浮點轉換，以及 widening 運算的 cross-EEW overlap 規則 |
| [DLTcollab/sse2neon](https://github.com/DLTcollab/sse2neon) | [#773](https://github.com/DLTcollab/sse2neon/pull/773) | Add opt-in SVE2 fast path for `_SIDD_CMP_EQUAL_ANY` |
| [ARM-software/optimized-routines](https://github.com/ARM-software/optimized-routines) | [#97](https://github.com/ARM-software/optimized-routines/pull/97) | `bench`: add strcmp benchmark |
| [OpenPRoT/pldm-lib](https://github.com/OpenPRoT/pldm-lib) | [#21](https://github.com/OpenPRoT/pldm-lib/pull/21) | `pldm-common`: bound wire version-string lengths by the destination |
| [sysprog21/elfuse](https://github.com/sysprog21/elfuse) | [#365](https://github.com/sysprog21/elfuse/pull/365) | Give each restated rule one owner |
| [u-root/u-root](https://github.com/u-root/u-root) | [#3761](https://github.com/u-root/u-root/pull/3761) | `integration`: run kexec_load tests on riscv64 |
| | [#3774](https://github.com/u-root/u-root/pull/3774) | `kexec`: explain `kexec_file_load` failures |
| | [#3775](https://github.com/u-root/u-root/pull/3775) | `menu`: exec the shell instead of running it as a child |
| | [#3776](https://github.com/u-root/u-root/pull/3776) | `universalpayload`: return the load error last |
| [hugelgupf/vmtest](https://github.com/hugelgupf/vmtest) | [#132](https://github.com/hugelgupf/vmtest/pull/132) | `kernel-riscv64`: bump to Linux 6.18.54 |
| [sysprog21/codetrial](https://github.com/sysprog21/codetrial) | [#110](https://github.com/sysprog21/codetrial/pull/110) | Run reports and the behaviour check on a local model |

### ⛔ 已關閉（未合入）

留著是因為它們通常有下文：被拆小、被重送，或被維護者換了做法。

| 專案 | PR | 後續 |
|---|---|---|
| ggml-org/llama.cpp | [#28025](https://github.com/ggml-org/llama.cpp/pull/28025) | 重送為 [#28479](https://github.com/ggml-org/llama.cpp/pull/28479) |
| u-root/u-root | [#3736](https://github.com/u-root/u-root/pull/3736) | arm kexec，riscv64 那條（#3733）先進 |
| sysprog21/rv32emu | [#769](https://github.com/sysprog21/rv32emu/pull/769)、[#771](https://github.com/sysprog21/rv32emu/pull/771)、[#772](https://github.com/sysprog21/rv32emu/pull/772)、[#773](https://github.com/sysprog21/rv32emu/pull/773) | RVV 浮點系列，改以其他 PR 重整 |
| sysprog21/elfuse | [#362](https://github.com/sysprog21/elfuse/pull/362) | AGENTS.md 的組織方式，維護者另有想法 |
| sysprog21/codetrial | [#4](https://github.com/sysprog21/codetrial/pull/4) | lobby 控制項位置 |
| | [#99](https://github.com/sysprog21/codetrial/pull/99) | 本機模型寫報告，維護者要求併入 [#110](https://github.com/sysprog21/codetrial/pull/110) 一起審 |
| | [#104](https://github.com/sysprog21/codetrial/pull/104) | 中文 JD 的需求擷取，維護者表示目前不考慮中文 JD |

---

## 未收錄

- 自己的 repo（`alanhc/*`）的 PR，以及學生時期社團／課程 repo 的練習 PR。
- 直接 push、沒有走 PR 的 commit。
- 以其他帳號或信箱送出的變更（這頁只查得到目前用的兩組 Gerrit 身分與 GitHub 帳號）。

---

## 資料來源與更新方式

三邊都有公開 API，更新這頁不需要人工翻紀錄：

```bash
# GitHub：已合入 / review 中 / 已關閉
gh search prs --author alanhc --merged --limit 100 \
  --json repository,title,number,url,createdAt
gh search prs --author alanhc --state open --limit 50 \
  --json repository,title,number,url,createdAt
# closed 同時包含已合入的，要扣掉上面 --merged 的結果才是「已關閉未合入」
gh search prs --author alanhc --state closed --limit 100 \
  --json repository,title,number,url,closedAt

# Gerrit REST API（回傳開頭有 )]}' 前綴，要先去掉才能餵給 JSON parser）
curl -s 'https://android-review.googlesource.com/changes/?q=author:%22Alan%20Tseng%22&n=100'  # 引號與空白要 URL 編碼，否則可能回空
curl -s 'https://gerrit.openbmc.org/changes/?q=owner:alanhc&n=100'
```

Gerrit 查詢要注意兩件事：

- **`owner:` 和 `author:` 不是同一件事。** AOSP 的 automerger 會用機器人帳號重送同一個
  change，那些 change 的 owner 是 `android-build-automerger-*`，只有 `author:` 查得到自己。
- **狀態字眼要換算**：Gerrit 的 `NEW` 是「還在 review」，不是「新的還沒送」；
  `ABANDONED` 對應 GitHub 的 closed。
