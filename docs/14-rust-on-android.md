# Android 上的 Rust:Chip Vendor 需要知道什麼

> 系列文章之十四。總覽請見《Chip Vendor 視角的 Android Build System》。

Google 自 Android 12 起把 Rust 列為平台開發語言,動機非常直接:歷年 Android 安全漏洞約七成是記憶體安全問題,而新寫的 Rust code 幾乎消滅了這一類。對 chip vendor,問題是:什麼時候輪到我?要準備什麼?

---

## 一、現況:Rust 已經在系統裡的哪些地方

AOSP 內已用 Rust 重寫或新寫的元件(逐版增加):

- **Keystore2**(金鑰管理核心)、**DNS-over-HTTP/3**、**Ultra-wideband stack**、**Bluetooth stack(gabeldorsche 部分)**、**Virtualization framework(AVF/pKVM 相關)**、Media 相關 parser 等。
- **Kernel 側**:上游 Linux 的 Rust for Linux 持續推進,Android Common Kernel 跟進;Android 14+ 的 ACK 已可寫 Rust kernel module(實驗性 → 逐步實用化),Google 已有 Rust 寫的 driver 案例。
- **Binder**:官方提供 Rust binder binding(`libbinder_rs`),AIDL compiler 可產 Rust backend——**這意味著用 Rust 寫 HAL service 已是官方支援路徑**。

政策風向:Google 的立場是「新 code 優先用記憶體安全語言」,C/C++ 存量不強制重寫。CDD 目前不強制 vendor 用 Rust,但平台元件的示範效應與安全審查壓力會逐步傳導。

---

## 二、Build system 整合:Soong 原生支援

Rust 在 AOSP 不用 Cargo,而是 Soong 原生規則(對照 Soong 篇):

```python
rust_binary {
    name: "myvendor_telemetry",
    srcs: ["src/main.rs"],
    vendor: true,                       // vendor variant 規則同樣適用
    rustlibs: [
        "libbinder_rs",
        "liblog_rust",
        "vendor.myvendor.hardware.thermal-V1-rust",   // AIDL Rust backend
    ],
}

rust_library {
    name: "libmyvendor_algo",
    crate_name: "myvendor_algo",
    srcs: ["src/lib.rs"],
    vendor_available: true,
}

rust_ffi_shared {                        // 給 C/C++ 呼叫的 FFI 介面
    name: "libmyvendor_algo_ffi",
    crate_name: "myvendor_algo_ffi",
    srcs: ["src/ffi.rs"],
    vendor: true,
}
```

要點:

- **第三方 crate 要 vendored 進 `external/rust/crates/`**(有既定流程與審查),不能 build 時抓 crates.io——供應鏈管控。
- `vendor: true`/`vendor_available` 的 image variant 規則、install 路徑,與 C/C++ 完全一致。
- AIDL 介面加 `backend: { rust: { enabled: true } }` 即產 Rust binding——HAL 開發篇的整套流程(freeze、VINTF、sepolicy)不變,只是實作語言換掉。
- Kernel 側:Kleaf 支援 Rust kernel module 的 build(隨 ACK 版本演進,需開對應 config)。

---

## 三、Chip vendor 的採用策略

### 3.1 先吃甜區

風險低、收益高的切入點:

1. **新寫的 daemon/service**:解析外部輸入(協定、檔案格式)的元件——記憶體安全收益最大。
2. **新 HAL service**:AIDL Rust backend 成熟,綁定層官方維護;3A/演算法等既有 C++ 資產繼續用 FFI 掛。
3. **工具鏈與 host 工具**:產測工具、解析器等,風險幾乎為零的練兵場。

暫緩:重寫既有穩定的 C++ HAL(收益低、風險高)、與大量既有 C++ 深度耦合的熱路徑(FFI 邊界成本)、舊平台維護分支(工具鏈版本綁定問題)。

### 3.2 Kernel driver 的判斷

觀察指標:你所在 domain 的 binding 成熟度(上游 Rust abstraction 是否覆蓋你要的子系統——GPU、網路已有實例,多數子系統仍在演進)、ACK 對 Rust module 的 KMI 政策。務實路徑:**新的、獨立性高的 driver 試點**,核心 driver 等 binding 穩定。GKI 篇的紀律(KMI symbol、ABI 檢查)對 Rust module 同樣適用。

### 3.3 組織準備

- **能力建設**:C++ 工程師轉 Rust 的學習曲線集中在所有權/生命週期,計畫性地讓 2–3 人先在工具類專案練起來,再進 production。
- **FFI 紀律**:Rust 的安全保證止於 `unsafe` 與 FFI 邊界——邊界層要薄、集中、重點 review(`bindgen`/`cxx` 工具輔助)。
- **安全論述**:對客戶與認證(未來可能的安全要求),「新元件用 Rust」會逐漸從加分項變成期待值。

---

## 結語

> **Rust 進 Android 不是語言時尚,是 Google 對「七成漏洞是記憶體安全」的結構性回應;Soong 與 AIDL 已把路鋪好,vendor variant 的規則原封不動適用。** Chip vendor 的正確姿勢不是觀望也不是全面重寫,而是「新增元件優先評估 Rust、FFI 邊界管好、kernel 側跟著 ACK 節奏走」——五年後回頭看,今天開始練兵的團隊會感謝自己。
