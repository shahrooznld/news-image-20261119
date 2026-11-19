#!/usr/bin/env python3
"""news-image-20261119: draw one image summing up the world news of
Thursday 19 November 2026 and write it to /output/entry.png.

Pure Python standard library: no network, no files read, no Pillow.
The picture is drawn with a small built-in 5x7 bitmap font and encoded
as a PNG with zlib, so the program is deterministic: two runs write
the same bytes. Run it as the grader does:
    MAKEFUN_OUTPUT_DIR=out python3 main.py
"""
import binascii
import os
import struct
import zlib

W, H = 1024, 1024

# --- palette ------------------------------------------------------------
PAPER = (247, 242, 231)
INK = (20, 20, 20)
NAVY = (14, 42, 71)
RED = (180, 35, 24)
GOLD = (201, 162, 39)
GREY = (90, 90, 90)
CARD = (255, 255, 255)
LINE = (216, 210, 196)
SKY = (70, 130, 180)
GREEN = (46, 125, 50)

# --- 5x7 bitmap font (uppercase, digits, punctuation) -------------------
# Each glyph is 7 rows of 5 pixels; '#' is on, '.' is off.
FONT = {
    "A": ("01110", "10001", "10001", "11111", "10001", "10001", "10001"),
    "B": ("11110", "10001", "10001", "11110", "10001", "10001", "11110"),
    "C": ("01110", "10001", "10000", "10000", "10000", "10001", "01110"),
    "D": ("11110", "10001", "10001", "10001", "10001", "10001", "11110"),
    "E": ("11111", "10000", "10000", "11110", "10000", "10000", "11111"),
    "F": ("11111", "10000", "10000", "11110", "10000", "10000", "10000"),
    "G": ("01110", "10001", "10000", "10111", "10001", "10001", "01111"),
    "H": ("10001", "10001", "10001", "11111", "10001", "10001", "10001"),
    "I": ("01110", "00100", "00100", "00100", "00100", "00100", "01110"),
    "J": ("00111", "00010", "00010", "00010", "00010", "10010", "01100"),
    "K": ("10001", "10010", "10100", "11000", "10100", "10010", "10001"),
    "L": ("10000", "10000", "10000", "10000", "10000", "10000", "11111"),
    "M": ("10001", "11011", "10101", "10101", "10001", "10001", "10001"),
    "N": ("10001", "11001", "10101", "10011", "10001", "10001", "10001"),
    "O": ("01110", "10001", "10001", "10001", "10001", "10001", "01110"),
    "P": ("11110", "10001", "10001", "11110", "10000", "10000", "10000"),
    "Q": ("01110", "10001", "10001", "10001", "10101", "10010", "01101"),
    "R": ("11110", "10001", "10001", "11110", "10100", "10010", "10001"),
    "S": ("01111", "10000", "10000", "01110", "00001", "00001", "11110"),
    "T": ("11111", "00100", "00100", "00100", "00100", "00100", "00100"),
    "U": ("10001", "10001", "10001", "10001", "10001", "10001", "01110"),
    "V": ("10001", "10001", "10001", "10001", "10001", "01010", "00100"),
    "W": ("10001", "10001", "10001", "10101", "10101", "11011", "10001"),
    "X": ("10001", "10001", "01010", "00100", "01010", "10001", "10001"),
    "Y": ("10001", "10001", "01010", "00100", "00100", "00100", "00100"),
    "Z": ("11111", "00001", "00010", "00100", "01000", "10000", "11111"),
    "0": ("01110", "10001", "10011", "10101", "11001", "10001", "01110"),
    "1": ("00100", "01100", "00100", "00100", "00100", "00100", "01110"),
    "2": ("01110", "10001", "00001", "00110", "01000", "10000", "11111"),
    "3": ("11110", "00001", "00001", "01110", "00001", "00001", "11110"),
    "4": ("00010", "00110", "01010", "10010", "11111", "00010", "00010"),
    "5": ("11111", "10000", "11110", "00001", "00001", "10001", "01110"),
    "6": ("01110", "10000", "10000", "11110", "10001", "10001", "01110"),
    "7": ("11111", "00001", "00010", "00100", "01000", "01000", "01000"),
    "8": ("01110", "10001", "10001", "01110", "10001", "10001", "01110"),
    "9": ("01110", "10001", "10001", "01111", "00001", "00001", "01110"),
    " ": ("00000", "00000", "00000", "00000", "00000", "00000", "00000"),
    ".": ("00000", "00000", "00000", "00000", "00000", "01100", "01100"),
    ",": ("00000", "00000", "00000", "00000", "01100", "00100", "01000"),
    ":": ("00000", "01100", "01100", "00000", "01100", "01100", "00000"),
    ";": ("00000", "01100", "01100", "00000", "01100", "00100", "01000"),
    "'": ("00100", "00100", "01000", "00000", "00000", "00000", "00000"),
    "-": ("00000", "00000", "00000", "01110", "00000", "00000", "00000"),
    "&": ("01100", "10010", "10100", "01000", "10101", "10010", "01101"),
    "(": ("00010", "00100", "01000", "01000", "01000", "00100", "00010"),
    ")": ("01000", "00100", "00010", "00010", "00010", "00100", "01000"),
    "!": ("00100", "00100", "00100", "00100", "00100", "00000", "00100"),
    "?": ("01110", "10001", "00001", "00110", "00100", "00000", "00100"),
    "/": ("00001", "00010", "00010", "00100", "01000", "01000", "10000"),
    "%": ("11001", "11010", "00010", "00100", "01000", "01011", "10011"),
    "$": ("00100", "01111", "10100", "01110", "00101", "11110", "00100"),
    "+": ("00000", "00100", "00100", "11111", "00100", "00100", "00000"),
    "=": ("00000", "00000", "11111", "00000", "11111", "00000", "00000"),
    '"': ("01010", "01010", "00000", "00000", "00000", "00000", "00000"),
    "*": ("00000", "00100", "10101", "01110", "10101", "00100", "00000"),
}

# Em dash / en dash / bullet / curly apostrophe map to plain glyphs.
ALIASES = {"\u2014": "-", "\u2013": "-", "\u2019": "'", "\u2018": "'",
           "\u2022": "*", "\u00b7": "*", "\u201c": '"', "\u201d": '"'}


def glyph(ch):
    return FONT.get(ALIASES.get(ch, ch), FONT["?"])


def text_width(text, scale):
    """Width in pixels of text drawn at the given scale (6 px per char)."""
    return len(text) * 6 * scale


def wrap_text(text, scale, max_width):
    """Greedy word wrap; returns a list of lines fitting max_width."""
    words = text.split(" ")
    lines, cur = [], ""
    for word in words:
        trial = word if not cur else cur + " " + word
        if text_width(trial, scale) <= max_width or not cur:
            cur = trial
        else:
            lines.append(cur)
            cur = word
    if cur:
        lines.append(cur)
    return lines


class Canvas:
    """An RGB pixel buffer with tiny drawing helpers."""

    def __init__(self, w, h, bg):
        self.w = w
        self.h = h
        self.px = bytearray(bg * (w * h))

    def _set(self, x, y, color):
        if 0 <= x < self.w and 0 <= y < self.h:
            i = (y * self.w + x) * 3
            self.px[i:i + 3] = bytes(color)

    def rect(self, x, y, w, h, color):
        for yy in range(max(0, y), min(self.h, y + h)):
            base = (yy * self.w + max(0, x)) * 3
            row = bytes(color) * (min(self.w, x + w) - max(0, x))
            self.px[base:base + len(row)] = row

    def hline(self, x, y, w, color, t=1):
        self.rect(x, y, w, t, color)

    def vline(self, x, y, h, color, t=1):
        self.rect(x, y, t, h, color)

    def circle(self, cx, cy, r, color, fill=True):
        for yy in range(cy - r, cy + r + 1):
            dx = int((r * r - (yy - cy) ** 2) ** 0.5) if abs(yy - cy) <= r else 0
            if fill:
                self.rect(cx - dx, yy, dx * 2 + 1, 1, color)
            else:
                self._set(cx - dx, yy, color)
                self._set(cx + dx, yy, color)

    def disc(self, cx, cy, r, color):
        self.circle(cx, cy, r, color, fill=True)

    def ring(self, cx, cy, r, color, t=2):
        for k in range(t):
            self.circle(cx, cy, r - k, color, fill=False)

    def line(self, x0, y0, x1, y1, color):
        """Bresenham line."""
        dx, dy = abs(x1 - x0), abs(y1 - y0)
        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1
        err = dx - dy
        while True:
            self._set(x0, y0, color)
            if x0 == x1 and y0 == y1:
                return
            e2 = 2 * err
            if e2 > -dy:
                err -= dy
                x0 += sx
            if e2 < dx:
                err += dx
                y0 += sy

    def char(self, x, y, ch, scale, color):
        g = glyph(ch)
        for row in range(7):
            bits = g[row]
            for col in range(5):
                if bits[col] == "1":
                    self.rect(x + col * scale, y + row * scale,
                              scale, scale, color)

    def text(self, x, y, s, scale, color):
        for ch in s:
            self.char(x, y, ch, scale, color)
            x += 6 * scale
        return x

    def text_center(self, cx, y, s, scale, color):
        self.text(cx - text_width(s, scale) // 2, y, s, scale, color)

    def block(self, x, y, s, scale, color, max_width, leading=None):
        """Wrapped text block; returns the y just below the last line."""
        lh = leading if leading is not None else 9 * scale
        for ln in wrap_text(s, scale, max_width):
            self.text(x, y, ln, scale, color)
            y += lh
        return y


# --- PNG encoding (stdlib only, deterministic) --------------------------
def _chunk(kind, data):
    out = struct.pack(">I", len(data)) + kind + data
    out += struct.pack(">I", binascii.crc32(kind + data) & 0xFFFFFFFF)
    return out


def to_png(canvas):
    raw = bytearray()
    stride = canvas.w * 3
    for yy in range(canvas.h):
        raw.append(0)  # filter: None
        raw += canvas.px[yy * stride:(yy + 1) * stride]
    ihdr = struct.pack(">IIBBBBB", canvas.w, canvas.h, 8, 2, 0, 0, 0)
    return (b"\x89PNG\r\n\x1a\n"
            + _chunk(b"IHDR", ihdr)
            + _chunk(b"IDAT", zlib.compress(bytes(raw), 9))
            + _chunk(b"IEND", b""))


# --- little pictograms ----------------------------------------------------
def draw_globe(c, cx, cy, r):
    """A simple globe: blue disc, meridian/parallel lines, three dots."""
    c.disc(cx, cy, r, SKY)
    c.ring(cx, cy, r, NAVY, 3)
    for k in range(1, 4):  # parallels
        yy = cy - r + k * (2 * r) // 4
        dx = int((r * r - (yy - cy) ** 2) ** 0.5)
        c.rect(cx - dx, yy, dx * 2 + 1, 2, (255, 255, 255))
    for k in range(-2, 3):  # meridians
        rx = abs(k) * r // 3
        for yy in range(cy - r + 2, cy + r - 1):
            t = (yy - cy) / r
            xx = int(rx * (1 - t * t) ** 0.5)
            c._set(cx - xx, yy, (255, 255, 255))
            c._set(cx + xx, yy, (255, 255, 255))
    c.disc(cx - r // 2, cy - r // 4, 7, RED)     # USA
    c.disc(cx + r // 2, cy - r // 5, 7, GOLD)    # China
    c.disc(cx + r // 4, cy + r // 2, 7, CARD)    # Russia


def draw_court(c, x, y, w, h, color):
    """A courthouse: pediment, three columns, base."""
    c.line(x, y + 18, x + w // 2, y, color)
    c.line(x + w // 2, y, x + w, y + 18, color)
    c.rect(x, y + 18, w, 6, color)
    for k in range(3):
        cx = x + 6 + k * (w - 12) // 3
        c.rect(cx, y + 24, 8, h - 32, color)
    c.rect(x, y + h - 8, w, 8, color)


def draw_bridge(c, x, y, w, h, color):
    """A suspension bridge: deck, two towers, cables, arch."""
    c.rect(x, y + h - 6, w, 6, color)
    c.rect(x + w // 6, y, 8, h, color)
    c.rect(x + 5 * w // 6 - 8, y, 8, h, color)
    c.line(x + w // 6 + 4, y + 4, x + w // 2, y + h // 2, color)
    c.line(x + 5 * w // 6 - 4, y + 4, x + w // 2, y + h // 2, color)
    for k in range(1, 6):
        xx = x + k * w // 6
        c.vline(xx, y + h // 2 - k * 2, h // 2 + k * 2 - 6, color, 2)


def draw_flag_stripes(c, x, y, w, h):
    """Three small flag bars: USA, China, Russia."""
    # USA: red/white stripes + blue corner
    c.rect(x, y, w, h, (255, 255, 255))
    for k in range(0, 7, 2):
        c.rect(x, y + k * h // 7, w, h // 7, RED)
    c.rect(x, y, w * 2 // 5, h * 4 // 7, NAVY)
    # China: red field, gold stars as dots
    c.rect(x + w + 14, y, w, h, RED)
    c.disc(x + w + 14 + w // 4, y + h // 3, 6, GOLD)
    c.disc(x + w + 14 + w // 2, y + h // 4, 3, GOLD)
    c.disc(x + w + 14 + w // 2, y + h // 2, 3, GOLD)
    # Russia: white / blue / red horizontal bands
    c.rect(x + 2 * w + 28, y, w, h, (255, 255, 255))
    c.rect(x + 2 * w + 28, y + h // 3, w, h // 3, (0, 60, 160))
    c.rect(x + 2 * w + 28, y + 2 * h // 3, w, h // 3, RED)


# --- the front page ---------------------------------------------------------
def build_png():
    c = Canvas(W, H, PAPER)

    # Masthead: navy band, paper name, the date in large type.
    c.rect(0, 0, W, 124, NAVY)
    c.text_center(W // 2, 16, "THE WORLD IN ONE IMAGE", 3, GOLD)
    c.text_center(W // 2, 52, "THURSDAY 19 NOVEMBER 2026", 6, CARD)
    c.rect(0, 106, W, 3, GOLD)
    c.rect(0, 116, W, 8, RED)

    # Lead story: the Shenzhen three-way summit.
    c.text(36, 148, "APEC SUMMIT * SHENZHEN, CHINA", 3, RED)
    c.text(36, 190, "TRUMP, XI & PUTIN", 7, INK)
    c.text(36, 246, "MEET IN SHENZHEN", 7, INK)
    y = c.block(36, 322, "FIRST THREE-WAY SUMMIT OF THE US, CHINA "
                "AND RUSSIA LEADERS", 3, INK, 700, leading=27)
    y = c.block(36, y + 6, "JOINT PLEDGE ON NUCLEAR RISKS AND "
                "STEADY ENERGY FLOWS", 3, INK, 700, leading=27)
    c.text(36, 440, "DISCUSSED: UKRAINE, IRAN, TRADE", 2, GREY)
    draw_globe(c, 875, 290, 80)
    draw_flag_stripes(c, 800, 400, 54, 34)
    c.hline(36, 486, 952, INK, 2)

    # Middle row: the ICJ genocide ruling and the Crimean Bridge.
    c.text(36, 508, "THE HAGUE * UN COURT", 3, RED)
    c.text(36, 544, "MYANMAR GUILTY", 5, INK)
    c.text(36, 586, "OF GENOCIDE", 5, INK)
    c.block(36, 640, "UN COURT: 2017 CRACKDOWN ON ROHINGYA "
           "WAS GENOCIDE", 3, INK, 460, leading=27)
    draw_court(c, 400, 700, 70, 60, NAVY)
    c.vline(512, 500, 270, LINE, 2)

    c.text(528, 508, "UKRAINE * WAR", 3, RED)
    c.text(528, 544, "CRIMEAN BRIDGE", 5, INK)
    c.text(528, 586, "HIT A 3RD TIME", 5, INK)
    c.block(528, 640, "UKRAINE STRIKES THE BRIDGE AGAIN - RAIL "
           "SECTION HIT, TRAINS HALTED", 3, INK, 460, leading=27)
    draw_bridge(c, 800, 700, 150, 48, NAVY)
    c.hline(36, 786, 952, INK, 2)

    # Bottom row: three short cards.
    cards = [
        (36, "MIDDLE EAST", "ISRAEL PUSHES", "INTO GAZA",
         "GROUND OPERATION IN CENTRAL GAZA"),
        (364, "GULF", "US HITS IRAN", "GULF HIT BACK",
         "IRAN HITS KUWAIT AND BAHRAIN AFTER US STRIKE"),
        (692, "TECH * MARKETS", "RECORD $81BN", "ANTHROPIC IPO",
         "AI FIRM RAISES ABOUT $81BN IN RECORD DEBUT"),
    ]
    for x, kicker, h1, h2, sub in cards:
        c.rect(x, 800, 296, 150, CARD)
        c.rect(x, 800, 296, 4, RED)
        c.rect(x, 800, 4, 150, LINE)
        c.rect(x + 292, 800, 4, 150, LINE)
        c.rect(x, 946, 296, 4, LINE)
        c.text(x + 16, 814, kicker, 2, RED)
        c.text(x + 16, 838, h1, 3, INK)
        c.text(x + 16, 865, h2, 3, INK)
        c.block(x + 16, 898, sub, 2, GREY, 264, leading=18)

    # Footer ticker: the rest of the day, in one strip.
    c.rect(0, 962, W, 62, NAVY)
    c.text_center(W // 2, 970,
                  "ALSO: CYCLONE AKVAN NEARS INDIA * UNREST IN BANGLADESH",
                  2, CARD)
    c.text_center(W // 2, 992,
                  "MIGRANT BOAT SINKS OFF SENEGAL * COP31 TALKS IN FINAL STAGE",
                  2, CARD)
    return to_png(c)


def main():
    out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
    os.makedirs(out_dir, exist_ok=True)
    path = os.path.join(out_dir, "entry.png")
    data = build_png()
    with open(path, "wb") as f:
        f.write(data)
    print("wrote %s (%d bytes)" % (path, len(data)))


if __name__ == "__main__":
    main()
