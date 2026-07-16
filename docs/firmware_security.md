---
sidebar_label: 韌體安全全景
---

# 韌體安全全景：在 OS 之下、開機之前，守住信任的起點

> 目標讀者：嵌入式／韌體工程師，或想建立韌體安全整體觀的人。
> 這是一篇**總圖**——把韌體安全當成一個領域來組織，各站點的深入版另有專文：開機信任鏈見〈[Secure Boot 解析](./Secure_Boot_解析.md)〉與〈[ARM Trusted Firmware (TF-A) 解析](./ARM_Trusted_Firmware_解析.md)〉，執行期存取控制見〈[SELinux](./selinux.md)〉。

## TL;DR

韌體是整台裝置**特權最高、能見度最低、最難修補**的一層——它在 OS 之下、開機之前執行，上面所有安全機制都建立在「相信韌體是乾淨的」這個前提上。韌體安全不是單一功能，而是一條跨越裝置生命週期的防線：**開機時**驗證信任鏈、**執行期**隔離特權、**更新時**只接受簽署過的 image、**面對攻擊**時收斂攻擊面、**在供應鏈**管好金鑰。這五道防線的強度，永遠等於最弱的那一環。

---

## 一張圖：韌體安全的五道防線

```
                     ┌──────────────────────────────────────┐
   裝置生命週期  →   │  出廠      開機       執行        更新   │
                     └──────────────────────────────────────┘
                          │         │          │          │
   ①供應鏈與金鑰 ─────────┘         │          │          │
      ROTPK/fuse 燒錄、HSM 簽署      │          │          │
                                    │          │          │
   ②開機信任鏈 ─────────────────────┘          │          │
      immutable code + immutable key           │          │
      + 先驗證再執行（Secure Boot / AVB）        │          │
                                               │          │
   ③執行期隔離 ────────────────────────────────┘          │
      TrustZone/TEE、SELinux、記憶體保護、secure peripheral │
                                                          │
   ④韌體更新 ─────────────────────────────────────────────┘
      signed update、anti-rollback、A/B + 回滾

   ⑤攻擊面（貫穿全程）：debug port、download mode、fault injection、side-channel
```

各道防線回答的問題不同，這是最好記的框架：

- **①供應鏈**：這台裝置該相信誰？（金鑰怎麼產、怎麼存、怎麼燒進 fuse）
- **②開機**：怎麼保證只跑被授權簽署的 code？（信任鏈的錨點與遞迴）
- **③執行期**：開機後怎麼防止一個被攻陷的元件動到不該碰的東西？（隔離）
- **④更新**：怎麼安全地換掉韌體、又不被降級回有漏洞的舊版？
- **⑤攻擊面**：以上全對了，攻擊者還能從哪裡進來？（多半不在密碼學本身）

---

## 為什麼韌體是最值得攻擊的一層

三個特性疊在一起，讓韌體成為高價值目標：

- **特權最高**：BL1/BootROM、Secure Monitor（EL3）比 OS kernel 還底層，攻下這裡等於繞過上面一切防禦。
- **能見度最低**：對應用開發者是黑盒子，一般 EDR／防毒看不到這一層，植入後極難察覺。
- **最難修補**：ROM 是光刻進晶片的，bug 是**永久的**——Apple 的 checkm8（BootROM use-after-free）讓數億台裝置終生可被 tethered jailbreak，無法靠 OTA 修補。同類例子在 MediaTek BROM 也有（見下方攻擊面）。這是整個產業最深刻的一課：**ROM 程式碼越少越好、攻擊面越窄越好。**

---

## ① 開機信任鏈（boot-time）

核心只有一句話：**每一段程式碼，都由前一段已被信任的程式碼驗證後才執行。** 這條遞迴鏈需要兩個錨點——一段不可修改的程式碼（BootROM）和一把不可修改的公鑰（eFuse 裡的 ROTPK hash）。ARM 平台用 TBBR 的 X.509 憑證鏈驗到 bootloader，Android 再用 AVB 接手驗到 kernel 與 system。

> 完整機制（簽章 vs 加密、eFuse、TBBR 憑證鏈、AVB 2.0、boot state 四色）見〈[Secure Boot 解析](./Secure_Boot_解析.md)〉；各 BL 階段與 EL3 的角色見〈[ARM Trusted Firmware (TF-A) 解析](./ARM_Trusted_Firmware_解析.md)〉。

## ② 執行期隔離（runtime）

開機驗證通過只是起點；系統跑起來後，還要防止任何一個被攻陷的元件橫向擴散。四種主要手段：

| 手段 | 做什麼 | 深入 |
|---|---|---|
| **TrustZone / TEE** | 硬體把系統切成 Secure／Normal World，金鑰運算、指紋、DRM 跑在 Secure World，Normal World 連 secure RAM 都讀不到 | 〈[TF-A 解析](./ARM_Trusted_Firmware_解析.md)〉 |
| **MAC（SELinux）** | 即使 root，沒有 policy 允許一律拒絕；把每個 process 關進最小權限的 domain | 〈[SELinux](./selinux.md)〉、〈[SEPolicy 速查](./android_sepolicy.md)〉 |
| **記憶體保護** | W^X（可寫不可執行）、ASLR、硬體標記如 **MTE**（Memory Tagging）精準抓 UAF／overflow | — |
| **記憶體防火牆** | TZASC/TZC 把 secure region 在匯流排層擋掉 Normal World 存取，設錯一個 region 就漏金鑰 | 〈[TF-A 解析](./ARM_Trusted_Firmware_解析.md)〉 |

## ③ 韌體更新（secure update）

能更新韌體是好事，但更新通道本身就是攻擊面。安全更新有三個支柱：

- **簽章驗證**：裝置只接受用信任金鑰簽署的 image，OTA 下載回來先驗簽再寫入。
- **Anti-rollback**：光驗簽不夠——舊版簽章**也是有效的**。攻擊者可以刷回有漏洞的舊韌體再攻擊。對策是版本計數器存在防竄改儲存（eFuse／RPMB），刷入比計數器舊的版本一律拒絕（實機錯誤如 `image (bl1_a): rejected, anti-rollback`）。
- **A/B 與回滾**：寫入備用 slot，開機成功才切換，失敗自動退回舊 slot，避免更新失敗變磚。

> 一個具體案例——MTK preloader 怎麼接上 Google A/B OTA、以及 `update_engine` byte-level 寫入為何要求 image 自帶 device header：見〈[MTK Preloader Combo Header 與 OTA](./mtk-preloader-combo-header-ota.md)〉。

## ④ 攻擊面（attack surface）

Secure Boot 的破口通常**不在密碼學本身**，而在下面這些地方——這也是防禦者最容易忽略的一環：

| 攻擊面 | 說明 | 對策方向 |
|---|---|---|
| **Debug port 殘留** | 量產機忘了關 JTAG／UART console／`fastboot oem` 後門 | 出貨前依 lifecycle state 鎖死 debug |
| **Download mode / BROM exploit** | 高通 EDL、聯發科 BROM download mode 是驗證還沒跑到就能進入的入口。若 BootROM 本身有記憶體安全漏洞（如 `mtkclient`／kamakiri 所利用的 MTK BROM bug），攻擊者能借 USB 下載模式取得最高權執行——而且因為在 ROM，無法修補 | recovery／download path 要與正常 boot path 同等看待；ROM 攻擊面壓到最小 |
| **Fault injection（glitching）** | 在 ROM 執行「驗證是否通過」的分支瞬間，對電源／時脈打毛刺讓 CPU 跳錯分支 | 冗餘比對、隨機延遲、把「通過」編碼成非平凡常數而非 0/1 |
| **TOCTOU** | 驗完雜湊後、跳轉執行前，image 若還在攻擊者可寫的記憶體就被掉包 | 先搬進受保護記憶體，再驗證，再執行 |
| **實體 flash 讀取／side-channel** | 直接拆 flash 讀內容、或用功耗／電磁側信道推金鑰 | 敏感資料加密儲存、金鑰不落 flash、關鍵運算做 side-channel 防護 |

> 攻擊面與 checkm8／glitching／TOCTOU 的細節見〈[Secure Boot 解析](./Secure_Boot_解析.md)〉的「攻擊面」節。一份把 MediaTek BootROM exploit 逐步拆解的優秀讀物見下方參考資料。

## ⑤ 供應鏈與金鑰（supply chain）

比漏洞更常見的失守，是流程與金鑰管理出錯：

- **金鑰階層與隔離**：SoC 廠簽 BL2/BL31、手機廠簽 BL33，分層讓某層金鑰洩漏不必動到 ROTPK。私鑰放 HSM，原則是「產出即簽章，人手不碰私鑰」。
- **產線的不可逆性**：ROTPK hash 與 secure boot enable bit 一次燒進 eFuse，燒錯或私鑰外流，召回都救不回來——所以 key ceremony 與 fuse 燒錄 SOP 是量產最嚴肅的環節。
- **覆蓋率是最低標**：Secure Boot 的強度取決於**覆蓋率最低的那個 image**——某個 splash screen、DSP firmware 或 coprocessor image 忘了納入驗證，整條鏈就有破口。
- **可追溯性**：SBOM（軟體物料清單）、image provenance、簽章紀錄，讓事後能查「這台裝置到底跑了誰簽的什麼」。

---

## 三個貫穿全局的原則

1. **鏈的強度等於最弱環**——不管是信任鏈、更新覆蓋率還是攻擊面，一個沒守到的點就讓其餘全部投資歸零。
2. **ROM 層的錯無法挽回**——越底層越接近 immutable，設計時就要假設它改不了、把攻擊面壓到最小。
3. **可除錯性與安全性天生對立**——JTAG、download mode、verbose log 是開發的命脈，也是攻擊者的入口。差別只在**出貨前有沒有依 lifecycle state 關掉**，這條界線是韌體安全實務的核心紀律。

---

## 參考資料

- NIST SP 800-193, *Platform Firmware Resiliency Guidelines*（protect / detect / recover 三支柱）
- NIST SP 800-147, *BIOS Protection Guidelines*
- Arm DEN0006, *Trusted Board Boot Requirements (TBBR)*；DEN0022, *Power State Coordination Interface (PSCI)*
- [Android Verified Boot 2.0](https://source.android.com/docs/security/features/verifiedboot)
- [Dissecting a MediaTek BootROM exploit](https://tinyhack.com/2021/01/31/dissecting-a-mediatek-bootrom-exploit/)——逐步拆解 MTK BROM download mode 漏洞（`mtkclient`／kamakiri 的底層原理），ROM 層攻擊面的絕佳教材
- checkm8 技術分析（axi0mX）、mtkclient 專案——攻擊面研究的入門教材
- 站內深入版：[Secure Boot 解析](./Secure_Boot_解析.md)、[ARM Trusted Firmware (TF-A) 解析](./ARM_Trusted_Firmware_解析.md)、[SELinux](./selinux.md)
