# Yocto Project

Yocto 是一套用來「打造客製化 embedded Linux 發行版」的建構框架。它不是一個發行版，而是幫你從原始碼建出專屬的 toolchain、kernel、rootfs image 的工具集。核心建構引擎是 **BitBake** 搭配 **OpenEmbedded**。

## 核心概念

- **BitBake**：任務排程與建構引擎，解析 recipe、處理相依、執行 fetch/compile/package 等 task。
- **Recipe (`.bb`)**：描述「如何建一個套件」——原始碼來源 (`SRC_URI`)、版本、相依 (`DEPENDS`)、編譯與安裝步驟。
- **Layer (`meta-*`)**：一組 recipe/設定的集合，可疊加組合（如 `meta`、`meta-poky`、BSP 的 `meta-<vendor>`）。以 `bblayers.conf` 管理啟用哪些 layer。
- **Machine / Distro**：`MACHINE` 指定目標硬體，`DISTRO` 指定發行版政策。

## 基本流程

```bash
source oe-init-build-env      # 設定環境、進入 build/
# 編輯 conf/local.conf 設定 MACHINE 等
bitbake core-image-minimal    # 建構目標 image
```

產物在 `tmp/deploy/images/<machine>/`，包含 kernel、device tree 與 **rootfs image**（如 `.wic`、`.ext4`、`.tar.bz2`），可燒錄到目標板。

參考：https://docs.yoctoproject.org/
