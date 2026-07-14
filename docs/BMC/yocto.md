# Yocto Project

OpenBMC 用 **Yocto Project** 這套嵌入式 Linux build 框架來產生 BMC firmware image。它不是一個發行版，而是「幫你組出自己發行版」的工具鏈。

核心概念：
- **bitbake**：build 引擎，解析 recipe、處理相依、跑各 task（fetch/compile/install/package）。
- **recipe (`.bb`)**：描述單一軟體怎麼抓原始碼、編譯、安裝；`.bbappend` 用來覆寫/擴充既有 recipe。
- **layer (`meta-*`)**：一組 recipe 與設定的集合，可疊加。OpenBMC 有 `meta-phosphor`、各廠 `meta-<vendor>` / `meta-<board>`。
- **image recipe**：定義最終要放進 rootfs 的套件集合。
- **machine / distro conf**：選硬體與發行版設定。

常見流程：

```bash
. setup <machine>        # OpenBMC 提供的環境設定
bitbake obmc-phosphor-image
```

- 產物在 `tmp/deploy/images/<machine>/`（含可燒錄的 flash image）。

參考：https://www.yoctoproject.org/

相關筆記：openbmc、flash、device_tree。
