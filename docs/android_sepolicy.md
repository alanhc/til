# Android SEPolicy / SELinux

Android 使用 SELinux 做強制存取控制（MAC），對每個 process 與資源標上 security context，並依 policy 規則決定是否允許操作。

## 核心概念
- **Security context**：`user:role:type:mls` 格式，例如 `u:r:untrusted_app:s0`。權限判斷主要看 type（Type Enforcement）。
- **`.te` 檔**：定義某個 domain 的規則，例如 `allow` / `neverallow`。
- **`allow`**：`allow <source_type> <target_type>:<class> <permissions>;`。
- **`neverallow`**：編譯期檢查的禁止規則，違反會導致 build 失敗，用來守住安全底線。
- **file_contexts**：把檔案路徑對應到 type（label）。

## AVC denied
權限被拒時會在 `dmesg` / `logcat` 出現 audit log：

```
avc: denied { read } for pid=1234 comm="myproc" name="foo" \
  scontext=u:r:mydomain:s0 tcontext=u:object_r:mytype:s0 tclass=file
```

從 `scontext`（來源）、`tcontext`（目標）、`tclass`（class）與 `{ }` 內的 permission 反推需要補的 `allow` 規則。可用 `audit2allow` 產生候選規則，但仍須人工審視是否合理，避免過度開放權限。
