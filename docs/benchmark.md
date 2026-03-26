## hardware
![](assets/benchmark/file-20260117093837822.png)
![](assets/benchmark/file-20260116225154885.png)![](assets/benchmark/file-20260116225211942.png)![](assets/benchmark/file-20260116225254696.png)![](assets/benchmark/file-20260116225306320.png)
![](assets/benchmark/file-20260116225014813.png)
![](assets/benchmark/file-20260116224831606.png)![](assets/benchmark/file-20260116224839882.png)![](assets/benchmark/file-20260116224907069.png)
![](assets/benchmark/file-20260116223628716.png)
![](assets/benchmark/file-20260116223037035.png)
![](assets/benchmark/file-20260116222256792.png)
![](assets/benchmark/file-20260116222240609.png)
![](assets/benchmark/file-20260116222016563.png)
![](assets/benchmark/file-20260116220632017.png)![](assets/benchmark/file-20260116220653755.png)![](assets/benchmark/file-20260116220706339.png)![](assets/benchmark/file-20260116220717657.png)
![](assets/benchmark/file-20260116215815383.png)
![](assets/benchmark/file-20260116220430624.png)![](assets/benchmark/file-20260116215828207.png)![](assets/benchmark/file-20260116215856312.png)


# performance

## CPU
![](assets/benchmark/file-20260116223215392.png)![](assets/benchmark/file-20260116223227195.png)![](assets/benchmark/file-20260116223241542.png)
![](assets/benchmark/file-20260116220537789.png)![](assets/benchmark/file-20260116220549125.png)![](assets/benchmark/file-20260116220559642.png)![](assets/benchmark/file-20260116220446499.png)


## geekbench
![](assets/benchmark/file-20260116222314647.png)
![](assets/benchmark/file-20260116215910034.png)


## 圖形
![](assets/benchmark/file-20260116223310067.png)
![](assets/benchmark/file-20260116222938084.png)
![](assets/benchmark/file-20260116222720222.png)
![](assets/benchmark/file-20260116220735063.png)![](assets/benchmark/file-20260116220746946.png)![](assets/benchmark/file-20260116220803385.png)
![](assets/benchmark/file-20260116220048983.png)
![](assets/benchmark/file-20260116221103841.png)![](assets/benchmark/file-20260116221145800.png)![](assets/benchmark/file-20260116221219098.png)![](assets/benchmark/file-20260116221239056.png)
遊戲
perfdog
![](assets/benchmark/file-20260116220109861.png)


## gpu
![](assets/benchmark/file-20260116225352416.png)
![](assets/benchmark/file-20260116223259758.png)
![](assets/benchmark/file-20260116222907023.png)![](assets/benchmark/file-20260116222915147.png)![](assets/benchmark/file-20260116222923117.png)
![](assets/benchmark/file-20260116220829753.png)
![](assets/benchmark/file-20260116221029021.png)

連線
![](assets/benchmark/file-20260116221311945.png)
![](assets/benchmark/file-20260116221326403.png)

電池
![](assets/benchmark/file-20260116221406931.png)

Power
![](assets/benchmark/file-20260116221503514.png)![](assets/benchmark/file-20260116221511343.png)


example
 iPhone 17 Series Performance Review: Huge Leap! https://youtu.be/Y9SwluJ9qPI?si=W8SBEhL4D-ngn_sl
 Snapdragon 8 Gen 5 Review: Wrong Name, Okay Performance https://youtu.be/I4bJxrPV6ns?si=C9mIWQKuGWngtE9R
全球首开Switch 2芯片！性能到底有多强？
https://youtu.be/kXX9n62N72s?si=nhG2TR8FtdFda1Dp

https://sysprog21.github.io/rv32emu-demo/
![](assets/benchmark/file-20260117085442894.png)
![](assets/benchmark/file-20260117085703563.png)


## WASM 限制
**呼叫邊界成本**：JS ↔ Wasm 來回呼叫、資料轉換（尤其是物件/字串）會貴
**系統 API 受限**：在瀏覽器裡很多能力要走 Web API，跟 OS native syscall 路徑不同
**SIMD / Threads / GC 等特性可用性**：有些功能要看環境支援與編譯選項
**記憶體存取模式**：Wasm 很快的前提是你的程式本身 cache-friendly；random access 一樣慢
**I/O bound 工作**：瓶頸在網路/磁碟/DOM 時，Wasm 再快也救不了

## WASM 實際
CPU + 瀏覽器 Wasm JIT/AOT + 執行環境（電源管理/散熱/背景程序）