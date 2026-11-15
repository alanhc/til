# Usage (OpenOCD must already be running):
#   arm-none-eabi-gdb -x debug.gdb
file blink.elf
target extended-remote localhost:3333
monitor reset halt
# With BOOT0=1 the reset vector comes from ROM, so start our image by hand:
set $sp = *(unsigned int *)0x08000000
set $pc = *(unsigned int *)0x08000004
break main
continue
