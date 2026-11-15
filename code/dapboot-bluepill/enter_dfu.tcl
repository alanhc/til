init
halt
wait_halt 2000
# enable PWR+BKP clocks, unlock backup domain, write the magic dapboot looks for
mww 0x4002101C [expr {[read_memory 0x4002101C 32 1] | (1<<27) | (1<<28)}]
mww 0x40007000 [expr {[read_memory 0x40007000 32 1] | (1<<8)}]
mwh 0x40006C04 0x4F42
echo "BKP_DR1 before reset = [format 0x%04x [read_memory 0x40006C04 16 1]]"
reset run
sleep 1500
halt
wait_halt 2000
echo "pc after reset       = [format 0x%08x [lindex [get_reg pc] 1]]"
echo "BKP_DR1 after boot   = [format 0x%04x [read_memory 0x40006C04 16 1]]"
resume
shutdown
