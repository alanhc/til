# Linux 開機流程

從按下電源到看到登入畫面，大致經過以下階段：

1. **韌體 (BIOS / UEFI)**：CPU reset 後執行主機板韌體，做硬體初始化與 POST，再依開機順序找開機裝置。
   - Legacy BIOS：讀取 MBR 第一磁區的 boot code。
   - UEFI：讀 EFI System Partition (ESP) 上的 `.efi` bootloader，支援 GPT 與 Secure Boot。
2. **Bootloader (如 GRUB)**：載入 kernel image (`vmlinuz`) 與 initramfs 到記憶體，帶入 kernel 參數 (cmdline) 後跳入 kernel。
3. **Kernel 初始化**：解壓自身、初始化 subsystem 與必要 driver、掛載 initramfs 當臨時 root。
4. **initramfs / initrd**：記憶體中的臨時 root filesystem，內含掛載「真正 root」所需的 driver/工具（如 LVM、RAID、加密磁碟），完成後 `switch_root` 切到真正的 rootfs。
5. **init (PID 1)**：kernel 啟動的第一個 user space 程序，現代發行版多為 **systemd**，負責把系統帶到目標狀態、拉起服務。

## 觀察

- `dmesg` — kernel ring buffer（開機訊息）。
- `systemd-analyze` / `systemd-analyze blame` — 分析開機耗時。

相關：ARM/embedded 平台的開機流程見 `booting/boot.md`。
