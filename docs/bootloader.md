
[从零开始写一个简单的bootloader（1）](https://blog.csdn.net/lee_jimmy/article/details/82079342)

UBOOT启动流程中的BL0,BL1,BL2 https://blog.csdn.net/qq_49864684/article/details/118897622

https://github.com/milisarge/awesome-littlekernel?tab=readme-ov-file

什麼是 Little Kernel ？

- [用于嵌入式操作系统的微内核](https://blog.csdn.net/guoqx/article/details/135433035)
    - https://github.com/littlekernel/lk
    - Android 的 LK: https://android.googlesource.com/kernel/lk/
    - 高通的 chipset 用的 LK 是 fork 自 littlekernel/lk，來作為 Android 裝置的 bootloader(Aboot)

- [Booting process of Android devices](https://en.wikipedia.org/wiki/Booting_process_of_Android_devices)
    - As of 2018, 90% of the SoCs of the Android market are supplied by either Qualcomm, Samsung or MediaTek.[1] Other vendors include UNISOC, Rockchip, Marvell, Nvidia and previously Texas Instruments.
    - stage 1: Primary Bootloader (PBL) (Boot ROM)
        - space is limited, usually less than 16 KB
    - stage 2: Secondary Bootloader (SBL) (e.g., Little Kernel
- [Boot ROM](https://en.wikipedia.org/wiki/Boot_ROM)