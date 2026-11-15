init
halt
wait_halt 2000
mww 0x4002101C [expr {[read_memory 0x4002101C 32 1] | (1<<27) | (1<<28)}]
mww 0x40007000 [expr {[read_memory 0x40007000 32 1] | (1<<8)}]
mwh 0x40006C04 0x4F42
reset run
for {set i 0} {$i < 20} {incr i} {
  sleep 300
  set fnr [read_memory 0x40005C48 32 1]
  echo "t=[expr {($i+1)*300}]ms CNTR=[format 0x%04x [read_memory 0x40005C40 32 1]] FN=[expr {$fnr & 0x7ff}] LCK=[expr {($fnr>>13)&1}] DADDR=[format 0x%02x [read_memory 0x40005C4C 32 1]] APB1ENR.USB=[expr {([read_memory 0x4002101C 32 1]>>23)&1}]"
}
shutdown
