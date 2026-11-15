init
reset halt
wait_halt 2000
# 1. backup the whole 64 KB first
dump_image backup-before-dapboot.bin 0x08000000 0x10000
# 2. bootloader at 0x08000000, app at 0x08002000 (ELF carries the addresses)
flash write_image erase dapboot.elf
flash write_image erase app.elf
verify_image dapboot.elf
verify_image app.elf
echo "vec@0x08000000: [format {0x%08x 0x%08x} {*}[read_memory 0x08000000 32 2]]"
echo "vec@0x08002000: [format {0x%08x 0x%08x} {*}[read_memory 0x08002000 32 2]]"
reset run
shutdown
