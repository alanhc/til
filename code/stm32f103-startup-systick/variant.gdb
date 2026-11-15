# Usage: arm-none-eabi-gdb -batch -ex "file tick-badvtor.elf" -x variant.gdb
# Flash, let it run 1 s from a real reset (dapboot -> app), then see where the CPU is.
set pagination off
set confirm off
target extended-remote localhost:3333
monitor reset halt
load
monitor reset run
monitor sleep 1000
monitor halt
maintenance flush register-cache
printf "VTOR=0x%08x  vector[15] there=0x%08x  IPSR=%d\n", *(unsigned*)0xE000ED08, *(unsigned*)(*(unsigned*)0xE000ED08 + 0x3C), $xpsr & 0x1FF
printf "pc=0x%08x  ms=%u\n", $pc, ms
info symbol $pc
monitor resume
detach
quit
