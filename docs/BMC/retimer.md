# PCIe Retimer

高速訊號在 PCB 上走長距離會衰減，Retimer 是主動元件，負責把 PCIe 訊號重新取樣、重建（re-clock），恢復乾淨的眼圖，延長可用走線距離。

- 對比 **redriver**：redriver 只做類比等化/放大（不重生時脈）；**retimer** 有 CDR，會完整重建訊號，等於一個新的訊號起點。
- 常見於 PCIe Gen4/Gen5 需要跨 riser、cable、backplane 的長通道。
- 每顆 retimer 都有 EEPROM/eye margin 等狀態，通常透過 I2C/SMBus 由 BMC 存取。

韌體更新：
- Retimer 有自己的 firmware，需要定期更新以修正訊號調校或相容性問題。
- BMC 常透過 I2C 或 PLDM (Type 5, firmware update) 更新其 firmware，並回報版本。
- 更新流程通常需要在特定 power state 下進行，避免影響鏈路。

相關筆記：mctp、redfish（firmware inventory / update）。
