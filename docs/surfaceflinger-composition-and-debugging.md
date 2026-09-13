# SurfaceFlinger：Android 畫面是怎麼被「合成」出來的

## 前言

在 Android 上做系統整合，遲早會遇到這類 bug report：

- 「開分割畫面之後耗電變高」
- 「滑動列表偶爾掉幀，但 App 端 profiler 看起來很正常」
- 「某個浮動視窗疊上去之後，整台機器溫度就上來了」

這三個問題的共同答案，往往都指向同一個 native process：**SurfaceFlinger**。

它是 Android 圖形堆疊裡最容易被忽略、但對功耗與流暢度影響最大的一層。App 端的 profiler 看不到它，因為它根本不在 App 的 process 裡；而它做的決策（要用硬體還是 GPU 合成）幾乎不會出現在任何 UI 上，只會反映在電流與 frame time 上。

這篇文章整理 SurfaceFlinger 的角色、資料流、合成路徑的分歧點，以及實務上可用的除錯手段。

---

## 一、SurfaceFlinger 是什麼

SurfaceFlinger（以下簡稱 SF）是 Android 的**畫面合成服務**，以 native process 形式存在：

```
/system/bin/surfaceflinger
```

由 init 在開機早期啟動，屬於 Android 開機流程中相當前面的一環——沒有它，畫面出不來。

它的職責可以用一句話概括：

> 把系統中所有可見的 layer，合成成一張最終畫面，並在正確的時間點送到 display。

這裡的 layer 不只是「App 的視窗」。一個典型的畫面至少包含：

| Layer | 來源 |
|---|---|
| App 主視窗 | 前景 Activity |
| Status bar | SystemUI |
| Navigation bar | SystemUI |
| 輸入法視窗 | IME |
| Dim / scrim layer | 對話框背後的遮罩 |
| Rounded corner overlay | 螢幕圓角遮罩 |
| Cursor / pointer | 外接滑鼠、觸控筆 |

SF 要做的，就是決定這些 layer 的 Z-order、裁切區域、透明度混合方式，然後選擇一條最省成本的路徑把它們疊起來。

**重要的觀念切分：**

- **繪製（rendering）** 是 App 自己的事，發生在 App process 裡（Skia / HWUI / Vulkan / OpenGL）。
- **合成（composition）** 是 SF 的事。

App 畫得再快，如果合成端塞住，畫面照樣掉幀。反之也成立。這兩件事分開看，是後續除錯的基礎。

---

## 二、資料流：Buffer 是怎麼傳過去的

### 2.1 傳統 BufferQueue 模型

Android 圖形堆疊的核心是 **producer–consumer** 模型，中介是 `BufferQueue`：

```
App process                          SurfaceFlinger process
┌──────────────────┐                ┌──────────────────────┐
│  Canvas / GL     │                │                      │
│       ↓          │                │                      │
│  Surface         │  BufferQueue   │  Layer (consumer)    │
│  (producer)      │ ─────────────► │       ↓              │
│                  │  dequeue/queue │  Composition         │
└──────────────────┘                └──────────────────────┘
```

流程大致是：

1. App 從 BufferQueue `dequeueBuffer()` 拿到一塊可寫入的 graphic buffer
2. App 把畫面內容繪製進去（GPU 或 CPU）
3. App `queueBuffer()` 把 buffer 交回佇列
4. SF 在下一個合成週期 `acquireBuffer()` 取用
5. 合成完成、buffer 不再被需要後 `releaseBuffer()` 歸還給 App 重複使用

Buffer 本身是 `GraphicBuffer`（底層是 gralloc 配置的共享記憶體），**跨 process 傳遞的只有 handle，不是像素資料**。這是整個機制能夠低成本的關鍵——沒有任何一次 memcpy。

通常會配置 2~3 塊 buffer（double / triple buffering）。Triple buffering 能吸收 App 偶發的 frame time 抖動，代價是多一幀的延遲。

### 2.2 BLAST：Android 12 之後的變化

Android 12 引入 **BLAST**（Buffer Layer At SurfaceFlinger Transaction），把 BufferQueue 的實作搬到 client 端，buffer 改以 transaction 形式提交給 SF。

動機是減少 App 與 SF 之間的 binder 往返次數與同步點——舊模型下 SF 是 consumer，`dequeue`/`queue` 都可能牽涉跨 process 呼叫；BLAST 讓 buffer 提交與其他 layer 屬性變更（位置、大小、透明度）能在**同一個 atomic transaction** 裡一起送出。

實務上的意義：以前「視窗 resize 時 buffer 尺寸與 layer 尺寸不同步」造成的一幀閃爍或黑邊，在 BLAST 之後結構性地變好了。這對平板的分割畫面拖曳、自由視窗調整尺寸特別有感。

---

## 三、節奏：VSYNC 與 Choreographer

合成不能隨時做，必須對齊 display 的掃描週期，否則會 tearing。

### 3.1 硬體 VSYNC 與軟體模型

Display 硬體會週期性產生 VSYNC 訊號。但 SF 不會直接把每個硬體 VSYNC 都轉發出去——那樣太耗電，而且時間點也不理想。

SF 內部維護一個 VSYNC 的**預測模型**（早期叫 `DispSync`，後來演化為 `VSyncPredictor` / `VsyncTracker`）：用取樣到的硬體 VSYNC 時間戳擬合出週期與相位，然後生成兩條虛擬時間軸：

- **VSYNC-app**：喚醒 App 開始繪製下一幀
- **VSYNC-sf**：喚醒 SF 開始合成

兩者之間刻意錯開一個 phase offset。這個 offset 是功耗與延遲之間的權衡參數：

- offset 太小 → App 還沒畫完 SF 就要合成，容易掉幀
- offset 太大 → 每一幀的 end-to-end latency 增加，觸控會有拖沓感

在支援可變刷新率（VRR）的裝置上還會多一層 `Scheduler` 決定當下該用哪個 refresh rate，並在切換時處理 offset 重算。

### 3.2 App 端的 Choreographer

App 這邊對應的入口是 `Choreographer`。`View.invalidate()` 不會立刻繪製，而是註冊一個 callback，等 VSYNC-app 到來時才真正走 measure / layout / draw。

所以 UI thread 的一幀時間預算是**一個 refresh interval**：60Hz 是 16.6ms，90Hz 是 11.1ms，120Hz 只有 8.3ms。高刷新率把預算壓縮得很緊，這是高刷平板上 jank 特別容易被看見的原因。

---

## 四、關鍵分歧點：Device Composition vs Client Composition

這是整篇文章最重要的一節。SF 有兩條合成路徑，成本差距很大。

### 4.1 Hardware Composer HAL

SF 透過 **HWC**（Hardware Composer HAL，新版本走 AIDL composer 介面）與顯示硬體溝通。流程的核心是兩個呼叫：

1. **`validateDisplay()`** — SF 把這一幀所有 layer 的描述（位置、格式、blending mode、transform）交給 HWC，問：「這些你能自己處理嗎？」
2. HWC 回覆每個 layer 的 composition type
3. **`presentDisplay()`** — 真正送出

常見的 composition type：

| Type | 意義 |
|---|---|
| `DEVICE` | 由顯示硬體的 overlay engine 直接處理，SF 不碰 |
| `CLIENT` | HWC 做不到，退回讓 SF 用 GPU 畫進一張 framebuffer target |
| `SOLID_COLOR` | 純色，硬體直接填 |
| `CURSOR` | 游標，可獨立低延遲更新 |
| `DISPLAY_DECORATION` | 圓角、打孔等裝飾層（Android 13 起） |

### 4.2 為什麼要在意這件事

**Device composition** 的路徑是：display controller 直接讀取各個 layer 的 buffer，在掃描輸出時做疊合。GPU 完全不參與，記憶體頻寬用量最小，功耗最低。

**Client composition** 的路徑是：SF 用 `RenderEngine`（Android 12/13 起預設 `SkiaGLRenderEngine`，較早版本是 `GLESRenderEngine`）把需要 fallback 的 layer 用 GPU 畫進一張暫存 buffer，再把這張 buffer 交給 HWC。

代價包含：

- 喚醒 GPU（可能觸發升頻）
- 多一輪 read + write 的記憶體頻寬
- 多一塊 framebuffer target 的記憶體
- SF 自己的 CPU 時間也拉長，壓縮合成的時間預算

在功耗敏感的裝置上，同一個畫面走 device 或 client composition，電流差距是可以直接量出來的。

### 4.3 什麼情況會 fallback 到 GPU

Overlay engine 是固定功能硬體，能力有邊界。常見的觸發原因：

**Layer 數量超過硬體 overlay plane 上限。** 這是最常見的一種。上限依 SoC 與 display pipeline 設計而異，需要查該平台的 display 規格；一旦超過，多出來的 layer 就會被合併成 client composition。

**不支援的變換組合。** 旋轉、縮放、鏡射，或這些變換的組合，硬體支援程度各不相同。

**不支援的 pixel format 或 color space。** 特別是 HDR 內容需要 tone mapping 時。

**特殊的 blending 需求。** 複雜的 alpha 混合、backdrop blur 這類效果。

**Protected content 的路徑限制。** DRM 內容的 secure path 可能限制可用的 plane。

### 4.4 平板場景為什麼特別容易踩到

大螢幕 Android 的使用模式和手機不同，而 layer 數量會累加得很快：

```
分割畫面 + 浮動視窗的 layer 組成（示意）

  App A 主視窗
  App A 的 SurfaceView（影片播放）
  分割線 divider
  App B 主視窗
  浮動視窗（PiP 或 bubble）
  浮動視窗的陰影 layer
  Status bar
  Navigation bar
  IME 視窗
  Rounded corner overlay × 4
```

在手機上，全螢幕單一 App 的情境通常只有 3~5 個 layer，overlay plane 綽綽有餘。但平板的多工情境很容易一口氣衝上十幾層——這時候超過硬體上限、掉到 GPU composition 幾乎是必然的。

「開分割畫面之後耗電變高」這個 bug，多數情況下的根因就是這個。

---

## 五、除錯手段

### 5.1 dumpsys：第一站

```bash
adb shell dumpsys SurfaceFlinger
```

輸出很長，但幾個區塊值得優先看：

- **Layer 列表與 Z-order**：確認實際有幾層、哪些是意料之外冒出來的
- **每個 layer 的 composition type**：`DEVICE` 還是 `CLIENT`，直接對應上一節的分析
- **Display 資訊**：解析度、目前 refresh rate、支援的 display mode
- **HWC dump**：vendor 提供的 HWC 內部狀態，通常包含 plane 配置

只列 layer 名稱：

```bash
adb shell dumpsys SurfaceFlinger --list
```

單一 layer 的 frame latency：

```bash
adb shell dumpsys SurfaceFlinger --latency <layer name>
```

輸出是三欄時間戳（desired present / actual present / frame ready），可以算出實際的 frame interval 分布。

### 5.2 TimeStats：統計式的 jank 資料

Android 10 起 SF 內建 TimeStats，適合做長時間統計而非單點觀察：

```bash
# 啟用並清空
adb shell dumpsys SurfaceFlinger --timestats -enable -clear

# ...操作待測情境...

# 取出報告
adb shell dumpsys SurfaceFlinger --timestats -dump -maxlayers 10
```

裡面有 frame duration 的 histogram、missed frame 計數、present-to-present 分布。做壓測或迴歸比較時比逐幀 trace 好用得多。

### 5.3 Perfetto：看清楚是誰的問題

這是判斷「App 端還是合成端」最有效的工具。抓 trace 時務必包含 `gfx`、`view`、`sched` 這些 category，然後在 UI 上看這幾條 track：

- **`surfaceflinger` process**：`onMessageInvalidate` / `composite` 這些 slice 的長度，就是 SF 每幀的 CPU 開銷。突然變長通常伴隨 client composition。
- **App 的 UI thread 與 RenderThread**：`Choreographer#doFrame`、`DrawFrames` 的長度。
- **`VSYNC-app` / `VSYNC-sf`**：節奏是否穩定、有沒有 refresh rate 切換。
- **Frame Timeline（Android 12 起）**：`Expected Timeline` 與 `Actual Timeline` 兩條 track 會直接標出 jank，並且**分類歸因**——是 `AppDeadlineMissed` 還是 `SurfaceFlingerCpuDeadlineMissed`。這個分類省下大量猜測時間。

判讀原則很簡單：

| 現象 | 指向 |
|---|---|
| App RenderThread 超時、SF 正常 | App 端繪製問題 |
| App 正常、SF slice 明顯變長 | 合成端問題，先查 composition type |
| 兩邊都正常但仍掉幀 | 看 `sched` track，可能是 CPU 排程 / 大核搶不到 |
| Frame interval 週期性跳動 | 可能是 refresh rate 切換或 buffer 數不足 |

### 5.4 Winscope / Layer Trace

需要逐幀檢視 layer 樹的變化（例如視窗轉場動畫出現異常）時，可以錄製 layer trace 並用 Winscope 檢視。這在追「動畫過程中某一幀位置錯了」這類問題時幾乎是唯一有效的手段。具體開啟方式在不同 Android 版本略有差異，建議查對應版本的 developer 文件或直接用 Developer Options 裡的 trace 選項。

### 5.5 一個實務檢查順序

遇到「畫面卡 / 耗電高」的 bug report，我的順序是：

1. `dumpsys SurfaceFlinger` 看 layer 數與 composition type → 先排除 GPU composition fallback
2. 如果有 fallback，找出是哪個 layer 造成的，往上追是哪個元件建的
3. 抓 Perfetto，用 Frame Timeline 的 jank 分類決定往 App 端還是 SF 端查
4. 用 TimeStats 做修改前後的量化比較，避免「感覺好像順一點」這種結論

---

## 六、小結

SurfaceFlinger 的角色可以壓縮成三件事：

1. **收集 buffer** — 透過 BufferQueue / BLAST transaction 從各個 producer 取得畫面內容
2. **對齊節奏** — 以 VSYNC 模型決定何時繪製、何時合成
3. **選擇路徑** — 透過 HWC 盡可能走 device composition，做不到才 fallback 到 GPU

而第 3 點是最值得系統整合工程師關注的。它不會產生 crash，不會出現在任何 log 的 error level，只會安靜地讓電流上升、讓 frame time 逼近預算上限。要看見它，只能主動去 `dumpsys` 裡確認 composition type。

大螢幕與多工情境會系統性地放大這個問題——這也是為什麼手機平台調好的參數，搬到平板上未必成立。

---

## 延伸閱讀方向

- AOSP 官方文件的 Graphics 章節（BufferQueue、Hardware Composer、VSYNC 相關頁面）
- `frameworks/native/services/surfaceflinger/` 的原始碼，特別是 `SurfaceFlinger.cpp` 的 `composite()` 路徑與 `CompositionEngine`
- `hardware/interfaces/graphics/composer/` 的 HAL 介面定義
- Perfetto 官方的 Android frame timeline 使用說明
- 各 SoC vendor 的 display pipeline 規格文件——overlay plane 數量與能力邊界只能從這裡確認
