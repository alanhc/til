---
title: 關於我
sidebar_label: 關於我
sidebar_position: 11
---

# 關於我

**Alan Tseng** — 用 AI agent 讓韌體工作跑更快的嵌入式軟體工程師。

工作範圍大致是三塊：**Android 平台整合**、**伺服器韌體（OpenBMC）**、
以及把 **AI agent 接進韌體開發流程**。這個站是這些工作的副產品——
邊做邊記，記完再整理成索引與名詞表。

---

## 現在在做什麼

**MediaTek，嵌入式軟體工程師（2025 – 至今）**

Android 平台整合與自動化，主要在 build、log triage 與跨團隊整合這幾段，
並把 AI agent 實際放進日常流程裡（不是 demo，是要能重跑的那種）。

## 經歷

| 期間 | 單位 | 做什麼 |
|---|---|---|
| 2025 – 至今 | **MediaTek** | Android 平台整合與自動化，AI agent 導入韌體開發流程 |
| 2024/12 – 2025/09 | **Wiwynn** | 伺服器平台的 **OpenBMC** 韌體開發與除錯 |
| 2024/09 – 2024/12 | **Pegatron** | 以 Kubernetes 做 rack-scale 伺服器的驗證自動化 |
| 2022/07 – 2022/11 | **LINE**（實習） | API 開發用的內部工具 |

**學歷**：國立臺灣大學 資訊工程 碩士（2024）

---

## 技術主軸

三條線，對應這個站的三個索引：

| 主軸 | 在做／在讀的東西 | 入口 |
|---|---|---|
| **Android 與開機鏈** | AOSP build、GKI／kleaf、SELinux、AVB 與 verified boot、TF-A／OP-TEE、各家 SoC 的 boot flow 對照 | [Android 系列索引](android_index.md) |
| **伺服器韌體與 BMC** | OpenBMC、IPMI／Redfish、PLDM／SPDM、sensor 與 thermal、LinuxBoot 與 u-root | [BMC 系列索引](bmc_index.md) ｜ [Embedded 系列索引](embedded_index.md) |
| **低階效能與工具鏈** | RISC-V（RVV、SpacemiT IME）、SIMD intrinsics、編譯器與模擬器、CPU 端的 LLM 推論 | [開源貢獻紀錄](contributions.md) |

近期在補的是 **Tegra／Jetson BSP**——driver 與 device tree、L4T 與 meta-tegra、
開機鏈的實機操作，路線圖寫在 [Tegra BSP 學習地圖](../tegra-bsp-learning-map.md)。

## 開源貢獻

貢獻散在 GitHub、AOSP Gerrit 與 OpenBMC Gerrit 三個系統上，
完整清單（含合入狀態、依影響力與依領域兩種排序）在
[開源貢獻紀錄](contributions.md)：

- **Android Common Kernel**：`kernel/common` 5 個 change 已合入（dma-heap、dma-buf、binder、scsi/ufs），automerge 傳播到多條分支
- **AOSP HAL**：`hardware/interfaces` 與 `libhardware` 共 17 筆在 review，主軸是替範例實作補 service fuzzer
- **上游專案**：llama.cpp（SpacemiT X60 的 RISC-V 矩陣加速）、u-root（riscv64 kexec）、sse2neon、shecc、elfuse、rv32emu、libspdm、OpenBMC libpldm

## 幾篇代表性的筆記

| 主題 | 文章 |
|---|---|
| AI agent 的安全架構 | [Kubernetes 作為 AI 代理系統之縱深防禦平台](../HERMES_AI_KUBERNETES_SECURITY_ARCHITECTURE.md) |
| AI 輔助韌體開發 | [MCP、Skills 與 Harness 的三層拆解](../ai-firmware-mcp-skills-harness.md) |
| 效能除錯的實戰過程 | [在 Pixel 8 上追一個 llama.cpp 的 SVE 效能退化](../llama-cpp-pixel8-sve-flash-attention.md) |
| 開機流程的全景 | [從按下電源到 Linux：PC、伺服器、Android、ARM Server](../boot-flow-intro.md) |
| 設計筆記 | [設備租約與遠端除錯通道](../BMC/device-lease-design.md) |

---

## 這個站

一個 TIL（Today I Learned）知識庫，用 Docusaurus 建置，push 到 `main` 就自動發佈。
內容以繁體中文為主，約 320 篇。

筆記大多平鋪在 `docs/` 底下，所以另外長出 [`0.map/`](README.md) 這一層：
每個主題一份**索引**（有哪些文章、從哪篇開始讀）與一份**名詞表**
（從一個陌生的縮寫反查回原始筆記）。想找東西的話從
[知識地圖](README.md) 進來比看側邊欄快。

## 聯絡

- GitHub：[@alanhc](https://github.com/alanhc)
- LinkedIn：[alanhc316](https://www.linkedin.com/in/alanhc316/)
- Email：[alan.tseng.cs@gmail.com](mailto:alan.tseng.cs@gmail.com)
- 個人網站：[alanhc.github.io](https://alanhc.github.io/)
