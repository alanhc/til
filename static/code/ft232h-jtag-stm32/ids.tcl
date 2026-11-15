init
sleep 200
halt
echo "DBGMCU_IDCODE: [read_memory 0xE0042000 32 1]"
echo "CPUID:         [read_memory 0xE000ED00 32 1]"
echo "FLASH_SIZE_KB: [read_memory 0x1FFFF7E0 16 1]"
resume
shutdown
