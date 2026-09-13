# OTA 與簽章流程實戰:Chip Vendor 視角

> 系列文章之五。總覽請見《Chip Vendor 視角的 Android Build System》。

簽章與 OTA 是 build system 的「最後一哩」,也是最容易在量產前夕出事的一哩:開發期一切正常,換 release key 後開不了機;OTA 包做出來了,裝置卻回報 signature mismatch。本文把金鑰體系、target-files 工作流、A/B 更新與 AVB 驗證串成一條完整的線。

---

## 一、金鑰體系:誰簽什麼

### 1.1 APK 簽章金鑰

AOSP build 內建四把 **test key**(`build/make/target/product/security/`),所有人共用、私鑰公開:

| Key | 簽什麼 |
|---|---|
| `platform` | 與 system 同 UID / 需要 `signature` 權限的 app |
| `shared` | contacts/launcher 家族 |
| `media` | media 相關 |
| `testkey`(releasekey) | 其他所有 app |

量產必須換成自己的 **release keys**——test key 簽的裝置等於沒鎖門(任何人都能簽出「系統級」app)。Chip vendor 的常見分工:公版/樣機用 test key 或 vendor 自己的 dev key,**量產 key 由 OEM 持有**,在 OEM 的簽章機房做 re-sign。

### 1.2 Verified Boot 金鑰(AVB)

**AVB(Android Verified Boot 2.0)** 負責開機鏈的完整性:

```
ROM/PBL(SoC 內建,信任根)
  └─ 驗證 bootloader(用燒進 fuse 的 OEM key hash)
      └─ bootloader 驗證 vbmeta.img(AVB key)
          └─ vbmeta 驗證 boot / vendor_boot / dtbo(hash descriptor)
                        與 system / vendor(dm-verity hashtree descriptor)
```

關鍵檔案與設定:

```makefile
# BoardConfig.mk
BOARD_AVB_ENABLE := true
BOARD_AVB_ALGORITHM := SHA256_RSA4096
BOARD_AVB_KEY_PATH := external/avb/test/data/testkey_rsa4096.pem   # 量產要換!
```

`vbmeta.img` 是所有 partition 驗證資訊的目錄;**chained partition** 機制允許把某些 partition(如 `boot` 用 Google 的 GKI 簽章、`vendor` 用你的 key)交給不同的 key 驗——這正是 chip vendor / Google / OEM 三方分權的機制。

此外還有 bootloader 階段的 **fuse/anti-rollback**:rollback index 防止刷回舊版(舊版可能有已知漏洞),OTA 時 `vbmeta` 中的 rollback index 遞增,fuse 燒錄後不可逆——測試時誤燒 fuse 是不可挽回的事故,量產設定要嚴格管控。

### 1.3 其他金鑰

- **kernel module 簽章**:GKI 要求 module 簽章或走 KMI 檢查。
- **APEX**:framework 模組化更新單元,各有自己的簽章 key + payload key。
- **OTA 包簽章**:整個 update zip 用 releasekey 簽,recovery/update_engine 驗證。

---

## 二、target-files:簽章與 OTA 的中樞

日常 `m` 出來直接刷機的 image 是 test key 簽的。正式流程全部繞著 **target_files.zip** 走:

```bash
m dist   # 或 m target-files-package
# 產物:out/dist/<product>-target_files-<build_id>.zip
```

這個 zip 裡有:所有 partition 的內容(尚未打包成最終 image)、META/ 設定(分割區大小、AVB 參數、fstab)、apkcerts.txt(每個 APK 用哪把 key)。它是後續一切的「原料」:

```
target_files.zip
  ├─ sign_target_files_apks ──▶ signed-target_files.zip    (換 release key)
  ├─ img_from_target_files ───▶ image.zip                  (fastboot 刷機包)
  └─ ota_from_target_files ───▶ ota.zip                    (OTA 更新包)
```

### 2.1 換 key:sign_target_files_apks

```bash
sign_target_files_apks \
  -o \                                          # 覆蓋 APK 簽章
  -d ~/.android-certs \                         # release keys 目錄
  --avb_vbmeta_key ~/keys/avb_release.pem \
  --avb_vbmeta_algorithm SHA256_RSA4096 \
  target_files.zip signed-target_files.zip
```

它做的事:重簽所有 APK/APEX、替換 OTA 驗證憑證、重算 AVB metadata、更新 `build fingerprint` 相關欄位。**簽章後的 target_files 才是量產的 single source of truth**——歸檔它,未來所有 incremental OTA 都要用它當基準。

### 2.2 產 OTA 包:ota_from_target_files

```bash
# Full OTA:從任何版本升上來
ota_from_target_files -k release_key signed-target_files.zip full-ota.zip

# Incremental OTA:從特定舊版升上來(小很多)
ota_from_target_files -k release_key \
  -i old-signed-target_files.zip \
  new-signed-target_files.zip incr-ota.zip
```

Incremental 是二進位 diff,所以**基準版本必須一個 byte 都不差**——這就是為什麼舊版 signed target_files 必須嚴格歸檔。裝置上任何 partition 被改過(root、手動 flash),incremental OTA 就會在驗證舊 partition hash 時失敗。

---

## 三、A/B(Seamless)Update

### 3.1 機制

現代裝置標配 **A/B 分區**:每個可更新 partition 有兩份 slot(`system_a`/`system_b`⋯⋯)。

```
使用者正常使用 slot A
   │
   ├─ update_engine 背景下載 OTA payload,寫入 slot B
   ├─ (Virtual A/B:寫入 COW snapshot,不需完整第二份空間)
   ├─ 驗證 slot B 的 hash / AVB
   ├─ 標記 slot B 為 active,重開機
   └─ 開機成功 → commit;開機失敗 N 次 → bootloader 自動 fallback 回 slot A
```

好處:更新中斷不會變磚、失敗自動回滾、使用者感知的 downtime 只有一次重開機。**Virtual A/B**(Android 11+ 標配)用 snapshot/COW 省掉靜態雙份空間,搭配 dynamic partitions(super.img)。

### 3.2 OTA 包的內容差異

A/B OTA 不是 recovery 腳本,而是 `payload.bin`(update_engine 格式)+ `payload_properties.txt`。Debug 手段:

```bash
adb logcat -s update_engine     # 更新進度與錯誤
adb shell update_engine_client --update --follow --payload=file:///...  # 手動餵包
bootctl get-active-boot-slot    # 查 slot 狀態
```

### 3.3 Chip vendor 要顧的事

- **Boot 相關 partition 的 slot 化**:`boot`、`vendor_boot`、`dtbo` 都是 A/B,bootloader 要正確處理 slot suffix 與 retry/fallback 計數。這段 code 在你的 bootloader 裡,Google 幫不了。
- **分割區大小規劃**:`BOARD_SUPER_PARTITION_SIZE` 要容納 Virtual A/B 的 snapshot 空間,估太緊會 OTA 失敗。
- **rollback index 策略**:哪個版本遞增、fuse 何時燒,要與 OEM 講清楚。
- **與 OEM 的責任切分**:通常 vendor 出 BSP 與工具鏈,OEM 端做簽章、OTA server 與版本管理;但 OTA 失敗最後 debug 的常常還是 BSP 團隊——payload 驗證失敗十之八九是「基準 target_files 對不上」或「有人動過 partition」。

---

## 四、量產前檢查清單

1. **User build + release key 完整驗證**:userdebug 過了不算數。
2. **AVB 全鏈驗證**:鎖 bootloader(`fastboot flashing lock`)後能正常開機;`avbtool verify_image` 自查。
3. **GKI boot.img 用 Google 簽章版本**:自編 debug kernel 換回 certified GKI。
4. **test key 清查**:`apkcerts.txt` 裡不得殘留 testkey;`androidboot.verifiedbootstate` 應為 green。
5. **OTA 演練**:full OTA、incremental OTA(前一個量產版 → 新版)、更新中斷斷電、開機失敗 fallback,四種都要實測。
6. **signed target_files 歸檔**:含簽章環境與工具版本——incremental OTA 的可重現性靠這個。
7. **金鑰治理**:release key 只存在 HSM/簽章機房;CI 禁止接觸;key rotation 計畫(APK 支援 v3 rotation,AVB key 換了就是不同信任根,要走 bootloader 支援)。

---

## 五、常見事故現場

**換 release key 後開不了機**
→ 多半是 AVB:image 是新 key 簽的,裝置 fuse/bootloader 還認舊 key hash;或 vbmeta 沒有跟著 re-sign。用 serial console 看 bootloader 的 AVB 錯誤碼。

**簽章權限 app 失效**
→ app 宣告 `sharedUserId` 或 signature 權限,但量產簽章時 `apkcerts.txt` 把它簽到別把 key。檢查 `LOCAL_CERTIFICATE` / `certificate:` 屬性。

**Incremental OTA 驗證失敗**
→ 基準 target_files 不是裝置上實際跑的那份(重簽過、重打包過、或裝置被動過)。改推 full OTA 止血,再查版本管理流程。

**OTA 後 vendor/system 不相容**
→ system 更新了但 vendor 沒跟上(或反過來),VINTF compatibility check 擋下。OTA 策略要決定:整包一起更,或確保跨版本 vendor interface 相容。

---

## 結語

簽章與 OTA 的核心是一條**信任鏈**與一份**可重現性**:

> **信任鏈從 SoC fuse 一路延伸到 APK 簽章,任何一環的 key 對不上,裝置就拒絕開機或拒絕更新;可重現性則繫於 signed target_files 的嚴格歸檔——它是量產版本唯一的事實來源。**

把「user build + release key + 鎖 bootloader + OTA 演練」做成 CI 的常態,而不是量產前一週的儀式,這條最後一哩就不會變成最後一劫。
