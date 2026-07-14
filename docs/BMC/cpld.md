# CPLD

**CPLD**（Complex Programmable Logic Device）是板上的可程式邏輯裝置，容量介於 GAL 與 FPGA 之間，非揮發（開機即運作，不需外部載入 bitstream）。伺服器主機板常用它做「膠合邏輯」與時序控制。

常見用途：
- **Power sequencing**：依正確順序與時序拉起各組電源 rail，等 power-good 才進下一步。
- **Reset / clock 邏輯**：管理 reset 樹、時脈致能。
- **Glue logic**：把各晶片間零散的訊號整合、解碼。
- **presence / strap 讀取**：彙整板上偵測訊號給 BMC。

與 BMC 的關係：
- BMC 常透過 GPIO、I2C 或 JTAG 與 CPLD 互動，讀取電源狀態、觸發 power on/off。
- CPLD firmware（邏輯）可更新，BMC 有時負責在板上更新（in-system programming）。

相關筆記：cpld 常是 openbmc_boot_flow 中電源時序的關鍵一環。
