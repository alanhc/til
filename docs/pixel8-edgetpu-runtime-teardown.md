# 把 Pixel 8 的 TPU 從一支 shell binary 開機：libedgetpu_util.so 拆解

[上一篇 benchmark](./pixel8-cpu-gpu-npu-benchmark.md) 的結尾我下了一個更正：Tensor G3 上其實存在一條非 TFLite 的 TPU 路徑——`/vendor/lib64/libedgetpu_util.so` 導出一整套 C ABI。但那次我只讀了符號表就收手，留了一句「非 TFLite 的 TPU 路徑是存在的」。

這篇把那條路實際走了一遍。結論比我當初想的更強：**這支函式庫不是 NNAPI 的替身，它就是整個 Edge TPU runtime**。我用一支普通的 command-line binary 把 TPU 開機、載入韌體，全程沒碰 NNAPI、沒碰 binder、沒碰任何 HAL 行程。

先講一個貫穿全文的前提，因為它決定了每個「成功」要怎麼讀：**這台 `AOSP_on_shiba` 的 `adb shell` 是 root、而且在 `su` domain**（userdebug build）。所以底下每一個「跑起來了」都是 root 的結果。它證明的是這套 API 完整且能動，**不是**證明 App 搆得到——App 搆不搆得到是另一件事，我用第四節那張表單獨回答。

環境：shiba（Pixel 8，Tensor G3，晶片代號 `rio`，韌體 `zum_tpu_20241118.0.0`），SELinux enforcing。靜態分析用 binutils 的 aarch64 工具，harness 用 NDK r29 對 API 35 編。

---

## 一、它的形狀：一支函式庫，三套 ABI

第一個意外在 `DT_NEEDED`。對一支要摸到硬體加速器的函式庫來說，它的相依短得離譜：

```bash
$ readelf -dW libedgetpu_util.so | grep NEEDED
libdl.so   libm.so   liblog.so   libc.so
```

沒有 binder、沒有 AIDL stub、連 `libc++` 都沒有（C++ runtime 靜態連進去了）。它靠 `open`／`ioctl`／`mmap` 自己摸 `/dev/edgetpu`。

256 個定義出來的動態符號**全部是 C**，一個 mangled name 都沒有。而它們乾淨地分成三個彼此無關的家族——注意這裡：**上一篇我算成 199 + 12 = 少算了一整組**：

| 家族 | 符號數 | 角色 | 裝置上的使用者 |
|---|---:|---|---|
| `DarwinnApi2_*` | 199 | device／buffer／graph／request／wake lock | 9 支 Pixel 相機 HAL 函式庫 |
| `DarwinnDelegate_*` | 12 | 進入點——建立與釋放 device | 同上那 9 支 |
| `thr*` | 40 | graph／SQ-container 的 vendor plugin ABI | **無** |
| linker & misc | 5 | `__start`／`__stop` section marker | — |

兩件事值得停下來看。

第一，生產環境真正的使用者**不是 NNAPI HAL，是相機**。`grep` 遍整台裝置，呼叫 `DarwinnDelegate_CreateVirtualDevice` 的是 `/apex/com.google.pixel.camera.hal/lib64/` 底下 9 支 ML pipeline——`libgcam_frsdk`、`libgoog_mlpipe`、`libgoog_catpipe`、`libroi_tracking` 等等。這是很強的證據：這套 API 才是快路，NNAPI 反而是繞路。

第二，`thr*` 這組正好相反：它是一套完整、自洽的 API（`thrGraphCreate`、`thrLoadSqContainer`、`thrInvocationContextInvokeOnce`……），但**這個 build 上沒有任何東西連結它**。其中兩個函式是純常數回傳，剛好把它的身分供出來：

```
thrGetVendorId()          → "sb_pixel"
thrGetVendorApiVersion()  → "0.6.0"
```

一套帶版本號的 vendor plugin 契約，出貨了但在 G3 上未被使用。

---

## 二、沒有 header，就從反組譯讀簽名

沒有標頭檔，但進入點小到可以直接讀。版本 getter 五條指令就把整個契約交代完：

```
DarwinnApi2_GetVersionInfo:
    cbz  x0, .skip
    mov  w8, #0x2c        // 44
    str  w8, [x0]         // *minor = 44
.skip:
    mov  w0, #0x2         // return major = 2
    ret
```

讀成 `int GetVersionInfo(uint32_t *minor)`，回傳 2、寫入 44 → **API 2.44**。實機跑一次，印的正是 `2.44`，跟反組譯完全吻合。

物件方法更薄——三條指令，從 offset 0 載入 vtable 指標，再 tail-call 進固定的 slot。每個 `DarwinnApi2_*` accessor 都只是 C++ vtable 的一層 C 皮：

```
DarwinnApi2_VirtualDevice_NumChips:
    ldr  x8, [x0]         // vtable
    ldr  x1, [x8, #16]    // slot 2
    br   x1
```

這個 vtable 佈局也把整個類別的形狀畫出來了：+16 `NumChips`、+32 `ChipIds`、+208 `GetBufferFactory`、+224 `InError`、+240 `GetMasterDeviceFd`、+256 `GetViiVersion`。

這也解釋了我踩到的頭兩個 crash：

1. `GetMasterDeviceFd` 是 `(vd, int *out)`，不是 `(vd)`。只給一個參數，它會把 fd 寫進 `x1` 裡剛好殘留的垃圾位址。
2. 更關鍵：`DarwinnDelegate_CreateVirtualDevice` **根本不回傳 `VirtualDevice*`**。它回一個 `EdgeTpuDevice` handle，要再經 `EdgeTpuDevice_GetVirtualDevice`（一次雙重解參考）才拿得到真正的 `VirtualDevice*`。把 handle 直接丟給 `DarwinnApi2_*` 就是 segfault。

---

## 三、把 TPU 開起來

指標修對之後，整條 bring-up 是六個呼叫：`GetDefaultDeviceSpec` 填出 spec → `CreateVirtualDevice` 拿 handle → `EdgeTpuDevice_GetVirtualDevice` 取出 device。用 NDK r29 編、推到 `/data/local/tmp`、以 root 執行：

```
DarwinnDelegate API   : 1.7
DarwinnApi2 API       : 2.44
DarwinnApi2 BuildInfo : 697800475
thrGetVendorId        : sb_pixel

CreateVirtualDevice   → status=0  dev=0xb400006ecf67e2d0
  EdgeTpuDevice       → VirtualDevice=0xb400006e4f680e90
  EventManager        = 0xb400006e9f682410
  NumChips            = 1
  InError             = 0
  GetMasterDeviceFd   → st=0 fd=4
  GetViiVersion       → st=0 v=2
  ChipIds             → n=1 ids=[10000]
  BufferFactory       = 0xb400006f4f67ed20
  fd 4 → /dev/edgetpu-soc
  VirtualDevice_Free  done
```

最後那行 `readlink(/proc/self/fd/4)` 是鐵證：這個行程手上握著的就是那顆加速器的裝置節點本身。

而 kernel driver 也同步這樣說：

```
I edgetpu rio: Powering up
I edgetpu rio: R52 boot stage: 0
I edgetpu rio: loaded prod firmware (1.0 697800475)
I Darwinn  : Firmware Build Label: zum_tpu_20241118.0.0
I edgetpu rio: Powering down
```

`GetBuildInfo` 回的那個 `697800475`，就是 driver 剛載入的韌體版本號——API 回報的正是硬體當下的狀態。

---

## 四、哪一道牆才是真的擋住 App 的那道

root 證明 API 能動，但對「App 搆不搆得到」一句話都沒說。候選的關卡有兩道——Unix 權限（DAC）與 SELinux（MAC）——我用同一支 binary、一次只改一個變數把它們分開驗：先降到 app uid 但**留在 `su` domain**（只測 DAC），再保持 uid 0 但透過寫入 `/proc/self/attr/current` 轉成 `untrusted_app` domain（只測 MAC）。

| 條件 | `open()` 節點 | `dlopen()` 函式庫 | device bring-up |
|---|---|---|---|
| uid 0 · `su`（基準） | OK | OK | status 0, fd 4 |
| uid 10999 · `su`（只有 DAC） | EACCES | OK | status 13 |
| uid 0 · `untrusted_app`（只有 MAC） | EACCES | OK | status 13 |

兩道關卡**各自都足以擋住**。注意中間那欄：`dlopen` 永遠成功——那三支 public library 帶的是 `same_process_hal_file` 這個 SELinux 標籤，就是為了讓 App 行程 map 得進來。**載入 runtime 從來不是問題，卡的只有裝置節點**（`/dev/edgetpu-soc` 是 `system:system 0660`，SELinux type `edgetpu_device`）。

DAC 失敗那一格印出的訊息，是整個拆解裡最有價值的一行：

```
INTERNAL: Failed to open device fd from EdgeTPU service.
errno=Invalid argument. If you are running a test tool, this
may be a permission error. Please follow this link for
recommended fix: go/darwinn-app-permissions
```

「from EdgeTPU service」——直接 open 不是它唯一嘗試的路。這支函式庫沒有任何 binder 符號，不可能自己跟 service 講話；它是在**執行期 `dlopen` 了 `libedgetpu_client.google.so`**（binder client）去向 service 要一個 fd。這正好接上[上一篇更正](./pixel8-cpu-gpu-npu-benchmark.md)查到的那條路：**service 那端以套件名稱＋簽章為鍵的白名單**。

於是兩篇合起來，完整的圖是這樣：

- **直接路徑**（`ioctl`/`mmap` 自己開節點）：被 DAC＋MAC 擋住，只有 `system` uid＋HAL domain 的行程走得通——相機就是這樣走的。
- **服務 fallback 路徑**（`dlopen` binder client，向 service 要 fd）：被 vendor 白名單擋住，這才是留給 App 的那條，而且原廠裝置上它是關著的。

補一個當初我差點搞錯的細節：這台是 userdebug、`adb shell` 是 root，所以我能**直接 open** 節點。上一篇在原廠裝置上是 uid 2000 的 shell 走**服務路徑**被 `GetEdgeTpuFd` 的 `uid % 100000` 區間檢查擋掉——兩者不衝突，是兩條不同的 code path 各有各的鎖。

---

## 五、graph 從哪來：編譯器與 DGC0 容器格式

`RegisterGraph` 要的是編譯好的 Darwinn graph，餵不進 `.tflite`。編譯器在裝置上確實存在——`libedgetpu_tflite_compiler.so`，60 MB，五個 C 函式——但它帶的是 `vendor_file` 標籤（不是 `same_process_hal_file`），所以**沒有 App map 得進來**，它唯一的使用者是 `vendor.google.edgetpu_vendor_service@1.0-service`。

跟 runtime 不同，編譯器是**帶著 assertion 出貨**的，於是它把參數名連同 Google 自己的錯字一起交了出來：

```
// 每個 null-check 分支上的 assertion 字串
"seriazlied_options != nullptr"   // x2 [原文如此]
"out_fd != nullptr"               // x5
"out_bytes != nullptr"            // x6
"out_status_string != nullptr"    // x7
```

值得記一筆：**編譯輸出是透過 file descriptor 回傳的，不是 heap buffer**。拿 MobileNet v1 配一個空的 options proto 去餵，它跑到 `Couldn't read from cache. Going to re-compile model` 才乾淨地 `exit(1)`；缺的欄位名字在 binary 別處：`Chip id cannot be empty.`。

同一批字串指向 `/data/vendor/edgetpu/cache/`——這台上那裡**已經躺著 10 個先前 NNAPI 與相機跑出來的編譯容器**。它們的佈局一眼可讀（`xxd` 前 64 bytes）：

```
00000000: 3500 0000 0a14 7a75 6d5f 7470 755f 3230  5.....zum_tpu_20
00000010: 3234 3131 3138 2e30 2e30 1213 3334 3430  241118.0.0..3440
00000020: 3633 3037 3032 3939 3038 3433 3233 3618  630702990843236.
00000030: 0128 80e0 2b38 5440 01d0 0f00 0044 4743  .(..+8T@.....DGC
00000040: 3000 0000                                 0...
```

`0x35` 是開頭那段 protobuf header 的長度，內容是韌體 build label 加 model id；接著一個 uint32，然後在 +0x3d 出現 `DGC0` magic，後面才是 payload。容器裡嵌的字串直接把模型供出來：`contours.tflite`、`landmark_detector`——一個來自相機管線的臉部 landmark graph，**未加密**躺在磁碟上。

---

## 六、走到哪裡停下來

把其中一個容器註冊進去——沒成功，但失敗的方式很有訊息量。

`RegisterGraphByBuffer` **不是** `(vd, buffer, size, ...)`。讀 prologue 就知道：`x1`、`x2` 被搬進之後會被當成 refcounted 物件解參考的指標暫存器，而 `w3`、`w4` 才是當 32-bit int 處理。我把長度（716941）塞在第二個指標的位置，於是它在清理路徑上、一個 atomic refcount 遞減裡爆掉。

所以容器得先用 `BufferFactory` 包成一個 `DarwinnApi2` 的 `Buffer` 物件才行。往下這條鏈——`AllocateBuffer` → `CopyFrom` → `RegisterGraph` → `CreateInferenceRequest` → `AddInput`／`AddOutput` → `Submit` → `Wait`——是搆得到的，但 runtime 出貨時把 assertion 都編掉了，所以每一個簽名都得用一次「crash 了再讀反組譯」的循環去換。工作就停在這裡。

---

## 收尾：這改變了什麼

回頭看，最重要的一句修正是關於「這支函式庫到底是什麼」。它**不是** NNAPI stack 的另一個入口。相機 HAL 的證據說得很白：9 支生產函式庫跳過 NNAPI，直接呼叫 `DarwinnDelegate_CreateVirtualDevice`。真正把 App 擋在外面的，是一個 owner 設錯的字元裝置——不是缺一套 API。

三個要對前文微調的點：

- 256 個符號不是 199＋12，中間漏了一整組 40 個的 `thr*`（外加 5 個 linker 符號）。
- 「client library 轉呼叫到特權服務」這句成立，而且關係還反過來了：是 `libedgetpu_util` 在 fallback 時 `dlopen` 了**它**去要 fd。
- 「非 TFLite 路徑存在」不只成立，而且比當初講的更強——它能從一支 shell binary 把晶片開機。

還有一個 build 特定的事實：`edgetpu_app_service` 在 `AOSP_on_shiba` 上根本不存在（上一篇引的那段 allowlist 錯誤是原廠裝置的行為）。

---

> 方法論的坑，留給後來的人：這台 `adb shell` 是 uid 0、在 `su` domain。凡是「它動了」都是 root 結果，只證明 API 完整可用，**不**證明 App 搆得到——那個問題由第四節那張表回答，答案是搆不到。要把 MAC 和 DAC 分開，訣竅是從 `su` 寫 `/proc/self/attr/current` 做 dyntransition，同時保持 uid 0。所有裝置端的測試 binary 與推上去的模型都在跑完後刪除；那個 model cache 只讀、沒寫。
