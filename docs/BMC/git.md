# Git / Gerrit Workflow

OpenBMC 上游採 **Gerrit** 做 code review，流程與 GitHub PR 不同：以「每個 commit = 一個可審查的 change」為單位，靠 `Change-Id` 追蹤修訂。

核心工具 `git review`：

```bash
git clone https://gerrit.openbmc.org/<repo>
# 改完 code
git commit -s            # -s 加 Signed-off-by（必要）
git review               # 推到 Gerrit 建立/更新 change
```

重點：
- commit message 尾端會有 `Change-Id: I....`（由 commit-msg hook 產生），同一個 change 的多次修訂共用它。
- **修訂既有 change**：改完後 `git commit --amend`，再 `git review`，會變成同一 change 的新 patch set，而不是新 change。
- review 分數：`Code-Review +2` 才可合併，`Verified +1`（多由 CI 給）。
- 每個 commit 都要 `Signed-off-by`（DCO）。

參考：https://gerrit.openbmc.org/

相關筆記：yocto、openbmc。
