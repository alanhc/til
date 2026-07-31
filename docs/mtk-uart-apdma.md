# MediaTek UART APDMA：從 Virtual FIFO 硬體模型讀懂 `mtk-uart-apdma.c`

> 本文對照 `torvalds/linux` master 分支（2026-07）的 `drivers/dma/mediatek/mtk-uart-apdma.c` 與 `drivers/tty/serial/8250/8250_mtk.c` 撰寫，所有 register offset、常數與函式名皆取自 upstream source，非記憶推測。文末附驗證說明。

## 一、先把名字搞清楚

在 MediaTek 平台上「APDMA」這個詞會出現在兩個不同層次，很容易混淆：

- **硬體上的 APDMA**：Application Processor DMA，掛在 peripheral bus 上、服務低速周邊（UART / I2C / SPI 等）的 DMA controller。
- **Linux driver 裡的 APDMA**：upstream 目前只有 UART 這一支被 mainline 化，檔案是 `drivers/dma/mediatek/mtk-uart-apdma.c`，Kconfig 是 `CONFIG_MTK_UART_APDMA`。

所以當有人說「APDMA driver 掛掉了」，在 upstream 語境下九成是指 UART 那支。

另外要跟同目錄下的兩個兄弟區分開，它們是**完全不同的 controller**，不要混用除錯經驗：

| 檔案 | 用途 |
|---|---|
| `mtk-uart-apdma.c` | UART 專用，Virtual FIFO 模型 |
| `mtk-hsdma.c` | High-Speed DMA，memcpy 類 |
| `mtk-cqdma.c` | Command-Queue DMA |

還有一個常見誤記：DT compatible 是 `mediatek,mt6577-uart-dma`，**中間沒有 `ap`**。寫 `mediatek,mt6577-uart-apdma` 是 probe 不起來的。

## 二、為什麼 UART 需要 DMA

傳統 8250 UART 靠 FIFO + 中斷收送。FIFO 通常只有 16～64 bytes，baud rate 拉到 3～4 Mbps（典型場景：藍牙 H4/H5 over UART、GNSS、modem control channel）時：

- RX 端 FIFO 很快滿，來不及進中斷就 **overrun**，封包直接掉。
- 中斷頻率高到吃掉可觀的 CPU 時間，而且每次都是 IRQ context。

DMA 的價值不只是「省 CPU」，更關鍵的是**把 timing 容忍度從微秒級拉到毫秒級**。這在 tablet / phone 專案上直接決定 BT firmware download 會不會失敗。

## 三、核心：Virtual FIFO（VFF）模型

MediaTek 這顆 DMA 不是常見的「給我一個 buffer、搬完通知你」的 one-shot 模型，而是 **ring buffer + 硬體讀寫指標**，也就是把 DRAM 的一塊區域當成一個「虛擬的、很大的 FIFO」——這就是 VFF 前綴的由來。

概念上：

```
        VFF_ADDR ─────────────────────────► DRAM ring buffer
                  ┌───────────────────────────────────┐
                  │                                   │
                  │   ◄─ VFF_LEN (ring 大小) ─►       │
                  └───────────────────────────────────┘
                         ▲                 ▲
                      VFF_RPT           VFF_WPT
                    (read pointer)   (write pointer)

  TX 方向：SW 推進 WPT  → HW 追著讀，推進 RPT
  RX 方向：HW 推進 WPT  → SW 追著讀，推進 RPT
```

方向決定了誰是生產者。這點在讀 code 時非常重要，因為同一組 register 在 TX / RX 的語意是鏡像的。source 裡有兩行註解把這件事講得最清楚：

```c
/* TX: the buffer size HW can read. RX: the buffer size SW can read. */
#define VFF_VALID_SIZE		0x3c
/* TX: the buffer size SW can write. RX: the buffer size HW can write. */
#define VFF_LEFT_SIZE		0x40
```

也就是 `VALID_SIZE` 永遠是「已經有資料、可被消費的量」，`LEFT_SIZE` 永遠是「還有空間、可被生產的量」，只是消費者/生產者的身分依方向對調。

### 3.1 Ring wrap 的處理

Ring 大小上限與 wrap 標記是分開的兩個欄位，藏在同一個 32-bit 值裡：

```c
#define VFF_RING_SIZE	0xffff
/* invert this bit when wrap ring head again */
#define VFF_RING_WRAP	0x10000
```

低 16 bits 是實際 offset，bit 16 是 **wrap flag**。每繞完一圈就把這個 bit 反轉。這是經典的「多一位元解決 full/empty 歧義」手法——只看 offset 的話，`RPT == WPT` 無法分辨 ring 是空的還是滿的；加上 wrap bit 之後就沒有歧義。

RX handler 計算已收到多少 bytes 時就是靠這個：

```c
rg = mtk_uart_apdma_read(c, VFF_RPT);
wg = mtk_uart_apdma_read(c, VFF_WPT);
cnt = (wg & VFF_RING_SIZE) - (rg & VFF_RING_SIZE);

/*
 * The buffer is ring buffer. If wrap bit different,
 * represents the start of the next cycle for WPT
 */
if ((rg ^ wg) & VFF_RING_WRAP)
	cnt += len;
```

`(rg ^ wg) & VFF_RING_WRAP` 就是在問「這兩個指標在不在同一圈」。不在同一圈的話 `cnt` 會是負的，補一個 ring 長度回來。

### 3.2 中斷門檻不對稱

TX 跟 RX 的 threshold 策略刻意不同：

```c
/*
 * interrupt trigger level for tx
 * if threshold is n, no polling is required to start tx.
 * otherwise need polling VFF_FLUSH.
 */
#define VFF_TX_THRE(n)		(n)
/* interrupt trigger level for rx */
#define VFF_RX_THRE(n)		((n) * 3 / 4)
```

- **TX threshold = 整個 ring 大小**。意思是「等到 ring 全空才中斷」，等同於「這批資料全部送完了」。註解也點出，如果設成別的值就得去 polling `VFF_FLUSH`，那就失去意義了。
- **RX threshold = 3/4 ring**。留 1/4 的緩衝空間給「中斷發出後、SW 還沒來得及處理完」這段時間繼續寫入。這是防 overrun 的安全邊際，不是隨手取的數字。

## 四、Register map 全表

全部來自 source，base 是每個 channel 各自的 iomem：

| Offset | 名稱 | 說明 |
|---|---|---|
| `0x00` | `VFF_INT_FLAG` | 中斷狀態 / 清除 |
| `0x04` | `VFF_INT_EN` | 中斷致能 |
| `0x08` | `VFF_EN` | DMA 致能 |
| `0x0c` | `VFF_RST` | Warm reset |
| `0x10` | `VFF_STOP` | 停止請求 |
| `0x14` | `VFF_FLUSH` | 把殘留資料沖出去 |
| `0x1c` | `VFF_ADDR` | Ring buffer 實體位址（低 32 bits） |
| `0x24` | `VFF_LEN` | Ring 長度 |
| `0x28` | `VFF_THRE` | 中斷門檻 |
| `0x2c` | `VFF_WPT` | Write pointer |
| `0x30` | `VFF_RPT` | Read pointer |
| `0x3c` | `VFF_VALID_SIZE` | 可消費量（方向相關） |
| `0x40` | `VFF_LEFT_SIZE` | 可生產量（方向相關） |
| `0x50` | `VFF_DEBUG_STATUS` | 除錯狀態，卡住時的第一手線索 |
| `0x54` | `VFF_ADDR2` | 位址高位元（>32-bit 定址用） |

注意 `0x18`、`0x20`、`0x34`、`0x38` 是空洞——driver 沒用到，不代表硬體沒有，只是 upstream 用不上。

## 五、Driver 架構

### 5.1 建立在 virt-dma 之上

```c
#include "../virt-dma.h"
```

driver 不自己管 descriptor queue，而是用 kernel 的 **virtual DMA channel** 框架。三層結構：

```c
struct mtk_uart_apdmadev {   /* controller 層 */
	struct dma_device ddev;
	struct clk *clk;
	bool support_ext_addr;
	unsigned int dma_requests;
};

struct mtk_chan {            /* channel 層 */
	struct virt_dma_chan vc;
	struct dma_slave_config	cfg;
	struct mtk_uart_apdma_desc *desc;
	enum dma_transfer_direction dir;
	void __iomem *base;
	unsigned int irq;
	unsigned int rx_status;
};

struct mtk_uart_apdma_desc { /* descriptor 層 */
	struct virt_dma_desc vd;
	dma_addr_t addr;
	unsigned int avail_len;
};
```

`struct mtk_chan` 特別值得看：**每個 channel 有自己的 `base` 和自己的 `irq`**。這解釋了為什麼 DT 裡 `reg` 和 `interrupts` 都是一長串——不是一個 controller 配一組，而是 N 個獨立的 register block。

預設 channel 數：

```c
#define MTK_UART_APDMA_NR_VCHANS	8
```

可被 DT 的 `dma-requests` 覆寫。每個 UART port 要 TX / RX 各一條，所以 8 條大約服務 4 個 port。

### 5.2 註冊的 dmaengine ops

```c
dma_cap_set(DMA_SLAVE, mtkd->ddev.cap_mask);
mtkd->ddev.device_alloc_chan_resources = mtk_uart_apdma_alloc_chan_resources;
mtkd->ddev.device_free_chan_resources  = mtk_uart_apdma_free_chan_resources;
mtkd->ddev.device_tx_status      = mtk_uart_apdma_tx_status;
mtkd->ddev.device_issue_pending  = mtk_uart_apdma_issue_pending;
mtkd->ddev.device_prep_slave_sg  = mtk_uart_apdma_prep_slave_sg;
mtkd->ddev.device_config         = mtk_uart_apdma_slave_config;
mtkd->ddev.device_pause          = mtk_uart_apdma_device_pause;
mtkd->ddev.device_terminate_all  = mtk_uart_apdma_terminate_all;
mtkd->ddev.src_addr_widths = BIT(DMA_SLAVE_BUSWIDTH_1_BYTE);
mtkd->ddev.dst_addr_widths = BIT(DMA_SLAVE_BUSWIDTH_1_BYTE);
mtkd->ddev.directions = BIT(DMA_DEV_TO_MEM) | BIT(DMA_MEM_TO_DEV);
mtkd->ddev.residue_granularity = DMA_RESIDUE_GRANULARITY_SEGMENT;
```

三個關鍵限制值得記下來：

1. **只支援 1-byte bus width**。這是 UART，本來就是 byte stream。
2. **只有 slave 方向，沒有 `DMA_MEMCPY`**。要 memcpy 請找 HSDMA/CQDMA。
3. **沒有 `device_resume`**。有 `pause` 卻沒有 `resume`——這是設計上的取捨，pause 之後實際上得靠重新 issue 來恢復。

### 5.3 只吃一個 scatterlist entry

```c
/*
 * dmaengine_prep_slave_single will call the function. and sglen is 1.
 * 8250 uart using one ring buffer, and deal with one sg.
 */
static struct dma_async_tx_descriptor *mtk_uart_apdma_prep_slave_sg(...)
{
	if (!is_slave_direction(dir) || sglen != 1)
		return NULL;
	...
}
```

`sglen != 1` 直接回 `NULL`。因為 VFF 模型本來就是「一塊連續 ring buffer」，scatter-gather 在這裡沒有意義。這也是為什麼呼叫端一律用 `dmaengine_prep_slave_single()` 而非 `_sg()`。

**除錯提示**：如果你在 log 看到 prep 失敗但參數看起來都對，先確認呼叫端沒有傳多段 sg。

## 六、三條主要路徑

### 6.1 TX

`mtk_uart_apdma_start_tx()` 的邏輯：

```c
vff_sz = c->cfg.dst_port_window_size;
if (!mtk_uart_apdma_read(c, VFF_LEN)) {
	/* 第一次才做完整初始化 */
	mtk_uart_apdma_write(c, VFF_ADDR, d->addr);
	mtk_uart_apdma_write(c, VFF_LEN, vff_sz);
	mtk_uart_apdma_write(c, VFF_THRE, VFF_TX_THRE(vff_sz));
	mtk_uart_apdma_write(c, VFF_WPT, 0);
	mtk_uart_apdma_write(c, VFF_INT_FLAG, VFF_TX_INT_CLR_B);
	if (mtkd->support_ext_addr)
		mtk_uart_apdma_write(c, VFF_ADDR2, upper_32_bits(d->addr));
}
```

用 `VFF_LEN == 0` 當作「尚未初始化」的判斷條件——ring 長度為 0 是不可能的合法狀態，拿來當 sentinel 很省事。後續傳輸只推進 pointer，不重設 ring。

接著是推進 WPT，注意 wrap 處理：

```c
wpt = mtk_uart_apdma_read(c, VFF_WPT);
wpt += c->desc->avail_len;
if ((wpt & VFF_RING_SIZE) == vff_sz)
	wpt = (wpt & VFF_RING_WRAP) ^ VFF_RING_WRAP;

/* Let DMA start moving data */
mtk_uart_apdma_write(c, VFF_WPT, wpt);
```

當 offset 剛好走到 ring 邊界，就把 offset 歸零、翻轉 wrap bit。`(wpt & VFF_RING_WRAP) ^ VFF_RING_WRAP` 這個寫法同時完成了「清掉低位 offset」和「反轉 wrap bit」兩件事。

最後補一個 flush：

```c
if (!mtk_uart_apdma_read(c, VFF_FLUSH))
	mtk_uart_apdma_write(c, VFF_FLUSH, VFF_FLUSH_B);
```

確保尾端不足一個 burst 的資料也會被推出去，不會卡在硬體裡。

### 6.2 RX 與 residue 回報

RX 端 `mtk_uart_apdma_rx_handler()` 有一個容易忽略的 early return：

```c
mtk_uart_apdma_write(c, VFF_INT_FLAG, VFF_RX_INT_CLR_B);

if (!mtk_uart_apdma_read(c, VFF_VALID_SIZE))
	return;
```

**先清中斷旗標，再檢查有沒有資料。** 順序不能反——反過來會漏掉「中斷已觸發但資料在檢查瞬間被讀完」的競態。而且這個 early return 走的是「不關 DMA、繼續收」的路徑，只有真的有資料時才停下來處理。

計算完 `cnt` 之後：

```c
c->rx_status = d->avail_len - cnt;
mtk_uart_apdma_write(c, VFF_RPT, wg);
```

`rx_status` 存的是 **residue**（還沒收到的量），透過 `mtk_uart_apdma_tx_status()` 回報給上層：

```c
dma_set_residue(txstate, c->rx_status);
```

呼叫端就用 `rx_size - residue` 反推「這次實際收到多少」。8250_mtk 那邊正是這樣算的：

```c
dmaengine_tx_status(dma->rxchan, dma->rx_cookie, &state);
total = dma->rx_size - state.residue;
```

**這是整條 RX 路徑的資料量真相來源**。如果收到的 byte 數不對，`rx_status` 的計算就是第一個要下斷點的地方。

### 6.3 Terminate：三步驟停機

`mtk_uart_apdma_terminate_all()` 裡有一段註解直接寫出硬體要求的順序：

```c
/*
 * Stop need 3 steps.
 * 1. set stop to 1
 * 2. wait en to 0
 * 3. set stop as 0
 */
mtk_uart_apdma_write(c, VFF_STOP, VFF_STOP_B);
ret = readx_poll_timeout(readl, c->base + VFF_EN,
		  status, !status, 10, 100);
if (ret)
	dev_err(c->vc.chan.device->dev, "stop: fail, status=0x%x\n",
		mtk_uart_apdma_read(c, VFF_DEBUG_STATUS));

mtk_uart_apdma_write(c, VFF_STOP, VFF_STOP_CLR_B);
```

在此之前還會先 flush 並等 flush 完成，同樣有 100 µs timeout。**兩處 timeout 失敗時都會把 `VFF_DEBUG_STATUS` 印出來**——這是 driver 主動留給你的除錯線索，遇到 `stop: fail` 或 `flush: fail` 一定要把那個 status 值記下來。

最後 `synchronize_irq(c->irq)` 確保沒有 handler 還在跑，才去釋放 descriptor。這個順序是防 use-after-free 的必要條件。

## 七、消費端：`8250_mtk.c`

### 7.1 用不用 DMA 由 DT 決定

```c
dmacnt = of_property_count_strings(pdev->dev.of_node, "dma-names");
if (dmacnt == 2) {
	data->dma = devm_kzalloc(...);
	data->dma->fn = mtk8250_dma_filter;
	data->dma->rx_size = MTK_UART_RX_SIZE;
	data->dma->rxconf.src_maxburst = MTK_UART_RX_TRIGGER;
	data->dma->txconf.dst_maxburst = MTK_UART_TX_TRIGGER;
}
```

**必須剛好兩個 `dma-names`**（tx / rx），少一個就整個不啟用，而且不會有錯誤訊息。DT 寫錯時的症狀是「安靜地退回 PIO 模式」，效能掉了但沒有任何 log——這種無聲失敗最難查。

相關常數：

```c
#define MTK_UART_RX_SIZE	0x8000	/* 32 KB ring */
#define MTK_UART_TX_TRIGGER	1
#define MTK_UART_RX_TRIGGER	MTK_UART_RX_SIZE
```

RX ring 是 32 KB。搭配前面 `VFF_RX_THRE(n) = n * 3 / 4`，實際中斷門檻是 24 KB。

### 7.2 Window size 是怎麼傳下去的

```c
dma->rxconf.src_port_window_size = dma->rx_size;
dma->rxconf.src_addr             = dma->rx_addr;
dma->txconf.dst_port_window_size = UART_XMIT_SIZE;
dma->txconf.dst_addr             = dma->tx_addr;
```

APDMA driver 裡的 `vff_sz` 就是從 `src_port_window_size` / `dst_port_window_size` 讀出來的。這是一個相對少見的 `dma_slave_config` 欄位用法——**它在這裡的語意是 ring buffer 大小，而不是字面上的「port window」**。讀 code 時如果直覺套用一般意義會誤解。

TX 用的是 `UART_XMIT_SIZE`（tty layer 的標準值），跟 RX 的 32 KB 不同。

### 7.3 Console 一律不走 DMA

```c
/* disable DMA for console */
if (uart_console(port))
	up->dma = NULL;
```

這行在 `mtk8250_startup()` 裡。**只要這個 port 被當成 console，DMA 就被強制關掉。**

實務上這造成一個很容易誤判的現象：

> 你在 `chosen/stdout-path` 指定了某個 UART 當 console，然後懷疑 APDMA 沒作用，去量效能——結果當然沒作用，因為 code 直接把它關了。

原因是 console 需要在任意 context（包含 panic、atomic、IRQ disabled）同步輸出，DMA 的非同步語意根本無法滿足。這是設計決定，不是 bug。

**除錯時務必先確認你測的 port 不是 console。**

## 八、DT 綁定與定址寬度演進

```dts
apdma: dma-controller@11000400 {
	compatible = "mediatek,mt2712-uart-dma",
		     "mediatek,mt6577-uart-dma";
	reg = <0 0x11000400 0 0x80>,   /* channel 0 */
	      <0 0x11000480 0 0x80>,   /* channel 1 */
	      <0 0x11000500 0 0x80>,
	      ...;                      /* 每 channel 一個 0x80 block */
	interrupts = <...>;             /* 每 channel 一個 */
	clocks = <...>;
	clock-names = "apdma";
	#dma-cells = <1>;
};
```

每個 channel 佔 `0x80`，`reg` 和 `interrupts` 的項數必須跟 `dma-requests` 一致，否則 probe 時 `devm_platform_ioremap_resource(pdev, i)` 或 `platform_get_irq(pdev, i)` 會失敗。

`of_device_id` 表把定址寬度編碼進 `.data`：

```c
static const struct of_device_id mtk_uart_apdma_match[] = {
	{ .compatible = "mediatek,mt6577-uart-dma", .data = (void *)32 },
	{ .compatible = "mediatek,mt6795-uart-dma", .data = (void *)33 },
	{ .compatible = "mediatek,mt6835-uart-dma", .data = (void *)34 },
	{ .compatible = "mediatek,mt6985-uart-dma", .data = (void *)35 },
	{ /* sentinel */ },
};
```

32 → 33 → 34 → 35 bits，直接反映了行動裝置記憶體容量往上爬的歷史（4 GB → 8 GB → 16 GB → 32 GB）。

probe 時的處理：

```c
bit_mask = (unsigned int)(uintptr_t)of_device_get_match_data(&pdev->dev);
if (bit_mask > 32)
	mtkd->support_ext_addr = true;

rc = dma_set_mask_and_coherent(&pdev->dev, DMA_BIT_MASK(bit_mask));
```

超過 32 bits 就啟用 `VFF_ADDR2` 寫入高位元。

**這是實務上的高頻踩雷點**：如果 DT 上只寫了 `mediatek,mt6577-uart-dma`（32-bit），但 buffer 被配置在 4 GB 以上的實體位址，DMA 會寫到錯誤位置。舊 binding 文件裡的 `mediatek,dma-33bits` 屬性後來被 compatible-based 的做法取代了。新平台請確認 compatible 用對，不要為了「反正相容」就套舊的字串。

## 九、除錯清單

依「最常見 → 最少見」排序：

1. **這個 port 是 console 嗎？** 是的話 DMA 被 `mtk8250_startup()` 強制關閉，一切效能測試無效。
2. **DT 的 `dma-names` 剛好兩個嗎？** 不是的話靜默退回 PIO，沒有任何錯誤訊息。
3. **compatible 字串對嗎？** 是 `-uart-dma` 不是 `-uart-apdma`；定址寬度也綁在這個字串上。
4. **`reg` / `interrupts` 的項數對得上 `dma-requests` 嗎？** 對不上會在 probe 迴圈第 i 次失敗。
5. **Clock 和 power domain 上了嗎？** `devm_clk_get()` 失敗會直接 `dev_err("No clock specified")` 並中止 probe；driver 用 `pm_runtime`，channel 的 alloc/free 對應 `pm_runtime_resume_and_get()` / `pm_runtime_put_sync()`。
6. **看到 `stop: fail` 或 `flush: fail` 了嗎？** 把訊息裡的 `VFF_DEBUG_STATUS` 值抄下來，那是硬體卡在哪的直接證據。
7. **收到的 byte 數不對？** 斷點下在 `mtk_uart_apdma_rx_handler()` 的 `c->rx_status = d->avail_len - cnt;`，檢查 wrap bit 的判斷。
8. **34/35-bit 平台上偶發資料錯亂？** 檢查 `support_ext_addr` 有沒有被設起來、`VFF_ADDR2` 有沒有寫入。

Runtime 觀察管道：

```sh
# 確認 driver 有註冊
ls /sys/class/dma/

# 中斷次數（有 DMA 的話 UART 中斷應該顯著少於 PIO 模式）
cat /proc/interrupts | grep -i -E 'apdma|uart'

# 動態 log
echo 'file mtk-uart-apdma.c +p' > /sys/kernel/debug/dynamic_debug/control
```

## 十、小結

`mtk-uart-apdma.c` 只有 653 行，但濃縮了幾個值得帶走的通用觀念：

- **Ring buffer 用額外一個 bit 解決 full/empty 歧義**，是 lock-free 佇列的經典手法，不限於 DMA。
- **TX / RX threshold 不對稱**反映了兩個方向風險不同：TX 慢一點只是延遲，RX 慢一點會掉資料。
- **同一組 register 在不同方向語意鏡像**，讀 MediaTek 硬體 driver 時是常態，先確認方向再讀 code。
- **「安靜地退回較差路徑」是最難查的失敗模式。** `dma-names` 數量不對就不啟用 DMA、console port 直接關 DMA，兩個都不會留下 log。遇到「功能正常但效能不對」的問題，優先懷疑這類無聲降級。

---

## 驗證說明

本文所有 code 片段、register offset、常數值與註解，皆直接取自以下 upstream 檔案（2026-07-29 抓取自 `raw.githubusercontent.com/torvalds/linux/master`）：

- `drivers/dma/mediatek/mtk-uart-apdma.c`（653 行）
- `drivers/tty/serial/8250/8250_mtk.c`

DT binding 範例取自 `Documentation/devicetree/bindings/dma/mtk-uart-apdma.txt`（kernel.org 線上版本）。該文件在較新的 kernel 已轉為 YAML 格式，欄位語意一致但檔名不同，實作前請以你所用 kernel 版本的 binding 為準。

以下為**作者依 code 行為所作的推論，非文件明述**，引用時請自行驗證：

- 34/35-bit 定址寬度對應 16 GB / 32 GB 記憶體容量的說法，是依 `DMA_BIT_MASK` 語意推得，MediaTek 未公開說明各數值的導入動機。
- 「8 條 channel 約服務 4 個 port」是由「TX/RX 各一條」推得的算術，實際配置依平台 DT 而定。
- 除錯清單的排序依據為作者經驗，非統計數據。

`VFF_DEBUG_STATUS` 各 bit 的意義需要 MediaTek 內部文件，本文未涵蓋。
