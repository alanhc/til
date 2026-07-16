---
sidebar_label: MTK Preloader Combo Header
---

# MTK Preloader Combo Header 與 Google OTA 流程整理

> 整理日期:2026-07-16
> 資料來源標註:[公開] = 可從公開 code/文件驗證(mtkclient、u-boot、XDA dump);[推論/內部] = 邏輯推論或需 MTK 內部 source 確認。

---

## 1. 背景:Preloader 住在哪裡

- MTK boot chain 前段:**BROM → Preloader → LK/BL2 → ...**
- Preloader **不在 GPT 分割區**,而是住在 hardware boot region:
  - eMMC:boot0 / boot1 hardware partition(`/dev/block/mmcblk0boot0`、`mmcblk0boot1`)
  - UFS:boot LU(LU0/LU1,device node 通常是 `/dev/block/sda`、`sdb`)
- BROM 讀 boot region 時,要求最前面有一顆 **device header**(boot header),驗過才會載入真正的 preloader 程式碼。

## 2. Device header 的三種型態 [公開]

實際 dump boot0/boot1,開頭 magic 會是三者之一:

| Magic | 意義 |
|---|---|
| `EMMC_BOOT` | 單一 eMMC 用 header |
| `UFS_BOOT` | 單一 UFS 用 header |
| `COMBO_BOOT` | **Combo header**:一份 image 同時支援多種 storage |

(來源:XDA MTK unbrick guide 的 hex dump 觀察、mtkclient parser。)

## 3. Binary layout(單一 header,以 eMMC 為例)[公開,mtkclient 驗證]

mtkclient `Tools/preloader_emu_mmc.py` 的 parsing 邏輯:

```
0x000  "EMMC_BOOT\0"        ← device header magic(UFS 為 "UFS_BOOT")
0x008  version
0x010  u32 → BRLYT offset    (通常 0x200)
──────────────────────────────
BRLYT:  "BRLYT" magic        ← BootROM Layout header
BRLYT+0x0C  u32 → preloader 本體 start offset(常見 0x800 / 0x1000)
──────────────────────────────
GFH:    "MMM\x01" ... "FILE_INFO"   ← 真正的 preloader binary 從這裡開始
GFH+0x20  u32 → preloader 長度
```

三層結構:**device header(跳板)→ BRLYT(layout)→ GFH/FILE_INFO(本體)**。

補充 [公開]:u-boot `tools/mtk_image.h` 有舊平台(MT76xx 路由器線)的 struct 定義——`gen_boot_header`(name[12] + version + size,padding 到 0x200)、`brom_layout_header`(BRLYT magic `0x42424242`、type enum:EMMC=0x10005、SDMMC=0x10008 等)。但 u-boot **沒有 COMBO_BOOT**,combo 是手機線(MT67xx/MT68xx)的東西。

## 4. Combo header 是什麼 [公開 magic + 推論/內部 struct]

- 概念:把最外層 device header 換成一個**容器**,裡面放多組 entry,每組對應一種 storage type/設定,各自指向對應的 BRLYT/GFH。eMMC BROM 和 UFS BROM 各認各的 entry。
- 動機:量產機種常有 **second source 料件**(同專案出 eMMC 版 + UFS 版,或不同顆粒)。Combo header 讓工廠和 OTA 只需維護**一份 preloader image**,不用按料件分兩份。
- ⚠️ 精確的 struct 欄位**不在公開 code**:mtkclient 只認 magic 沒展開欄位;u-boot 沒有。最準的來源是 MTK 內部 DA source 或 preloader build 產 header 的 pack 工具(`pl` 的 mkimage 那段)。

## 5. 跟 Google A/B OTA(update_engine)的接法

1. **Build 端** [推論/內部可驗]:`AB_OTA_PARTITIONS += preloader`;target_files 裡放的是**含 device header 的 raw image**,不是純 preloader binary。
   - 對比:SP Flash Tool 燒錄路徑是由工具/DA 負責 header;OTA 路徑 update_engine 只會 byte-level 寫入,所以 image 必須自帶 header。
2. **Device 端** [推論/內部可驗]:init 階段由 MTK plpath utils 建 by-name symlink:
   - eMMC:`preloader_a → mmcblk0boot0`、`preloader_b → mmcblk0boot1`,且需清 `/sys/block/mmcblk0bootX/force_ro`
   - UFS:指到 boot LU(sda/sdb)
3. **update_engine 視角**:它不知道這是特殊區域,就是照 payload 做 byte-level 讀寫 + hash 驗證。因此:
   - **Incremental OTA 的 source verification** 要求裝置上 boot region 實際內容(**含 header 型態**)與 build 端的 source image 完全一致。

## 6. 常見故障模式

| 情境 | 結果 |
|---|---|
| 工廠燒錄的 header 型態(如純 EMMC_BOOT)≠ OTA image 的(如 COMBO_BOOT) | incremental OTA source hash mismatch → verify 階段 fail |
| 有人用 mtkclient / SPFT 重刷過 preloader(header 或 padding 不同) | 同上 |
| Full OTA 寫入了與裝置 storage 不匹配的 header | 最壞情況開機磚(BROM 認不得 header) |
| Combo 的另一面:若不用 combo,不同料件機器各燒各的 header | OTA 得出多份 payload;統一 combo image 則一份通吃 |

## 7. Debug 快速驗法

```bash
# 裝置端 dump boot region 開頭
dd if=/dev/block/mmcblk0boot0 of=/tmp/boot0_head.bin bs=4096 count=1

# 跟 target_files/IMAGES/ 裡的 preloader image 開頭 diff
xxd boot0_head.bin | head
xxd preloader_xxx.img | head
```

對三個點:**magic 字串、BRLYT offset(0x10 處的 u32)、GFH 起始 offset**。一對就知道是不是 header 型態不一致。

## 8. 參考來源

- mtkclient(bkerler/mtkclient):`Tools/preloader_emu_mmc.py`、`mtkclient/Library/partition.py` — header parsing 邏輯
- u-boot `tools/mtk_image.h` / `mtk_image.c` — 舊平台 device header/BRLYT struct 定義
- XDA: "Fixing Bricked Preloader on Mediatek MTK Devices" — EMMC_BOOT/UFS_BOOT/COMBO_BOOT magic 與 FILE_INFO offset 的實機 dump 觀察
- MediaTek IoT Yocto 文件 — BROM 僅支援 eMMC/UFS boot、boot partition fallback 行為
