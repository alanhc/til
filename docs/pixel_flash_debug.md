# Flash History — Pixel 8 (shiba)

**Date:** 2026-05-03  
**Device:** Google Pixel 8 (codename: shiba)  
**Serial:** 38011FDJH00C9F  
**Bootloader:** ripcurrent-16.4-14097582  
**Baseband:** g5300i-250909-251024-B-14326967  
**Host:** macOS (darwin 25.3.0, Apple Silicon)  
**fastboot:** 37.0.0-14910828 (`/opt/homebrew/bin/fastboot`)  
**Image directory:** `/Users/alantseng/shiba-images`

---

## 問題經過

### 第一次嘗試（失敗）

從 `/Users/alantseng/shiba-images` 執行：

```bash
cd shiba-images   # 失敗：已在該目錄，找不到子目錄
ANDROID_PRODUCT_OUT=$(pwd) fastboot --disable-verity --disable-verification flashall -w
```

`cd shiba-images` 因工作目錄已是 `/Users/alantseng/shiba-images` 而失敗，但 `fastboot` 仍正常執行（`$(pwd)` 指向正確路徑）。

flash 進行到 `pvmfw_b` 寫入完成後中斷，錯誤訊息如下：

```
Sending 'boot_b' (65536 KB)                        OKAY [  1.565s]
Writing 'boot_b'                                   OKAY [  0.133s]
Sending 'init_boot_b' (8192 KB)                    OKAY [  0.196s]
Writing 'init_boot_b'                              OKAY [  0.017s]
Sending 'dtbo_b' (16384 KB)                        OKAY [  0.400s]
Writing 'dtbo_b'                                   OKAY [  0.026s]
Sending 'pvmfw_b' (1024 KB)                        OKAY [  0.032s]
Writing 'pvmfw_b'                                  OKAY [  0.009s]
fastboot: error: Failed to find AVB_MAGIC at offset: 0
```

### 根本原因分析

**`--disable-verity --disable-verification`** 這兩個 flag 讓 fastboot 在 flash 前嘗試對 vbmeta 相關 image 進行 patch（將 `FLAGS_HASHTREE_DISABLED` 與 `FLAGS_VERIFICATION_DISABLED` 寫入 vbmeta header）。

Pixel 8 有 `vendor_kernel_boot` 這個較新的 partition，對應的 `vbmeta_vendor_kernel_boot.img` 並不在 image 目錄中。fastboot 找不到該檔案時，嘗試讀取某個替代 image，但該 image 在 offset 0 沒有 `AVB0` magic，因此拋出：

```
Failed to find AVB_MAGIC at offset: 0
```

確認 image 目錄中的 vbmeta 檔案均正常（皆以 `AVB0` 開頭）：

| 檔案 | 大小 | Offset 0 |
|------|------|-----------|
| vbmeta.img | 8 KB | `AVB0` ✓ |
| vbmeta_system.img | 4 KB | `AVB0` ✓ |
| vbmeta_vendor.img | 4 KB | `AVB0` ✓ |

**注意：** Homebrew 安裝的 fastboot 與 Google 官方 Platform Tools 為完全相同的 binary（均為 37.0.0-14910828），更換 binary 無法解決此問題。

### 解決方案

這批 image 是以 release key 簽署的，dm-verity 在開機時可正常驗證，**不需要** disable verity。移除兩個 flag 後即可正常 flash：

```bash
cd /Users/alantseng/shiba-images
ANDROID_PRODUCT_OUT=$(pwd) fastboot flashall -w
```

---

## 成功 Flash 紀錄（2026-05-03）

**指令：**
```bash
ANDROID_PRODUCT_OUT=/Users/alantseng/shiba-images fastboot flashall -w
```

**Slot：** 切換至 slot b

| Partition | 大小 | 結果 | 耗時 |
|-----------|------|------|------|
| boot_b | 65536 KB | OKAY | send 1.553s / write 0.134s |
| init_boot_b | 8192 KB | OKAY | send 0.194s / write 0.018s |
| dtbo_b | 16384 KB | OKAY | send 0.389s / write 0.031s |
| pvmfw_b | 1024 KB | OKAY | send 0.027s / write 0.010s |
| vbmeta_b | 8 KB | OKAY | send 0.001s / write 0.011s |
| vbmeta_system_b | 4 KB | OKAY | send 0.001s / write 0.009s |
| vbmeta_vendor_b | 4 KB | OKAY | send 0.001s / write 0.008s |
| vendor_boot_b | 65536 KB | OKAY | send 1.569s / write 0.135s |
| vendor_kernel_boot_b | 65536 KB | OKAY | send 1.559s / write 0.127s |
| *(reboot into fastboot)* | — | OKAY | — |
| super (metadata) | 5 KB | OKAY | send 0.002s / write 0.129s |
| product_b | ~379 MB (2 sparse chunks) | OKAY | — |
| system_b | ~930 MB (4 sparse chunks) | OKAY | — |
| system_dlkm_b | 11504 KB | OKAY | send 0.300s / write 0.207s |
| system_ext_b | 213276 KB | OKAY | send 5.501s / write 0.687s |
| system_a (stub) | 59180 KB | OKAY | send 1.533s / write 0.209s |
| vendor_b | ~783 MB (3 sparse chunks) | OKAY | — |
| vendor_dlkm_b | 21368 KB | OKAY | send 0.569s / write 0.258s |
| userdata | erase + wipe | OKAY | 2.158s |
| metadata | erase | OKAY | 0.021s |

**總耗時：103.931 秒**

### 預期警告說明

- `Invalid sparse file format at header magic`：product / system / vendor 為 sparse image，fastboot 切分後分批傳送，此訊息為正常現象。
- `Erase successful, but not automatically formatting. File system type raw not supported.`：`/data` 與 `metadata` 將於首次開機時由 Android 自行格式化，正常現象。
- `wipe task partition not found: cache`：Pixel 8 採用 A/B + dynamic partition，沒有獨立的 cache partition，正常現象。
- `Setting current slot to 'b'`：A/B slot rotation，每次 flash 後交替，正常現象。

### 首次開機注意事項

- 首次開機會執行 dexopt（app 預先編譯），可能需要 **5–10 分鐘** 才會進入 launcher，屬正常現象。
- 因執行了 `-w`（wipe），userdata 已清除，裝置將以出廠狀態開機。
