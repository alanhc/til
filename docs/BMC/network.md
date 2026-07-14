# Network (phosphor-networkd)

`phosphor-network`

OpenBMC 的網路管理服務，負責 BMC 網卡的設定（IP、DNS、hostname、VLAN、NTP 等），並把設定透過 D-Bus 曝露給 Redfish / IPMI 使用。

- 專案：`phosphor-networkd`（daemon 名 `xyz.openbmc_project.Network`）。
- 底層通常搭配 **systemd-networkd**，networkd 服務會產生/管理 `.network` 設定。
- 設定項目：static / DHCP IPv4、IPv6、gateway、DNS、hostname、MAC、VLAN。
- D-Bus 物件路徑約在 `/xyz/openbmc_project/network/<interface>`。

常見操作：
- 透過 Redfish `EthernetInterfaces` 或 `busctl` 讀寫設定。
- 也可經 IPMI LAN channel 設定（相容舊工具）。

參考：https://github.com/openbmc/phosphor-networkd

相關筆記：ntp、redfish。
