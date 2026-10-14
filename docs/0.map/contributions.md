---
title: 開源貢獻紀錄
sidebar_label: 開源貢獻紀錄
sidebar_position: 14
---

# 開源貢獻紀錄

貢獻散在四個不同的系統上：**GitHub PR**、**AOSP 的 Gerrit**（android-review）、
**OpenBMC 的 Gerrit**，以及 Linux 和 U-Boot 的 **mailing list**（用 patchwork 追蹤）。
各邊的狀態字眼還不一樣（merged / MERGED / NEW / ABANDONED / New / RFC），
所以這頁統一成同一套圖例，並在最後附上重新查詢的指令，讓它可以隨時更新。

> 資料以 **2026-10-14** 查詢結果為準。

**圖例**：✅ 已合入 ｜ 🔄 review 中 ｜ ⏸ 暫停（等前置條件或併入別的討論） ｜ ⛔ 已關閉（未合入）

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
| GitHub | u-root、vmtest、llama.cpp、sse2neon | 8 | 5 |
| GitHub | ARM-software、DMTF、OpenPRoT | 3 | 5 |
| GitHub | triton-cpu、spine-triton、UCAgent | 3 | 3 |
| GitHub | 其他（cert-tools、os-in-1000-lines） | 3 | — |
| Mailing list | Linux（dma-buf、SpacemiT K1 DT） | — | 3 |
| Mailing list | U-Boot（SpacemiT K1） | — | —（⏸ 2） |

主題大致分四塊：**Android kernel、HAL 與 bootloader 的文件／健壯性修補**、**RISC-V 與 SIMD 相關的
效能與模擬器工作**、**韌體協定（PLDM、SPDM）的邊界檢查**，以及新開的 **Triton CPU backend**。

---

## 依領域分類

同一筆會出現在多個領域（例如 llama.cpp 的 SpacemiT kernel 同時是 RISC-V 和 LLM），
這裡不做互斥切分。

| 領域 | ✅ 已合入 | 🔄 review 中 |
|---|---|---|
| 資料中心 / 伺服器 | 8 | 11 |
| RISC-V | 7 | 10 |
| Compiler / 工具鏈 / 執行環境 | 15 | 9 |
| LLM / AI | 14 | 4 |
| Android | 8 | 18 |
| 韌體 / 開機 | 11 | 14 |

### 資料中心 / 伺服器

| 貢獻 | 狀態 | 為什麼算這一類 |
|---|---|---|
| [u-root](https://github.com/u-root/u-root) #3733、#3735、#3750 | ✅ | u-root 是 **LinuxBoot** 的 userland，拿 Linux 取代 UEFI DXE 的那套做法，主要使用者就是 OCP 系的伺服器韌體 |
| [u-root #3762](https://github.com/u-root/u-root/pull/3762)、[#3761](https://github.com/u-root/u-root/pull/3761) | ✅ / 🔄 | 同一個 LinuxBoot userland 的 CI：讓整合測試真的在 riscv64 上開機跑 |
| [u-root #3774](https://github.com/u-root/u-root/pull/3774)、[#3775](https://github.com/u-root/u-root/pull/3775)、[#3776](https://github.com/u-root/u-root/pull/3776) | ✅ / 🔄 / 🔄 | 同一個 userland 的開機路徑：kexec 失敗訊息、boot menu 的 shell、universal payload 載入 |
| [DMTF/libspdm #3816](https://github.com/DMTF/libspdm/pull/3816)、[#4087](https://github.com/DMTF/libspdm/pull/4087) | ✅ | SPDM 是 PCIe／CXL 裝置認證與量測的協定，用在伺服器內部元件的信任建立 |
| [DMTF/libspdm #4088](https://github.com/DMTF/libspdm/pull/4088)、[#4122](https://github.com/DMTF/libspdm/pull/4122) | 🔄 | 同一套 SPDM 參考實作的演算法協商：協商失敗時把已寫入的選擇還原 |
| [OpenPRoT/pldm-lib #21](https://github.com/OpenPRoT/pldm-lib/pull/21) | ✅ | PRoT（Platform Root of Trust）＋ PLDM，伺服器主板上的信任根 |
| [OpenPRoT/pldm-lib #32](https://github.com/OpenPRoT/pldm-lib/pull/32)、[#33](https://github.com/OpenPRoT/pldm-lib/pull/33) | 🔄 | #21 的後續：解碼失敗也要回應、descriptor 字串長度的邊界 |
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
| [spine-triton #38](https://github.com/spacemit-com/spine-triton/pull/38) | 🔄 | SpacemiT 的 Triton backend：X60 的 `xsmtvdot` 擴充名稱寫錯，在 K1 上實測才發現 |
| [Linux：K1 DT 標 `bootph-pre-ram`](https://patchwork.kernel.org/project/linux-riscv/patch/20261012235624.77993-2-alan.tseng.cs@gmail.com/) ×2 | 🔄 | 讓 SpacemiT K1 的 SPL 需要的節點直接寫在 Linux 的 device tree 裡，U-Boot 不必再自己補 |
| U-Boot：[Milk-V Jupiter](https://patchwork.ozlabs.org/project/uboot/patch/20261012151530.1564771-1-alan.tseng.cs@gmail.com/)、[SDHCI 不再依賴 `max-frequency`](https://patchwork.ozlabs.org/project/uboot/patch/20261013084448.433298-2-alan.tseng.cs@gmail.com/) | ⏸ | 把 Jupiter 板子加進 mainline U-Boot；前者等上面的 Linux DT 先進，後者併入既有的 mmc 討論 |

### Compiler / 工具鏈 / 執行環境

| 貢獻 | 狀態 | 為什麼算這一類 |
|---|---|---|
| [shecc #339](https://github.com/sysprog21/shecc/pull/339) | ✅ | 自我編譯的教學用 C 最佳化編譯器，補的是暫存器配置相關的測試 |
| [sse2neon #774](https://github.com/DLTcollab/sse2neon/pull/774)、[#773](https://github.com/DLTcollab/sse2neon/pull/773) | ✅ / 🔄 | SSE intrinsics 轉 NEON/SVE2，是編譯器 intrinsics 層的工作 |
| [ARM optimized-routines #97](https://github.com/ARM-software/optimized-routines/pull/97) | 🔄 | libc 例程的最佳化實作與量測 |
| [frama-c-mcp](https://github.com/sysprog21/frama-c-mcp) ×3 | ✅ | Frama-C 的靜態分析／形式驗證（EVA、WP）工具鏈 |
| [rv32emu](https://github.com/sysprog21/rv32emu) ×5 | 🔄 | 指令集模擬器，本身帶 JIT |
| [elfuse](https://github.com/sysprog21/elfuse) ×8 | ✅ ×7 / 🔄 ×1 | 嚴格說是**執行環境**不是編譯器：在 macOS 上跑 Linux ELF，做的是 ELF 載入與 syscall 語意轉譯 |
| [triton-cpu](https://github.com/triton-lang/triton-cpu) #324、#329、#330 | ✅ | Triton 的 CPU backend（MLIR lowering）：`tl.histogram` 的 mask、沒有原生 bf16 指令時 fp32→bf16 的 round-to-nearest-even、多開 43 個測試 |
| [spine-triton #38](https://github.com/spacemit-com/spine-triton/pull/38) | 🔄 | Triton backend 傳給 LLVM 的 `-mattr` 名稱 |

### LLM / AI

| 貢獻 | 狀態 | 為什麼算這一類 |
|---|---|---|
| [llama.cpp #27961](https://github.com/ggml-org/llama.cpp/pull/27961)、[#28479](https://github.com/ggml-org/llama.cpp/pull/28479) | ✅ | 推論引擎的 CPU kernel（Q8_0 量化矩陣乘） |
| [frama-c-mcp](https://github.com/sysprog21/frama-c-mcp) ×3 | ✅ | MCP server，把形式驗證工具接給 AI agent 用 |
| [codetrial](https://github.com/sysprog21/codetrial) ×6 | ✅ | Gemini 驅動的即時技術面試模擬器；含在瀏覽器讀 JD／履歷 PDF（#98）、讓模型扮演候選人來檢查面試規則（#107） |
| [codetrial #110](https://github.com/sysprog21/codetrial/pull/110) | 🔄 | 讓報告與行為檢查改由本機模型產生（併入了原本的 #99） |
| [triton-cpu](https://github.com/triton-lang/triton-cpu) #324、#329、#330 | ✅ | Triton 是寫 GPU／AI kernel 的語言與編譯器，PyTorch `torch.compile` 的 kernel 就是用它產生 |
| [spine-triton #38](https://github.com/spacemit-com/spine-triton/pull/38) | 🔄 | 同一套 Triton，跑在 SpacemiT 的 AI CPU 上 |
| [XS-MLVP/UCAgent](https://github.com/XS-MLVP/UCAgent) #140、#141 | 🔄 | 用 LLM agent 做晶片單元驗證（香山／UnityChip）；補上 PR 測試的 CI，並讓 skill script 用 agent 自己的 Python 跑 |

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
| [u-root #3774](https://github.com/u-root/u-root/pull/3774)、[#3775](https://github.com/u-root/u-root/pull/3775)、[#3776](https://github.com/u-root/u-root/pull/3776) | ✅ / 🔄 / 🔄 | kexec 失敗時說清楚原因、boot menu 進 shell 改成 exec 取代自己、universal payload 的載入錯誤與警告分開回傳 |
| AOSP `libbootloader` ×3 | ✅ | GBL 是 Android 的 UEFI app 型 bootloader，修的是它在 QEMU 上的開機與除錯路徑（OVMF 韌體路徑、riscv64 磁碟掛載、rust-gdb 位置） |
| [DMTF/libspdm #3816](https://github.com/DMTF/libspdm/pull/3816)、[#4087](https://github.com/DMTF/libspdm/pull/4087) | ✅ | 裝置韌體的認證與 session key 管理；#4087 是 #3816 review 時答應補的測試 |
| [DMTF/libspdm #4088](https://github.com/DMTF/libspdm/pull/4088)、[#4122](https://github.com/DMTF/libspdm/pull/4122) | 🔄 | Responder 與 Requester 兩側的 NEGOTIATE_ALGORITHMS 失敗還原 |
| [OpenPRoT/pldm-lib #21](https://github.com/OpenPRoT/pldm-lib/pull/21) | ✅ | PLDM 是韌體之間（BMC ↔ 裝置）的管理協定 |
| [OpenPRoT/pldm-lib #32](https://github.com/OpenPRoT/pldm-lib/pull/32)、[#33](https://github.com/OpenPRoT/pldm-lib/pull/33)、[openbmc/libpldm](https://gerrit.openbmc.org/q/project:openbmc/libpldm) ×4 | 🔄 | 同上 |
| [Linux：K1 DT 標 `bootph-pre-ram`](https://patchwork.kernel.org/project/linux-riscv/patch/20261012235624.77993-2-alan.tseng.cs@gmail.com/) ×2 | 🔄 | 標出 SPL 階段就要用到的節點（時脈、UART、SD／eMMC、SPI NOR），讓 U-Boot 直接沿用 Linux 的 DT |
| U-Boot：Milk-V Jupiter、SDHCI `max-frequency` RFC | ⏸ | 見下方 [Mailing list](#mailing-list) |

> 不屬於上述任一類：[cert-tools #55](https://github.com/blockchain-certificates/cert-tools/pull/55)（區塊鏈證書工具的日期解析修正）、
> [Linux dma-buf 的 kernel-doc](https://patchwork.kernel.org/project/dri-devel/patch/20260902135923.3599022-1-alan.tseng.cs@gmail.com/)（和 AOSP 那筆修同一段文件）。

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
| 3 | [libspdm #3816](https://github.com/DMTF/libspdm/pull/3816)、[#4087](https://github.com/DMTF/libspdm/pull/4087) — key update rollback 與它的測試 | 191 ★ | star 數不高但身分特殊：**DMTF 的 SPDM 參考實作**。修的是 KEY_UPDATE 失敗時金鑰只換了一半、無法回復的正確性問題；#4087 是 review 時答應補的 callback 順序測試 |
| 4 | [triton-cpu #329](https://github.com/triton-lang/triton-cpu/pull/329)、[#330](https://github.com/triton-lang/triton-cpu/pull/330)、[#324](https://github.com/triton-lang/triton-cpu/pull/324) — histogram 的 mask、沒有 avx512bf16 時 bf16 的 RNE、多開 43 個測試 | 214 ★（上游 triton 20k ★） | 兩個都是**算錯數字**的正確性 bug，而且 CI（GNR、Arm）抓不到，只有在沒有 AVX-512 的 x86 上才會出現；triton-cpu 直接 merge 進上游，作者身分保留 |
| 5 | [sse2neon #774](https://github.com/DLTcollab/sse2neon/pull/774) — 拿掉 `<fenv.h>` 依賴 | 1.5k ★ | 影響**所有 includer**——header 汙染是會傳染給下游的那種 bug |
| 6 | [u-root #3750](https://github.com/u-root/u-root/pull/3750)、[#3735](https://github.com/u-root/u-root/pull/3735)、[#3774](https://github.com/u-root/u-root/pull/3774)、[#3762](https://github.com/u-root/u-root/pull/3762) — reboot 指令、zimage 長度上限、kexec 失敗訊息、riscv64 CI 的網卡 | 3.1k ★ | 一個新指令、一個邊界修正、一個錯誤回報，同樣在開機路徑上；#3762 是 CI，讓 riscv64 整合測試有網路可用 |
| 7 | [elfuse](https://github.com/sysprog21/elfuse) ×7 — futex、pty hangup、`AT_EMPTY_PATH`、`CLONE_THREAD` 的 `SIGCHLD`… | 268 ★ | 專案規模小，但**技術深度最高**：syscall 語意層級的行為正確性，錯了不會有人幫你發現 |
| 8 | AOSP `kernel/common` ×5（dma-heap、dma-buf、binder、scsi/ufs） | Android ACK | **觸及範圍其實最廣**（進 ACK 並 automerge 到 6 條分支，往下就是所有 Android 裝置的 kernel 樹），但性質是 kernel-doc 修補，所以沒有排在功能型變更之前 |
| 9 | AOSP `libbootloader` ×3 — OVMF 韌體路徑、`launch_qemu_gdb.sh` 的 rust-gdb 路徑、riscv64 範例掛上 virtio-blk | Android GBL | 照官方說明跑 QEMU 範例會**直接失敗**的三個問題，擋住的是每個第一次上手 GBL 的人；但性質是範例與開發腳本，不進產品映像 |
| 10 | [pldm-lib #21](https://github.com/OpenPRoT/pldm-lib/pull/21) — wire 上版本字串長度以目的端為上限 | 2 ★ | 韌體協定的邊界檢查，性質重要但專案還很新，採用面有限 |
| 11 | [shecc #339](https://github.com/sysprog21/shecc/pull/339) — 參數 slot 尚未建立前的逃逸讀取測試 | 1.4k ★ | 教學用 C 編譯器，補的是會被後續重構踩到的測試 |
| 12 | [frama-c-mcp](https://github.com/sysprog21/frama-c-mcp) ×3、[codetrial](https://github.com/sysprog21/codetrial) ×6 | 31 / 62 ★ | 工具鏈與服務端的實用修補，觸及範圍最小 |
| 13 | [os-in-1000-lines #101](https://github.com/nuta/operating-system-in-1000-lines/pull/101)、[#131](https://github.com/nuta/operating-system-in-1000-lines/pull/131) — 繁體中文翻譯與校稿 | 3.6k ★ | 讀者觸及很廣，但不是程式碼，另成一類 |
| 14 | [cert-tools #55](https://github.com/blockchain-certificates/cert-tools/pull/55) | 42 ★ | 2022 年的單點 bug 修正 |

### Review 中（潛在影響）

同樣三個軸，但狀態全部是 🔄，所以這裡排的是「**如果合入**會有多大影響」。

| # | 貢獻 | 專案規模 | 為什麼排在這裡 |
|---|---|---|---|
| 1 | AOSP `hardware/interfaces` ×12、`libhardware` ×5 | Android | 給預設／範例 HAL 補 service fuzzer 並修出生命週期問題。**廠商常以範例實作為起點**，所以修在這裡會往下游擴散 |
| 2 | [Linux：K1 DT 標 `bootph-pre-ram`](https://patchwork.kernel.org/project/linux-riscv/patch/20261012235624.77993-2-alan.tseng.cs@gmail.com/) ×2 | Linux mainline | 進了就是 mainline kernel 的 DT，所有 K1 板子的 U-Boot SPL 都會沿用；也是 U-Boot 那邊 Jupiter patch 的前置條件 |
| 3 | [libspdm #4088](https://github.com/DMTF/libspdm/pull/4088)、[#4122](https://github.com/DMTF/libspdm/pull/4122) — NEGOTIATE_ALGORITHMS 失敗時還原已協商的演算法 | 191 ★ | SPDM 參考實作的狀態一致性；#4122 是維護者在 #4088 review 時指出 Requester 端也有同樣問題後補的 |
| 4 | [u-root #3775](https://github.com/u-root/u-root/pull/3775)、[#3776](https://github.com/u-root/u-root/pull/3776) — boot menu 的 shell、universal payload 的回傳值 | 3.1k ★ | 都在開機路徑上：#3775 修的是進 shell 後 boot 程序還留在底下、離開 shell 被當成錯誤；#3776 是 API 整理 |
| 5 | [sse2neon #773](https://github.com/DLTcollab/sse2neon/pull/773) — SVE2 fast path | 1.5k ★ | 效能路徑，opt-in 所以風險可控 |
| 6 | [optimized-routines #97](https://github.com/ARM-software/optimized-routines/pull/97) — strcmp benchmark | 711 ★ | Arm 官方倉庫，但性質是 benchmark 而非實作 |
| 7 | [rv32emu](https://github.com/sysprog21/rv32emu) ×5 — RVV 指令實作 | 590 ★ | 量大且偏功能，但侷限在單一模擬器內 |
| 8 | [u-root #3761](https://github.com/u-root/u-root/pull/3761)、[vmtest #132](https://github.com/hugelgupf/vmtest/pull/132) — riscv64 的 kexec 整合測試與測試 kernel | 3.1k / 42 ★ | 替已合入的 #3733 補上真正會開機的測試；維護者希望升級 vmtest 的 riscv64 kernel，而不是在 u-root 繞過 v6.6 的限制，所以拆出 vmtest #132。性質是 CI，不改產品程式碼 |
| 9 | [libpldm](https://gerrit.openbmc.org/q/project:openbmc/libpldm) ×4（OpenBMC）、[pldm-lib #32](https://github.com/OpenPRoT/pldm-lib/pull/32)、[#33](https://github.com/OpenPRoT/pldm-lib/pull/33) | OpenBMC / 新專案 | 韌體協定的邊界檢查，影響面取決於這兩個 library 被採用的程度 |
| 10 | [UCAgent #140](https://github.com/XS-MLVP/UCAgent/pull/140)、[#141](https://github.com/XS-MLVP/UCAgent/pull/141) — PR 跑測試的 CI、skill script 用對 Python | 230 ★ | 晶片驗證 agent；#140 順手修了 main 上兩個已經壞掉的測試 |
| 11 | [spine-triton #38](https://github.com/spacemit-com/spine-triton/pull/38) — `xsmtvdot` 名稱與範例的 import | 15 ★ | 修的是 X60 矩陣擴充根本開不起來的問題，但專案剛開源、使用者少 |
| 12 | [Linux dma-buf kernel-doc](https://patchwork.kernel.org/project/dri-devel/patch/20260902135923.3599022-1-alan.tseng.cs@gmail.com/) | Linux mainline | 和 AOSP 已合入那筆修同一段文件；性質是文件修補，至今沒有回應 |
| 13 | [codetrial #110](https://github.com/sysprog21/codetrial/pull/110) | 62 ★ | 功能型但侷限在單一小專案 |

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

## Mailing list

Linux 和 U-Boot 不收 PR，patch 用 `git send-email` 寄到 mailing list，狀態看
patchwork（[kernel.org](https://patchwork.kernel.org/)、[ozlabs](https://patchwork.ozlabs.org/project/uboot/list/)）。
patchwork 的 `New` 只代表「還沒有人改狀態」，不等於有人在看。

| 專案 | Patch | 狀態 | 後續 |
|---|---|---|---|
| Linux（riscv / devicetree） | [riscv: dts: spacemit: k1: mark boot-critical SoC nodes bootph-pre-ram](https://patchwork.kernel.org/project/linux-riscv/patch/20261012235624.77993-2-alan.tseng.cs@gmail.com/)、[mark K1 board boot devices bootph-pre-ram](https://patchwork.kernel.org/project/linux-riscv/patch/20261012235624.77993-3-alan.tseng.cs@gmail.com/) | 🔄 | U-Boot reviewer 希望 SPL 用的 `bootph-pre-ram` 先進 Linux 的 DT，再讓 U-Boot 沿用，所以先送這組 |
| Linux（dma-buf） | [dma-buf: fix stale return value documentation for dma_buf_set_name()](https://patchwork.kernel.org/project/dri-devel/patch/20260902135923.3599022-1-alan.tseng.cs@gmail.com/) | 🔄 | 與 AOSP 已合入的那筆修的是同一段 kernel-doc；linux-media 的 patchwork 標成 Not Applicable（dma-buf 走 drm-misc），dri-devel 上還沒有回應 |
| U-Boot（SpacemiT K1） | [spacemit: k1: add Milk-V Jupiter](https://patchwork.ozlabs.org/project/uboot/patch/20261012151530.1564771-1-alan.tseng.cs@gmail.com/) | ⏸ | 等上面的 Linux DT 進了再送 v2。實機測試時發現 SPL 認不得板上的 GigaDevice SPI NOR，v2 要一起修 |
| U-Boot（SpacemiT K1） | [RFC: mmc: k1: do not require max-frequency in the device tree](https://patchwork.ozlabs.org/project/uboot/patch/20261013084448.433298-2-alan.tseng.cs@gmail.com/) ×2 | ⏸ | 維護者指出已經有一串討論在處理同一件事，請改到那邊繼續，不要另開 thread |

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
| | [#3774](https://github.com/u-root/u-root/pull/3774) | `kexec`: explain `kexec_file_load` failures |
| [triton-lang/triton-cpu](https://github.com/triton-lang/triton-cpu) | [#324](https://github.com/triton-lang/triton-cpu/pull/324) | Enable 43 more `test_core.py` tests on the CPU backend |
| | [#329](https://github.com/triton-lang/triton-cpu/pull/329) | Honor the mask in `tl.histogram` |
| | [#330](https://github.com/triton-lang/triton-cpu/pull/330) | Round fp32 to bf16 to nearest even without native support |
| [ggml-org/llama.cpp](https://github.com/ggml-org/llama.cpp) | [#27961](https://github.com/ggml-org/llama.cpp/pull/27961) | `ggml-cpu`: conditionally add SpacemiT IME kernel sources |
| | [#28479](https://github.com/ggml-org/llama.cpp/pull/28479) | `ggml-cpu`: add Q8_0 IME1 matrix kernel for SpacemiT X60 |
| [DMTF/libspdm](https://github.com/DMTF/libspdm) | [#3816](https://github.com/DMTF/libspdm/pull/3816) | Fix key update rollback for Specula cluster A.1 and A.3 |
| | [#4087](https://github.com/DMTF/libspdm/pull/4087) | Assert the exact key update callback sequence in KEY_UPDATE tests |
| [OpenPRoT/pldm-lib](https://github.com/OpenPRoT/pldm-lib) | [#21](https://github.com/OpenPRoT/pldm-lib/pull/21) | `pldm-common`: bound wire version-string lengths by the destination |
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
| [OpenPRoT/pldm-lib](https://github.com/OpenPRoT/pldm-lib) | [#32](https://github.com/OpenPRoT/pldm-lib/pull/32) | `pldm-interface`: answer requests that fail to decode |
| | [#33](https://github.com/OpenPRoT/pldm-lib/pull/33) | `pldm-common`: bound descriptor and downstream string lengths |
| [DMTF/libspdm](https://github.com/DMTF/libspdm) | [#4088](https://github.com/DMTF/libspdm/pull/4088) | Restore negotiated algorithms when NEGOTIATE_ALGORITHMS fails |
| | [#4122](https://github.com/DMTF/libspdm/pull/4122) | Restore negotiated algorithms when the ALGORITHMS response is rejected |
| [sysprog21/elfuse](https://github.com/sysprog21/elfuse) | [#365](https://github.com/sysprog21/elfuse/pull/365) | Give each restated rule one owner |
| [u-root/u-root](https://github.com/u-root/u-root) | [#3761](https://github.com/u-root/u-root/pull/3761) | `integration`: run kexec_load tests on riscv64 |
| | [#3775](https://github.com/u-root/u-root/pull/3775) | `menu`: exec the shell instead of running it as a child |
| | [#3776](https://github.com/u-root/u-root/pull/3776) | `universalpayload`: return the load error last |
| [hugelgupf/vmtest](https://github.com/hugelgupf/vmtest) | [#132](https://github.com/hugelgupf/vmtest/pull/132) | `kernel-riscv64`: bump to Linux 6.18.54 |
| [sysprog21/codetrial](https://github.com/sysprog21/codetrial) | [#110](https://github.com/sysprog21/codetrial/pull/110) | Run reports and the behaviour check on a local model |
| [spacemit-com/spine-triton](https://github.com/spacemit-com/spine-triton) | [#38](https://github.com/spacemit-com/spine-triton/pull/38) | Fix `xsmtvdot` feature name and stale imports in examples |
| [XS-MLVP/UCAgent](https://github.com/XS-MLVP/UCAgent) | [#140](https://github.com/XS-MLVP/UCAgent/pull/140) | `ci`: run unit tests on PRs and fix two stale prompt assertions |
| | [#141](https://github.com/XS-MLVP/UCAgent/pull/141) | `fix(skill)`: run Python skill scripts with the current interpreter |

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
- 以其他帳號或信箱送出的變更（這頁只查得到目前用的兩組 Gerrit 身分、GitHub 帳號與寄 patch 的信箱）。

---

## 資料來源與更新方式

四邊都有公開 API，更新這頁不需要人工翻紀錄：

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

# Mailing list：Linux 系在 kernel.org 的 patchwork，U-Boot 在 ozlabs
curl -s 'https://patchwork.kernel.org/api/patches/?submitter=alan.tseng.cs@gmail.com&per_page=50'
curl -s 'https://patchwork.ozlabs.org/api/patches/?submitter=alan.tseng.cs@gmail.com&per_page=50'
```

lore.kernel.org 對 curl 會擋（防機器人驗證），所以腳本查 patchwork；
patchwork 只有狀態沒有討論內容，回覆要回信箱或用瀏覽器看 lore。

Gerrit 查詢要注意兩件事：

- **`owner:` 和 `author:` 不是同一件事。** AOSP 的 automerger 會用機器人帳號重送同一個
  change，那些 change 的 owner 是 `android-build-automerger-*`，只有 `author:` 查得到自己。
- **狀態字眼要換算**：Gerrit 的 `NEW` 是「還在 review」，不是「新的還沒送」；
  `ABANDONED` 對應 GitHub 的 closed。
