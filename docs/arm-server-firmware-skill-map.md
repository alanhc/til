---
title: "ARM Server 韌體技能地圖：DMTF 協定組、UEFI，與一台桌上型 BMC + ERoT"
description: "從公開規格、開源專案與業界常見分工，整理 ARM server 韌體分成哪幾條軌道，每條需要什麼；哪些能用 QEMU 補完、哪些非得碰硬體不可。附一個用 BeagleBone Black + STM32 搭出 BMC + satellite MCU 子系統的練習專案。"
sidebar_label: "ARM Server 韌體技能地圖"
tags: [firmware, bmc, openbmc, mctp, pldm, spdm, uefi, rtos, freertos]
date: 2026-09-05
---

# ARM Server 韌體技能地圖

> 素材來自公開規格、開源專案與業界常見分工。這篇談的是**技能結構**：
> ARM server 韌體實際上分成哪幾條軌道、彼此共用什麼、哪些能純軟體補完。

假設的起點：會 C、能讀 datasheet 的 bit-field、用過 Linux kernel 的除錯工具（ftrace / kgdb / crash dump）、
碰過 BMC 的管理介面（Redfish 或 IPMI）。缺的不是基礎，而是幾組具體的規格關鍵字。

有一個容易被忽略的觀察：GPU server 平台上有不少 manageability 韌體，是跑在 ARM M-class MCU 上的 RTOS 程式。
**一塊兩百元的 STM32F103C8T6 就是 Cortex-M3**；而 BeagleBone Black（Cortex-A8 跑 Linux）
和 BMC 常用的 AST2600（Cortex-A7 跑 OpenBMC）是同族架構。
**這兩塊板子接起來，就是一台桌上型的 BMC + satellite MCU 子系統。** 這是本文後半的核心。

---

## 一、五條軌道

| # | 軌道 | 核心關鍵字 |
|---|---|---|
| 1 | **BMC / OpenBMC** | OpenBMC、Redfish、**MCTP / PLDM / SPDM**、IPMI、thermal & power、FW update |
| 2 | **Server Embedded FW（M-class MCU）** | **Cortex-M + RTOS**、C/C++ manageability、bring-up、debug |
| 3 | **Firmware Update Infra** | PLDM Type 5、簽章、A/B、rollback、大規模部署 |
| 4 | **FW Security / Resiliency** | SPDM、attestation、RoT、NIST SP 800-193 |
| 5 | **SBIOS / UEFI** | EDK2、PEI/DXE、ACPI、BIOS↔BMC |

軌道 1–4 **共用同一套 DMTF 協定堆疊**，所以一個做得夠深的專案可以一次涵蓋四條。
軌道 5 是另一個世界，但值得補到「能對話」的程度——BIOS 與 BMC 之間的介面（KCS、IPMI、eSPI／LPC）
兩邊都得懂，不必成為 UEFI 專家。

---

## 二、技能缺口與補法

| 關鍵字 | 出現於 | 補法 | 需硬體 | 時數 | 優先 |
|---|---|---|---|---|---|
| **MCTP**（DSP0236 base / DSP0237 SMBus binding） | 1,2,3,4 | QEMU OpenBMC 跑 `mctpd`；再自己在 MCU 實作 endpoint | 選配 | 8–12h | **P0** |
| **PLDM**（DSP0248 monitoring / DSP0267 FW update） | 1,2,3 | `pldmtool` 跑 GetPLDMTypes / GetSensorReading；再實作 responder | 選配 | 8–12h | **P0** |
| **SPDM**（DSP0274）+ attestation | 1,4 | libspdm + spdm-emu 對打；再做簡化版上 MCU | 否 | 6–10h | **P0** |
| **OpenBMC 自建 image** | 1 | Yocto build `romulus` / `ast2600-evb`，跑 QEMU | 否 | 6–8h | **P0** |
| **UEFI / EDK2** | 5（及 1 的 BIOS↔BMC 介面） | OVMF on QEMU + 寫 DXE driver + gdb 單步 | 否 | 15–25h | **P1** |
| **BIOS↔BMC 介面**（KCS、IPMI over KCS、eSPI/LPC） | 1,5 | 讀規格 + 在 QEMU 觀察 | 否 | 4h | **P1** |
| **ACPI** | 5 | 在 OVMF 上 dump / 改一張表 | 否 | 6h | P2 |
| **Cortex-M + RTOS** | 2 | STM32 + FreeRTOS 實作 manageability 韌體 | **需** | 20h | **P1** |
| **JTAG / SWD halt-mode debug** | 1,2,5 | Pico probe + OpenOCD + gdb | **需** | 4–6h | **P1** |
| **I2C/SMBus 實機抓包** | 1,2 | 邏輯分析儀 + sigrok/PulseView 解 SMBus | **需** | 4h | **P1** |
| **FW 簽章 / A-B / rollback**（NIST SP 800-193） | 3,4 | MCU 雙 bank + 簽章驗證 + 失敗回滾 | **需** | 10h | **P1** |
| **Secure / Measured Boot 實作** | 4,5 | OVMF + swtpm 簽 PK/KEK/db；U-Boot FIT 簽章 | 選配 | 6–10h | **P0/P2** |
| **Yocto / BitBake** | 1 | OpenBMC 本身就是 Yocto，順帶練 | 否 | — | — |

**結論**：最貴的三個缺口（UEFI、DMTF 協定組、Secure Boot 實作）**九成不需要硬體**。
硬體補的是最後那塊「真的接過線、抓過波形、停過 core」的實作經驗。

---

## 三、P0：零硬體階段（約 40–55 小時）

| 週 | 項目 | 產出 |
|---|---|---|
| 1–2 | **OpenBMC on QEMU + MCTP + PLDM**：build `romulus` 或 `ast2600-evb`，開 `mctpd` / `pldmd`，用 `pldmtool` 跑 GetPLDMTypes、GetSensorReading，對照 DSP0236 / DSP0248 讀懂訊息流 | 實際跑通 MCTP / PLDM 訊息流 |
| 3 | **SPDM**：libspdm + spdm-emu requester/responder 對打，跑一次 GET_VERSION → GET_CAPABILITIES → GET_DIGESTS → GET_MEASUREMENTS | 把 attestation 從概念接到實作 |
| 3–5 | **EDK2 / OVMF on QEMU**：build OVMF、寫一個 DXE driver 與 UEFI Shell app、搞懂 SEC→PEI→DXE→BDS。關鍵差異化在於 **gdb attach 到 QEMU，在 DXE dispatch 下中斷點單步走** | 中文圈幾乎沒人寫過的「UEFI 階段除錯」筆記 |
| 5–6 | **Secure Boot + measured boot**：swtpm + OVMF，自簽 PK/KEK/db，簽一個 EFI binary，看它先被擋再被放行，看 PCR 值變化 | Secure Boot / measured boot / attestation 整組可實作驗證 |

延伸閱讀：[Secure Boot 與 Attestation：從信任的起點談起](./secure-boot-attestation.md)。

---

## 四、P1：桌上型 BMC + ERoT 迷你系統（約 60–80 小時）

```
                    ┌──────────────────────────────┐
   Redfish / HTTP   │  BeagleBone Black (Cortex-A8) │
   ←───────────────►│  扮演 BMC                      │
                    │  Linux + AF_MCTP + mctpd       │
                    │  + pldmd + Redfish 前端        │
                    └───────────┬──────────────────┘
                                │  I2C / SMBus（實體線，2.2k 上拉）
                                │  ← 邏輯分析儀掛在這裡抓包
                    ┌───────────┴──────────────────┐
                    │  STM32F103C8T6 (Cortex-M3)    │
                    │  扮演 satellite MCU / ERoT     │
                    │  FreeRTOS                      │
                    │  · MCTP over SMBus endpoint    │
                    │  · PLDM Type 2 sensor responder│
                    │  · PLDM Type 5 FW update       │
                    │    (A/B bank + 簽章 + rollback)│
                    │  · SPDM measurement 簡化版      │
                    └───────────┬──────────────────┘
                                │ SWD
                    ┌───────────┴──────────────────┐
                    │  Pico probe + OpenOCD + gdb   │
                    │  halt-mode debug              │
                    └──────────────────────────────┘
```

### 里程碑

| M | 內容 | 時數 | 學到的那句話 |
|---|---|---|---|
| M1 | MCU + FreeRTOS 骨架，I2C slave 通、UART log 通、Pico probe 能 halt 住 core 讀暫存器 | 12h | SWD halt-mode debug 跟 gdbserver 的差別，在於前者不需要 OS 還活著 |
| M2 | 實作 **MCTP over SMBus** endpoint（DSP0237）：封包組裝、EID、多封包重組 | 15h | 從零寫過 MCTP transport，而不只是呼叫 `pldmtool` |
| M3 | 疊上 **PLDM Type 2**：回報溫度/電壓 sensor；BBB 端用 Linux AF_MCTP + mctpd 當 bus owner 讀到值 | 15h | 端到端 PLDM 感測鏈路兩端都寫過 |
| M4 | **PLDM Type 5 韌體更新**：雙 bank、簽章驗證、更新中斷電後 rollback 到舊版 | 15h | 一條符合 NIST SP 800-193 protect / detect / recover 三支柱的更新流程 |
| M5 | 邏輯分析儀抓 SMBus 波形，逐 bit 對照 MCTP header；BBB 端把 sensor 曝成 **Redfish** resource | 10h | Redfish 一路 debug 到 I2C 波形，整條路走過一遍 |

這一個專案同時涵蓋：Cortex-M + RTOS（軌 2）、MCTP/PLDM/SPDM（軌 1,2,3,4）、
FW update infra（軌 3）、security & resiliency（軌 4），以及實機 debug 能力。

### 三個要提前知道的坑

1. **STM32F103 的 I2C slave 有著名 errata**（bus lock-up、需 workaround）。若卡超過一個晚上，
   改用第二顆 Pico 當 endpoint，或先用 UART 當 MCTP serial binding（DSP0253）跑通協定邏輯，
   再換回 SMBus。**協定實作才是重點，不要死在 I2C 周邊上。**
2. **BBB 的 Linux AF_MCTP 需要 kernel 5.15+**。Debian for BBB 常見 5.10 / 6.1，先確認版本，
   必要時自己編 kernel（順帶練 BSP）。
3. **F103C8T6 標稱 64KB flash**（多數實體是 128KB）。A/B 雙 bank 要把單一 image 壓在 ~28KB 內，
   做得到但要克制；不要塞 HAL 全家桶。

### 選修

- **BBB U-Boot verified boot**：FIT image 簽章 → 真硬體上的 chain of trust
- **ACPI**：在 OVMF 上 dump 並改一張表，補齊 SBIOS 軌
- **Zephyr**：部分 ERoT / satellite MCU 專案在用；FreeRTOS 做完再說

**明確不建議做**（會吃掉時間但對 server 韌體幫助有限）：BBB 的 PRU、示波器、
AST2600 實體 EVB（QEMU `romulus` 就夠）、二手伺服器。

---

## 五、採購清單（NT$500 以內）

| 品項 | 價格 | 用途 |
|---|---|---|
| 8ch 邏輯分析儀（Saleae clone）+ sigrok/PulseView | NT$200–300 | M5 抓 SMBus |
| Raspberry Pi Pico ×2 | NT$150–300 | 一顆當 picoprobe（SWD），一顆當備用 MCTP endpoint |
| 杜邦線、2.2k–4.7k 電阻數顆 | NT$50 | I2C 上拉 |

**接線注意**：BBB I2C 是 **3.3V**，STM32F103 的 PB6/PB7 雖 5V tolerant，
但整條 bus 統一 3.3V 上拉即可，不需 level shifter。BBB 的 P9 header 有現成 I2C2。

---

## 六、該答得出來的問題

拿來自我檢查，答不出來的就是還沒讀通的地方。

**DMTF 協定組（軌 1,2,3,4）**

1. MCTP 在協定堆疊的哪一層？為什麼不直接用 I2C？
   （關鍵：它是 transport-agnostic 的封包層，同一套上層協定可跑在 SMBus / PCIe VDM / serial 上）
2. PLDM Type 0/1/2/5 分別是什麼？（base / SMBIOS / monitoring & control / FRU / firmware update）
3. SPDM 的 GET_MEASUREMENTS 流程？跟 TPM quote 的 attestation 差在哪？
   （誰是 verifier、有沒有 PCR、session 建立方式）
4. Redfish 相對 IPMI 的優勢？為什麼業界要換？（RESTful/JSON schema、可擴充、security model）
5. BMC 與 host 誰先開機？BMC 掛掉時 host 會怎樣？
6. BIOS 跟 BMC 怎麼溝通？（KCS、IPMI over KCS、LPC/eSPI、in-band vs out-of-band 的差別）

**開機與安全（軌 4,5）**

7. UEFI 的 SEC → PEI → DXE → BDS 各做什麼？
8. Secure Boot 的 PK / KEK / db / dbx 關係？dbx 塞爆後業界怎麼辦？（SBAT）
9. Secure Boot 與 Measured Boot 差在哪？（擋 vs 記帳；哪個需要 TPM）
10. NIST SP 800-193 的三支柱？（Protect / Detect / Recover）
11. 韌體更新到一半斷電怎麼救？（A/B、golden image、RoT for Recovery）

**實務除錯**

12. Redfish 上一顆 sensor 讀不到值，怎麼一路查下去？
    （Redfish → `pldmd` log → `mctpd` → I2C transaction → 邏輯分析儀波形，這條完整路徑）
13. I2C bus hang 住怎麼救？（9-clock recovery、為什麼會 hang）
14. halt-mode debug（JTAG/SWD）與 gdbserver 的本質差別？
15. 為什麼 BMC 用 Cortex-A 跑 Linux，而 ERoT / satellite 用 Cortex-M 跑 RTOS？
    （即時性、attack surface、獨立性、成本）

---

## 七、時間軸總覽

| 週 | 主線 |
|---|---|
| 1–2 | MCTP + PLDM on QEMU |
| 3 | SPDM（libspdm） |
| 3–5 | EDK2 / OVMF + gdb |
| 5–6 | Secure Boot + swtpm |
| 6–8 | M1–M2（MCU 骨架 + MCTP） |
| 9–11 | M3–M4（PLDM sensor + FW update） |
| 12–14 | M5（波形 + Redfish）+ 專案文件化 |

**約 100–135 小時 / 14 週**（每週 8–10 小時）。若時間更緊，砍掉的順序是：
ACPI → Zephyr → EDK2 深入（只保留 build + boot 到能對話）→ M5。
**P0 的 MCTP / PLDM 那 20 小時不要砍**，那是投報率最高的一段。

---

## 參考

- [DMTF DSP0236 — MCTP Base Specification](https://www.dmtf.org/standards/pmci)
- [DMTF DSP0248 / DSP0267 — PLDM Monitoring / Firmware Update](https://www.dmtf.org/standards/pmci)
- [DMTF DSP0274 — SPDM](https://www.dmtf.org/standards/spdm)
- [OpenBMC](https://github.com/openbmc/openbmc)
- [DMTF/libspdm](https://github.com/DMTF/libspdm)、[spdm-emu](https://github.com/DMTF/spdm-emu)
- [TianoCore EDK2 / OVMF](https://github.com/tianocore/edk2)
- [NIST SP 800-193 — Platform Firmware Resiliency Guidelines](https://csrc.nist.gov/pubs/sp/800/193/final)
- [Linux AF_MCTP](https://docs.kernel.org/networking/mctp.html)
- [sigrok / PulseView](https://sigrok.org/)
