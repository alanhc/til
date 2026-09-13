# HAL 開發實戰:從 AIDL 介面到開機起服務,End-to-End

> 系列文章之八。總覽請見《Chip Vendor 視角的 Android Build System》。

前面的文章分別講過 `Android.bp`(03)、sepolicy(04)、VINTF(01):本文把它們串成一條線——**從零寫一支 stable AIDL HAL,直到它在裝置上開機自動起來、framework 找得到、VTS 過得了**。以一支假想的 thermal 擴充 HAL 為例。

---

## 一、背景:HIDL → stable AIDL

| | HIDL | Stable AIDL |
|---|---|---|
| 引入 | Android 8(Treble) | Android 11 起主推 |
| 語言 | 自創 `.hal` | AIDL(與 app 層同源) |
| 現況 | **凍結,不收新介面**,存量逐步遷移 | 新 HAL 一律用這個 |
| 服務註冊 | hwservicemanager | servicemanager(與 framework 同一個) |

新開發只考慮 AIDL。維護舊平台時你仍會碰到 HIDL(`android.hardware.foo@2.4` 這種命名),概念可對照理解。

---

## 二、Step 1:定義介面(aidl_interface)

目錄結構(放在你的 `hardware/myvendor/` 或 `vendor/myvendor/interfaces/`):

```
vendor/myvendor/interfaces/thermal/
 ├─ Android.bp
 └─ vendor/myvendor/hardware/thermal/
     ├─ IThermalExt.aidl
     └─ ThrottleLevel.aidl
```

```java
// IThermalExt.aidl
package vendor.myvendor.hardware.thermal;
import vendor.myvendor.hardware.thermal.ThrottleLevel;

@VintfStability
interface IThermalExt {
    ThrottleLevel getThrottleLevel(in String zone);
    void setPolicy(in String policy);
}
```

```python
// Android.bp
aidl_interface {
    name: "vendor.myvendor.hardware.thermal",
    vendor_available: true,
    srcs: ["vendor/myvendor/hardware/thermal/*.aidl"],
    stability: "vintf",
    owner: "myvendor",
    backend: {
        java: { enabled: true },   // 若有 system 端 Java client
        ndk: { enabled: true },    // HAL 實作用 NDK backend
    },
}
```

關鍵:`stability: "vintf"` + `@VintfStability`。第一次 build 後執行:

```bash
m vendor.myvendor.hardware.thermal-freeze-api   # 凍結 version 1
```

凍結產生 `aidl_api/` 快照,之後任何介面變更都會被 build system 比對——**改凍結過的介面 = build fail**,要嘛開新 version,要嘛 revert。這就是你對客戶的 ABI 合約(對照 GKI 篇的 KMI:一個管 kernel,一個管 HAL)。

---

## 三、Step 2:實作 service

```
vendor/myvendor/thermal-service/
 ├─ Android.bp
 ├─ main.cpp
 ├─ ThermalExt.h / ThermalExt.cpp
 ├─ thermal-ext-service.rc
 └─ thermal-ext-service.xml        # VINTF fragment
```

```cpp
// ThermalExt.h
#include <aidl/vendor/myvendor/hardware/thermal/BnThermalExt.h>

class ThermalExt : public aidl::vendor::myvendor::hardware::thermal::BnThermalExt {
    ndk::ScopedAStatus getThrottleLevel(const std::string& zone,
                                        ThrottleLevel* _aidl_return) override;
    ndk::ScopedAStatus setPolicy(const std::string& policy) override;
};
```

```cpp
// main.cpp
#include <android/binder_manager.h>
#include <android/binder_process.h>

int main() {
    auto service = ndk::SharedRefBase::make<ThermalExt>();
    const std::string name =
        std::string(ThermalExt::descriptor) + "/default";
    binder_exception_t st =
        AServiceManager_addService(service->asBinder().get(), name.c_str());
    CHECK_EQ(st, EX_NONE);
    ABinderProcess_joinThreadPool();
    return EXIT_FAILURE;   // joinThreadPool 不應返回
}
```

```python
// Android.bp
cc_binary {
    name: "vendor.myvendor.thermal-service",
    vendor: true,
    relative_install_path: "hw",
    srcs: ["main.cpp", "ThermalExt.cpp"],
    shared_libs: [
        "libbase", "libbinder_ndk",
        "vendor.myvendor.hardware.thermal-V1-ndk",
    ],
    init_rc: ["thermal-ext-service.rc"],
    vintf_fragments: ["thermal-ext-service.xml"],
}
```

---

## 四、Step 3:init.rc 與 VINTF——讓它開機起來、被找到

```
# thermal-ext-service.rc
service vendor.thermal-ext /vendor/bin/hw/vendor.myvendor.thermal-service
    class hal
    user system
    group system
    capabilities SYS_NICE
```

```xml
<!-- thermal-ext-service.xml(VINTF fragment)-->
<manifest version="1.0" type="device">
    <hal format="aidl">
        <name>vendor.myvendor.hardware.thermal</name>
        <version>1</version>
        <fragment/>
        <interface>
            <name>IThermalExt</name>
            <instance>default</instance>
        </interface>
    </hal>
</manifest>
```

VINTF 這邊有兩份文件在對帳(詳見總覽篇):device manifest(我提供什麼,由各 fragment 組合)與 framework compatibility matrix(需要什麼)。自定 vendor HAL 通常只出現在 manifest;若 system 端有你自己的 client,也要把需求寫進 DCM(device compatibility matrix)讓檢查完整。

檢查工具:

```bash
adb shell vintf check                # 裝置上檢查 manifest/matrix 相容
m check-vintf-all                    # build time 全量檢查
```

---

## 五、Step 4:sepolicy——讓它活下來

沒有 policy,service 一啟動就死(或 servicemanager 拒絕註冊)。最小集合(詳細除錯見 sepolicy 篇):

```
# device/myvendor/common/sepolicy/vendor/thermal_ext.te
type thermal_ext, domain;
type thermal_ext_exec, exec_type, vendor_file_type, file_type;
init_daemon_domain(thermal_ext)

binder_use(thermal_ext)                          # 用 binder
add_service(thermal_ext, thermal_ext_service)    # 註冊 service
allow thermal_ext sysfs_thermal:file r_file_perms;

# service_contexts
vendor.myvendor.hardware.thermal.IThermalExt/default u:object_r:thermal_ext_service:s0

# file_contexts
/vendor/bin/hw/vendor\.myvendor\.thermal-service u:object_r:thermal_ext_exec:s0
```

另外在 `service.te`(或同檔)補 `type thermal_ext_service, service_manager_type, hal_service_type;`。Client 端(如果是你的 system 端元件)還需要 `find` 該 service 的 allow 規則。

---

## 六、Step 5:掛進 product、驗證

```makefile
# device.mk
PRODUCT_PACKAGES += vendor.myvendor.thermal-service
```

驗證清單:

```bash
adb shell ps -AZ | grep thermal            # 起來了嗎?domain 對嗎?
adb shell service list | grep myvendor     # 註冊成功?
adb shell dmesg | grep avc | grep thermal  # sepolicy denial?
adb shell vintf check                      # VINTF 相容?
```

Client 端呼叫(NDK backend 為例):

```cpp
auto binder = ndk::SpAIBinder(AServiceManager_waitForService(
    "vendor.myvendor.hardware.thermal.IThermalExt/default"));
auto hal = IThermalExt::fromBinder(binder);
```

**VTS**:自定 vendor HAL 要自己寫 VTS test(`VtsHalTargetTest` 模板,gtest + 對每個 declared instance 跑),放進 `test_suites: ["vts"]`。標準 HAL(`android.hardware.*`)則有現成 VTS,你的實作要通過它(詳見 xTS 篇)。

---

## 七、版本演進與多實例

**加方法** = 開新版本:

```bash
# 修改 .aidl 後
m vendor.myvendor.hardware.thermal-freeze-api    # 凍成 V2
```

Service 端可同時支援 V1/V2 client(AIDL 向下相容:新方法舊 client 不呼叫即可);manifest 的 `<version>` 更新。**刪方法、改簽名 = 不允許**,只能加。

**多實例**:同一介面可註冊多個 instance(`/default`、`/soc`⋯⋯),VINTF fragment 逐一宣告——多顆相同 IP(如雙 ISP)的標準做法。

**HIDL 遷移備忘**:`hidl2aidl` 工具可轉介面初稿;passthrough mode(同進程載入 `.so`)在 AIDL 時代已不建議,一律 binderized。

---

## 結語

一支 HAL 要活起來,五個檔案缺一不可:

> **`.aidl` 定合約(freeze 後不可毀約)、`Android.bp` 編出來、`.rc` 讓 init 起它、VINTF fragment 讓 framework 承認它、sepolicy 讓它有權做事。** 開機後 `ps -AZ`、`service list`、`dmesg | grep avc`、`vintf check` 四連,就是 HAL 工程師的健檢四件套。
