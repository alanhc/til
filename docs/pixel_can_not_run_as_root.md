## 背景
adb root

adbd cannot run as root in production builds

## 步驟
adb reboot bootloader

https://developers.google.com/android/images
找16.0.0 (BP4A.260205.001, Feb 2026) Link > 這版本要和bootloader
https://github.com/topjohnwu/Magisk/releases
adb install Magisk\ v30.7.apk 
Performing Streamed Install
Success


adb pull /sdcard/Download/magisk_patched-30700_uGZAZ.img ./
fastboot flash init_boot magisk_patched-30700_uGZAZ.img
fastboot reboot
Rebooting                                          OKAY [  0.000s]
Finished. Total time: 0.000s


```
shiba:/ # cd sys/class/                                                                                                   
amcs/                   dqe1/                   konepure/               ppp/                    st54spi/
android_usb/            drm/                    kovaplus/               pps/                    thermal/
aoc/                    ect/                    leds/                   ptp/                    touch_offload/
aoc_chan/               edgetpu/                lirc/                   pwm/                    trusty_ipc/
aoc_char/               extcon/                 lwis/                   pyra/                   tty/
arvo/                   firmware/               mdio_bus/               rc/                     typec/
backlight/              fth/                    mem/                    regulator/              typec_mux/
battery_history/        gnss/                   misc/                   remoteproc/             ublk-char/
bbd/                    goodix_fp/              mmc_host/               retimer/                udc/
bcm/                    goog_touch_interface/   nd/                     rfkill/                 uio/
bdi/                    gsa/                    net/                    rpmsg/                  usb_power_delivery/
block/                  gsa_gsc/                nfc/                    rtc/                    usb_role/
bluetooth/              gxp/                    nvme-generic/           ryos/                   video4linux/
bsg/                    hidraw/                 nvme-subsystem/         savu/                   video_codec/
cpif/                   i2c-dev/                nvme/                   scsi_device/            wakeup/
devcoredump/            ieee80211/              pci_bus/                scsi_disk/              watchdog/
devfreq-event/          ieee802154/             pci_epc/                scsi_generic/           wwan/
devfreq/                input/                  phy/                    scsi_host/              xt_idletimer/
devlink/                iommu/                  pmic/                   sound/                  zram-control/
dma/                    isku/                   pmsg/                   spi_master/
dma_heap/               kone/                   power_supply/           spidev/
dqe0/                   koneplus/               powercap/               sscoredump/
shiba:/ # cd sys/class/                                                                
```