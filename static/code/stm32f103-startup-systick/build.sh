#!/bin/sh
# Build both labs. Needs arm-none-eabi-gcc (Arm GNU Toolchain) on PATH.
set -e
CFLAGS="-mcpu=cortex-m3 -mthumb -O0 -g -ffreestanding -nostdlib -Wall -T link.ld"

# Lesson 1: startup only
arm-none-eabi-gcc $CFLAGS -Wl,-Map=lab.map -o lab.elf startup-lab.c

# Lesson 2: SysTick, plus two broken VTOR variants for the experiment
arm-none-eabi-gcc $CFLAGS -o tick.elf                           systick-lab.c
arm-none-eabi-gcc $CFLAGS -DNO_VTOR -o tick-novtor.elf          systick-lab.c
arm-none-eabi-gcc $CFLAGS -DVTOR_VALUE=0x08000000 -o tick-badvtor.elf systick-lab.c

arm-none-eabi-size lab.elf tick.elf
