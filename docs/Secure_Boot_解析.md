---
title: Secure Boot 解析:從一顆 eFuse 到 Android 開機的完整信任鏈
sidebar_label: Secure Boot 解析
---

# Secure Boot 解析:從一顆 eFuse 到 Android 開機的完整信任鏈

> 目標讀者:嵌入式/韌體工程師。本文是〈ARM Trusted Firmware 解析〉的姊妹篇——上一篇講「誰在跑」,這一篇講「憑什麼信任它」。

## 前言:Secure Boot 要解決什麼問題

一台裝置從上電到進系統,要執行十幾段來自 flash 的程式碼。flash 是可以被改寫的——透過刷機工具、透過供應鏈、透過一個有寫入權限的漏洞。Secure Boot 回答的問題很單純:**如何保證裝置只執行「被授權者簽署過」的程式碼,即使攻擊者能任意改寫儲存內容?**

答案的核心只有一句話:**每一段程式碼,都由前一段已被信任的程式碼驗證後才執行。** 這條遞迴的鏈要成立,需要兩個錨點:一段不可修改的程式碼(immutable code),和一把不可修改的公鑰(immutable key)。其餘全部是工程細節。本文就來把這些工程細節攤開。

## 密碼學基礎:為什麼是「簽章」而不是「加密」

常見的誤解是把 Secure Boot 和「韌體加密」混為一談。Secure Boot 的核心是**完整性與來源驗證**,不是機密性,用的是數位簽章:

1. 廠商在簽署伺服器(理想上是 HSM)持有**私鑰**,對 image 的雜湊值(SHA-256 以上)簽章,簽章附在 image 後面。
2. 裝置只持有對應的**公鑰**(或公鑰的雜湊)。開機時重算 image 雜湊、用公鑰驗證簽章,兩者吻合才跳轉執行。

公鑰不怕被讀走——它本來就是公開的;但**怕被換掉**。攻擊者若能把裝置上的公鑰換成自己的,就能簽署任何程式碼。所以真正要保護的不是金鑰的機密性,而是公鑰的**不可竄改性**。這就是 eFuse 登場的地方。

演算法上,RSA-2048/4096 與 ECDSA P-256/P-384 都常見;ROM 空間吃緊的晶片偏好 ECDSA(金鑰短、驗證程式碼小)。近年因應後量子遷移,LMS/ML-DSA 也開始出現在新平台的規格書上。

## 兩個錨點:Boot ROM 與 eFuse

**Boot ROM(BL1)** 是光刻進晶片的,物理上不可修改。它是信任鏈中唯一「不需要被驗證」的程式碼——不是因為它安全,而是因為沒有更早的東西能驗證它。這也意味著 ROM 的 bug 是永久的:Apple 的 checkm8(BootROM USB 堆疊 use-after-free)讓數億台 iOS 裝置終生可被 tethered jailbreak,無法透過任何軟體更新修補。這是整個產業最深刻的一課:**ROM 程式碼要越少越好、攻擊面要越窄越好。**

**eFuse(或 OTP)** 是一次性可程式化的熔絲陣列。產線上會燒入:

- **ROTPK hash**:Root of Trust 公鑰的雜湊。公鑰本體放在 flash 上的憑證裡沒關係,ROM 驗證時先把它雜湊、和 eFuse 裡的值比對,確認公鑰未被調包,再用它驗簽章。只存雜湊是為了省 fuse 位數。
- **Secure Boot enable bit**:未燒之前晶片什麼都肯跑(方便開發),燒下去之後不可逆地強制驗證。
- **Anti-rollback counter**:後面會講。

從此,「這台裝置信任誰」被物理性地決定了。這也是為什麼 Secure Boot 的金鑰管理是量產流程中最嚴肅的環節——私鑰洩漏或 fuse 燒錯,召回都救不回來。

## ARM 平台的實作:TBBR 憑證鏈

上一篇提過 TF-A 的 boot flow(BL1→BL2→BL31/BL32/BL33)。TBBR(Trusted Board Boot Requirements)定義了這條鏈上每個 image 怎麼被驗證,設計上比「一把公鑰簽到底」精緻得多——它是一條 **X.509 憑證鏈**:

```
ROTPK (hash 在 eFuse)
  └─ 驗證 BL2 的 content certificate ──▶ 驗證 BL2 image
       └─ Trusted Key Certificate(裝著下一層的公鑰)
            ├─ BL31 key cert ─▶ BL31 content cert ─▶ BL31 image
            ├─ BL32 key cert ─▶ BL32 content cert ─▶ BL32 image
            └─ BL33 key cert ─▶ BL33 content cert ─▶ BL33 image
```

每個 image 配兩張憑證:**key certificate** 用上一層的金鑰簽署,內容是「這個 image 該用哪把公鑰驗」;**content certificate** 內容是「這個 image 的正確雜湊值」。分層的好處是金鑰隔離——BL33 的簽署金鑰可以交給另一個團隊(甚至另一家公司,例如 SoC 廠簽 BL2/BL31、手機廠簽 BL33),洩漏了也只影響那一層,換金鑰不用動到 ROTPK。

TF-A 把這些 image 和憑證打包成 **FIP(Firmware Image Package)**,用 `fiptool` 操作、`cert_create` 產憑證,整條鏈可以在 QEMU 上完整跑起來練習。

## Android 的接力:AVB 2.0

TBBR 鏈驗到 BL33(bootloader)就結束了,但 kernel、ramdisk、system partition 還沒被保護。Android 用 **Android Verified Boot(AVB)2.0** 接手:

- **vbmeta partition** 是驗證的中樞:裡面存著各 partition 的雜湊(小 partition 如 boot、dtbo 用整體 hash)或 **hashtree descriptor**(大 partition 如 system、vendor 用 Merkle tree,執行期由 dm-verity 逐 block 驗證,避免開機時算整個 partition 的雜湊)。
- vbmeta 本身由 OEM 金鑰簽署,bootloader 內建這把公鑰來驗它——所以 TBBR 鏈保證 bootloader 沒被動過,bootloader 再保證 vbmeta 沒被動過,vbmeta 保證其他所有 partition。信任就這樣一路傳遞下去。
- **Rollback index**:vbmeta 裡帶版本號,裝置把已見過的最大版本記在防竄改儲存(RPMB 或 eFuse)。刷回舊版簽章依然有效,但版本號過不了——這就擋掉了「降級到有漏洞的舊版再攻擊」的路線。

**Boot state** 是使用者可感知的部分:**green**(鏈完整)、**yellow**(鎖著、但用的是使用者自訂金鑰驗證)、**orange**(bootloader 已解鎖,不驗證,開機時那個警告畫面)、**red**(驗證失敗,拒絕開機)。`fastboot flashing unlock` 之所以強制清除 userdata,是因為解鎖後 TEE 會拒絕釋出綁定在 verified 狀態上的金鑰(這也是 Widevine 從 L1 掉到 L3 的原因)——資料本來就再也解不開了,清除只是誠實面對。

## 攻擊面:鏈會從哪裡斷

寫防禦的人必須懂攻擊。Secure Boot 的破口通常不在密碼學本身:

**ROM/早期 bootloader 的記憶體安全漏洞。** checkm8 之外,高通 EDL(Emergency Download Mode)、聯發科 BROM 的漏洞(kamakiri/mtkclient 所利用)都屬此類:驗證邏輯還沒跑到,攻擊者已經借 USB 下載模式取得執行權。教訓:recovery/download path 的攻擊面和正常 boot path 一樣重要。

**Fault injection(glitching)。** 在 ROM 執行「驗證是否通過」的那條分支指令瞬間,對電源或時脈打一個毛刺,讓 CPU 跳錯分支。實務對策:關鍵判斷用冗餘比對、隨機延遲、把「驗證通過」編碼成非平凡常數而不是 0/1。

**TOCTOU(time-of-check to time-of-use)。** 驗完雜湊之後、跳轉執行之前,image 若還在攻擊者可寫的記憶體(例如共享 DRAM,另一顆 coprocessor 還能寫),就可能被掉包。原則:先搬進受保護的記憶體,再驗證,再執行。

**金鑰與流程失誤。** 比漏洞更常見:debug 簽章金鑰流出、產線裝置忘了燒 secure boot fuse、某個 partition(例如 splash screen 或 DSP firmware)根本沒被納入驗證範圍。Secure Boot 的強度取決於覆蓋率最低的那個 image。

## 實作 checklist(如果你正要幫平台加上 Secure Boot)

實務上的順序大致是:先確認 ROM 支援與 fuse map,定義金鑰階層(誰簽哪一層、金鑰存哪個 HSM、怎麼輪替),把簽署整進 build system(產出即簽章,人手不碰私鑰),開發階段用 development key + 未燒 fuse 的樣機,量產前做 key ceremony 與 fuse 燒錄 SOP,並確認每一條開機路徑——正常、recovery、download mode——都在驗證範圍內。最後留一份「私鑰洩漏時的應變計畫」,因為到時候你不會有時間現想。

## 動手練習

1. **AVB**:拿 `avbtool` 對一個 boot.img 做 `add_hash_footer`、自製 vbmeta,再用 `verify_image` 走一遍驗證,你會對 descriptor 結構立刻有感。
2. **TF-A TBBR**:在 QEMU 上以 `TRUSTED_BOARD_BOOT=1` 編譯 TF-A,用 `cert_create` 產憑證鏈,故意改一個 byte 看 BL2 在哪裡把你擋下來。
3. **U-Boot FIT signature**:開發板上最容易完整走一遍「簽署→燒錄→驗證失敗→修復」流程的環境。

## 結語

Secure Boot 沒有魔法:一段改不了的 ROM、一把換不掉的公鑰、一條「先驗證再執行」的紀律,遞迴到底。難的從來不是密碼學,而是覆蓋率——每一條執行路徑、每一個 image、每一顆會碰記憶體的 coprocessor 都要納入;以及紀律——金鑰管理與產線流程的每一步都不能便宜行事。鏈的強度,永遠等於最弱的那一環。

## 參考資料

- Arm DEN0006: Trusted Board Boot Requirements(TBBR)
- [TF-A Trusted Board Boot 文件](https://trustedfirmware-a.readthedocs.io/en/latest/design/trusted-board-boot.html)
- [Android Verified Boot 2.0](https://android.googlesource.com/platform/external/avb/+/master/README.md)
- [Android 官方文件:Verified Boot](https://source.android.com/docs/security/features/verifiedboot)
- [U-Boot FIT Signature Verification](https://docs.u-boot.org/en/latest/usage/fit/signature.html)
- checkm8 技術分析(axi0mX)、mtkclient 專案——攻擊面研究的入門教材
