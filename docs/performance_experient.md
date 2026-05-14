這張是**瀏覽器版 (m.youtube.com)** 的偵錯面板,跟第一張(原版 YouTube App)很像,但有個關鍵差異值得注意。

**判讀:這張也是軟解,但證據更明確**

關鍵線索:
- **Codecs: `vp09.02.51.10.01.09.16.09.00 (332)`** — 一樣是 VP9 Profile 2 HDR
- **Color: `smpte2084 (PQ) / bt2020`** — HDR10
- **Current Res: 640x360@60** — 又被砍到 360p
- **Viewport / Frames: 411x231*2.63 / 22 dropped of 537** — ⚠️ **掉了 22 frame**

跟第一張對照:

| 項目 | 第一張 (YouTube App) | 第三張 (Chrome m.youtube) |
|---|---|---|
| 環境 | Native App | Chrome 瀏覽器 |
| Codec | VP9 Profile 2 HDR | VP9 Profile 2 HDR |
| 解析度 | 640x360@60 | 640x360@60 |
| 掉幀 | 0 / 47 | **22 / 537 (~4%)** |

**為什麼瀏覽器版掉幀比較明顯?**

Chrome on Android 播 VP9 的路徑:
1. Chrome 走 `MediaCodec` API 試硬解 — Profile 2 不支援 → fallback
2. 走 Chromium 內建的 **libvpx 軟解**(在 renderer process)
3. 加上瀏覽器這層 sandbox + Skia compositor,overhead 比 native ExoPlayer 軟解還重

所以即使解析度被砍到 360p60(理論上 CPU 應付綽綽有餘),瀏覽器這條 pipeline 多了好幾層,加上 tone mapping(HDR→SDR 顯示)如果是 CPU 在做,就會週期性掉幀。

**也就是說,這三張串起來就是一個很完整的 codec capability story:**

1. **第一張 (App + HDR)**:VP9 Profile 2 硬解不支援 → 軟解 360p,native path 還算順(0 掉幀)
2. **第二張 (ReVanced + SDR)**:client 主動避開 HDR,拿 Profile 0 → 硬解 720p60,完美
3. **第三張 (Chrome + HDR)**:Chrome 拿到 Profile 2 → 軟解 360p,但瀏覽器 pipeline overhead 較重,開始掉幀

**順帶觀察 sCPN**

三張的 sCPN(Session Client Playback Nonce)都不同,但 Video ID 都是 `VzoqgEsmUjY`,這代表 YouTube 後端確實依 client 能力動態給不同的 streaming manifest——同一支影片,三個 client 拿到三套不同的 ABR (Adaptive Bitrate) ladder。
這張跟第二張幾乎一模一樣,但有一個非常關鍵的差異。
關鍵差異:[plat] vs [exo2]
項目第二張第四張解碼器標籤[exo2][plat]裝置Google Pixel 10Google Pixel 10Video format334 vp9, 1280x720@60334 vp9, 1280x720@60Dropped frames0 / 46664 / 5127
[plat] 是什麼意思?
[plat] = Platform decoder,也就是直接用 Android 系統原生的 MediaPlayer / MediaCodec 路徑,不經過 ExoPlayer 的封裝。
YouTube App 的播放器架構大致有幾條路徑:

[exo2] — ExoPlayer 2,Google 自家寫的進階播放器,可控性高、支援 DASH/SABR/低延遲
[plat] — Android Platform Media APIs(MediaCodec 直接打),最底層、最原生
也可能看到 [mse](Web 上的 Media Source Extensions)

兩條路徑都是硬解(VP9 Profile 0 在 Tensor G5 上是硬解),但實作不同:

[exo2]:ExoPlayer 自己管 buffer、demux、render scheduling,然後丟給 MediaCodec 解
[plat]:更貼近 OS,讓 Android framework 自己排程

為什麼會切換?
YouTube App 會根據 A/B test、裝置、影片特性動態切換 player 後端。Pixel 10 上,Google 可能在測試讓某些情境走 [plat] 路徑——可能為了:

降低 CPU/記憶體 overhead
利用 Android 14+ 的新 MediaCodec feature(例如 low-latency mode)
統一 Pixel 自家裝置的播放體驗

為什麼 [plat] 反而掉幀 (4 / 5127)?
雖然只有 ~0.08%,但確實比 [exo2] 的 0 / 4666 多。可能原因:

[plat] 路徑對 frame scheduling 控制力較弱,vsync 對齊不如 ExoPlayer 精準
Buffer 管理不如 [exo2] 那麼 aggressive
720p60 在系統有背景負載時,[plat] 的容錯比較差

不過 4 frame in 5127 基本上肉眼看不出來,屬於完全可接受的範圍。
```
Step 1: 開 YouTube debug overlay(看 codec + 解析度)
        ↓
Step 2: adb shell dumpsys media.codec | grep Codec
        ↓ 看到 c2.{vendor}.xxx → 硬解;c2.google/android → 軟解
        ↓
Step 3: adb logcat | grep -i "creating codec"
        ↓ 確認 App 實際 instantiate 哪個 codec
        ↓
Step 4 (BSP-level): cat /proc/mtk_vcodec/... 確認 VDEC 真的在跑
```