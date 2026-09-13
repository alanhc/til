---
sidebar_label: 環形緩衝區 Circular Buffer
---

# 環形緩衝區（Circular Buffer / Ring Buffer）

**環形緩衝區（Circular Buffer，又叫 Ring Buffer）** 是一段固定大小的陣列，配上「頭尾指標繞圈回頭」的規則，用來實作一個 FIFO（先進先出）佇列。它是嵌入式 / 韌體世界裡最重要的資料結構之一——UART 收發、DMA、log 系統幾乎都靠它。

這篇用 **C**，因為它幾乎只活在 C 的世界。而且要先講清楚一件事：**這題在嵌入式面試幾乎必問，但在純軟體的 LeetCode 題庫裡卻很少見**（LeetCode 622「Design Circular Queue」是少數）。原因是它的難點不在演算法複雜度，而在「full/empty 怎麼分」「並行下怎麼免鎖」這些貼著硬體的細節——這正是韌體面試想篩的東西。

## 為什麼要 ring buffer

想像 UART 中斷來了一個 byte，你得先存起來，等主程式有空再處理。這種「生產者一直塞、消費者慢慢拿」的場景需要一個佇列。但在韌體上你不能用會動態 `malloc` 的普通佇列，原因是：

- **固定記憶體**：嵌入式系統記憶體有限、且忌諱在執行期做動態配置（碎片化、不確定的延遲）。ring buffer 開機時配好一塊固定陣列，之後不再要求記憶體。
- **FIFO 語意**：資料的順序要保持，先進的先被處理。
- **producer / consumer 解耦**：中斷（producer）和主迴圈（consumer）各跑各的，用 ring buffer 當中間的緩衝，速度不匹配時也不會掉資料（除非滿了）。
- **O(1) 的存取**：push / pop 都是常數時間，不搬移資料，只動指標。

核心結構是一塊陣列加上兩個索引：

- **head（或 write index）**：producer 下次要寫入的位置。
- **tail（或 read index）**：consumer 下次要讀取的位置。

每次寫入，head 前進一格；每次讀取，tail 前進一格。走到陣列尾端就繞回開頭（取模），這就是「環形」的由來。

```
       陣列（size = 8）
   索引:  0   1   2   3   4   5   6   7
        ┌───┬───┬───┬───┬───┬───┬───┬───┐
        │   │ B │ C │ D │   │   │   │   │
        └───┴───┴───┴───┴───┴───┴───┴───┘
              ▲           ▲
             tail        head
          （下個讀）    （下個寫）
```

## Full 還是 Empty？經典難題

這是 ring buffer 唯一真正的難點，也是面試最愛追問的地方。

當 `head == tail` 時，緩衝區是**空的**（沒東西可讀）。但問題來了：當你一直寫，寫到 head 繞一整圈追上 tail，這時 `head == tail` 又成立了——可是這代表**滿的**。同一個條件 `head == tail`，卻同時代表空和滿，無法區分。

有兩種經典解法：

### 解法 A：犧牲一格不用

規定「當 head 再前進一格就會等於 tail 時，就算滿了」。也就是永遠留一個空格不裝資料，讓「滿」和「空」的指標狀態不會撞在一起：

- 空：`head == tail`
- 滿：`(head + 1) % size == tail`

代價是 `size` 個格子只能裝 `size - 1` 筆資料。優點是實作極簡單、不需要額外變數，而且在單生產單消費（SPSC）下天然免鎖——這是它最大的價值，後面會講。

### 解法 B：另存一個 count

多維護一個 `count` 記錄目前有幾筆資料：

- 空：`count == 0`
- 滿：`count == size`

優點是 `size` 個格子全都能用，容量不浪費，而且判斷直覺。缺點是 `count` 這個變數會同時被 producer（寫時 +1）和 consumer（讀時 -1）修改——在有中斷或多執行緒的環境下，`count` 就成了共享狀態，需要保護（關中斷或用 atomic），反而破壞了「SPSC 免鎖」的美好性質。

**面試回答的框架**：先講清楚「`head == tail` 有歧義」這個核心矛盾，再說兩種解法各自的取捨——A 省一格但換來 SPSC 免鎖，B 不浪費容量但引入共享的 `count`。能講出這層 trade-off，比只寫出 code 更能過關。

## 用 `& (size - 1)` 取代取模

前面用了 `% size` 來繞回。但取模（除法）在很多嵌入式 MCU 上很慢，甚至沒有硬體除法器。**如果把 `size` 設成 2 的次方**，就能用位元 AND 取代取模：

```c
/* 當 SIZE 是 2 的次方時，這兩者等價，但 & 快得多 */
index = (index + 1) % SIZE;
index = (index + 1) & (SIZE - 1);
```

原理：2 的次方 `SIZE` 減 1 後，低位全是 1（例如 `SIZE = 8` → `SIZE - 1 = 0b0111`）。任何數 `& 0b0111` 就是「只保留低 3 位」，效果等同對 8 取模，但只花一個 AND 指令。這也是為什麼幾乎所有正式的 ring buffer 實作都強制 buffer 大小是 2 的次方。

（位元運算的細節可參考另一篇「位元運算 Bit Manipulation」。）

## SPSC 為什麼能免鎖

**SPSC = Single Producer, Single Consumer**，只有一個生產者、一個消費者。這是韌體最常見的組態：UART 接收中斷是唯一的 producer，主迴圈是唯一的 consumer。

在 SPSC + 「解法 A（留一格）」下，可以**不用鎖、不用關中斷**，原因是責任分得很乾淨：

- 只有 producer 會**修改** `head`，consumer 只**讀** `head`。
- 只有 consumer 會**修改** `tail`，producer 只**讀** `tail`。

沒有任何一個變數被兩邊同時寫，就沒有 race condition。producer 寫完資料再更新 `head`，consumer 看到 `head` 變了才會去讀新資料——只要「先寫資料、後更新 head」這個順序被保證，就是安全的。這是 ring buffer 在中斷驅動的韌體裡如此受歡迎的根本原因。

（對比之下，解法 B 的 `count` 兩邊都要改，就享受不到這個免鎖特性。）

### memory barrier 的概念（點到為止）

上面說「先寫資料、後更新 head」，但這個順序有個隱藏的敵人：**編譯器和 CPU 可能會重排指令**。編譯器最佳化或 CPU 的 out-of-order execution 可能讓「更新 head」跑到「寫入資料」之前——這樣 consumer 就會讀到還沒寫好的髒資料。

解法是插入 **memory barrier（記憶體屏障）**，強制「屏障之前的寫入」在「屏障之後的寫入」之前對另一方可見：

- producer：寫完資料 → **write barrier** → 再更新 `head`。
- consumer：讀到 `head` → **read barrier** → 再讀資料。

在單核心、只有中斷的簡單場景，通常只需要「編譯器屏障」（避免編譯器重排），例如把索引宣告成 `volatile` 或用 GCC 的 `__sync_synchronize()` / C11 的 `atomic_thread_fence`。在多核心（如多核 SoC）就需要真正的硬體 memory barrier 指令（ARM 的 `DMB` 等）。這是很深的主題，面試能點出「需要 barrier、單核多核要求不同」就足夠展現深度。

## Firmware 應用

- **UART RX / TX**：接收中斷每來一個 byte 就 push 進 RX ring buffer，主程式再慢慢 pop 處理；傳送則相反，主程式 push 進 TX ring buffer，TX 中斷（或 DMA）逐一取出送出。這是 ring buffer 最經典的用途。
- **DMA**：很多 DMA 控制器支援「circular mode」，硬體自動把資料連續搬進一塊環形記憶體並繞回，軟體只要追著讀。ADC 連續取樣、音訊串流常這樣做。
- **log ring buffer**：把最近 N 筆 log 存在固定大小的環形緩衝，滿了就覆蓋最舊的。系統崩潰後可以 dump 出這塊記憶體看「死前最後發生什麼」。Linux kernel 的 `printk` ring buffer（`dmesg` 看到的東西）就是這個概念。

## 完整 C 實作

用「解法 A（留一格）+ 2 的次方大小 + `& (size-1)`」，這是韌體最實用的組合：

```c
#include <stdint.h>
#include <stdbool.h>
#include <stddef.h>

#define RB_SIZE 256                 /* 必須是 2 的次方 */
#define RB_MASK (RB_SIZE - 1)

typedef struct {
    uint8_t buffer[RB_SIZE];
    volatile size_t head;           /* 只有 producer 寫 */
    volatile size_t tail;           /* 只有 consumer 寫 */
} ring_buffer_t;

void rb_init(ring_buffer_t *rb) {
    rb->head = 0;
    rb->tail = 0;
}

/* 空：head == tail */
bool rb_is_empty(const ring_buffer_t *rb) {
    return rb->head == rb->tail;
}

/* 滿：再寫一格 head 就會撞上 tail（留一格不用） */
bool rb_is_full(const ring_buffer_t *rb) {
    return ((rb->head + 1) & RB_MASK) == rb->tail;
}

/* 目前資料筆數 */
size_t rb_count(const ring_buffer_t *rb) {
    return (rb->head - rb->tail) & RB_MASK;
}

/* producer 呼叫：寫入一個 byte，成功回 true，滿了回 false */
bool rb_push(ring_buffer_t *rb, uint8_t data) {
    size_t next = (rb->head + 1) & RB_MASK;
    if (next == rb->tail)           /* 滿了，不覆蓋 */
        return false;
    rb->buffer[rb->head] = data;    /* 先寫資料 */
    /* 這裡在多核心下需要 write barrier，確保上一行先完成 */
    rb->head = next;                /* 後更新 head，consumer 才會看到 */
    return true;
}

/* consumer 呼叫：讀出一個 byte 到 *out，成功回 true，空了回 false */
bool rb_pop(ring_buffer_t *rb, uint8_t *out) {
    if (rb->head == rb->tail)       /* 空了 */
        return false;
    *out = rb->buffer[rb->tail];    /* 先讀資料 */
    /* 這裡在多核心下需要 read/write barrier */
    rb->tail = (rb->tail + 1) & RB_MASK;   /* 後更新 tail */
    return true;
}
```

幾個實作重點：

- `rb_count` 用 `(head - tail) & MASK` 一行搞定「跨越繞回邊界」的筆數計算，不需要 if 判斷 head 是否已經繞回——這也是 2 的次方大小帶來的另一個便利。
- `head`、`tail` 宣告成 `volatile`，是最起碼的手段，防止編譯器把「另一方會改的變數」快取在暫存器裡而看不到更新。嚴謹的多核程式要進一步用 C11 `stdatomic.h` 的 atomic 型別配合明確的 memory order。
- `rb_push` 選擇「滿了就回 false 不覆蓋」。log buffer 則常反過來——滿了就推進 tail 覆蓋最舊資料，這是另一種設計選擇，看需求決定。

## 面試角度

- **這是嵌入式面試的高頻必考題**。被要求「手寫一個 ring buffer」時，主考官真正在看的是：你能不能講清楚 full/empty 的歧義與解法、知不知道 2 的次方大小的 `& (size-1)` 技巧、懂不懂 SPSC 免鎖與 memory barrier。把 code 寫出來只是及格，講出這些取捨才是加分。
- **常見追問**：「如果 buffer 滿了怎麼辦？」（回 false / 覆蓋舊資料，看場景）、「多個 producer 怎麼辦？」（就不再是 SPSC，需要鎖或 lock-free 的 CAS 手法）、「怎麼保證中斷和主程式不打架？」（SPSC 責任分離 + barrier，或關中斷）。
- **純軟體題庫少見**：LeetCode 上對應的是 **622. Design Circular Queue** 和 **641. Design Circular Deque**，但它們只考「介面正確」，不碰並行與 barrier。真正的深度在硬體場景，這也是為什麼它是「韌體人才篩選器」——會 LeetCode 不代表會這題。
