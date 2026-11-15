init
halt
wait_halt 2000
set pc [lindex [get_reg pc] 1]
echo "pc            = [format 0x%08x $pc]"
echo "SCB_VTOR now  = [format 0x%08x [read_memory 0xE000ED08 32 1]]"
echo "vtor_at_entry = [format 0x%08x [read_memory 0x20000004 32 1]]"
echo "cfgr_at_entry = [format 0x%08x [read_memory 0x20000008 32 1]]"
echo "blink_count   = [read_memory 0x20000000 32 1]"
echo "BKP_DR1       = [format 0x%04x [read_memory 0x40006C04 16 1]]"
echo "GPIOB_IDR PB2 = [expr {([read_memory 0x40010C08 32 1] >> 2) & 1}]"
resume
shutdown
