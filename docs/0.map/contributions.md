---
title: 開源貢獻紀錄
sidebar_label: 開源貢獻紀錄
sidebar_position: 10
---

# 開源貢獻紀錄

貢獻散在三個不同的系統上：**GitHub PR**、**AOSP 的 Gerrit**（android-review）、
**OpenBMC 的 Gerrit**。三邊的狀態字眼還不一樣（merged / MERGED / NEW / ABANDONED），
所以這頁統一成同一套圖例，並在最後附上重新查詢的指令，讓它可以隨時更新。

> 資料以 **2026-09-21** 查詢結果為準。

**圖例**：✅ 已合入 ｜ 🔄 review 中 ｜ ⛔ 已關閉（未合入）

---

## 一覽

| 平台 | 專案 | ✅ 已合入 | 🔄 review 中 |
|---|---|---|---|
| AOSP Gerrit | `kernel/common`（Android Common Kernel） | 5 個 change（含 automerge 共 13 筆） | 1 |
| AOSP Gerrit | `platform/hardware/interfaces` | — | 12 |
| AOSP Gerrit | `platform/hardware/libhardware` | — | 5 |
| OpenBMC Gerrit | `openbmc/libpldm` | — | 4 |
| GitHub | sysprog21（elfuse / codetrial / frama-c-mcp / shecc / rv32emu） | 15 | 6 |
| GitHub | u-root、llama.cpp、sse2neon | 5 | 2 |
| GitHub | ARM-software、DMTF、OpenPRoT | — | 3 |
| GitHub | 其他（cert-tools、os-in-1000-lines） | 2 | — |

主題大致分三塊：**Android kernel 與 HAL 的文件／健壯性修補**、**RISC-V 與 SIMD 相關的
效能與模擬器工作**、**韌體協定（PLDM、SPDM）的邊界檢查**。

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
| 1 | [llama.cpp #27961](https://github.com/ggml-org/llama.cpp/pull/27961) — 條件式納入 SpacemiT IME kernel sources | 129k ★ | 觸及範圍最大的一筆，而且是**讓 RISC-V 加速路徑真的編得進去**的那一步，不是文件 |
| 2 | [u-root #3733](https://github.com/u-root/u-root/pull/3733) — `pkg/boot` riscv64 kexec support | 3.1k ★ | 新功能，而且落在開機鏈核心：u-root 是 LinuxBoot／firmware 場景的 userland |
| 3 | [sse2neon #774](https://github.com/DLTcollab/sse2neon/pull/774) — 拿掉 `<fenv.h>` 依賴 | 1.5k ★ | 影響**所有 includer**——header 汙染是會傳染給下游的那種 bug |
| 4 | [u-root #3750](https://github.com/u-root/u-root/pull/3750)、[#3735](https://github.com/u-root/u-root/pull/3735) — reboot 指令、zimage 長度上限 | 3.1k ★ | 一個新指令、一個邊界修正，同樣在開機路徑上 |
| 5 | [elfuse](https://github.com/sysprog21/elfuse) ×7 — futex、pty hangup、`AT_EMPTY_PATH`、`CLONE_THREAD` 的 `SIGCHLD`… | 268 ★ | 專案規模小，但**技術深度最高**：syscall 語意層級的行為正確性，錯了不會有人幫你發現 |
| 6 | AOSP `kernel/common` ×5（dma-heap、dma-buf、binder、scsi/ufs） | Android ACK | **觸及範圍其實最廣**（進 ACK 並 automerge 到 6 條分支，往下就是所有 Android 裝置的 kernel 樹），但性質是 kernel-doc 修補，所以沒有排在功能型變更之前 |
| 7 | [shecc #339](https://github.com/sysprog21/shecc/pull/339) — 參數 slot 尚未建立前的逃逸讀取測試 | 1.4k ★ | 教學用 C 編譯器，補的是會被後續重構踩到的測試 |
| 8 | [frama-c-mcp](https://github.com/sysprog21/frama-c-mcp) ×3、[codetrial](https://github.com/sysprog21/codetrial) ×4 | 31 / 62 ★ | 工具鏈與服務端的實用修補，觸及範圍最小 |
| 9 | [os-in-1000-lines #101](https://github.com/nuta/operating-system-in-1000-lines/pull/101) — 繁體中文翻譯 | 3.6k ★ | 讀者觸及很廣，但不是程式碼，另成一類 |
| 10 | [cert-tools #55](https://github.com/blockchain-certificates/cert-tools/pull/55) | 42 ★ | 2022 年的單點 bug 修正 |

### Review 中（潛在影響）

同樣三個軸，但狀態全部是 🔄，所以這裡排的是「**如果合入**會有多大影響」。

| # | 貢獻 | 專案規模 | 為什麼排在這裡 |
|---|---|---|---|
| 1 | [llama.cpp #28479](https://github.com/ggml-org/llama.cpp/pull/28479) — Q8_0 IME1 matrix kernel for SpacemiT X60 | 129k ★ | 比已合入的 #27961 更進一步：那筆是把路接上，**這筆是 kernel 本身**。合入的話是這份清單裡影響最大的一筆 |
| 2 | AOSP `hardware/interfaces` ×12、`libhardware` ×5 | Android | 給預設／範例 HAL 補 service fuzzer 並修出生命週期問題。**廠商常以範例實作為起點**，所以修在這裡會往下游擴散 |
| 3 | [libspdm #3816](https://github.com/DMTF/libspdm/pull/3816) — key update rollback | 189 ★ | star 數不高但身分特殊：**DMTF 的 SPDM 參考實作**，安全協定的正確性問題 |
| 4 | [sse2neon #773](https://github.com/DLTcollab/sse2neon/pull/773) — SVE2 fast path | 1.5k ★ | 效能路徑，opt-in 所以風險可控 |
| 5 | [optimized-routines #97](https://github.com/ARM-software/optimized-routines/pull/97) — strcmp benchmark | 711 ★ | Arm 官方倉庫，但性質是 benchmark 而非實作 |
| 6 | [rv32emu](https://github.com/sysprog21/rv32emu) ×5 — RVV 指令實作 | 590 ★ | 量大且偏功能，但侷限在單一模擬器內 |
| 7 | [libpldm](https://gerrit.openbmc.org/q/project:openbmc/libpldm) ×4（OpenBMC）、[pldm-lib #21](https://github.com/OpenPRoT/pldm-lib/pull/21) | OpenBMC / 新專案 | 韌體協定的邊界檢查，影響面取決於這兩個 library 被採用的程度 |

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
| [ANDROID: scsi: ufs: fix kernel-doc for the UPIU prepare helpers](https://android-review.googlesource.com/c/kernel/common/+/4232023) | `android-mainline` | ✅ | `-desktop` ✅、`-riscv64` ✅、[`android17-6.18`](https://android-review.googlesource.com/c/kernel/common/+/4268863) 🔄 |
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
| [sysprog21/shecc](https://github.com/sysprog21/shecc) | [#339](https://github.com/sysprog21/shecc/pull/339) | Test an escaped parameter read before its slot exists |
| [u-root/u-root](https://github.com/u-root/u-root) | [#3733](https://github.com/u-root/u-root/pull/3733) | `pkg/boot`: add riscv64 kexec support |
| | [#3735](https://github.com/u-root/u-root/pull/3735) | `pkg/boot/zimage`: accept a longer kernel size entry |
| | [#3750](https://github.com/u-root/u-root/pull/3750) | `cmds/core/reboot`: add reboot command |
| [ggml-org/llama.cpp](https://github.com/ggml-org/llama.cpp) | [#27961](https://github.com/ggml-org/llama.cpp/pull/27961) | `ggml-cpu`: conditionally add SpacemiT IME kernel sources |
| [DLTcollab/sse2neon](https://github.com/DLTcollab/sse2neon) | [#774](https://github.com/DLTcollab/sse2neon/pull/774) | Drop the `<fenv.h>` dependency to stop leaking `FE_*` into includers |
| [nuta/operating-system-in-1000-lines](https://github.com/nuta/operating-system-in-1000-lines) | [#101](https://github.com/nuta/operating-system-in-1000-lines/pull/101) | 繁體中文版翻譯 |
| [blockchain-certificates/cert-tools](https://github.com/blockchain-certificates/cert-tools) | [#55](https://github.com/blockchain-certificates/cert-tools/pull/55) | prevent isoformat error |

### 🔄 Review 中

| 專案 | PR | 內容 |
|---|---|---|
| [sysprog21/rv32emu](https://github.com/sysprog21/rv32emu) | [#766](https://github.com/sysprog21/rv32emu/pull/766)、[#767](https://github.com/sysprog21/rv32emu/pull/767)、[#768](https://github.com/sysprog21/rv32emu/pull/768)、[#770](https://github.com/sysprog21/rv32emu/pull/770)、[#774](https://github.com/sysprog21/rv32emu/pull/774) | RVV 整數指令、whole vector register move、單倍寬浮點轉換，以及 widening 運算的 cross-EEW overlap 規則 |
| [ggml-org/llama.cpp](https://github.com/ggml-org/llama.cpp) | [#28479](https://github.com/ggml-org/llama.cpp/pull/28479) | `ggml-cpu`: add Q8_0 IME1 matrix kernel for SpacemiT X60 |
| [DLTcollab/sse2neon](https://github.com/DLTcollab/sse2neon) | [#773](https://github.com/DLTcollab/sse2neon/pull/773) | Add opt-in SVE2 fast path for `_SIDD_CMP_EQUAL_ANY` |
| [ARM-software/optimized-routines](https://github.com/ARM-software/optimized-routines) | [#97](https://github.com/ARM-software/optimized-routines/pull/97) | `bench`: add strcmp benchmark |
| [DMTF/libspdm](https://github.com/DMTF/libspdm) | [#3816](https://github.com/DMTF/libspdm/pull/3816) | Fix key update rollback for Specula cluster A.1 and A.3 |
| [OpenPRoT/pldm-lib](https://github.com/OpenPRoT/pldm-lib) | [#21](https://github.com/OpenPRoT/pldm-lib/pull/21) | `pldm-common`: bound wire version-string lengths by the destination |
| [sysprog21/elfuse](https://github.com/sysprog21/elfuse) | [#365](https://github.com/sysprog21/elfuse/pull/365) | Give each restated rule one owner |

### ⛔ 已關閉（未合入）

留著是因為它們通常有下文：被拆小、被重送，或被維護者換了做法。

| 專案 | PR | 後續 |
|---|---|---|
| ggml-org/llama.cpp | [#28025](https://github.com/ggml-org/llama.cpp/pull/28025) | 重送為 [#28479](https://github.com/ggml-org/llama.cpp/pull/28479) |
| u-root/u-root | [#3736](https://github.com/u-root/u-root/pull/3736) | arm kexec，riscv64 那條（#3733）先進 |
| sysprog21/rv32emu | [#769](https://github.com/sysprog21/rv32emu/pull/769)、[#771](https://github.com/sysprog21/rv32emu/pull/771)、[#772](https://github.com/sysprog21/rv32emu/pull/772)、[#773](https://github.com/sysprog21/rv32emu/pull/773) | RVV 浮點系列，改以其他 PR 重整 |
| sysprog21/elfuse | [#362](https://github.com/sysprog21/elfuse/pull/362) | AGENTS.md 的組織方式，維護者另有想法 |
| sysprog21/codetrial | [#4](https://github.com/sysprog21/codetrial/pull/4) | lobby 控制項位置 |

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

# Gerrit REST API（回傳開頭有 )]}' 前綴，要先去掉才能餵給 JSON parser）
curl -s 'https://android-review.googlesource.com/changes/?q=author:"Alan Tseng"&n=100'
curl -s 'https://gerrit.openbmc.org/changes/?q=owner:alanhc&n=100'
```

Gerrit 查詢要注意兩件事：

- **`owner:` 和 `author:` 不是同一件事。** AOSP 的 automerger 會用機器人帳號重送同一個
  change，那些 change 的 owner 是 `android-build-automerger-*`，只有 `author:` 查得到自己。
- **狀態字眼要換算**：Gerrit 的 `NEW` 是「還在 review」，不是「新的還沒送」；
  `ABANDONED` 對應 GitHub 的 closed。
