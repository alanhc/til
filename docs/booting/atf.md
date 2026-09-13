# ARM Trusted Firmware（TF-A）

**ARM Trusted Firmware（TF-A）** 是 ARMv8-A/AArch64 平台的參考安全韌體，提供各開機階段（boot stage）與 secure world 的基礎服務，並實作 **PSCI** 等標準介面。開機依序經過 BL1 → BL2 → BL31 → BL33 各階段。

## Boot stages（BL 各階段）

- **BL1（AP Trusted ROM）**：上電後最先執行、通常燒在唯讀 ROM 中的信任根（root of trust），負責初始化並驗證、載入 BL2。
- **BL2（Trusted Boot Firmware）**：完成更多平台初始化，並負責載入與驗證後續各 image（BL31、BL32、BL33）。是 secure boot 驗證鏈的重要一環。
- **BL31（EL3 Runtime Firmware）**：常駐在最高權限的 **EL3（Secure Monitor）**，在 OS 執行期間持續提供服務，處理 secure/non-secure world 之間的切換（SMC），並實作 **PSCI**（Power State Coordination Interface，管理 CPU 開關機、待機、系統關機/重開）。
- **BL32（Secure-EL1 Payload，選用）**：secure world 的 OS，例如 OP-TEE，用來跑 Trusted Application。
- **BL33（Non-trusted Firmware）**：non-secure world 的開機韌體，例如 U-Boot 或 UEFI，接著載入一般 OS（Linux）。

## secure world 概念

ARM TrustZone 把系統分為 **secure world** 與 **non-secure（normal）world**，TF-A 在 EL3 擔任兩者間的守門人（Secure Monitor），確保機密運算與金鑰等敏感操作隔離於一般 OS 之外。

## 參考連結

https://developer.arm.com/documentation/110342/0100/Bare-metal-development-on-Juno/Introduction/Arm-Trusted-Firmware-boot-process


ARM trusted firmware https://hackmd.io/@BooleanII/linux2024-ARM_Trusted_Firmware

[機密運算解決方案巡禮：Arm】揭露自家機密運算架構下一步](https://www.ithome.com.tw/tech/145565)
