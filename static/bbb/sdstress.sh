#!/bin/sh
# SD I/O stress for the sdhci-omap timeout. Run as root; logs to /dev/shm so
# results survive a hung card. Usage: N=20 MB=64 sh sdstress.sh
D=/home/debian/sdtest
N=${N:-20}; MB=${MB:-64}
mkdir -p $D
now() { awk '{print $1}' /proc/uptime; }
to() { dmesg | grep -c 'mmc0: Timeout'; }
echo "start kernel=$(uname -r) N=$N MB=$MB timeouts=$(to)"
for i in $(seq 1 $N); do
	t0=$(now)
	# pattern 1: what kexec load did (copy a ~5.7 MB kernel image onto the card)
	for j in 1 2 3 4 5; do cp /dev/shm/zImage-cpswfix $D/k$j || echo "cp fail $i/$j"; done
	sync
	# pattern 2: large sequential write + read back from the card
	dd if=/dev/zero of=$D/big bs=1M count=$MB conv=fsync 2>/dev/null || echo "write fail $i"
	echo 3 > /proc/sys/vm/drop_caches
	dd if=$D/big of=/dev/null bs=1M 2>/dev/null || echo "read fail $i"
	rm -f $D/big $D/k*; sync
	echo "iter $i done in $(awk -v a=$t0 -v b=$(now) 'BEGIN{printf "%.1f", b-a}')s timeouts=$(to)"
done
echo "end timeouts=$(to)"
