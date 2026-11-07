import mmap, os, struct, sys
def rd(addr):
    fd = os.open("/dev/mem", os.O_RDONLY | os.O_SYNC)
    base = addr & ~0xfff
    m = mmap.mmap(fd, 0x1000, mmap.MAP_SHARED, mmap.PROT_READ, offset=base)
    v = struct.unpack("<I", m[addr - base:addr - base + 4])[0]
    m.close(); os.close(fd); return v
for name, a in [("CM_PER_GPIO1_CLKCTRL", 0x44E000AC),
                ("conf_gpmc_a5 (USR0)", 0x44E10854), ("conf_gpmc_a6 (USR1)", 0x44E10858),
                ("conf_gpmc_a7 (USR2)", 0x44E1085C), ("conf_gpmc_a8 (USR3)", 0x44E10860),
                ("GPIO1_OE", 0x4804C134), ("GPIO1_DATAOUT", 0x4804C13C), ("GPIO1_DATAIN", 0x4804C138)]:
    v = rd(a); extra = ""
    if "GPIO1_" in name: extra = "  bits21-24=%s" % format((v >> 21) & 0xf, "04b")[::-1]
    print("%-22s 0x%08x = 0x%08x%s" % (name, a, v, extra))
