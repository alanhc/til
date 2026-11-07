import os, ctypes, time
fd = os.open("/dev/ptp0", os.O_RDONLY)
clk = ((~fd) << 3) | 3
lib = ctypes.CDLL("libc.so.6", use_errno=True)
class ts(ctypes.Structure): _fields_ = [("s", ctypes.c_long), ("ns", ctypes.c_long)]
for i in range(3):
    t = ts(); r = lib.clock_gettime(ctypes.c_int(clk), ctypes.byref(t))
    print("ptp0", r, t.s, t.ns); time.sleep(0.5)
