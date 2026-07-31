# SELinux Sepolicy 除錯實戰:Chip Vendor 視角

> 系列文章之四。總覽請見《Chip Vendor 視角的 Android Build System》。

對 BSP 工程師來說,sepolicy 是「功能明明寫好了,一跑就 permission denied」的萬年嫌疑犯。本文從 Treble 之後的 policy 架構講起,建立一套系統化的除錯流程:看懂 avc denial、產生規則、放對位置、避開 neverallow,以及那些 audit2allow 不會告訴你的坑。

---

## 一、架構:policy 也被 Treble 切成兩半

### 1.1 目錄結構

```
system/sepolicy/          # Platform policy,Google 管,不要動
  public/                 # 對 vendor 可見的 type/attribute 定義
  private/                # platform 內部,vendor 不可引用
  vendor/                 # Google 提供的 vendor 端通用 policy
device/<vendor>/<board>/sepolicy/   # 你的地盤
  *.te                    # type enforcement 規則
  file_contexts           # 檔案 → security context 對應
  service_contexts        # binder service → context
  property_contexts       # system property → context
  hwservice_contexts      # HIDL service → context
  genfs_contexts          # sysfs/procfs 節點 → context
```

`BoardConfig.mk` 把你的目錄掛進去:

```makefile
BOARD_VENDOR_SEPOLICY_DIRS += device/myvendor/myboard/sepolicy/vendor
```

### 1.2 核心概念速記

- 一切皆有 **security context**:`u:r:my_hal_camera:s0`(process)、`u:object_r:vendor_camera_file:s0`(檔案)。
- **Type enforcement**:預設全部拒絕,規則只能開洞:`allow <source> <target>:<class> <permissions>;`
- **Domain** = process 的 type。daemon 啟動時透過 `init` + `domain_trans` 進入自己的 domain。
- **Attribute** = type 的集合(如 `coredomain` 代表所有 platform process),neverallow 大量用它。
- Vendor process **必須**離開 `coredomain` 之外;你不能定義 platform type,只能引用 `public/` 裡的。

---

## 二、系統化除錯流程

### Step 0:先確認真的是 SELinux

```bash
adb shell getenforce            # Enforcing / Permissive
adb shell setenforce 0          # 暫時切 permissive(userdebug/eng 才可以)
```

切 permissive 後功能正常 → 是 sepolicy 問題;還是壞 → 別浪費時間查 policy。**注意**:有些 denial 標了 `permissive=1` 仍會列印但不阻擋;另外 Android 對 vendor 的要求是量產必須 enforcing,permissive 只是除錯手段。

### Step 1:抓 denial

```bash
adb shell dmesg | grep avc          # kernel log
adb logcat -b events | grep avc    # userspace(logd)
```

典型 denial 長這樣:

```
avc: denied { read write } for pid=1234 comm="my_hal_camera"
     name="video0" dev="tmpfs" ino=567
     scontext=u:r:my_hal_camera:s0
     tcontext=u:object_r:video_device:s0
     tclass=chr_file permissive=0
```

逐欄位讀:

| 欄位 | 意義 |
|---|---|
| `{ read write }` | 被拒絕的 permission |
| `scontext` | 誰(source domain) |
| `tcontext` | 對什麼(target type) |
| `tclass` | 物件類別(file、chr_file、binder、property_service⋯⋯) |
| `permissive` | 0=真的被擋,1=只記錄未阻擋 |

### Step 2:用 audit2allow 產生候選規則

```bash
adb shell dmesg | grep avc | audit2allow -p out/.../precompiled_sepolicy
# 或在 host 上:
cat denials.txt | audit2allow
```

輸出:

```
allow my_hal_camera video_device:chr_file { read write };
```

**但不要無腦照抄**,先問三個問題(見第三節)。

### Step 3:放進正確的 .te 檔

```
# device/myvendor/myboard/sepolicy/vendor/my_hal_camera.te
type my_hal_camera, domain;
type my_hal_camera_exec, exec_type, vendor_file_type, file_type;

init_daemon_domain(my_hal_camera)          # init 啟動時轉入此 domain

allow my_hal_camera video_device:chr_file rw_file_perms;
binder_call(my_hal_camera, servicemanager)
```

盡量用 `system/sepolicy` 提供的 **macro**(`rw_file_perms`、`binder_call`、`get_prop` 等),比裸寫 permission 精確且可讀。

### Step 4:確認 label 本身是對的

一半以上的 denial 根因不是「缺 allow 規則」,而是**東西被標錯了 type**:

```bash
adb shell ls -Z /dev/video0                    # 看檔案 context
adb shell ps -AZ | grep my_hal                 # 看 process domain
```

危險訊號:

- tcontext 出現 `default` 家族——`vendor_default_prop`、`device`、`unlabeled`、`vendor_file`(泛用型)→ 表示你根本沒幫它定 label。**正解是補 contexts 檔,不是 allow 一個 default type**(多半也會撞 neverallow)。
- process 跑在 `su` / `shell` / `init` 而不是自己的 domain → `init_daemon_domain` 沒生效,檢查 exec 檔的 label 與 init.rc。

補 label 的位置:

```
# file_contexts
/dev/my_isp[0-9]*         u:object_r:my_isp_device:s0
/vendor/bin/hw/my-service u:r:my_hal_camera_exec:s0

# genfs_contexts(sysfs/procfs 無法用 file_contexts)
genfscon sysfs /devices/platform/my_isp u:object_r:sysfs_my_isp:s0

# property_contexts
vendor.myvendor.camera.   u:object_r:vendor_camera_prop:s0

# service_contexts(AIDL service)
vendor.myvendor.hardware.thermal.IThermal/default u:object_r:my_thermal_service:s0
```

改 `file_contexts` 後,已存在的檔案要 `restorecon`(或重刷 image)才會重新標籤。

### Step 5:重 build、驗證

```bash
m selinux_policy                     # 只編 policy
adb push ... && adb reboot           # 或整包重刷 vendor
adb shell dmesg | grep avc           # 確認 denial 消失
```

---

## 三、audit2allow 之外:判斷「該不該 allow」

拿到候選規則後,三個必問:

**1. 這是不是 neverallow 禁區?**

Google 在 `system/sepolicy` 定義了大量 `neverallow`,violation 會**直接 build fail**(CTS 也會再驗一次)。經典禁區:vendor domain 不得直接讀寫 `system_data_file`、不得 `dlopen` system 私有庫、不得對 `coredomain` 任意 binder call、app domain 不得直接開 device node。撞到時的訊息:

```
libsepol.report_failure: neverallow violated by
  allow my_hal_camera system_data_file:file { read };
```

撞到 neverallow = **設計錯了**,不是 policy 寫法問題。正解通常是:改走 HAL/AIDL 介面、把檔案搬到 `/data/vendor`、或用 property 溝通。

**2. 範圍是不是開太大?**

`audit2allow` 只看見一次 denial,常誘導你寫出過寬的規則。`allow my_hal vendor_file:file *` 這種東西過得了今天,過不了 security review 與下一次 GMS 認證。針對實際需要的 type + permission 開最小洞。

**3. 是不是 label 問題假扮成 permission 問題?**(見 Step 4)

---

## 四、Chip vendor 特有的坑

**dontaudit 吃掉 log**:setenforce 0 後功能正常、卻完全找不到 denial?可能被 `dontaudit` 規則靜音了。除錯做法:在 `out/` 下的 CIL 產物(如 `plat_sepolicy.cil`、`vendor_sepolicy.cil`)搜尋相關 type 的 `dontaudit` 規則確認嫌疑,然後暫時把該規則從 policy source 註解掉、重編 policy 再抓一次 log。確認完記得還原——那些 dontaudit 多半是 Google 刻意加來壓噪音的。

**開機早期的 denial**:first-stage init、載入 vendor_boot module 時的 denial 只在 serial console/`dmesg` 有,logcat 看不到,而且時間點在 policy load 之前的行為不受 policy 管——看到 `security_load_policy` 的時間戳再判讀。

**property 的兩段權限**:設 property 要 `set_prop`(source 端),讀要 `get_prop`;vendor 與 system 互讀 property 還要看 property 本身的 context 是否雙方可見。跨界 property 建議走 `vendor.` 前綴並在 `property_contexts` 明確定 label。

**多專案共用 policy**:公版 sepolicy 放 `device/<vendor>/common/sepolicy`,專案差異放專案目錄,兩者都掛進 `BOARD_VENDOR_SEPOLICY_DIRS`。同名 type 重複定義會 build fail,公版要用 attribute 與 macro 留擴充點。

**VTS/CTS 相關檢查**:`neverallow` 之外,CTS 有 `SELinuxHostTest` 檢查 policy 格式與禁用 pattern;GMS 認證前跑一次 `sepolicy-analyze` 自查:

```bash
sepolicy-analyze precompiled_sepolicy permissive   # 不得有 permissive domain
sepolicy-analyze precompiled_sepolicy neverallow -w -f neverallows.txt
```

---

## 五、除錯心智圖(速查)

```
功能失敗
 ├─ setenforce 0 後正常?
 │   ├─ 否 → 不是 SELinux,去查別的
 │   └─ 是 → 抓 avc denial
 │        ├─ 沒有 denial → 懷疑 dontaudit / 開機早期 → serial console
 │        └─ 有 denial
 │             ├─ tcontext 是 *_default / unlabeled / device?
 │             │    └─ 是 → 補 file_contexts / genfs / property_contexts + restorecon
 │             ├─ scontext 不是預期 domain?
 │             │    └─ 是 → 查 exec label + init_daemon_domain
 │             └─ label 都對 → audit2allow 產生候選
 │                  ├─ 撞 neverallow? → 重新設計(走 HAL/AIDL/搬路徑)
 │                  └─ 沒撞 → 縮小範圍、用 macro、放對 .te → 重驗
```

---

## 結語

Sepolicy 除錯的本質是**讀懂 denial 的四元組(scontext, tcontext, tclass, permission),然後在「補 label」「開最小洞」「重新設計」三個選項中做對選擇**。`audit2allow` 只是打字員,判斷永遠在你:被 neverallow 擋下來的,從來不是 policy 問題,而是架構在提醒你——那條路 Google 不想讓任何 vendor 走。
