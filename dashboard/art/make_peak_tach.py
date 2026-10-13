"""Race Tach heater card art for the Peak page (800x800, matches the Dial's Race Tach livery).

Outputs: tach_face.png (black face, numerals 0-7 x100 degF, ticks, caption; no needle/redline),
tach_needle.png (transparent; orange needle pointing at 0 = 225 deg, rotated by card_mod),
tach_redline_pN.png (transparent; red arc from profile N's target to 700).
Sweep: 270 deg, 0 at 225 deg (bottom-left) clockwise to 700 at -45 deg (bottom-right).
Run: uv run --with pillow python3 make_peak_tach.py [t1 t2 t3 t4]  (targets in degF)
"""
import math, sys
from PIL import Image, ImageDraw, ImageFont

S = 800; SS = 4; W = S * SS; C = W / 2
R_OUT = 0.46 * W; R_MAJ = 0.395 * W; R_MIN = 0.42 * W; R_NUM = 0.33 * W
BG = (14, 15, 17, 255); CREAM = (236, 236, 236, 255); MID = (154, 160, 168, 255); DIM = (90, 94, 102, 255)
EMBER = (255, 122, 26, 255); RED = (220, 36, 36, 255)
FONT = '/System/Library/Fonts/HelveticaNeue.ttc'

def ang(v):  # degF -> compass angle (deg, 0 = +x, counter-clockwise positive in math coords)
    return 225 - (v / 700.0) * 270

def pt(a, r):
    return (C + r * math.cos(math.radians(a)), C - r * math.sin(math.radians(a)))

def down(img):
    return img.resize((S, S), Image.LANCZOS)

def face():
    img = Image.new('RGBA', (W, W), BG)
    d = ImageDraw.Draw(img)
    # bezel ring
    d.ellipse((C - R_OUT - 6*SS, C - R_OUT - 6*SS, C + R_OUT + 6*SS, C + R_OUT + 6*SS), outline=(44, 46, 52, 255), width=3*SS)
    # arc track
    bb = (C - R_OUT, C - R_OUT, C + R_OUT, C + R_OUT)
    d.arc(bb, start=-ang(0), end=-ang(700), fill=(60, 63, 70, 255), width=2*SS)
    f_num = ImageFont.truetype(FONT, int(0.085 * W), index=0)
    f_cap = ImageFont.truetype(FONT, int(0.03 * W), index=0)
    for v in range(0, 701, 20):
        a = ang(v)
        major = v % 100 == 0
        r1 = R_OUT
        r2 = R_MAJ if major else R_MIN
        d.line([pt(a, r1), pt(a, r2)], fill=CREAM if major else DIM, width=(5 if major else 2) * SS)
        if major:
            x, y = pt(a, R_NUM)
            d.text((x, y), str(v // 100), font=f_num, fill=CREAM, anchor='mm')
    d.text((C, C + 0.21 * W), 'x100 °F', font=f_cap, fill=MID, anchor='mm')
    down(img).save('tach_face.png')

def needle():
    img = Image.new('RGBA', (W, W), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    a = ang(0)
    tip = pt(a, R_MAJ - 10*SS)
    tail = pt(a + 180, 0.07 * W)
    # tapered needle: polygon from tail to tip
    nx, ny = math.cos(math.radians(a + 90)), -math.sin(math.radians(a + 90))
    w0 = 7 * SS
    poly = [(tail[0] + nx*w0, tail[1] + ny*w0), (tip[0] + nx*1.5*SS, tip[1] + ny*1.5*SS),
            (tip[0] - nx*1.5*SS, tip[1] - ny*1.5*SS), (tail[0] - nx*w0, tail[1] - ny*w0)]
    d.polygon(poly, fill=EMBER)
    hub = 0.045 * W
    d.ellipse((C - hub, C - hub, C + hub, C + hub), fill=(28, 29, 33, 255), outline=(70, 73, 80, 255), width=3*SS)
    d.ellipse((C - hub*0.35, C - hub*0.35, C + hub*0.35, C + hub*0.35), fill=EMBER)
    down(img).save('tach_needle.png')

def redline(n, target):
    img = Image.new('RGBA', (W, W), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    r = R_OUT - 7*SS
    bb = (C - r, C - r, C + r, C + r)
    d.arc(bb, start=-ang(target), end=-ang(700), fill=RED, width=9*SS)
    down(img).save(f'tach_redline_p{n}.png')

if __name__ == '__main__':
    targets = [int(x) for x in sys.argv[1:5]] or [490, 510, 530, 575]
    face(); needle()
    for i, t in enumerate(targets, 1):
        redline(i, t)
    # preview composite with the needle at 0 and profile 2 redline
    f = Image.open('tach_face.png').convert('RGBA'); f.alpha_composite(Image.open('tach_redline_p2.png'))
    f.alpha_composite(Image.open('tach_needle.png')); f.save('tach_preview.png')
    print('rendered', targets)
