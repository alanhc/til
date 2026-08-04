# AOSP Codebase：repo 與 manifest

AOSP 不是一個 git repo，而是**上千個 git repo 的集合**。管理它們的工具叫 `repo`（Google 寫的 Python 腳本，包在 git 外面），而「哪些 repo、各自要抓哪個分支、放在哪個目錄」全部記錄在一份 **manifest** 裡。

搞懂 manifest，就能回答「我這份 code 到底是哪一版」以及「怎麼只換掉其中一個 repo」。

## .repo 目錄

`repo init` 之後，工作目錄底下會出現一個 `.repo/`：

```
.repo/
├── manifests/          # manifest 本身也是一個 git repo
│   ├── default.xml     # 主 manifest
│   └── ...
├── manifest.xml        # 指向目前使用的 manifest（symlink）
├── projects/           # 各個 repo 的 git 目錄（實體）
└── repo/               # repo 工具本身
```

## default.xml：版本的真正來源

想知道手上這份 code 是哪一版，看這裡：

```bash
cat .repo/manifests/default.xml
```

```xml
<default revision="android16-qpr2-release"
         remote="aosp"
         sync-j="4" />
```

- **`revision`**：預設的分支/tag。**這就是版本**——上面這份是 Android 16 QPR2 的 release 分支。
- **`remote`**：預設從哪個 remote 抓（對應檔案裡的 `<remote>` 定義）。
- **`sync-j`**：預設的平行下載數。

檔案裡接著會有大量的 `<project>` 條目，每個描述一個 repo：

```xml
<project path="frameworks/base" name="platform/frameworks/base" />
<project path="external/libcxx" name="platform/external/libcxx"
         revision="some-other-branch" />
```

- `name`：remote 上的 repo 路徑。
- `path`：checkout 到本機的哪個目錄。
- `revision`：沒寫就用 `<default>` 的，寫了就覆蓋——**所以個別 repo 可能和主線不同版**。

其他常用查詢：

```bash
repo manifest -r -o snapshot.xml   # 匯出目前每個 repo 的實際 commit（-r = revision 展開成 SHA）
repo info                           # 看目前的 manifest 分支與各 project 狀態
repo forall -c 'git log -1 --oneline'   # 對每個 repo 執行指令
```

`repo manifest -r` 匯出的快照非常重要：**它把「浮動的分支名」變成「固定的 commit SHA」**，是要重現某次 build 時唯一可靠的做法。

## GLOBAL-PREUPLOAD.cfg

```
.repo/manifests/GLOBAL-PREUPLOAD.cfg
```

這份設定定義 **`repo upload` 之前會自動跑的檢查**（preupload hook），對所有 project 生效。典型的檢查項目：

- commit message 格式（是否有 `Bug:`、`Test:` 欄位）
- 是否包含 `Change-Id`（Gerrit 需要）
- 程式碼格式（`clang-format`、`google-java-format`）
- 檔案權限、行尾、是否誤加二進位檔

個別 project 也可以有自己的 `PREUPLOAD.cfg`，會和全域的疊加。

想跳過檢查（不建議）：

```bash
repo upload --no-verify
```

## 常用 repo 指令

```bash
# 初始化：指定 manifest 來源與分支
repo init -u https://android.googlesource.com/platform/manifest \
          -b android-15.0.0_r34

# 同步（-c 只抓當前分支，-j 平行數，--no-tags 省空間）
repo sync -c -j8 --no-tags --fail-fast

# 只同步某幾個 project
repo sync frameworks/base

# 看所有 repo 的修改狀態
repo status

# 建立跨 repo 的工作分支
repo start my-feature --all
```

`repo sync` 的幾個實用選項：

| 選項 | 作用 |
|---|---|
| `-c` / `--current-branch` | 只抓 manifest 指定的分支，大幅節省時間與空間 |
| `--no-tags` | 不抓 tag，同上 |
| `-j<N>` | 平行下載數，太大容易被 server 限流 |
| `--fail-fast` | 有 repo 失敗就立刻停，不要拖完整輪 |
| `--force-sync` | 強制覆蓋本地變更（**會丟掉修改**） |

## local_manifests：加自己的 repo

不改上游 manifest 而加入自己的 project，做法是放一份 local manifest：

```
.repo/local_manifests/my_stuff.xml
```

```xml
<?xml version="1.0" encoding="UTF-8"?>
<manifest>
  <remove-project name="platform/packages/apps/Browser2" />
  <project path="vendor/myvendor"
           name="myvendor/vendor"
           remote="github"
           revision="main" />
</manifest>
```

- `<remove-project>`：把上游的某個 project 拿掉。
- `<project>`：加入自己的。

這樣 `repo sync` 就會把自訂的 repo 一併拉下來，而且升級上游 manifest 時不會衝突。

## 相關筆記

- [AOSP Build System 與 chip vendor](./01-android-build-system-chip-vendor.md)
- [BSP 分支與 manifest 管理](./16-bsp-branch-manifest-management.md)
- [AOSP Pixel 完整流程](./aosp_pixel_full_workflow.md)
- [Android Build Number](./Android_build_number.md)
