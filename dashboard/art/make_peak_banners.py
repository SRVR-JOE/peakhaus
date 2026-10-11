"""Section banners for the Peak page, 800x120, "Daybreak" language.

Graphite field, cream Helvetica Neue title at x=28, a thin ember-to-red rule under it,
and one restrained line-art motif at the right edge. Output: banner_<key>.png next to this file.
Run: uv run --with pillow python3 make_peak_banners.py
"""
from PIL import Image, ImageDraw, ImageFont

W, H = 800, 120
BG = (14, 15, 17)
HAIR = (38, 40, 45)
EMBER = (255, 122, 26)
RED = (214, 48, 49)
GOLD = (201, 162, 74)
CREAM = (236, 236, 236)
PROFILES = [(40, 80, 255), (60, 220, 70), (255, 40, 140), (235, 235, 235)]
FONT = ImageFont.truetype('/System/Library/Fonts/HelveticaNeue.ttc', 40, index=1)  # 1 = Medium


def lerp(a, b, t):
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))


def rule(d, x0, x1, y):
    for x in range(x0, x1):
        d.point((x, y), fill=lerp(EMBER, RED, (x - x0) / max(1, x1 - x0)))
    for x in range(x0, x1):
        d.point((x, y + 1), fill=lerp(HAIR, BG, (x - x0) / max(1, x1 - x0)))


def base(title):
    im = Image.new('RGB', (W, H), BG)
    d = ImageDraw.Draw(im)
    d.text((28, 32), title, font=FONT, fill=CREAM)
    tw = d.textlength(title, font=FONT)
    rule(d, 28, int(28 + tw), 86)
    d.line((0, H - 1, W, H - 1), fill=HAIR)
    return im


def S(im):
    """4x supersampled overlay drawer: returns (overlay, draw, scale)."""
    ov = Image.new('RGBA', (W * 4, H * 4), (0, 0, 0, 0))
    return ov, ImageDraw.Draw(ov), 4


def finish(im, ov):
    im.paste(ov.resize((W, H), Image.LANCZOS), (0, 0), ov.resize((W, H), Image.LANCZOS))
    return im


def peak_pro():
    """Motif = the real rig silhouette: outline of the Daybreak render's alpha, faint gold fill inside."""
    from PIL import ImageFilter, ImageChops
    im = base('Peak Pro'); ov, d, s = S(im)
    src = Image.open('daybreak_3q.webp').convert('RGBA')
    a = src.split()[3]
    a = a.crop(a.getbbox())
    h = 104 * s
    w = int(a.width * h / a.height)
    a = a.resize((w, h), Image.LANCZOS).point(lambda v: 255 if v > 110 else 0)
    inner = a.filter(ImageFilter.MinFilter(2 * s + 1))           # eroded by ~2px (at 1x)
    edge = ImageChops.subtract(a, inner)                           # ~2px outline band
    fill = Image.new('RGBA', (w, h), GOLD + (46,))                 # ~18% gold
    line = Image.new('RGBA', (w, h), EMBER + (255,))
    x0 = 748 * s - w // 2                                          # centred at x~748 like the other motifs
    x0 = min(x0, (W - 20) * s - w)
    y0 = (60 * s) - h // 2
    ov.paste(fill, (x0, y0), inner)
    ov.paste(line, (x0, y0), edge)
    return finish(im, ov)


def session():
    im = base('Session'); ov, d, s = S(im)
    x, y = 735, 60
    flame = [(x, y - 42), (x + 22, y - 10), (x + 16, y + 26), (x, y + 40), (x - 16, y + 26), (x - 22, y - 10)]
    d.polygon([(p[0] * s, p[1] * s) for p in flame], outline=EMBER + (255,), width=s * 2)
    inner = [(x, y - 14), (x + 9, y + 4), (x, y + 24), (x - 9, y + 4)]
    d.polygon([(p[0] * s, p[1] * s) for p in inner], outline=RED + (255,), width=s * 2)
    return finish(im, ov)


def profiles():
    im = base('Profiles'); ov, d, s = S(im)
    for i, c in enumerate(PROFILES):
        cx, cy, r = 672 + i * 34, 60, 9
        d.ellipse(((cx - r) * s, (cy - r) * s, (cx + r) * s, (cy + r) * s), fill=c + (255,))
        d.ellipse(((cx - r - 4) * s, (cy - r - 4) * s, (cx + r + 4) * s, (cy + r + 4) * s), outline=HAIR + (255,), width=s)
    return finish(im, ov)


def battery():
    im = base('Battery & use'); ov, d, s = S(im)
    x, y = 690, 60
    d.rounded_rectangle((x * s, (y - 18) * s, (x + 70) * s, (y + 18) * s), radius=6 * s, outline=GOLD + (255,), width=s * 2)
    d.rounded_rectangle(((x + 72) * s, (y - 8) * s, (x + 78) * s, (y + 8) * s), radius=2 * s, fill=GOLD + (255,))
    d.rounded_rectangle(((x + 6) * s, (y - 12) * s, (x + 44) * s, (y + 12) * s), radius=3 * s, fill=EMBER + (255,))
    return finish(im, ov)


def lights():
    im = base('Lights'); ov, d, s = S(im)
    x, y = 735, 54
    d.ellipse(((x - 22) * s, (y - 30) * s, (x + 22) * s, (y + 14) * s), outline=EMBER + (255,), width=s * 2)
    d.rectangle(((x - 11) * s, (y + 16) * s, (x + 11) * s, (y + 30) * s), outline=GOLD + (255,), width=s * 2)
    d.line(((x - 8) * s, (y + 36) * s, (x + 8) * s, (y + 36) * s), fill=GOLD + (255,), width=s * 2)
    for ang in (-50, 0, 50):
        import math
        a = math.radians(ang - 90)
        x0, y0 = x + 30 * math.cos(a), y - 8 + 30 * math.sin(a)
        x1, y1 = x + 40 * math.cos(a), y - 8 + 40 * math.sin(a)
        d.line((x0 * s, y0 * s, x1 * s, y1 * s), fill=RED + (255,), width=s * 2)
    return finish(im, ov)


def bridge():
    im = base('Bridge & Dial'); ov, d, s = S(im)
    # dial ring with tick marks
    cx, cy, r = 745, 60, 30
    d.ellipse(((cx - r) * s, (cy - r) * s, (cx + r) * s, (cy + r) * s), outline=GOLD + (255,), width=s * 2)
    import math
    for i in range(9):
        a = math.radians(-225 + i * 33.75)
        x0, y0 = cx + (r - 7) * math.cos(a), cy + (r - 7) * math.sin(a)
        x1, y1 = cx + (r - 2) * math.cos(a), cy + (r - 2) * math.sin(a)
        d.line((x0 * s, y0 * s, x1 * s, y1 * s), fill=(RED if i >= 7 else HAIR) + (255,), width=s * 2)
    a = math.radians(-225 + 6 * 33.75)
    d.line((cx * s, cy * s, (cx + (r - 10) * math.cos(a)) * s, (cy + (r - 10) * math.sin(a)) * s), fill=EMBER + (255,), width=s * 2)
    # bluetooth rune, left of the dial
    bx, by = 680, 60
    pts = [(bx, by - 26), (bx + 12, by - 13), (bx - 12, by + 13), (bx, by + 26), (bx + 12, by + 13), (bx - 12, by - 13)]
    d.line([(p[0] * s, p[1] * s) for p in [(bx, by - 26), (bx, by + 26)]], fill=EMBER + (255,), width=s * 2)
    d.line([(p[0] * s, p[1] * s) for p in pts], fill=EMBER + (255,), width=s * 2)
    return finish(im, ov)


for key, fn in [('peak_pro', peak_pro), ('session', session), ('profiles', profiles),
                ('battery', battery), ('lights', lights), ('bridge', bridge)]:
    fn().save(f'banner_{key}.png', optimize=True)
    print('banner_' + key)
