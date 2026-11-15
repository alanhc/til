#!/bin/sh
# Build the test app (linked at 0x08002000) and a 10x-slower v2 for the DFU test.
arm-none-eabi-gcc -mcpu=cortex-m3 -mthumb -O0 -g3 -ffreestanding -nostdlib -Wall \
    -T app.ld -o app.elf app.c
sed 's/delay(200000);/delay(2000000);   \/* v2: 10x slower *\//' app.c > app_v2.c
arm-none-eabi-gcc -mcpu=cortex-m3 -mthumb -O0 -g3 -ffreestanding -nostdlib -Wall \
    -T app.ld -o app_v2.elf app_v2.c
arm-none-eabi-objcopy -O binary app_v2.elf app_v2.bin
