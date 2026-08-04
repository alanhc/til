# Device Tree

x86 平台可以靠 ACPI 或 PCI 列舉自動發現硬體，但 **ARM 的嵌入式系統（BMC 就是）大多數週邊掛在 I2C、SPI、GPIO 上，是「不可列舉」的**——kernel 沒辦法自己問出「i2c-7 上 0x4c 位址接的是一顆 TMP75 溫度感測器」。

**Device Tree** 就是用來解決這件事的：把板子上的硬體配置寫成一份與程式碼分離的描述檔，開機時交給 kernel，kernel 依照描述去配對並載入對應的 driver。**同一份 kernel binary 搭配不同的 device tree，就能跑在不同板子上。**

## 檔案格式與工具鏈

| 名詞 | 全名 | 說明 |
|---|---|---|
| **dts** | Device Tree Source | 人寫的原始檔，一塊板子一份 |
| **dtsi** | Device Tree Source Include | 可被 `#include` 的共用片段（i 是 include），通常放 SoC 層級的共通描述 |
| **dtc** | Device Tree Compiler | 把 dts 編譯成 dtb 的工具，也能反編譯 |
| **dtb** | Device Tree Blob | 編譯後的二進位檔（副檔名 `.dtb`），bootloader 載入到記憶體後把位址傳給 kernel |
| **dtbo** | Device Tree Blob Overlay | 疊加片段，可在執行期套用到既有 dtb 上 |

分層慣例是：SoC 廠提供 `<soc>.dtsi` 描述晶片內部的控制器，板廠再寫一份 `<board>.dts` 用 `#include` 引入它、然後只補上自己板子接了什麼週邊。

```bash
# 編譯
dtc -I dts -O dtb -o board.dtb board.dts

# 反編譯（手上只有 dtb 時很有用）
dtc -I dtb -O dts -o board.dts board.dtb

# 在跑起來的機器上直接看目前生效的 device tree
ls /proc/device-tree/
dtc -I fs -O dts /proc/device-tree      # 把執行中的 device tree 反編譯回來看
```

## 語法結構

Device tree 是一棵樹，節點裡放 property：

```dts
&i2c7 {
    status = "okay";
    clock-frequency = <100000>;

    tmp75@4c {
        compatible = "ti,tmp75";
        reg = <0x4c>;
    };
};
```

- **節點名稱** `tmp75@4c`：`@` 後面是 unit address，要和 `reg` 一致。
- **`reg`**：裝置在父匯流排上的位址。掛在 I2C 底下就是 I2C slave address，掛在記憶體匯流排底下就是暫存器基底位址與長度。
- **`status`**：`"okay"` 啟用、`"disabled"` 停用。SoC 的 dtsi 通常把所有控制器預設為 `disabled`，由板子的 dts 逐一打開自己有用到的。
- **`&i2c7`**：透過 label 參考既有節點並「補充」它的內容，不必重寫整棵樹的路徑。

### compatible

**`compatible` 是 device tree 最關鍵的一個 property**，它是硬體與 driver 之間的配對鍵。

格式慣例是 `"廠商,型號"`，可以給一個字串陣列，由具體到通用排列：

```dts
compatible = "ti,tmp75", "ti,lm75";
```

kernel 開機時走訪 device tree，拿每個節點的 `compatible` 去比對所有 driver 註冊的 `of_match_table`；比中了就呼叫該 driver 的 `probe()`。上面這個例子的意思是「我是 TMP75，但如果沒有 TMP75 的 driver，用 LM75 的 driver 也能動」。

driver 端對應的寫法：

```c
static const struct of_device_id tmp75_of_match[] = {
    { .compatible = "ti,tmp75" },
    { }
};
MODULE_DEVICE_TABLE(of, tmp75_of_match);
```

**新增一個感測器最常見的失敗原因，就是 dts 裡的 `compatible` 字串和 driver 裡的對不起來**，結果 `probe()` 根本沒被呼叫，`dmesg` 裡什麼都看不到。

### phandle

**phandle** 是 device tree 裡的「指標」，用來讓一個節點參考另一個節點。

實際寫法是給節點一個 label，再用 `&label` 去引用；`dtc` 編譯時會自動配一個唯一的整數 ID（也就是 phandle 值）填進去：

```dts
gpio0: gpio@1e780000 {
    gpio-controller;
    #gpio-cells = <2>;
};

my_device {
    /* 參考 gpio0 這個 controller 的第 5 隻腳，active low */
    reset-gpios = <&gpio0 5 GPIO_ACTIVE_LOW>;

    /* 參考中斷控制器 */
    interrupt-parent = <&vic>;
    interrupts = <3>;
};
```

`#gpio-cells = <2>` 宣告「引用我的時候要再帶 2 個參數」（這裡是腳位編號與極性）。同理還有 `#address-cells`、`#size-cells`、`#interrupt-cells`。phandle 就是這樣把 GPIO、中斷、時脈、regulator 等資源的提供者與使用者串起來的。

### 刪除節點與屬性

繼承 dtsi 之後常會遇到「上層定義了我不要的東西」，這時用刪除語法：

```dts
/ {
    /delete-node/ some-node;
};

&i2c7 {
    /delete-property/ clock-frequency;
    /delete-node/ tmp75@4c;
};
```

比起把 dtsi 改壞，優先用 `status = "disabled"` 或 `/delete-node/` 在自己的 dts 裡處理，這樣才不會影響其他共用同一份 dtsi 的板子。

## binding YAML

**binding** 是「某個 `compatible` 該有哪些 property、型別為何、哪些是必填」的規格文件，放在 kernel 原始碼的 `Documentation/devicetree/bindings/` 底下。自 5.x 起格式從純文字改為 **YAML（json-schema）**，好處是可以被機器驗證。

```yaml
%YAML 1.2
---
$id: http://devicetree.org/schemas/hwmon/ti,tmp75.yaml#
$schema: http://devicetree.org/meta-schemas/core.yaml#

title: TI TMP75 Temperature Sensor

maintainers:
  - Someone <someone@example.com>

properties:
  compatible:
    enum:
      - ti,tmp75
  reg:
    maxItems: 1

required:
  - compatible
  - reg
```

新增 driver 時 binding 是必要交付物，而且可以用 kernel 內建的 target 檢查自己的 dts 有沒有違反 schema：

```bash
make dt_binding_check          # 檢查 binding 檔本身寫得對不對
make dtbs_check                # 拿 binding 去驗證所有 dts
```

## 開機流程中的 device tree

1. **bootloader（u-boot）** 從 flash 讀出 `dtb` 載入到記憶體某個位址。
2. 跳轉到 kernel 時，把 dtb 的實體位址放進暫存器（ARM 是 `r2`，arm64 是 `x0`）傳給 kernel。
3. kernel 早期以 `early_init_dt_scan()` 解析 dtb，取得記憶體大小、CPU 數量、`chosen` 節點裡的 kernel command line。
4. driver 註冊時，kernel 拿 device tree 的節點與 driver 的 `of_match_table` 配對，配上就呼叫 `probe()`。

詳見 [BMC 開機流程](./bootup.md)。u-boot 端可以用 `fdt` 系列指令在載入後、跳轉前臨時修改 device tree：

```
=> fdt addr ${fdt_addr}
=> fdt print /
=> fdt set /soc/i2c@1e78a000 status "disabled"
```

## 在 Yocto 專案中修改

OpenBMC 用 Yocto 建置，kernel 原始碼不會直接躺在專案目錄下，要先用 `devtool` 把它取出來：

```bash
devtool modify linux-aspeed
# 原始碼會出現在 build/workspace/sources/linux-aspeed/
# 改完直接 bitbake，devtool 會用你改過的樹去編
```

dts 檔通常在 `arch/arm/boot/dts/aspeed/` 底下。改完之後：

```bash
bitbake obmc-phosphor-image
```

完成後把新的 image 燒進去（見 [flash](./flash.md)），開機後用 `ls /proc/device-tree/` 或 `dmesg` 確認新節點有被 probe 到。

## 參考

- [Device Tree Specification](https://www.devicetree.org/specifications/)
- [Linux kernel — Documentation/devicetree/](https://docs.kernel.org/devicetree/usage-model.html)
- [Device Tree Reference（eLinux wiki）](https://elinux.org/Device_Tree_Reference)
