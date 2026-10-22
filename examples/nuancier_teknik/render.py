"""Contoh TEKNIK Studio Sonya (sinkron suara per baris, audio sintetis, wipe, pemeriksaan zona aman).
BUKAN contoh tampilan: jangan meniru kerangka header/judul/kartu/strip ini. Tiap pesanan harus punya arah visual sendiri.
Jalankan: buat vo/ dengan `python3 toolkit/studio.py vo-split vo.mp3 examples/nuancier_teknik/lines.json examples/nuancier_teknik/vo`,
lalu `python3 examples/nuancier_teknik/render.py full`.
"""
import sys, json, math, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from toolkit.studio import VideoWriter, load_wav, save_wav, normalize, place, mix, SR

D = os.path.dirname(os.path.abspath(__file__))
W, H, FPS = 1080, 1920, 30
WHITE = (255, 255, 255); TINTA = (21, 23, 28)
KOB = (47, 75, 219); SIN = (226, 71, 43); OKER = (231, 160, 46)
MUTED = (108, 114, 126); GUIDE = (206, 210, 218); PALE = (240, 242, 246)
L, R, T, B = 70, 940, 222, 1498   # area aman

FD = os.path.join(os.path.dirname(os.path.dirname(D)), 'assets', 'fonts') + '/'
def F(name, size): return ImageFont.truetype(FD + name, size)
DISP = lambda s: F('InterDisplay-Bold.otf', s)
BODY = lambda s: F('Inter-Regular.otf', s)
MEDI = lambda s: F('Inter-Medium.otf', s)
MONO = lambda s: ImageFont.truetype(FD + 'DejaVuSansMono.ttf', s)

def ease(x): x = max(0., min(1., x)); return 1 - (1 - x) ** 3
def prog(t, t0, d): return ease((t - t0) / d)
def lerp(a, b, k): return a + (b - a) * k

# ---------------- suara
# Contoh ini membaca potongan suara dari <folder contoh>/vo/lines.json (hasil `studio.py vo-split`).
meta = json.load(open(D + '/' + os.environ.get('VO','vo') + '/lines.json'))
durs = [m['dur'] for m in meta]
GAP = .38
starts = []; t = .45
for d in durs: starts.append(t); t += d + GAP
END = starts[-1] + durs[-1]
TOTAL = END + 1.9
NS = len(meta)
# batas adegan (di tengah jeda); adegan i aktif di [bnd[i], bnd[i+1])
bnd = [0] + [starts[i] - GAP / 2 for i in range(1, NS)] + [TOTAL]

# ---------------- logo fiktif
def make_logo(detail=1.0, icon=False, base=512):
    im = Image.new('RGBA', (base, base), (0, 0, 0, 0)); d = ImageDraw.Draw(im); c = base / 2
    if icon:
        d.ellipse([16, 16, base - 16, base - 16], fill=KOB + (255,))
        pts = [(c + 170 * math.sin(i * math.pi / 5) * (1 if i % 2 == 0 else .45), c - 170 * math.cos(i * math.pi / 5) * (1 if i % 2 == 0 else .45)) for i in range(10)]
        d.polygon(pts, fill=WHITE + (255,))
        return im
    d.ellipse([16, 16, base - 16, base - 16], outline=KOB + (255,), width=30)
    pts = [(c + 150 * math.sin(i * math.pi / 5) * (1 if i % 2 == 0 else .45), c - 150 * math.cos(i * math.pi / 5) * (1 if i % 2 == 0 else .45)) for i in range(10)]
    d.polygon(pts, fill=KOB + (255,))
    if detail > 0.01:
        ly = Image.new('RGBA', (base, base), (0, 0, 0, 0)); e = ImageDraw.Draw(ly)
        e.ellipse([60, 60, base - 60, base - 60], outline=KOB + (255,), width=3)
        for i in range(36):
            a = i * math.pi / 18
            e.line([c + 168 * math.cos(a), c + 168 * math.sin(a), c + 198 * math.cos(a), c + 198 * math.sin(a)], fill=KOB + (255,), width=3)
        e.text((c, c + 215), 'NUANCIER · FIKTIF', font=MONO(15), fill=KOB + (255,), anchor='mm')
        e.text((c, c - 215), 'EST. 2026', font=MONO(15), fill=KOB + (255,), anchor='mm')
        a = ly.split()[3].point(lambda v: int(v * detail)); ly.putalpha(a)
        im = Image.alpha_composite(im, ly)
    return im

LOGO = {}
def logo(size, detail=1.0, icon=False):
    key = (round(detail, 2), icon)
    if key not in LOGO: LOGO[key] = make_logo(detail, icon)
    return LOGO[key].resize((max(2, int(size)), max(2, int(size))), Image.LANCZOS)

def paste_logo(img, cx, cy, size, detail=1.0, icon=False, alpha=1.0):
    lg = logo(size, detail, icon)
    if alpha < 1:
        lg.putalpha(lg.split()[3].point(lambda v: int(v * alpha)))
    img.alpha_composite(lg, (int(cx - lg.width / 2), int(cy - lg.height / 2)))

# ---------------- gambar bantu
BOXES = []
def check(box, tag):
    x0, y0, x1, y1 = box
    if x0 < L - 10 or x1 > R + 1 or y0 < T - 1 or y1 > B + 1:
        raise SystemExit('Di luar area aman: %s %s' % (tag, box))

def text(d, xy, s, font, fill, anchor='la', spacing=0, tag=None, safe=True):
    if spacing:
        x, y = xy
        if anchor[0] == 'r': x -= sum(font.getlength(ch) + spacing for ch in s) - spacing
        elif anchor[0] == 'm': x -= (sum(font.getlength(ch) + spacing for ch in s) - spacing) / 2
        x0 = x
        for ch in s:
            d.text((x, y), ch, font=font, fill=fill, anchor='l' + anchor[1]); x += font.getlength(ch) + spacing
        bb = (x0, y - font.size, x, y + font.size)
        if safe: check((x0, y - font.size * .5, x, y + font.size * .5), tag or s)
        return x
    bb = d.textbbox(xy, s, font=font, anchor=anchor)
    if safe: check(bb, tag or s)
    d.text(xy, s, font=font, fill=fill, anchor=anchor)
    return bb

def dashed(d, p0, p1, fill=GUIDE, dash=14, gap=10, width=2, upto=1.0):
    x0, y0 = p0; x1, y1 = p1; L_ = math.hypot(x1 - x0, y1 - y0) * upto
    ux, uy = (x1 - x0) / max(1, math.hypot(x1 - x0, y1 - y0)), (y1 - y0) / max(1, math.hypot(x1 - x0, y1 - y0))
    s = 0
    while s < L_:
        e = min(s + dash, L_)
        d.line([x0 + ux * s, y0 + uy * s, x0 + ux * e, y0 + uy * e], fill=fill, width=width); s += dash + gap

def dcircle(d, cx, cy, r, fill=GUIDE, n=48, width=2, upto=1.0):
    for i in range(n):
        if i / n > upto: break
        if i % 2: continue
        a0 = i * 2 * math.pi / n; a1 = (i + 1) * 2 * math.pi / n
        d.line([cx + r * math.cos(a0), cy + r * math.sin(a0), cx + r * math.cos(a1), cy + r * math.sin(a1)], fill=fill, width=width)

def wrap(words, font, maxw):
    lines = [[]]; cur = 0; sp = font.getlength(' ')
    for w, col in words:
        wl = font.getlength(w)
        if lines[-1] and cur + sp + wl > maxw: lines.append([]); cur = 0
        cur += (sp if lines[-1] else 0) + wl; lines[-1].append((w, col))
    return lines

def headline(img, spec, t_rel, y0=318, size=92):
    """spec: list (kata, 'k'|'s'|None). Mengembalikan y bawah."""
    f = DISP(size); words = []
    for w in spec:
        words.append((w[0], w[1]))
    lines = wrap(words, f, R - L); lh = int(size * 1.17); sp = f.getlength(' ')
    ly = Image.new('RGBA', (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(ly); under = []
    for li, ln in enumerate(lines):
        x = L; y = y0 + li * lh
        for w, col in ln:
            c = {'k': KOB, 's': SIN, None: TINTA}[col]
            bb = text(d, (x, y), w, f, c + (255,), tag=w)
            if col: under.append((x, y + size + 12, x + f.getlength(w)))
            x += f.getlength(w) + sp
    for (x0, yy, x1) in under:
        k = prog(t_rel, .35, .45)
        d.rectangle([x0, yy, x0 + (x1 - x0) * k, yy + 7], fill=(KOB if True else SIN) + (255,))
    a = prog(t_rel, 0, .35); off = int((1 - a) * 28)
    if a < 1:
        ly.putalpha(ly.split()[3].point(lambda v: int(v * a)))
    img.alpha_composite(ly, (0, off))
    return y0 + len(lines) * lh

def subtext(img, s, y, t_rel, d0=.5):
    ly = Image.new('RGBA', (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(ly)
    f = BODY(44); words = [(w, None) for w in s.split()]
    lines = wrap(words, f, R - L)
    for i, ln in enumerate(lines):
        text(d, (L, y + i * 62), ' '.join(w for w, _ in ln), f, MUTED + (255,))
    a = prog(t_rel, d0, .4); ly.putalpha(ly.split()[3].point(lambda v: int(v * a)))
    img.alpha_composite(ly, (0, int((1 - a) * 18)))

def tag(d, x, y, s, col, font=None, anchor='la', pad=14):
    font = font or MONO(26); bb = d.textbbox((x, y), s, font=font, anchor=anchor)
    box = (bb[0] - pad, bb[1] - 8, bb[2] + pad, bb[3] + 8); check(box, s)
    d.rectangle(box, outline=col, width=3); d.text((x, y), s, font=font, fill=col, anchor=anchor)
    return box

# ---------------- elemen tetap (chrome)
PILLARS = [('NC-01', 'KOBALT', KOB), ('NC-02', 'SINABAR', SIN), ('NC-03', 'OKER', OKER)]
def chrome(img, si, t):
    d = ImageDraw.Draw(img)
    # garis konstruksi
    k = prog(t, .1, .9)
    dashed(d, (505, T), (505, B), upto=k, fill=PALE if False else GUIDE)
    dashed(d, (L, 1040), (R, 1040), upto=k, fill=GUIDE)
    # tanda potong
    for (x, y, sx, sy) in [(L, T, 1, 1), (R, T, -1, 1), (L, B, 1, -1), (R, B, -1, -1)]:
        d.line([x, y, x + 34 * sx, y], fill=TINTA, width=3); d.line([x, y, x, y + 34 * sy], fill=TINTA, width=3)
    # header
    text(d, (L + 12, 262), 'NUANCIER STUDIO', MONO(26), TINTA, spacing=4, tag='hdr')
    text(d, (R - 12, 262), 'NC-01 · LOGO', MONO(26), KOB, anchor='rm', spacing=4, tag='hdr2')
    # strip swatch + penghitung halaman
    for i, (code, nm, col) in enumerate(PILLARS):
        x = L + 12 + i * 100
        d.rectangle([x, 1432, x + 84, 1470], fill=col if i == 0 else col)
        if i != 0: d.rectangle([x + 3, 1435, x + 81, 1467], fill=WHITE); d.rectangle([x + 3, 1435, x + 81, 1467], fill=col) if False else None
    text(d, (L + 12, 1486), 'NC-01 · KOBALT', MONO(22), MUTED, anchor='lm', spacing=3, tag='sw')
    text(d, (R - 12, 1486), '%02d/%02d' % (si + 1, NS), MONO(26), TINTA, anchor='rm', spacing=3, tag='pg')

# ---------------- adegan
VY = 800   # atas area visual
def scene0(img, tr):   # hook
    y = headline(img, [('Logomu', None), ('hilang', 'k'), ('di', None), ('ukuran', None), ('foto', None), ('profil?', None)], tr)
    d = ImageDraw.Draw(img)
    life = durs[0]
    appear = prog(tr, .15, .6)
    shrink = prog(tr, life * .55, life * .42)
    size = lerp(520, 56, shrink) * (.6 + .4 * appear)
    cy = lerp(1130, 1130, shrink); cx = 505
    detail = 1.0 if shrink < .05 else lerp(1.0, 1.0, shrink)
    paste_logo(img, cx, cy, size, 1.0, alpha=appear)
    if shrink > .4:
        d = ImageDraw.Draw(img)
        dcircle(d, cx, cy, 70, fill=SIN, upto=prog(tr, life * .78, .5), width=3)
        a = prog(tr, life * .85, .4)
        if a > .1: tag(d, 505, 1260, '??? · 32 PX', SIN, anchor='ma')

def scene1(img, tr):   # uji tiga detik
    headline(img, [('Uji', None), ('tiga detik', 'k'), ('yang', None), ('jarang', None), ('dilakukan.', None)], tr)
    d = ImageDraw.Draw(img)
    life = durs[1]; n = 3
    seg = life / 3.2
    cnt = min(3, int(tr / seg) + 1)
    num = str(3 - (cnt - 1))
    a = prog(tr % seg, 0, .25)
    d.text((505, 1060 - int((1 - a) * 22)), num, font=DISP(420), fill=KOB, anchor='mm')
    for i in range(3):
        x0 = 195 + i * 250; fill = min(1, max(0, (tr - i * seg) / seg))
        d.rectangle([x0, 1330, x0 + 220, 1342], outline=GUIDE, width=2)
        d.rectangle([x0, 1330, x0 + 220 * fill, 1342], fill=KOB)
    text(d, (505, 1385), 'DETIK', MONO(24), MUTED, anchor='mm', spacing=6)

def scene2(img, tr):   # 01 kecilkan
    y = headline(img, [('01', 'k'), ('Kecilkan', None), ('sampai', None), ('32', 'k'), ('px.', 'k')], tr, size=88)
    subtext(img, 'Bentuk hilang berarti terlalu ramai.', y + 14, tr)
    d = ImageDraw.Draw(img)
    sizes = [256, 128, 64, 32]; gap = 56
    total = sum(sizes) + gap * 3; x = 505 - total / 2; base = 1290
    for i, s in enumerate(sizes):
        a = prog(tr, 1.0 + i * .7, .45)
        cx = x + sum(sizes[:i]) + gap * i + s / 2
        if a > 0:
            paste_logo(img, cx, base - s / 2 - (1 - a) * 20, s, 1.0, alpha=a)
            d = ImageDraw.Draw(img)
            col = SIN if s == 32 else MUTED
            text(d, (cx, base + 40), '%d PX' % s, MONO(24), col, anchor='mm', spacing=3)
    a = prog(tr, 1.0 + 3 * .7 + .2, .5)
    if a > .05:
        d = ImageDraw.Draw(img); cx = x + sum(sizes[:3]) + gap * 3 + 16
        dcircle(d, cx, base - 16, 40, fill=SIN, upto=a, width=3)
    d = ImageDraw.Draw(img); dashed(d, (L + 12, base), (R - 12, base), fill=GUIDE)

def scene3(img, tr):   # 02 hapus detail
    y = headline(img, [('02', 'k'), ('Hapus', None), ('detail', None), ('kecil.', None)], tr, size=88)
    subtext(img, 'Garis tipis dan teks mini lenyap duluan.', y + 14, tr)
    life = durs[3]
    k = prog(tr, life * .38, life * .4)
    detail = 1 - k
    paste_logo(img, 505, 1150, 400, detail)
    d = ImageDraw.Draw(img)
    labs = [('GARIS TIPIS', (255, 1000), (330, 1060)), ('TEKS MINI', (755, 1000), (680, 1128))]
    a = prog(tr, .7, .4) * (1 - k * .9)
    for s, (tx, ty), (px, py) in labs:
        if s == 'TEKS MINI': tx, ty = 800, 1320; px, py = 640, 1296
        else: tx, ty = 210, 1000; px, py = 340, 1030
        col = SIN
        if a > .05:
            dashed(d, (tx, ty + (20 if s == 'GARIS TIPIS' else -20)), (px, py), fill=col, width=3, dash=8, gap=6)
            tag(d, tx, ty, s, col, font=MONO(22), anchor='mm')
    if k > .2:
        a2 = prog(tr, life * .6, .4)
        if a2 > .05: tag(d, 505, 1400, 'LEBIH SEDERHANA = LEBIH TERBACA', KOB, font=MONO(22), anchor='mm')

def scene4(img, tr):   # 03 versi ikon
    y = headline(img, [('03', 'k'), ('Siapkan', None), ('versi', None), ('ikon.', None)], tr, size=88)
    subtext(img, 'Satu simbol untuk ruang sempit.', y + 14, tr)
    sizes = [260, 128, 64, 32]; gap = 56
    total = sum(sizes) + gap * 3; x = 505 - total / 2; base = 1290
    for i, s in enumerate(sizes):
        a = prog(tr, .9 + i * .55, .45); cx = x + sum(sizes[:i]) + gap * i + s / 2
        if a > 0:
            paste_logo(img, cx, base - s / 2 - (1 - a) * 20, s, icon=True, alpha=a)
            d = ImageDraw.Draw(img); text(d, (cx, base + 40), '%d PX' % s, MONO(24), MUTED, anchor='mm', spacing=3)
    a = prog(tr, 3.2, .5)
    if a > .05:
        d = ImageDraw.Draw(img); cx = x + sum(sizes[:3]) + gap * 3 + 16
        # centang
        k = a; p = [(cx - 20, base - 74), (cx - 5, base - 59), (cx + 24, base - 96)]
        pts = [p[0], (lerp(p[0][0], p[1][0], min(1, k * 2)), lerp(p[0][1], p[1][1], min(1, k * 2)))]
        d.line(pts, fill=KOB, width=7)
        if k > .5:
            kk = (k - .5) * 2; d.line([p[1], (lerp(p[1][0], p[2][0], kk), lerp(p[1][1], p[2][1], kk))], fill=KOB, width=7)
    d = ImageDraw.Draw(img); dashed(d, (L + 12, base), (R - 12, base), fill=GUIDE)

def scene5(img, tr):   # 04 uji di ponsel
    y = headline(img, [('04', 'k'), ('Uji', None), ('di', None), ('layar', None), ('ponsel.', None)], tr, size=88)
    d = ImageDraw.Draw(img)
    pw, ph = 280, 500; px0 = 230; py0 = 740
    a = prog(tr, .5, .6)
    off = int((1 - a) * 40)
    d.rounded_rectangle([px0, py0 + off, px0 + pw, py0 + ph + off], radius=42, outline=TINTA, width=5, fill=WHITE)
    paste_logo(img, px0 + 56, py0 + 70 + off, 48, 1.0)
    d = ImageDraw.Draw(img)
    d.rectangle([px0 + 90, py0 + 58 + off, px0 + 210, py0 + 70 + off], fill=PALE)
    d.rectangle([px0 + 90, py0 + 78 + off, px0 + 170, py0 + 86 + off], fill=PALE)
    for i in range(3):
        d.rectangle([px0 + 24, py0 + 130 + i * 118 + off, px0 + pw - 24, py0 + 220 + i * 118 + off], fill=PALE)
    z = prog(tr, 1.6, .6)
    if z > .02:
        cx0, cy0 = px0 + 56, py0 + 70 + off
        dcircle(d, cx0, cy0, 40, fill=KOB, width=3, upto=z)
        dashed(d, (cx0 + 40, cy0), (655, 940), fill=KOB, width=3, dash=10, gap=7, upto=z)
        zs = 220 * z
        if zs > 20:
            d.ellipse([740 - zs / 2 - 10, 940 - zs / 2 - 10, 740 + zs / 2 + 10, 940 + zs / 2 + 10], outline=KOB, width=3, fill=WHITE)
            paste_logo(img, 740, 940, zs, 1.0)
            d = ImageDraw.Draw(img)
    a2 = prog(tr, 2.6, .5)
    if a2 > .05:
        tag(d, 740, 1130, 'TERBACA?', KOB, anchor='mm')
    a3 = prog(tr, 3.4, .5)
    if a3 > .05:
        text(d, (L + 12, 1290), 'Di sini pelangganmu', BODY(40), MUTED, tag='ln1')
        text(d, (L + 12, 1342), 'paling sering melihatnya.', BODY(40), MUTED, tag='ln2')

def scene6(img, tr):   # penutup
    y = headline(img, [('Simpan,', None), ('lalu', None), ('uji', None), ('logomu', 'k'), ('hari', None), ('ini.', None)], tr, size=88)
    d = ImageDraw.Draw(img)
    cw = 262; gap = 24; x0 = 505 - (cw * 3 + gap * 2) / 2
    for i, (code, nm, col) in enumerate(PILLARS):
        a = prog(tr, .5 + i * .3, .55); xo = x0 + i * (cw + gap); yo = 840 + int((1 - a) * 60)
        if a > .02:
            ly = Image.new('RGBA', (W, H), (0, 0, 0, 0)); e = ImageDraw.Draw(ly)
            e.rectangle([xo, yo, xo + cw, yo + 330], fill=col + (255,))
            e.rectangle([xo, yo + 330, xo + cw, yo + 400], fill=WHITE + (255,), outline=TINTA + (255,), width=3)
            tc = TINTA if col == OKER else WHITE
            e.text((xo + 20, yo + 22), code, font=MONO(24), fill=tc + (255,), anchor='la')
            e.text((xo + 20, yo + 365), nm, font=MONO(24), fill=TINTA + (255,), anchor='lm')
            check((xo, yo, xo + cw, yo + 400), 'swatch')
            ly.putalpha(ly.split()[3].point(lambda v: int(v * a))); img.alpha_composite(ly)
    a = prog(tr, 1.9, .6)
    if a > .02:
        ly = Image.new('RGBA', (W, H), (0, 0, 0, 0)); e = ImageDraw.Draw(ly)
        e.text((505, 1340), 'Nuancier Studio', font=DISP(72), fill=TINTA + (255,), anchor='mm')
        check((505 - 260, 1300, 505 + 260, 1380), 'wordmark')
        ly.putalpha(ly.split()[3].point(lambda v: int(v * a))); img.alpha_composite(ly, (0, int((1 - a) * 16)))
    a = prog(tr, 2.2, .5)
    if a > .02:
        ly = Image.new('RGBA', (W, H), (0, 0, 0, 0)); e = ImageDraw.Draw(ly)
        text(e, (505, 1392), 'LOGO · IDENTITAS MEREK · BISNIS KREATIF', MONO(20), MUTED + (255,), anchor='mm', spacing=3)
        ly.putalpha(ly.split()[3].point(lambda v: int(v * a))); img.alpha_composite(ly)

SCENES = [scene0, scene1, scene2, scene3, scene4, scene5, scene6]

def scene_index(t):
    for i in range(NS):
        if bnd[i] <= t < bnd[i + 1]: return i
    return NS - 1

def wipe(img, t):
    for i in range(1, NS):
        b = bnd[i]; hw = GAP / 2
        if b - hw <= t <= b + hw:
            u = (t - (b - hw)) / (2 * hw)
            d = ImageDraw.Draw(img)
            if u < .5:
                k = ease(u * 2); d.rectangle([0, 0, W * k, H], fill=KOB)
            else:
                k = ease((u - .5) * 2); d.rectangle([W * k, 0, W, H], fill=KOB)
            return

def frame(t):
    img = Image.new('RGBA', (W, H), WHITE + (255,))
    si = scene_index(t)
    tr = t - starts[si] if si > 0 else t - starts[0]
    # perbaiki: anim adegan mengikuti waktu relatif ke awal baris
    chrome(img, si, t - bnd[si] if si > 0 else t)
    SCENES[si](img, max(0, tr))
    wipe(img, t)
    if t > END + .3 and si == NS - 1: pass
    return img.convert('RGB')

# ---------------- audio
rng = np.random.default_rng(7)
def click(freq=1700, dur=.05, gain=.35):
    n = int(SR * dur); tt = np.arange(n) / SR
    env = np.exp(-tt * 90)
    return (np.sin(2 * np.pi * freq * tt) * .6 + rng.standard_normal(n) * .4) * env * gain
def whoosh(dur=GAP, gain=.18):
    n = int(SR * dur); tt = np.arange(n) / SR
    x = rng.standard_normal(n); k = 60
    x = np.convolve(x, np.ones(k) / k, 'same')
    return x * np.sin(np.pi * tt / dur) ** 2 * gain * 4

def build_audio(path):
    n = int(SR * TOTAL); out = np.zeros(n); vo = np.zeros(n)
    for m, s in zip(meta, starts):
        place(vo, load_wav(m['file']), s)
    vo = normalize(vo, .8)
    fx = np.zeros(n)
    for i in range(1, NS):
        place(fx, whoosh(), bnd[i] - GAP / 2)
        place(fx, click(2100, .05, .3), bnd[i] + .02)
    # klik kecil untuk elemen yang muncul
    for tt in [starts[2] + 1.0, starts[2] + 1.7, starts[2] + 2.4, starts[2] + 3.1, starts[4] + .9, starts[4] + 1.45, starts[4] + 2.0, starts[4] + 2.55]:
        place(fx, click(1500, .04, .22), tt)
    place(fx, click(1200, .09, .3), starts[6] + 2.2)
    out = vo + fx
    out = np.clip(out, -1, 1)
    save_wav(path, out)

if __name__ == '__main__':
    mode = sys.argv[1] if len(sys.argv) > 1 else 'full'
    if mode == 'still':
        for t in [float(x) for x in sys.argv[2:]]:
            frame(t).save(D + '/still_%05.2f.png' % t)
        print('ok')
        sys.exit()
    build_audio(D + '/mix.wav')
    out = D + '/' + os.environ.get('OUT','nuancier_motion_luna') + '.mp4'
    with VideoWriter(out, audio=D + '/mix.wav') as vw:
        for i in range(int(TOTAL * FPS)):
            vw.write(frame(i / FPS))
    print('done', out, TOTAL)
