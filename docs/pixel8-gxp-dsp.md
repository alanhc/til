# 當防護開滿反而露出破口：Pixel 8 GXP DSP 漏洞與 MTE 繞過完整分析

**作者**：整理自 HITCON 2025 — Billy（Jheng Bing Jhong）& Pan Zhenpeng（Peter），STAR LABS SG

---

## 摘要

在資安研究的演進脈絡中，有一個反直覺的現象：主流防護機制愈完備，攻擊者就愈傾向把目光移向邊緣地帶。HITCON 2025 上，STAR LABS SG 的研究員 Billy 與 Peter 展示了一條針對 Google Pixel 8（Android 14）的本地提權鏈，起點是一顆幾乎無人研究過的 Google 自家 DSP（GXP），終點是 root shell。整條攻擊鏈中，MTE、KASLR、SELinux 等主流防護全數被繞過——不是靠什麼花式 bypass，而是從一開始就走了一條這些防護根本看不到的路。

---

## 一、為什麼要研究 GXP？攻擊面的選擇邏輯

在開始分析漏洞本體前，先理解研究者的「目標選擇」思維，才能看懂這整件事的脈絡。

Pixel 8 上的防護配置幾乎是目前 Android 裝置的天花板：

- **MTE（Memory Tagging Extension）**：ARM v8.5 引入的硬體記憶體標籤機制，用於在 pointer 與物理記憶體之間做標籤比對，有效攔截 buffer overflow 與 use-after-free
- **PAC（Pointer Authentication Code）**：在 pointer 中嵌入簽章，抵禦 ROP/JOP 攻擊
- **PAN / PXN**：防止 kernel 態直接操作 user space 記憶體
- **KASLR**：核心地址空間隨機化
- **slab free-list randomization、stack/heap 初始化強化、list 完整性檢查**…等一系列 kernel hardening

面對這樣的環境，研究者將攻擊面分成四個層次：

| 攻擊面類型 | 範例 |
|---|---|
| Universal | Linux kernel unix socket、binder、pipe buffer |
| Chipset-specific | Mali GPU、Qualcomm GPU driver、Qualcomm DSP |
| Vendor-specific | Samsung NPU、KNOX/Defex |
| Model/Module-specific | 特定機型的單一模組 |

越往下走，防護通常越薄，但影響範圍也越窄。GXP（Google eXtended Processing）屬於最後一類：

- 2022 年才隨 Pixel 7 引入
- 零公開文件、零 toolchain、零既有漏洞研究
- 影像處理核心組件，Google Camera 等系統 App 都依賴它
- 過去 Qualcomm DSP、Samsung NPU 都有類似問題被挖出 → 同樣模式能否複製？

這就是為什麼 GXP 成為目標：**最新、最少人看、又在高價值的系統 pipeline 上**。

---

## 二、進場前的障礙：SELinux Policy 分析

研究者不能直接碰 GXP。在 `untrusted_app` context 下，SELinux policy 明確禁止 open GXP device node，但允許對其發送特定 ioctl。

這個矛盾透露出一個設計：**必定有一個中介 server 代為 open device 後，將 file descriptor 傳回給 app**。

逆向 `libedge_tpu_client`、`libgxp.so` 等 library 後，確認了整條路徑：

```
Untrusted App
    → libedge_tpu_client（client library）
        → edge_tpu_app_server（system server，有 GXP 存取權）
            → open("/dev/gxp")
                → 將 FD 傳回 App
                    → App 可對 FD 發送 ioctl
```

只要能在「被列入白名單的 App 簽章或 context 下」執行程式碼，就能觸及 GXP 攻擊面。

---

## 三、漏洞本體：DMA 方向信任錯誤

### 3.1 正常 DMA mapping 的邏輯

DMA（Direct Memory Access）讓周邊硬體（如 DSP）可以不經過 CPU 直接存取系統記憶體。為了讓 CPU 端的記憶體保護與 DSP 端的 MMU 設定保持一致，kernel driver 在建立 mapping 時，必須同時設定：

1. **CPU 端 VMA（Virtual Memory Area）的存取屬性**（read-only / read-write）
2. **DSP MMU 上同一塊實體頁面的屬性**（透過 DMA direction：`DMA_TO_DEVICE`、`DMA_FROM_DEVICE`、`DMA_BIDIRECTIONAL`）

兩邊應該保持一致。

### 3.2 GXP driver 的問題

在 `ioctl(GXP_MAP_BUFFER, ...)` 的處理函數 `gxp_mapping_create()` 中，存在以下邏輯：

```c
// 虛擬化程式碼示意
struct vma = find_extend_vma(mm, user_vaddr);
folio_flags = derive_flags_from_vma(vma);  // 正確：從 VMA 取得 CPU 端屬性
// ...

// 問題在這裡：
mapping_dir = user_provided_dir;           // 錯誤：直接信任 user 傳入的 DMA 方向
dsp_mmu_flags = map_dir_to_mmu(mapping_dir);
set_dsp_mmu(phys_addr, dsp_mmu_flags);    // DSP MMU 被設定為 read-write
```

CPU 端的 VMA 屬性（read-only）被正確讀取，但 DSP MMU 的設定卻直接採用 user 傳入的 `mapping_dir`，完全沒有跟 VMA 屬性做比對。

攻擊者只要傳入 `DMA_BIDIRECTIONAL`，DSP 端就會認為那塊記憶體是可讀可寫的。

### 3.3 取得的 Primitive

這個 bug 提供了一個強力原語：

> **Write Read-Only Memory Primitive**
> CPU 端視為 read-only 的實體頁面，可透過 DSP 被任意寫入。

這繞過了 CPU MMU 的唯讀保護，MTE 對此完全無感知——因為 MTE 保護的是 CPU 端的記憶體存取合法性，不涉及 DMA 路徑。

---

## 四、確認可利用性：從模擬到 Replay Attack

### 4.1 第一次嘗試：模擬 DSP Firmware（失敗）

研究者嘗試：

1. 透過 kernel 的 device tree 找到 GXP firmware 的實體位址
2. 用自寫 kernel module 把 firmware dump 出來
3. 丟進 IDA 逆向，找「會對 buffer 寫入的 handler」
4. 嘗試用 QEMU 模擬執行

結果：QEMU 不支援該 DSP 的指令集、系統暫存器行為與公開文件不符，加上無符號表，逆向成本過高。數天後放棄。

### 4.2 第二次嘗試：Replay Attack + Frida（成功）

思路轉換：**不需要搞懂 DSP 怎麼運作，只需要找到「系統自己怎麼用 GXP」，然後重放它。**

步驟：

1. 從 SELinux policy 找出哪些 App 有 GXP 存取權（Google Camera 是最常用的）
2. 用 Frida 的 `Interceptor.attach()` hook Google Camera process 中所有 ioctl 呼叫
3. 列舉 `libgxp.so` 的所有 exported functions 並加 hook，記錄實際拍照時的 call flow 與參數
4. 找到關鍵 API：類似 `gxp_copy_open_named_library_from_buffer()` 的高階函式
5. 確認這個 API 會觸發前述的可疑 mapping 路徑，且**確認 DSP 會對 buffer 執行寫入**

PoC 驗證：

```
1. 在 user space 建立一個 read-only 映射頁面，初始化為 0x00
2. 透過 ioctl(GXP_MAP_BUFFER) 將其 import 給 GXP，強塞 DMA_BIDIRECTIONAL
3. 呼叫 gxp_copy_* API
4. 回到 CPU 端讀取該頁面 → 內容已變為 0xAA
```

**Write Read-Only Memory Primitive 實證成立。**

---

## 五、Exploit Chain：從 App 到 Root Shell

### 5.1 整體架構

```
Untrusted App
  │
  ├─[Stage 1]─ GXP write read-only → 覆寫 camera provider 的 library
  │                                  → 強迫 camera provider 重啟
  │                                  → 在 camera provider context 取得程式碼執行
  │
  ├─[Stage 2]─ 再次使用 write read-only（此時以 camera provider 身份）
  │             → 修改 modprobe 相關路徑設定
  │             → 在指定路徑放入惡意 kernel module binary
  │             → 觸發 modprobe
  │
  └─[Stage 3]─ Kernel module 被載入
               → 關閉 SELinux
               → 建立 reverse shell → Root Shell
```

### 5.2 為什麼選 Camera Provider？

`android.hardware.camera.provider` 服務具備兩個關鍵特性：

- 可以 open / ioctl GXP device（繼續使用漏洞）
- 可以 open / mmap 特定 vendor library（成為 library hijacking 目標）

這讓它成為一個在 SELinux policy 下「合法擁有足夠權限」的橋接點。

### 5.3 Library Hijacking 與強迫重啟

**問題：不知道 camera provider 的 PID。**

解法：利用 Android 系統的一個特性——開機早期啟動的 system daemon PID 落在一個相對小且穩定的範圍。研究者從有能力發送 kill signal 的 context，遍歷這個 PID 範圍逐一 kill。init 會自動拉起被殺死的 daemon，camera provider 也在其中，下次重啟時就會載入被替換過的 library。

**限制**：如果系統已長期運行且 camera provider 中途曾重啟過，PID 可能已超出穩定範圍，此方法不穩定。

### 5.4 Exploit 為何需要 5 分鐘？

GXP copy API 的行為類似 `strcpy`：遇到 `0x00` 就中止。但 shellcode 幾乎必然含有大量 null byte。研究者只能逐 byte 反覆呼叫 API，慢慢填入 payload，加上多個 stage 之間的 DSP ↔ CPU 記憶體同步，完整 exploit 執行時間約 5 分鐘。

---

## 六、漏洞的修補

Google 的修補方向是從根本上切斷「user 控制 DMA 方向」的可能性：

```
修補前：
  User 提供的 dir → mapping_dir → DSP MMU 屬性

修補後：
  Host VMA → get_user_pages flags（GUP flags）→ GCI flags → DSP MMU 屬性
```

透過強制從 VMA 的實際權限推導出 DMA 方向，user 傳入的 `dir` 參數被完全忽略，攻擊路徑不復存在。

---

## 七、防禦視角與啟示

### 7.1 MTE 不是萬靈丹，請搞清楚它保護什麼

MTE 的設計目標是抵禦**記憶體破壞類漏洞**（buffer overflow、use-after-free）。它在 CPU 端的 pointer 與對應記憶體頁面之間建立標籤比對，在每次 CPU 存取時做驗證。

它完全看不到的情況包括：

- **DMA 路徑的寫入**：DSP 直接透過 bus 寫入實體記憶體，不經過 CPU MMU
- **DSP/NPU/ISP 的 MMU 配置錯誤**
- **Driver 層的邏輯漏洞與權限邊界錯配**

導入 MTE 後的正確心態是：「我們對一類特定記憶體破壞攻擊更有抵抗力」，而不是「本地提權問題解決了」。

### 7.2 協同處理器的攻擊面必須列入 Threat Model

隨著 SoC 整合度提升，現代旗艦手機中存在大量協同處理器：DSP、NPU、ISP、Baseband、Secure Enclave… 每一顆都有自己的 driver、自己的 MMU、自己的 DMA 路徑。

安全審查不能只看 Linux 主線 + Android framework，所有 OEM/Google 自研 IP 的 driver 都應該成為一級審查目標，重點包括：

- DMA 方向是否由 kernel 根據 VMA 權限決定，還是信任 user input
- DSP/NPU 的 MMU 屬性是否與 CPU 端的 VMA 保持一致
- 有無 runtime consistency check 機制

### 7.3 Replay Attack 是研究閉源硬體的標準方法論

在沒有文件、沒有 ISA 規格、沒有 SDK 的情況下，研究者不需要完整逆向 firmware。只要：

1. 找出「誰在正常使用這個 device」（SELinux policy 是極好的地圖）
2. 用動態插樁（Frida）錄製 production App 的實際 call flow
3. 把真實的 App 行為當作「非官方 SDK」來重放

對藍隊的啟示：system App 對 kernel driver 的 ioctl 序列，是偵測 exploit 的重要訊號。非預期的參數組合（如 `DMA_BIDIRECTIONAL` 搭配既有 read-only VMA）應該被視為異常。

### 7.4 Kernel Module 仍然是最終後門

整條攻擊鏈最終落腳點是任意載入 kernel module。企業裝置或高價值目標的防線建議：

- 評估是否需要完全禁用動態 module 載入（`CONFIG_MODULES=n`）
- 若需要 module 支援，嚴格限制 `modprobe` 的可執行路徑與檔案來源
- 對 boot chain 與 system image 做完整性保護，確保 vendor library 無法被靜默替換

---

## 八、結論

這場研究的技術密度很高，但背後的思維邏輯其實相當清晰：**防護越完備的地方，研究者越應該往「防護沒覆蓋到的地方」找**。GXP DSP 之所以成為突破口，不是因為它特別脆弱，而是因為它幾乎沒有被任何人看過。

從防禦的角度來說，這個案例最值得帶走的一句話是：

> **真正的攻擊面，常常躲在你以為「只是加速影像處理的小 IP」裡面。**

在把主流防護都打開之前，先確保你知道自己的 Threat Model 覆蓋到哪裡；打開之後，不要誤以為它覆蓋到了所有地方。

---

*本文整理自 HITCON 2025 Day 1 議程，原始研究由 Billy（Jheng Bing Jhong）與 Pan Zhenpeng（Peter）於 STAR LABS SG 完成。漏洞已於 2024 Q1 完成修補。*
