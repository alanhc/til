#!/bin/bash
# Wait for serial_console.py to interrupt autoboot, then boot the BBB over TFTP.
# Arm first: touch logs/break.flag, then power-cycle the board.
#
#   KERNEL=zImage DTB=am335x-boneblack.dtb INITRD=initrd.img ./tftpboot.sh
#   KERNEL=zImage-bringup DTB=am335x-boneblack-bringup.dtb INITRD= ./tftpboot.sh
#
# INITRD empty boots without an initramfs (bootz addr - fdt).
D=${BBB_DIR:-$HOME/bbb-bringup}
KERNEL=${KERNEL-zImage}
DTB=${DTB-am335x-boneblack.dtb}
INITRD=${INITRD-initrd.img}
BOOTARGS=${BOOTARGS-console=ttyS0,115200n8 root=/dev/mmcblk0p3 ro rootfstype=ext4 rootwait earlycon net.ifnames=0 bringup.boot=tftp}

until [ ! -e $D/logs/break.flag ]; do sleep 0.3; done
ip route get 192.168.10.242 | grep -q 'dev enp5s0' || echo "WARN: route to BBB not via enp5s0 (Tailscale ip rule missing?)"
$D/ub.sh 'setenv ipaddr 192.168.10.242; setenv serverip 192.168.10.154' >/dev/null
$D/ub.sh "tftp \${loadaddr} $KERNEL" 150 | grep -E 'Bytes|rror|T T'
$D/ub.sh "tftp \${fdtaddr} $DTB" 50 | grep -E 'Bytes|rror|T T'
if [ -n "$INITRD" ]; then
  $D/ub.sh "tftp \${rdaddr} $INITRD" 150 | grep -E 'Bytes|rror|T T'
  $D/ub.sh 'setenv rdsize ${filesize}' >/dev/null
  RD='${rdaddr}:${rdsize}'
else
  RD=-
fi
$D/ub.sh "setenv bootargs $BOOTARGS" >/dev/null
L=$D/logs/current.log; n=$(wc -l < $L)
printf 'bootz ${loadaddr} %s ${fdtaddr}\r' "$RD" > $D/logs/tx.fifo
for i in $(seq 1 240); do tail -n +$((n+1)) $L | grep -qE 'login:|Kernel panic|Bad Linux' && break; sleep 0.5; done
tail -n +$((n+1)) $L | sed 's/\x1b\[[0-9;?]*[a-zA-Z]//g' | grep -E 'bootz|Starting kernel|Linux version|Kernel command line|mounted filesystem|login:|panic' | cut -c1-170
