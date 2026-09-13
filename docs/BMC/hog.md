# GPIO Hog

在 device tree 中直接宣告某支 GPIO 於開機時就被 kernel「佔用並設定成固定狀態」，不需要任何 driver 或 user space 程式介入。常用來拉高/拉低 enable、reset、power-good select 等訊號。

在 gpio controller node 底下加子節點：

```dts
&gpio0 {
    my-enable-hog {
        gpio-hog;
        gpios = <5 GPIO_ACTIVE_HIGH>;
        output-high;        /* 或 output-low / input */
        line-name = "board-enable";
    };
};
```

重點：
- `gpio-hog` 屬性代表這是一個 hog。
- 方向：`output-high`、`output-low`、`input`。
- kernel 在 probe gpio controller 時就套用，早於大部分服務啟動。
- 被 hog 的 pin 之後不能再被別的 driver/user space 請求（已被佔住）。

適合「開機即需固定電位、且不會再變動」的訊號。若之後要動態控制，應改用一般 GPIO 而非 hog。
