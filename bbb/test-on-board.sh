#!/bin/sh
# Runs on the BBB as root: load the driver, toggle USR3, unload it.
set -x
uname -r
ls /sys/firmware/devicetree/base/ | grep -E 'usr-led|leds'
insmod /dev/shm/usr_led.ko
dmesg | tail -3
ls /sys/bus/platform/drivers/usr-led/
P=/sys/bus/platform/devices/usr-led
cat $P/on; sleep 4
echo 0 > $P/on; cat $P/on; sleep 4
echo 1 > $P/on; cat $P/on; sleep 4
echo maybe > $P/on; cat $P/on
cat /sys/kernel/debug/gpio 2>/dev/null | grep -iE 'usr|led|gpio-5[0-9]' | head
rmmod usr_led
dmesg | tail -2
