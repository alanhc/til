# 異構 SoC 的 IPC 與三種 Domain：一份自學地圖

> 素材：mainline kernel、TF-A，以及手邊的兩塊開發板。
> 適用對象：做 Android/Linux 平台整合，但沒實際碰過協處理器韌體的人。

---

## 為什麼「domain」這個詞會讓人學不下去

剛開始查資料時，「domain」在不同文件裡指的是完全不同的東西。
把它拆成三個彼此獨立的面向之後，整件事才變得可學。

| 面向 | 它回答的問題 | Linux 對應機制 |
|---|---|---|
| **Lifecycle domain** | 這顆核現在活著嗎？掛了誰救？ | `remoteproc` |
| **Power domain** | 它有沒有電？時脈誰開？refcount 多少？ | `genpd` |
| **Memory / access domain** | 它能存取哪段記憶體？位址怎麼翻譯？ | IOMMU / carveout |

三者在 device tree 裡交會——`power-domains`、`iommus`、`mboxes`、`memory-region`
這幾個 property 一起讀，才是一顆 IP 的完整身分。

## 異構 IPC 其實只有四個零件

不管叫 RPMsg、IPI、mailbox 還是 SCPI，拆開來都是這四樣：

1. **共享記憶體 + vring** — 資料本身
2. **Mailbox / doorbell** — 通知對方「有東西了」的中斷
3. **Resource table** — 韌體宣告它需要什麼記憶體、要幾組 vring
4. **Name service** — endpoint 協商，讓兩邊對得上號

RPMsg 只是把這四個包成一套標準 API。看懂這四樣，換平台就只是換 device tree。

---

## 實驗一：BeagleBone Black，有協處理器的世界

AM3358 = Cortex-A8 + 兩顆 PRU（200MHz、無 cache、無 pipeline stall）。
它走的是**完全標準的 mainline remoteproc + rpmsg 流程**，和 i.MX8、TI AM62、
各家 SoC 的 SCP 是同一套 API。

四個階段，每階都要量測，不要只求跑通：

### 1. 跑通 loopback
`/sys/class/remoteproc/remoteprocN/state` 寫 start/stop，firmware 放 `/lib/firmware`，
Linux 端開 rpmsg char device 收發。

**重點不是跑起來**，而是打開 firmware 的 ELF 看 resource table，
把它宣告的 carveout 與 vring 位址，跟 `dmesg`、`/proc/iomem` 對起來。
這一步做完，「韌體怎麼跟 kernel 講好記憶體怎麼分」就具體了。

### 2. 拆解一次往返延遲
- PRU 端：數指令週期。沒有 cache、沒有 pipeline stall，**指令數就是時間**。
- Linux 端：ftrace 抓 mailbox IRQ → vring callback → user space wakeup。

結論通常違反直覺：延遲的大頭不在 IPC 本身，在**排程喚醒**。
這個結論在任何 NPU/DSP 的 command submission 上都成立。

### 3. 故意弄壞它
讓遠端進無窮迴圈、寫壞 vring index、傳輸中途 `echo stop`。
觀察 remoteproc 的錯誤偵測與 recovery 路徑。

異構系統真正難的部分全在這裡——**A 掛了 M 要怎樣、M 掛了 A 怎麼知道**。
正常運作時你什麼也學不到，只有壞掉時才會暴露誰依賴誰。

### 4. 接到 power domain
把協處理器的 power/clock domain 關掉再開，觀察 remoteproc 與 genpd 的
相依關係與 refcount。做完這步，三種 domain 才真正串起來。

---

## 實驗二：Orange Pi Zero 2（H616），沒有協處理器的世界

Allwinner H616 已經拿掉了 ARISC 管理處理器（早期 A64/H3/H5 才有，
社群還有 crust 這套開源 SCP 韌體）。所以這塊板子上沒有 IPC 可以練。

但它是很好的**對照組**。TF-A 的 Allwinner 文件講得很清楚：
A64/H5 需要把程式碼載進 ARISC 才能控制 CPU 上下電，而 H6/H616 是由
BL31 直接寫 power sequence 暫存器。

同一件事，兩種架構：

- **有 SCP**：工作外包出去，代價是要處理 IPC、生命週期、故障恢復
- **無 SCP**：EL3 自己下場寫暫存器，簡單但 CPU 得醒著才能做決策

把兩邊都跑過，對「為什麼要有 SCP」的理解會比讀十篇架構文章扎實。
而且 H616 的 TF-A / U-Boot / kernel 三段都能自己 build 自己刷，
是很順的 boot chain 練習台。

---

## 讀碼：mainline 裡的現成教材

以 MediaTek 平台為例（這些都是 mainline 公開程式碼，任何人都能讀）：

| 主題 | 檔案 |
|---|---|
| 協處理器生命週期 + IPI | `drivers/remoteproc/mtk_scp.c`、`mtk_scp_ipi.c` |
| Power domain | `drivers/soc/mediatek/mtk-pm-domains.c` |
| Memory domain | `drivers/iommu/mtk_iommu.c` + SMI larb |
| 硬體命令佇列 | `drivers/mailbox/mtk-cmdq-mailbox.c` |
| 無 SCP 的 PSCI 實作 | TF-A `plat/allwinner/` |

`mtk_scp.c` 當初是為 Chromebook 平台上游化的，patch series、review 討論、
binding 文件都公開可查——**從 patch series 反推系統架構**是我最推薦的讀法，
因為設計取捨的理由通常寫在 review comment 裡，不在文件裡。

---

## 建議的順序

先 BBB 做完四階（有實測數據），再讀 mainline 對照（有了實作直覺再讀碼快很多），
最後 H616 補 boot chain 那一段。倒過來走會很痛苦。
