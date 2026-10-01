"""One-off icon generator for the PWA manifest (run once, output committed
to the repo like any other static asset -- no runtime dependency on PIL
beyond this script). Produces a simple "GT" lettermark matching the app's
existing dark-navy/cyan/purple theme (see base.html's nav logo)."""
from PIL import Image, ImageDraw, ImageFont

BG = (10, 14, 23)        # #0a0e17 -- matches body background / theme-color
ACCENT = (34, 211, 238)  # #22d3ee -- cyan, "G"
ACCENT2 = (168, 85, 247)  # #a855f7 -- purple, "T"

FONT_CANDIDATES = [
    r"C:\Windows\Fonts\arialbd.ttf",
    r"C:\Windows\Fonts\seguisb.ttf",
    r"C:\Windows\Fonts\Arial.ttf",
]


def _load_font(size):
    for candidate in FONT_CANDIDATES:
        try:
            return ImageFont.truetype(candidate, size)
        except OSError:
            continue
    return ImageFont.load_default()


def make_icon(size, path):
    img = Image.new("RGB", (size, size), BG)
    draw = ImageDraw.Draw(img)
    font = _load_font(int(size * 0.5))

    g_box = draw.textbbox((0, 0), "G", font=font)
    t_box = draw.textbbox((0, 0), "T", font=font)
    g_w, g_h = g_box[2] - g_box[0], g_box[3] - g_box[1]
    t_w, t_h = t_box[2] - t_box[0], t_box[3] - t_box[1]

    gap = size * 0.02
    total_w = g_w + gap + t_w
    start_x = (size - total_w) / 2
    y = (size - max(g_h, t_h)) / 2

    draw.text((start_x - g_box[0], y - g_box[1]), "G", font=font, fill=ACCENT)
    draw.text((start_x + g_w + gap - t_box[0], y - t_box[1]), "T", font=font, fill=ACCENT2)

    img.save(path)


if __name__ == "__main__":
    import os
    os.makedirs("static/icons", exist_ok=True)
    make_icon(192, "static/icons/icon-192.png")
    make_icon(512, "static/icons/icon-512.png")
    print("Icons written to static/icons/")
