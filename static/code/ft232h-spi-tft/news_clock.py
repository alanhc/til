"""Clock + Taiwan news headlines on the 128x64 TFT (via FT232H).

Top bar: time and date. Below: Google News (zh-TW) headlines, 3 lines at a time,
long headlines scroll up line by line. News refreshes every 10 minutes.
Usage: python news_clock.py      (Ctrl+C to stop)
"""
import threading
import time
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime

from PIL import Image, ImageDraw, ImageFont

from tft_test import HEIGHT, WIDTH, open_display

FEED_URL = "https://news.google.com/rss?hl=zh-TW&gl=TW&ceid=TW:zh-Hant"
REFRESH_SEC = 600      # how often to re-fetch news
PAGE_SEC = 3.0         # how long each 3-line page stays up
LINES_PER_PAGE = 3

FONT_TIME = ImageFont.truetype("C:/Windows/Fonts/consolab.ttf", 16)
FONT_DATE = ImageFont.truetype("C:/Windows/Fonts/msjh.ttc", 11)
FONT_NEWS = ImageFont.truetype("C:/Windows/Fonts/msjh.ttc", 12)
FONT_SRC = ImageFont.truetype("C:/Windows/Fonts/msjh.ttc", 10)

WEEKDAYS = "一二三四五六日"
HEADER_H = 18
LINE_H = 15
COL_TIME = (255, 255, 255)
COL_DATE = (120, 200, 255)
COL_NEWS = (255, 230, 120)
COL_SRC = (140, 140, 140)
COL_RULE = (60, 90, 160)


class News:
    """Fetches headlines in a background thread so the clock never stalls."""

    def __init__(self):
        self.items = []          # list of (title, source)
        self.status = "新聞載入中…"
        self.lock = threading.Lock()
        threading.Thread(target=self._loop, daemon=True).start()

    def _loop(self):
        while True:
            try:
                req = urllib.request.Request(FEED_URL, headers={"User-Agent": "Mozilla/5.0"})
                root = ET.fromstring(urllib.request.urlopen(req, timeout=15).read())
                items = []
                for it in root.findall("./channel/item"):
                    title = (it.findtext("title") or "").strip()
                    src = (it.findtext("source") or "").strip()
                    if src and title.endswith(" - " + src):
                        title = title[: -len(" - " + src)]
                    title = title.split(" | ")[0]  # drop "| author | section" tails
                    if title:
                        items.append((title, src))
                with self.lock:
                    self.items = items
                    self.status = "" if items else "沒有抓到新聞"
            except Exception as e:  # network down etc. — keep old headlines if we have them
                with self.lock:
                    if not self.items:
                        self.status = f"新聞讀取失敗：{type(e).__name__}"
            time.sleep(REFRESH_SEC)

    def snapshot(self):
        with self.lock:
            return list(self.items), self.status


def wrap(text, font, width):
    """Wrap by pixel width, character by character (works for Chinese)."""
    lines, cur = [], ""
    for ch in text:
        if font.getlength(cur + ch) > width and cur:
            lines.append(cur)
            cur = ch.lstrip() if ch == " " else ch
        else:
            cur += ch
    if cur:
        lines.append(cur)
    return lines


def pages_for(title, src):
    """Split a headline into 3-line pages; long ones scroll by one line at a time."""
    lines = wrap(title, FONT_NEWS, WIDTH - 4)
    last_start = max(0, len(lines) - LINES_PER_PAGE)
    return [lines[s:s + LINES_PER_PAGE] for s in range(0, last_start + 1)], src


def render(now, page_lines, src, idx, total, status):
    img = Image.new("RGB", (WIDTH, HEIGHT), "black")
    d = ImageDraw.Draw(img)

    d.text((1, -1), now.strftime("%H:%M:%S"), font=FONT_TIME, fill=COL_TIME)
    d.text((WIDTH - 1, 1), f"{now.month}/{now.day} ({WEEKDAYS[now.weekday()]})",
           font=FONT_DATE, fill=COL_DATE, anchor="ra")
    d.line((0, HEADER_H - 1, WIDTH - 1, HEADER_H - 1), fill=COL_RULE)

    if status:
        for i, line in enumerate(wrap(status, FONT_NEWS, WIDTH - 4)[:LINES_PER_PAGE]):
            d.text((2, HEADER_H + 1 + i * LINE_H), line, font=FONT_NEWS, fill=COL_SRC)
        return img

    for i, line in enumerate(page_lines):
        d.text((2, HEADER_H - 1 + i * LINE_H), line, font=FONT_NEWS, fill=COL_NEWS)
    return img


def main():
    disp = open_display()
    news = News()
    headline, page, page_started = 0, 0, time.monotonic()
    last_second = None

    while True:
        items, status = news.snapshot()
        if items:
            headline %= len(items)
            pages, src = pages_for(*items[headline])
            if time.monotonic() - page_started >= PAGE_SEC:
                page_started = time.monotonic()
                page += 1
                if page >= len(pages):
                    page, headline = 0, (headline + 1) % len(items)
                    pages, src = pages_for(*items[headline])
            page_lines = pages[min(page, len(pages) - 1)]
        else:
            page_lines, src = [], ""

        now = datetime.now()
        key = (now.second, headline, page, status)
        if key != last_second:  # only push a frame when something changed
            disp.image(render(now, page_lines, src, headline, len(items), status))
            last_second = key
        time.sleep(0.05)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        pass
