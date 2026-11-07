#!/bin/bash
# After tftpboot.sh brings up the 7.3 kernel: copy u-root kexec and the kernel
# into RAM (/dev/shm) on the BBB, run kexec load + exec, and show what the
# serial console printed. Everything stays off the SD card, because heavy SD
# I/O has hung sdhci-omap on this kernel.
D=${BBB_DIR:-$HOME/bbb-bringup}
L=$D/logs/current.log
: "${BBB_PASS:?set BBB_PASS to the BBB debian password (export it)}"
SUDO='echo "$BBB_PASS" | sudo -S -p ""'
for i in $(seq 1 90); do T=5 $D/bbbssh.sh "echo ssh-ok" 2>/dev/null | grep -q ssh-ok && break; sleep 2; done

A=$(mktemp); trap 'rm -f $A' EXIT
printf '#!/bin/sh\necho "$BBB_PASS"\n' > $A; chmod 700 $A
SSH_ASKPASS=$A SSH_ASKPASS_REQUIRE=force DISPLAY=:0 timeout 90 \
  scp -o PubkeyAuthentication=no -o LogLevel=ERROR \
  $D/kexec-arm $D/tftp/${KEXEC_KERNEL:-zImage-bringup} debian@192.168.10.242:/dev/shm/ < /dev/null >/dev/null 2>&1

CMD=${KEXEC_CMDLINE:-'console=ttyS0,115200n8 root=/dev/mmcblk0p3 ro rootfstype=ext4 rootwait earlycon net.ifnames=0 bringup.boot=kexec-1'}
T=60 $D/bbbssh.sh "cd /dev/shm; uname -r; $SUDO env TMPDIR=/dev/shm ./kexec-arm -d -L -l ${KEXEC_KERNEL:-zImage-bringup} -c '$CMD' > kexec-load.log 2>&1; echo load_exit=\$?; echo kexec_loaded=\$(cat /sys/kernel/kexec_loaded); grep -E 'Mem map|System RAM|Reserved|decompresses|Added|Entry' kexec-load.log"

n=$(wc -l < $L)
T=10 $D/bbbssh.sh "sync; $SUDO sh -c 'nohup /dev/shm/kexec-arm -e > /dev/shm/kexec-exec.log 2>&1 &'" >/dev/null 2>&1
for i in $(seq 1 240); do tail -n +$((n+1)) $L | grep -qE 'login:|Kernel panic|Unable to handle' && break; sleep 0.5; done
echo "=== serial since kexec -e ==="
tail -n +$((n+1)) $L | sed 's/\x1b\[[0-9;?]*[a-zA-Z]//g' | grep -aE 'kexec|Bye|Starting new|^\\[[0-9:]*\\] (C:|DTB|Uncompress)|Error|Booting Linux|Linux version|Kernel command line|Machine model|Memory:|mounted filesystem|eth0: Link|mmc0: Timeout|panic|Oops|login:' | cut -c1-170
