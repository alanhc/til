"""Cycle through candidate offsets for a 128x64 ST7735 panel; pick the one with a clean border.

Each candidate: wipe the whole controller RAM (132x162), then draw a 128x64 frame at that offset
with a big number, plus R/G/B bars labelled with letters to check the colour order.
Usage: python tft_calibrate.py [seconds_per_candidate]
"""
import os
import sys
import time

try:
    import libusb_package
    os.environ["PATH"] = os.path.dirname(libusb_package.get_library_path()) + os.pathsep + os.environ["PATH"]
except ImportError:
    pass
os.environ["BLINKA_FT232H"] = "1"

import board
import digitalio
from adafruit_rgb_display import st7735
from PIL import Image, ImageDraw, ImageFont

W, H = 128, 64
CANDIDATES = [(2, 70), (2, 71), (2, 72), (2, 73), (0, 71), (0, 72)]
HOLD = float(sys.argv[1]) if len(sys.argv) > 1 else 5.0

spi = board.SPI()
cs = digitalio.DigitalInOut(board.C0)
dc = digitalio.DigitalInOut(board.C1)
rst = digitalio.DigitalInOut(board.C2)


def make(w, h, xo, yo, reset):
    return st7735.ST7735R(
        spi, cs=cs, dc=dc, rst=rst if reset else None,
        width=w, height=h, x_offset=xo, y_offset=yo,
        invert=False, bgr=False, baudrate=24_000_000, rotation=0,
    )


try:
    big = ImageFont.load_default(size=30)
except TypeError:
    big = ImageFont.load_default()
small = ImageFont.load_default()

full = make(132, 162, 0, 0, reset=True)

for i, (xo, yo) in enumerate(CANDIDATES, 1):
    full.fill(0)
    disp = make(W, H, xo, yo, reset=False)
    img = Image.new("RGB", (W, H), "black")
    d = ImageDraw.Draw(img)
    d.rectangle((0, 0, W - 1, H - 1), outline="white")
    for j, (c, name) in enumerate([((255, 0, 0), "R"), ((0, 255, 0), "G"), ((0, 0, 255), "B")]):
        x0 = 70 + j * 18
        d.rectangle((x0, 10, x0 + 14, 40), fill=c)
        d.text((x0 + 7, 50), name, fill="white", font=small, anchor="mm")
    d.text((32, 32), str(i), fill="yellow", font=big, anchor="mm")
    disp.image(img)
    print(f"#{i}: x_offset={xo}, y_offset={yo}", flush=True)
    time.sleep(HOLD)

print("Done.")
