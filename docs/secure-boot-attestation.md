# Secure Boot 與 Attestation：從信任的起點談起

> 給有技術背景、但還沒真正碰過安全開機與遠端證明的工程師

---

## 一、先說結論：這是兩件不同的事

很多人把 Secure Boot 和 Attestation 混為一談，因為它們常常一起出現、都跟「信任」有關、都需要金鑰和簽章。但它們解決的是兩個方向相反的問題：

| | Secure Boot | Attestation |
|---|---|---|
| 核心問題 | 我要不要執行這段程式碼？ | 我該不該相信這台機器？ |
| 誰做決定 | 裝置自己 | 遠端的另一方 |
| 決定的時機 | 每一層載入的當下 | 事後，隨時 |
| 失敗的後果 | 開不起來、進 recovery | 開得起來，但拿不到憑證／被拒絕存取 |
| 資料流向 | 不對外 | 對外輸出一份簽名報告 |

一句話版本：

- **Secure Boot 是門禁**——不符合規定的東西進不來。
- **Attestation 是履歷**——把發生過的事誠實地寫下來、簽名，交給別人審查。

兩者不互相取代。實務上，一個設計良好的系統會**先用 Secure Boot 擋掉明顯的壞東西，再用 Attestation 把「實際上載入了什麼」證明給外界看**。中間還有一個常被忽略、卻是把兩者串起來的關鍵環節：**Measured Boot**。這篇文章會依序把三者講清楚，然後看看 PC、手機、IoT、雲端機密運算各自怎麼實作。

---

## 二、為什麼需要它們：信任要從哪裡開始？

先想一個看似無聊的問題：**你的作業系統怎麼知道自己沒被改過？**

答案是：它不知道。一個被感染的 kernel 完全可以回報「我很乾淨」。防毒軟體跑在 OS 上，如果 OS 本身已經被控制，防毒軟體看到的世界就是攻擊者想讓它看到的世界。

這類攻擊有個名字叫 **bootkit / rootkit**：攻擊者不去攻擊應用程式，而是往下鑽，搶在 OS 起來之前就取得控制權。位置越低，權限越高，也越難被偵測。經典的例子包括改寫 MBR/UEFI bootloader、把惡意模組塞進 initramfs、或是直接刷一份被改過的韌體。

所以我們需要一個**由下往上**的驗證機制。但「由下往上」立刻碰到雞生蛋的問題：最底層的那段程式碼，誰來驗證它？

答案是：**沒有人**。你必須有一段被無條件信任的東西，這就是 **Root of Trust（RoT，信任根）**。

RoT 的可信度不來自軟體驗證，而來自**物理特性**：

- 它燒在 mask ROM 裡，出廠後不可寫（例如 SoC 的 BootROM）
- 或它的驗證用公鑰雜湊燒在 **eFuse / OTP** 裡，一次性寫入、不可逆
- 或它跑在一顆獨立的安全晶片內（TPM、Secure Element、Secure Enclave）

RoT 的大小決定了你的 **TCB（Trusted Computing Base，可信計算基底）**。工程上的原則很簡單：**TCB 越小越好**，因為 RoT 出問題就無藥可救——它燒死在硬體裡，沒辦法用 OTA 修。歷史上真的發生過：某些 SoC 的 BootROM 被找到驗證邏輯漏洞，結果是整個世代的晶片永久失守（例如 Nintendo Switch 早期型號的 Tegra X1 USB recovery 漏洞，以及 Apple A5–A11 的 checkm8）。

---

## 三、Secure Boot：逐層驗證的信任鏈

### 3.1 基本模型

Secure Boot 的做法是把信任「接力」下去。每一層在把控制權交給下一層之前，先驗證下一層：

```
[RoT: BootROM / 硬體]
        │  用燒在 fuse 裡的公鑰雜湊驗證 ↓
        ▼
[第一階段 bootloader]
        │  用內含的公鑰驗證 ↓
        ▼
[第二階段 bootloader / UEFI]
        │  驗證 ↓
        ▼
[Kernel + initramfs]
        │  驗證 ↓
        ▼
[驅動模組 / rootfs / 應用程式]
```

驗證的內容通常是**數位簽章**：開發者用私鑰對映像檔簽名，裝置用對應的公鑰驗證。演算法一般是 RSA-2048/3072 或 ECDSA P-256，搭配 SHA-256。

這條鏈有兩個容易被忽略的性質：

**第一，鏈是脆的。** 任何一環驗證失敗或被跳過，後面全部失去意義。所以「有 Secure Boot」不等於安全——要看鏈有沒有斷。常見的斷點是：驗證了 kernel 卻沒驗證 initramfs、驗證了 initramfs 卻沒驗證 rootfs、或是留了一個開發用的 debug 開關可以繞過。

**第二，鏈只保護開機那一瞬間。** Secure Boot 是 load-time 驗證，不是 runtime 保護。一旦 kernel 載入完成、驗證通過，之後記憶體裡發生什麼事它完全不管。runtime 的完整性要靠別的機制（dm-verity、IMA、W^X、CFI、hypervisor-based protection 等）。

### 3.2 防回滾（Anti-Rollback）

只驗證簽章還不夠。假設你發了一個修補漏洞的新版韌體，攻擊者可以把裝置刷回**舊版本**——那個舊版本簽章完全合法，只是有已知漏洞。

解法是**版本計數器**：韌體映像檔裡帶一個單調遞增的版本號，裝置在 eFuse 或 TPM 的 monotonic counter 裡記錄「我看過的最高版本」。低於這個數字的映像檔一律拒絕。

代價是**不可逆**：一旦 anti-rollback 計數器往上跳，就永遠回不去。所以量產流程中通常會把「升 counter」和「發布新版」拆開，先讓新版跑一段時間確認穩定，再推一個 bump 版本。

### 3.3 UEFI Secure Boot（PC 平台）

PC 上的 Secure Boot 由 UEFI 規範定義，靠一組階層式的金鑰資料庫運作：

- **PK（Platform Key）**：平台擁有者的最高權限金鑰，通常是 OEM。控制誰可以改 KEK。
- **KEK（Key Exchange Key）**：控制誰可以改 db 和 dbx（PK 也有這個權限）。通常包含 OEM 和 Microsoft 的金鑰。
- **db（Signature Database）**：允許清單。裡面是可接受的簽章憑證或映像檔雜湊。
- **dbx（Forbidden Signature Database）**：撤銷清單。已知有漏洞的 bootloader 雜湊會被加進來。

開機時 UEFI 韌體檢查每個 EFI 執行檔的簽章：出現在 dbx 就拒絕，能被 db 裡的憑證驗證就放行。

`dbx` 值得特別注意，因為**它會滿**。UEFI NVRAM 是一塊固定的小分區，而 authenticated variable 每次更新都得整份寫入；隨著被撤銷的 bootloader 越來越多（BootHole、BlackLotus 這類漏洞每爆一次就要加一批雜湊），有些機器的 dbx 已經逼近上限，寫不進新版。

因此業界後來把撤銷往**版本化**的方向移：**SBAT（Secure Boot Advanced Targeting）** 讓 shim 用一個 `SbatLevel` 變數表達「低於這個版本的元件一律拒絕」，一筆記錄就能取代成百上千個雜湊；Microsoft 也為 Windows Boot Manager 導入了類似的 **Secure Boot SVN**。值得注意的是 SBAT 由 shim 執行而非 UEFI 韌體，所以更新速度比 dbx 快得多——這是個典型的「把機制往上搬一層以換取敏捷度」的設計決策。

**Linux 的 shim 機制**是個實務上的巧妙妥協。Linux 發行版不可能每個都去跟 Microsoft 簽自己的 bootloader，於是有了 shim：一個極小的、由 Microsoft 簽名的墊片程式。它被信任後，再用發行版自己的金鑰去驗證 GRUB 和 kernel。使用者也可以透過 **MOK（Machine Owner Key）** 註冊自己的金鑰，用來簽自編的 kernel 模組（顯卡驅動、VirtualBox 模組常會碰到這個）。

### 3.4 嵌入式 / IoT SoC

嵌入式世界沒有 UEFI，流程更貼近硬體，但概念一致：

1. **BootROM** 從 mask ROM 執行，這是絕對的 RoT，不可修改。
2. BootROM 從 **eFuse/OTP** 讀出 **ROTPK**（Root of Trust Public Key）的雜湊值——注意通常存的是雜湊而非完整公鑰，因為 fuse 空間昂貴。
3. 載入第一階段 bootloader（NXP 叫 HAB、TI 叫 Secure Boot、Xilinx 叫 CSU boot），比對映像檔內附公鑰的雜湊是否等於 fuse 裡的值，再用該公鑰驗證簽章。
4. 之後進入 Arm **TF-A（Trusted Firmware-A）** 定義的階段。要注意這裡**不是單純的線性接力**：BL1 驗證並載入 BL2，BL2 把 BL31、BL32、BL33 **三個映像檔全部驗證並載入**，然後把控制權交給 **BL31**（常駐的 EL3 runtime，處理 PSCI、SMC 等）；BL31 初始化 **BL32**（Secure-EL1 Payload，例如 OP-TEE），再跳進非安全世界的 **BL33**（U-Boot / UEFI），最後才是 Linux。BL31/32/33 是並列的角色而非三個接續的階段。（這套命名是 AArch64 的；AArch32 沒有 BL31，EL3 runtime 的位置由 BL32 擔任。）

嵌入式的獨特痛點在於**量產與金鑰管理**：

- fuse 是一次性的。燒錯一顆板子就報廢，燒錯一批就是災難。
- 產線上要有 HSM 保管簽章私鑰，不能讓私鑰以明文出現在產線電腦上。
- 開發板通常出廠時 Secure Boot 是關的（fuse 未燒），方便開發；量產時才「closed」。這意味著**開發期間你測的是未啟用狀態，真正啟用後的行為必須另外驗證**——很多專案在這裡踩雷。

---

## 四、Measured Boot：不擋，只記錄

現在來看串起兩端的關鍵環節。

Secure Boot 有個結構性的限制：**它是二元的**。要嘛過、要嘛不過。它不告訴你「實際上載入了哪個版本」，只告訴你「載入的東西簽章合法」。但簽章合法的映像檔可能有一百個版本，其中九十九個有已知漏洞。

而且 Secure Boot 的判斷發生在裝置內部，外界看不到。如果你是一台雲端伺服器的租戶，你怎麼知道那台機器真的開了 Secure Boot？

**Measured Boot** 補上這個缺口。它的做法是：**每一層在執行下一層之前，先算出下一層的雜湊值，記錄到一個防篡改的地方，然後照常執行**。注意——**它不阻止任何東西**，只是誠實記帳。

### 4.1 PCR 與 extend 操作

記帳的地方通常是 TPM 的 **PCR（Platform Configuration Register）**。PC 平台上有 24 個 PCR（這是 TCG PC Client Platform TPM Profile 的要求；TPM 2.0 library spec 本身把數量交給實作決定），每個是一個雜湊長度的暫存器（SHA-256 bank 就是 32 bytes）。

PCR 不能直接寫入，只能做一種操作叫 **extend**：

```
PCR_new = Hash( PCR_old || measurement )
```

這個設計非常精巧，值得停下來想一下它為什麼安全：

- **不可逆**：因為是雜湊，你無法從 PCR 值反推歷程。
- **不可偽造**：要讓 PCR 停在某個特定值，你必須知道整個 extend 序列。攻擊者無法「跳過」自己的那筆記錄——他若要讓最終值看起來乾淨，得先算出一個能碰撞出目標值的輸入。
- **有序**：`A 然後 B` 和 `B 然後 A` 會得到不同的 PCR 值。順序也被記錄下來了。
- **只增不減**：對開機量測用的 PCR 0–15 而言，唯一能清回 0 的方式是重開機。惡意軟體無法「洗掉」自己的痕跡。（例外：PCR 23、部分實作的 PCR 16 屬於可重設的除錯／應用用途，可用 `TPM2_PCR_Reset` 在執行期歸零；PCR 17–22 保留給 DRTM，初值是 `0xFF...FF`，由特殊指令重設。用來記錄信任鏈的一律是 0–15。）

慣例上的 PCR 分配（TCG PC Client 規範）：

| PCR | 內容 |
|---|---|
| 0 | UEFI 韌體本體（CRTM、BIOS code） |
| 1 | 韌體設定、平台設定資料 |
| 2–3 | 選配 ROM（顯卡、網卡等擴充卡韌體）程式碼與設定 |
| 4 | Boot Manager、開機載入器 |
| 5 | GPT / 分割表 |
| 6 | 平台製造商自訂用途 |
| 7 | **Secure Boot 狀態與金鑰資料庫（PK/KEK/db/dbx）** |
| 8–15 | 作業系統可自由使用（GRUB、kernel、IMA 等） |

PCR 7 特別重要——它記錄了 Secure Boot 的**設定**。這是「用 Attestation 證明 Secure Boot 有開」的具體實現方式。

### 4.2 Event Log

光有 PCR 值是沒用的——它只是一串 32 bytes 的雜湊，看不出任何意義。所以韌體同時會維護一份 **TCG Event Log**：純文字（其實是結構化二進位）的流水帳，記錄每一次 extend 的細節：extend 了哪個 PCR、雜湊值多少、對應的是哪個檔案或事件。

Event Log 本身**不受保護**，可以被任意竄改。但這不要緊，因為驗證方會拿 Event Log 從 0 開始重放一次 extend 運算，看最終結果是否等於 TPM 回報的 PCR 值。對不上就代表 log 被動過。這是一個很優雅的設計：**用受保護的小資料（PCR）來驗證不受保護的大資料（log）的完整性**。

Linux 上你可以直接看：

```bash
# PCR 現值
cat /sys/class/tpm/tpm0/pcr-sha256/*
# 或
tpm2_pcrread sha256

# UEFI event log（tpm2_eventlog 只吃檔案路徑，不吃 stdin）
sudo tpm2_eventlog /sys/kernel/security/tpm0/binary_bios_measurements
```

### 4.3 Sealing：本地端的信任應用

在談遠端之前，先提一個純本地的應用：**Sealing（封印）**。

你可以要求 TPM「把這個祕密加密起來，而且只有在 PCR 等於特定值時才允許解密」。這就是 **Windows BitLocker** 的運作方式。它的預設 validation profile 會隨 Secure Boot 狀態切換：

- **Secure Boot 已啟用**（現代機器的預設）→ 綁 **PCR 7 + PCR 11**
- **Secure Boot 未啟用** → 綁 **PCR 0, 2, 4, 11**

（PCR 11 是 BitLocker 自己的存取控制欄位，兩種 profile 都一定包含。）如果有人把硬碟拆到另一台機器、改了 bootloader、或關掉 Secure Boot，PCR 值就對不上，TPM 直接拒絕吐出金鑰，你會看到要求輸入 recovery key 的畫面。

Linux 上對應的是 `systemd-cryptenroll --tpm2-device=auto --tpm2-pcrs=7`，或 Clevis + Tang 的組合。

Sealing 也解釋了一個常見的困擾：**為什麼更新 BIOS 之後 BitLocker 要你輸入 recovery key？** 在預設的 PCR 7+11 profile 下，通常是因為韌體更新順帶改動了 Secure Boot 變數或憑證（PCR 7 變了），或更新過程暫時關閉了 Secure Boot / TPM。這不是 bug，是機制正常運作——順帶一提，這也是為什麼**韌體更新流程應該主動 suspend 保護再恢復**，而不是讓使用者去翻 recovery key。

---

## 五、Attestation：把證據簽名交給外界

Sealing 是「我自己相信自己」。**Attestation 則是「讓別人相信我」**。

### 5.1 Quote 的組成

TPM 提供一個叫 **Quote** 的操作。流程是：

1. **驗證方（Verifier）產生一個隨機的 nonce**，送給被驗證的裝置。
2. 裝置呼叫 `TPM2_Quote`，把 nonce 和要證明的 PCR 索引丟進去。
3. TPM 在內部組出一份結構：`{ PCR 摘要, nonce, TPM 韌體版本, 其他中繼資料 }`，**用一把 TPM 內部的私鑰簽名**。
4. 裝置把 Quote + Event Log 一起送回驗證方。

**nonce 是防重放的關鍵。** 沒有 nonce 的話，攻擊者可以在機器乾淨時錄一份 Quote，之後即使機器被入侵，也拿舊的錄影帶重播。加上 nonce 之後，每次挑戰的答案都不同，而且簽名涵蓋了 nonce，無法事後拼接。

### 5.2 金鑰身分：EK、AK、與隱私問題

簽名用的私鑰從哪來？這牽涉到一個微妙的設計問題。

- **EK（Endorsement Key）**：每顆 TPM 獨有的身分金鑰。TPM 2.0 的作法不是「燒入金鑰對」，而是燒入一顆唯一的 **EPS（Endorsement Primary Seed）**，EK 再由 EPS 加上一個公開的 template **確定性地衍生**出來——所以 EK 隨時可以重建，但換掉 EPS（`TPM2_ChangeEPS`）就永遠回不去。出廠時真正寫進 NV 的是製造商簽發的 **EK 憑證**，它證明「這是一顆真正的 Infineon/Nuvoton TPM，不是軟體模擬的」。
- 問題來了：EK 是**全球唯一且永久**的。如果每次 attestation 都用 EK 簽名，等於在每個服務面前掛著同一個硬體序號——這是嚴重的隱私問題（跨網站追蹤）。
- 解法：**AK（Attestation Key）**。裝置產生一把或多把 AK，透過一個叫 **credential activation** 的協定，讓某個 CA 確認「這把 AK 確實住在一顆有合法 EK 的 TPM 裡」，然後簽發 AK 憑證。實際 attestation 用 AK 簽名，EK 只在註冊階段出現一次。
- 更進一步的方案是 **DAA（Direct Anonymous Attestation）**，用零知識證明達成「我是合法 TPM 群體的一員，但我不告訴你我是哪一顆」。Intel SGX 早期的 EPID 就是這一類。

隱私和可追溯性在這裡是直接衝突的：企業 IT 希望能精確識別每一台裝置，個人使用者希望不要被跨服務追蹤。不同平台在這條線上的取捨不同。

### 5.3 Verifier 怎麼判斷？

拿到 Quote 之後，驗證方要做四件事：

1. **驗證簽章鏈**：AK 憑證 → CA → 製造商根憑證。確認這是真硬體。
2. **檢查 nonce**：是我剛剛發的那個嗎？防重放。
3. **重放 Event Log**：從 log 重算 PCR，跟 Quote 裡的值比對。確認 log 沒被改。
4. **比對參考值（Reference Values）**：這是**最難的一步**。

第 4 步難在哪？因為你必須知道「正確的 PCR 值應該是多少」。而 PCR 0 的值取決於 BIOS 的每一個 byte——同一型號機器，不同 BIOS 版本、不同設定、插了不同的顯卡（PCR 2 會變），值就不一樣。

實務上的做法是**參考值資料庫**，也就是 TCG 講的 **RIM（Reference Integrity Manifest）**：供應商發布每個韌體版本的預期量測值，驗證方拿來比對。這在封閉環境（單一機型的企業車隊、雲端業者自己的機房）可行；在開放的異質環境幾乎不可能窮舉。

這就是為什麼**現實中的 attestation 政策通常不是「PCR 必須完全等於某值」，而是分層的**：
- 嚴格比對關鍵項目（PCR 7 的 Secure Boot 狀態、kernel 的量測值）
- 對容易變動的項目（PCR 2、PCR 5）放寬或忽略
- 或改用**語意化的量測**：不記錄「這個 byte 序列」，而記錄「這個具名元件的版本」

### 5.4 RATS 架構：把角色講清楚

IETF 的 **RFC 9334（Remote ATtestation procedureS Architecture）** 為這件事定義了一套通用詞彙，讀規格書時很有用：

- **Attester**：被驗證的實體，產生 **Evidence**（例如 TPM Quote）。
- **Verifier**：檢查 Evidence，產出 **Attestation Result**。
- **Relying Party**：根據 Attestation Result 決定要不要放行的一方（例如 KMS、VPN gateway、網路准入控制）。
- **Endorser**：硬體製造商，提供 **Endorsement**（例如 EK 憑證），讓 Verifier 知道這顆晶片是真的。
- **Reference Value Provider**：提供預期量測值的一方（通常是軟體供應商）。

關鍵洞察是 **Verifier 和 Relying Party 是分開的**。Verifier 負責密碼學上的「這份證據是真的、內容是這些」，Relying Party 負責業務上的「這樣的狀態我接不接受」。兩者可以由不同組織擔任，這讓 attestation 可以做成服務（例如 Microsoft Azure Attestation、Intel Trust Authority）。

---

## 六、各平台實作對照

### 6.1 PC / 伺服器：UEFI + TPM 2.0

- **Secure Boot**：UEFI db/dbx，前面已述。
- **Measured Boot**：TPM PCR 0–7 由韌體 extend，OS 之後用 PCR 8+。
- **Attestation**：Windows 有 Device Health Attestation，可與 Intune / 條件式存取整合；Linux 生態有 Keylime（開源的持續遠端證明框架）。
- **值得注意的差異**：**dTPM vs fTPM**。dTPM 是獨立晶片，透過 LPC/SPI 匯流排連到 CPU——這條匯流排在某些設計上可以被物理探測（歷史上有人用邏輯分析儀直接抓到 BitLocker 金鑰）。fTPM 則跑在 CPU 的安全模式內（Intel PTT、AMD fTPM），沒有匯流排可探測，但和主 CPU 共用晶片，就繼承了 CPU 側通道漏洞的風險。沒有絕對優劣，看威脅模型。

### 6.2 Android：Verified Boot + Key Attestation

Android 的 **AVB（Android Verified Boot）** 有個很有教學價值的設計——**boot state 顏色**：

| 狀態 | 意義 |
|---|---|
| 🟢 Green | bootloader 已鎖，用 OEM 金鑰驗證通過。完全信任。 |
| 🟡 Yellow | bootloader 已鎖，但用**使用者自行註冊的金鑰**驗證通過。開機時顯示警告與金鑰指紋。 |
| 🟠 Orange | bootloader 已解鎖，不驗證。顯示警告。 |
| 🔴 Red | 驗證**失敗**。分兩種：dm-verity 偵測到毀損（`eio`）時顯示警告，使用者按電源鍵可繼續開機、30 秒未確認則關機；找不到有效 OS 時則無法開機。 |

Yellow 這個狀態值得玩味：它承認了「使用者有權在自己的裝置上跑自己的軟體」，但同時把這個事實**如實記錄並對外揭露**。這是 Secure Boot 從「廠商鎖定」轉向「可驗證的自主權」的一個重要設計。

rootfs 的完整性則交給 **dm-verity**：整個唯讀分割區被組織成一棵 Merkle tree，root hash 被簽名。每讀取一個 block 就即時驗證其雜湊路徑——這已經超越 load-time，是**持續的 runtime 驗證**。

**Android Key Attestation** 則是應用層可以直接用的 attestation：你在 Keystore 產生一把金鑰時可以要求 attestation，系統會回傳一條憑證鏈，根部是 Google 的憑證，中間的擴充欄位裡帶著：verified boot state（上面那個顏色）、boot 的 root hash、OS 版本與 patch level、金鑰是否真的在硬體裡、是否需要使用者驗證才能使用等等。

> ⚠️ 實作提醒：Google 已輪替 attestation 根憑證。驗證端若沒有在 **2026-04-10** 前加入新的根憑證，會開始拒絕所有 RKP-enabled 裝置（也就是絕大多數現代 Android）。根憑證發布在 `https://android.googleapis.com/attestation/root`。

銀行 App 檢查裝置有沒有 root，底層通常就是靠這個（以及 Play Integrity API），而不是靠掃描 `/system/xbin/su` 之類的土法煉鋼。

### 6.3 iOS：整合式的信任鏈

Apple 的做法是垂直整合：Boot ROM（燒在晶片裡）→ iBoot → kernel，每一層用 **Image4（img4）** 格式驗證，憑證鏈以 RSA-4096 / SHA-384 上溯到 Apple Root CA。（A9 及更早的晶片中間還有一階 **LLB**；A10 之後 Boot ROM 直接載入 iBoot。）加上 **Secure Enclave**——一顆獨立的協處理器，有自己的 boot ROM、記憶體加密與專屬 AES 引擎——處理生物辨識資料與金鑰。

有兩個 Apple 特有的機制值得一提：

- **個人化簽章（personalized signing）**：韌體映像檔的簽章綁定裝置的 **ECID**（每台唯一）與一個伺服器給的 nonce。這代表你不能把 A 手機的合法韌體拿去裝 B 手機，也不能離線降級——安裝時必須向 Apple 伺服器要一張針對這台裝置、這次安裝的簽章（「TSS/APTicket」）。這是防回滾做到極致的形式。
- **App Attest / DeviceCheck**：給 App 開發者的 attestation API，用來證明「這個請求來自我發布的、未被竄改的 App，跑在真的 Apple 裝置上」。

### 6.4 IoT / 嵌入式：PSA 與 DICE

小型 MCU 沒有 TPM 的空間與功耗預算，於是有兩套輕量方案：

**Arm PSA（Platform Security Architecture）** 定義了 **PSA Attestation Token**（已於 2025 年獨立成為 **RFC 9783**）：以 **EAT（Entity Attestation Token，RFC 9711）** 格式編碼，用 CBOR 序列化、COSE 簽名——比 X.509 + JSON 省下大量的碼和頻寬。Token 裡帶的是實作 ID、生命週期狀態、開機量測、以及挑戰值。參考實作是 **TF-M（Trusted Firmware-M）**。

**DICE（Device Identifier Composition Engine）** 則是個很巧妙的想法，它甚至不需要專屬的安全硬體。核心是一條**逐層金鑰衍生鏈**：

```
UDS（Unique Device Secret，燒在 fuse，只有第一層看得到）
   │
   ▼  CDI_1 = KDF( UDS, Hash(Layer1_code) )
[Layer 1] ── 用完 UDS 後把它從記憶體與存取權限中鎖掉
   │
   ▼  CDI_2 = KDF( CDI_1, Hash(Layer2_code) )
[Layer 2]
   │
   ▼  ...
```

美妙之處在於：**金鑰本身就是量測值的函數**。如果任何一層的程式碼被改了一個 bit，往下衍生出的所有金鑰全部不同——裝置會「自然地」失去解密舊資料、或用預期身分簽名的能力。你不需要一個「檢查然後拒絕」的邏輯，**竄改直接導致密碼學上的身分改變**。而且 UDS 只需被最底層存取一次就可以永久鎖住，大幅縮小 TCB。

DICE 現在也被用在資料中心——**Caliptra**（Open Compute Project 底下，由 AMD、Google、Microsoft、NVIDIA 共同發起的開源矽智財 RoT）就以 DICE 為基礎。

### 6.5 雲端機密運算：attestation 的殺手級應用

這是 attestation 最能展現價值的場景，因為它解決了一個過去無解的問題：**你把資料上傳到雲端，怎麼知道雲端業者（或被入侵的 hypervisor、或有權限的管理員）沒在偷看？**

機密運算的答案是：把工作負載跑在硬體隔離的環境裡，**連 hypervisor 和 host OS 都無法讀取其記憶體**（記憶體被 CPU 用專屬金鑰即時加解密）。而 attestation 就是你確認「我的資料真的進到了那個受保護的盒子裡」的唯一手段。

典型流程是這樣的——注意它把 attestation 和**金鑰釋出**綁在一起，這是關鍵設計：

1. 你在雲端啟動一個機密 VM 或 enclave，裡面跑你的程式碼。
2. 環境向 CPU 索取一份 attestation report，內容包含**啟動時載入的程式碼與資料的量測值**，由 CPU 內建的、無法匯出的金鑰簽名。
3. 你（或你信任的 KMS）驗證這份報告：簽章鏈是否連到 Intel/AMD 的根憑證？量測值是否等於我編譯出來的預期值？TCB 版本有沒有已知漏洞？
4. **只有全部通過，KMS 才把資料解密金鑰送進那個環境。**

如果雲端業者換了程式碼，量測值就不對，金鑰永遠不會被釋出，資料就永遠是密文。**信任從「相信雲端業者的合約與名譽」轉移到「相信 CPU 廠商的硬體與密碼學」**——這不是消除信任，而是把信任搬到一個可驗證的地方。

三大實作的差異：

| | Intel SGX | AMD SEV-SNP | Intel TDX |
|---|---|---|---|
| 保護單位 | 應用程式內的 enclave | 整台 VM | 整台 VM（TD） |
| 量測 | MRENCLAVE（程式碼）、MRSIGNER（簽署者） | attestation report 的 `MEASUREMENT` 欄位 | MRTD + RTMR[0–3]（可執行期擴充） |
| 報告簽章來源 | Quoting Enclave，用 PCK 憑證鏈（DCAP） | VCEK／VLEK，由 AMD 的 KDS 簽發 | TD Quote，同樣走 Quoting Enclave |
| 程式改寫成本 | 高（要切分 enclave、處理 ECALL/OCALL） | 低（現有 VM 幾乎直接搬） | 低 |
| TCB 大小 | 小（只有 enclave 內的程式碼） | 大（整個 guest OS 都在裡面） | 大 |

這裡有個典型的工程權衡：SGX 的 TCB 最小、攻擊面最窄，但你得重寫應用程式；SEV-SNP/TDX 幾乎不用改程式，代價是整個 guest OS 都進了 TCB，kernel 的漏洞就是你的漏洞。

**RTMR** 值得特別提一下：TDX 除了啟動時的 MRTD，還提供 4 個 Runtime Measurement Register，語意上等同於 TPM 的 PCR，可以在 TD 執行期間繼續 extend。這讓 attestation 可以涵蓋「啟動後又載入了什麼」，而不只是啟動那一刻的快照。

---

## 七、常見誤解與實務陷阱

**「開了 Secure Boot 就安全了」**
Secure Boot 只驗證 load time。一個帶有 0-day 的、簽章完全合法的 kernel 照樣會被載入。而且鏈只要有一環沒接上（最常見：驗證了 kernel 卻沒驗證 initramfs 或 rootfs），保護就等於零。

**「Attestation 能證明機器沒被入侵」**
不能。它證明的是「開機時載入了這些東西」。開機後被 exploit 打進去的 runtime 攻擊，在 PCR 上完全看不到。要涵蓋執行期，需要 IMA、RTMR、或 runtime attestation 這類額外機制。

**「PCR 值對就代表沒問題」**
PCR 值對代表「跟參考值一致」。如果參考值本身就是一個有漏洞的版本，一致只是證明你確實在跑那個有漏洞的版本。**Attestation 回答的是「是什麼」，不是「安不安全」**——後者是 Relying Party 的政策問題。

**忘記 nonce / 挑戰值**
沒有新鮮度保證的 attestation 可以被重放。這是自幹 attestation 協定時最常見的致命錯誤。

**把 Secure Boot 當成 DRM，或反過來**
技術機制是中性的，但**誰持有金鑰**決定了它的政治意涵。使用者可以自行註冊金鑰（UEFI 的 MOK、Android 的 yellow state），和硬體被永久鎖在單一廠商的簽章上，是兩種完全不同的產品決策。討論時把「機制」和「金鑰所有權」分開講，會清楚很多。

**開發階段沒測 closed 狀態**
如同前面提到的，開發板通常 fuse 未燒。等到量產前才第一次啟用 Secure Boot，往往會發現一堆問題：某個模組沒簽、debug console 被關掉導致無法診斷、OTA 流程沒對應 anti-rollback。**盡早準備一批「已 closed」的樣品持續測試。**

**測試環境的私鑰外流**
開發用的簽章金鑰如果和量產金鑰是同一把，或測試金鑰意外被信任在量產裝置上，整套機制瞬間歸零。這類事故在業界並不罕見（例如某些廠商的 platform key 被外洩到公開的韌體映像檔中）。金鑰分離與 HSM 保管不是流程潔癖，是必要條件。

---

## 八、總結

把整條路徑串起來，一台裝置從上電到被外界信任，經過的是這樣的流程：

```
上電
 │
 ├─ [Secure Boot]  每一層驗證下一層的簽章 ──失敗→ 停止開機
 │
 ├─ [Measured Boot] 每一層把下一層的雜湊 extend 進 PCR/RTMR
 │                  （不擋，只記帳；同時寫 Event Log）
 │
 ├─ [OS 啟動]      dm-verity / IMA 持續驗證執行期完整性
 │
 └─ [Attestation]  外界送 nonce 挑戰
                    → 硬體用 AK 簽出 Quote（PCR + nonce）
                    → Verifier 驗簽章鏈、重放 log、比對參考值
                    → Relying Party 決定：放行？釋出金鑰？拒絕存取？
```

三個機制、三種角色：

- **Secure Boot** 讓裝置能拒絕明顯錯誤的程式碼——**預防**。
- **Measured Boot** 讓裝置無法隱瞞自己執行了什麼——**記錄**。
- **Attestation** 讓外界能獨立驗證這些記錄——**證明**。

最後一個觀念上的收束：這一整套東西的價值，不在於「達成絕對安全」——沒有這種東西。它的價值在於**把信任從「相信一個聲明」轉換成「驗證一個證據」**。過去你只能相信對方說「我的系統很乾淨」；現在你可以要求一份由硬體簽名、無法偽造、涵蓋新鮮度的證據，然後自己判斷。

這個轉換，才是 attestation 真正在做的事。

---

## 延伸閱讀

- **RFC 9334** — Remote ATtestation procedureS (RATS) Architecture：角色與詞彙的權威定義，讀其他規格前先讀這份。
- **RFC 9711** — Entity Attestation Token (EAT)：輕量 attestation token 的格式。
- **RFC 9783** — Arm PSA Attestation Token。
- **TCG PC Client Platform Firmware Profile**：PCR 分配與 event log 格式的規範來源。
- **TCG TPM 2.0 Library Specification**：Part 1（架構）比 Part 3（命令）好讀得多，先看 Part 1。
- **UEFI Specification, Chapter 32** — Secure Boot 與金鑰資料庫。
- **Android Verified Boot 文件**（source.android.com/security/verifiedboot）：boot state 與 AVB 的設計說明寫得很清楚。
- **Arm Trusted Firmware-A 文件**：嵌入式信任鏈 BL1–BL33 的實際實作。
- **Open Compute Project — Caliptra**：開源的資料中心 RoT，DICE 的實務範例。
- **Confidential Computing Consortium** 的白皮書：SGX / SEV-SNP / TDX 的中立比較。

實作練習建議：在自己的 Linux 機器上跑 `tpm2_pcrread` 和 `tpm2_eventlog`，改一個 BIOS 設定再看一次，觀察哪些 PCR 變了。這比讀十篇文章都有感覺。
