# 從 Linux 走進 SoC 內部：RTOS 與 co-processor 韌體的學習地圖

> **這篇寫給誰**：已經懂 Linux / Android 平台，想往 SoC 韌體、BSP、平台系統軟體方向走的人。
>
> **這篇不寫什麼**：不是 RTOS API 教學。網路上那種文章夠多了。
>
> **本文所有內容皆取自公開資料**（官方文件、mainline kernel、開源專案），不涉及任何非公開資訊。文中明確區分「可查證事實」與「我的推論」。

---

## 0. 先講一個反直覺的結論

如果你感興趣的是 SoC 平台軟體（Tegra BSP、Pixel/Tensor 平台、車用 SoC 這一類），而你正打算「把 RTOS 學好」——

**RTOS 本身通常不是能力的重心。**

我把這個判斷的依據攤開來講。業界 SoC 平台系統軟體常見的技能組合大致是：

- embedded / system software 開發經驗
- **出色的 C 程式能力**與 low-level driver 經驗，以及**系統層級的除錯能力**
- ARM 處理器架構
- 電腦系統基礎：**cache、bus、memory controller、DMA**
- 加分：晶片或板級 bring-up 經驗、JTAG 與除錯工具

注意這張清單裡**沒有 RTOS**。有的是 C、driver、debug、ARM 架構、記憶體子系統、bring-up。

> 以下是**我的推論**：直接在 co-processor 上工作的角色（sensor hub、silicon security、穿戴裝置等）通常會明確需要 RTOS 或 bare-metal firmware；而 AP 側的平台／BSP 工作則更接近上面那張清單。也就是說：**RTOS 重不重要，取決於你站在 AP 這一側還是 co-processor 那一側。**

所以正確的問題不是「我該不該學 RTOS」，而是：

> **RTOS 知識在哪個接點上，能讓我對 SoC 平台的理解變得完整？**

答案是三個接點：**AMP 架構下的 co-processor 韌體、AP↔MCU 的 IPC 機制、以及跨核心的 crash 分析**。這篇文章就沿著這三個接點走。

**這也是為什麼 RTOS 對「Linux 出身的人」特別划算**：懂 Linux driver 的人很多，懂 RTOS 的人也很多，但**能同時站在兩邊、講清楚一次 rpmsg 交易從 Linux 的 `virtqueue` 到對面 RTOS 的 ISR 之間發生什麼事的人很少**。

---

## 1. 地形圖：你的手機 SoC 裡藏了幾顆 CPU？

打開任何一顆現代手機或車用 SoC 的 block diagram，Application Processor 上跑的 Linux/Android，只佔這顆晶片的一部分。旁邊躺著好幾顆你平常看不見的核心，**上面跑的幾乎都是 RTOS 或 bare-metal 韌體**：

| 隱藏核心 | 典型工作 | 常見架構 | 為什麼平台工程師會碰到 |
|---|---|---|---|
| **Sensor Hub / ALWAYS-ON MCU** | AP 睡著時持續收 IMU、計步、語音喚醒、環境光 | Cortex-M / RISC-V | 待機功耗、感測器延遲、喚醒路徑 |
| **SCP / Power MCU** | DVFS、電壓調節、溫控、電源狀態機 | Cortex-M | 效能問題、thermal throttling、suspend/resume 失敗 |
| **Modem / Connectivity** | 5G 協定堆疊、Wi-Fi/BT firmware | 專用 DSP + MCU | 連線異常、modem crash、AP 被拖住 |
| **DSP / NPU / APU** | 音訊後處理、AI 模型推論 | 廠商自有 DSP | 推論延遲、firmware 版本相容、記憶體共享 |
| **Display / Camera ISP MCU** | 影像管線的即時控制 | Cortex-M/R | 掉幀、tearing、camera 開啟延遲 |
| **Security MCU / Root of Trust** | 安全開機、金鑰管理、開機量測 | 隔離的專用核心 | secure boot 失敗、attestation、韌體簽章 |

這種「不同核心跑不同 OS」的架構叫 **AMP（Asymmetric Multi-Processing）**，對照的是 Linux SMP（多核跑同一個 kernel）。

**Linux 側的人會在什麼時候撞上它？** 幾乎所有難查的 bug：

- 「待機一晚掉 8% 電」→ 可能是 sensor hub 韌體沒進低功耗，或它一直在敲 AP。
- 「suspend 偶爾回不來」→ 可能卡在某顆 co-processor 的握手。
- 「相機開啟要 2 秒」→ 可能是 ISP MCU 的韌體載入路徑。
- 「dmesg 出現 `remoteproc0: crash detected`」→ 對面掛了，而你要負責解出它為什麼掛。

**這些問題表面上是 Linux 問題，實際上你必須理解對岸。**

---

## 2. RTOS 必要最小集（重點導向的壓縮版）

這一節不教 API，只保留「對岸發生什麼事」你必須知道的部分。每小節結尾附一題**自我檢查**。

### 2.1 Task、優先權、搶佔

Co-processor 上不是 super loop 就是一個 RTOS，把工作切成幾個有優先權的 task。核心規則只有一條：**永遠跑優先權最高的 Ready task，高優先權一 Ready 就立刻搶佔低優先權。**

推論出來的結論很重要：**只要高優先權 task 不阻塞，低優先權 task 一行都跑不到。** RTOS 不追求公平，它追求「重要的事準時做完」。

> **自我檢查**：「Linux 的 CFS 和 RTOS 的 fixed-priority preemptive 有什麼本質差異？為什麼 Linux 有 `SCHED_FIFO`？」
> 好的回答會提到：CFS 目標是吞吐量與公平，RTOS 目標是**最壞情況有上界**；`SCHED_FIFO`/`SCHED_RR` 就是 Linux 為了即時性開的後門，而 `PREEMPT_RT` 是把整個 kernel 改造成可搶佔以壓低最壞延遲。

### 2.2 Priority Inversion —— 最經典的一題

```
低優先權 L  拿到 mutex M
高優先權 H  想要 M，被迫等 L                  ← 合理
中優先權 Mid 醒來，搶佔了 L                    ← 災難：
                                               Mid 沒有鎖，卻讓 H 無限期等待
```

解法是 **Priority Inheritance**：H 卡在 L 的鎖上時，暫時把 L 的優先權提升到 H，讓 L 快點放鎖。另一種是 **Priority Ceiling Protocol**（每把鎖預先標定一個上限優先權，拿到鎖就升上去）。

經典案例是 1997 年 NASA 火星拓荒者號的重複重開機，事後被定位為 priority inversion（VxWorks 的 mutex 沒開啟 inheritance）。

**Linux 側的對應**：`PTHREAD_PRIO_INHERIT` 屬性，以及 kernel 內部的 **rt_mutex**（PI-futex）。這正是 `PREEMPT_RT` 把大量 spinlock 換成 rt_mutex 的原因之一。

> **自我檢查**：「這就是為什麼保護共享資料要用 mutex 而不是 binary semaphore ——為什麼？」
> 答：**mutex 有所有權 (ownership)**，系統知道「現在是誰持有」，才能把持有者的優先權拉上來；semaphore 是純計數器，give 和 take 可以是不同的 task，沒有持有者可以提升。

### 2.3 中斷：latency 從哪裡來

三條鐵律：

1. **ISR 要短**。只做必須立刻做的（清 flag、把 FIFO 讀走），其餘丟給 task。這就是 Linux 的 top-half / bottom-half，RTOS 叫 **deferred interrupt processing**。
2. **ISR 裡不能 block**，也只能呼叫 ISR-safe 的 API。
3. **最壞中斷延遲的主要來源是關中斷的臨界區**。每寫一次 `enter_critical()`，都在推高系統的最壞延遲。

> **自我檢查**：「一個中斷從硬體拉線到你的 handler 執行第一行，中間有哪些延遲來源？」
> 拆解：目前是否關中斷（臨界區）→ 是否有更高優先權的 ISR 在跑 → 硬體的 vector fetch / 暫存器堆疊 → cache miss 造成的取指令延遲 → handler 前置（Linux 的 irq_enter、RTOS 的 context save）。**能把這串講完，代表這條路徑真的懂了。**

### 2.4 記憶體：能靜態就別動態

嵌入式的黃金守則：**開機時配置完，之後不 malloc。** 原因是 heap fragmentation——一個跑三個月的裝置，heap 可能碎到配不出一塊連續空間，然後在半夜掛掉，而你在辦公室永遠重現不出來。

替代方案：靜態配置、固定大小的 memory pool / slab（配置釋放 O(1)、永不碎片化）、以及用 **MPU** 做 thread 間的記憶體隔離。

**Stack overflow** 是這個領域最常見也最難查的 bug：它會安靜地踩爛隔壁 task 的資料，然後在完全無關的地方 crash。所以生產韌體一定會開 stack guard 或填色檢查。

> **自我檢查**：「你怎麼決定一個 task 的 stack 要多大？怎麼驗證？」
> 答：靜態分析最深呼叫鏈 + ISR 巢狀 + 是否用 FPU（Cortex-M 的 lazy stacking 會多推 S0–S31）；驗證用填色法（開機填 pattern，跑完看最高水位）加上 MPU stack guard。

---

## 3. 主戰場：AP ↔ Co-processor 的介面

**這一節是整篇文章的重點，也是我認為投資報酬率最高的部分。** 因為它同時吃 Linux 側和 RTOS 側的知識，而多數人只熟一邊。

### 3.1 一次完整的交易長什麼樣

```
Linux (Cortex-A)                          RTOS (Cortex-M)
─────────────────                         ────────────────
  1. 準備 payload
  2. 寫進 shared memory 的 ring buffer
  3. cache clean（把資料推出去）
  4. memory barrier
  5. 寫 mailbox 暫存器（敲門鈴）  ──IPI──►  6. mailbox ISR 觸發
                                            7. cache invalidate（別讀到舊值）
                                            8. 從 ring 取出，丟進 queue
                                            9. ISR 結束，喚醒 worker task
                                           10. task 處理
                                           11. 寫回結果 + cache clean
  13. mailbox ISR                ◄──IPI──  12. 敲回門鈴
  14. cache invalidate、讀結果、喚醒 waiter
```

**這張圖你要能徒手畫出來並解釋每一步。** 它是理解所有 co-processor 問題的骨架。

### 3.2 Linux 側的三個框架

| 框架 | 負責什麼 | 你該讀的 |
|---|---|---|
| **remoteproc** | co-processor 的生命週期：載入韌體 ELF、配置記憶體、解除 reset、偵測 crash、recovery | `drivers/remoteproc/`、`Documentation/staging/remoteproc.rst` |
| **rpmsg** | 架在 virtio 上的訊息通道，提供類似 socket 的 endpoint 語意 | `drivers/rpmsg/`、`Documentation/staging/rpmsg.rst` |
| **mailbox** | 抽象化各家 SoC 的門鈴硬體 | `drivers/mailbox/` |

搭配的開源標準實作是 **OpenAMP**（對面 RTOS 那一側的 libmetal + open-amp），Zephyr 和 FreeRTOS 都有整合。

**韌體怎麼被載入的？** remoteproc 解析 ELF，找 **resource table**（一個放在韌體 ELF 裡的特殊 section），從中得知：需要多少 carveout 記憶體、vring 放哪、有幾個 virtio device、trace buffer 在哪。然後配置記憶體、複製 segment、解除 reset。

> **自我檢查**：「如果 remoteproc 說載入成功，但對面沒有任何反應，你怎麼查？」
> 一個好的回答會是一串有序的假設：韌體的 link address 和 carveout 的實體位址對不上 → resource table 版本不合 → reset/clock 沒真的解開 → 對面卡在 early init 前（用 trace buffer 或 GPIO toggle 驗證）→ mailbox 中斷沒被路由到。

### 3.3 Cache Coherency：這裡是 bug 的溫床

Cortex-A 和 Cortex-M 通常**不在同一個 coherency domain**。AP 寫進「DDR」的資料可能還躺在 L1/L2 cache 裡，對面的 M 核透過另一條路徑讀 DDR，讀到的是舊值。

處理方式有三種，你要能講出取捨：

1. **軟體維護**：每次寫完 `clean`（把 dirty line 推出去），每次讀前 `invalidate`（丟掉可能過期的 line）。彈性最大，但漏一次就是幽靈 bug。**Invalidate 的粒度必須對齊 cache line，否則會誤刪隔壁的資料**——這是實際會發生的災難。
2. **把共享區域標成 non-cacheable / device memory**：正確但慢，適合小的控制結構（例如 ring 的 head/tail 指標）。常見做法是**混合**：descriptor 用 non-cacheable，大 payload 用 cacheable + 明確維護。
3. **硬體 coherency**（ACE/CCI/CHI 之類的互連）：如果 SoC 支援就最省事，但很多低功耗 MCU 不在裡面。

還有 **memory barrier**：ARM 是 weakly-ordered 記憶體模型，編譯器和 CPU 都會重排。「先寫資料、再更新 tail 指標」如果沒有 barrier，對面可能先看到新的 tail、再看到舊的資料。順序是 `寫 payload → DMB → 更新 index → cache clean → 敲 mailbox`。

> **自我檢查**：這是最核心的一題。「你在 shared memory 上實作一個 SPSC ring buffer，AP 是 producer、MCU 是 consumer，兩邊 cache 不 coherent。請說明你會怎麼處理。」
> 這題值得花時間想透，最能分辨「讀過」和「做過」。

### 3.4 DMA 與 IOMMU/SMMU

Co-processor 常常自己會發 DMA。這帶出兩件事：

- **位址空間不同**：MCU 看到的位址不一定等於 AP 看到的實體位址（可能經過一層 address translation 或 window remap）。Linux 側處理這件事的概念是 `dma_addr_t` 與 `dma_map_*`。
- **SMMU / IOMMU**：現代 SoC 會把 co-processor 放在 SMMU 後面，避免它亂寫 AP 的記憶體。這既是安全機制，也是新的 bug 來源（stream ID 設錯 → SMMU fault）。

> **自我檢查**：「為什麼要把一顆 DSP 放在 SMMU 後面？如果不放會怎樣？」
> 答：DSP 韌體若被攻破或有 bug，可以任意 DMA 到整個系統記憶體，繞過所有 MMU 保護。這是真實的攻擊面（DMA attack）。放在 SMMU 後面就只能存取被授權的區域。

### 3.5 Crash、Watchdog 與 Recovery

Co-processor 掛掉時，你拿到的通常是：

- **remoteproc coredump**：一份記憶體快照，需要配對正確的 `.elf` 才解得出符號。
- **共享記憶體上的 log ring buffer**：對面在死前寫的最後幾行。
- **Watchdog timeout 通知**：只告訴你「它不動了」，不告訴你為什麼。

於是核心技能是：**從一份 dump 回推它卡在哪。** 流程大致是：

1. 用 `readelf`/`nm` 建立符號表，或直接 `gdb-multiarch firmware.elf`。
2. 找到 RTOS 的 thread 清單（每個 RTOS 都有一個全域的 TCB 陣列或 linked list）。
3. 對每個 thread 取出保存的 SP，手動 unwind stack，還原 call stack。
4. 看它停在哪：卡在 semaphore？卡在等 mailbox 回應？stack 已經被踩爛（看到不合理的位址）？deadlock（兩個 thread 互等）？

**Zephyr 有 `CONFIG_DEBUG_COREDUMP` 和一組 `coredump_gdbserver.py` 工具可以做這件事，可以在自己的板子上完整練習一遍。** 這是把「我讀過」變成「我做過」最直接的方式。

> **自我檢查**：「假設某顆 sensor hub 每兩三天會 watchdog reset 一次，log 沒有明顯線索。你怎麼下手？」
> 這是開放式系統題，重點是方法論：先確認是 hang 還是 crash（watchdog 種類）→ 加上 pre-reset 的 dump 路徑 → 檢查是不是特定事件序列觸發（相關性分析）→ 檢查 stack 高水位是否接近上限 → 檢查有沒有偶發的長臨界區或優先權設計問題 → 用 tracing 抓時間軸。

---

## 4. 用 Zephyr 把這些變成「我做過」

前面講的東西，讀懂不難，難的是**真的動手實作過**。Zephyr 是目前最適合拿來當練習載體的 RTOS，原因很具體：

**它和 Linux 同構。** Zephyr 用一模一樣的 **Kconfig** 和 **Devicetree**，有對標 Linux 的 **driver model**，開發流程也是 GitHub PR + maintainer + DCO。授權是 Apache 2.0。這代表兩件事：

1. 你的 Linux 知識**可以直接遷移**，學習成本低。
2. 兩邊可以**對照著學**——例如「Zephyr 的 devicetree 是編譯期展開成常數，Linux 是執行期解析 DTB blob」，這種對比會讓你對兩邊都理解得更深。

（對照組：FreeRTOS 只是一顆 kernel，小而好懂、適合讀完整份原始碼；Apache NuttX 走 POSIX 相容路線；Eclipse ThreadX 是原 Azure RTOS，2023 年底微軟宣布捐給 Eclipse 基金會、以 MIT 授權開源，2024 年完成移轉，強項在安全認證。這三個知道定位即可，練習用 Zephyr 就夠。）

### 4.1 版本選擇（2026-09 現況）

| 版本 | 發布 | EOL | 用途 |
|---|---|---|---|
| **4.4.0** | 2026-04-14 | 2027-04-12 | 最新穩定版，**學習與個人專案用這個** |
| 4.3.0 | 2025-11-14 | 2026-10-15 | 前一個穩定版 |
| **3.7.0 (LTS3)** | 2024-07-26 | 2029-07-27 | 長期支援，產品用 |

Zephyr 約每四個月一個穩定版，下一版 4.5 預計 2026 年 10 月。**注意 3.x → 4.x 之間 API 有不少變動**，網路上兩三年前的教學可能已經編不過，永遠對照你使用版本的官方文件。

### 4.2 環境與第一支程式

```bash
python3 -m venv ~/zephyrproject/.venv
source ~/zephyrproject/.venv/bin/activate
pip install west

west init -m https://github.com/zephyrproject-rtos/zephyr ~/zephyrproject
cd ~/zephyrproject
west update
west zephyr-export
west packages pip --install

west sdk install

west build -p always -b <your_board> samples/basic/blinky
west flash
```

`-p always` 是 pristine build，新手期建議都加——Zephyr 的 CMake cache 在你改 Kconfig 或 devicetree 後常常不會正確重算，會產生「我明明改了為什麼沒效果」的鬼故事。

**沒有板子也能練**：`west build -b native_sim` 把整個 Zephyr 編成一個 Linux 執行檔直接跑，或 `-b qemu_cortex_m3` 跑在 QEMU 上。

### 4.3 三個一定會卡住的地方

**west workspace**：Zephyr 不是一個 repo 是幾十個，`west.yml` 是 manifest。**不要把你的應用寫在 `zephyr/samples/` 裡**，要建獨立的 application 目錄，否則更新版本時會打架。

**Kconfig**：跟 Linux 一樣。你在 `prj.conf` 寫設定，但**最終生效的是 `build/zephyr/.config`**——board 和 SoC 層也有預設值。「我加了 `CONFIG_XXX=y` 但沒生效」九成是 `depends on` 沒滿足，用 `west build -t menuconfig` 查依賴比瞎猜快十倍。

**Devicetree**：硬體配置寫在 `.dts` / overlay，不寫在 C 裡：

```dts
/ {
    aliases { led0 = &green_led; };
    leds {
        compatible = "gpio-leds";
        green_led: led_0 { gpios = <&gpio0 13 GPIO_ACTIVE_LOW>; };
    };
};
```

```c
static const struct gpio_dt_spec led = GPIO_DT_SPEC_GET(DT_ALIAS(led0), gpios);
gpio_pin_configure_dt(&led, GPIO_OUTPUT_ACTIVE);
```

**關鍵差異**：Zephyr 的 devicetree 是**編譯期**處理的，`DT_*` 巨集在建置時就展開成常數，零執行期開銷；Linux 是執行期解析 DTB。除錯時打開 `build/zephyr/zephyr.dts`，那是所有 `.dts`/`.dtsi`/overlay 合併後的最終結果——「為什麼我的 overlay 沒效果」的答案幾乎都在那裡。

---

## 5. 安全側：secure boot 與 Root of Trust

如果你對安全韌體方向有興趣（SoC 的 security firmware、silicon security 這一類），這一節是必修。

**信任鏈的骨架**（各家名字不同，結構一致）：

```
不可變的 ROM code（矽內，無法更新）
   └─ 驗證並載入 → 第一階段 bootloader
        └─ 驗證並載入 → 後續 bootloader / TEE
             └─ 驗證並載入 → kernel / co-processor firmware
```

每一層都在**執行下一層之前驗證它的簽章**。要理解的概念：

- **Root of Trust**：信任的起點，必須是不可變的（ROM）+ 一個燒在 fuse 裡的公鑰雜湊。
- **Measured boot vs. Verified boot**：measured 是「把每一層的雜湊記錄下來」（PCR / attestation 用），verified 是「驗不過就不給跑」。兩者常同時存在。
- **Anti-rollback**：用單調遞增的 fuse counter 防止把韌體降版到有已知漏洞的版本。這是很多人漏掉的一環。
- **金鑰的層級**：ROM 只信一把根公鑰，後面用簽章鏈或 key derivation 展開。

**可以動手練的縮小版**：**MCUboot**。它是 Zephyr 生態的標準 bootloader，slot0/slot1 雙分割、image signing、swap vs. overwrite 升級、以及可選的 anti-rollback counter，全部都有。做一次「簽章的韌體 OTA 升級 + 故意用錯誤的金鑰簽名讓它拒絕開機 + 觸發一次 rollback」，你就把整條信任鏈實際跑過了。

> **和管理平面的連結**：如果你有 BMC / server firmware 背景，這裡有一個值得對照的觀點——**SPDM / MCTP / PLDM 在機箱層級做的事（元件身分認證、韌體量測、安全更新），和 SoC 內部 RoT 對各個 co-processor 做的事，是同一個問題在不同尺度上的展開。** 能把這兩層對起來看，理解會更完整。

---

## 6. Debug 能力：真正的分水嶺

我的判斷是：**平台系統軟體最終拉開差距的不是知識廣度，是除錯的方法論。** 因為平台工程師的日常就是「一個沒人知道原因的問題丟到你桌上」。

值得刻意練習的四件事：

**1. 從 dump 還原現場。** 前面 3.5 節講的流程，在 Zephyr 上完整做一遍。

**2. Tracing 的雙邊視角。** Linux 側用 `ftrace` / `perf` / LTTng，Zephyr 側有 tracing subsystem（可輸出到 SystemView 之類的工具）。**能把兩邊的時間軸對齊**，是解「AP 等 MCU 等了多久」這類問題的唯一辦法。

**3. 硬體層的觀測。** GPIO toggle + 邏輯分析儀是最誠實的量測工具，因為它不改變時序。相對地，`printf` 可能花掉數毫秒且會 block，直接改變你要觀察的現象（Heisenbug）。SEGGER RTT / ARM ITM 是折衷方案。JTAG 則能在系統掛住時 halt 住看現場。

**4. 假設驅動，而不是亂改。** 面對開放問題時，關鍵是：先建立假設、設計能證偽它的實驗、再動手。「我先加 log 看看」和「我懷疑是 cache clean 漏了，所以我先把那塊改成 non-cacheable 看問題是否消失」是完全不同等級的做法。

---

## 7. 可以直接做的四個專案

每一個都能把前面的內容變成實際做過的經驗。按投資報酬率排序：

### 專案一：雙核 AMP 的 IPC 實作 ★★★★★

**硬體**：STM32MP1（Cortex-A7 跑 Linux + Cortex-M4 跑 Zephyr）最標準；NXP i.MX8MP 也可以；預算最低的替代是 Raspberry Pi Pico 的雙 M0+ 自刻 IPC。

**做什麼**：Linux 側用 remoteproc 載入 M4 韌體、用 rpmsg 建立通道；M4 側跑 Zephyr + OpenAMP。實作一個 request/response 協定，量測 round-trip latency 的分布（不只平均，要看 p99）。

**加分**：故意把 cache 維護拿掉，重現資料損毀，然後修好它並解釋原理。

**成果描述**：「在 STM32MP1 上實作 Linux(A7)↔Zephyr(M4) 的 rpmsg 通道，量測並優化 IPC round-trip latency，處理跨 coherency domain 的 cache 維護與 memory ordering。」

### 專案二：跨核心的 crash 分析工具鏈 ★★★★★

**做什麼**：讓 M4 側故意發生四種故障（空指標、stack overflow、deadlock、watchdog hang），從 Linux 側取得 coredump，寫一支腳本自動符號化並印出所有 thread 的 call stack。

**為什麼值得做**：很少人真的做過，而它直接對應「平台工程師日常」，比「會寫 RTOS task」深得多。

### 專案三：MCUboot 完整信任鏈 ★★★★

**做什麼**：在 Zephyr 板子上加 MCUboot，做簽章韌體的 OTA 升級、驗簽失敗的拒絕開機、以及 rollback 保護。畫出完整的信任鏈圖。

**加分**：把它和你已知的另一套信任鏈（AVB、UEFI Secure Boot、或 BMC 的 firmware attestation）做對照分析。

### 專案四：低功耗路徑分析 ★★★

**做什麼**：Zephyr 上開 `CONFIG_PM` / `CONFIG_PM_DEVICE`，用電流錶量待機電流，分析 tickless idle 與 device runtime PM 的實際效果。做一個「感測器持續採樣但 AP 睡著」的情境，量整體功耗。

**為什麼有用**：手機/穿戴 SoC 極度在意功耗，一條真實的電流曲線比任何理論分析都有說服力。

---

## 8. 自我檢核：這 15 題你能答嗎

前 5 題是基礎，中 5 題是分水嶺，後 5 題是加分。

1. Fixed-priority preemptive 和 Linux CFS 的本質差異？`SCHED_FIFO` 存在的理由？
2. Priority inversion 是什麼？為什麼 mutex 能解而 semaphore 不能？
3. 一個中斷的端到端延遲有哪些來源？哪一個通常最大？
4. 為什麼嵌入式要避免執行期 malloc？替代方案？
5. 怎麼決定 task stack 大小？怎麼驗證沒有 overflow？
6. **畫出一次 AP→co-processor 的完整交易，標出 cache 與 barrier 的位置。**
7. **兩顆核心不在同一個 coherency domain，你怎麼設計 shared memory ring buffer？**
8. **remoteproc 的 resource table 裡有什麼？韌體是怎麼被載入並啟動的？**
9. **一顆 co-processor watchdog reset，你手上有 coredump 和它的 elf，說明你的分析步驟。**
10. **為什麼要把 DSP 放在 SMMU 後面？**
11. Zephyr 的 devicetree 和 Linux 的 devicetree，處理時機有什麼根本差異？
12. Secure boot 的信任鏈從哪裡開始？anti-rollback 為什麼必要？
13. Measured boot 和 verified boot 差在哪？各自解決什麼問題？
14. Tickless idle 解決什麼問題？代價是什麼？
15. 你要怎麼把 Linux 側的 ftrace 時間軸和 RTOS 側的 trace 對齊？

**第 6～10 題是這篇文章真正想幫你補的部分。** 如果你能把這五題講得有細節、有取捨、有踩過的坑，你對 co-processor 的理解就和「讀過 RTOS 教科書」完全不同了。

---

## 9. 資源

- **Zephyr**：[docs.zephyrproject.org](https://docs.zephyrproject.org/) —— Getting Started、Kernel Services、Devicetree Guide、Debugging（含 coredump）
- **OpenAMP**：[openampproject.org](https://www.openampproject.org/) —— AMP 通訊的開源標準實作
- **Linux 文件**：`Documentation/staging/remoteproc.rst`、`Documentation/staging/rpmsg.rst`、`Documentation/core-api/dma-api.rst`
- **MCUboot**：[mcuboot.com](https://www.mcuboot.com/)
- **FreeRTOS**：[freertos.org](https://www.freertos.org/) —— 官方免費書《Mastering the FreeRTOS Real Time Kernel》，想快速讀完一整份 kernel 原始碼從這裡開始
- **Apache NuttX**：[nuttx.apache.org](https://nuttx.apache.org/)｜**Eclipse ThreadX**：[threadx.io](https://threadx.io/)
- **ARM 架構**：ARMv8-A / ARMv7-M Architecture Reference Manual 的 memory model 章節（barrier 語意的權威來源）
- **書**：*Hard Real-Time Computing Systems*（Buttazzo，排程理論）、*Making Embedded Systems*（Elecia White，工程實務）

---

## 結語

回到開頭那個結論：**RTOS 不是 SoC 平台軟體的主科，但它是讓你對 SoC 的理解變完整的那一塊拼圖。**

如果只有 Linux 側的經驗，你對 SoC 平台的理解會停在 `remoteproc0: crash detected` 這一行。加上 RTOS 和 AMP 的理解，你可以繼續往下追——追到對面的 thread 卡在哪、為什麼卡、以及你怎麼證明的。

**那條分界線，就是「只看得到 Linux」和「看得到整顆 SoC」的分界線。**

---

*本文版本資訊以 2026 年 9 月為準。標注為「推論」的段落是我的判斷，不是查證過的事實。Zephyr 迭代快速，實作細節請以官方文件的對應版本頁面為準。*
