# Rust 韌體筆記：常被追問的那些點

> 定位：寫給**已經有 C / 系統軟體底子**、想把 Rust 用在 BSP / bare-metal 韌體上的人。
> 不是 Rust 入門教學，而是整理「講到這裡通常會被追問什麼」——用問答的形式逼自己把理解說清楚。
> 最後更新：2026-09 · 對應 Rust 1.98 / Edition 2024

---

## 0. 怎麼用這份筆記

| 讀者情境 | 建議路徑 |
|---|---|
| 時間很趕，只想抓重點 | §1 → §7 → §9 → 回頭補 §2.7、§3.3、§4 |
| 從零開始學 | §2 → §3 → §4 → 做 §10 的 side project → §7 |
| 已經會 Rust，只缺韌體角度 | §3 → §4 → §5 → §7 的「韌體專屬題」 |

**核心心法**：韌體場景談 Rust，**重點很少在語法**，而在三件事——
1. 你知不知道 Rust 的安全保證**具體防住了哪一類 bug**（而不是喊 "memory safe"）
2. 你知不知道**保證在哪裡會斷掉**（`unsafe`、FFI、MMIO、DMA、中斷）
3. 你能不能在**沒有 heap、沒有 OS、要塞進 flash** 的環境裡把它用起來

---

## 1. 產業現況：先把事實擺出來

這一段的用途是——談 "Why Rust for firmware?" 時，講的是產業事實而不是行銷語。

- **Linux kernel**：Rust 已經不是實驗性質了。Miguel Ojeda 在 2025 年底送出 "rust: conclude the Rust experiment" patch，把文件裡「實驗性、僅供開發者」的段落刪掉，理由是「Rust 已經透過 Android 進到數百萬台裝置」。
- **NVIDIA**：`nova-core` / `nova-drm`——NVIDIA 新一代 GPU 的**開源 kernel driver 是用 Rust 寫的**，在 Linux 7.2 / 7.3 持續擴充中（GSP firmware 為界面）。**這是目前最有說服力的一個例證**，它說明 GPU / kernel driver 這條線為什麼開始採用 Rust。
- **Android / Google**：memory safety bug 曾經佔 Android 高風險漏洞 **60% 以上**；Google 的策略不是重寫舊 C/C++（平台裡超過 70% 是 memory-unsafe 語言），而是 **"new code in memory-safe languages"**——新程式碼走 Rust，舊程式碼靠 MTE / HWASan 守。2025 年 Android memory safety 漏洞佔比首次掉到 20% 以下。
- **功能安全**：Ferrocene（Ferrous Systems）提供通過 ISO 26262 / IEC 61508 認證的 Rust toolchain，這是車用（含 NVIDIA DRIVE 這條線）能用 Rust 的前提。
- **生態成熟度標記**：`embedded-hal` 1.0 在 2024 年初釋出，代表 embedded 生態的 trait 介面終於穩定，driver crate 不再各自為政。

**一句話版本**：
> "It's not a language preference — it's a defect-class elimination strategy. Memory safety bugs were the single largest CVE category in both Android and the kernel, and the industry response is to write *new* code in Rust rather than rewrite old code. NVIDIA's nova driver and Android's platform Rust are both instances of that."

---

## 2. 語言核心機制（用 C 韌體工程師的視角）

### 2.1 Ownership / Move — 對照 `malloc`/`free`

**規則**：每個值有唯一 owner；owner 離開 scope 時值被 drop；賦值/傳參預設是 **move**（除非型別是 `Copy`）。

```rust
let a = String::from("fw");
let b = a;              // move：a 從此不可用
// println!("{a}");     // 編譯錯誤：borrow of moved value
```

**它防住的 C bug**：
- double free — 因為只有一個 owner 會 drop
- use after free — move 之後原變數在**編譯期**就被標記為不可用
- 忘記 free — drop 是自動插入的（RAII，等同 C++ destructor，但編譯器強制）

**C 對照**：
```c
char *a = malloc(n);
char *b = a;
free(a);
free(b);        // double free — C 編譯器完全不會抱怨
```

> 常見追問：「Rust 有 GC 嗎？」→ **沒有**。所有權是純編譯期分析，drop 是編譯器在對的位置插入的呼叫，**零執行期額外成本**。這對韌體是關鍵：沒有 runtime、沒有 GC pause、可預測的釋放時機。

### 2.2 Borrowing / Aliasing — 對照 `restrict`

**規則（整份筆記最核心的一條）**：在任一時間點，對同一份資料，只能有
- **多個** `&T`（shared / immutable borrow），**或**
- **恰好一個** `&mut T`（exclusive borrow）

兩者不可同時存在。

```rust
let mut buf = [0u8; 4];
let r1 = &buf;
let r2 = &buf;              // OK：多個唯讀
let w = &mut buf;           // error[E0502]: cannot borrow `buf` as mutable
w[0] = 1;
println!("{r1:?} {r2:?}");  // ← 因為 r1/r2 在這之後還被用到，所以上面才會錯
```

> **NLL（Non-Lexical Lifetimes）補充**——這是個很好的追問點：借用的存活範圍不是到 scope 結尾，而是到**最後一次使用**。所以如果把最後那行 `println!` 拿掉，上面的 `&mut buf` 就**合法**了。理解這點，才算真的懂借用規則而不是背規則。

**為什麼韌體工程師該在意**：這其實就是**編譯器強制執行的 `restrict`**。C 裡 `restrict` 是你對編譯器的承諾，錯了就是 UB 而且沒人告訴你；Rust 裡 `&mut` **本質上就是 `restrict` 指標**，編譯器幫你驗證。所以 rustc 可以放心對 `&mut` 做 aliasing-based 最佳化。

**它防住的 C bug**：iterator invalidation、在別人持有指標時 realloc、多執行緒 data race。

> 常見追問：「這規則會不會太嚴格？」→ 會，所以有 **interior mutability**（§2.8）把檢查搬到執行期，以及 `unsafe` 讓你自己承擔（§2.7）。重點是**預設安全、例外顯式標記**。

### 2.3 Lifetime — 對照 dangling pointer

Lifetime 不是「變數活多久」，而是**編譯器用來驗證「引用不會活得比被引用的資料久」的標註**。

```rust
fn longest<'a>(x: &'a str, y: &'a str) -> &'a str {
    if x.len() > y.len() { x } else { y }
}
```
讀法：「回傳的引用，其有效期不超過 `x` 和 `y` 兩者中較短的那個」。

```rust
fn dangle() -> &String {     // 編譯錯誤
    let s = String::from("x");
    &s                        // s 在函式結束時 drop
}
```

**C 對照**：回傳 stack local 的位址——C 編譯器頂多給 warning，Rust 直接不給過。

**實務上**：90% 的情況 lifetime 由 **elision rules** 自動推導，你不用寫。真正需要手寫的場合是「struct 裡放引用」，而**韌體程式碼裡這種 struct 通常是 `'static`**（指向 MMIO 區域、指向 `static` buffer）。

> 常見追問：「`'static` 是什麼意思？」→ 兩個意思要分清楚：`&'static T` = 引用的資料活到程式結束（例如 `static` 變數、字串字面量、`.rodata`）；`T: 'static` 作為 bound = 這個型別**不含任何非 'static 的引用**（`String` 滿足 `T: 'static`）。

### 2.4 Trait / 泛型 / 單態化 — 對照 C 的 ops struct

C 的多型長這樣：
```c
struct uart_ops { int (*write)(struct uart*, const u8*, size_t); };
```
Rust：
```rust
trait Uart {
    fn write(&mut self, buf: &[u8]) -> Result<usize, Error>;
}
```

兩種派送方式，**這個取捨在韌體上特別重要**：

| | 靜態派送 `impl Trait` / `<T: Trait>` | 動態派送 `&dyn Trait` |
|---|---|---|
| 機制 | **monomorphization**：每個具體型別生一份程式碼 | fat pointer =（資料指標, vtable 指標） |
| 執行期成本 | 零，可 inline | 一次間接呼叫，無法跨界 inline |
| 程式碼大小 | **會膨脹**（每個型別一份） | 只有一份 |
| 何時用 | 熱路徑、只有一兩種具體型別 | flash 吃緊、型別多、需要執行期選擇 |

> **實務做法**：「在 MCU 上我會實際量。`cargo bloat` / `cargo size` 看 `.text`，如果某個泛型函式被單態化出十幾份，我會考慮改成 `dyn` 或把泛型函式的本體抽成非泛型的 inner function，只留薄薄一層泛型外殼（thin generic wrapper），這樣單態化只複製那層外殼。」——這是 flash 受限環境的標準手法。

補充術語：以前叫 *object safety*，2024 年後官方改稱 **dyn compatibility**（能不能做成 `dyn Trait`）。

### 2.5 錯誤處理 — 對照 `errno` / `-EINVAL`

```rust
enum Option<T> { Some(T), None }
enum Result<T, E> { Ok(T), Err(E) }
```

- `?` 運算子 = 「錯就提早回傳」，等同 C 裡到處寫的 `if (ret < 0) return ret;`，但**不可能忘記檢查**（`Result` 有 `#[must_use]`，忽略會 warning）。
- `panic!` = 不可恢復。韌體上通常設 `panic = "abort"`，`#[panic_handler]` 裡記 log 再重開（§3.7）。

**它防住的 C bug**：忽略回傳值。C 裡 `read()` 回傳 -1 沒人檢查是經典漏洞來源。

> 常見追問：「什麼時候該 panic、什麼時候該回 `Result`？」→ 「`Result` 用於呼叫者能合理處理的狀況（周邊 busy、CRC 不符、timeout）；`panic` 用於違反不變式、代表韌體本身有 bug 的狀況（狀態機進到不可能的 state）。在安全關鍵的韌體我傾向把 panic 路徑收斂到一個會寫 crash log 並觸發 watchdog reset 的 handler，而不是靜靜 halt。」

### 2.6 `Send` / `Sync` — 執行緒與中斷安全，寫進型別系統

- `Send`：型別可以**跨執行緒轉移所有權**
- `Sync`：`&T` 是 `Send`，也就是**可以多執行緒同時共享引用**

兩者都是 **auto trait**，編譯器自動推導。記住幾個經典：

| 型別 | Send | Sync | 為什麼 |
|---|---|---|---|
| `Rc<T>` | ✗ | ✗ | 引用計數非原子，跨執行緒會算錯 |
| `Arc<T>` | ✓* | ✓* | 原子計數（*需 `T: Send + Sync`） |
| `RefCell<T>` | ✓ | ✗ | 借用計數非原子 |
| `Mutex<T>` | ✓* | ✓* | 這正是 `Mutex` 的用途（*需 `T: Send`） |
| `*const T` / `*mut T` | ✗ | ✗ | 裸指標，編譯器不知道你要幹嘛 |

> **韌體角度的重點**：「`Send`/`Sync` 不只管執行緒。在 bare-metal 上，**ISR 就是另一個執行單元**。當我要把周邊的 handle 從 `main` 交給中斷處理常式，型別系統會逼我證明這件事是安全的——通常是包進 `Mutex<RefCell<Option<T>>>` 搭配 `critical-section`。C 裡這是靠 code review 和註解在守的，Rust 裡是編譯器在守。」

### 2.7 `unsafe` 與 UB — 最容易講錯的一題

**最重要的觀念澄清（先講這句，會顯得你懂）**：
> `unsafe` **不會關掉 borrow checker**。它只解鎖五件編譯器無法驗證的事，其他所有規則照樣生效。

`unsafe` 解鎖的五件事：
1. 解引用裸指標（raw pointer）
2. 呼叫 `unsafe` 函式（含所有 FFI）
3. 存取/修改 `static mut`
4. 實作 `unsafe` trait（`Send`、`Sync`）
5. 存取 `union` 的欄位

**正確的心智模型**：`unsafe` 是**義務轉移**。編譯器說「這裡我證明不了，你來證明」。所以每個 `unsafe` block 上面都該有 `// SAFETY:` 註解說明為什麼成立——這在 Linux kernel 的 Rust code 是**強制規範**，自己的 code 也該照做。

```rust
/// # Safety
/// `addr` 必須是有效、對齊、且在整個 'static 期間唯一映射到此周邊的 MMIO 位址。
unsafe fn read_reg(addr: *const u32) -> u32 {
    // SAFETY: 由呼叫端保證 addr 有效且對齊（見上方契約）。
    unsafe { core::ptr::read_volatile(addr) }
}
```

**核心設計模式：safe abstraction**——把 `unsafe` 關在小盒子裡，對外只露出無法誤用的安全 API。整個 embedded Rust 生態就是這個模式：PAC 內部全是 `unsafe` 的 MMIO 存取，對外是 safe 的 `.set_bit()`。

**Rust 的 UB 有哪些**（至少要知道這三四個）：
- 解引用 dangling / 未對齊 (unaligned) 指標
- 違反 aliasing 規則（同時存在 `&mut` 和其他引用）
- data race
- 讀取未初始化記憶體
- 產生無效值（`bool` 不是 0/1、`char` 超出範圍、`&T` 為 null）
- 破壞函式的安全契約

> 常見追問：「Rust 就不會有記憶體漏洞了嗎？」→ **不要說會**。正確答法：「Safe Rust 在**已知的 soundness bug 之外**保證沒有 UB。實務上漏洞會出現在三個地方：`unsafe` block 內的邏輯錯誤、FFI 邊界（C 那側的假設沒被滿足）、以及邏輯漏洞（Rust 不防你把金鑰印到 log）。所以我看 Rust 韌體的 review 重點會放在 `unsafe` 的 SAFETY 契約和 FFI wrapper，那是攻擊面收斂之後剩下的部分。」

補充：`static mut` 現在幾乎不能用了——Edition 2024 起 `static_mut_refs` 是 **error**，因為對 `static mut` 取引用太容易做出 aliasing UB。取而代之用 `&raw mut`（Rust 1.82 起穩定，取代 `addr_of_mut!`）或直接用 `SyncUnsafeCell` / `static_cell`。

### 2.8 Interior Mutability — 透過 `&T` 修改內容

當 borrow 規則太緊時的逃生口。**全部都是建立在 `UnsafeCell<T>` 之上**（唯一被編譯器認可、允許透過 `&T` 修改的型別）。

| 型別 | 檢查時機 | 違規後果 | no_std 可用 |
|---|---|---|---|
| `Cell<T>` | 無（只能整份換掉） | — | ✓ (core) |
| `RefCell<T>` | **執行期**計數 | `panic!` | ✓ (core) |
| `Mutex<T>` (std) | 執行期上鎖 | 阻塞 | ✗ |
| `critical-section::Mutex` | 關中斷 | — | ✓ |
| `AtomicU32` 等 | 硬體原子指令 | — | ✓ (視 target) |

> 韌體注意：`AtomicU32` 在部分 target（如 `thumbv6m`，Cortex-M0）**沒有硬體 CAS**，只有 load/store atomic。需要 CAS 時要用 `portable-atomic` crate（用關中斷模擬）。這個細節講出來很有說服力。

---

## 3. `no_std` / Bare-metal — 真正的韌體部分

### 3.1 三層函式庫：`core` / `alloc` / `std`

```
core   ← 無任何依賴。型別、trait、Option/Result、指標操作、原子。永遠可用。
alloc  ← 需要一個 global allocator。Box / Vec / String / BTreeMap。
std    ← 需要 OS：檔案、執行緒、網路、時間、std::sync。韌體上通常沒有。
```

`#![no_std]` = 「不要連結 `std`，只給我 `core`」。想要 `Vec` 就 `extern crate alloc;` 並提供 `#[global_allocator]`。

> 常見追問：「`no_std` 到底少了什麼？」→ 「少的是**需要 OS 支援的東西**：heap、執行緒、檔案系統、`std::time`、`println!`、以及 unwinding。語言本身完全沒少——trait、泛型、閉包、iterator、`?`、pattern matching 全都在 `core` 裡，都是零成本的編譯期構造。」

### 3.2 專案骨架

```rust
#![no_std]
#![no_main]

use cortex_m_rt::entry;
use panic_halt as _;          // 提供 #[panic_handler]

#[entry]
fn main() -> ! {              // 韌體 main 永不回傳
    loop {}
}
```

`.cargo/config.toml`：
```toml
[build]
target = "thumbv7em-none-eabihf"   # Cortex-M4F。Tegra 那側是 aarch64-unknown-none-softfloat

[target.thumbv7em-none-eabihf]
runner = "probe-rs run --chip STM32F411RETx"
rustflags = ["-C", "link-arg=-Tlink.x"]
```

`memory.x`（餵給 linker script）：
```
MEMORY
{
  FLASH : ORIGIN = 0x08000000, LENGTH = 512K
  RAM   : ORIGIN = 0x20000000, LENGTH = 128K
}
```

**target triple 讀法**：`thumbv7em-none-eabihf` = `<arch>-<vendor/os>-<abi>`，`none` 就是「沒有作業系統」。`aarch64-unknown-none-softfloat` 是 kernel / EL2 韌體常用的（關掉 SIMD/FP，因為那些 register 在 exception handler 裡不一定有存）。

`Cargo.toml` 的 release profile（韌體必調）：
```toml
[profile.release]
opt-level = "z"      # 或 "s"：對 flash size 最佳化
lto = true           # 跨 crate inline + 死碼消除，通常省很多
codegen-units = 1
panic = "abort"      # 不要 unwinding table
debug = true         # 不影響 flash 大小（debug info 不進 .text），但 defmt/backtrace 需要
```

### 3.3 MMIO：`volatile` 在 Rust 裡怎麼寫

**Rust 沒有 `volatile` 關鍵字**——它是**操作**不是型別修飾詞。

```rust
use core::ptr::{read_volatile, write_volatile};

const GPIOA_ODR: *mut u32 = 0x4002_0014 as *mut u32;

// SAFETY: 位址來自 SoC datasheet，4-byte 對齊，且此函式為唯一存取者。
unsafe { write_volatile(GPIOA_ODR, 1 << 5); }
let v = unsafe { read_volatile(GPIOA_ODR) };
```

**為什麼 Rust 選擇這樣做（設計論述）**：C 的 `volatile` 是型別修飾詞，會沿著型別到處傳染，而且「`volatile struct` 的哪些存取是 volatile」在 C 標準裡定義得很糊。Rust 把它變成**明確的函式呼叫**，你一眼就看得出哪一行真的打到硬體。

**volatile ≠ atomic ≠ memory barrier**（韌體上一定要分清楚）：
- `volatile`：阻止**編譯器**省略/合併/重排這次存取。**不產生任何 CPU 指令**。
- `atomic`：保證操作不可分割，並可指定 ordering，會產生 `LDREX/STREX`、`DMB` 之類指令。
- barrier：`cortex_m::asm::dsb()` / `dmb()` / `isb()`——阻止**CPU / store buffer / 寫入緩衝**重排。

> 經典陷阱題：「只用 `volatile` 寫 DMA descriptor 夠不夠？」→ **不夠**。`volatile` 只管編譯器。你還需要 (a) cache maintenance（clean/invalidate，若該區域可 cache）、(b) `DSB` 確保寫入真的出去、才能去戳 DMA 的 kick register。Rust 在這件事上和 C 完全一樣，沒有魔法。

**存取 `packed` struct 欄位**：不能取引用（會是 unaligned reference = UB），要用 `&raw const`：
```rust
#[repr(C, packed)]
struct Hdr { a: u8, b: u32 }
let h = Hdr { a: 1, b: 2 };
let b = unsafe { core::ptr::read_unaligned(&raw const h.b) };
```

### 3.4 Embedded 生態的四層架構

```
BSP     (board support)   ← "板子上的 LED 在 PA5"
 ↑
HAL     (stm32f4xx-hal)   ← 實作 embedded-hal trait，safe API，typestate
 ↑
PAC     (stm32f4)         ← svd2rust 從 SVD 檔自動生成，一個暫存器一個型別
 ↑
硬體 / MMIO
```

- **PAC**（Peripheral Access Crate）由 `svd2rust` 從廠商的 **SVD 檔**自動生成。等同於 C 的 `stm32f4xx.h`，但**型別安全**：唯讀欄位沒有 `write()` 方法、bitfield 是 enum 而不是 magic number。
- **`embedded-hal` 1.0**：一組跨廠商的 trait（`SpiBus`、`I2c`、`OutputPin`、`DelayNs`…）。意義是**driver 可攜**——一個 sensor driver 寫一次，任何實作了這些 trait 的 MCU 都能用。C 世界沒有這種東西（每家 HAL 都自己一套）。
- 非阻塞/非同步版本是分開的 crate：`embedded-hal-nb`、`embedded-hal-async`。

### 3.5 中斷、臨界區、與 singleton

**問題**：怎麼把 `main` 裡建立的周邊 handle 傳給 ISR？在 C 裡就是一個 global 加上關中斷；在 Rust 裡型別系統會擋你。

標準解法：
```rust
use core::cell::RefCell;
use critical_section::Mutex;

static TIMER: Mutex<RefCell<Option<Timer>>> = Mutex::new(RefCell::new(None));

// main 裡
critical_section::with(|cs| {
    TIMER.borrow(cs).replace(Some(timer));
});

// ISR 裡
#[interrupt]
fn TIM2() {
    critical_section::with(|cs| {
        if let Some(t) = TIMER.borrow(cs).borrow_mut().as_mut() {
            t.clear_interrupt();
        }
    });
}
```

**這段的精髓**：`critical_section::with` 給你一個 `CriticalSection` token `cs`。`Mutex::borrow` **要求你出示這個 token 才給你資料**。也就是說——**「必須在關中斷的狀態下才能碰這個資料」這件事，被編碼進了函式簽章**，忘記關中斷會編譯不過。C 裡這是靠註解和自律。

**Singleton / `Peripherals::take()`**：PAC 提供 `Peripherals::take() -> Option<Peripherals>`，第二次呼叫回 `None`。這在型別層面保證**整個程式只有一個地方能拿到某個周邊的 `&mut`**，從根本上消除「兩個模組同時設定同一個暫存器」這類 bug。

**RTIC** 更進一步：把資源共享與優先權宣告出來，用 **SRP (Stack Resource Policy)** 在編譯期算出誰需要跟誰互斥，只在必要時提升 BASEPRI（而不是無腦關全部中斷）。這是「Rust 讓你做到 C 做不到的事」的好例子。

### 3.6 沒有 heap 怎麼辦

- **`heapless`**：`Vec<T, N>`、`String<N>`、`spsc::Queue<T, N>`、`FnvIndexMap`——容量是 **const generic**，整份放 stack 或 `static`，滿了回 `Err` 而不是 panic。
- **`static_cell`**：在執行期初始化一個 `static`，拿到 `&'static mut T`。取代 `static mut`。
- **const generics**：`struct Buf<const N: usize> { data: [u8; N] }`——編譯期決定大小，零成本。
- 真要 heap：`embedded-alloc` + `#[global_allocator]`，但**大多數安全關鍵韌體規範直接禁止動態配置**（MISRA、DO-178C），這點提出來會顯得你懂領域。

> Kernel 補充：Rust for Linux 用的是**可失敗配置**——`KBox::new(x, GFP_KERNEL)?` 回傳 `Result`，因為 kernel 裡 OOM 不能 abort。這跟 userspace Rust 的 `Box::new` 直接 abort 不同。做 kernel / driver 時知道這個差別很值錢。

### 3.7 Panic handler

`no_std` binary **必須**提供一個：
```rust
#[panic_handler]
fn panic(info: &core::panic::PanicInfo) -> ! {
    // 實務上：把 file:line 寫進 RAM 的 crash log（不要碰 flash，可能正在燒）
    // 餵一次 watchdog 也不要，讓它 timeout 觸發 reset
    cortex_m::interrupt::disable();
    loop { cortex_m::asm::bkpt(); }
}
```
現成的：`panic-halt`（停住）、`panic-reset`（重開）、`panic-probe`（透過 defmt/RTT 印出來，開發時用）。

> 常見追問：「production 韌體 panic 了該怎麼辦？」→ 「不能靜靜 halt——那是最糟的失效模式，裝置變磚而且沒有線索。我的做法是：關中斷 → 把 PC/LR/panic location 寫進一塊**不會被 reset 清掉的 RAM（noinit section）** → 觸發 watchdog reset → 開機時 bootloader 檢查那塊 RAM，把 crash log 上報。這跟 C 韌體的做法一樣，Rust 只是讓 panic 的入口收斂成單一函式，比 C 到處散落的 `assert` 好接。」

### 3.8 Typestate Pattern — 用型別系統做狀態機

**這是 embedded Rust 最漂亮的招，也是最能展示零成本抽象的例子。**

```rust
use core::marker::PhantomData;

pub struct Input;
pub struct Output;

pub struct Pin<MODE> {
    idx: u8,
    _mode: PhantomData<MODE>,
}

impl Pin<Input> {
    pub fn is_high(&self) -> bool { /* ... */ true }
    pub fn into_output(self) -> Pin<Output> {
        // 設定暫存器切換模式
        Pin { idx: self.idx, _mode: PhantomData }
    }
}

impl Pin<Output> {
    pub fn set_high(&mut self) { /* ... */ }
}
```

**效果**：`Pin<Input>` **根本沒有 `set_high` 這個方法**，對輸入腳位寫值不是執行期錯誤，是**編譯期不存在的東西**。`PhantomData` 佔 0 bytes，整套抽象**零執行期成本**。

同樣的手法用在：DMA transfer（`Idle` → `InProgress` → `Complete`）、UART（`Configured` / `Unconfigured`）、電源狀態、加密引擎的 key-loaded 狀態。

> 一句話總結：「這是把狀態機從**執行期的 if-else 檢查**搬到**編譯期的型別檢查**。C 裡我們用 enum + assert，錯誤在跑到那行才發現；Rust 裡違規的程式碼根本編不出來，而且因為 `PhantomData` 是 ZST，binary 完全沒有變大。」

### 3.9 Async：Embassy 與 RTIC

- **Embassy**：`no_std` 的 async executor。`async fn` 被編譯成 **state machine struct**，大小在編譯期已知，**不需要 heap、不需要每個 task 一份 stack**。這解決了傳統 RTOS 最痛的問題——每個 thread 都要預留 stack，而你永遠不知道要留多少。
- **RTIC**：中斷驅動、基於硬體優先權的並行框架，不是 async runtime，更接近「型別安全的裸機中斷排程器」。

> 常見追問：「async 在 MCU 上為什麼是零成本？」→ 「因為 `async fn` 是編譯期轉換：編譯器把它變成一個實作 `Future` 的 struct，`.await` 點變成 state machine 的狀態。所有 local 變數存在這個 struct 裡，大小編譯期已知。相較 RTOS 每個 task 要靜態分配一塊保守估計的 stack，async task 的記憶體用量是**精確的**。代價是 executor 的複雜度，以及 debug 時 call stack 比較難讀。」

---

## 4. Rust ↔ C 互操作（FFI）— 實務上最常被追問的一段

因為沒有人會把既有韌體整包重寫，**實務上真正的問題是怎麼漸進導入**。

### 4.1 基本形狀

**Rust 呼叫 C**：
```rust
use core::ffi::{c_char, c_int};

unsafe extern "C" {
    fn crc32(data: *const u8, len: usize) -> u32;
    fn c_init(name: *const c_char) -> c_int;
}
```

**C 呼叫 Rust**：
```rust
#[unsafe(no_mangle)]
pub extern "C" fn fw_checksum(ptr: *const u8, len: usize) -> u32 {
    if ptr.is_null() || len == 0 { return 0; }
    // SAFETY: 呼叫端保證 ptr..ptr+len 是有效且存活的可讀記憶體。
    let s = unsafe { core::slice::from_raw_parts(ptr, len) };
    s.iter().fold(0u32, |a, &b| a.wrapping_add(b as u32))
}
```
> 注意 Edition 2024 的語法變動：`extern` block 要寫 `unsafe extern "C"`，`no_mangle` 要寫 `#[unsafe(no_mangle)]`。用舊語法代表參考資料已經過時。

### 4.2 型別佈局：`repr`

| 屬性 | 意義 | 用在哪 |
|---|---|---|
| `#[repr(C)]` | 用 C 的佈局規則與順序 | 所有跨 FFI 的 struct/enum |
| `#[repr(transparent)]` | 與唯一欄位佈局完全相同 | newtype wrapper 過 FFI |
| `#[repr(packed)]` | 無 padding | wire protocol、暫存器 image（小心 unaligned） |
| `#[repr(u32)]` | 指定 enum 的底層型別 | C enum 對接 |

**預設的 `repr(Rust)` 不保證欄位順序**——編譯器會重排來省 padding。忘記加 `#[repr(C)]` 是 FFI 最常見的 bug。

### 4.3 幾個一定要知道的 FFI 陷阱

1. **Panic 不可以穿過 FFI 邊界**。Rust 1.81 起，panic 要 unwind 出 `extern "C"` 函式會直接 **abort**（以前是 UB）。韌體上通常 `panic = "abort"`，所以無所謂，但要講得出來。
2. **Null pointer optimization**：`Option<&T>`、`Option<NonNull<T>>`、`Option<extern "C" fn()>` 和裸指標**同樣大小**，`None` 就是 null。所以 C 的「可為 NULL 的指標」在 Rust 側可以誠實地寫成 `Option<&T>`，不需要額外空間。這題很愛考。
3. **字串**：C 是 NUL 結尾、Rust 的 `str` 是 (ptr, len) 且保證 UTF-8。要用 `CStr` / `CString` 轉換，**不能直接丟**。
4. **所有權要講清楚**：誰 malloc 誰 free。Rust 配置的記憶體不能給 C `free()`，反之亦然。慣例是「誰配置誰提供釋放函式」。
5. **`usize` vs `size_t`**：一般相同，但 cross-compile 到奇怪 target 時要驗證。用 `core::ffi::*` 的型別別名比較保險。

### 4.4 工具與導入策略

- **`bindgen`**：讀 C header 產生 Rust FFI 宣告。放在 `build.rs` 裡跑，header 改了自動同步。
- **`cbindgen`**：反向，從 Rust 產生 C header，給既有的 C build 用。
- **build system**：Rust 側編成 `staticlib`（`crate-type = ["staticlib"]`）產出 `.a`，讓既有的 Makefile / Kbuild / Soong 直接連進去。**這是漸進導入最常見的形狀。**

**「如何在既有 C 韌體中導入 Rust」的標準答法（背這個結構）**：
> 1. 先挑**新的、葉節點的、攻擊面高的**模組——parser、protocol handler、crypto wrapper。不要從核心排程器開始。
> 2. 用 `bindgen` 對既有 header 產生 binding，Rust 模組編成 `staticlib` 接進現有 build。
> 3. 在 Rust 側寫一層薄的 **safe wrapper**，把所有 `unsafe` 收斂在裡面，上層業務邏輯全部是 safe Rust。
> 4. CI 上加 `clippy -D warnings`、`cargo miri`（跑得動的邏輯部分）、以及既有的 HIL 測試。
> 5. 量 flash / RAM 差異（`cargo size`、`cargo bloat`），準備好向主管解釋成本。
>
> 「風險我會誠實講：toolchain 認證、團隊學習曲線、debug 工具鏈成熟度（尤其是廠商提供的 debugger 對 Rust symbol 的支援），還有廠商 BSP 只出 C 這件事。所以是**漸進**，不是重寫。」

---

## 5. 除錯與工具鏈（「你怎麼 debug」）

| 工具 | 用途 | C 世界的對照 |
|---|---|---|
| `probe-rs` | flash + debug，支援 CMSIS-DAP/J-Link/ST-Link | OpenOCD + GDB |
| `defmt` | 延遲格式化 log：把格式字串留在 host 端，target 只送 index + 參數 | printf，但省掉數 KB flash 和頻寬 |
| RTT | 透過 debug probe 的高速 log 通道，不佔 UART | SWO / semihosting |
| `cargo-binutils` (`cargo size`, `cargo nm`, `cargo objdump`) | 看 section 大小、符號 | `arm-none-eabi-size` 等 |
| `cargo bloat` | **哪個函式吃掉我的 flash** | 沒有好對照，Rust 這邊比較好用 |
| `flip-link` | 把 stack 放到 RAM 最下面，overflow 會撞到未映射區而 fault | 手動加 guard page / canary |
| Miri | 在直譯器裡跑，抓 UB、unaligned access、data race | Valgrind + UBSan（但更嚴格） |
| `cargo careful` | 用 debug assertion 過的 std 跑測試 | `-D_GLIBCXX_ASSERTIONS` |
| `cargo clippy` | lint | `-Wall -Wextra` + 靜態分析 |

**`defmt` 值得多講兩句**（韌體上特別實用）：傳統 `printf("temp=%d\n", t)` 會把格式字串整包放進 flash，還要在 target 上跑格式化。`defmt` 把字串放進 ELF 的一個特殊 section（**不燒進 device**），target 只送出「第 37 號字串 + 參數 t」，host 端的 `defmt-print` 再組回來。省 flash、省頻寬、省 CPU——這正是韌體會在意的三件事。

**cross compile 常見指令**：
```bash
rustup target add thumbv7em-none-eabihf aarch64-unknown-none-softfloat
cargo build --release --target thumbv7em-none-eabihf
cargo size --release -- -A          # 各 section 大小
cargo bloat --release -n 20         # 最肥的 20 個函式
```
自訂 target（廠商 SoC 常見）：寫一份 target JSON，用 nightly 的 `-Z build-std=core,alloc` 自己編 `core`。

---

## 6. 容易被忽略但很關鍵的細節（雜項但高 CP 值）

- **`#[inline]` vs `#[inline(always)]`**：跨 crate inline 需要 `#[inline]`（或開 LTO）。ISR 裡的短函式標 `#[inline(always)]` 可以省掉呼叫開銷。
- **`core::hint::black_box`**：benchmark 時防止最佳化把你的程式碼刪光。
- **溢位行為**：debug build 溢位會 panic，release build 是 **wrapping**。韌體上要明確用 `wrapping_add` / `checked_add` / `saturating_add`，不要依賴預設。
- **`const fn`**：編譯期計算，可以用來算 baud rate divisor、查表，不佔執行期。
- **`#[non_exhaustive]`**：對外公開的 enum 加這個，之後新增變體不算 breaking change。做 SDK 時很重要。
- **Zero-sized types (ZST)**：`PhantomData`、空 struct 佔 0 bytes，`[ZST; 1000]` 也佔 0 bytes。typestate 的基礎。
- **`Drop` 在 `no_std` 一樣有效**，可以用來做「離開 scope 自動關中斷 / 自動 disable 周邊」的 RAII guard。
- **`build.rs`**：編譯期跑 Rust 程式，用來跑 `bindgen`、產生查表、把 git hash 塞進 binary。

---

## 7. 自我檢查題庫

### A. 語言基礎

**Q1. 解釋 ownership 的三條規則。**
> 每個值有唯一 owner；同時只能有一個 owner；owner 離開 scope 時值被 drop。這是純編譯期分析，沒有執行期成本。

**Q2. `&T` 和 `&mut T` 可以同時存在嗎？為什麼不行？**
> 不行。允許的話就有 aliasing——你透過 `&mut` 改了資料，持有 `&T` 的人看到的東西在他背後變了。這正是 iterator invalidation 和 data race 的根源。反過來說，因為保證了這件事，`&mut` 等於是編譯器驗證過的 `restrict` 指標，rustc 可以據此做更積極的最佳化。

**Q3. `String` 和 `&str` 差在哪？`Vec<T>` 和 `&[T]` 呢？**
> `String`/`Vec<T>` 是 owned、可增長、資料在 heap，本體是 (ptr, len, capacity)。`&str`/`&[T]` 是 borrowed view，(ptr, len) 的 fat pointer，不擁有資料。API 設計慣例：參數收 `&str`/`&[T]`（最泛用），回傳給 `String`/`Vec`（轉移所有權）。

**Q4. `Copy` 和 `Clone` 差在哪？**
> `Copy` 是 marker trait，代表「按位複製就是有效的複製」，賦值時是隱式 copy 而非 move。`Clone` 是顯式的 `.clone()`，可以做深拷貝。`Copy` 必須也是 `Clone`。有 `Drop` 的型別不能是 `Copy`（不然會 double drop）。

**Q5. `'static` 的兩種意思？** → 見 §2.3。

**Q6. `Box<dyn Error>` 和泛型 `E: Error` 怎麼選？**
> `Box<dyn Error>` 方便但要 heap，`no_std` 用不了。韌體上我會定義自己的 `enum Error { Timeout, Crc, Busy }`，實作 `core::fmt::Debug`，零配置。

### B. 進階 / soundness（區分「會用」和「懂」）

**Q7. `unsafe` 具體解鎖了哪五件事？它會關掉 borrow checker 嗎？**
> 見 §2.7。**強調「不會關掉 borrow checker」**——很多人以為會。

**Q8. 什麼是 safe abstraction？舉個例子。**
> 把 `unsafe` 封在模組內，對外只暴露不可能誤用的 API。`Vec` 內部全是裸指標操作，但 `vec[i]` 越界是 panic 不是 UB。embedded 的例子是 PAC：內部是 `write_volatile`，外部是 `.moder().bits(0b01)`，唯讀欄位連 `write` 方法都沒有。

**Q9. `Send` 和 `Sync` 的定義？`Rc` 為什麼不是 `Send`？**
> 見 §2.6。`Rc` 的引用計數是非原子的 `usize`，兩個執行緒同時 clone 會漏加，計數歸零過早 → use after free。

**Q10. 為什麼 `RefCell` 是 `Send` 但不是 `Sync`？**
> 整份搬到另一個執行緒是安全的（同時只有一個持有者）；但如果 `&RefCell` 被兩個執行緒共享，它的借用計數不是原子的，會 race。

**Q11. `Mutex<T>` 為什麼可以 `Sync`？**
> 因為它序列化了存取。`impl<T: Send> Sync for Mutex<T>`——只要 `T` 可以跨執行緒移動，`Mutex` 就能安全共享。注意條件是 `T: Send` 不是 `T: Sync`，因為 `Mutex` 保證同時只有一個執行緒看得到 `T`。

**Q12. 舉三種 Rust 的 UB。** → 見 §2.7。

**Q13. Rust 能保證不會有記憶體漏洞嗎？** → 見 §2.7 的追問，**不要說「會」**。

**Q14. memory leak 在 Rust 裡是 UB 嗎？**
> 不是。leak 是 **safe** 的——`mem::forget`、`Box::leak`、`Rc` 循環引用都能在 safe Rust 裡漏記憶體。Rust 保證的是「不會有 UB」，不是「不會漏」。這是常見的誤解。

**Q15. 什麼是單態化？它在韌體上的代價？** → 見 §2.4。

### C. 韌體專屬

**Q16. Rust 怎麼做 volatile MMIO？為什麼沒有 `volatile` 關鍵字？** → 見 §3.3。

**Q17. `volatile`、`atomic`、`memory barrier` 三者的差別？** → 見 §3.3。三者**很常被混為一談**。

**Q18. `no_std` 少了什麼？語言功能有少嗎？** → 見 §3.1。

**Q19. 沒有 heap 要怎麼寫程式？**
> `heapless` 的固定容量容器 + const generics + `static_cell`。API 設計上改成「呼叫端提供 buffer」：`fn parse<'a>(input: &'a [u8], out: &mut [u8]) -> Result<usize, Error>`。這其實跟寫嚴謹的 C 韌體是同一套思維。

**Q20. 描述 typestate pattern，並說明它的執行期成本。** → 見 §3.8。成本是**零**（`PhantomData` 是 ZST）。

**Q21. 怎麼在 ISR 和 main 之間安全共享周邊？** → 見 §3.5。重點在「critical section token 被編碼進函式簽章」。

**Q22. 韌體 panic 了要怎麼處理？** → 見 §3.7。

**Q23. DMA buffer 在 Rust 裡有什麼特別的問題？**
> 這是 Rust embedded 的**經典難題**：DMA 是「編譯器和 CPU 都看不見的第三方在改你的記憶體」。問題有三層——(a) 借用檢查：buffer 借給 DMA 期間，CPU 不能碰，所以要**把 buffer 的所有權 move 進 transfer object**，完成時再 move 回來（typestate + ownership 的組合技）；(b) `mem::forget` 問題：如果使用者 `forget` 掉 transfer object，Drop 不會跑，DMA 還在寫一塊已經被重用的 stack 記憶體——這是有名的 "leakpocalypse"，解法是要求 `'static` buffer 或用 closure-scoped API；(c) cache：Rust 不幫你做 cache maintenance，要自己 clean/invalidate 加 barrier。

**Q24. Cortex-M0 上為什麼 `AtomicU32::fetch_add` 不能用？** → 見 §2.8（無硬體 CAS，用 `portable-atomic`）。

**Q25. 怎麼量和控制 Rust 韌體的 flash size？**
> `opt-level = "z"` + `lto = true` + `codegen-units = 1` + `panic = "abort"`；用 `cargo size -A` 看 section、`cargo bloat` 找肥函式；常見肥源是**單態化過度**和**格式化機器（`core::fmt`）被拉進來**——後者用 `defmt` 取代 `write!` 可以省掉好幾 KB。

### D. 設計 / 決策題

**Q26. 你會怎麼在既有 C 韌體專案導入 Rust？** → 見 §4.4，**照那個五步驟走，並把風險講清楚**。

**Q27. 什麼情況下你會建議**不要**用 Rust？**
> 幾個真實的限制：(a) 廠商只提供 C BSP 且沒有 SVD 檔，PAC 要手刻，成本高；(b) 需要通過特定功能安全認證但預算不允許買認證 toolchain；(c) 團隊沒有任何 Rust 經驗且專案時程極緊——學習曲線在 borrow checker 這關是真的陡；(d) 目標架構 LLVM 不支援（某些 DSP、老 8-bit MCU）。

**Q28. Rust 讓你能做到什麼是 C 做不到的？**（這題比「Rust 比 C 安全」深一層）
> 三個具體的：(1) **typestate**——把周邊狀態機搬到編譯期，違規程式碼編不出來；(2) **critical section token**——把「必須在關中斷下呼叫」寫進型別；(3) **`embedded-hal` trait**——driver 跨廠商可攜，C 世界沒有等價物。這三個都是零成本抽象，不是安全檢查，是**表達力**。

**Q29. Rust 在 Linux kernel / Android 的現況？** → 見 §1。GPU / kernel driver 那條線的代表是 `nova`；Android 這邊則是 "new code in memory-safe languages" 策略和 `<20%` 那個數字。

**Q30. 怎麼確認自己真的會用？**
> 動手做，見 §10 的練手專案。只讀過 The Book 不等於會用。

---

## 8. 手寫練習

1. **實作一個 ring buffer（SPSC），`no_std`、固定容量。** 重點：const generics、`Option`、wrapping index、以及「怎麼讓 producer 和 consumer 分屬不同執行單元」（split 成兩個 half，各自持有一端）。
2. **把這段 C 的 register 存取改寫成 safe Rust API。** 重點：`read_volatile`、`unsafe` 收斂、bitfield 用 enum。
3. **這段程式碼為什麼編不過？** 通常是 borrow 在迴圈中延長、或者 move 之後又用。
4. **這段 `unsafe` 有什麼問題？** 通常是缺少對齊檢查、null 檢查、或者 `from_raw_parts` 的長度沒驗證。
5. **實作 `Drop` 讓周邊離開 scope 時自動關閉。** 重點：RAII guard、`Drop` 不能有回傳值也不能失敗。
6. **給定一個 struct，說出它的記憶體佈局和大小。** 重點：`repr(C)` vs `repr(Rust)`、padding、`Option<&T>` 的 niche optimization。

**寫 code 時的好習慣**：每個 `unsafe` 上面寫 `// SAFETY:`；錯誤路徑回 `Result` 不 panic；想清楚為什麼選這個型別。

---

## 9. 英文技術表達

**談動機**
> "The motivation isn't the language itself — it's eliminating an entire defect class. Memory safety accounted for the majority of high-severity CVEs in both Android and the kernel, and the industry consensus is to write *new* code in a memory-safe language rather than attempt a rewrite."

**談 unsafe**
> "`unsafe` doesn't disable the borrow checker. It unlocks five specific operations the compiler can't verify. What it really does is *shift the proof obligation* to me — so every `unsafe` block in my code carries a `SAFETY` comment stating the invariant I'm relying on. That's also the review convention in the kernel's Rust code."

**談 zero-cost abstraction**
> "Typestate is my favourite example. Encoding pin direction in the type parameter means calling `set_high()` on an input pin isn't a runtime error — the method simply doesn't exist. And because `PhantomData` is a zero-sized type, the binary is byte-for-byte identical to the hand-written version."

**談限制（誠實 = 可信）**
> "Rust doesn't eliminate memory bugs — it *shrinks the attack surface* to `unsafe` blocks and FFI boundaries. On a project with a large C BSP, most of the risk still lives at that boundary, so that's where I'd focus review effort."

**談導入策略**
> "I'd start with a leaf module with a high attack surface — a parser or protocol handler — generate bindings with `bindgen`, build it as a staticlib, and link it into the existing build. Wrap the FFI in a thin safe layer so the business logic above it is entirely safe Rust. Then measure the flash and RAM delta before proposing anything wider."
---

## 10. 兩週學習計畫 + 練手專案

### 兩週計畫（每天 1.5–2 小時）

| 天 | 內容 |
|---|---|
| 1–2 | Ownership / borrow / lifetime。做 [Rustlings](https://github.com/rust-lang/rustlings) 的 ownership + lifetimes 章節 |
| 3–4 | Trait / 泛型 / `dyn`。手刻一個 trait + 兩種實作，用 `cargo bloat` 比較靜態 vs 動態派送的 size |
| 5 | `Result` / `Option` / 錯誤設計。寫一個 `no_std` 的 enum error 型別 |
| 6–7 | **Rustonomicon**：`unsafe`、UB、FFI 三章。這是投報率最高的兩天 |
| 8–9 | Embedded Rust Book + Discovery Book。建一個 `no_std` blinky，跑起來 |
| 10 | Typestate：自己刻一個 `Pin<Input>` / `Pin<Output>` |
| 11 | FFI：用 `bindgen` 包一個 C 函式庫，`cbindgen` 反向匯出一個函式 |
| 12 | 工具：`defmt` + `probe-rs` 跑一次、`cargo size` / `bloat` 看一次、`miri` 跑一次 |
| 13 | 讀 `nova-core` 或任一 Rust kernel driver 的原始碼，能講出它怎麼包 `unsafe` |
| 14 | 把 §7 的三十題自己寫下答案，再回頭對照官方文件查證 |

### 練手專案（挑一個做）

這幾個練習依實用價值排序：

1. **把某個既有的 C 工具重寫成 Rust，並量化差異**。例如一個 log parser，量 throughput 和記憶體，驗證「同樣的邏輯，少了一整類 bug，效能持平或更好」。**這個最容易上手**。
2. **在 QEMU 上跑一個 `no_std` aarch64 bare-metal 程式**：印字串到 PL011 UART、設一個 timer 中斷。不用買板子，`qemu-system-aarch64 -M virt` 就能跑。這是 SoC BSP bring-up 最基本的起點。
3. **用 `bindgen` 包一個既有的 C 韌體函式庫，做出 safe wrapper**。這是「漸進導入」的實際演練，比純 Rust 專案更貼近真實專案。
4. **對某個開源 Rust embedded crate 送一個小 PR**（文件、測試、一個 driver 的 bug fix）。能拿到上游 review 的回饋。

---

## 11. 參考資源（照這個順序讀）

| 資源 | 為什麼讀 |
|---|---|
| [The Rust Book](https://doc.rust-lang.org/book/) | 基礎，第 4/10/15/16 章最重要 |
| [Rust by Example](https://doc.rust-lang.org/rust-by-example/) | 快速查語法 |
| **[The Rustonomicon](https://doc.rust-lang.org/nomicon/)** | **投報率最高**：`unsafe`、UB、FFI、variance |
| [The Embedded Rust Book](https://docs.rust-embedded.org/book/) | `no_std`、PAC/HAL、concurrency |
| [Discovery Book](https://docs.rust-embedded.org/discovery/) | 動手做，有板子的話 |
| [Embedonomicon](https://docs.rust-embedded.org/embedonomicon/) | 從零建 `#![no_std]` runtime，講 linker、`.vector_table`、記憶體佈局 |
| [Rust for Linux 文件](https://docs.kernel.org/rust/) | 做 kernel / driver 的話必讀 |
| [nova driver 文件](https://docs.kernel.org/gpu/nova/index.html) | **目前最完整的 Rust kernel driver 範例** |
| [Android Rust / memory safety](https://source.android.com/docs/security/test/memory-safety) | **大規模導入的第一手數據** |
| [Rust Atomics and Locks](https://marabos.nl/atomics/) (Mara Bos, 免費線上) | 並行、`Send`/`Sync`、memory ordering 講得最清楚 |
| [Rust Embedded Blog](https://blog.rust-embedded.org/) | 生態現況 |

---

## 附錄：速查表

**Cheat sheet — 一分鐘複習**

```
所有權   唯一 owner，move 是預設，drop 自動，零執行期成本
借用     N 個 &T 或 1 個 &mut T，二選一。&mut ≡ 編譯器驗證過的 restrict
生命週期 保證引用不比資料活久。'static 有兩個意思（引用 / bound）
Trait    靜態派送 = 快但胖；dyn = 省 flash 但有間接呼叫
錯誤     Result + ? 取代 errno；panic 給 invariant 違反
Send     可跨執行單元移動          Sync   &T 可跨執行單元共享
unsafe   解鎖五件事，不關 borrow checker，義務轉移，寫 SAFETY 註解
no_std   少 OS 相關功能，語言功能一個沒少
MMIO     read_volatile/write_volatile，不是關鍵字，volatile ≠ barrier ≠ atomic
臨界區   critical_section::with → token → Mutex::borrow(cs)
typestate 狀態進型別參數，PhantomData 是 ZST，零成本
FFI      #[repr(C)]、unsafe extern "C"、Option<&T> 是 null-optimized
size     opt-level="z" + lto + codegen-units=1 + panic="abort" + defmt
```

**重點回顧**
1. `unsafe` 不關 borrow checker，解鎖五件事 → 義務轉移 → SAFETY 註解
2. volatile 只管編譯器；barrier 管 CPU；atomic 管不可分割性
3. Send / Sync 在 bare-metal 上管的是 ISR，不只是 thread
4. typestate 是零成本，因為 `PhantomData` 是 ZST
5. Rust **不保證**沒漏洞，它把攻擊面收斂到 `unsafe` 和 FFI
6. 導入策略：葉節點模組 → bindgen → staticlib → safe wrapper → 量 size
7. kernel driver 這條線看 `nova`；大規模導入看 Android 的 new-code-in-Rust 策略
