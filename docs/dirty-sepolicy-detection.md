# Dirty SEPolicy 偵測：一種讓所有 Root 方案都現形的新向量

## 前言

2026 年初，Android root 社群（r/androidroot）開始討論一種被稱為 **dirty sepolicy detection** 的偵測手法。它的特別之處在於：不管你用 Magisk、KernelSU（及其分支）還是 APatch，只要你 root 了，這個手法幾乎都能驗出來。目前已知至少有五個 App 導入這種偵測，且多半是銀行與金流類應用——Ana Vodafone、Digital Rupee SBI、BRImo、Birbank，以及 Shopee（蝦皮）。

對長年在「root 隱藏」這場貓捉老鼠遊戲裡打滾的人來說，這個向量之所以難纏，是因為它繞過了傳統隱藏術所依賴的所有假設。要理解它，得先從 Android 的 SELinux 講起。

## 一、地基：SELinux 與 binary policy

Android 自 5.0 起全面啟用 SELinux（Security-Enhanced Linux）強制存取控制（MAC）。它和傳統 Linux 權限（UID/GID）不同，不問「你是不是 root」，而是問一個更嚴格的問題：

> 這個 **domain**（主體，例如某個行程的安全脈絡）能不能對那個 **type**（客體，例如某個檔案或 socket）執行這個 **動作**（read、write、execute…）？

一條規則長這樣：

```
allow untrusted_app  app_data_file : file { read write getattr };
```

系統裡數萬條這種規則，會被 `checkpolicy` / `secilc` 編譯成一份**二進位政策檔（binary policy）**。開機早期，init 把這份 policy 載入核心，核心將它保存在記憶體中的 `selinux_state` 結構裡。此後每一次跨 domain 的存取，核心都會查這張表決定放行或拒絕。

這裡有一個對偵測至關重要的性質：

> **原廠 ROM 的 policy 是確定且可預期的。** 同一款機型、同一個系統版本，載入的 policy 內容位元級一致。

換句話說，原廠 policy 有一個「指紋」。任何偏離，都是異常。

## 二、Root 如何「弄髒」policy

Magisk、KernelSU、APatch 這類方案要能運作，前提是讓「本不該存在的權限」存在。它們在開機流程中，把額外的規則注入到核心那份 policy，常見的動作包括：

- 為 su daemon 的 domain 開放廣泛存取權限，讓它能操作系統各處；
- 允許一般 App 與 root 管理服務通訊（例如透過特定 socket 或 binder）；
- 把某些 domain 設為 **permissive**（只記錄、不阻擋），以避免相容性問題；
- 使用者安裝的模組（例如 Magisk 的 `sepolicy.rule`）再各自追加自訂規則。

這些操作全都發生在**核心中那份正在運行的 policy** 上。於是產生了一個無法否認的事實：

> 核心裡實際生效的 policy ≠ 原廠 policy。

這份被加料、被污染的狀態，就是所謂的 **dirty sepolicy**。注意這不是「檔案系統上多了一個檔案」那種表層痕跡，而是核心安全子系統的內部狀態被改動了。

## 三、偵測原理：直接讀核心的 policy

核心透過 selinuxfs 把當前 policy 暴露在一個節點上：

```
/sys/fs/selinux/policy
```

這個節點沒有嚴格的存取限制——**任何 App 都能讀它**，而且讀到的正是**當下記憶體裡那份完整、生效中的 binary policy**。這就給了 App 一個直接檢查核心狀態的窗口。

導入 dirty sepolicy 偵測的 App，其原生 C/C++ 安全 SDK 大致做這幾件事：

1. `open("/sys/fs/selinux/policy", O_RDONLY)`，把整份 policy 讀進記憶體；
2. 依照 SELinux binary policy 的格式（版本標頭、symbol table、AV rules…）自行解析；
3. 拿解析結果去比對「原廠應有的模樣」，尋找污染痕跡：
   - 出現名稱可疑的自訂 type 或 domain（例如帶有 `magisk`、`su`、`ksu` 字樣）；
   - 存在任何 **permissive** 的 domain；
   - `untrusted_app` 這類本該受限的 domain 被授予了異常權限；
   - 規則總數、結構或雜湊值和該機型原廠對不上。

只要命中任一條件，App 即判定裝置已被 root，隨後採取行動——擋登入、擋結帳、直接閃退。以 Shopee 為例，社群回報它不封鎖 App 啟動，而是精準地擋住「進入結帳頁」這一步，且與付款方式無關。

### 為什麼這招特別致命

傳統的 root 隱藏（如 Magisk Hide 的思路、後續的 Shamiko、HMA 改套件名等）本質上是在**騙表層**：藏掉 root 相關的檔案路徑、隱藏 su 二進位、改掉可疑的 package 名稱、過濾 `/proc/mounts` 裡的掛載痕跡。這些之所以有效，是因為它們偽造的是「App 能觀察到的周邊資訊」。

但 dirty sepolicy 不一樣。**Root 要能運作，就必須真的修改核心裡的 policy——這是功能性的、不可迴避的。** 你沒辦法「一邊讓 root 生效、一邊讓 policy 保持原廠乾淨」，因為那份被改動的 policy 正是 root 賴以運作的東西。改了就是改了，它就明明白白躺在核心記憶體裡，透過 `/sys/fs/selinux/policy` 對全世界開放。

這也解釋了為什麼它「打擊面全覆蓋」：Magisk、KernelSU 全系分支、APatch，儘管實作路徑各異，最終都得注入 sepolicy 規則，因此都會在這份 policy 上留下痕跡。

## 四、破解原理：在核心讀取路徑上 hook

既然無法讓 policy 真的變乾淨（那 root 就廢了），反制的思路就轉為：**攔截 App 讀取 policy 的那一瞬間，餵給它一份假的乾淨版本。**

當 App 讀取 `/sys/fs/selinux/policy` 時，這個請求在核心裡最終會走到 `security_read_policy`（以及相關的 `selinux_state` 存取路徑）。KernelSU 的「Hide SELinux modifications」設定、APatch 的 `selinux_hook` KPM，就把 hook 埋在這個位置：

```
        App 讀取 /sys/fs/selinux/policy
                    │
                    ▼
        security_read_policy   ◄──── hook 攔截點
                    │
        ┌───────────┴────────────┐
        │  呼叫者是非特權 App UID？ │
        └───────────┬────────────┘
            是 │                │ 否（系統自身 / 特權脈絡）
               ▼                ▼
   回傳一份「原廠、未修改」    回傳真實（髒的）policy，
   的 policy 副本            root 功能照常運作
```

效果等於對 App 演一場戲：它讀到的是原廠模樣，而核心裡實際生效的仍是加料版。因為 hook 點位於核心層——比任何 App 都更底層——App 沒有辦法繞過它去讀到真實狀態。這也是為什麼這兩個機制「有效得如此徹底」：它們不是藏檔案，而是在資訊的源頭直接偷天換日。

各方案目前的對應做法：

- **KernelSU 及其分支：** 更新到最新版，於設定中啟用「Hide SELinux modifications」。
- **APatch：** 使用 `selinux_hook` KPM。
- **Magisk：** 因 Magisk 本身不在核心層做這種 hook，社群提出的路徑是先透過 Kpatch-next 模組，搭配 WebUI-X 安裝 kpatch，再套用來自 APatch 的 `selinux_hook` KPM。此法目前未經充分測試，相容性因裝置而異。

## 五、如何自行驗證某個 App 是否使用此向量

若你想確認手上某個 App 是不是靠 dirty sepolicy 來偵測，最直接的方式是觀察它的系統呼叫。對目標行程執行 `strace`（或用 frida 掛鉤 libc），留意在它崩潰或功能被封鎖之前，是否出現針對 policy 節點的開檔：

```
openat(AT_FDCWD, "/sys/fs/selinux/policy", O_RDONLY|...) = 3
read(3, ...)
```

若在功能被擋的前一刻看到這組呼叫，基本可以確定它正在讀取並解析 policy 做污染判斷。反過來，若你的 SELinux 隱藏機制生效，App 依然會執行同樣的 `openat`——差別在於它 `read` 回去的內容已被 hook 換成乾淨版。

## 六、這場攻防的走向

Dirty sepolicy detection 把 root 隱藏的戰場，從「檔案系統與使用者空間的偽裝」推進到了「核心安全狀態的真偽」。它的優勢在於利用了一個 root 無法迴避的副作用；而防禦方的優勢，則在於核心層 hook 永遠比 App 更底層。

可以預期，接下來偵測方可能不只讀 `/sys/fs/selinux/policy`，而會轉向交叉驗證：比對 policy 雜湊與已知原廠指紋資料庫、檢查 `selinuxfs` 其他節點的一致性、或觀察讀取延遲等旁路訊號來反偵測 hook 的存在。而隱藏方也會相應地讓假 policy 更逼真、hook 更難被旁路察覺。這是一場會持續下去的軍備競賽——只是這一回合，戰線推到了核心的 SELinux 子系統。

---

### 名詞速查

| 名詞 | 說明 |
|---|---|
| **SELinux** | Android 的強制存取控制機制，以 domain/type 規則決定存取權限 |
| **binary policy** | 編譯後載入核心的二進位規則檔，開機時進入 `selinux_state` |
| **dirty sepolicy** | 被 root 方案注入額外規則、偏離原廠的 policy 狀態 |
| **permissive domain** | 只記錄不阻擋的 domain，常是污染痕跡之一 |
| **`/sys/fs/selinux/policy`** | selinuxfs 節點，任何 App 可讀取當前生效的 policy |
| **`security_read_policy`** | 核心中回應 policy 讀取請求的函式，是 hook 的攔截點 |
| **selinux_hook / Hide SELinux modifications** | 在核心讀取路徑上餵回乾淨 policy 副本的隱藏機制 |

*本文技術脈絡整理自 r/androidroot 社群討論串「Apps that use Dirty SEPolicy detection」（作者 sidex15，SUSFS4KSU 模組開發者）及留言區的技術補充。*
