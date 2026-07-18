---
sidebar_label: AVB 深入解析
---

# Android Verified Boot（AVB）深入解析：從信任根到 vbmeta 的完整開機驗證

> 給 Android 系統開發者的技術長文——理解 AVB 的設計動機、信任鏈運作、vbmeta 結構、dm-verity 驗證，以及刷機與客製化時最常踩到的雷。

---

## 一、為什麼需要開機驗證？

Android 是一個層層堆疊的系統：晶片上電後，先跑晶片內建的 ROM code，接著載入 bootloader，bootloader 載入 kernel 與 ramdisk，kernel 再掛載 `system`、`vendor` 等分區，最後才進到 Android framework。這條啟動路徑上的每一層，都可能成為攻擊者的目標。

想像一個沒有開機驗證的世界：攻擊者只要有辦法寫入 `boot` 或 `system` 分區——例如透過一個提權漏洞、或是實體接觸裝置刷入修改過的映像——他就可以植入一個開機即載入的 rootkit。這種惡意程式跑在 kernel 或更底層，權限比任何 app 都高，能攔截解鎖畫面、竊取金鑰、繞過所有應用層的安全機制，而且因為它「先於系統」啟動，一般的防毒或系統還原幾乎清不掉它。這類攻擊被稱為 **persistent / evil-maid attack**。

**Android Verified Boot（AVB）** 就是為了封住這個攻擊面而生。它的核心主張是：**裝置在開機的每一個階段，都必須先驗證下一階段程式碼的完整性與真實性，確認它是由可信任的金鑰簽署、且內容未被竄改，才允許執行。** 一旦驗證失敗，裝置要嘛拒絕開機、要嘛明確警告使用者，絕不默默載入一個可能被動過手腳的系統。

AVB 目前的主流實作是 **AVB 2.0**（對應的參考程式庫叫 `libavb`），自 Android 8.0（Oreo）起成為要求。它整合並取代了早期較零散的做法——過去 dm-verity 與 boot 映像簽章是分開處理的，AVB 2.0 用一個統一的 metadata 分區（`vbmeta`）把整條信任鏈串了起來。

---

## 二、信任鏈（Chain of Trust）：從硬體信任根開始

AVB 的安全性建立在一條**信任鏈**上，而這條鏈必須有一個不可被竄改的起點，稱為**硬體信任根（Hardware Root of Trust）**。

### 信任根

信任根通常是燒錄在晶片內部一次性可程式化記憶體（eFuse / OTP）中的一段資料——最常見的是**公鑰的雜湊值**，或是啟用/停用驗證的旗標。因為它燒進了硬體，即使攻擊者能改寫所有 flash 分區，也無法改變這個信任根。開機最初階段的程式碼（ROM code / 廠商 bootloader）會信任這個根，並以它為起點往上驗證。

### 逐層驗證

信任鏈的運作邏輯是「已驗證的程式碼負責驗證下一段程式碼」：

1. **ROM code**（燒在晶片裡，天生可信）驗證並載入 **bootloader**。
2. **Bootloader** 使用信任根中的公鑰，驗證 **vbmeta** 分區的簽章。vbmeta 是整個 AVB 的樞紐，裡面存放了其他分區的驗證資訊。
3. 一旦 vbmeta 本身通過驗證，bootloader 就信任 vbmeta 裡記載的所有 hash 與 metadata，並據此驗證 **boot / init_boot / vendor_boot** 等分區。
4. Kernel 啟動後，對於 `system`、`vendor`、`product` 這類大型唯讀分區，改由 **dm-verity** 在執行期持續驗證（見第四節）。

這條鏈的關鍵性質是：**任何一環被竄改，簽章或 hash 就對不上，驗證會在那一環中斷。** 攻擊者無法從中間插入自己的程式碼，因為他沒有對應的私鑰去重新簽署，而信任根又改不了。

---

## 三、vbmeta 分區：AVB 的樞紐

理解 AVB，最重要的就是理解 `vbmeta` 這個分區。它不存放實際的系統內容，而是存放**「如何驗證其他分區」的 metadata 與簽章**。

### vbmeta 的結構

一個 vbmeta image 大致由這幾個部分組成：

- **Header**：描述整個 vbmeta 的版本、各區塊大小與偏移、演算法等。
- **Authentication data**：包含對 vbmeta 內容的簽章（signature）與雜湊（hash）。這是 bootloader 用信任根公鑰去驗證的對象。
- **Auxiliary data**：真正承載驗證資訊的區塊，裡面是一連串 **descriptor**。

### Descriptor：AVB 的資訊單元

Auxiliary data 裡的 descriptor 是 AVB 表達「該驗證什麼」的基本單位，常見類型包括：

- **Hash descriptor**：用於**小型、需整塊載入記憶體**的分區，例如 `boot`、`init_boot`、`vendor_boot`。它記錄整個分區內容的一個雜湊值。bootloader 把分區整個讀進來，算出 hash 跟 descriptor 裡的值比對，一致才放行。適合 boot 這種載入時就會整份讀入的分區。
- **Hashtree descriptor**：用於**大型唯讀**分區，例如 `system`、`vendor`、`product`。它記錄的是一棵 hash tree（Merkle tree）的根雜湊與相關參數，交給 dm-verity 在執行期逐區塊驗證（見第四節）。因為這些分區可能有數 GB，不可能開機時整份算一次 hash，所以用 hash tree 做「用到哪塊驗哪塊」。
- **Chain partition descriptor**：這是 AVB 2.0 一個重要的彈性設計。它允許某個分區（例如 `vendor`）**使用另一把獨立的金鑰**來驗證，並把該分區的 vbmeta 資訊「鏈結」出去。這讓 SoC 廠商、ODM、OEM 可以各自管理自己分區的簽署權限——例如晶片商簽 `vbmeta_vendor`，OEM 簽主 `vbmeta`——而不必共用同一把私鑰。
- **Kernel command line descriptor**：讓 AVB 可以在驗證通過後，動態往 kernel command line 注入參數（例如啟用 dm-verity 的相關參數）。
- **Property descriptor**：儲存任意的 key-value 資訊，供 bootloader 或系統讀取。

### vbmeta 的「總開關」角色

因為主 `vbmeta` 分區透過 hash descriptor 與 chain descriptor 涵蓋（或鏈結）了其他所有分區的驗證資訊，它實際上成為整個裝置驗證狀態的**單一入口**。這也是為什麼——如同後面刷機章節會談到——刷入一個「空的」或「停用驗證旗標」的 vbmeta，就等於一次關掉整條鏈的驗證。

---

## 四、dm-verity：執行期的區塊級驗證

對於 `boot` 這種開機時整份載入的小分區，開機時算一次 hash 就夠了。但 `system`、`vendor` 動輒好幾 GB，而且是掛載後才被陸續讀取，不可能在開機時整份驗證完。這就是 **dm-verity** 登場的地方。

dm-verity 是 Linux kernel `device-mapper` 的一個 target，它在被保護的分區之上疊一層透明的驗證層。運作方式如下：

1. **建立 hash tree**：把分區內容切成固定大小的區塊（通常 4 KiB），對每個區塊算 hash，這些 hash 又組成下一層，逐層往上收斂，最後形成一棵 Merkle tree，頂端是一個**根雜湊（root hash）**。
2. **根雜湊被 AVB 保護**：這個 root hash 存在 vbmeta 的 hashtree descriptor 裡，並且被 vbmeta 的簽章覆蓋。所以只要 vbmeta 通過驗證，root hash 就是可信的。
3. **執行期逐塊驗證**：當系統實際去讀取分區的某個 4 KiB 區塊時，dm-verity 即時計算該區塊的 hash，並沿著 hash tree 一路驗證到 root hash。只要有任何一塊被竄改，hash 對不上，讀取就會失敗。

這種設計的精妙之處在於：**驗證成本只在真正讀取資料時才付出**，而且是區塊粒度，不需要開機時掃描整個分區。代價是每次讀取多了 hash 計算的開銷，但現代 SoC 對此有硬體加速，實務上影響很小。

### 驗證失敗時怎麼辦？

dm-verity 支援不同的錯誤處理模式。在正式量產、bootloader 上鎖的裝置上，讀到損毀區塊通常會導致 I/O 錯誤甚至裝置重啟或進入救援，以確保絕不執行被竄改的內容。這也是為什麼刷了自訂 `system` 卻沒處理好 verity 的裝置，會開機開到一半崩潰或 bootloop。

---

## 五、Rollback Protection：防止降級攻擊

光是驗證「內容有沒有被改」還不夠。設想一個情境：某個舊版 Android 有一個已知漏洞，後來的更新修掉了。攻擊者雖然沒辦法偽造新映像（沒有私鑰），但他手上有一份**過去官方正式簽署過的舊版映像**——那份映像的簽章是完全合法的。如果沒有額外防護，他就能把裝置「降級」回那個有漏洞的版本，再利用漏洞攻擊。這叫 **rollback / downgrade attack**。

AVB 的 **rollback protection（防回滾）** 就是為此設計。做法是：

- 每個 vbmeta 帶有一個 **rollback index**（單調遞增的版本序號）。
- 裝置在一個**防竄改的儲存位置**（例如 RPMB、專用的 eFuse，或 TEE 保護的區域）記錄它「見過的最高 rollback index」。
- 開機驗證時，如果映像的 rollback index **低於**裝置記錄的值，就代表這是一個舊版本，驗證失敗、拒絕開機。
- 成功開機到一個更新的版本後，裝置會把記錄的 index 往上更新，之後就再也回不去更舊的版本了。

AVB 2.0 還支援**多個 rollback index location（index slot）**，讓不同的分區群組可以有各自的防回滾計數器，配合 chain partition 的多金鑰設計，讓 OEM 與廠商能獨立管理各自元件的版本下限。

---

## 六、開機狀態：GREEN / YELLOW / ORANGE / RED

AVB 把驗證的結果對應到四種**開機狀態（boot state）**，並要求 bootloader 依狀態向使用者顯示對應的警告。這套顏色狀態同時反映了「bootloader 是否上鎖」與「用的是誰的金鑰」：

- **GREEN**：bootloader 已上鎖（locked），且系統由**裝置原廠的信任根金鑰**驗證通過。這是量產裝置的正常狀態，不顯示任何警告，安全等級最高。
- **YELLOW**：bootloader 已上鎖，但系統是由**使用者自行設定的信任根金鑰**驗證通過的（例如玩家自編譯 AOSP、刷了自簽的 GSI 並把自己的公鑰寫進裝置）。開機時會顯示警告畫面，告知使用者作業系統由自訂金鑰簽署，並通常顯示該金鑰的指紋。
- **ORANGE**：bootloader 已**解鎖（unlocked）**，AVB 不進行驗證。這是開發與刷機的狀態，開機時顯示「bootloader 已解鎖、無法保證裝置完整性」的警告。
- **RED**：驗證**失敗**——例如映像被竄改、簽章對不上，但 bootloader 仍處於上鎖狀態。這種情況下裝置通常會拒絕繼續開機。

你在解鎖 bootloader 或刷機後看到的那個開機警告畫面，本質上就是 AVB 在如實回報當前的 boot state。這個「明確告知使用者」的設計本身也是安全模型的一部分：即使使用者選擇解鎖與客製化，系統也不會假裝一切正常。

值得一提的是，這些狀態會透過 **Keystore / Keymaster** 傳遞給 **Android Keystore**，影響金鑰的 attestation 結果。也就是說，一旦裝置解鎖或驗證狀態改變，某些依賴硬體驗證的功能（例如部分金融、DRM、企業合規 app 的完整性檢查）可能會偵測到並拒絕運作。

---

## 七、AVB 在整體 Android 安全模型中的位置

AVB 不是孤立的機制，它是 Android 縱深防禦的**地基層**，往上支撐了好幾個關鍵能力：

**與檔案加密的關係**：Android 的 File-Based Encryption（FBE）與金鑰管理依賴一個「可信的系統」來保管與使用金鑰。如果系統本身可以被竄改，加密就失去意義——被改過的系統可以偷走金鑰。AVB 保證了「只有通過驗證的系統」才會被載入，也才能存取受保護的金鑰。

**與 Keystore / 硬體 attestation 的關係**：如上所述，boot state 會納入 key attestation，讓遠端伺服器能驗證一台裝置的開機完整性。這是許多企業 MDM、支付、內容保護服務判斷「這台裝置可不可信」的依據之一。

**與 OTA 更新的關係**：AVB 確保推送下來的系統映像是完整、真實、未在傳輸過程中被掉包的。搭配 A/B（seamless）更新機制，新映像寫入備用 slot 後同樣要通過 AVB 驗證才會被切換為開機 slot，驗證失敗還能回退到舊 slot，兼顧安全與可靠。

可以說，AVB 回答的是一個最根本的問題：**「我現在跑的這個系統，是不是那個我原本信任的系統？」** 沒有這個保證，上面所有的加密、金鑰、權限機制都是建立在流沙上。

---

## 八、開發與刷機實務：與 AVB 打交道

對系統開發者、ROM 維護者、或想刷自訂系統的人來說，AVB 是最常需要「處理」的一道關卡。以下是幾個典型場景與做法。**注意：以下操作多半需要先解鎖 bootloader，且會使裝置進入 ORANGE/YELLOW 狀態、觸發資料清除，請務必先備份。**

### 為什麼刷了自訂映像會開不了機

當你刷入一個自己修改或編譯的 `system`、`vendor` 或 `boot`，它的內容 hash 就跟原本 vbmeta 裡記載的對不上了。在上鎖或仍啟用驗證的裝置上，AVB 會判定驗證失敗（RED），拒絕開機或 bootloop。要順利開機，你必須**告訴 AVB 別去驗證這些你改過的分區**，或是**用你自己的金鑰重新簽署並讓裝置信任你的金鑰**。

### 常見做法一：停用驗證（刷 vbmeta 旗標）

最常見的快速做法，是刷入原廠的 `vbmeta.img` 但帶上停用旗標：

```bash
# 停用 AVB 驗證與 dm-verity，讓改過的分區能開機
fastboot --disable-verity --disable-verification flash vbmeta vbmeta.img
```

這兩個旗標會在 vbmeta 的 header 裡設定對應的 disable flag：

- `--disable-verification`：關閉 AVB 對分區的完整性驗證。
- `--disable-verity`：關閉 dm-verity（`system`/`vendor` 的執行期 hashtree 驗證）。

如果裝置有多個 vbmeta（例如 `vbmeta_system`、`vbmeta_vendor`），可能需要對每一個都比照處理。

### 常見做法二：刷入空白 vbmeta

某些教學會提供或建議刷一個「空的」vbmeta——不含任何 descriptor、或明確帶停用旗標——效果同樣是讓 AVB 不去驗證後續分區。GSI（Generic System Image）測試常用這種方式，因為 GSI 的 `system` 顯然跟原廠 vbmeta 對不上。

### 常見做法三：用自己的金鑰重新簽署（YELLOW 狀態）

如果你在做正式的自訂 ROM，較嚴謹的做法是用 `avbtool` 產生自己的金鑰、重新簽署映像與 vbmeta，並把自己的公鑰寫進裝置（`fastboot flash avb_custom_key`）。這樣裝置會以你的金鑰驗證系統，進入 YELLOW 狀態——依然有完整的驗證保護，只是信任根換成了你的金鑰，而不是完全關掉驗證。這比直接停用驗證安全得多，適合要發布給他人使用的 ROM。

`avbtool` 是 AOSP 原始碼樹裡（`external/avb`）提供的官方工具，可以用來產生 vbmeta、加簽 hash / hashtree descriptor、產生金鑰、以及檢視現有 vbmeta 的內容。想理解一個映像的 AVB 結構時，`avbtool info_image` 是很實用的除錯起點：

```bash
# 檢視一個映像 / vbmeta 的 AVB metadata（descriptor、旗標、演算法等）
avbtool info_image --image vbmeta.img
```

### 一個常見的坑：改一個地方，驗證卻在別處失敗

因為 vbmeta 是一整條鏈的樞紐，開發者常犯的錯誤是「只處理了 `boot`，卻忘了 `system` 的 dm-verity 仍在生效」，導致開機到掛載 `system` 時才崩潰。除錯時的心法是：**先在腦中把這台裝置的信任鏈畫出來**——有哪些 vbmeta 分區？主 vbmeta 用 chain descriptor 鏈結了哪些子 vbmeta？哪些分區走 hash、哪些走 hashtree？想清楚後，才知道要在哪一層下停用旗標或重新簽署。

### 上鎖前務必三思

反過來，如果要把一台刷過自訂系統的裝置**重新上鎖**（`fastboot flashing lock`），一定要確保裝置上所有分區都能通過某把裝置信任的金鑰的驗證。否則上鎖後 AVB 會判 RED、拒絕開機，而你又處在上鎖狀態無法輕易刷回——這是導致裝置變磚（brick）的經典原因。務必在上鎖前確認系統是完整、可驗證的官方或正確簽署的映像。

---

## 九、小結

Android Verified Boot 是 Android 安全架構中最底層、也最容易被忽略的一環。它從一個燒在硬體裡、改不掉的信任根出發，透過 vbmeta 這個樞紐把 bootloader、boot 映像、以及 `system`/`vendor` 等大型分區的驗證資訊串成一條完整的信任鏈：小分區用 hash descriptor 整塊驗證，大分區交給 dm-verity 做區塊級的執行期驗證，rollback index 擋掉降級攻擊，而 GREEN/YELLOW/ORANGE/RED 四種 boot state 則如實地把驗證結果呈現給使用者與上層的 attestation 機制。

對開發者而言，AVB 既是保護裝置與使用者資料的地基，也是客製化系統時必須理解與正確處理的關卡。理解它的信任鏈與 vbmeta 結構，你就能明白為什麼刷機要處理 vbmeta、為什麼改一個分區會在另一個地方開不了機、以及為什麼重新上鎖前必須格外小心。一句話總結：**AVB 回答的是「跑在這台裝置上的，是不是那個我原本信任的系統」——這個問題的答案，決定了其上一切安全機制是否站得住腳。**
