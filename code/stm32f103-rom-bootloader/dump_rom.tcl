# Dump STM32F103 system memory (ROM bootloader) and option bytes over JTAG.
# Usage:
#   openocd -f ft232h-jtag.cfg -f target/stm32f1x.cfg -f dump_rom.tcl
# Output stays on your machine; the ROM image is ST's code, don't publish it.
init
reset halt
dump_image sysmem.bin   0x1FFFF000 0x800
dump_image optbytes.bin 0x1FFFF800 0x10
echo [format "rom\[0\] MSP   = 0x%08x" [read_memory 0x1FFFF000 32 1]]
echo [format "rom\[1\] Reset = 0x%08x" [read_memory 0x1FFFF004 32 1]]
echo [format "F_SIZE       = %d KB"   [read_memory 0x1FFFF7E0 16 1]]
reset run
shutdown
