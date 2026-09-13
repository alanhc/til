# 機密要放哪裡？從 OP-TEE Secure Storage 看 HDCP 與 Widevine 的金鑰儲存全景

> 本文全部內容取自公開資料（OP-TEE 官方文件、JEDEC/DCP 規格公開描述、學術論文、Linaro 簡報、SoC 廠商公開手冊），不包含任何廠內資訊。
> 文中以〔查證〕標示有公開來源可對照的敘述，以〔推論〕標示我根據機制推導、但沒有找到明確公開出處的部分。

---

## 一、為什麼把 HDCP 和 Widevine 放在一起談

在 Android 平台整合的日常裡，這兩個東西常常在同一週壞掉：

- 「這台機器 Widevine 掉到 L3 了，Netflix 只剩 SD。」
- 「接外接螢幕會黑畫面，log 說 HDCP authentication failed。」

表面上一個是 DRM、一個是輸出保護，但它們在系統設計上其實是**同一個問題的兩端**：都有一批「出廠時燒進去、之後不能外洩、不能被回滾、不能被複製到另一台機器」的長期機密，而這些機密最後都得落在同一組儲存機制上。

所以與其分開讀，不如先把**整個機密儲存的地形圖**畫出來，再看 HDCP 和 Widevine 各自站在哪一格。這篇文章就是這張地形圖。

---

## 二、先分類：三種機密，生命週期完全不同

在談「存哪裡」之前，得先分清楚要存的是什麼。一台裝置上的內容保護相關機密，大致分成三層：

### 第 1 層：不可變的信任根（immutable RoT）

出廠燒錄，之後永遠不能改，通常也永遠不能被軟體讀出明文。

| 項目 | 典型載體 | 用途 |
|---|---|---|
| HUK（Hardware Unique Key） | SoC eFuse / OTP | 派生 TEE 內所有儲存金鑰 |
| Chip ID / Die ID | SoC OTP | 綁定裝置身份，參與金鑰派生 |
| RPMB authentication key | eMMC/UFS 內部 OTP | 認證 RPMB 存取 |
| Boot ROM 公鑰 hash | SoC eFuse | Secure Boot 驗簽 |

〔查證〕OP-TEE 明確要求平台實作 `tee_otp_get_hw_unique_key()` 與 `tee_otp_get_die_id()`；若平台沒實作而用了預設常數，官方文件直接寫「沒有任何防護，secure storage 可被解密或複製到其他裝置」。這句話值得貼在辦公桌上。

### 第 2 層：出廠 provision 的長期憑證

這一層是本文的主角。它們**不是燒在 eFuse**（太大、且部分需要可更新），而是以加密 blob 的形式存在某個 flash 區域，開機後由 TA 解開使用。

- Widevine keybox（或後續換來的 device certificate）
- HDCP 1.4 的 DPK 集合、HDCP 2.x 的 device private key 與 certificate
- Attestation key（Keymaster/KeyMint）
- 各家廠商自訂的 DRM / CAS 憑證

特徵是：**一次性、不可再生、遺失即報廢，而且必須防回滾**。

### 第 3 層：執行期產生的短期金鑰

Content key、session key、HDCP 的 `ks`／`kd`、TLS session key。這一層存活在 secure memory，通常根本不落地。落地的話就是設計錯誤。

> 這個三層分類是理解後面所有取捨的基礎：**第 1 層拼硬體、第 3 層拼記憶體隔離、第 2 層拼儲存**。而第 2 層正是最容易出包的一層。

---

## 三、儲存介質的地形圖

Android + TEE 的裝置上，第 2 層機密實際上只有這幾個地方可以放：

| 介質 | 容量 | 防回滾 | 防抹除 | 早期開機可用 | 典型用途 |
|---|---|---|---|---|---|
| SoC eFuse / OTP | 數百 bits ~ 數 KB | 天生（燒了不能改） | 是 | 是 | HUK、chip ID、少量小金鑰 |
| eMMC/UFS **RPMB** | 128 KB 的倍數，最大 16 MB〔查證〕 | **是**（write counter + HMAC） | 是（不受 userdata wipe 影響） | 需 storage driver 起來 | 防回滾計數器、小型機密 |
| **REE FS**（`/data/tee`，加密後放一般檔案系統） | 幾乎不限 | 否（明顯弱點） | **否**（factory reset 會掉） | 否（要等 `/data` mount） | 一般 TA 持久化資料 |
| 獨立 raw partition（`/persist`、`/vendor_boot` 旁的私有分割區） | 依規劃 | 否（除非另外配 counter） | 是（不在 userdata 內） | 是 | keybox、HDCP blob 的常見落點 |
| Secure OTP / 廠商專屬安全區 | 依 SoC | 是 | 是 | 是 | 廠商自訂 |

這張表已經回答了大半問題：**沒有任何一格同時滿足「大容量 + 防回滾 + 防抹除 + 早期可用」**。實務上都是組合拳，這就是為什麼各家 SoC 的做法看起來都不太一樣。

---

## 四、OP-TEE Secure Storage 的機制細節

### 4.1 API 面：GlobalPlatform 的 Persistent Object

TA 這一側看到的介面很單純，就是 GP TEE Internal Core API 的持久化物件：

```c
TEE_Result res;
TEE_ObjectHandle obj;
const char id[] = "widevine.keybox";

res = TEE_CreatePersistentObject(
        TEE_STORAGE_PRIVATE_RPMB,        /* storageID：決定落在哪個後端 */
        (void *)id, sizeof(id),
        TEE_DATA_FLAG_ACCESS_WRITE | TEE_DATA_FLAG_OVERWRITE,
        TEE_HANDLE_NULL,                  /* 沒有 attribute，純 data object */
        keybox, sizeof(keybox),
        &obj);
```

〔查證〕OP-TEE 支援兩個後端同時存在，用不同的 storage ID 區分：`TEE_STORAGE_PRIVATE_REE` 與 `TEE_STORAGE_PRIVATE_RPMB`（`TEE_STORAGE_PRIVATE` 則對應編譯期選定的預設）。

關鍵在於：**object ID 的命名空間是 per-TA 的**。A TA 存的 `"keybox"` 和 B TA 存的 `"keybox"` 是兩個不同的檔案，因為加密金鑰本身就綁了 TA UUID（見下節）。這也代表：**TA UUID 一改，舊資料就永遠讀不回來了**——這是升級時很經典的一個坑。

### 4.2 金鑰階層：HUK → SSK → TSK → FEK

〔查證〕OP-TEE 的四層派生：

```
HUK (硬體唯一金鑰，來自 OTP)
 │
 └─ SSK  = HMAC-SHA256(HUK, ChipID || 固定字串)      ← 每台裝置一把
     │
     └─ TSK  = HMAC-SHA256(SSK, TA_UUID)              ← 每個 TA 一把
         │
         └─ FEK  (每個檔案隨機產生，用 TSK 加密後放在該檔 metadata)
```

這個設計的意義：

- **跨裝置不可搬移**：SSK 綁 HUK 與 chip ID，把 image dump 到另一台機器解不開。
- **跨 TA 不可讀**：惡意 TA 拿不到別人的 TSK。
- **每檔獨立**：FEK 隨機，單一檔案洩漏不會擴散。

### 4.3 REE FS：加密後寄放在 normal world

〔查證〕REE FS 把加密後的檔案放在 `/data/tee/<file_number>`，另有一個 `/data/tee/dirf.db` 作為目錄檔，列出所有持久化物件。完整性以二元 hash tree 保護，metadata 與 block data 都用 AES-GCM；每次更新採 out-of-place 策略並維護版本 0/1 兩份，藉此達成 Write／Truncate／Rename／Create／Delete 的原子性。

它的優點是容量幾乎不限、實作簡單；缺點非常明確，而且是本文的重點：

1. **不防回滾**。整個 `/data/tee` 是 normal world 拿得到的檔案，任何人可以先備份、之後蓋回去。加密和 hash tree 保護的是「機密性」與「完整性」，不是「新鮮度」。
2. **不防抹除**。`/data` 被 wipe（factory reset、fastboot -w、userdata 損毀重建）就整批消失。
3. **依賴 tee-supplicant**。實際 I/O 由 normal world 的 `tee-supplicant` 代理，`/data` 沒 mount 之前不能用——這對「開機早期就要 HDCP」的場景是致命的。

〔推論〕正因為第 2 點，把 Widevine keybox 單獨放 REE FS 是危險的：一次 factory reset 就等於永久失去 L1，而 keybox 通常無法在售後重新 provision。

### 4.4 RPMB FS：真正能防回滾的那一格

〔查證〕OP-TEE 的 RPMB 分割區佈局：開頭 128 bytes 是 partition metadata；offset 512 起是 FAT（每個檔案一個 entry）；檔案資料則從尾端往前配置。加密使用 AES-CBC 搭配 ESSIV，IV 由 block index 以 FEK 的 SHA-256 加密導出。原子性來自兩點：eMMC 規格保證單一 RPMB block 寫入是原子的，且 FAT 更新一定排在資料寫入成功之後。

RPMB 之所以能防回滾，靠的是 eMMC/UFS 內部的兩樣東西：

- **一把 32-byte 的 authentication key**，寫入後不可讀、不可改（一次性）。
- **一個單調遞增的 write counter**。每次成功寫入 +1，主機端必須在請求裡帶對的 counter 值與 HMAC-SHA256，否則裝置直接拒絕。

所以「把舊資料整包蓋回去」這招在 RPMB 上不成立——舊資料裡的 counter 已經過期了。

**RPMB key 的燒錄**是整條路上最容易做出磚頭的一步。〔查證〕OP-TEE 提供三種模式：

| 設定 | 行為 | 風險 |
|---|---|---|
| 產線用 mmc-tools 手動燒 | 最安全，在受控環境完成 | 需要產線流程配合 |
| `CFG_RPMB_WRITE_KEY=y` | 由 OP-TEE 自行燒錄 | 金鑰可能在裝置尚未鎖定時被 normal world 觀察到 |
| `CFG_RPMB_TESTKEY=y` | 用固定常數測試金鑰 | **絕不可進量產** |
| `CFG_RPMB_TESTKEY=n` | 由 HUK 與 eMMC 序號派生 | 官方建議的量產做法 |

〔查證〕OP-TEE 也要求平台實作 `plat_rpmb_key_is_ready()`，避免在板子安全狀態還沒建立前就把 key 燒下去。

〔推論〕注意最後一列的隱藏成本：如果 RPMB key 派生自「HUK + eMMC 序號」，那麼**換 eMMC 料件、或維修更換儲存裝置，就等於 secure storage 全滅**。這是產品決策，不只是韌體決策——而在整合階段常常沒人問這個問題，直到 RMA 流程跑起來才發現。

### 4.5 RPMB 的容量現實

〔查證〕eMMC 的 RPMB 分割區大小由 `RPMB_SIZE_MULT` 決定，單位 128 KB，最大 128 倍即 16 MB；實務上量產配置常見 4 MB。

〔推論〕這個數字決定了架構：4 MB 聽起來不小，但它同時要服務 Keymaster/KeyMint 的 rollback counter、bootloader lock state、AVB rollback index、Trusty/OP-TEE 自己的 metadata……真正留給 DRM 的空間相當有限。所以常見的折衷是：

> **大 blob 放別處，防回滾的「證據」放 RPMB。**
>
> 也就是：keybox 或 HDCP key blob 的密文放在獨立分割區或 REE FS，而它的版本號／hash／一次性 provisioning 旗標放進 RPMB。想回滾？密文可以蓋回去，但 RPMB 裡的 counter 對不上，TA 就拒絕載入。

〔推論〕這個 pattern 在各家實作中反覆出現，我認為是這類系統最值得記住的一個設計原則。

---

## 五、Widevine 這條線

### 5.1 L1 / L3 到底差在哪

〔查證〕依公開的學術研究整理：

- **L1**：加解密與影像處理**都在 TEE 內**，可播 HD/4K。
- **L2**：Android 上實務不採用。
- **L3**：純軟體實作，操作在 TEE 外，解析度受限（通常 SD）。

一台機器「掉到 L3」的意思，多半不是 TEE 壞了，而是 **L1 所需的憑證讀不到或驗不過**，framework 於是 fallback。

### 5.2 Keybox：128 bytes 的信任根

〔查證〕公開研究文獻整理出的 keybox 結構，總長 **128 bytes**：

| 欄位 | 長度 | 說明 |
|---|---|---|
| Device ID | 32 bytes (256-bit) | 裝置唯一識別 |
| Device Key | 16 bytes (128-bit AES) | 真正的 root of trust |
| Provisioning Token / Key Data | 72 bytes (576-bit) | provisioning 請求時使用 |
| Magic | 4 bytes | ASCII `"kbox"` |
| CRC-32 | 4 bytes | 完整性檢查 |

〔查證〕研究者指出，keybox 的完整性驗證即是檢查最後 8 bytes 是否為 magic + CRC-32。

這 128 bytes 就是整台裝置 L1 能力的全部。它由 Widevine 產生、在產線階段寫入裝置，**且無法在售後重新產生**。

### 5.3 落地位置：由 OEM 決定，因此每家都不一樣

Widevine 只規定「OEMCrypto 實作必須把 keybox 存在安全、無法被一般軟體讀取的地方」，具體位置是 OEM 的自由。〔查證〕公開研究中觀察到的實例：

- 某 Qualcomm 平台 L1：keybox 加密後放在 Secure File System，路徑 `/persist/data/sfs/keybox_lvl1.dat`。
- L3（純軟體）：keybox 從 `/data/mediadrm/IDMxxxx/L3/ay64.dat` 載入。
- Device RSA key：以 `cert.bin` 形式存在 `/data/mediadrm/IDMxxxx/`。

〔推論〕注意上面的對比很有意思：L1 的 keybox 放在 **`/persist`（不隨 factory reset 消失）**，而 L3 的資料放在 **`/data`（會消失）**。這正好呼應第三節的表格——L3 的憑證可以重新 provision，L1 的不行，所以只有 L1 的那份必須放在抹不掉的地方。

### 5.4 兩階段：keybox 換 certificate

〔查證〕公開研究把流程拆成三段：

1. **Certificate provisioning**：裝置產生 nonce，用 root of trust 派生金鑰，組出帶 HMAC 保護的請求，向 provisioning server 換取裝置憑證。
2. **License provisioning**：以 RSA 簽名的請求取得 session key，再派生出內容金鑰。
3. **Content decryption**：以 AES-128-CTR 解 MPEG-CENC 內容。

〔推論〕這代表裝置上其實有**兩份**要保護的長期資料：出廠燒進去的 keybox，以及第一次上網後換回來的 device certificate。前者絕對不能掉；後者掉了可以重換，但如果 provisioning token 是一次性的、或伺服器端對重複 provisioning 有頻率限制，「可以重換」也可能不如想像中可靠。整合時值得實測一次「清掉 certificate 後能不能自動復原」，而不是假設它可以。

### 5.5 為什麼 unlock bootloader 會掉 L1

〔推論〕Widevine 的 robustness 要求 keybox 只在裝置處於受驗證的開機狀態時可用。bootloader 解鎖後，AVB 的信任鏈斷了，TA 無法保證跑在其上的 OS 未被竄改，因此正確的實作應該**主動拒絕載入 keybox**。這不是 bug，是設計。網路上大量「解鎖後修復 L1」的討論，本質上都是在繞過這個檢查。

---

## 六、HDCP 這條線

HDCP 的機密和 Widevine 有一個關鍵差異：**它是 DCP（Digital Content Protection LLC）授權發放的，並且受 robustness rule 約束**——規範直接要求這些金鑰不得以明文形式離開受保護的硬體邊界。

### 6.1 HDCP 1.4 要存什麼

- **KSV**（Key Selection Vector）：40-bit，公開值，authentication 時會送出去。
- **Device Private Keys**：**40 把 56-bit 金鑰**，共 280 bytes，機密。

〔推論〕280 bytes 很小，理論上塞得進 eFuse，但因為需要可撤銷／可更換的彈性，實務上多半仍以加密 blob 形式儲存。

### 6.2 HDCP 2.2/2.3 要存什麼

依 DCP 公開的 HDCP 2.2 on HDMI 規格：

- **Receiver 端**
  - `cert_rx`：**522 bytes** 的裝置憑證 = Receiver ID (5) + 公鑰 (131：128-byte modulus + 3-byte exponent) + Reserved (2) + DCP 的 RSA-3072 簽章 (384)。此為公開資料。
  - `kpriv_rx`：對應的 RSA 私鑰。**最高機密**。
- **Transmitter 端**
  - `lc128`：128-bit **全域常數**，由 DCP 發給所有授權者，用於派生 `kd`。這一把之所以敏感，是因為它**全世界共用一把**——洩漏一次，影響所有裝置。
- **雙方共用的執行期產物**：`km`、`kd`、`ks`、`riv`，這些屬於第 3 層，不落地。

〔查證〕HDCP 2.2 認證流程分為 AKE（驗證接收端持有有效且未被撤銷的公鑰憑證）、Locality Check（確認接收端在鄰近範圍）、SKE（交換 session key）、以及 repeater 情境下的下游拓撲驗證。

### 6.3 存放與使用方式

〔推論，但與公開實作一致〕典型做法是：

1. 產線把 HDCP key set 以裝置專屬金鑰加密成 blob，寫入獨立分割區（或 TEE secure storage）。
2. 開機或第一次要輸出時，HDCP TA 從 secure storage 讀出 blob、在 secure world 解密。
3. 明文金鑰**不回傳給 normal world**，而是直接寫進 HDMI/DP controller 的安全暫存器；該暫存器區間由 TZASC 之類的位址空間控制器保護，normal world 讀不到也寫不到。

〔查證〕Linaro 的 OP-TEE HDCP 提案正是沿這條路走：把 HDCP 控制從 kernel（libDRM）搬進一個 HDCP TA，由 TA 監管暫存器存取、以 TZASC 保護 HDCP 暫存器，並與 Widevine／PlayReady TA 做 session 層級的整合。該簡報明確指出動機：**在現行 Linux 端管理 HDCP 的架構下，沒有任何機制阻止使用者在安全內容播放中途把 HDCP 關掉**。

〔查證〕同一份簡報也坦承：硬體 IP（該案例為 Cadence）搭配的是非開源韌體，因此金鑰實際如何存放與管理仍未公開。這也是為什麼 HDCP 的儲存細節在公開文獻裡遠比 Widevine 稀少。

---

## 七、把兩條線疊在一起：一張決策表

回到最初的問題——這些東西到底該放哪？我把判準整理成四個問題：

| 判準 | Widevine keybox | Widevine cert | HDCP key blob | Rollback counter |
|---|---|---|---|---|
| 大小 | 128 B | ~KB | 數百 B ~ KB | 數十 B |
| factory reset 後必須存活？ | **必須** | 最好 | **必須** | **必須** |
| 需要防回滾？ | 是（防重放舊 provisioning 狀態） | 中等 | 是（防裝回被撤銷的憑證） | **本體** |
| 開機早期就要用？ | 否（播放時才要） | 否 | **可能是**（開機畫面就要輸出） | 是 |
| → 合理落點 | 獨立分割區 / RPMB | REE FS + RPMB counter | 獨立分割區 / RPMB | **RPMB** |

〔推論〕結論其實很簡單：**RPMB 是稀有資源，把它花在「證據」而不是「內容」上**。128 bytes 的 keybox 直接放 RPMB 沒問題；幾 KB 的 HDCP blob 就要衡量；而真正非 RPMB 不可的，是那些用來判斷「你手上這份密文是不是最新的」的計數器。

---

## 八、整合工程師的踩雷清單

整理幾個在系統整合階段會遇到、且成因都指向本文機制的問題：

**1. `CFG_RPMB_TESTKEY=y` 流到量產**
測試金鑰是公開常數，等於 RPMB 沒有防護。開發階段方便，但必須在量產映像檔關掉，且要有 CI 檢查而不是靠 code review。

**2. RPMB key 燒錄失敗 → 磚**
RPMB key 是一次性的。燒到一半斷電、或燒了錯的值，這顆 eMMC 的 RPMB 就永遠不可用。產線流程必須有「已燒錄」的可查詢狀態。

**3. 換 eMMC 料件導致 secure storage 全滅**
若 RPMB key 派生自 eMMC 序號，換料等於換金鑰。這件事要在料號決策階段就問清楚。

**4. `/data` wipe 後 Widevine 掉 L1**
如果 keybox 或其 provisioning 狀態被放在 REE FS，factory reset 就會帶走它。判斷方法很直接：wipe 前後各跑一次 `dumpsys media.drm`，看 security level 有沒有變。

**5. TA UUID 或 HUK 變更導致舊資料讀不回**
TSK 綁 TA UUID、SSK 綁 HUK 與 chip ID。改任一個，`TEE_OpenPersistentObject()` 就會回 `TEE_ERROR_ITEM_NOT_FOUND`。跨版本升級時特別要注意 TA 重構有沒有順手改到 UUID。

**6. bootloader 解鎖後 L1 消失**
如第 5.5 節，這是預期行為。收到這類回報時要先確認裝置的 lock state，而不是先查 TA。

**常用的檢查手段**（都是公開工具）：

```bash
# Widevine 目前的 security level 與支援的 scheme
adb shell dumpsys media.drm

# 檢查 DRM plugin 是否正常載入
adb logcat -s DrmHal ClearKeyCryptoPlugin

# OP-TEE 這一側的 secure storage I/O（需 tee-supplicant 有開 log）
adb logcat | grep -i tee-supplicant

# eMMC RPMB 分割區大小（RPMB_SIZE_MULT，單位 128KB）
adb shell cat /sys/class/mmc_host/mmc0/mmc0:0001/raw_rpmb_size_mult
```

---

## 九、小結

三句話：

1. **機密要分層看**。eFuse 存不可變的根、RPMB 存防回滾的證據、REE FS 或獨立分割區存大塊密文——沒有一格能全包。
2. **OP-TEE 的 secure storage 保證的是機密性、完整性、原子性，但 REE FS 不保證新鮮度**。要防回滾，只有 RPMB 那條路。
3. **Widevine 與 HDCP 在儲存層面是同一個問題**：一批一次性、不可再生、必須綁定裝置的長期憑證。它們壞掉的原因，多半不在 DRM 邏輯，而在儲存與 provisioning 的邊界條件——factory reset、換料、解鎖、UUID 變更。

---

## 參考資料

1. [Secure storage — OP-TEE Documentation](https://optee.readthedocs.io/en/latest/architecture/secure_storage.html) — REE FS / RPMB FS 架構、SSK/TSK/FEK 金鑰階層、hash tree、RPMB 佈局與 key programming 選項
2. [Secure Storage in OP-TEE — Jens Wiklander, Linaro Connect SFO17-309](https://static.linaro.org/connect/sfo17/Presentations/SFO17-309%20Secure%20storage%20updates.pdf)
3. [Secure Storage Updates in OP-TEE — Linaro Connect LAS16-504](http://static.linaro.org/connect/las16/Presentations/Friday/LAS16-504%20-%20Secure%20Storage%20updates%20in%20OP-TEE.pdf)
4. [HDCP Support in OP-TEE — Linaro Connect SAN19-507](https://static.linaro.org/connect/san19/presentations/san19-507.pdf) — HDCP TA 設計動機、TZASC 保護、與 Widevine/PlayReady TA 的整合
5. [Exploring Widevine for Fun and Profit — Gwendal Patat et al., arXiv:2204.09298](https://arxiv.org/pdf/2204.09298) — keybox 結構、L1/L3 定義、OEMCrypto API、provisioning 流程、實測到的儲存路徑
6. [Diving into the depths of Widevine L3 — Neodyme](https://neodyme.io/en/blog/widevine_l3/)
7. [HDCP 2.2 on HDMI Specification, Rev. 2.2 — Digital Content Protection LLC](https://www.digital-cp.com/sites/default/files/specifications/HDCP%20on%20HDMI%20Specification%20Rev2_2_Final1.pdf) — cert_rx 結構、lc128、AKE/LC/SKE 流程
8. [Understanding HDMI & HDCP 2.2 Authentication — Synopsys](https://www.synopsys.com/blogs/chip-design/hdmi-hdcp2-authentication-process.html)
9. [Widevine DRM Overview — Google for Developers](https://developers.google.com/widevine/drm/overview)
10. [Trusty TEE — Android Open Source Project](https://source.android.com/docs/security/features/trusty)
11. [i.MX Android Security User's Guide (UG10158) — NXP](https://www.nxp.com/docs/en/user-guide/UG10158.pdf) — RPMB 作為 secure storage 的角色、Trusty 上的 lock state 與 rollback index 儲存

---

*本文所有技術敘述均來自上列公開資料或由其推導；標示〔推論〕者為作者依機制推理所得，未必反映任何特定產品的實際實作。*
