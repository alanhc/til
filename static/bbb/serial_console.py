#!/usr/bin/python3
"""Log the BBB J1 debug UART and let other processes type into it.

  serial_console.py [port] [logfile]

- Every received line is written to the log with a host timestamp. A partial
  line (e.g. the U-Boot "=> " prompt) is flushed after 0.3 s of silence.
- Anything written to logs/tx.fifo is sent to the board:
      printf 'bdinfo\\r' > logs/tx.fifo
- While logs/break.flag exists, a space is sent every 20 ms between the
  "U-Boot 20xx" banner and "Starting kernel", so autoboot is interrupted
  even with bootdelay=0 while Linux never sees the flood. The flag is
  removed once the "=> " prompt shows up, so it can be armed at any time.
- Reopens the port if the USB-TTL adapter disconnects (e.g. power cycle).
"""
import os, select, sys, time, serial

port = sys.argv[1] if len(sys.argv) > 1 else "/dev/ttyUSB0"
out = sys.argv[2] if len(sys.argv) > 2 else "logs/current.log"
logdir = os.path.dirname(os.path.abspath(out))
fifo = os.path.join(logdir, "tx.fifo")
flag = os.path.join(logdir, "break.flag")

if not os.path.exists(fifo):
    os.mkfifo(fifo)
# O_RDWR keeps the FIFO open even when no writer is attached, so we never see EOF.
fifo_fd = os.open(fifo, os.O_RDWR | os.O_NONBLOCK)

UBOOT_MARKERS = (b"U-Boot 20", b"U-Boot SPL", b"Board: ", b"DRAM:  ")

def stamp():
    return time.strftime("%H:%M:%S")

with open(out, "a", buffering=1, errors="replace") as f:
    def emit(raw):
        f.write("[%s] %s\n" % (stamp(), raw.rstrip(b"\r").decode(errors="replace")))

    while True:
        try:
            ser = serial.Serial(port, 115200, timeout=0)
        except serial.SerialException:
            time.sleep(0.2)
            continue
        f.write("[%s] ### port opened\n" % stamp())
        buf, last_rx, tail = b"", time.time(), b""
        in_uboot = False
        # The USB hub may take seconds to re-enumerate after power-on, so the
        # port can come back after the U-Boot banner. Spam blindly for a short
        # window right after (re)open so we still beat bootdelay=0.
        blind_until = time.time() + 4 if os.path.exists(flag) else 0
        try:
            while True:
                r, _, _ = select.select([ser.fileno(), fifo_fd], [], [], 0.02)
                if fifo_fd in r:
                    ser.write(os.read(fifo_fd, 4096))
                if ser.fileno() in r:
                    data = ser.read(4096)
                    if not data:
                        raise serial.SerialException("disconnected")
                    buf += data
                    # Look for stage markers in the whole new chunk (plus the
                    # previous tail, for markers split across reads); a chunk
                    # can be far longer than the tail we keep.
                    window = tail + data
                    u = max(window.rfind(m) for m in UBOOT_MARKERS)
                    k = window.rfind(b"Starting kernel")
                    if u > k:
                        in_uboot = True
                    elif k > u:
                        in_uboot = False
                    tail = window[-64:]
                    last_rx = time.time()
                    while b"\n" in buf:
                        line, buf = buf.split(b"\n", 1)
                        emit(line)
                # Flush a partial line on silence, or when the board echoes a
                # long run of our break spaces without ever sending a newline.
                if buf and (time.time() - last_rx > 0.3 or len(buf) > 256):
                    emit(buf)
                    buf = b""
                if os.path.exists(flag) and (in_uboot or time.time() < blind_until):
                    if b"=> " in tail:
                        os.remove(flag)
                        in_uboot = False
                        f.write("[%s] ### autoboot interrupted\n" % stamp())
                    else:
                        ser.write(b" ")
        except (serial.SerialException, OSError):
            if buf:
                emit(buf)
            f.write("[%s] ### port lost\n" % stamp())
            ser.close()
