
```
$ fastboot flashall -w
--------------------------------------------
Bootloader Version...: ripcurrent-16.4-14097582
Baseband Version.....: g5300i-250909-251024-B-14326967
Serial Number........: 38011FDJH00C9F
--------------------------------------------
Checking 'product'                                 OKAY [  0.000s]
Setting current slot to 'a'                        OKAY [  0.108s]
[liblp] Partition system_a will resize from 0 bytes to 848281600 bytes
[liblp] Partition system_dlkm_a will resize from 0 bytes to 11145216 bytes
[liblp] Partition system_ext_a will resize from 0 bytes to 254935040 bytes
[liblp] Partition product_a will resize from 0 bytes to 369336320 bytes
[liblp] Partition vendor_a will resize from 0 bytes to 775467008 bytes
[liblp] Partition vendor_dlkm_a will resize from 0 bytes to 27426816 bytes
[liblp] Partition system_b will resize from 0 bytes to 18411520 bytes
Sending 'boot_a' (65536 KB)                        OKAY [  1.560s]
Writing 'boot_a'                                   OKAY [  0.133s]
Sending 'init_boot_a' (8192 KB)                    OKAY [  0.201s]
Writing 'init_boot_a'                              OKAY [  0.017s]
Sending 'dtbo_a' (16384 KB)                        OKAY [  0.389s]
Writing 'dtbo_a'                                   OKAY [  0.026s]
Sending 'vendor_kernel_boot_a' (65536 KB)          OKAY [  1.554s]
Writing 'vendor_kernel_boot_a'                     OKAY [  0.137s]
Sending 'pvmfw_a' (1024 KB)                        OKAY [  0.026s]
Writing 'pvmfw_a'                                  OKAY [  0.009s]
Sending 'vendor_boot_a' (65536 KB)                 OKAY [  1.556s]
Writing 'vendor_boot_a'                            OKAY [  0.140s]
Sending 'vbmeta_a' (8 KB)                          OKAY [  0.001s]
Writing 'vbmeta_a'                                 OKAY [  0.005s]
Sending 'vbmeta_system_a' (4 KB)                   OKAY [  0.001s]
Writing 'vbmeta_system_a'                          OKAY [  0.005s]
Sending 'vbmeta_vendor_a' (4 KB)                   OKAY [  0.001s]
Writing 'vbmeta_vendor_a'                          OKAY [  0.005s]
Erasing 'userdata'                                 OKAY [  0.732s]
Erase successful, but not automatically formatting.
File system type raw not supported.
Erasing 'metadata'                                 OKAY [  0.020s]
Erase successful, but not automatically formatting.
File system type raw not supported.
Sending sparse 'super' 1/9 (254972 KB)             OKAY [  6.220s]
Writing 'super'                                    OKAY [  0.390s]
Sending sparse 'super' 2/9 (254972 KB)             OKAY [  6.181s]
Writing 'super'                                    OKAY [  0.398s]
Sending sparse 'super' 3/9 (254972 KB)             OKAY [  6.195s]
Writing 'super'                                    OKAY [  0.390s]
Sending sparse 'super' 4/9 (254972 KB)             OKAY [  6.132s]
Writing 'super'                                    OKAY [  0.415s]
Sending sparse 'super' 5/9 (254972 KB)             OKAY [  6.239s]
Writing 'super'                                    OKAY [  0.387s]
Sending sparse 'super' 6/9 (254972 KB)             OKAY [  6.186s]
Writing 'super'                                    OKAY [  0.388s]
Sending sparse 'super' 7/9 (254972 KB)             OKAY [  6.222s]
Writing 'super'                                    OKAY [  0.373s]
Sending sparse 'super' 8/9 (254972 KB)             OKAY [  6.165s]
Writing 'super'                                    OKAY [  0.377s]
Sending sparse 'super' 9/9 (211236 KB)             OKAY [  5.152s]
Writing 'super'                                    OKAY [  0.332s]
Erasing 'userdata'                                 OKAY [  0.697s]
Erase successful, but not automatically formatting.
File system type raw not supported.
wipe task partition not found: cache
Erasing 'metadata'                                 OKAY [  0.013s]
Erase successful, but not automatically formatting.
File system type raw not supported.
Rebooting                                          OKAY [  0.000s]
Finished. Total time: 65.572s
```