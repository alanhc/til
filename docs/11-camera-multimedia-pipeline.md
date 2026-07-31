# Camera 與多媒體 Pipeline 實戰:Chip Vendor 視角

> 系列文章之十一。總覽請見《Chip Vendor 視角的 Android Build System》。

Camera、codec、顯示是多媒體 SoC 的核心賣點,也是 BSP 中最複雜、xTS fail 最集中的領域。本文把三條 pipeline(相機、編解碼、顯示)與它們共用的地基(graphics buffer)講清楚。

---

## 一、共用地基:Graphics Buffer 的一生

多媒體的本質是「buffer 在硬體 IP 之間流轉」:ISP 產生 → GPU 處理 → codec 編碼 → DPU 顯示。關鍵抽象:

- **Gralloc HAL(IAllocator/IMapper)**:分配 graphics buffer。你要實作 usage flags 的仲裁——同一塊 buffer 要被 camera 寫、GPU 讀、encoder 讀,格式與對齊要同時滿足所有 IP(常見私有格式 + UBWC/AFBC 壓縮)。
- **dmabuf / dmabuf heaps**:kernel 側的 buffer 共享機制(取代舊的 ION,Android 12 起強制遷移)。你的 heap 實作決定分配延遲與記憶體碎片行為。
- **SurfaceFlinger / HWC(Hardware Composer HAL)**:合成。HWC 決定哪些 layer 走 DPU overlay(省電)、哪些丟給 GPU 合成(萬能但耗電)。**overlay 策略是顯示功耗的第一槓桿**。
- **同步**:sync fence(acquire/release fence)貫穿全部——fence 沒處理對,症狀是畫面撕裂、卡死或 job 亂序,而且極難查。

---

## 二、Camera pipeline

### 2.1 架構

```
App (Camera2 API / CameraX)
 └─ camera framework(CameraService)
     └─ Camera HAL(ICameraProvider/ICameraDevice,AIDL)
         └─ 你的 camera stack:3A、ISP driver、sensor driver、pipeline 管理
             └─ hardware:sensor → CSI/MIPI → ISP(多級)→ memory
```

HAL3 的模型是 **per-frame control**:framework 每一幀送一個 capture request(全套參數:曝光、對焦、白平衡⋯⋯),HAL 回 result metadata + buffers。你的實作要處理 pipeline depth(in-flight requests)、partial result、多 stream 並發(preview + video + still)。

### 2.2 Chip vendor 的責任區

- **3A(AE/AF/AWB)演算法**:核心 IP,通常是 blob 交付(見 Soong 篇的 prebuilt 做法)。
- **metadata 正確性**:HAL3 定義了數百個 metadata key,`CtsCameraTestCases` 逐一驗證行為——**metadata 是 camera CTS fail 的最大宗**(宣告支援了某能力但行為不符)。
- **能力分級**:`LEGACY/LIMITED/FULL/LEVEL_3` 決定你宣告什麼;宣告越高測得越嚴。多鏡頭(logical multi-camera)、HDR、夜景等進階能力各有對應測項。
- **tuning**:每個 sensor + lens 組合都要調(校準資料進工廠流程,見量產篇);公版提供 tuning 工具鏈給客戶是標配。
- **效能**:啟動時間、shot-to-shot、預覽 fps——與功耗篇的方法論共用(Perfetto + ATRACE 埋點)。

---

## 三、Codec pipeline(Codec2)

### 3.1 架構

```
App (MediaCodec API)
 └─ media framework
     └─ Codec2 HAL(取代舊 OMX,Android 11+ 新 codec 一律 Codec2)
         └─ 你的 codec plugin:V4L2 driver 或私有介面 → HW encoder/decoder
```

你要提供:Codec2 component 實作(對接你的 HW codec driver)、`media_codecs.xml`(宣告支援的 codec/profile/level/性能點)、`media_codecs_performance.xml`(併發與 fps 能力)。

### 3.2 重點與坑

- **宣告與實測一致**:`media_codecs.xml` 宣告的每一項,`CtsMediaTestCases` 都會驗——性能點(如 4K60 併發數)虛報必炸。
- **secure playback(DRM)**:Widevine L1 需要 secure buffer path(TEE + secure memory),buffer 流轉全程不可被 CPU 讀——與 Gralloc、HWC 的 secure 支援全鏈配合。
- **低延遲模式、tunneled playback**:電視/串流場景的加分項,各有 CTS 測項。
- **格式邊界**:奇數解析度、非對齊 stride、動態解析度切換——CTS 最愛考的 edge case,HW 不支援就要 SW fallback 或正確拒絕。

---

## 四、顯示 pipeline

```
SurfaceFlinger
 └─ HWC HAL(IComposer,AIDL)
     └─ DPU driver(DRM/KMS)→ MIPI-DSI/eDP → panel
```

Chip vendor 重點:

- **DRM/KMS driver**:GKI 時代 display driver 是 vendor module,atomic commit 模型。
- **HWC 策略**:layer 能力對帳(格式、旋轉、縮放、HDR)→ 決定 overlay 分配。策略太保守 = GPU 合成耗電;太激進 = 顯示異常。
- **更新率**:LTPO/VRR、幀率切換策略(與 framework 的 frame rate vote 協作)、panel 的 idle 模式——續航的重要槓桿。
- **HDR 與色彩管理**:色彩空間轉換(CSC)在哪一級做、tone mapping、`CtsDisplayTestCases`/`CtsGraphicsTestCases` 相關驗證。
- **Panel bringup**:DT 裡的 timing/porch 參數、DSI 命令序列、亮度曲線(含 DC 調光)——新專案最常見的顯示類工作。

---

## 五、除錯工具速查

```bash
# Camera
adb shell dumpsys media.camera            # HAL 狀態、stream 配置、metadata
adb shell cmd media.camera watch          # per-frame 監看

# Codec
adb shell dumpsys media.player / media.codec
adb logcat -s CCodec Codec2Client         # Codec2 錯誤

# Display / 合成
adb shell dumpsys SurfaceFlinger          # layer 列表、HWC 分配結果(哪層 GPU 哪層 DPU)
adb shell dumpsys gfxinfo <pkg>           # jank 統計

# Buffer / fence:Perfetto 開 gfx、sf、hal tag,看 fence 等待
# kernel 側:/sys/kernel/debug/dri/、dmabuf 統計(/sys/kernel/dmabuf/)
```

xTS 對應(詳見 xTS 篇):`CtsCameraTestCases`、`CtsMediaTestCases`、`CtsDeqpTestCases`(GPU)、CTS-V 的 camera/av sync 手動測項——多媒體是 chip vendor xTS 工作量的最大來源。

---

## 結語

> **多媒體 pipeline 的第一性原理是 buffer 與 fence:誰分配、什麼格式、誰在等誰。** 三條 pipeline(camera、codec、display)各自複雜,但 fail 模式高度共通——宣告與實作不一致(metadata/media_codecs.xml)、buffer 格式協商錯、fence 亂序。把「宣告的每一項都有測試守著」當原則,CTS 就不會在出貨前給你驚喜。
