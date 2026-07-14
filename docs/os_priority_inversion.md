# Priority Inversion（優先權反轉）

作業系統排程中的經典問題。

## 問題

當高優先權的 task 需要等待低優先權 task 持有的資源（lock）時，會發生**優先權反轉**：若此時有中優先權 task 搶佔了低優先權 task 的 CPU，低優先權 task 遲遲無法釋放資源，導致高優先權 task 被間接卡住。著名案例為 NASA 火星探測車 Mars Pathfinder 的系統重啟問題。

## 解法

- **Priority Inheritance（優先權繼承）**：持有資源的低優先權 task 暫時繼承等待者的高優先權，儘快完成並釋放資源後再降回原優先權。
- **Priority Ceiling（優先權天花板）**：每個資源預先設定一個「天花板優先權」（等於可能存取它的最高優先權），task 取得資源時即提升到該優先權，可避免死結。

參考：https://hackmd.io/@DamienChen/H1WS_XV_p
