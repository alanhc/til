"""0.96" 128x64 RGB TFT (ST7735-compatible) test via FT232H.

Wiring: SCL->D0, SDA->D1, CS->C0, DC->C1, RES->C2, VCC/BLK->3V, GND->GND
Calibrated for this panel: visible window starts at column 2, row 70 of the controller RAM;
colours need invert=False, bgr=False.
"""
import os

# Make the libusb DLL (from the libusb-package wheel) findable by pyusb, and enable Blinka's FT232H mode.
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

WIDTH, HEIGHT = 128, 64
X_OFFSET, Y_OFFSET = 2, 67


def open_display():
    return st7735.ST7735R(
        board.SPI(),
        cs=digitalio.DigitalInOut(board.C0),
        dc=digitalio.DigitalInOut(board.C1),
        rst=digitalio.DigitalInOut(board.C2),
        width=WIDTH,
        height=HEIGHT,
        x_offset=X_OFFSET,
        y_offset=Y_OFFSET,
        invert=False,
        bgr=False,
        baudrate=24_000_000,
        rotation=0,
    )


if __name__ == "__main__":
    disp = open_display()
    img = Image.new("RGB", (WIDTH, HEIGHT), "black")
    d = ImageDraw.Draw(img)
    font = ImageFont.load_default()

    d.rectangle((0, 0, WIDTH - 1, HEIGHT - 1), outline="white")
    for j, c in enumerate([(255, 0, 0), (0, 255, 0), (0, 0, 255)]):
        d.rectangle((4 + j * 40, 4, 4 + j * 40 + 39, 18), fill=c)
    d.text((WIDTH // 2, 32), "Hello FT232H!", fill="yellow", font=font, anchor="mm")
    d.text((WIDTH // 2, 50), "128 x 64", fill="cyan", font=font, anchor="mm")

    disp.image(img)
    print("Done. Expect: white frame, red/green/blue bars, yellow 'Hello FT232H!', cyan '128 x 64'.")
