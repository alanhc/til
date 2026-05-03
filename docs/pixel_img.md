我們 build 出來的 (m 編譯)
Image	來源
boot.img	kernel + ramdisk，AOSP build
init_boot.img	generic ramdisk，AOSP build
dtbo.img	device tree overlay，AOSP build
pvmfw.img	protected VM firmware，AOSP build
vbmeta.img	AVB metadata，AOSP build
vbmeta_system.img	AVB metadata for system，AOSP build
vbmeta_vendor.img	AVB metadata for vendor，AOSP build
vendor_boot.img	vendor ramdisk，AOSP build
vendor_kernel_boot.img	vendor kernel modules，AOSP build
super (super partition 裡的)	system / system_ext / product / vendor / vendor_dlkm / system_dlkm，AOSP build
system_other.img	AOSP build
Google 提供的 (vendor blob extract)
Image	來源
vendor.img	vendor blob (extract-google_devices-shiba.sh)
vendor_dlkm.img	vendor kernel modules blob
Google 原廠 (未從我們 build 取得)
Image	來源
bootloader.img	原廠 bootloader，不是 m build 出來的
radio.img (baseband)	原廠 radio firmware，不是 m build 出來的
重點：bootloader.img 和 radio.img 是從 vendor tarball 解壓縮出來的原廠 binary，AOSP m 不會 build 這兩個。其他大部分 image 都是我們自己 build 的，vendor.img 則是 Google 提供的閉源 blob。