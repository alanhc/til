---
title: SELinux 是什麼？為什麼 Android 韌體工程師必須懂它
sidebar_label: SELinux
---

# SELinux 是什麼？為什麼 Android 韌體工程師必須懂它

在 Android 平台整合的日常裡，`avc: denied` 大概是最常被丟來丟去的 log 之一——功能壞了、開機卡住、CTS 過不了，最後追下去常常是一條 SELinux denial。這篇文章從基礎概念講起，一路講到 Android 的分層架構與 denial 的 ownership 判斷，最後說明為什麼對 Android 韌體/平台工程師而言，SELinux 不只是安全機制，而是出貨的硬條件。

## 一、SELinux 是什麼

SELinux（Security-Enhanced Linux）是 Linux 核心的**強制存取控制**（MAC, Mandatory Access Control）機制，由 NSA 開發後併入主線 kernel。Android 自 4.3 引入，5.0 起全面 enforcing。

### MAC vs DAC:root 不等於無敵

傳統 Linux 權限（rwx、uid/gid）是 DAC（Discretionary Access Control）：權限跟著 user 走，擁有者可以自己決定誰能存取。這有兩個致命問題：

1. **root 全能**：任何一個以 root 執行的 daemon 被攻破，攻擊者就拿到整台機器。
2. **權限自主決定**：一個有 bug 的程式可以把敏感資料開放給任何人。

SELinux 把這個模型翻過來：權限不再跟著 uid，而是跟著 policy 定義的 domain。**即使 process 是 root，沒有 policy 明確允許的操作一律拒絕。**這就是 least privilege 的強制化。

### Label 與 Type Enforcement

每個 process、檔案、socket 都帶有一個 security context（label），格式為：

```
u:r:untrusted_app:s0
(user : role : type : level)
```

核心機制是 **type enforcement**:policy 規則定義「哪個 type 的 process 可以對哪個 type 的物件做什麼操作」：

```
allow untrusted_app app_data_file:file { read write };
```

### 運作模式

| 模式 | 行為 |
|---|---|
| Enforcing | 違規直接阻擋並記 log(量產必須) |
| Permissive | 只記 log 不阻擋（debug 用） |

userdebug build 可用 `getenforce` / `setenforce` 查看與切換。

## 二、SELinux 的組成元件

### Kernel 端

- **LSM hooks**:kernel 在各安全敏感操作點（open、exec、bind…）埋的掛鉤，SELinux 透過 LSM framework 接入。
- **Security Server**:kernel 內做存取決策的核心。
- **AVC(Access Vector Cache)**：快取決策結果；denial log 開頭的 `avc:` 就是它印的。
- **selinuxfs**（`/sys/fs/selinux`）：與 userspace 溝通的介面。

### Policy 端

- **`.te` 檔**:type enforcement 規則（allow / neverallow / dontaudit 等）。
- **Context 定義檔**:
  - `file_contexts` — 檔案路徑對應的 label
  - `property_contexts` — Android property 的 label
  - `service_contexts` — binder service 的 label
  - `seapp_contexts` — app 該跑在哪個 domain
  - `genfs_contexts` — sysfs / procfs 等虛擬檔案系統的 label
- 編譯後產出二進位 policy（Android 上是 CIL，開機時組合或使用 `precompiled_sepolicy`）。

### Userspace 端

- **libselinux**：查詢/設定 context 的 library。
- **常用工具**:`ls -Z` / `ps -Z`（看 label）、`restorecon`（重設檔案 label）、`chcon`、`audit2allow`（從 denial 產生規則建議——注意，只是建議，不能無腦採用）。
- **init**：開機時載入 policy、幫檔案打 label。

## 三、Android 的 sepolicy 分層架構

Treble 之後，sepolicy 被拆成多層，開機時由 init 將各層 CIL 合併編譯：

| 層 | 位置 | Owner |
|---|---|---|
| Platform | `system/sepolicy` | Google / AOSP，基本不能改 |
| Platform-vendor 介面 | `system/sepolicy/vendor` | Google 定義 |
| Vendor | `device/<soc>/.../sepolicy`、`vendor/...` | SoC vendor |
| ODM / OEM | `odm/sepolicy` | OEM |

關鍵規則：**vendor 層不能違反 platform 的 neverallow**,CTS 會直接抓出來。這個分層不只是安全設計，更是 Treble 架構契約的 enforcement——vendor process 不能亂碰 system 資源，是 framework 能獨立升級（GKI/Treble）的前提之一。

## 四、實戰：讀懂 denial 並找出 owner

一條典型的 denial 長這樣：

```
avc: denied { read } for pid=1234 comm="app"
name="foo" scontext=u:r:untrusted_app:s0
tcontext=u:object_r:vendor_file:s0 tclass=file
```

意思是：**source context(誰)** 對 **target context(什麼東西)** 執行了被 policy 拒絕的 **操作（read）**。

在跨團隊環境裡，denial 的 triage 難點往往不是技術，而是 ownership——每個人都說「不是我」。判斷依據不是「誰的 process」，而是**這條規則該定義在哪一層**:

1. **查 scontext 的 domain 定義在哪一層**:
   ```bash
   grep -r "type untrusted_app" --include="*.te" system/ device/ vendor/
   ```
   domain 宣告在哪層，規則通常就該加在哪層。

2. **查 tcontext 的 label 從哪來**:grep 各層的 `file_contexts` / `property_contexts` / `service_contexts`，找到是誰幫這個物件打的 label——打 label 的那層通常就是 owner。

3. **git blame 拿白紙黑字**：找到定義行後直接 blame,commit author / module owner 一翻兩瞪眼，Gerrit 上還能看到當初的 reviewer。

4. **看 prefix 快速分流**:SoC vendor 自訂 prefix（如 `mtk_*`）歸 SoC 內部團隊；OEM 自訂的通常在 odm 層。

與其問「這是不是你的」，不如直接丟證據：「`type xxx` 定義在 `device/.../sepolicy/xxx.te`,git blame 是你們 team 的 commit,file_contexts 的 label 也是同一個 change 加的。」Ownership 由 code 定義位置決定，不由誰願意認領決定。

另外兩個常見情境：

- **「denial 有出現但功能正常」**：確認該 domain 是否 permissive（log 帶 `permissive=1` 只記錄不阻擋），或是否該加 `dontaudit` 消音。permissive domain 的 denial 可先降優先級，但量產前必須清掉。
- **`audit2allow` 的輸出不能無腦放行**：每一條 allow 都是在攻擊面上開洞。正確流程是先問「這個存取本來就該發生嗎」——該發生就在正確的層加最小規則；不該發生就修 code 走正規介面（binder / HAL），而不是直接開檔案權限。

## 五、為什麼對 Android 韌體工程師特別重要

### 1. 它是漏洞緩解，不是漏洞修補

漏洞永遠修不完。SELinux 的價值是把「被攻破」和「被拿下整台機器」之間拉開距離——exploit chain 的每一步都可能撞上 policy 的牆。歷史上多個 Android 提權漏洞鏈（如 Stagefright 的後續利用）就是被 SELinux 斬斷了後半段：media server 被打穿，但 policy 不允許它碰的東西依然碰不到。

### 2. Android 的威脅模型需要它

手機上跑著數百個互不信任的第三方 app，加上品質參差的 vendor daemon 與 HAL。`untrusted_app` domain 把每個 app 關進沙盒；即使 app 透過 native 漏洞執行任意 code，能觸及的檔案、socket、device node 仍被 policy 限死。

### 3. 它是出貨的硬條件

CTS 直接驗證 sepolicy——neverallow 違反就過不了，GMS 認證就拿不到。對量產產品線而言，SELinux 不是「加分的安全機制」，而是認證 gate 的一部分。sepolicy 錯誤也是整合階段 build break 與 boot loop 的常見來源。

### 4. 它是跨層 debug 的必備素養

韌體/平台工程師的日常橫跨 kernel、HAL、framework。很多「功能莫名壞掉」的問題，最後都是一條被忽略的 avc denial:driver node label 打錯、HAL 少了一條 allow、property 存取被擋。看不懂 denial，就等於 debug 工具箱少了一把關鍵的鑰匙。

### 5. 放錯位置的規則是未來的債

在錯誤的層加規則、或加了過寬的規則，短期看起來「解掉了」，長期則是安全債和 CTS 炸彈——下次 platform 升級、neverallow 收緊，炸的就是當初圖方便的人。精確的 ownership 歸位與最小權限規則，是整合工程師能為產品品質把守的重要一關。

## 小結

SELinux 的本質是把 least privilege 從「建議」變成「強制」：每個 process 被關進 policy 定義的盒子裡，root 也不例外。對 Android 韌體工程師來說，它同時是安全機制、架構契約（Treble 分層）、認證門檻（CTS/GMS），以及日常 triage 中判斷問題歸屬的依據。讀懂 denial、找對 owner、在正確的層加最小的規則——這三件事做好，SELinux 就從絆腳石變成你手上的利器。
