# 多專案 BSP 的 Branch 與 Manifest 管理:SCM 視角

> 系列文章之十六(完)。總覽請見《Chip Vendor 視角的 Android Build System》。

一家 chip vendor 同時活著的組合可能是:5 顆 SoC × 3 個 Android 版本 × 上百個客戶專案 × 每月 security patch。程式碼管理策略錯了,工程師的時間會全部耗在 cherry-pick 與「這個 fix 到底進了哪些分支」的考古上。本文整理 repo/manifest 的管理模式與分支策略。

---

## 一、repo 與 manifest 的基本盤

AOSP 用 `repo` 管理數百個 git repo,一切從 manifest XML 開始:

```xml
<manifest>
  <remote name="aosp" fetch="https://android.googlesource.com/" />
  <remote name="myvendor" fetch="ssh://git.myvendor.com/" />
  <default revision="main" remote="myvendor" sync-j="8" />

  <!-- AOSP 專案:鎖 tag -->
  <project path="frameworks/base" name="platform/frameworks/base"
           remote="aosp" revision="refs/tags/android-15.0.0_r5" />
  <!-- 自家 BSP -->
  <project path="vendor/myvendor/camera" name="bsp/camera" revision="soc_a-a15" />
  <!-- 客戶專案 overlay -->
  <project path="device/odmx/projy" name="cust/odmx/projy" revision="main" />
</manifest>
```

管理上的核心武器:

- **分層 manifest(include)**:`base.xml`(AOSP)+ `soc_a.xml`(SoC 層)+ 客戶專案 manifest include 前兩者。改一處,全家生效。
- **`repo manifest -r`**:把當前所有 repo 的 HEAD 固化成 pinned manifest——**每個 release/每日 build 都要留一份**,這是「可重現 build」的最低要求(對照 OTA 篇的 target_files 歸檔:一個管 source,一個管 binary)。
- **local manifests**:開發者本機疊加,不進正式檔。

---

## 二、分支模型:三層結構

業界常見(名稱各家不同,結構高度趨同):

```
AOSP tag (android-15.0.0_rX)
  └─ ① platform 主線:soc-common-a15
  │     所有 SoC 共用的 AOSP 修改 + 公共 BSP 框架
  └─ ② SoC 線:soc_a-a15 / soc_b-a15
  │     各 SoC 的 driver、HAL、公版 device tree
  └─ ③ 客戶線:soc_a-a15-odmx(或客戶自己拉走維護)
        客戶專案 device tree 與客製
```

**鐵律:修改放在最上層能放的位置。** 一個 fix 若與 SoC 無關,進 ①,所有 SoC 線 merge 下來自動獲得;放進 ③ 的公共 fix 就是未來的考古題。

**流動方向單一化**:fix 永遠先進上游層,再 merge/cherry-pick 往下流。禁止「先進客戶線再想辦法回流」——回流靠自覺必然失敗,要嘛制度化(定期回流 review),要嘛工具化(commit 打 tag 追蹤)。

### 版本維度

每個 Android 版本一組分支(`-a14`/`-a15`)。跨版本的 fix 靠 cherry-pick + 追蹤工具(issue tracker 記錄「此 bug 影響哪些版本、各版本修復 commit」)。**security patch 是最大宗的跨分支作業**:每月 bulletin 的 patch 要落到所有在維護的版本線——這件事必須工具化(腳本比對 patch 是否已在各分支),人工核對撐不過三個月。

---

## 三、與客戶的邊界

三種合作模式,SCM 佈局不同:

| 模式 | 說明 | SCM 佈局 |
|---|---|---|
| **Release 交付** | 定期出 BSP 包(manifest + source/prebuilt),客戶自己維護 | 你只管到 ②,客戶拿 pinned manifest 起自己的庫 |
| **代管客戶線** | 客戶專案分支在你的 server 上 | ③ 在你這,權限隔離(客戶 A 不可見客戶 B) |
| **聯合開發** | 大客戶,雙向 code flow | 專用 remote + gerrit 權限模型,回流條款寫進合約 |

共通要點:

- **權限隔離**:blob 的 source repo(3A、modem)與 prebuilt repo 分開,manifest 按客戶等級組裝(source 授權客戶 vs prebuilt-only 客戶拿到的 manifest 不同)。
- **release 節奏**:主 release(對齊年度升級,見升級篇)+ 月度 patch release(security + critical fix)。每個 release = pinned manifest + release notes + 公版 xTS 報告(見 xTS 篇)。
- **客戶回報問題的第一個問題**:「你的 manifest 版本?」——沒有 pinned manifest 文化,支援成本翻倍。

---

## 四、CI 與工程紀律

分支模型的成敗在 CI 與紀律,不在圖畫得漂不漂亮:

1. **每分支 daily build + 冒煙測試**:merge 往下流之後 build 壞掉要當天知道。分支數 × 產品數的 build matrix 是機房容量規劃的輸入。
2. **Gerrit + 強制 review**:AOSP 生態的標準;搭配 commit message 規範(`[MYVENDOR][BUG-ID]` 前綴)讓年度 rebase(見升級篇)時能機械識別自家 patch。
3. **合併機器人**:①→② 的定期自動 merge(conflict 才叫人),避免「攢三個月一次 merge」的大爆炸。
4. **分支生命週期管理**:明確的 EOL 政策(哪個版本線維護到何時),寫進與客戶的合約;死分支及時歸檔,別讓 CI 資源陪葬。
5. **考古工具**:`git log --grep BUG-ID` 跨 repo 搜尋的包裝腳本、fix 覆蓋範圍查詢(這個 CVE patch 進了哪些分支)——支援團隊每天在用的東西值得投資。

---

## 五、常見反模式

- **「快速出貨」直接在客戶線改公共 code** → 三個月後另一個客戶踩同一個 bug,沒人記得修過。
- **manifest 用 branch 不用 pinned revision 出 release** → 客戶今天 sync 和明天 sync 拿到不同東西,「同版本」變成薛丁諤的貓。
- **blob 更新沒有版本對應表** → prebuilt `.so` 與哪個 source commit 對應查不到,tombstone 符號化失敗(見穩定性篇)。
- **每個客戶 fork 全套 tree** → 磁碟與 CI 成本爆炸;正解是 overlay 式(客戶只 fork 真正要改的 repo)。

---

## 結語

> **多專案 BSP 管理的第一性原理:每個 fix 只存在一份,住在它能住的最上層,靠自動化往下流;每個 release 都能用一份 pinned manifest 一字不差地重現。** 做到這兩句話,一百個客戶專案是規模;做不到,十個專案就是泥沼。

---

## 系列全目錄

1. Chip Vendor 視角的 Android Build System 總覽
2. GKI 與 Kleaf Kernel Build 實戰
3. Soong 與 Android.bp 實戰:vendor variant 與 VNDK
4. SELinux Sepolicy 除錯實戰
5. OTA 與簽章流程實戰
6. xTS 認證測試實戰:CTS/VTS/GTS/STS
7. 開機流程與 Bootloader 實戰
8. HAL 開發實戰:AIDL End-to-End
9. Android 年度版本升級方法論
10. 效能與功耗調校實戰
11. Camera 與多媒體 Pipeline 實戰
12. Ramdump 與穩定性除錯實戰
13. 工廠與量產流程實戰
14. Android 上的 Rust
15. Project Mainline 與 APEX 對 Vendor 的影響
16. 多專案 BSP 的 Branch 與 Manifest 管理(本文)
