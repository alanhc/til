# 三個子系統，同一套心法：DRM、V4L2、ASoC 的共通設計模式

## 為什麼放在一起看

顯示 (DRM/KMS)、視訊 (V4L2 + Media Controller)、音訊 (ALSA/ASoC) 表面上是三套毫不相干的 API，但它們解的是同一類問題：**一條由多顆獨立 IP 串起來的硬體管線，要讓 userspace 能列舉、協商、設定、餵資料，而且 uAPI 一旦公開就不能破壞**。三者各自演化了十幾年，卻收斂到高度相似的手法。把這些同構的地方整理出來，換子系統時可以少繞不少路。

以下內容皆對應 mainline 概念，未涉及任何特定廠商的內部實作。

## 對照表

| 面向 | DRM/KMS | V4L2 / Media Controller | ASoC |
|---|---|---|---|
| 拓樸描述 | plane → CRTC → encoder → connector | entity + pad + link（`/dev/mediaX`） | DAPM widget + route、DAI link |
| 泛型控制 | `drm_property`（atomic blob） | `v4l2_ctrl`（`V4L2_CID_*`） | `snd_kcontrol`（amixer） |
| 能力協商 | connector mode list、`atomic_check` | `TRY_FMT` / subdev pad format 沿 pipeline 傳播 | `hw_params` 求 rate/format/channels 交集 |
| 驗證與套用分離 | `atomic_check` / `atomic_commit` | `VIDIOC_TRY_FMT` / `S_FMT`、link validate | constraint + `hw_params` / `trigger` |
| 緩衝區模型 | GEM + PRIME（dma-buf） | videobuf2 + `QBUF`/`DQBUF` | ring buffer + `hw_ptr`/`appl_ptr` |
| 驅動組裝 | component + `drm_of` / of_graph | `v4l2_async` notifier / of_graph | `snd_soc_register_card` + `-EPROBE_DEFER` |

## 模式一：拓樸是「節點 + 連線」，而非寫死的管線

三者都拒絕把 pipeline 寫死在驅動裡，改成把硬體拆成可獨立描述的節點，再讓 userspace 查詢與改接線。DRM 的 KMS object 每個都有 ID 與一組 property；Media Controller 直接把 entity/pad/link 這張圖攤給 userspace，還能用 `MEDIA_IOC_SETUP_LINK` 改連線；DAPM 的 widget/route 更進一步——它用這張圖做**動態電源管理**，沒有被使用中的 path 走到的 widget 就關電。

同一個抽象、三種用途：DRM 拿它做 atomic 狀態機，V4L2 拿它做 format 傳播，ASoC 拿它做 power gating。

## 模式二：先 try，再 commit

「會失敗的驗證」與「不能失敗的套用」必須分開，否則無法 rollback。這在三邊長得幾乎一樣：

- DRM atomic：`atomic_check()` 可以回傳 `-EINVAL`、且不得有副作用；一旦進到 `atomic_commit()` 就只准成功。
- V4L2：`VIDIOC_TRY_FMT` 與 `VIDIOC_S_FMT` 走同一段邏輯，差別只在寫不寫回硬體狀態；串流啟動前還有一次 link validation。
- ASoC：constraint 與 `hw_params` 負責談妥並配置，`trigger()` 在 atomic context 裡執行，設計上不預期失敗。

Bring-up 時的常見誤區，就是把驗證邏輯塞進 commit/trigger 路徑，結果失敗時狀態機半生不熟。

## 模式三：能力是集合，協商就是求交集

沒有一邊是「userspace 指定什麼就給什麼」。connector 從 EDID 列舉 mode list；subdev 每個 pad 各有支援的 mbus code 與解析度，`S_FMT` 的結果要沿著 pipeline 傳播並保持一致；ASoC 則是把 CPU DAI、codec DAI、platform 三方的 rate/format/channel 能力取交集（`snd_soc_runtime_calc_hw`），談不出交集就是 `-EINVAL`。

所以「設不進去」十次有八次不是 bug，是交集為空。先看各節點各自宣告了什麼，比盯著失敗的那個 ioctl 有用。

## 模式四：一張「卡」由多個 driver 拼出來

顯示控制器、DSI bridge、panel 是三個 driver；sensor、CSI receiver、ISP 是三個 driver；CPU DAI、codec、amplifier 也是三個。三邊都靠 DT 的 of_graph 描述連接關係，都需要延遲綁定機制等到成員到齊：DRM 用 component framework，V4L2 用 async notifier，ASoC 直接讓 `snd_soc_register_card()` 回 `-EPROBE_DEFER`。

**這也是三者最集中的 bring-up 失敗來源**：probe 順序不對、of_graph endpoint 沒對上、某個成員永遠沒出現，於是整張卡靜悄悄地不註冊。看 `/sys/kernel/debug/devices_deferred` 通常比 dmesg 快。

## 不對稱的地方

不要把類比推太遠，有兩個真正的差異：

**緩衝區交換 vs. 環形緩衝。** DRM 與 V4L2 共用 dma-buf 作為通貨，buffer 以 fd 形式在子系統間傳遞，`V4L2_MEMORY_DMABUF` 加上 PRIME import 就是零拷貝 camera-to-display 的標準做法。ALSA 走的是另一條路——音訊 buffer 小、速率固定，用單一 ring buffer 加上 `hw_ptr`/`appl_ptr` 追蹤即可，沒有 buffer 交換的概念。想在音訊路徑上套 dma-buf 思維會踩空。

**同步原語。** DRM 有成熟的 `dma-fence`（explicit out-fence、隱式 `dma_resv`）；V4L2 至今仍以阻塞式 `DQBUF` 加 timestamp 為主，fence 支援長年停留在提案階段；ASoC 則根本不需要 fence，時間基準來自 sample clock，period interrupt 就是節拍器。

## 除錯入口速查

- **DRM**：`modetest`、`drm_info`、`/sys/kernel/debug/dri/*/state`（直接 dump atomic state）
- **V4L2**：`media-ctl -p` 看圖、`v4l2-ctl --all` 看 format 與 control、`v4l2-compliance` 驗 uAPI
- **ASoC**：`amixer contents`、`/sys/kernel/debug/asoc/*/dapm/*`（看每個 widget 的 power 狀態）
- **共通**：`/sys/kernel/debug/devices_deferred`、`dyndbg` 打開對應檔案的 debug print

## 延伸閱讀

- `Documentation/gpu/drm-kms.rst`、`drivers/gpu/drm/drm_atomic_helper.c`
- `Documentation/userspace-api/media/`、`drivers/media/common/videobuf2/`
- `Documentation/sound/soc/`、`sound/soc/soc-pcm.c`、`sound/soc/soc-dapm.c`
