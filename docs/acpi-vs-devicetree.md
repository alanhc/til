# ACPI 與 Device Tree 到底差在哪:從「kernel 怎麼知道板子上有什麼」講起

> 本文為入門導向,假設你寫過應用層程式、大致知道 driver 是什麼,但沒實際碰過開機階段的硬體描述。所有範例與引用皆來自公開規格與 mainline kernel 文件,文末附完整出處。

---

## 一、先問一個更根本的問題

你的筆電開機時,Linux 怎麼知道機器上有一顆觸控板?

直覺的答案是「driver 去掃啊」。這個直覺在某些情況下是對的,在某些情況下完全行不通,而這個分界線,正是 ACPI 與 Device Tree 存在的全部理由。

### 會自我介紹的硬體

PCIe 和 USB 是「可列舉」(discoverable / enumerable)的匯流排。它們的規格裡明文定義了一套自我描述機制:

- **PCIe** 每個裝置都有一塊標準化的 configuration space,固定的 offset 0x00 是 Vendor ID,0x02 是 Device ID,還有 class code、BAR(Base Address Register)告訴你它要多少記憶體空間。OS 只要照著規矩把匯流排走一遍,就能問出「這裡有一顆 vendor 0x8086、device 0x1234 的網卡,它需要 128KB 的 MMIO 空間」。
- **USB** 更直白,裝置插上去之後,host 送一個 GET_DESCRIPTOR 請求,裝置就回一份 device descriptor,裡面有 VID/PID、class、endpoint 配置。

所以在這兩種匯流排上,「掃描」是可行的。Linux 的 `lspci`、`lsusb` 就是在讀這些自述資料。硬體自己會講話,OS 只要會聽就好。

### 不會自我介紹的硬體

問題出在其他地方。板子上絕大多數的東西根本不在 PCIe 或 USB 上:

- 掛在 **I2C** 上的觸控 IC、電源管理晶片、感測器
- 掛在 **SPI** 上的 NOR flash、螢幕
- 直接接在 SoC 內部匯流排上的 **memory-mapped** 週邊 —— UART、GPIO controller、DMA controller、中斷控制器、時鐘控制器

這些東西沒有任何自述機制。一顆 I2C 裝置只有一個 7-bit 位址(0x00–0x7F,實際可用更少),它不會告訴你它是誰。你對 0x38 送一個 read,它可能回你資料,也可能因為你送錯指令而鎖死。你不能亂掃 —— 掃 I2C 匯流排是有副作用的,某些晶片會被特定的 bit pattern 觸發進入奇怪的狀態。

Memory-mapped 的裝置更慘。UART 的暫存器在 0x0900_0000 還是 0x1c02_0000?中斷接到 SPI 33 還是 SPI 74?沒有任何辦法從硬體「問」出來。這些是板子設計者拍板的事實,只存在於電路圖裡。

### 三個時代的三種答案

於是問題變成:**這些「只存在於電路圖裡的事實」,要用什麼方式告訴 OS?**

歷史上有三種答案:

1. **寫死在 OS 裡。** 早期 ARM Linux 的做法,每塊板子一個 C 檔案,叫 board file。`arch/arm/mach-omap2/board-omap3beagle.c` 這種。裡面用 C 結構體宣告板上有哪些裝置、位址多少,然後 `platform_device_register()` 一個個註冊。
2. **Device Tree(DT)。** 把那些事實抽出來變成一份純資料檔,跟 kernel binary 分開。
3. **ACPI。** 把那些事實 *加上操作它們的程式碼* 一起放進 firmware,OS 執行 firmware 提供的方法。

第一種為什麼被淘汰,是理解後面兩種的關鍵。

### board file 為什麼會爆炸

ARM 的商業模式是授權 IP,SoC 廠商拿去自己搭配週邊、自己畫板子。結果就是 LWN 上這句對 ARM 生態的描述:

> "ARM specifies the instruction set and CPU behavior... Details beyond the CPU are largely left up to the individual manufacturer. There are no standard components, and no required BIOS."

x86 世界有 IBM PC 相容的歷史包袱當作事實標準 —— PIC 在 0x20、UART 在 0x3F8、有 BIOS 幫你把事情做好。ARM 沒有。每一塊板子都是全新的宇宙。

2011 年前後,`arch/arm/` 底下的 board file 數量失控,每支援一塊新板子就要往 mainline 塞一個新的 C 檔案,而且這些檔案彼此高度重複又互不相容。維護者要 review 的不是「這段程式有沒有 bug」,而是「這塊我永遠看不到的板子上,UART 是不是真的在這個位址」。這件事根本無法 review,也無法測試。

Device Tree 的核心洞見就是:**這些不是程式,是資料。** 資料就該用資料的方式表達,不該編進 kernel binary 裡。用 LWN 那篇文章的話說,device tree 的好處之一是「much less clutter in the platform description as you cannot include code」—— 你**沒辦法**在裡面塞程式碼,這是特性不是限制。

---

## 二、Device Tree:把板子畫成一棵樹

### 血統

Device Tree 不是 Linux 發明的。它的祖先是 **Open Firmware(IEEE 1275)**,1990 年代 Sun 和 Apple 用的開機韌體標準。SPARC 和 PowerPC 的機器上,firmware 會把硬體描述成一棵樹交給 OS。Linux 的 PowerPC port 沿用了這套機制,ARM 在 2011 年前後的大整併中把它借了過來,現在 RISC-V、MIPS、部分 x86 embedded 也在用。

現在的正式規格由 devicetree.org 維護,最新釋出版本是 **Devicetree Specification v0.4**(2023 年 6 月 28 日)。

### 資料模型:node 與 property

Device Tree 是一棵樹,每個節點(node)代表一個裝置或一個邏輯分組,每個節點底下有一堆屬性(property),就是 key-value pair。value 的型別很簡單:32-bit 整數陣列、字串、字串陣列、byte array,或是空的(表示 boolean true)。

一份最小可用的例子,描述一顆掛在 I2C bus 1 上、位址 0x38 的觸控 IC:

```dts
&i2c1 {
    status = "okay";
    clock-frequency = <400000>;

    touchscreen@38 {
        compatible = "edt,edt-ft5406";
        reg = <0x38>;
        interrupt-parent = <&gpio2>;
        interrupts = <5 IRQ_TYPE_EDGE_FALLING>;
        reset-gpios = <&gpio2 6 GPIO_ACTIVE_LOW>;
        vcc-supply = <&reg_3v3>;
        touchscreen-size-x = <1024>;
        touchscreen-size-y = <600>;
    };
};
```

逐行拆解:

- **`touchscreen@38`** —— 節點名稱。`@` 後面是 unit address,慣例上要跟 `reg` 的第一個值一致。它主要是給人看的、也是 `dtc` 一致性檢查的依據,但 kernel 配對 driver 時不看它。
- **`compatible = "edt,edt-ft5406"`** —— 最重要的一個屬性。它是「這是什麼東西」的字串識別碼,格式是 `廠商前綴,型號`。Kernel driver 會宣告一張 `of_device_id` 表,裡面列出自己支援哪些 compatible 字串,配對成功就 probe 起來。它可以是一個字串陣列,由具體到通用排列,例如 `compatible = "acme,widget-v2", "acme,widget"`,讓只認得舊型號的 driver 也能接手。
- **`reg = <0x38>`** —— 裝置在父匯流排上的位址。在 I2C node 底下,它是 slave address;在 memory-mapped 的 node 底下,它是 `<起始位址 長度>`,而且要幾個 cell 表示,由父節點的 `#address-cells` / `#size-cells` 決定。這是 DT 初學者最容易撞牆的地方 —— `reg` 的語意完全依賴上下文。
- **`interrupt-parent = <&gpio2>` + `interrupts = <5 ...>`** —— 中斷接到哪。`&gpio2` 是一個 **phandle**,DT 裡的「指標」,指向另一個節點。編譯後它會變成一個整數 ID。
- **`reset-gpios`、`vcc-supply`** —— 這兩個是資源引用。它們告訴 driver「你要拉的 reset 腳在 gpio2 的第 6 隻,active low」「你的電源來自 reg_3v3 這個 regulator」。注意這裡只是**指出資源在哪**,至於「開機時要先給電再放開 reset,中間等 5ms」這個 **順序與時序**,DT 完全沒有講 —— 那寫在 driver 裡。**記住這一點,它是後面對比 ACPI 的關鍵。**
- **`touchscreen-size-x`** —— 純粹的組態參數。

### 從文字到 kernel 的一生

```
foo.dts  ──(C preprocessor)──▶  foo.dts.tmp
         ──(dtc 編譯)────────▶  foo.dtb        (Flattened Device Tree, FDT)
         ──(bootloader 載入)──▶  記憶體中,位址放進 r2/x0
         ──(kernel unflatten)─▶  記憶體中的 device_node 樹
         ──(of_platform_populate)▶ 一堆 struct platform_device
         ──(driver match)─────▶  probe()
```

幾個值得注意的環節:

- **`.dts` 會先過 C preprocessor。** 所以你可以 `#include <dt-bindings/interrupt-controller/irq.h>`,用 `IRQ_TYPE_EDGE_FALLING` 這種名字而不是裸數字。這也是為什麼 `.dtsi`(include 檔)可以層層堆疊 —— SoC 廠出 `mt8195.dtsi`,板廠 include 它再加上自己的東西。
- **`dtc` 檢查得了格式,檢查不了事實。** 它其實有一組內建檢查(`unit_address_vs_reg`、`simple_bus_reg`、`interrupts_property` 等),會抓出 unit address 與 `reg` 不一致這類問題。但它無從得知你填的位址對不對 —— 你把 UART 的 base address 寫成隔壁那顆的,`dtc` 不會有意見。近年 kernel 加入了以 YAML 撰寫的 binding schema(`Documentation/devicetree/bindings/**/*.yaml`),搭配 `make dt_binding_check` / `make dtbs_check` 可以做 schema 驗證,但這是編譯期的事,跟執行期無關。
- **bootloader 有機會動手腳。** 它可以在把 DTB 交給 kernel 之前修改內容 —— 填入實際偵測到的 RAM 大小、序號、螢幕面板 ID。這是 DT 唯一的「動態」成分,而且動態的是 bootloader,不是 DT 本身。

### Overlay:Android 的做法

一份 DTB 描述一塊板子。但同一顆 SoC 會出很多變體 —— 不同的面板、不同的 camera 模組、不同的 SKU。全部寫死在一份 DTB 裡會爆炸,所以有了 **overlay**。

Android 的架構(DTO,Device Tree Overlay)是這樣:主 DTB 描述 SoC 共通的部分,放在 `boot`(或 `dtb`)分割區;各種變體的差異寫成 overlay,編成 `.dtbo` 放在專屬的 **`dtbo` 分割區**。Bootloader 開機時讀出主 DTB,依照偵測到的板子型號挑選對應的 overlay 疊上去,合併成一份完整的 DTB 再交給 kernel。

Android 官方文件的描述:

> "A device tree overlay (DTO) enables a central DTB to be overlaid on the DT (a device tree blob for overlay (DTBO))."

同一頁另外說明了 overlay 能做什麼:「adding nodes to the tree and making changes to properties in the existing tree」。

Overlay 可以新增節點、也可以覆寫既有節點的屬性 —— 這代表「最終 kernel 看到的 DT」跟「你在 source tree 裡讀到的那份 dts」可能長得不一樣。整合階段的很多疑難雜症就出在這裡。

Android 9 起還規定 bootloader 在合併完之後不得再自行修改 DTO 的屬性,把責任邊界劃清楚。

### Binding 是什麼,為什麼它是 ABI

一份 DT 裡寫 `touchscreen-size-x`,driver 裡就要去讀 `touchscreen-size-x`。這個「屬性叫什麼名字、什麼型別、什麼意思」的約定,就叫 **binding**。Binding 文件放在 kernel 的 `Documentation/devicetree/bindings/` 底下,新增或修改 binding 要經過 device tree maintainer review。

重點來了:**binding 被視為 ABI**。因為 DTB 可能被燒進裝置的某個分割區,或是存在你買不到的 bootloader 裡,使用者升級 kernel 時不會一起換掉。所以 kernel 文件的原則是:

> "Certainly a stable binding means that a newer kernel will not break on an older device tree, but that doesn't mean the binding is frozen for all time."

但這不代表 binding 永遠凍結。文件也說明了演進的方式:

> "For instance, if a new property is added, then default to the previous behaviour if it is missing. If a binding truly needs an incompatible change, then change the compatible string at the same time."

(這段文字在 kernel 文件中標明引自 2013 年 ARM mini-summit 的討論摘要,並非文件本身的原創論述。)

翻成白話:**只能加,不能改語意;真的要破壞相容性,就換一個 compatible 字串,當作新裝置處理。** 這條規則解釋了為什麼 kernel 裡會看到 `"acme,widget"`、`"acme,widget-v2"`、`"acme,widget-v2a"` 這種看起來很囉唆的字串家族。

### 再深一層:provider–consumer 模型

前面那份 dts 裡有兩行值得單獨拿出來講:

```dts
reset-gpios = <&gpio2 6 GPIO_ACTIVE_LOW>;
vcc-supply = <&reg_3v3>;
```

這是 DT 最核心也最容易讓初學者卡住的設計 —— **provider–consumer 模型**。

板子上有一些「提供資源的東西」:GPIO controller 提供腳位、clock controller 提供時脈、regulator 提供電源、pin controller 提供腳位功能切換、中斷控制器提供中斷線。它們在 DT 裡各自是一個節點,叫 **provider**。其他裝置需要這些資源時,用 phandle 指過去,叫 **consumer**。

Provider 節點會宣告「引用我需要幾個參數」:

```dts
gpio2: gpio@11002000 {
    compatible = "acme,soc-gpio";
    reg = <0x11002000 0x1000>;
    gpio-controller;
    #gpio-cells = <2>;        // 引用我要帶 2 個 cell:腳位編號 + flags
    interrupt-controller;
    #interrupt-cells = <2>;
};

clk26m: clock-26m {
    compatible = "fixed-clock";
    #clock-cells = <0>;       // 我只有一個輸出,引用時不用帶參數
    clock-frequency = <26000000>;
};

topckgen: clock-controller@10000000 {
    compatible = "acme,soc-topckgen";
    reg = <0x10000000 0x1000>;
    #clock-cells = <1>;       // 我有很多輸出,引用時要帶 index
};
```

所以 `<&gpio2 6 GPIO_ACTIVE_LOW>` 是「gpio2 這個 provider、第 6 隻腳、active low」,而 `<&topckgen CLK_UART0>` 是「topckgen 的第 CLK_UART0 號時脈」。`#gpio-cells`、`#clock-cells` 這些 `#xxx-cells` 屬性,就是在定義引用時的參數個數。

理解這件事,DT 裡九成的語法就通了。`clocks` / `resets` / `dmas` / `phys` / `power-domains` / `pinctrl-0` 全都是同一個模式。它也解釋了兩個常見現象:

- **`-EPROBE_DEFER` 為什麼那麼常見。** Consumer 先於 provider 被 probe 是很正常的事(DT 的節點順序不代表 probe 順序),此時 consumer 拿不到資源,回傳 `-EPROBE_DEFER`,kernel 之後會重試。整條依賴鏈就是這樣自然收斂的。如果某個裝置一直卡在 defer,通常代表它依賴的 provider 根本沒 probe 成功 —— 往上游追,不要在 consumer 裡繞。
- **為什麼 dts 常常要跨檔案改。** 你要開一顆新的 I2C 裝置,可能得同時碰觸 pinctrl 節點(把腳位切成 I2C 功能)、regulator 節點(確保電源存在)、以及裝置本身。這三件事在三個不同的 `.dtsi` 裡。

**現在把這一整套拿去跟 ACPI 對照。** ACPI 裡沒有等價的 provider–consumer 圖。`_CRS` 直接給你一個「已經可以用的資源」,`_PS0` 直接把電源與 reset 處理完。時脈?ACPI 幾乎不描述時脈樹 —— 因為 firmware 已經把該開的時脈開好了,OS 不需要知道那棵樹長什麼樣。Pin mux?同理,firmware 在 OS 拿到控制權之前就設定完畢。

這是兩者哲學差異最具體的體現:**DT 把整塊板子的依賴關係攤開給 OS,要求 OS 自己按正確順序組裝;ACPI 把組裝好的結果交給 OS,只留下必要的操作介面。** DT 的作法更透明也更靈活(你能精細控制每一顆時脈的開關來省電),代價是 kernel 要背負整棵依賴樹的知識;ACPI 的作法更省事,代價是那些細節你看不到也調不了。

### DT 明確不做的事

DT 沒有迴圈、沒有判斷、沒有函式呼叫。它就是一份資料。這句話值得再說一次,因為它是整篇文章的分水嶺:

**在 DT 世界裡,「怎麼操作這顆硬體」的知識,100% 住在 kernel driver 裡。**

DT 說「reset 腳是 gpio2 pin 6」,driver 說「拉低 10ms 再放開,然後等 300ms 才能發第一個 I2C command」。前者是資料,後者是程式,兩者必須版本相符。你把新的 dts 配上舊的 kernel,可能就是不會動。

---

## 三、ACPI:把板子寫成一支可以被呼叫的程式

### 血統

ACPI(Advanced Configuration and Power Interface)1996 年由 Intel、Microsoft、Toshiba 提出,取代當時的 APM(Advanced Power Management)和 PnP BIOS。

它的原始動機跟 DT 其實不同。APM 時代,省電邏輯全在 BIOS 裡,OS 只能說「我要睡了」然後把控制權交出去,發生什麼事 OS 一無所知,也無從介入。ACPI 的 "OS-directed" 精神是把**決策權**交還給 OS —— 由 OS 決定什麼時候讓誰進入哪個省電狀態,而 firmware 提供**執行那個決策的方法**。

「描述有什麼硬體」在 ACPI 裡反而是附帶的能力。這個出身差異解釋了它為什麼長成現在這樣。

最新版本是 **ACPI 6.6**(2025 年 5 月釋出),由 UEFI Forum 維護。

### 資料模型:一堆表格,加上一個直譯器

ACPI 給 OS 的東西是一組**表格**,從一個叫 RSDP 的錨點開始串起來:

```
RSDP  (Root System Description Pointer)   ← UEFI 從 config table 交給 OS
  └─ XSDT (Extended System Description Table)  ← 一張指標陣列,指向下面所有表
       ├─ FADT (Fixed ACPI Description Table)  ← 固定暫存器位置、電源相關參數
       │    └─ DSDT (Differentiated System Description Table)  ★ 主要的裝置描述
       │         ↑ 注意:DSDT 不是 XSDT 的項目,只能透過 FADT 的 DSDT/X_DSDT 欄位抵達
       ├─ SSDT (Secondary System Description Table)  ★ 補充/動態載入的裝置描述(這個才是 XSDT 的項目)
       ├─ MADT (Multiple APIC Description Table)  ← 中斷控制器與 CPU 介面的列舉
       ├─ MCFG ← PCIe ECAM 的記憶體位址
       ├─ GTDT ← Arm generic timer(Arm 專用)
       ├─ PPTT ← 處理器拓樸(cache 階層、cluster)
       └─ SPCR ← serial console 重導向
```

大部分表是純資料,結構固定,直接讀就好。但打星號的 **DSDT 和 SSDT 不一樣** —— 它們裡面裝的是 **AML(ACPI Machine Language)**,一種 bytecode。

**Linux kernel 內建一個 AML 直譯器。** 這件事對第一次聽到的人通常有點衝擊:你的 kernel 裡有一台虛擬機,在跑主機板廠商寫的程式。這份直譯器實作叫 **ACPICA**,是 Intel 維護的跨 OS 參考實作,以原始碼形式匯入 Linux(`drivers/acpi/acpica/`)、也被 FreeBSD 等系統採用。

AML 的人類可讀形式叫 **ASL(ACPI Source Language)**,用 `iasl` 這支編譯器在 ASL 與 AML 之間來回轉換。

### 同一顆觸控 IC,用 ASL 怎麼寫

```asl
Device (TSC1)
{
    Name (_HID, "ACME0001")         // Hardware ID,對應 DT 的 compatible
    Name (_UID, 1)                  // 同型多顆時用來區分

    // _CRS:Current Resource Settings,對應 DT 的 reg / interrupts / gpios
    Name (_CRS, ResourceTemplate ()
    {
        I2cSerialBusV2 (0x0038, ControllerInitiated, 400000,
                        AddressingMode7Bit, "\\_SB.I2C1",
                        0x00, ResourceConsumer, , Exclusive, )
        GpioInt (Edge, ActiveLow, ExclusiveAndWake, PullUp, 0x0000,
                 "\\_SB.GPO2", 0x00, ResourceConsumer, , ) { 5 }
        // 注意:reset 腳「沒有」出現在這裡。它由下面的 _PS0/_PS3 自行處理,
        //       OS 不需要知道它的存在 —— 這正是與 DT 版本最大的差別。
    })

    // _DSD:Device Specific Data,對應 DT 的自訂 property
    Name (_DSD, Package ()
    {
        ToUUID ("daffd814-6eba-4d8c-8a91-bc9bbf4aa301"),
        Package ()
        {
            Package () { "touchscreen-size-x", 1024 },
            Package () { "touchscreen-size-y", 600 }
        }
    })

    Method (_STA, 0, NotSerialized)   // 這個裝置存在嗎?
    {
        Return (0x0F)                 // present + enabled + shown + functioning
    }

    Method (_PS0, 0, Serialized)      // 進入 D0(全開)要做什麼
    {
        // 示意:給電、放開 reset、等待穩定
        Store (One, \_SB.GPO2.PWEN)
        Sleep (5)
        Store (One, \_SB.GPO2.RSTN)
        Sleep (300)
    }

    Method (_PS3, 0, Serialized)      // 進入 D3(關閉)要做什麼
    {
        Store (Zero, \_SB.GPO2.RSTN)
        Store (Zero, \_SB.GPO2.PWEN)
    }
}
```

兩個實務上的提醒:

- `_HID` 用的是 PNP ID 或 ACPI ID 格式,而且**必須是登記過的**(PNP 前綴由 UEFI Forum 的登記處管理)。上面的 `ACME0001` 是為了說明而編的,真實產品不可以隨便自創 —— 這正是後面會提到的 `PRP0001` 存在的理由。
- 真實的 firmware 裡,這個 `Device` 會被包在 `DefinitionBlock` 與對應的 `Scope`(例如 `Scope (\_SB.I2C1)`)之內,而不是像上面這樣裸露在檔案最外層。這裡為了聚焦在對照關係而省略。

**請把這段跟前面那段 dts 並排看。** 前面九成的東西是一一對應的:

| Device Tree | ACPI | 意義 |
|---|---|---|
| `compatible` | `_HID` / `_CID` | 這是什麼裝置 |
| `reg`(在 i2c 底下) | `_CRS` 裡的 `I2cSerialBus` | I2C slave 位址 |
| `interrupts` + `interrupt-parent` | `_CRS` 裡的 `GpioInt` | 中斷來源 |
| `reset-gpios` | *(沒有對應項)* | 見下方說明 |
| `touchscreen-size-x` | `_DSD` 裡的同名 property | 組態參數 |
| `status = "okay"` | `_STA` 方法回傳值 | 這裝置在不在 |

差別在兩個地方。

第一,`reset-gpios` 在 ACPI 版本裡**消失了**。ACPI 也有 `GpioIo` 這種資源描述子,你確實可以把 reset 腳交給 OS 管;但一旦這麼做,操作它的責任就回到 driver 身上,等於放棄了 ACPI 的優勢。慣例上,這種純粹屬於板級整合的腳位不會出現在 `_CRS` 裡 —— 它被封裝進下面那兩個方法。

第二,也是更根本的:**`_PS0` 和 `_PS3` 是方法,不是資料。**

在 DT 世界,「先給電、等 5ms、放開 reset、等 300ms」這段時序寫在 kernel 的 `edt-ft5x06.c` 裡。在 ACPI 世界,它寫在主機板的 firmware 裡,kernel 只是在該讓裝置醒來的時候呼叫 `_PS0`,至於裡面做了什麼、等了多久、動了哪幾隻腳,kernel 完全不需要知道。

**這就是整件事的核心差異。**

### ACPI 還提供哪些「行為」

`_PS0`/`_PS3` 只是冰山一角。ACPI 定義了幾百個以底線開頭的標準物件與方法,常見的幾類:

- **電源** —— `_PS0`~`_PS3`(裝置電源狀態)、`_ON`/`_OFF`(power resource)、`_S0W`(系統在 S0 時,裝置最深可進入哪個 D-state 且仍能發出喚醒訊號)、`_PRW`(喚醒來源)
- **系統睡眠** —— `_S3`/`_S4` 定義的睡眠狀態、`_PTS`(Prepare To Sleep)、`_WAK`
- **熱管理** —— Thermal Zone 底下的 `_TMP`(讀溫度)、`_PSV`(passive trip point)、`_CRT`(critical shutdown 溫度)、`_AC0`(風扇轉速對應的溫度)。**整套散熱策略可以完全由 firmware 描述,OS 只負責照做。**
- **事件** —— GPE(General Purpose Event)。硬體拉起一個 event,firmware 的 `_Lxx`/`_Exx` 方法被執行,裡面呼叫 `Notify()` 通知 OS「筆電蓋子關了」「電池拔掉了」「有裝置熱插拔」
- **廠商擴充** —— `_DSM`(Device Specific Method),用 UUID 區分不同的 method 集合,是廠商放自訂邏輯的正式後門
- **CPU 電源與效能** —— `_CST`(C-state)、`_PSS`(P-state),或現在的 CPPC

`_CRS` 也不只是靜態資料 —— 它可以是一個 `Method`,依照當下狀態回傳不同的資源配置。

所以 ACPI 描述的不只是「板子長什麼樣」,而是「板子怎麼被操作」。**Firmware 是硬體知識的擁有者,OS 是呼叫者。**

---

## 四、正面對決

有了前面的鋪陳,現在可以把差異攤開來看。

| 維度 | Device Tree | ACPI |
|---|---|---|
| 本質 | 靜態資料結構 | 資料表 + AML bytecode |
| 硬體操作知識在哪 | Kernel driver | Firmware |
| 電源/熱管理 | Driver 自己實作 | Firmware 提供 method |
| 誰能修 bug | Kernel 開發者(可能是社群) | 只有 firmware/BIOS 廠商 |
| 修正的發佈管道 | Kernel patch,可 backport | BIOS/UEFI 更新 |
| 原始碼形式 | `.dts` / `.dtsi` | `.asl` |
| 編譯器 | `dtc` | `iasl`(ACPICA) |
| 二進位形式 | `.dtb` / `.dtbo`(FDT) | DSDT/SSDT(AML) |
| 誰產生它 | SoC 廠 + 板廠,常在 kernel tree 內 | 主機板 firmware 團隊 |
| Kernel 內的執行期表示 | `struct device_node` | `struct acpi_device` |
| 執行期檢視 | `/sys/firmware/devicetree/base` | `/sys/firmware/acpi/tables` |
| 「動態」能力 | 幾乎沒有(overlay 是開機時的) | 有(AML 方法、GPE、SSDT 動態載入) |
| 規格維護者 | devicetree.org | UEFI Forum |
| 主要生態 | 嵌入式、Arm SoC、Android、RISC-V | x86 PC/server、Arm server |

### 差異的本質:抽象層畫在哪裡

上面那張表可以壓縮成一句話:**ACPI 在 OS 和硬體之間插入了一層由 firmware 實作的抽象層,DT 沒有。**

這件事的後果是雙向的。

**ACPI 的好處**,kernel 的 arm64 ACPI 文件講得很直接:

> "ACPI's byte code (AML) allows the platform to encode hardware behavior, while DT explicitly does not support this."

> "It allows the hardware vendors to take responsibility for power management behaviour without depending on an OS release cycle which is not under their control."

後面這句是重點:硬體廠商可以**不依賴 OS 的發佈週期**來出貨自己的電源管理行為。你買一台新筆電,Ubuntu 24.04 的 kernel 從沒見過這塊主機板,但它照樣能睡眠、能讀電池電量、能控風扇 —— 因為那些邏輯不在 kernel 裡,在你主機板的 BIOS 裡。

文件也點出這對 OS 多樣性的意義:

> "Hardware vendors would not be required to implement both DT and ACPI if they want to support multiple operating systems."

以及那個常被引用的目標:讓 firmware 處理細節,如此一來「the OS doesn't need to be ported to each and every device individually」。這正是 x86 生態能有 Windows、Linux、各種 BSD 共存,而每個 Arm 手機 SoC 都需要一份專屬 BSP 的結構性原因之一。

**ACPI 的代價**,同一句話反過來念就是:

那層抽象裡如果有 bug,你動不了。

Linux 的 ACPI 相關程式碼裡有大量的 quirk —— DMI 比對機型、然後套用 workaround。原因是某些機器的 DSDT 寫錯了,或是它只在 Windows 上被測過(所以裡面充滿 `If (_OSI ("Windows 2015")) { ... }` 這種分支,走 Linux 路徑的程式碼從來沒人跑過)。你能做的只有兩件事:等廠商出 BIOS 更新,或是把 DSDT 挖出來、反組譯、改掉、重編、用 `initrd` 覆蓋(kernel 有 `CONFIG_ACPI_TABLE_UPGRADE` 支援這件事)。兩者都不是一個好的 Tuesday。

反過來,**DT 的好處**是透明。所有東西都在 kernel source tree 裡,dts 是文字檔、driver 是 C、binding 有文件,全部可以 grep、可以改、可以送 patch。一個時序問題你今天就能在 driver 裡加 delay 驗證。

**DT 的代價**是耦合。硬體知識在 kernel 裡,就代表**支援新硬體 = 改 kernel**。你不能拿一份 generic 的 Arm Linux image 去開一塊沒人支援過的板子。這就是為什麼 Arm 嵌入式世界裡「BSP」這個詞如此沉重,而 x86 世界幾乎不談 BSP。

### 不只是週邊:CPU、記憶體與中斷怎麼描述

前面都在談一顆觸控 IC,但「板子上有什麼」還包含更基礎的東西:有幾顆 CPU、記憶體從哪到哪、中斷控制器在哪。兩邊的處理方式也不同,而且差異同樣有跡可循。

**Device Tree 這邊**,這些全部是樹上的節點,跟週邊沒有本質區別:

```dts
/ {
    #address-cells = <2>;
    #size-cells = <2>;

    memory@40000000 {
        device_type = "memory";
        reg = <0x0 0x40000000 0x0 0x80000000>;   // 從 0x4000_0000 開始,2GB
    };

    cpus {
        #address-cells = <1>;
        #size-cells = <0>;

        cpu0: cpu@0 {
            device_type = "cpu";
            compatible = "arm,cortex-a55";
            reg = <0x000>;
            enable-method = "psci";
            next-level-cache = <&l2>;
        };
        /* cpu@100, cpu@200 ... */
    };

    gic: interrupt-controller@c000000 {
        compatible = "arm,gic-v3";
        #interrupt-cells = <3>;
        interrupt-controller;
        reg = <0x0 0x0c000000 0x0 0x10000>,      // GICD,64KB
              <0x0 0x0c080000 0x0 0x80000>;      // GICR,4 顆 CPU × 128KB
    };
};
```

注意 `memory` node 的 `reg` —— 實務上這一項常常被 bootloader 在執行期改寫,因為記憶體大小要靠 bootloader 實際偵測。這也是「一定要看執行期 DT」的又一個理由。

**ACPI 這邊**,這些東西不放在 DSDT 的 AML 裡,而是各自有專屬的固定格式表格:

- **MADT** —— 列出所有 CPU(Arm 上是 GICC 結構)、GIC distributor / redistributor / ITS 的位址。等價於 DT 的 `cpus` node 加上 `interrupt-controller` node。
- **記憶體** —— 不在 ACPI 表裡。UEFI 開機時透過 **memory map**(`GetMemoryMap()`)交給 OS(傳統 BIOS 則是 INT 15h E820),ACPI 只負責描述 NUMA 拓樸(SRAT)與節點間距離(SLIT)。
- **PPTT** —— 處理器拓樸:哪些 CPU 屬於同一個 cluster、共用哪一層 cache。DT 用 `cpu-map` 和 `next-level-cache` 表達同一件事。
- **GTDT** —— Arm generic timer 的中斷號與 watchdog。
- **MCFG** —— PCIe ECAM 的基底位址。

這裡有個容易混淆的點值得說清楚:**ACPI 不是所有東西都是 AML。** 上面這些表全是固定二進位結構,直接解析就好,不需要直譯器。只有 DSDT 和 SSDT 裡是 AML。所以「kernel 跑 firmware 的 bytecode」這句話,精確地說只發生在裝置列舉與電源/熱管理那一塊。

### 一個常被誤解的點

DT 陣營有時會說「ACPI 只是把 driver 藏進 BIOS」。這不完全正確。ACPI 沒有取代 driver —— 觸控 IC 的通訊協定、暫存器定義、報點格式,還是要有一支 kernel driver 來處理。ACPI 取代的是 **平台整合的那一層**:電源怎麼開、reset 怎麼拉、中斷怎麼接、睡醒要做什麼。

換句話說,ACPI 把「這顆晶片怎麼用」留給 OS,把「這塊板子怎麼把這顆晶片接起來」交給 firmware。DT 則是兩者都留給 OS,只把「接線圖」寫成資料。

---

## 五、Linux 怎麼把兩者收斂

如果 DT 和 ACPI 是兩個平行宇宙,那 driver 作者要寫兩套程式嗎?

早期確實接近如此。現在不用了,因為 Linux 做了幾層抽象。

### fwnode:統一的 firmware node 抽象

Kernel 裡有一個 `struct fwnode_handle`,它是 DT 的 `device_node` 和 ACPI 的 `acpi_device` 的共同上層抽象。`struct device` 裡同時有 `of_node` 和 `fwnode` 兩個欄位,driver 透過 fwnode 層的 API 讀取屬性,就不必關心底下是誰。

所以 driver 裡可以直接寫:

```c
u32 x;

if (device_property_read_u32(dev, "touchscreen-size-x", &x) == 0)
        tsdata->size_x = x;
```

這支 `device_property_read_u32()` 在 DT 開機時去讀 dts 的 property,在 ACPI 開機時去讀 `_DSD` 的 property。**同一行程式碼,兩個世界都能跑。**

相對地,`of_property_read_u32()` 是 DT 專用的舊 API。新寫的 driver 應該優先用 `device_property_*` / `fwnode_property_*` 系列。

### _DSD:讓 ACPI 借用 DT 的命名

上面那件事能成立,前提是 ACPI 端要有一個「放任意 key-value」的地方。這就是 ACPI 5.1 引入的 `_DSD`。

`_DSD` 的內容是一個 package,第一個元素是 UUID,用來區分 property 的格式。那串 `daffd814-6eba-4d8c-8a91-bc9bbf4aa301` 是業界公認的 "Device Properties UUID",代表後面是一般的 key-value 陣列。

**慣例上,`_DSD` 裡的 property 名稱直接沿用 DT binding 的名稱。** `touchscreen-size-x` 在兩邊叫同一個名字不是巧合,是刻意設計。這讓 fwnode 抽象真的能發揮作用,而不是徒具形式。

### PRP0001:直接在 ACPI 裡寫 compatible

還有更激進的做法。Kernel 的 ACPI enumeration 文件提到:

> "if PRP0001 is returned by _HID, the ACPI subsystem will look for the 'compatible' property in the device object's _DSD"

也就是說,你可以這樣寫:

```asl
Device (TSC1)
{
    Name (_HID, "PRP0001")          // 魔術字:去看 _DSD 裡的 compatible
    Name (_CRS, ResourceTemplate () { /* ... */ })
    Name (_DSD, Package ()
    {
        ToUUID ("daffd814-6eba-4d8c-8a91-bc9bbf4aa301"),
        Package ()
        {
            Package () { "compatible", "edt,edt-ft5406" },
            Package () { "touchscreen-size-x", 1024 }
        }
    })
}
```

`_HID` 填 `PRP0001` 這個保留值,kernel 就會轉去 `_DSD` 裡找 `compatible`,然後用 **DT 的配對規則** 去找 driver。文件說明這樣做的目的是重用既有的 DT driver,不必為每顆晶片再去申請一組 ACPI ID。

這是一個很有意思的設計:ACPI 的框架、DT 的識別語意,混在一起用。

### 但開機時只有一個

Kernel 文件同時定下了明確的界線:

> "ACPI support in drivers and subsystems for Arm should never be mutually exclusive with DT support at compile time."

> "At boot time the kernel will only use one description method depending on parameters passed from the boot loader."

也就是說 —— **編譯期兩者都要能支援,執行期只能擇一。** 你不能一半裝置從 DT 來、一半從 ACPI 來。這個規則避免了兩套描述互相打架的無底洞。

EBBR 規格把同一件事寫成對平台的硬性要求:

> "Compliant systems are required to provide one, but not both, of the following tables: an Advanced Configuration and Power Interface [ACPI] table, or a Devicetree [DTSPEC] system description"

平台內部可以兩套都準備,提供一個設定選項讓使用者決定要暴露哪一套給 OS —— 但交給 OS 的只能有一份。

---

## 六、生態現實:誰在用哪一個

| 領域 | 用什麼 | 為什麼 |
|---|---|---|
| x86 桌機/筆電/伺服器 | ACPI | 歷史必然,Windows 相容性要求 |
| Arm 伺服器 | ACPI | 被規格強制,見下 |
| Arm 嵌入式 / 單板電腦 | DT | EBBR 允許,生態慣性 |
| Android 手機/平板 | DT + dtbo overlay | 垂直整合,BSP 模式 |
| RISC-V | DT 為主,ACPI 逐步成形 | 嵌入式出身,伺服器場景在補 |
| 虛擬機(QEMU/KVM) | 兩者都支援 | 看 guest 要什麼 |

Arm 伺服器那一格值得展開。Arm 為了讓 Arm server 能像 x86 server 一樣「裝哪個 OS 都能開」,定義了一系列基礎規範。其中 **BBR(Base Boot Requirements)** 定義了幾種 recipe(本文參照 Revision 2.1;Arm 目前已釋出 2.2):

- **SBBR** —— 給伺服器等級的系統,要求 UEFI + ACPI。這是 Arm SystemReady 認證中 ACPI 那一條路線的基礎。
- **EBBR** —— 給嵌入式系統,允許 UEFI + DT 或 ACPI,明確表態「Be agnostic about ACPI and Devicetree」。
- **LBBR** —— LinuxBoot Base Boot Requirements,給以 LinuxBoot 為韌體的 hyperscaler 場景。它不強制完整的 UEFI 開機與 runtime services,但**仍然要求 ACPI**。

(名稱上的小提醒:Arm 在 SystemReady 3.0 之後調整了認證分級的命名,舊的 SR / ES / IR 帶別已改為 **SystemReady band**(ACPI/SBBR 路線)與 **SystemReady Devicetree band**。底層的 recipe 沒變,但如果你搜到舊文件會看到不同的名字。)

所以「Arm 一定用 DT」是過時的印象。一台 Ampere 或 Graviton 的機器,是 ACPI 開機的,`acpidump` 拿出來看跟 x86 server 沒有本質差別。

kernel 文件對選型的立場也很務實:ACPI 適合追求標準化與長期相容的伺服器場景,DT 則適合垂直整合、需要詳盡描述特定硬體的裝置。**這不是誰比較先進的問題,是抽象層該畫在哪裡的問題。**

---

## 七、實務:怎麼看、怎麼查

理論講完了。真的遇到「裝置沒起來」的時候,兩個世界的手法完全不同。

### Device Tree 這邊

```bash
# 看 kernel 實際收到的 DT(不是你 source tree 裡那份!)
ls /sys/firmware/devicetree/base/
cat /sys/firmware/devicetree/base/model

# 把執行期的 DT 反組譯回可讀的 dts
dtc -I fs -O dts /sys/firmware/devicetree/base > runtime.dts

# 反組譯一份 dtb 檔
dtc -I dtb -O dts -o out.dts boot.dtb
fdtdump boot.dtb | less

# 看哪些 node 成功變成了 device、哪些 driver bind 上去了
ls /sys/bus/platform/devices/
ls -l /sys/bus/platform/drivers/*/

# I2C 上實際列舉出的裝置
ls /sys/bus/i2c/devices/
```

**最重要的一句話:一定要看執行期的 DT,不要看 source。** 因為 overlay 疊過、bootloader 改過,兩者可能完全不同。整合階段有相當比例的「明明 dts 寫對了卻不會動」,答案都在這一步。

常見症狀對照:

| 症狀 | 通常的原因 |
|---|---|
| `/sys/bus/platform/devices/` 裡有 device,但沒 bind 到 driver | `compatible` 字串跟 driver 的 `of_device_id` 表對不上(拼字、廠商前綴、driver 沒 enable) |
| node 根本沒出現在執行期 DT | overlay 沒套上、`status = "disabled"`、放在不會被 populate 的位置 |
| device 有了但 probe 失敗回 `-EPROBE_DEFER` | 依賴的 regulator/clock/gpio controller 還沒 ready,通常會自動重試;一直 defer 就是那個 provider 根本沒起來 |
| 屬性讀出來是垃圾值 | `#address-cells` / `#size-cells` 跟 `reg` 的 cell 數量不符 |
| 中斷收不到 | `interrupt-parent` 指錯、trigger type 寫反(edge/level、high/low) |

### ACPI 這邊

```bash
# 列出所有 ACPI 表
ls /sys/firmware/acpi/tables/

# 把表 dump 出來(需要 acpica-tools / iasl 套件)
sudo acpidump -b            # 產生一堆 *.dat
iasl -d dsdt.dat            # 反組譯成 dsdt.dsl,這是人類可讀的 ASL

# 或直接從 sysfs 抓
sudo cat /sys/firmware/acpi/tables/DSDT > dsdt.dat

# 看 ACPI 列舉出的裝置與它們在 namespace 裡的路徑
ls /sys/bus/acpi/devices/
cat /sys/bus/acpi/devices/*/path
cat /sys/bus/acpi/devices/*/hid

# 開啟 ACPI 直譯器的除錯輸出。前提:kernel 必須有 CONFIG_ACPI_DEBUG=y,
# 否則這些訊息根本沒被編進去(多數發行版的 kernel 是關的)。
# 加在 kernel cmdline:
#   acpi.debug_layer=0xFFFFFFFF acpi.debug_level=0x2
```

ACPI 這邊的 debug 心法完全不同:**你在讀別人寫的、已經編譯過的程式。** `iasl -d` 出來的 ASL 沒有註解、變數名稱是 `_T_0` 這種自動產生的東西,你要在裡面追「`_PS0` 到底做了什麼、`Notify` 有沒有被呼叫」。

常見手法:

- `iasl -d` 反組譯後,搜尋出問題的裝置名稱,人工閱讀那段 method
- 用 `initrd` 覆蓋 DSDT(`CONFIG_ACPI_TABLE_UPGRADE`)驗證假設 —— 改一行、重編、開機看看
- `acpi_osi=` 這類 kernel 參數,改變 firmware 眼中的 OS 身分,讓它走不同的分支
- 對照 Windows 上同一台機器的行為,判斷是「firmware 錯了」還是「Linux 沒實作」

| 症狀 | 通常的方向 |
|---|---|
| 裝置在 `/sys/bus/acpi/devices/` 有,但沒對應的 platform/i2c device | `_STA` 回傳說它不存在,或 `_CRS` 沒給出可用的資源 |
| 睡眠醒來後裝置死掉 | `_PS0` 沒把裝置正確叫醒,或 driver 沒有正確呼叫電源轉換 |
| 風扇/溫度行為異常 | Thermal Zone 的 trip point 定義,`_TMP` / `_PSV` / `_CRT` |
| 某些功能只在 Windows 上正常 | DSDT 裡有 `_OSI` 分支,Linux 走到未測試的路徑 |

### 一個實用的判斷順序

不管哪一邊,除錯的第一個問題永遠是同一個:**firmware 到底有沒有把這個裝置描述給 OS?**

- DT:它有沒有出現在 `/sys/firmware/devicetree/base` 裡?
- ACPI:它有沒有出現在 `/sys/bus/acpi/devices/` 裡?

如果沒有,問題在 firmware/bootloader/overlay,不在 driver。如果有但沒 bind,問題在識別碼配對。如果 bind 了但 probe 失敗,才輪到 driver 邏輯。這三段切乾淨,可以省掉大量無效的猜測。

---

## 八、如果你在設計一個平台

假設你有選擇權(很多時候沒有),幾個判斷維度:

**選 DT,如果:**

- 你的軟硬體是垂直整合的 —— 你同時控制 kernel 和板子,兩者一起出貨
- 硬體很特殊,需要大量非標準的描述
- 你的團隊在 kernel 裡工作,改 driver 比改 firmware 快
- 你在既有的 Arm 嵌入式 / Android 生態裡(現實上這幾乎是決定性的)

**選 ACPI,如果:**

- 你希望使用者能自由安裝任何 OS,而且開起來就能用
- 你要通過 Arm SystemReady(SBBR 路線)認證
- 你的電源與熱管理策略跟板子高度綁定,而且你不想每次調整都要送 kernel patch
- 你有能力維護一支 firmware 團隊 —— 這一點是硬需求,ACPI 把責任移到了 firmware,那個責任不會消失

**一個常被低估的成本:** 選 ACPI 等於承諾要長期維護一份 firmware。DSDT 不是寫完就結束的東西 —— 每一次硬體改版、每一顆料號替換、每一個被回報的睡眠問題,都要回到 ASL 裡改、重編、驗證、推送 BIOS 更新給已出貨的機器。x86 生態能扛住這件事,是因為主機板廠商本來就有這條產線。如果你的組織沒有,那麼「把責任移給 firmware」實際上只是把它移給一個不存在的團隊,結果會比留在 kernel 裡更糟。

**共通的原則:** 不論選哪個,「行為」都要放在正確的那一層。DT 專案裡不要試圖用一堆 property 去編碼流程(這是常見的反模式,會生出無法維護的 binding);ACPI 專案裡也不要把所有東西塞進 `_DSM`,那等於放棄了標準化帶來的好處。

---

## 九、常見誤解 Q&A

**Q:ACPI 是 x86 專用的嗎?**

不是。Arm 的支援從 **ACPI 5.0/5.1** 就進來了 —— MADT 的 GICC/GICD 結構與 GTDT 在 5.0 加入,GICR、GIC ITS、hardware-reduced model 等 AArch64 需要的完整集合在 5.1 補齊;kernel 文件也寫明 Arm 實作的是「the reduced hardware model of ACPI version 5.1 or later」。至於 PPTT 是 6.2 才加入,而且它是架構中立的(只是主要由 Arm 的需求推動)。Arm 伺服器透過 SBBR 被要求使用 ACPI。RISC-V 也在建立自己的 ACPI 支援。反過來,x86 也不是不能用 DT —— 某些 x86 SoC 的嵌入式應用就是用 DT 開機的。**架構跟描述方式沒有必然關係,是使用場景與規格要求決定的。**

**Q:那 UEFI 呢?UEFI 和 ACPI 是同一件事嗎?**

不是,但常被混為一談。**UEFI 是開機介面**,規範 firmware 怎麼載入並啟動 OS loader、提供什麼開機期服務(檔案系統存取、變數儲存、memory map)。**ACPI 是硬體描述與電源管理介面**,規範 OS 開機之後怎麼認識和操作硬體。兩者由同一個組織(UEFI Forum)維護、經常一起出現,但完全可以拆開:你可以用 U-Boot(非 UEFI)開機然後傳 ACPI 表,也可以用 UEFI 開機然後傳 Device Tree —— EBBR 規範的正是後面這種組合。

**Q:有了 ACPI 就不用寫 driver 了?**

不對。ACPI 取代的是「板級整合」那一層,不是晶片本身的驅動。觸控 IC 的通訊協定、報點格式、韌體升級流程,還是要一支 kernel driver 處理。ACPI 幫你解決的是「這顆 IC 接在哪條 I2C、電源怎麼開、中斷怎麼接、睡醒要做什麼」。

**Q:DT 可以像 ACPI 那樣描述行為嗎?**

規格上不行,而且這是刻意的。歷史上出現過幾次想在 DT 裡編碼流程的嘗試(用 property 陣列表達「先寫這個暫存器、延遲多久、再寫那個」),都被 DT maintainer 擋下來,理由是那等於發明一種難以驗證、難以維護的迷你語言。kernel 的立場很明確:**DT explicitly does not support this。** 需要行為描述的場景,正確答案是寫 driver,或是改用 ACPI。

**Q:我可以把 DT 和 ACPI 混著用嗎?比如 CPU 用 ACPI 描述、週邊用 DT?**

不行。kernel 文件明說開機時只會採用其中一種描述方式,EBBR 也要求平台只能提供其中一份給 OS。混用會讓資源歸屬與電源管理責任變得無法界定。

**Q:Device Tree 是 Linux 專有的嗎?**

不是。DT 的規格由 devicetree.org 獨立維護,U-Boot、FreeBSD、Zephyr、各種 RTOS 都在用。它只是在 Linux 生態裡最活躍。

**Q:DT overlay 可以在 OS 執行中動態套用嗎?**

Kernel 有 overlay 的執行期套用機制(configfs 介面、以及 FPGA region 這類使用場景),但這跟 Android 的 dtbo 是兩件事 —— 後者是 **bootloader 在開機時** 合併完才交給 kernel。實務上,執行期套用 overlay 在一般產品裝置上很少見,主要出現在 FPGA 與可插拔擴充板(如 BeagleBone cape)的場景。

**Q:為什麼我的筆電 Linux 睡眠有問題,換 kernel 也沒用?**

如果問題出在 DSDT 的 `_PS0`/`_PS3`/`_S0W` 邏輯,那段程式碼在你的 BIOS 裡,換 kernel 動不到它。你能做的是等 BIOS 更新、加 kernel quirk 參數繞過,或是自己反組譯 DSDT 改掉再用 initrd 覆蓋。這正是 ACPI 抽象的代價 —— 便利與不可見是同一枚硬幣的兩面。

---

## 十、想動手驗證的話

理解這兩套東西最快的方式是同時看到它們。QEMU 剛好可以在同一個架構上切換兩種描述方式,不需要任何實體板子。

**看 Device Tree:**

```bash
# 讓 QEMU 把它產生的 DT 直接 dump 出來
qemu-system-aarch64 -M virt,dumpdtb=virt.dtb -cpu cortex-a57 -nographic

# 反組譯來看
dtc -I dtb -O dts -o virt.dts virt.dtb
less virt.dts
```

你會看到 `cpus`、`memory`、`intc`(GIC)、`pl011`(UART)、`virtio_mmio` 這些節點,結構跟前面講的一模一樣。把 `-smp 4` 或 `-m 4G` 改一改再 dump 一次,對照差異,`cpus` 和 `memory` node 的變化會很直觀。

**看 ACPI:**

`qemu-system-aarch64 -M virt` 搭配 EDK2(UEFI)韌體開機時會走 ACPI 路徑。值得一提的是,這些表其實是 **QEMU 自己組出來的**(`hw/arm/virt-acpi-build.c`),透過 fw_cfg 交給 EDK2,EDK2 只負責載入並安裝給 OS。在 guest 裡:

```bash
sudo apt install acpica-tools
ls /sys/firmware/acpi/tables/
sudo acpidump -b
iasl -d dsdt.dat && less dsdt.dsl
```

同一台虛擬機、同樣的硬體,你會看到 MADT 裡列著跟 DT `cpus` node 相同的那幾顆 CPU,DSDT 裡的 `Device (COM0)` 對應 DT 裡的 `pl011` 節點。**兩份描述講的是同一件事,只是語言不同。** 把兩邊並排讀一次,這篇文章前面所有的抽象討論會瞬間變得具體。

**再進一步:** 在自己的 x86 機器上跑一次 `sudo acpidump -b && iasl -d dsdt.dat`,然後在反組譯出來的 `dsdt.dsl` 裡搜尋 `_OSI`。你會看到主機板廠商如何依照 OS 身分走不同分支 —— 那是理解「為什麼某些功能只在 Windows 上正常」最直接的一手證據。

---

## 十一、一頁總結

如果只能記住五句話:

1. **兩者解決同一個問題** —— 在不能自我列舉的硬體上,告訴 OS 板子上有什麼。
2. **DT 是純資料,ACPI 是資料加上可執行的 bytecode。** kernel 內建 AML 直譯器去執行 firmware 寫的方法。
3. **差別在抽象層畫在哪裡** —— DT 把硬體知識留在 kernel driver,ACPI 把它移進 firmware。前者透明可改但耦合,後者可攜可獨立更新但不透明。
4. **Linux 已經用 fwnode / `device_property_*` / `_DSD` / `PRP0001` 把兩者在 driver 層收斂**,同一支 driver 可以兩邊跑;但開機時只會有一種描述生效。
5. **生態是規格決定的** —— Arm server 被 SBBR 要求 ACPI,嵌入式與 Android 走 DT,EBBR 明說兩者擇一。「Arm 就是用 DT」已經是過時的印象。

---

## 附錄:名詞速查

| 縮寫 | 全名 | 說明 |
|---|---|---|
| DT | Device Tree | 硬體描述資料結構 |
| DTS / DTSI | Device Tree Source / Include | DT 的文字原始碼 |
| DTB | Device Tree Blob | 編譯後的二進位 DT,也叫 FDT |
| DTBO | Device Tree Blob Overlay | 疊加用的 DT 片段 |
| FDT | Flattened Device Tree | DTB 的格式名稱 |
| dtc | Device Tree Compiler | DTS ↔ DTB 的編譯器 |
| ACPI | Advanced Configuration and Power Interface | 韌體介面規格 |
| AML | ACPI Machine Language | ACPI 的 bytecode |
| ASL | ACPI Source Language | AML 的文字原始碼 |
| iasl | Intel ASL compiler | ASL ↔ AML 的編譯器 |
| ACPICA | ACPI Component Architecture | Intel 的 ACPI 參考實作,Linux 內建 |
| DSDT | Differentiated System Description Table | 主要的裝置描述表(含 AML) |
| SSDT | Secondary System Description Table | 補充的裝置描述表(含 AML) |
| FADT | Fixed ACPI Description Table | 固定暫存器與電源參數 |
| MADT | Multiple APIC Description Table | 中斷控制器與 CPU 介面的列舉 |
| _HID / _CID | Hardware ID / Compatible ID | ACPI 的裝置識別碼 |
| _CRS | Current Resource Settings | ACPI 的資源描述 |
| _DSD | Device Specific Data | ACPI 的自訂 key-value 屬性 |
| _DSM | Device Specific Method | ACPI 的廠商自訂方法 |
| GPE | General Purpose Event | ACPI 的硬體事件機制 |
| BBR | Base Boot Requirements | Arm 的開機需求規範 |
| SBBR / EBBR / LBBR | Server / Embedded / LinuxBoot BBR | BBR 的三種 recipe |

---

## 引用來源

規格:

- [ACPI Specification 6.6 (May 2025) — UEFI Forum](https://uefi.org/specifications)
- [Devicetree Specification v0.4 (2023-06-28) — devicetree.org](https://www.devicetree.org/specifications/)
- [Arm Base Boot Requirements, Revision 2.1](https://documentation-service.arm.com/static/661e74f45d66282bc2cf9cbc)(本文參照版本)
- [Arm Base Boot Requirements — latest](https://developer.arm.com/documentation/den0044/latest/)(目前為 2.2)
- [Embedded Base Boot Requirements (EBBR) Specification](https://arm-software.github.io/ebbr/)

Linux kernel 文件:

- [ACPI on Arm systems — `Documentation/arch/arm64/arm-acpi.rst`](https://docs.kernel.org/arch/arm64/arm-acpi.html)(ACPI vs DT 的官方立場、AML 能編碼硬體行為、開機時只用一種描述)
- [ACPI Device Enumeration — `Documentation/firmware-guide/acpi/enumeration.rst`](https://docs.kernel.org/firmware-guide/acpi/enumeration.html)(`_HID` 配對、`_DSD`、`device_property_*`、`PRP0001`)
- [Devicetree (DT) ABI — `Documentation/devicetree/bindings/ABI.rst`](https://docs.kernel.org/devicetree/bindings/ABI.html)(binding 的相容性原則)

其他:

- [Implementing DTO — Android Open Source Project](https://source.android.com/docs/core/architecture/dto)(主 DTB / overlay / dtbo 分割區)
- [Device trees I: Are we having fun yet? — LWN.net](https://lwn.net/Articles/572692/)(DT 的 SPARC/PowerPC 出身、ARM board file 的問題)
- [ACPI 1.0 Specification (Intel/Microsoft/Toshiba) — UEFI Forum 存檔](https://uefi.org/sites/default/files/resources/ACPI_1_Errata_B.pdf)

### 說明

- 文中所有直接引號皆為上列來源之原文;中文為筆者翻譯或詮釋。
- 程式碼範例為說明用途所撰寫,`edt,edt-ft5406` 為 mainline kernel 中實際存在的 compatible 字串,ASL 版本為筆者依 ACPI 規格對照撰寫之等價示意,未經實機驗證,請勿直接複製使用。
- 「常見症狀對照」兩張表為筆者依公開機制推論整理的除錯經驗歸納,非規格文件內容。
- 選型建議一節為筆者觀點。
