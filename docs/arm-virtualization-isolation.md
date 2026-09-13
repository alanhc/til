# Arm 虛擬化的隔離：從 Stage-2 到 Realm，四道邊界怎麼疊起來

> 這篇文章想回答一個問題：當我們說「這個 VM 被隔離了」，到底是誰、在哪一層、用什麼硬體機制擋住了誰？
> 內容全部來自公開規格與上游程式碼／郵件列表，文末附來源；推論性的判斷會另外標註。

---

## 一、隔離不是虛擬化的副產品，是虛擬化的目的

大多數人第一次接觸虛擬化，理解是「一台機器上跑多個 OS」。這個描述在伺服器時代成立，但在行動與車用平台上會誤導人。今天 Arm 平台導入 hypervisor，主要動機往往不是整併，而是**切邊界**：把 DRM 的解密流程、把生物辨識的比對、把第三方晶片廠的韌體 blob、把安全性等級不同的兩套 Android userspace，各自關進一個彼此看不到的盒子裡。

一旦把目標定成「隔離」而不是「共存」，評估標準就變了。問題不再是「效能損失幾 %」，而是：

1. 邊界由**誰**執行？是 hypervisor 的程式碼判斷，還是 MMU 硬體無條件檢查？
2. 邊界的 **TCB（可信計算基）** 有多大？有多少行程式碼一旦被攻破，隔離就全部失效？
3. 邊界擋得住哪些**存取路徑**？CPU 讀寫是一條路，DMA 是另一條，快取與時間側通道又是另一條。

Arm 架構在過去十幾年裡，其實是分四次、從四個不同角度回答這三個問題的。以下依序拆解。

---

## 二、第一道邊界：CPU 側的 Stage-2 位址翻譯

### 從「兩個 EL」到「兩段翻譯」

Armv7 的 Virtualization Extensions 引入 HYP mode，Armv8 之後正式成為 **EL2**。但真正撐起隔離的不是「多了一個特權層」，而是**多了一段位址翻譯**。

沒有虛擬化時，位址翻譯是一段：VA → PA，由 EL1 的 TTBR0/1_EL1 控制。開啟虛擬化後（`HCR_EL2.VM = 1`），對 EL1/EL0 而言變成兩段：

```
Guest VA --[Stage-1, guest 自己控制]--> IPA --[Stage-2, hypervisor 控制]--> PA
```

中間那個 **IPA（Intermediate Physical Address）** 是關鍵。Guest kernel 以為 IPA 就是實體位址，它可以隨意改自己的 stage-1 頁表、隨意存取任何「實體位址」——但它產出的每一個 IPA 都要再過一次 hypervisor 掌控的 stage-2 頁表。Stage-2 由 `VTTBR_EL2`（基底位址 + VMID）與 `VTCR_EL2`（粒度、起始 level、IPA 位寬）設定，guest 完全碰不到這兩個暫存器。

這件事的分量在於：**隔離的執行者是 MMU 硬體，不是 hypervisor 的判斷邏輯**。hypervisor 只在「建表」的那一刻做決策，之後每一次記憶體存取都由硬體無條件檢查。Guest 裡就算 kernel 被完全攻陷、任意程式碼執行，它能碰到的實體記憶體集合仍然被 stage-2 頁表的內容嚴格框住。

Stage-2 fault 發生時，`HPFAR_EL2` 會提供出錯的 IPA（而 `FAR_EL2` 給的是 VA），hypervisor 靠這組資訊區分「這是需要 demand paging 的合法存取」還是「這是 MMIO，要交給 VMM 模擬」還是「這是非法存取，殺掉」。

### VMID：讓 TLB 不必每次切換都清空

Stage-2 翻譯結果在 TLB 裡以 **VMID** 標記（配合 stage-1 的 ASID）。這讓多個 VM 的翻譯可以共存於 TLB，切換 VM 不需要 full TLB invalidate。從隔離角度看，VMID 是正確性要求：VMID 若被重複配置而沒有適當的 TLB 維護，就是一個跨 VM 的資料外洩通道。這也是為什麼 KVM 的 VMID 配置與 rollover 邏輯值得特別看一眼。

### VHE：把 host kernel 留在 EL2

早期 KVM/arm64 是 split mode：host kernel 在 EL1，一小段 hypervisor stub 在 EL2，每次進出 guest 都要跨 EL 搬運狀態，開銷很高。Armv8.1 的 **FEAT_VHE** 透過 `HCR_EL2.E2H` 與 `HCR_EL2.TGE`，把 EL2 的暫存器介面重新對映成 EL1 的樣子，讓未經修改的 host kernel 直接跑在 EL2。

值得注意的是**這是效能優化，不是隔離強化**——甚至方向相反：VHE 讓整個 host kernel 都在 EL2，等於把數百萬行程式碼放進 TCB。後面談 pKVM 時會看到，Android 走的正好是相反的路。

### 中斷與時間：隔離必須延伸到週邊狀態

只擋住記憶體不夠。一個 VM 若能任意操作 GIC 的分發器、或看到 host 的實體計時器，隔離一樣破功。Arm 的做法是把這兩者也虛擬化：

- **vGIC**：GICv3 提供 EL2 專屬的 `ICH_*` 系統暫存器與 list register（`ICH_LR<n>_EL2`），hypervisor 把虛擬中斷寫進 list register，guest 在 EL1 看到的是一組完整但受控的 CPU interface。GICv4 進一步支援 vLPI 直接注入，讓來自裝置的中斷不必每次都 trap 到 EL2。
- **Timer**：`CNTVOFF_EL2` 給每個 VM 一個虛擬時間偏移，`CNTHCTL_EL2` 決定 guest 能否直接讀實體計時器。

### Stage-2 擋不住的東西

坦白說清楚 stage-2 的邊界在哪裡，比誇大它更有用。Stage-2 管的是「哪塊實體記憶體可以被這個 VM 的 CPU 存取」，因此它**不管**：

- **DMA**：週邊裝置繞過 CPU MMU 直接打 PA（第三節處理）。
- **微架構共用資源**：L3 快取、記憶體頻寬、分支預測器。這是側通道與 QoS 干擾的來源，Arm 的回應是 **MPAM**（Memory System Resource Partitioning and Monitoring），但那是分割資源、降低干擾，不是密碼學意義的隔離。
- **hypervisor 自己**：stage-2 頁表是 hypervisor 建的，hypervisor 被攻破就全盤皆輸。這正是 CCA 要解決的問題。

---

## 三、第二道邊界：SMMU 與 DMA 隔離

### 為什麼 stage-2 對裝置完全無效

把一個 GPU、一個 NPU、一個 camera ISP passthrough 給 VM，意思是讓 guest 直接寫該裝置的 MMIO 暫存器。Guest 會在裝置的 DMA descriptor 裡填位址——填的是 IPA，還是 PA？

如果系統上沒有 IOMMU，裝置發出的匯流排交易帶的就是**實體位址，直接送進記憶體控制器，完全不經過 CPU 的 stage-2**。這代表 guest 只要在裝置暫存器裡填一個 host kernel 的實體位址，就能讀寫 host 記憶體。**沒有 IOMMU 的 device passthrough 等於沒有隔離**——這句話值得記住，因為它在實務上被違反的次數遠比想像中多。

### SMMUv3 的兩層對應關係

Arm 的 IOMMU 是 **SMMU**（System MMU）。SMMUv3 的模型與 CPU 側刻意做成同構：

| 概念 | CPU 側 | SMMU 側 |
|---|---|---|
| 身分識別 | EL / ASID / VMID | **StreamID**（哪個裝置）／ **SubstreamID**（裝置內哪個 context） |
| 第一段翻譯 | Stage-1（guest OS 控制） | Stage-1，由 **Context Descriptor (CD)** 描述 |
| 第二段翻譯 | Stage-2（hypervisor 控制） | Stage-2，由 **Stream Table Entry (STE)** 描述 |
| 翻譯路徑 | VA → IPA → PA | IOVA → IPA → PA |

每個發起 DMA 的裝置（或裝置內的每條 stream）有一個 StreamID，經 Stream Table 查到 STE；STE 裡帶著 stage-2 頁表基底與 VMID，也可以指向 CD table 做 stage-1。SubstreamID 對應 PCIe PASID，讓同一個裝置的不同 process context 走不同的 stage-1。

關鍵在於：**hypervisor 讓 SMMU 的 stage-2 使用和該 VM 的 CPU stage-2 完全相同的頁表與 VMID**。這樣一來，「裝置能碰到的記憶體」自動等於「VM 的 CPU 能碰到的記憶體」，兩條路徑收斂到同一個邊界。Guest 在裝置上填 IPA，SMMU 幫它翻成 PA，填錯了就是 SMMU fault，碰不到 host。

而 stage-1 留給 guest 自己管：guest 裡的 IOMMU driver 建自己的 IOVA → IPA 對應，這就是 **nested translation**。上游 Linux 與 QEMU 為此發展了 iommufd 相關介面與 vSMMU 模擬，把 stage-1 頁表的管理權下放給 guest，同時把 stage-2 牢牢握在 host 手上。

### 實務上的破口

值得留意的幾個地方：

- **共用 StreamID**：如果兩個功能不同、信任等級不同的 IP 共用同一個 StreamID，它們在 SMMU 眼裡是同一個實體，無法分開授權。這是 SoC 整合階段就決定的事，軟體事後補不回來。
- **繞過 SMMU 的路徑**：某些 SoC 內部的 interconnect 路徑（例如某些 coprocessor 對 SRAM 的存取）根本不經過 SMMU。
- **SMMU 自己的設定介面**：SMMU 的 command queue 與 Stream Table 必須只有 host 能寫，否則 guest 可以直接改自己的 STE。

---

## 四、第三道邊界：TrustZone 與 CCA — 一條正交的軸

到目前為止談的都是**垂直**切分：EL0 < EL1 < EL2 < EL3，上層管下層。TrustZone 引入的是**水平**切分：**世界（world）**。

### 世界 vs. 特權層

Secure world 與 Non-secure world 各自有完整的 EL0/EL1，而且這條界線不是靠頁表權限，是靠**每筆匯流排交易上的 NS bit**：交易帶著安全屬性走出核心，由 interconnect 與記憶體端的位址空間控制器（實作上常見的是 TZASC/TZC 這類元件，屬 implementation-defined 而非架構強制）決定放行與否。Normal world 的 EL1 是特權的，但它拿不到 Secure 的記憶體——因為那不是權限不足，是**物理位址空間根本不同**。

這解釋了一個常見混淆：TEE（跑在 Secure world）和 VM（跑在 Normal world 的 EL1）不是同一個維度的東西。一個 VM 再怎麼被隔離，它整個都在 Normal world 裡；一個 TEE 再怎麼安全，它對 Normal world 的 hypervisor 而言是「另一個世界」而不是「另一個 VM」。

### Secure EL2：Secure world 內部也要切

早期 Secure world 是一整塊：OP-TEE 和所有 vendor 的 trusted app、所有 secure driver 擠在同一個位址空間，任一個出包就全垮。Armv8.4 的 **FEAT_SEL2** 在 Secure world 裡也加了 EL2 與 stage-2，於是 Secure world 內部也能切成多個互相隔離的 **Secure Partition（SP）**。

配套的軟體架構是 **FF-A（Firmware Framework for Arm A-profile）**：定義 SP 之間、以及 SP 與 Normal world 之間的訊息傳遞與記憶體共享 ABI；**Hafnium** 是 Arm 開源的 SPMC（Secure Partition Manager Core）參考實作，跑在 S-EL2，對 SP 做的事情概念上就是 hypervisor 對 VM 做的事情。

所以 Arm 平台上其實可能同時存在**兩個 hypervisor**：Normal world 的 KVM/pKVM 在 NS-EL2，Secure world 的 Hafnium 在 S-EL2，兩者由 EL3 的 TF-A 做世界切換。

### Armv9 CCA：把 hypervisor 移出 TCB

前面留了一個問題沒解：**stage-2 頁表是 hypervisor 建的，所以 hypervisor 天然能看見所有 VM 的記憶體**。對雲端租戶或對「連 OEM 自己都不該看到使用者資料」的場景，這不夠。

Armv9 的 **CCA（Confidential Compute Architecture）** 用 **RME（Realm Management Extension）** 回答這件事，做法是把 TrustZone 那條「世界」軸從 2 條擴充成 4 條物理位址空間（PAS）：

- **Non-secure**（Normal world，host OS 與 hypervisor 在這）
- **Secure**（傳統 TrustZone / TEE）
- **Realm**（機密 VM 所在的新世界）
- **Root**（EL3 韌體專屬）

執行檢查的硬體是 **GPC（Granule Protection Check）**，依據 **GPT（Granule Protection Table）** 判斷「這個實體 granule 目前屬於哪個 PAS，這筆交易能不能碰」。GPT 只有 Root world 的 EL3 能寫。

於是隔離結構變成兩層串聯：

```
Realm VA --stage-1--> IPA --stage-2--> PA --GPC(GPT)--> 准 / 不准
```

Normal world 的 hypervisor 仍然負責 Realm 的**資源配置與排程**（決定給多少記憶體、什麼時候跑），但當某個 granule 被轉為 Realm PAS 之後，hypervisor 自己**在硬體層面**就讀不到它了。Realm 的內部管理交給跑在 Realm EL2 的 **RMM（Realm Management Monitor）**：Normal world 的 hypervisor 透過 **RMI**（Realm Management Interface）請求 RMM 建立與排程 Realm，Realm 內的 guest 則透過 **RSI**（Realm Services Interface）向 RMM 要服務，兩者的世界切換由 EL3 負責。

這是整個架構最漂亮的一步：**隔離不再依賴「hypervisor 有沒有正確地建表」，而是依賴「EL3 有沒有正確地維護 GPT」**——後者的程式碼量小了好幾個數量級，可稽核性完全不同。

---

## 五、第四道視角：實作面 — KVM、pKVM、Gunyah

架構提供機制，真正決定隔離強度的是誰用了哪些機制、TCB 畫在哪。

### 標準 KVM/arm64

Host kernel（VHE 下在 EL2）擁有全部 stage-2 頁表，可以讀寫任意 guest 記憶體——這對 server 場景是特性而非缺陷（live migration、ballooning、dirty logging 都靠它）。TCB = 整個 host kernel + VMM。

### pKVM：把 host kernel 趕下 EL2

Android Virtualization Framework 的 **pKVM（protected KVM）** 反轉了信任方向。開機時 Android kernel 先在 EL2，安裝完 pKVM 之後**自我降級（deprivilege）到 EL1**，之後 EL2 只剩下一小段 pKVM 程式碼。

pKVM 的核心手法是給 **host 自己也套上一張 stage-2 頁表**——初始是 identity map（IPA = PA，效能上幾乎無損），但這張表由 EL2 掌控。當一個 protected VM 被建立、需要記憶體時，那些頁面會從 host 的 stage-2 identity map 中**被 unmap 掉**：pVM 的頁表、vCPU 結構等 metadata 由 host「捐贈（donate）」給 hypervisor，在 pVM 銷毀前 host 都碰不到。Guest 資料頁走同樣的 donation 流程，host 若嘗試存取未共享的 pVM 記憶體會收到 SIGSEGV。要通訊時，guest 主動用 SHARE/UNSHARE hypercall 把特定頁面共享回去。

結果是：**即使整個 Android kernel 被完全攻陷，它也讀不到 pVM 的記憶體**，因為權限不在它手上。TCB 從數百萬行縮到數萬行。

上游狀態值得誠實交代：kernel 官方文件目前把 CPU memory isolation 列為已實作，而 **CPU state isolation 與透過 IOMMU 的 DMA isolation 仍標示為未實作**。2026 年 1 月 Will Deacon 送出的 30 個 patch 系列（基於 v6.19-rc4）開始把 protected guest 記憶體支援推上游，但仍需要 developer Kconfig 選項並且會 taint kernel，明確說明「完整的 host 隔離」尚未完成；該系列也提到這塊工作一部分是在等 `guest_memfd` 成熟，目前先沿用 Android 的 anonymous memory 做法。

### Gunyah：Type-1 的另一種答案

Qualcomm 的 **Gunyah** 是獨立的 Type-1 hypervisor，本身就不是 Linux 的一部分。它的上游策略在 2025 年出現明顯轉向：從原本的獨立 driver 介面（`gunyah_memfd`、`gunyah_irqfd`）改為**把 Gunyah 支援接進 KVM，讓 KVM 在 EL1 扮演管理角色**，實際的虛擬化由更高特權的 Gunyah 韌體執行，藉此複用 KVM 既有的記憶體管理、irqfd 與 vCPU 基礎設施。

---

## 六、把四道邊界放在同一張表上

| 邊界 | 硬體機制 | 誰設定 | 擋住誰 | 典型 TCB |
|---|---|---|---|---|
| CPU 記憶體 | Stage-2 MMU（`VTTBR_EL2`/`VTCR_EL2`）、VMID | Hypervisor (EL2) | Guest 的 CPU 存取 | Hypervisor（VHE 下含整個 host kernel） |
| DMA | SMMUv3 STE/CD、StreamID | Host/Hypervisor | 裝置的 DMA | Hypervisor + SMMU driver |
| 世界（水平） | NS bit、TZASC；S-EL2 stage-2 | EL3 (TF-A) / SPMC | 跨 world 存取 | TF-A + SPMC |
| PAS（CCA） | GPC / GPT | EL3 (Root) | 連 hypervisor 也擋 | EL3 + RMM |

實務上判斷一個平台的隔離主張是否成立，可以照這張表逐格問：

1. Stage-2 是否確實對該 VM 生效，還是只是「另一個 VM，但頁表其實 identity map 全部記憶體」？
2. 每個 passthrough 給 VM 的裝置是否都在 SMMU 後面，且 StreamID 沒有和別的 IP 混用？
3. 這個「安全」元件在 Secure world 還是 Normal world？如果在 Secure world，它和其他 SP 有沒有用 S-EL2 分開？
4. 主張「連 host 都看不到」的話，靠的是 pKVM 的 donation（軟體維護的 stage-2），還是 CCA 的 GPT（EL3 維護的物理檢查）？兩者的威脅模型不同。

---

## 七、幾點個人判斷（推論，非規格內容）

以下是我的解讀，與上述可驗證事實分開陳述：

- **Stage-2 與 GPC 的關係是互補而非替代。** CCA 並沒有讓 stage-2 變得不重要——Realm 內部一樣需要 stage-2 來做位址重映射與資源管理，GPC 只是在最後多加一道無法被 hypervisor 繞過的檢查。把 CCA 理解成「stage-2 的升級版」會走偏。
- **DMA 隔離是目前 Arm 機密運算最現實的落差。** CPU 側的路徑（stage-2 → pKVM donation → GPT）已經相當完整，但要讓一個 NPU 或 GPU 安全地服務 protected VM，需要裝置本身理解 PAS、需要 SMMU 支援對應檢查、需要完整的 attestation 鏈。從 kernel 文件仍把 pKVM 的 IOMMU DMA isolation 標為未實作來看，這一段的工程量還很大。
- **「隔離」在 SoC 上是整合問題，不是單一元件問題。** 前述任何一道邊界只要有一個 IP 繞過、一個 StreamID 共用、一段 SRAM 不受 TZASC 管，整條主張就會出現破口。這類問題往往在架構定案時就決定了，軟體端很難補救。

---

## 來源

事實陳述依據以下公開資料：

- [Protected KVM (pKVM) — The Linux Kernel documentation](https://www.kernel.org/doc/html/next/virt/kvm/arm/pkvm.html) — host stage-2 identity map、donation 機制、CPU memory isolation 已實作／CPU state 與 DMA isolation 未實作
- [AVF architecture | Android Open Source Project](https://source.android.com/docs/core/virtualization/architecture) — kernel 自 EL2 自我降級至 EL1、記憶體 donation 與 sharing 模型
- [KVM: arm64: Add support for protected guest memory with pKVM — LWN.net](https://lwn.net/Articles/1053007/) — 2026-01-05 的 30-patch 系列、基於 v6.19-rc4、developer Kconfig 與 kernel taint、guest_memfd 等待狀態
- [KVM: arm64: Base support for the pKVM hypervisor at EL2 — LWN.net](https://lwn.net/Articles/895790/)
- [Running Qualcomm's Gunyah Guests via KVM in EL1 — LWN.net](https://lwn.net/Articles/1018749/) — Gunyah 上游策略轉向 KVM in EL1
- [Realm Management Extension (RME) — Trusted Firmware-A documentation](https://trustedfirmware-a.readthedocs.io/en/latest/components/realm-management-extension.html) — 四個 PAS（Root / Secure / Realm / Non-secure）、GPT/GPC、EL3 角色、RMM 於 Realm EL2
- [Arm CCA Hardware Architecture (DEN0125)](https://developer.arm.com/documentation/den0125/latest/)
- [Secure Partition Manager — Trusted Firmware-A documentation](https://trustedfirmware-a.readthedocs.io/en/latest/components/secure-partition-manager.html) 與 [Hafnium SPMC documentation](https://hafnium.readthedocs.io/en/v2.12.0/secure-partition-manager/secure-partition-manager.html) — FF-A、S-EL2、SPMC
- [SMMUv3 nested translation support (QEMU patch series)](https://lists.nongnu.org/archive/html/qemu-devel/2024-07/msg00062.html) — vSMMU 巢狀翻譯的上游進展

暫存器名稱（`HCR_EL2`、`VTTBR_EL2`、`VTCR_EL2`、`HPFAR_EL2`、`CNTVOFF_EL2`、`ICH_LR<n>_EL2` 等）、FEAT_VHE / FEAT_SEL2 / FEAT_RME 的定義，以及 SMMUv3 的 StreamID / STE / CD 模型，均依 Arm Architecture Reference Manual 與 Arm SMMUv3 Architecture Specification。
