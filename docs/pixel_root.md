Magisk: 是運作在 User-space，它現在主要是透過修改（Patch）**`init_boot.img`** 裡的 Ramdisk 來取得權限。
KernelSU: 是直接運作在 Kernel-space，所以它是去修改（或替換）包含核心本身的 **`boot.img`**，這對想要練習 Kernel 編譯的你來說，契合度極高。

使用 Magisk 或 KernelSU 這要怎麼做

https://ivonblog.com/posts/kernelsu-android-root/
