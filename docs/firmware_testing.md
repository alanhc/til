# 韌體自動化測試

韌體測試和一般軟體測試最大的差別是：**測試對象是一塊實體板子**。你不能像跑 unit test 那樣「開一個 container 跑完就丟」，而是要處理燒錄、上電、序列埠輸出、板子當掉要能強制斷電重來這些事。

自動化韌體測試的核心問題因此是：**如何把「一堆板子」變成一個可以被 CI 排程的資源池**。

## LAVA

**LAVA**（Linaro Automated Validation Architecture）是 Linaro 開發的開源自動化測試框架，是這個領域最主流的方案。它把實體板子抽象成可排程的資源。

架構分兩層：

- **lava-server**：接收測試任務、排程、管理板子清單（device dictionary）、保存結果。有 Web UI 與 REST API，可被 CI 觸發。
- **lava-dispatcher**：實際跑測試的機器，接在板子旁邊，負責燒錄 image、控制電源、抓序列埠輸出。

一個 LAVA job 定義通常包含三段：

| 階段 | 做的事 |
|---|---|
| **deploy** | 把要測的 kernel / rootfs / 韌體 image 送到板子上（TFTP、fastboot、USB、直接燒 flash） |
| **boot** | 上電並等待開機，用序列埠的字串比對判斷有沒有開起來 |
| **test** | 在板子上執行測試腳本，把結果以特定格式印到 console，由 LAVA 解析 |

它解決的關鍵問題：

- **電源控制**：透過 PDU（可網控電源排插）或 relay 強制斷電重開，讓板子當掉時測試不會卡死。
- **序列埠擷取**：多數嵌入式測試唯一的輸出管道就是 UART，LAVA 統一收集並依 pattern 判斷成敗。
- **板子共用**：一整櫃板子由 server 統一排程，多個 CI job 可以排隊使用，不必每個工程師桌上放一塊。

## openQA

**openQA** 是 SUSE 開發的自動化測試框架，取徑完全不同：**以螢幕截圖比對為主**。它在虛擬機或實體機上跑系統，定期截圖，與預期的參考圖比對來判斷狀態，再用模擬的鍵盤滑鼠輸入來操作。

適合測試「有畫面」的東西——BIOS setup 選單、安裝流程、圖形介面。缺點是參考圖維護成本高，UI 一改就要重新截圖。

FOSDEM 2022 有一場講 LAVA 與 openQA 如何搭配使用（一個測 boot/console、一個測畫面）：[LAVA and openQA](https://archive.fosdem.org/2022/schedule/event/lava_openqa/)

## Linaro Validation Lab

[validation.linaro.org](https://validation.linaro.org/) 是 Linaro 對外開放的公開 LAVA 實例，可以直接看到真實專案怎麼組織測試 job、以及各種 ARM 板子的實際測試結果。要學 LAVA 的 job 定義寫法，看這裡的實例比讀文件快。

Linaro 也寫過一篇說明近年 LAVA 易用性改善的文章：[Why is LAVA now easier to use](https://www.linaro.org/blog/why-is-lava-now-easier-to-use)

## 韌體團隊的 CI/CD

除了「怎麼測」，還有「什麼時候測、測完怎麼辦」的流程問題。

典型的韌體 CI pipeline：

```
commit
  ↓
靜態檢查（clang-format、cppcheck、checkpatch）
  ↓
交叉編譯（多個 target 平行編）
  ↓
單元測試（在 host 上跑，不需要板子）
  ↓
上板測試（LAVA：燒錄 → 開機 → 功能測試）
  ↓
產出 nightly image
  ↓
（人工 sign-off）→ RC image → QA 正式驗證
```

幾個實務要點：

- **分層測試**：能在 host 上跑的（靜態檢查、unit test）就不要佔用板子資源，板子只跑非跑不可的整合測試。板子是稀缺資源。
- **build once, promote many**：同一份 binary 一路晉升通過各關卡，不要在每個階段重編。詳見 [韌體 image 管理](./firmware_image_management.md)。
- **測試要能區分「板子壞了」與「程式壞了」**：硬體不穩定造成的 false failure 會迅速摧毀團隊對 CI 的信任。

參考文章：
- [CI/CD for Firmware Teams（Dojo Five）](https://dojofive.com/blog/ci-cd-for-firmware-teams-how-to-streamline-your-workflow/)
- [OpenWrt CI/CD 做法](https://www.kmai.com.tw/openwrt-ci-cd-%E5%81%9A%E6%B3%95/)

## 相關筆記

- [BMC 韌體測試流程](./BMC/testing.md) — test plan / functional testing / report 的實務分工
- [韌體 image 管理](./firmware_image_management.md) — release channel 與 build promotion
