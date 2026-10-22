"""Kode render frame referensi Sonya (kolase rapi + close-up sinematik), 1080x1920.
Contoh TEKNIK: digambar 2x lalu diperkecil, sobekan kertas halus, teks ikut miring, cahaya/vignette/butiran.
Jalankan: python3 referensi/render_referensi.py <folder_keluar> [collage] [cinema]"""
import math, random, os, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageChops

FD = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'assets', 'fonts') + '/'
OUT = sys.argv[1] if len(sys.argv) > 1 else 'out'
os.makedirs(OUT, exist_ok=True)
S = 2
W, H = 1080 * S, 1920 * S
WHITE = (255, 255, 255); INK = (21, 23, 28); KOB = (47, 75, 219); SIN = (226, 71, 43); OKR = (231, 160, 46)
G1 = (108, 114, 126); G2 = (206, 210, 218); G3 = (240, 242, 246)


def F(w, px):
    n = {'B': 'InterDisplay-Bold.otf', 'M': 'Inter-Medium.otf', 'R': 'Inter-Regular.otf', 'mono': 'DejaVuSansMono.ttf'}[w]
    return ImageFont.truetype(FD + n, int(px * S))


def P(v):
    return int(v * S)


def wrap(d, s, f, maxw):
    out, cur = [], ''
    for w in s.split():
        t = (cur + ' ' + w).strip()
        if d.textlength(t, font=f) <= maxw * S or not cur:
            cur = t
        else:
            out.append(cur); cur = w
    out.append(cur)
    return out


def para(d, xy, s, f, fill, maxw, lh=1.18, anchor='la'):
    x, y = xy
    for ln in wrap(d, s, f, maxw):
        d.text((P(x), P(y)), ln, font=f, fill=fill, anchor=anchor)
        y += f.size / S * lh
    return y


def save(img, name):
    img = img.convert('RGB').resize((1080, 1920), Image.LANCZOS)
    img.save(os.path.join(OUT, name + '.png'))
    img.resize((540, 960), Image.LANCZOS).save(os.path.join(OUT, name + '.jpg'), quality=86)


def grain(img, amt=10, seed=1):
    rng = np.random.default_rng(seed)
    a = np.asarray(img.convert('RGB')).astype(np.int16)
    n = rng.normal(0, amt, a.shape[:2])[..., None]
    return Image.fromarray(np.clip(a + n, 0, 255).astype(np.uint8))


def handle(d, x, y, fill, size=30, anchor='la'):
    d.text((P(x), P(y)), '@nuancierstudio', font=F('M', size), fill=fill, anchor=anchor)


def mark(d, cx, cy, r, fg, bg):
    """Logo contoh fiktif: lingkaran dengan potongan seperempat + titik."""
    d.ellipse([P(cx - r), P(cy - r), P(cx + r), P(cy + r)], fill=fg)
    d.rectangle([P(cx), P(cy - r - 2), P(cx + r + 2), P(cy)], fill=bg)
    rr = r * 0.34
    d.ellipse([P(cx + r * 0.5 - rr), P(cy - r * 0.5 - rr), P(cx + r * 0.5 + rr), P(cy - r * 0.5 + rr)], fill=fg)


# ---------------------------------------------------------------- Kolase rapi
def _edge(a, b, n, amp, rnd, tear):
    """Titik dari a ke b; bila tear, beri noise halus (bukan gerigi acak)."""
    ph = [rnd.uniform(0, 6.28) for _ in range(4)]; fr = [rnd.uniform(3, 7), rnd.uniform(11, 19), rnd.uniform(29, 41), rnd.uniform(70, 90)]
    wt = [1.0, 0.45, 0.22, 0.12]
    (x0, y0), (x1, y1) = a, b
    L = math.hypot(x1 - x0, y1 - y0); nx, ny = -(y1 - y0) / L, (x1 - x0) / L
    pts = []
    for k in range(n):
        t = k / n
        off = sum(w * math.sin(f * t * 6.28 + p) for w, f, p in zip(wt, fr, ph)) / 1.8 * amp if tear else 0
        pts.append((x0 + (x1 - x0) * t + nx * off, y0 + (y1 - y0) * t + ny * off))
    return pts


def rip(box, tear, seed, rot=0.0, amp=5, inset=0):
    """Kertas persegi dipotong rapi; sisi di `tear` (t/r/b/l) disobek halus. inset menarik sisi sobek ke dalam."""
    x0, y0, x1, y1 = [P(v) for v in box]
    rnd = random.Random(seed); I = P(inset)
    c = [(x0 + (I if 'l' in tear else 0), y0 + (I if 't' in tear else 0)), (x1 - (I if 'r' in tear else 0), y0 + (I if 't' in tear else 0)),
         (x1 - (I if 'r' in tear else 0), y1 - (I if 'b' in tear else 0)), (x0 + (I if 'l' in tear else 0), y1 - (I if 'b' in tear else 0))]
    sides = ['t', 'r', 'b', 'l']; pts = []
    for k in range(4):
        a, b = c[k], c[(k + 1) % 4]
        n = max(2, int(math.hypot(b[0] - a[0], b[1] - a[1]) / P(4)))
        pts += _edge(a, b, n, P(amp), rnd, sides[k] in tear)
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2; r = math.radians(rot)
    return [(cx + (x - cx) * math.cos(r) - (y - cy) * math.sin(r), cy + (x - cx) * math.sin(r) + (y - cy) * math.cos(r)) for x, y in pts]


FIBER = (246, 244, 239)


def sheet(base, box, tear, col, seed, rot=0.0):
    outer = rip(box, tear, seed, rot, 5, 0)
    inner = rip(box, tear, seed + 100, rot, 4, 6)
    sh = Image.new('L', (W, H), 0)
    ImageDraw.Draw(sh).polygon([(x + P(4), y + P(9)) for x, y in outer], fill=70)
    base.paste((10, 12, 18), (0, 0), sh.filter(ImageFilter.GaussianBlur(P(9))))
    m = Image.new('L', (W, H), 0); ImageDraw.Draw(m).polygon(outer, fill=255)
    base.paste(FIBER, (0, 0), m)
    m = Image.new('L', (W, H), 0); ImageDraw.Draw(m).polygon(inner if tear else outer, fill=255)
    base.paste(grain(Image.new('RGB', (W, H), col), 5, seed), (0, 0), m)


def rtext(base, xy, s, f, fill, rot, center):
    """Teks ikut miring bersama kertasnya (rotasi sama terhadap pusat kertas)."""
    lay = Image.new('L', (W, H), 0); ImageDraw.Draw(lay).text((P(xy[0]), P(xy[1])), s, font=f, fill=255)
    lay = lay.rotate(-rot, resample=Image.BICUBIC, center=(P(center[0]), P(center[1])))
    base.paste(fill, (0, 0), lay)


def collage():
    im = Image.new('RGB', (W, H), (247, 247, 245))
    sheet(im, (500, 840, 1010, 1060), 't', OKR, 2, 1.4)
    sheet(im, (70, 230, 1010, 900), 'b', KOB, 1, -1.0)
    sheet(im, (70, 950, 420, 1170), 'r', SIN, 3, -1.6)
    sheet(im, (70, 1230, 1010, 1390), 'tb', WHITE, 4, 0.5)
    c1 = (540, 565)
    for k, w in enumerate(['Merek', 'itu', 'tempelan?']):
        rtext(im, (130, 300 + k * 160), w, F('B', 140), WHITE, -1.0, c1)
    rtext(im, (130, 1282), 'Bukan. Ia disusun, lapis demi lapis.', F('M', 40), INK, 0.5, (540, 1310))
    d = ImageDraw.Draw(im); handle(d, 70, 1450, INK)
    save(im, '4_kolase_a')

    im = Image.new('RGB', (W, H), SIN)
    rots = [-1.0, 0.8, -0.6]
    for i, (col, tc, w) in enumerate([(KOB, WHITE, 'Warna'), (OKR, INK, 'Huruf'), (WHITE, INK, 'Bentuk')]):
        y = 270 + i * 330
        box = (70, y, 830, y + 270)
        sheet(im, box, 'r', col, 10 + i, rots[i])
        rtext(im, (130, y + 70), w, F('B', 120), tc, rots[i], ((70 + 830) / 2, y + 135))
    d = ImageDraw.Draw(im)
    para(d, (70, 1300), 'Tiga lapis yang membuat merekmu dikenali.', F('B', 56), WHITE, 860, 1.1)
    handle(d, 70, 1450, WHITE)
    save(im, '4_kolase_b')


# ---------------------------------------------------------------- 6 Close-up sinematik
def cinema():
    big = Image.new('RGB', (W, H), INK); d = ImageDraw.Draw(big)
    cx, cy, r = P(1500), P(1100), P(1300)
    d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=KOB)
    d.rectangle([cx, cy - r - 10, cx + r + 10, cy], fill=INK)
    # cahaya
    yy, xx = np.mgrid[0:H, 0:W]
    light = np.exp(-(((xx - P(300)) ** 2 + (yy - P(500)) ** 2) / (2 * P(520) ** 2)))[..., None]
    a = np.asarray(big).astype(np.float32)
    a = a * (0.55 + 0.75 * light)
    vig = 1 - 0.55 * (((xx - W / 2) / (W * 0.75)) ** 2 + ((yy - H / 2) / (H * 0.75)) ** 2)[..., None]
    a = np.clip(a * np.clip(vig, 0.3, 1), 0, 255).astype(np.uint8)
    im = Image.fromarray(a).filter(ImageFilter.GaussianBlur(P(3)))
    im = grain(im, 6, 8); d = ImageDraw.Draw(im)
    para(d, (540, 1300), 'Lihat lebih dekat.', F('B', 88), WHITE, 860, anchor='ma')
    d.text((P(540), P(1430)), '@nuancierstudio', font=F('M', 28), fill=G2, anchor='ma')
    save(im, '6_sinema_a')

    im = Image.new('RGB', (W, H), INK); d = ImageDraw.Draw(im)
    mark(d, 540, 760, 280, KOB, INK)
    a = np.asarray(im).astype(np.float32)
    glow = np.asarray(im.filter(ImageFilter.GaussianBlur(P(60)))).astype(np.float32)
    im = Image.fromarray(np.clip(a + glow * 0.6, 0, 255).astype(np.uint8))
    im = grain(im, 5, 9); d = ImageDraw.Draw(im)
    d.line([P(240), P(1180), P(840), P(1180)], fill=(60, 64, 74), width=P(2))
    para(d, (540, 1230), 'Dari dekat, setiap lengkung punya alasan.', F('B', 60), WHITE, 820, 1.12, anchor='ma')
    d.text((P(540), P(1440)), 'Logo contoh, FIKTIF', font=F('M', 26), fill=G1, anchor='ma')
    save(im, '6_sinema_b')


for fn in ([globals()[a] for a in sys.argv[2:]] or [collage, cinema]):
    fn(); print('ok', fn.__name__)
