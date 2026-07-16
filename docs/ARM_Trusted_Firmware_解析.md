---
title: ARM Trusted Firmware(TF-A)解析:Android 開機前,你的手機都在跑什麼?
sidebar_label: ARM Trusted Firmware 解析
---

# ARM Trusted Firmware(TF-A)解析:Android 開機前,你的手機都在跑什麼?

> 目標讀者:嵌入式/韌體工程師,或想進入 Android firmware / bootloader 領域的開發者。
> 假設你熟悉 C、看得懂記憶體映射,但不一定碰過 Secure World。

## 前言:kernel 之前的世界

大多數人對 Android 開機的理解是「bootloader 載入 kernel」。但在 ARMv8-A 平台上,bootloader 被執行之前,SoC 已經跑過了好幾段韌體——初始化 DDR、建立安全世界、鎖定記憶體防火牆、驗證每一段程式的簽章。這一整段流程的核心,就是 ARM Trusted Firmware,舊稱 ATF,現在的正式名稱是 **Trusted Firmware-A(TF-A)**,由 Linaro 主導的 [trustedfirmware.org](https://www.trustedfirmware.org/projects/tf-a/) 社群維護,是 ARMv8-A/ARMv9-A 平台 Secure World 軟體的參考實作(reference implementation)。

「參考實作」這個詞很關鍵:ARM 定義了一堆規格——Trusted Board Boot Requirements(TBBR)、Power State Coordination Interface(PSCI)、SMC Calling Convention(SMCCC)——TF-A 就是這些規格的官方開源實作。高通、聯發科、三星、瑞薩、NXP 的量產韌體,不是直接基於 TF-A,就是實作了相同的介面。看懂 TF-A,等於看懂了整個 ARM 生態的開機與安全模型。

## 背景知識:TrustZone 與 Exception Level

要理解 TF-A 在做什麼,先要理解 ARMv8-A 的特權模型。硬體提供四個 Exception Level:

```
EL0  ─ user space(app)
EL1  ─ kernel(Linux / Trusted OS kernel)
EL2  ─ hypervisor(KVM、pKVM)
EL3  ─ Secure Monitor ← TF-A 的 BL31 就住在這裡
```

同時,TrustZone 把整個系統切成兩個世界:**Normal World(Non-secure)** 跑 Android/Linux,**Secure World** 跑 Trusted OS(OP-TEE、高通 QTEE、Trustonic Kinibi 等)。這個切割不只是軟體概念——AXI bus 上每筆 transaction 都帶著 NS bit,secure RAM、secure peripheral(例如指紋 sensor 的 SPI、crypto engine)在硬體層就拒絕來自 Normal World 的存取。

EL3 是唯一能在兩個世界之間切換的地方。Normal World 想請 Secure World 做事(例如用硬體金鑰簽章),就執行一條 `SMC` 指令,trap 進 EL3,由 Secure Monitor 保存context、切換 `SCR_EL3.NS` bit、跳進 Secure World。這個 Monitor,就是 TF-A 的 BL31。

## Boot Flow:BL1 到 BL33

TF-A 把開機切成一連串的 Boot Loader stage:

```
┌─────────┐   ┌─────────┐   ┌──────────────────┐
│  BL1    │──▶│  BL2    │──▶│  BL31 (EL3)      │──┐
│ BootROM │   │ 載入器   │   │ Secure Monitor   │  │ 常駐
└─────────┘   └─────────┘   └──────────────────┘  │
                   │                               │
                   │        ┌──────────────────┐   │
                   ├───────▶│  BL32 (S-EL1)    │◀──┤ SMC
                   │        │  Trusted OS      │   │
                   │        │  (OP-TEE 等)     │   │
                   │        └──────────────────┘   │
                   │        ┌──────────────────┐   │
                   └───────▶│  BL33 (EL2/EL1)  │◀──┘
                            │  Android         │
                            │  Bootloader      │──▶ Linux kernel
                            └──────────────────┘        │
                                                        ▼
                                                    Android
```

**BL1 — AP Trusted ROM。** AP 指 Application Processor,也就是跑 Android/Linux 的主 CPU(Cortex-A 核心),用來與 SoC 上其他處理器區分——例如管電源時序的 SCP(System Control Processor,通常是顆 Cortex-M)、modem DSP 等。BL1 是燒在晶片裡的 Boot ROM,上電後第一段在 AP 上執行的程式(實務上很多 SoC 前面還有獨立的 PMIC/SCP boot 流程,這裡簡化)。它只做最少的事:初始化少量 SRAM、從 boot media(eMMC/UFS/SPI-NOR)載入 BL2,並用燒在 eFuse 裡的 Root of Trust 公鑰雜湊(ROTPK hash)驗證 BL2 的簽章。ROM 不可修改,這就是整條信任鏈的錨點。

**BL2 — Trusted Boot Firmware。** 在 SRAM(或剛初始化好的部分 DRAM)執行,負責初始化 DDR、載入並驗證後面所有 image:BL31、BL32、BL33,以及各家 SoC 的專屬韌體(DDR training firmware、modem image 等)。驗證邏輯遵循 TBBR 的 X.509 憑證鏈設計——每個 image 附帶 content certificate 與 key certificate,一路鏈回 ROTPK。

**BL31 — EL3 Runtime Firmware。** 這是 TF-A 最重要的部分,開機後**常駐**在 secure memory,不會退場。它負責:

- **Secure Monitor**:處理 SMC,執行 world switch(保存/還原 GP registers、system registers,翻轉 `SCR_EL3.NS`)。
- **PSCI**:kernel 的 CPU hotplug、`suspend-to-RAM`、reboot,最後都是一個 SMC(例如 `CPU_SUSPEND`、`SYSTEM_OFF`)進到 BL31,由 platform code 去操作電源控制器。你在 device tree 看到的 `enable-method = "psci"` 就是這個。
- **中斷路由**:設定 GIC,決定 Secure interrupt(Group 0 / Secure Group 1)與 Non-secure interrupt(Group 1)分別 trap 到哪個世界。
- **各種 runtime service**:SDEI(secure delivery of events)、廠商自訂的 SiP service(`SMCCC` 有保留 vendor 區段的 function ID)、Spectre/Meltdown 類漏洞的 workaround(`SMCCC_ARCH_WORKAROUND_*`)。

**BL32 — Trusted OS。** 跑在 Secure EL1 的作業系統,提供 Trusted Application 的執行環境(TEE)。Android 上的 Keymaster/KeyMint、Gatekeeper、Widevine L1 DRM,本體都是跑在這裡的 TA。開源代表是 OP-TEE;量產手機上更常見的是高通 QTEE、Trustonic、三星 TEEGRIS。

**BL33 — Non-secure Firmware,也就是大家熟悉的 bootloader。** 在 Android 裝置上是高通 ABL(基於 EDK2 / UEFI)、聯發科 LK,或開發板常見的 U-Boot。它負責 fastboot、A/B slot 選擇、載入 `boot.img`,並執行 **Android Verified Boot(AVB)**——用 `vbmeta` 驗證 kernel/ramdisk/dtbo 的雜湊。注意信任鏈的銜接:BL1→BL2→BL33 由 TBBR 憑證鏈保證,BL33→kernel 由 AVB 保證,兩段合起來才是完整的 Verified Boot。

> 各家 SoC 對這些 stage 有自己的名字:高通的 PBL(=BL1)、XBL/SBL(≈BL2)、TZ(≈BL31+BL32);聯發科的 BootROM、Preloader(≈BL2)、ATF、LK(=BL33)。名字不同,角色對應得上。

## 為什麼這段韌體如此重要

**它是 Root of Trust 的軟體起點。** Secure Boot 的每一環——你的手機為什麼能保證跑的是原廠簽署的系統、解 bootloader 鎖為什麼會清資料並讓 Widevine 掉到 L3、防止刷回舊版有漏洞韌體的 anti-rollback(eFuse 版本計數)——全部建構在 BL1/BL2 的驗證鏈之上。這一層被攻破,上面所有安全機制都是空談。歷史上著名的例子如 checkm8(Apple BootROM 漏洞)說明了為什麼 ROM 層的 bug 無法透過 OTA 修補、影響終生。

**它是硬體安全功能的守門人。** KeyMint 的 hardware-backed key、StrongBox、指紋資料的隔離,依賴的都是 TF-A 開機早期設定好的記憶體防火牆(TZASC/TZC-400 之類的 address space controller)與 secure peripheral 配置。設錯一個 region,Normal World 就能直接讀到金鑰。

**它是電源管理的最終執行者。** 所有 CPU 上下線、cluster power down、系統 suspend,kernel 只是發出 PSCI 請求,真正操作 power controller 暫存器、維護 cache coherency 出入順序的是 BL31 的 platform code。

## 對 Android Firmware / Bootloader Engineer 的意義

如果你的目標職位是 Android bootloader 或 firmware engineer,TF-A 不是選修,是你的工作環境本身:

**Platform bring-up。** 新晶片或新板子的 bring-up,第一步往往就是把 TF-A 的 platform port(`plat/<vendor>/` 目錄)弄起來:實作 `plat_get_my_entrypoint`、console driver、DDR 初始化參數、`plat_psci_ops`(每個 power domain 怎麼開關)。TF-A 的 porting guide 定義了一整組必須實作的 platform API。

**Boot chain 與簽章。** 你會經手 image 的簽署流程、憑證鏈設定、fuse 燒錄(ROTPK、anti-rollback counter)、secure/non-secure 記憶體佈局。fastboot unlock 之後驗證行為怎麼改變、yellow/orange/red boot state 怎麼來的,你要能從 BL2 一路講到 AVB。

**Debug 的最後一哩。** 很多最難纏的 bug 最後都落在這一層:suspend 之後喚不醒(PSCI platform hook 的 resume 路徑漏還原某個暫存器)、隨機 hang 在 world switch(secure interrupt 路由設錯)、kernel 讀某段記憶體直接 bus fault(踩到 secure region)。這種問題 printk 救不了你,你需要 JTAG、`crash dump` 裡的 EL3 context,以及對 TF-A 原始碼的熟悉度。

**面試必考。** boot flow 各 stage 的職責、EL0–EL3、SMC 進出 EL3 時發生什麼事、PSCI 的 CPU_SUSPEND 流程、TBBR 憑證鏈——這些是 SoC 廠與手機廠韌體職位的標準考題。

## 從哪裡開始上手

TF-A 完全開源(BSD-3-Clause),而且可以不用真硬體就跑起來:

1. Clone [TF-A 原始碼](https://git.trustedfirmware.org/TF-A/trusted-firmware-a.git),用 QEMU virt platform(`PLAT=qemu`)搭配 OP-TEE 與 U-Boot 建一條完整的 boot chain,GDB 直接掛上去單步跟 BL1→BL2→BL31 的流程。
2. 讀 `docs/design/firmware-design.rst`,這是理解整體架構最好的一份文件。
3. 找一塊有開源支援的板子(Raspberry Pi 4、Rockchip RK3399、NXP i.MX8 系列都有 upstream platform port)實際編譯、燒錄、加 log。
4. 追一次 PSCI 呼叫:從 kernel 的 `cpu_suspend` 進 `psci_ops`,到 TF-A 的 `psci_cpu_suspend`,再到 platform 的 `pwr_domain_suspend`。跟完這一條線,你對「kernel 與韌體的邊界」的理解會完全不同。

## 結語

TF-A 是 ARM 生態裡少數「每台裝置都在跑、卻很少人讀過」的軟體。對應用開發者它是黑盒子;但對 firmware/bootloader engineer,它是信任鏈的起點、電源管理的終點、也是職涯的分水嶺——因為願意往 EL3 這一層鑽的人,一直都不多。

## 參考資料

- [Trusted Firmware-A 官方文件](https://trustedfirmware-a.readthedocs.io/)
- [TF-A 原始碼(trustedfirmware.org Gerrit)](https://git.trustedfirmware.org/TF-A/trusted-firmware-a.git)
- Arm DEN0006: Trusted Board Boot Requirements(TBBR)
- Arm DEN0022: Power State Coordination Interface(PSCI)
- Arm DEN0028: SMC Calling Convention(SMCCC)
- [Android Verified Boot 2.0(AVB)](https://android.googlesource.com/platform/external/avb/)
- [OP-TEE 文件](https://optee.readthedocs.io/)
