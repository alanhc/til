# Device Tree

Device Tree (DT) 是一種描述硬體的資料結構，用來告訴 kernel 那些「無法自我探測 (non-discoverable)」的硬體。常見於 ARM、RISC-V 等 embedded 平台；x86 多半靠 ACPI/PCI 自動列舉，較少用 DT。

為什麼需要：像 I2C、SPI、UART、GPIO、memory-mapped 週邊，硬體本身不會回報「我在哪、用哪個 IRQ、時脈多少」，因此需要一份靜態描述。

## 檔案類型

- `.dts` — Device Tree Source，人類可讀的文字描述（單一板子）。
- `.dtsi` — Source Include，可被 `.dts` 引入的共用片段（例如同一 SoC 的多塊板子共用）。
- `.dtb` — Device Tree Blob，經 `dtc` 編譯後的二進位檔，bootloader (如 U-Boot) 載入並傳給 kernel。

## 基本語法

```dts
/ {                     // root node
    soc {
        uart0: serial@10000000 {
            compatible = "ns16550a";   // 對應 driver
            reg = <0x10000000 0x100>;  // 位址與大小
            interrupts = <10>;
            status = "okay";
        };
    };
};
```

- `compatible`：driver 據此比對綁定 (binding)。
- `reg`：register 位址/大小或 bus address。
- node 以 `label: name@unit-address` 命名。

kernel 開機時 unflatten DTB，driver 透過 `of_*` API 讀取屬性。

參考：https://www.devicetree.org/
