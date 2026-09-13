---
title: UEFI gdb 除錯
sidebar_position: 3
---

# 在 UEFI 階段用 gdb 除錯：從 QEMU 到 DXE dispatch 單步

## 為什麼寫這篇

中文圈關於 UEFI 的文章，絕大多數停在「SEC → PEI → DXE → BDS 四個階段」的架構圖。
架構圖誰都看得懂，但那不等於你能在韌體裡下一個中斷點。

這篇要處理的是實際動手時會撞到的那些東西：toolchain tag 已經改名、新版 GCC 會擋住 build、
symbol 掛上去了但全域變數讀出來是錯的。這些沒有一個寫在官方文件裡，而每一個都會讓你卡上一小時。

文中所有位址、log、backtrace 都是實際跑出來的，不是示意。環境：

- Ubuntu 24.04.4 / gcc 13.3.0 / gdb 15.1
- edk2 `2970e5699b`(2026-08-12)
- QEMU q35,OVMF X64 DEBUG build

---

## 一、先把 OVMF build 出來

```bash
git clone --recurse-submodules https://github.com/tianocore/edk2
cd edk2
make -C BaseTools -j16
source edksetup.sh
```

### 坑 1：`GCC5` 這個 toolchain tag 已經不存在

網路上九成的教學會叫你打 `-t GCC5`。新版 edk2 會直接回你：

```
build: : warning: Tool chain [GCC5] is not defined
 : error 4000: Not available
	[GCC5] not defined. No toolchain available for build!
```

查一下現在有哪些：

```bash
grep -oE 'DEFINE (GCC|CLANG)[A-Z0-9]*_' Conf/tools_def.txt | sort -u
# DEFINE CLANGDWARF_
# DEFINE CLANGPDB_
# DEFINE GCC_
# DEFINE GCCNOLTO_
```

### 為什麼要選 `GCCNOLTO` 而不是 `GCC`

因為你要單步除錯。LTO 會跨模組 inline、把函式邊界打散，gdb 的 source-level stepping
會跳來跳去對不上原始碼。關掉 LTO 的代價只是 image 稍大 —— 對 QEMU 上的實驗完全不是問題。

**說明一下這條的證據等級**：我從一開始就選 `GCCNOLTO`，沒有先用 `GCC` build 一次來對照，
所以「LTO 會讓 stepping 難對應」是基於 LTO 的一般行為所做的預防性選擇，
不是我在 edk2 上實測出來的差異。想確認的話 build 兩份自己比。

### 坑 2:GCC 13 的 `-Werror` 會擋住 build

Ubuntu 24.04 的 gcc 13.3 對 `UefiCpuPkg/Library/MpInitLib/X64/AmdSev.c:326` 會報：

```
error: 'GhcbApicIds' may be used uninitialized [-Werror=maybe-uninitialized]
```

edk2 的 `GCC_ALL_CC_COMMON` 帶著 `-Werror`，所以這個警告直接讓 build 中斷。

直覺會想去改 `Conf/tools_def.txt` 裡的 `DEFINE GCC_ALL_CC_FLAGS`，加上
`-Wno-error=maybe-uninitialized`。**這個做法在我的環境下無效。**
我試過清掉整個 `Build/` 目錄、加 `-N` 停用 build cache，那個 flag 就是不會出現在
生成的 `GNUmakefile` 裡。我沒有把 edk2 的 flag 傳遞機制追到底，所以這裡只陳述觀察到的現象。

**有效的做法是改 DSC 的 `[BuildOptions]`。** 在 `OvmfPkg/OvmfPkgX64.dsc` 加一行：

```
[BuildOptions]
  GCC:*_*_*_CC_FLAGS                   = -Wno-error=maybe-uninitialized
```

要確認機制有沒有生效，可以拿同區段本來就有的 `-mno-mmx` 當對照 —— 它出現在生成的
makefile 裡，就代表這條路是通的。

### 驗證 flag 真的進去了（順便講一個 shell 陷阱)

```bash
M=Build/OvmfX64/DEBUG_GCCNOLTO/X64/UefiCpuPkg/Library/MpInitLib/DxeMpInitLib/GNUmakefile
if grep -q 'Wno-error=maybe-uninitialized' "$M"; then echo "有進去"; else echo "沒進去"; fi
```

**不要寫成這樣：**

```bash
grep -oE 'Wno-error=maybe-uninitialized' "$M" | head -1 || echo "沒進去"
```

`||` 掛在 `head` 上，而 `head` 對空輸入也回傳 0，所以「沒進去」永遠不會印出來。
我就是被這行騙了兩輪，以為 flag 有生效。

### Build

```bash
build -a X64 -t GCCNOLTO -p OvmfPkg/OvmfPkgX64.dsc -b DEBUG -n 16 -D DEBUG_ON_SERIAL_PORT
```

53 秒完成。FV 使用率：

```
SECFV          [39%]    84,880 /   212,992
PEIFV          [61%]   520,168 /   851,968
DXEFV          [50%] 7,627,240 / 15,204,352
FVMAIN_COMPACT [45%] 1,572,304 /  3,440,640
```

### 附帶一提：`DEBUG_ON_SERIAL_PORT` 與 `-debugcon` 是兩個不同的出口

build 時給了 `-D DEBUG_ON_SERIAL_PORT`，`DEBUG()` 的輸出就走**序列埠**。
這時如果你照著別的教學加 `-debugcon file:debug.log -global isa-debugcon.iobase=0x402`，
會得到一個 **0 行的空檔案**，看起來像韌體完全沒有 debug 輸出。兩者擇一。

---

## 二、讓 driver 停下來等你

UEFI 模組是 runtime 才被載入的。你沒辦法「開機前先下好中斷點」，因為那時候位址還不存在。

有三種解法，我建議**先學最土的那種**，因為它一定會動：

在 driver 的 entry point 放一個可控的等待迴圈。

```c
/* 要除錯時改成 TRUE 重 build */
volatile BOOLEAN  gMyDxeWaitForGdb = FALSE;

EFI_STATUS
EFIAPI
MyDxeDriverEntry (
  IN EFI_HANDLE        ImageHandle,
  IN EFI_SYSTEM_TABLE  *SystemTable
  )
{
  DEBUG ((DEBUG_INFO, "MyDxeDriver: entry, ImageHandle=%p\n", ImageHandle));

  while (gMyDxeWaitForGdb) {
    CpuPause ();
  }
  ...
}
```

`volatile` 不能省 —— 否則 `-Os` 會把整個迴圈最佳化掉。

開機時用 `-s`(在 :1234 開 gdbserver),**不要加 `-S`**。讓它自己跑到迴圈卡住，
你就不必去猜什麼時候 attach 才對：

```bash
qemu-system-x86_64 -machine q35 -m 2G \
  -drive if=pflash,format=raw,readonly=on,file=$FV/OVMF_CODE.fd \
  -drive if=pflash,format=raw,file=/tmp/vars.fd \
  -drive file=fat:rw:/tmp/esp,format=raw,media=disk \
  -display none -serial file:/tmp/ovmf-gdb.log -s
```

> `fat:rw:/tmp/esp` 讓 QEMU 把一個本機目錄當成 FAT 磁碟。你在 host 丟 `.efi` 進去，
> guest 立刻看得到，不用每次做 image。做韌體實驗時這一招省下的時間比什麼都多。

確認它真的卡住了 —— 有 `entry` 但沒有後續：

```bash
grep -n 'MyDxeDriver' /tmp/ovmf-gdb.log
# 677:Loading driver at 0x0007E757000 EntryPoint=0x0007E759CF2 MyDxeDriver.efi
# 681:MyDxeDriver: entry, ImageHandle=7E7AB198
```

---

## 三、算出 symbol 位址：image base 不是 `.text`

serial log 那行給你的是 **image base**：

```
Loading driver at 0x0007E757000 EntryPoint=0x0007E759CF2 MyDxeDriver.efi
                  ^^^^^^^^^^^^^ image base
```

很多教學會告訴你「`.text` 大概在 base + 0x240」。**不要背這個數字。**
它取決於 PE/COFF header 大小、linker script、build 設定，每個模組都可能不同。
自己查：

```bash
objdump -h Build/.../MyDxeDriver.debug | awk 'NR>4 && $2 ~ /^\./ {printf "%-14s VMA=0x%s\n", $2, $4}'
```

我這個 build 的結果：

```
.text          VMA=0x0000000000001000
.data          VMA=0x0000000000004000
```

所以：

```
image base            0x7E757000
.text = base + 0x1000 0x7E758000
.data = base + 0x4000 0x7E75B000
```

---

## 四、【核心】`add-symbol-file` 只重定位 `.text`

這是整篇最重要的一段，也是我覺得中文圈最缺的一段。

照著大多數教學做：

```
(gdb) add-symbol-file MyDxeDriver.debug 0x7E758000
(gdb) bt
#0  CpuPause () at MdePkg/Library/BaseLib/X64/GccInline.c:45
#1  MyDxeDriverEntry (...) at MyPkg/MyDxeDriver/MyDxeDriver.c:25
```

backtrace 完美解出來，函式名、檔名、行號都對。看起來一切正常。

然後你想確認旗標值：

```
(gdb) p gMyDxeWaitForGdb
$1 = 0 '\000'
```

**0?** 但程式明明還卡在 `while (gMyDxeWaitForGdb)` 裡面轉。

### 為什麼

`add-symbol-file <file> <addr>` 的第二個參數**只設定 `.text_addr`**。
全域變數住在 `.data`，而 `.data` 沒有被重定位 —— gdb 拿著 ELF 檔裡的原始 VMA
(`0x4000`)去讀，那個位址在執行時期根本不是你的變數。

**`.text` 有搬、`.data` 沒搬，所以函式解得出來、變數讀出垃圾。**
症狀特別會騙人，因為 backtrace 看起來完全正確，你會往別的方向去找問題。

### 正確寫法

每個 section 分別指定：

```bash
gdb -q \
  -ex 'set architecture i386:x86-64' \
  -ex 'target remote :1234' \
  -ex "add-symbol-file MyDxeDriver.debug 0x7E758000 -s .data 0x7E75B000"
```

```
(gdb) p gMyDxeWaitForGdb
$1 = 1 '\001'
```

這才是真的。

---

## 五、載入 DxeCore，看見完整的 dispatch 鏈

只掛自己的 driver,backtrace 到第四層就斷了：

```
#3  _ModuleEntryPoint () at MdePkg/Library/UefiDriverEntryPoint/DriverEntryPoint.c:123
#4  0x000000007fb49337 in ?? ()
#5  0x000000007fb79f30 in ?? ()
```

那些 `?? ()` 是 DxeCore。把它也掛上：

```bash
grep -oE 'Loading DXE CORE at 0x[0-9A-F]+' /tmp/ovmf-gdb.log
# Loading DXE CORE at 0x0007FB45000

objdump -h Build/OvmfX64/DEBUG_GCCNOLTO/X64/DxeCore.debug | grep -E '\.text|\.data'
# .text  VMA=0x00001000
# .data  VMA=0x00034000
```

```bash
  -ex "add-symbol-file DxeCore.debug 0x7FB46000 -s .data 0x7FB79000"
```

再看一次：

```
#0  CpuPause ()                    MdePkg/Library/BaseLib/X64/GccInline.c:45
#1  MyDxeDriverEntry ()            MyPkg/MyDxeDriver/MyDxeDriver.c:25
#2  ProcessModuleEntryPointList () .../AutoGen.c:211
#3  _ModuleEntryPoint ()           MdePkg/Library/UefiDriverEntryPoint/DriverEntryPoint.c:123
#4  CoreStartImage ()              MdeModulePkg/Core/Dxe/Image/Image.c:1707
#5  CoreDispatcher ()              MdeModulePkg/Core/Dxe/Dispatcher/Dispatcher.c:520
#6  DxeMain ()                     MdeModulePkg/Core/Dxe/DxeMain/DxeMain.c:547
#7  _ModuleEntryPoint ()           MdePkg/Library/DxeCoreEntryPoint/DxeCoreEntryPoint.c:46
```

**這張 backtrace 就是整個 DXE 階段的骨架。** 從 `DxeMain` 進來、`CoreDispatcher`
挑出可以載入的 driver、`CoreStartImage` 把它跑起來、最後進到你的 entry point。
架構圖上那個叫「DXE」的方塊，實際上就是這七層。

---

## 六、在 dispatcher 停下來，看 Depex 到底是什麼

DXE 最核心的概念是 **dispatcher 依 Depex 分輪載入 driver**。
`[Depex]` 寫在 `.inf` 裡，決定這個 driver 要等哪些 protocol 就位才能跑：

```
[Depex]
  gEfiCpuArchProtocolGuid
```

要看它實際怎麼運作，在 dispatcher 下中斷點：

```bash
  -ex 'break Dispatcher.c:520' \
  -ex 'set var gMyDxeWaitForGdb=0' \
  -ex 'continue' \
  -ex 'p *DriverEntry'
```

命中：

```
Breakpoint 1, CoreDispatcher () at .../Dispatcher/Dispatcher.c:520
520	        Status = CoreStartImage (DriverEntry->ImageHandle, NULL, NULL);
```

`p *DriverEntry` 印出 `EFI_CORE_DRIVER_ENTRY`,dispatcher 的核心資料結構：

```
Depex = 0x7fa2a118, DepexSize = 72
ScheduledLink = { BackLink = 0x7fb79f30 <mScheduledQueue> }
Dependent = 0, Scheduled = 0, Initialized = 1
```

`Depex` 指向的就是那串 dependency expression 的 bytecode,72 bytes。
`mScheduledQueue` 是「Depex 已滿足、排隊等著被載入」的佇列。

在這裡反覆 `continue`，你會看到 dispatcher 一輪一輪地掃：
把當下 Depex 滿足的 driver 挑出來載入 → 這些 driver 安裝了新的 protocol →
再重掃一遍，看有沒有 driver 因此變成可載入 → 直到某一輪沒有任何新的 driver 為止。

**這就是「我真的懂 DXE」和「我看過投影片」的分水嶺。**

---

## 七、官方 script

edk2 有附一個自動化的 gdb script：

```bash
gdb -ex "target remote :1234" \
    -ex "source BaseTools/Scripts/efi_gdb.py"
(gdb) info efi
```

可以先試，能動就省事。但**手動掛的方法一定要會** —— script 會因 edk2 版本、
模組型態而失效，而且它幫你做掉的正是你該理解的那部分。

---

## 小結：五個會讓你卡住的地方

1. `GCC5` toolchain tag 已移除，用 `GCC` 或 `GCCNOLTO`
2. 除錯用 `GCCNOLTO`,LTO 會讓 source-level stepping 對不上
3. GCC 13 的 `-Werror=maybe-uninitialized` 要靠 DSC `[BuildOptions]` 修
4. **`add-symbol-file` 只搬 `.text`，`.data` 要用 `-s .data <addr>` 另外指定**
5. 載入 DxeCore 的 symbol，才看得見完整的 dispatch 鏈

其中第 4 點是唯一一個「看起來一切正常但其實是錯的」，也是最值得記住的。
