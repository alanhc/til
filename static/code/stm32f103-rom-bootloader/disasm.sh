#!/bin/sh
# Disassemble the dumped ROM at its real address.
arm-none-eabi-objdump -D -b binary -marm -Mforce-thumb \
  --adjust-vma=0x1FFFF000 sysmem.bin > sysmem.dis
