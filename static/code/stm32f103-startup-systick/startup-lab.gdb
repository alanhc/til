# Flash lab.elf, then stop at each startup stage and look at RAM.
set pagination off
set confirm off
file lab.elf
target extended-remote localhost:3333
monitor reset halt
dump binary memory app-backup.bin 0x08002000 0x08004000
load
monitor reset halt

echo \n== A. reset: dapboot runs first, then jumps to us\n
hbreak Reset_Handler
continue
printf "pc=0x%08x sp=0x%08x (from our vector [0])\n", $pc, $sp
printf "speed=%u blink_count=%u   <- RAM leftovers, nothing copied yet\n", speed, blink_count
delete

echo \n== B. after the .data copy loop\n
hbreak startup-lab.c:41
continue
printf "speed=%u   <- copied from flash 0x%08x\n", speed, &_sidata
printf "blink_count=%u   <- not zeroed yet\n", blink_count
delete

echo \n== C. arriving at main: .bss is zero\n
hbreak main
continue
printf "speed=%u blink_count=%u\n", speed, blink_count
delete

echo \n== D. let it blink 3 times\n
hbreak startup-lab.c:23
set $n = 0
while $n < 3
  continue
  printf "blink_count=%u PC13 ODR bit=%d\n", blink_count, (*(unsigned*)0x4001100C >> 13) & 1
  set $n = $n + 1
end
delete

monitor reset run
detach
quit
