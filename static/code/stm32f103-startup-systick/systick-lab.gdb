# Lesson 2: watch SysTick interrupts arrive.
set pagination off
set confirm off
file tick.elf
target extended-remote localhost:3333
monitor reset halt
load
monitor reset halt

echo \n== A. main is about to turn SysTick on\n
hbreak main
continue
delete
printf "VTOR=0x%08x (set by Reset_Handler)\n", *(unsigned*)0xE000ED08
printf "vector[15] at VTOR+0x3C = 0x%08x, SysTick_Handler = 0x%08x\n", *(unsigned*)(*(unsigned*)0xE000ED08 + 0x3C), &SysTick_Handler

echo \n== B. stop at the very first instruction of SysTick_Handler\n
hbreak *SysTick_Handler
continue
printf "IPSR=%d (15 = SysTick)  lr=0x%08x  sp=0x%08x\n", $xpsr & 0x1FF, $lr, $sp
echo hardware pushed 8 words onto the stack:\n
printf "  r0=0x%08x r1=0x%08x r2=0x%08x r3=0x%08x\n", *(unsigned*)($sp), *(unsigned*)($sp+4), *(unsigned*)($sp+8), *(unsigned*)($sp+12)
printf "  r12=0x%08x lr=0x%08x pc=0x%08x xpsr=0x%08x\n", *(unsigned*)($sp+16), *(unsigned*)($sp+20), *(unsigned*)($sp+24), *(unsigned*)($sp+28)
info symbol *(unsigned*)($sp+24)
printf "ms=%u\n", ms

echo \n== C. three more ticks\n
set $n = 0
while $n < 3
  continue
  printf "ms=%u  SysTick CVR=%u\n", ms, *(unsigned*)0xE000E018
  set $n = $n + 1
end
delete

echo \n== D. run 2 seconds, then count\n
set $before = ms
monitor resume
monitor sleep 2000
monitor halt
printf "ms went from %u to %u: %u ticks in ~2000 ms\n", $before, ms, ms - $before

monitor resume
detach
quit
