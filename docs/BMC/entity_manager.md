# Entity Manager

OpenBMC 用來「描述硬體並動態探測」的服務。用 JSON 檔描述一塊板子上有哪些元件（sensor、fan、FRU、電源等），開機時依偵測結果決定要啟用哪些設定。

運作方式：
- **設定檔**：JSON 放在 `configurations/`，描述 `Exposes`（該板提供的 sensor/裝置）與 `Probe`（探測條件）。
- **Probe**：常用 FRU EEPROM 內容（如 `PRODUCT_PRODUCT_NAME`）比對，命中才套用該設定。
- 探測成功後，把裝置與設定放上 D-Bus (`xyz.openbmc_project.Configuration.*`)。
- 其他服務（dbus-sensors、phosphor-pid-control 等）訂閱這些 D-Bus 設定，動態建立 sensor 與控制迴路。

好處：
- 同一份 image 支援多種板型（不同硬體自動選對設定）。
- 新增硬體多半只要加 JSON，不必改 C++。

參考：https://github.com/openbmc/entity-manager

相關筆記：hwmon、pid_control、fru、hotplug。
