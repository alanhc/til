"""Paint a labelled ruler over the whole ST7735 RAM (132x162) to find the visible window.

Horizontal lines every 16 rows (labelled with their row number), vertical lines every 16 columns.
Whatever row/column labels you can see at the panel's edges give the y/x offsets directly.
"""
import os

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

W, H = 132, 162
disp = st7735.ST7735R(
    board.SPI(),
    cs=digitalio.DigitalInOut(board.C0),
    dc=digitalio.DigitalInOut(board.C1),
    rst=digitalio.DigitalInOut(board.C2),
    width=W, height=H, x_offset=0, y_offset=0,
    invert=True, bgr=True, baudrate=24_000_000, rotation=0,
)

img = Image.new("RGB", (W, H), "black")
d = ImageDraw.Draw(img)
font = ImageFont.load_default()

for x in range(0, W, 16):
    d.line((x, 0, x, H - 1), fill=(0, 90, 255))
    d.text((x + 2, 0), str(x), fill=(0, 200, 255), font=font)  # column labels along row 0
for y in range(0, H, 16):
    d.line((0, y, W - 1, y), fill=(255, 0, 0) if (y // 16) % 2 else (0, 255, 0))
    for x in (2, 46, 90):
        d.text((x, y + 3), f"y{y}", fill="yellow", font=font)

disp.image(img)
print("Ruler drawn over full 132x162 RAM.")
