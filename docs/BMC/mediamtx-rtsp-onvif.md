# MediaMTX / RTSP / ONVIF 筆記

> 三者常被放在一起講，但其實不在同一層。先把分層搞清楚，後面就都好懂。

## 0. 分層關係

```
ONVIF    ← 控制面：探索相機、查詢能力、取得串流 URL、控制 PTZ（SOAP/XML over HTTP）
RTSP     ← 訊令面：DESCRIBE / SETUP / PLAY，協商 codec 與傳輸方式
RTP/RTCP ← 資料面：實際搬運 H.264 / H.265 封包與品質回饋
MediaMTX ← 中介 server / proxy：收進上述串流，再轉出 RTSP / RTMP / HLS / WebRTC / SRT
```

一句話總結：**ONVIF 幫你「找到並問出」串流位址，RTSP 幫你「把串流拉下來」，MediaMTX 幫你「轉發給任何人看」。**

---

## 1. RTSP（Real Time Streaming Protocol）

### 是什麼

IETF 標準（RFC 2326 / RFC 7826，1998 起）。設計理念是「網路上的錄影機遙控器」——它本身**不搬運影像資料**，只負責控制指令：

| Method | 作用 |
|---|---|
| `OPTIONS` | 問 server 支援哪些指令 |
| `DESCRIBE` | 取得 SDP（有哪些 track、什麼 codec） |
| `SETUP` | 協商傳輸方式（UDP / TCP interleaved）與埠號 |
| `PLAY` / `PAUSE` | 開始 / 暫停播放 |
| `TEARDOWN` | 結束 session |

影像本體走 **RTP**，品質回饋走 **RTCP**。

### 為什麼重要

- 幾乎所有 IP camera、NVR、車用與工控攝影機都內建 RTSP server，是監控產業**事實上的共同語言**。
- 延遲可壓到 **100–200 ms** 等級（HLS 通常 2–10 s），即時監看、機器視覺 pipeline 都靠它。
- OpenCV、FFmpeg、GStreamer 全都原生支援，接分析流程幾乎零成本。

### 限制

- **NAT / 防火牆不友善**：RTP over UDP 用動態埠，跨網段常掛掉 → 改用 TCP interleaved（`rtsp_transport=tcp`）。
- **瀏覽器不能直接播**：這正是需要 MediaMTX 這類 gateway 的主因。
- 無標準化的鑑權以外安全機制（RTSPS 支援度參差）。

---

## 2. ONVIF（Open Network Video Interface Forum）

### 是什麼

一套讓不同廠牌 IP camera 有共同介面的產業標準。用 SOAP/XML over HTTP，主要服務：

| 服務 | 用途 |
|---|---|
| Device Service | 裝置資訊、時間、網路設定、使用者管理 |
| Media Service | 列出 profile、取得串流 URL（`GetStreamUri`）、snapshot |
| PTZ Service | 雲台上下左右、變焦、preset |
| Events Service | 移動偵測、IO 觸發等事件訂閱（WS-BaseNotification） |
| Imaging Service | 亮度、對比、白平衡、對焦 |

裝置探索用 **WS-Discovery**：UDP 多播到 `239.255.255.250:3702`，相機回覆自己的 XAddr（例如 `http://192.168.1.64/onvif/device_service`）。

### 常見 Profile

| Profile | 內容 |
|---|---|
| **S** | 基本串流 + PTZ（最常見） |
| **T** | H.265、進階事件、metadata |
| **G** | 錄影與回放 |
| **M** | 分析 metadata（物件偵測結果等） |
| **A / C / D** | 門禁控制相關 |

### 為什麼重要

不同品牌的 RTSP 路徑天差地遠：

```
Hikvision : rtsp://ip:554/Streaming/Channels/101
Dahua     : rtsp://ip:554/cam/realmonitor?channel=1&subtype=0
Axis      : rtsp://ip:554/axis-media/media.amp
```

有 ONVIF 就不必硬記——`GetProfiles()` → `GetStreamUri()` 直接問出來。**做多品牌自動化佈署時，這是關鍵**。

---

## 3. MediaMTX

### 是什麼

Go 寫的**單一 binary**、零外部依賴的即時媒體 server + proxy（前身是 `rtsp-simple-server`）。

**輸入**：RTSP、RTMP、SRT、WebRTC (WHIP)、HLS、UDP/MPEG-TS
**輸出**：RTSP、RTMP、SRT、WebRTC (WHEP)、HLS / LL-HLS

其他功能：

- `sourceOnDemand`：沒人看就不連相機，省頻寬與相機連線數
- 錄影分段（MP4 / fMP4）＋自動清理
- HTTP Control API（動態增刪 path）
- `runOnDemand` / `runOnPublish` 等 hook（可掛 AI 推論）
- Prometheus metrics、pprof
- 多種鑑權（internal / HTTP / JWT）

### 為什麼重要

以前要 `nginx-rtmp + Janus + GStreamer` 才能拼出來的東西，現在一個 binary + 一份 YAML 就搞定。特別適合：

- **CI / 測試環境的假相機**：用影片檔模擬 RTSP source，不用真的擺硬體
- **協定轉換 gateway**：讓瀏覽器（WebRTC）看得到 RTSP 相機
- **邊緣裝置的串流中樞**：ARM binary 只有十幾 MB

---

## 4. 實作：怎麼用

### 4.1 起 server

```bash
# Docker（建議 host network，否則 RTSP/WebRTC 埠會很麻煩）
docker run --rm -it --network=host bluenviron/mediamtx:latest

# 或直接抓 binary，會讀同目錄的 mediamtx.yml
./mediamtx
```

預設埠：

| 服務 | 埠 |
|---|---|
| RTSP | 8554 |
| RTMP | 1935 |
| HLS | 8888 |
| WebRTC | 8889 |
| SRT | 8890 |
| API | 9997 |

### 4.2 代理一台真相機

`mediamtx.yml`：

```yaml
paths:
  cam1:
    source: rtsp://admin:pass@192.168.1.64:554/Streaming/Channels/101
    sourceOnDemand: yes           # 沒 client 就不連線
    sourceOnDemandCloseAfter: 10s
    sourceProtocol: tcp           # 丟包嚴重時改 TCP
    record: yes
    recordPath: ./rec/cam1/%Y-%m-%d_%H-%M-%S
    recordSegmentDuration: 1h
    recordDeleteAfter: 168h       # 保留 7 天
```

播放端：

```
RTSP   : rtsp://<host>:8554/cam1
WebRTC : http://<host>:8889/cam1          ← 瀏覽器直接開，延遲最低
HLS    : http://<host>:8888/cam1/index.m3u8
```

### 4.3 用影片檔模擬一台相機（CI / 壓測神器）

```bash
ffmpeg -re -stream_loop -1 -i sample.mp4 -c copy \
       -f rtsp -rtsp_transport tcp rtsp://localhost:8554/fake_cam
```

或讓 MediaMTX 自己拉起來：

```yaml
paths:
  fake_cam:
    runOnDemand: >
      ffmpeg -re -stream_loop -1 -i /media/sample.mp4 -c copy
      -f rtsp rtsp://localhost:8554/$MTX_PATH
    runOnDemandRestart: yes
```

### 4.4 ONVIF 探索並自動接上

MediaMTX 本身**不做** ONVIF discovery，需另外的工具：

```bash
pip install onvif-zeep wsdiscovery
```

```python
from wsdiscovery.discovery import ThreadedWSDiscovery as WSD
from onvif import ONVIFCamera
import yaml, urllib.parse

# --- Step 1: 區網探索 ---
wsd = WSD(); wsd.start()
services = wsd.searchServices()
addrs = [x for s in services for x in s.getXAddrs()]
wsd.stop()
print(addrs)   # ['http://192.168.1.64:80/onvif/device_service', ...]

# --- Step 2: 問出 RTSP URL ---
paths = {}
for i, xaddr in enumerate(addrs):
    host = urllib.parse.urlparse(xaddr).hostname
    cam = ONVIFCamera(host, 80, 'admin', 'pass')
    media = cam.create_media_service()
    profile = media.GetProfiles()[0]
    uri = media.GetStreamUri({
        'StreamSetup': {'Stream': 'RTP-Unicast',
                        'Transport': {'Protocol': 'RTSP'}},
        'ProfileToken': profile.token
    }).Uri
    # 把帳密塞回 URL
    uri = uri.replace('rtsp://', 'rtsp://admin:pass@')
    paths[f'cam{i}'] = {'source': uri, 'sourceOnDemand': True}

# --- Step 3: 產生 MediaMTX 設定 ---
yaml.safe_dump({'paths': paths}, open('mediamtx.yml', 'w'))
```

PTZ 控制也是同一個 client：

```python
ptz = cam.create_ptz_service()
ptz.ContinuousMove({'ProfileToken': profile.token,
                    'Velocity': {'PanTilt': {'x': 0.5, 'y': 0.0}}})
```

### 4.5 接分析 pipeline

```python
import cv2
cap = cv2.VideoCapture('rtsp://localhost:8554/cam1', cv2.CAP_FFMPEG)
# 若延遲累積，設環境變數：
# OPENCV_FFMPEG_CAPTURE_OPTIONS="rtsp_transport;tcp|buffer_size;1024000"
```

---

## 5. 常見的坑

| 症狀 | 原因 / 解法 |
|---|---|
| ONVIF 回 **401 Unauthorized** | WS-UsernameToken digest 用 UTC 時間簽章，相機時間差 > 5 秒就失敗 → 先 `SetSystemDateAndTime` 或開 NTP |
| WS-Discovery 找不到相機 | 多播跨不了 VLAN / Docker bridge → 用 `--network=host`，或改用 IP 逐台掃 |
| 畫面破圖、馬賽克 | UDP 丟包 → `sourceProtocol: tcp`（FFmpeg 端是 `-rtsp_transport tcp`） |
| 延遲越看越久 | client 端 buffer 累積 → OpenCV 設小 buffer，或改用 WebRTC 播放 |
| 相機連線數爆掉 | 多個 client 各自連相機 → 用 MediaMTX 當單一 source 再 fan-out |
| 瀏覽器 WebRTC 連不上 | 跨網段需要 STUN/TURN → 設 `webrtcICEServers` 與 `webrtcAdditionalHosts` |
| CPU 飆高 | 不小心觸發轉碼 → 確認用 `-c copy`，MediaMTX 預設就是 remux 不轉碼 |
| 解析度太高吃資源 | 改抓 sub-stream（Hikvision `/Streaming/Channels/102`、Dahua `subtype=1`），預覽與分析夠用 |

---

## 6. 快速決策表

| 需求 | 建議 |
|---|---|
| 只是要看單台相機 | VLC 直接開 RTSP URL |
| 要給瀏覽器看 | MediaMTX → WebRTC（延遲 500 ms 以內）或 LL-HLS |
| 多品牌自動接入 | ONVIF discovery + `GetStreamUri` → 產生 MediaMTX config |
| CI 需要穩定的假串流 | MediaMTX + FFmpeg loop 影片檔 |
| 要錄影 + 即時看 | MediaMTX `record: yes`，同時開 RTSP / WebRTC 輸出 |
| 極低延遲跨公網 | SRT 或 WebRTC，別用 RTSP |

---

## 參考資料

- [MediaMTX 官方文件](https://mediamtx.org/docs/publish/rtsp-cameras-and-servers)
- [MediaMTX RTSP-specific features](https://mediamtx.org/docs/features/rtsp-specific-features)
- [MediaMTX GitHub (bluenviron/mediamtx)](https://github.com/bluenviron/mediamtx)
- RFC 7826 — Real-Time Streaming Protocol Version 2.0
- [ONVIF 官方規格](https://www.onvif.org/profiles/)
