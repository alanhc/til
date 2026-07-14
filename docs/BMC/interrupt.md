# Linux 中斷處理（Interrupt）

硬體透過 **IRQ（Interrupt Request）** 通知 CPU 有事件發生（如網路封包到達、timer 到期），CPU 暫停當前工作轉去執行對應的 **irq handler**。這讓系統不必忙碌輪詢（polling）即可即時反應。

/proc/interrupts

irq handler

## 觀察中斷

`/proc/interrupts` 可看到每個 IRQ 編號、在各 CPU 上的觸發次數、中斷控制器與對應裝置名稱：

```bash
cat /proc/interrupts
watch -n1 cat /proc/interrupts   # 動態觀察哪個中斷正在頻繁觸發
```

## irq handler 與 top/bottom half

中斷處理常拆成兩段，避免長時間關中斷：

- **top half（硬體中斷 handler）**：在中斷情境（interrupt context）中執行，必須極短、不可睡眠，通常只做必要的硬體 ack 與記錄，再排程後半段。
- **bottom half（延後處理）**：把耗時工作延後到較寬鬆的情境執行，Linux 提供 softirq、tasklet、workqueue 等機制（其中 workqueue 跑在 process context，可睡眠）。

## 註冊 handler

kernel driver 以 `request_irq()` 註冊 handler，handler 依實際狀況回傳 `IRQ_HANDLED`（已處理）或 `IRQ_NONE`（非本裝置的中斷，用於共享 IRQ）。
