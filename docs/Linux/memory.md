# Linux 記憶體管理

每個 process 看到的是自己獨立的 **virtual address space**，實體記憶體 (physical memory) 由 kernel 統一管理。virtual → physical 的轉換靠 **MMU** 搭配 page table 完成。

## Paging 與 MMU

- 記憶體以固定大小的 **page** 管理（x86-64 常見 4 KiB，也支援 2 MiB / 1 GiB huge page）。
- MMU 逐級走 page table 做位址轉換，並用 **TLB** 快取近期轉換結果加速。
- 存取未映射或無權限的頁 → **page fault**；kernel 可據此做 demand paging、copy-on-write。

## 配置器 (allocator)

- **Buddy system**：以 2 的次方的頁區塊管理實體頁，配置/釋放時分裂或合併，減少 external fragmentation。
- **Slab / slub**：在 buddy 之上，為固定大小的 kernel 物件 (如 `task_struct`, inode) 做快取，減少 internal fragmentation 並加速配置。

## Swap

- 記憶體吃緊時，把較少用的 page 寫到 swap（分割區或檔案），釋放實體記憶體。
- 過度 swap 會造成 thrashing；`vm.swappiness` 可調整傾向。

觀察指令：`free -h`、`vmstat`、`/proc/meminfo`。
