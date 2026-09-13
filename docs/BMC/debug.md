# BMC 除錯手法

BMC 上資源有限（記憶體小、無 GUI），常用兩種方式除錯：遠端 **gdb server** 動態除錯，以及事後的 **coredump analysis**。

## gdbserver 遠端除錯

BMC 端只跑輕量的 `gdbserver`，把完整的 gdb 跑在開發主機上，透過網路連線除錯目標程式：

```bash
# 在 BMC 上啟動 gdbserver，監聽 port 並附掛到目標程式
gdbserver :2345 /usr/bin/my-daemon
# 或附掛到已在跑的 process
gdbserver :2345 --attach <pid>
```

```bash
# 在開發主機上，用對應 target 的 cross gdb 連線
arm-linux-gnueabi-gdb my-daemon
(gdb) target remote <bmc-ip>:2345
```

## coredump analysis

程式 crash 時保留 core 檔，事後離線分析當時的呼叫堆疊與變數：

```bash
# 開啟 core dump（大小不限）
ulimit -c unlimited
# 事後以 gdb 載入執行檔與 core 檔
gdb /path/to/binary /path/to/core
(gdb) bt        # 印出 backtrace 找出 crash 位置
```

分析時務必使用**帶有 debug symbol** 的未 strip 版本 binary，backtrace 才能對應到原始碼行號。OpenBMC 系統多以 `systemd-coredump` 收集 core，可用 `coredumpctl list` / `coredumpctl gdb` 取用。
