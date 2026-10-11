"""Render the compact Peak "rig card" art: portrait 900x1200, no text, no leader lines.

Source: daybreak_3q.webp (Peak Pro Daybreak 3/4 render, transparent). Outputs next to this file:
  peak_rig_bg.png      graphite (14,15,17) background + rig + soft ground shadow
  peak_rig_glow.png    transparent; warm spill under the base ring (shown while a heat session runs)
  peak_rig_none.png    fully transparent (idle overlay)
  peak_rig_preview.png bg + glow composite, for eyeballing only (not uploaded)
Run from dashboard/art with daybreak_3q.webp beside it:  uv run --with pillow python3 make_peak_rig.py
Upload the three with ../upload_art.py from a staging directory NAMED "peak" (group = dir basename), then
copy the peak/* entries into dashboard/art/ids.json.
"""
from PIL import Image, ImageDraw, ImageFilter

W, H = 900, 1200
BG = (14, 15, 17, 255)

src = Image.open('daybreak_3q.webp').convert('RGBA')
peak = src.crop(src.getbbox())
ph = int(H * 0.86)
pw = int(peak.width * ph / peak.height)
peak = peak.resize((pw, ph), Image.LANCZOS)
px = (W - pw) // 2
py = 1120 - ph

canvas = Image.new('RGBA', (W, H), BG)
# soft elliptical ground shadow under the foot
sh = Image.new('L', (W, H), 0)
ImageDraw.Draw(sh).ellipse((px + 30, py + ph - 26, px + pw - 10, py + ph + 24), fill=150)
canvas.paste((0, 0, 0, 255), (0, 0), sh.filter(ImageFilter.GaussianBlur(16)))
canvas.alpha_composite(peak, (px, py))
canvas.convert('RGB').save('peak_rig_bg.png', optimize=True)

# warm spill under the base ring
g = Image.new('RGBA', (W, H), (0, 0, 0, 0))
m = Image.new('L', (W, H), 0)
cx = px + pw // 2 + 12          # the 3/4 render's foot sits slightly right of the bbox centre
ImageDraw.Draw(m).ellipse((cx - 175, py + ph - 34, cx + 175, py + ph + 24), fill=135)
g.paste((255, 122, 26, 255), (0, 0), m.filter(ImageFilter.GaussianBlur(24)))
g.save('peak_rig_glow.png', optimize=True)

Image.new('RGBA', (W, H), (0, 0, 0, 0)).save('peak_rig_none.png', optimize=True)

prev = Image.open('peak_rig_bg.png').convert('RGBA')
prev.alpha_composite(g)
prev.save('peak_rig_preview.png')
print(f'rig {pw}x{ph} at ({px},{py}); margins L/R {px}/{W-pw-px}, top {py}, bottom {H-(py+ph)}')
