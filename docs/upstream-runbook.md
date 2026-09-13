# 送出 kernel patch：實際跑過一遍的步驟

這份是操作手冊。每個步驟都實際執行過，包含四個中途撞到的錯誤與它們的解法。

另外兩份文件是**手冊**（按主題查用法）和**歷程**（走一遍開發過程）。

---

## 0. 目前狀態

已送出：[change 4200863](https://android-review.googlesource.com/c/kernel/common/+/4200863)

```text
ANDROID: dma-heap: fix struct dma_heap kernel-doc
分支：android-mainline
狀態：NEW，等待 review
```

環境設定已完成的部分：

| 項目 | 值 |
|---|---|
| `user.name` | `Alan Tseng` |
| `user.email` | `alan.tseng.cs@gmail.com`（必須是 Gerrit 已註冊的） |
| `http.cookiefile` | `~/.gitcookies` |
| push 目標 | `git push aosp HEAD:refs/for/android-mainline` |

`aosp` 這個 remote 指向 `android.googlesource.com`，**它會自動路由到 Gerrit**，不需要改成 `android-review` 主機。

---

## 1. 選題材（真正的門檻）

流程只要學一次，找到值得修的東西才是每次都要重來的部分。

### 三道必過的關卡

**關卡一：這段程式碼在 mainline 存不存在？**

```bash
git log --oneline -1 -S "函式名" -- 路徑/檔案.c
```

看到 `ANDROID:` 開頭 → ACK 專屬，只能送 Gerrit，不要送 LKML。

**關卡二：mainline 現在還錯不錯？**

不要相信手上的 tree。`android14-6.1` 落後 mainline 約兩年。

```bash
curl -s https://raw.githubusercontent.com/torvalds/linux/master/路徑/檔案.c | grep -B12 "函式簽名"
```

**關卡三：`android-mainline` 現在還錯不錯？**

ACK 的改動先進 `android-mainline`，再往下合到發行分支。**直接送舊發行分支多半會被退。**

```bash
cd ~/android14-6.1/common && git fetch --depth=1 aosp android-mainline
```

```bash
git show FETCH_HEAD:路徑/檔案.c | grep -B12 "函式簽名"
```

`--depth=1` 很重要，完整 fetch 會拉幾百 MB。

### 這三關實際淘汰掉的兩個候選

| 候選 | 淘汰在哪 |
|---|---|
| `dma_buf_set_name` kernel-doc | 關卡二：mainline 是對的。關卡三：android-mainline 裡那段 ANDROID 修改已被移除，只剩舊發行分支有 → 送上去會被當 churn 退 |
| `dma_buf_account_task` 等 | 關卡一：`git log` 顯示是 `ANDROID:` commit → 不是 mainline 題材 |

**兩分鐘的檢查，換掉一次上傳後被打回票。** 這是整份文件最有價值的一段。

### 掃描方式

```bash
scripts/kernel-doc -none 路徑/檔案.c 2>&1 | grep warning
```

```bash
scripts/checkpatch.pl -f 路徑/檔案.c
```

批次掃 `android-mainline` 的某幾個子系統（不用整棵 checkout）：

```bash
cd ~/android14-6.1/common && git archive FETCH_HEAD drivers/dma-buf drivers/android | tar -x -C /tmp/am
```

```bash
for f in $(find /tmp/am -name '*.c'); do n=$(scripts/kernel-doc -none "$f" 2>&1 | grep -c warning); [ "$n" -gt 0 ] && echo "$n $f"; done
```

### 什麼會被接受

| 類型 | mainline | ACK |
|---|---|---|