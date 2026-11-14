"""Fine ruler: pin down the exact top row and left column of the visible window.

- Rows 40..76: a coloured line every 4 rows, each labelled with its row number just below it.
- Columns 0..4: one-pixel coloured strips (red, green, blue, white, yellow) to find the left edge.
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

colors = [(255, 0, 0), (0, 255, 0), (80, 120, 255), (255, 0, 255)]
label_x = [12, 42, 72, 102]
for i, y in enumerate(range(40, 77, 4)):
    c = colors[i % 4]
    d.line((6, y, W - 1, y), fill=c)
    d.text((label_x[i % 4], y + 1), str(y), fill=c, font=font)

for x, c in enumerate([(255, 0, 0), (0, 255, 0), (80, 120, 255), (255, 255, 255), (255, 255, 0)]):
    d.line((x, 0, x, H - 1), fill=c)

disp.image(img)
print("Fine ruler drawn.")
