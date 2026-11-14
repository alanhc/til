"""Find the bottom edge: frame starts at row 70, height shrinks 64 -> 56; pick the first with a visible bottom line.
Usage: python tft_bottom.py [seconds_per_candidate]
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

HOLD = float(sys.argv[1]) if len(sys.argv) > 1 else 6.0
HEIGHTS = [64, 63, 62, 61, 60, 59, 58, 57, 56]

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
    big = ImageFont.load_default(size=28)
except TypeError:
    big = ImageFont.load_default()

full = make(132, 162, 0, 0, reset=True)
for i, h in enumerate(HEIGHTS, 1):
    full.fill(0)
    disp = make(128, h, 2, 70, reset=False)
    img = Image.new("RGB", (128, h), "black")
    d = ImageDraw.Draw(img)
    d.rectangle((0, 0, 127, h - 1), outline="white")
    d.text((64, 28), str(i), fill="yellow", font=big, anchor="mm")
    disp.image(img)
    print(f"#{i}: height={h} (bottom line at row {70 + h - 1})", flush=True)
    time.sleep(HOLD)
print("Done.")
