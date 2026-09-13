# Linux Kernel 概觀

Linux 是 monolithic kernel：排程、記憶體管理、檔案系統、網路、driver 都跑在同一個 kernel address space。但它支援 loadable kernel module (`.ko`)，可在執行期動態載入/卸載，兼具模組化彈性。

## User space vs Kernel space

- **Kernel space**：特權模式 (privileged / ring 0)，可存取所有硬體與記憶體。
- **User space**：一般程式執行的受限模式，不能直接碰硬體。
- 兩者透過 **system call** 交界；user 程式要做 I/O、開檔、建 process 都得經由 syscall 進入 kernel。

## 主要 subsystem

- **Process scheduler**：決定哪個 task 上 CPU（如 CFS / EEVDF）。
- **Memory management**：virtual memory、paging、配置器。
- **VFS**：抽象各種檔案系統 (ext4、xfs、tmpfs…) 的統一介面。
- **Network stack**：socket、TCP/IP。
- **Device drivers**：佔 kernel 原始碼最大宗。

## System call

- glibc 等 wrapper 包裝，最終以特定指令 (x86-64 的 `syscall`) 觸發，切換到 kernel。
- 可用 `strace <cmd>` 觀察一支程式實際發出的 syscall。

參考：https://www.kernel.org/
