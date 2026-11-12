"""CONTOH (disetujui Jers 12 Nov 2026): Sonya / Nuancier - 'Level Uji Logo'. Pelajari TEKNIKNYA, jangan salin adegannya.
Jalankan dari folder kerja yang berisi words.json (transkrip berwaktu), lines.txt (naskah, satu kalimat per baris), vo.wav.

Bahasa gerak: kanvas halus 2x (gerak.py Nabila), caption karaoke dari waktu kata asli,
setiap kalimat divisualkan (pola Bagas), karakter pixel Herman & Sonya (NEAREST, skala sama)."""
import sys, json, math, random, wave
import os
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(ROOT, 'toolkit'))
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
import gerak as G
import studio as ST
from gerak import seg, out_cubic, out_expo, out_back, in_out, lerp, cl, rgba, P, text, rrect, tw

S = G.S; W, H = 1080, 1920; FPS = 30
# Zona aman Instagram Reels: atas 220, bawah 420, kanan 140 -> isi x 140..940 (tengah 540)
G.X0, G.X1, G.TOPY, G.CAPY, G.BARY = 140, 940, 250, 1388, 1462
G.BOLD = 'Poppins-Bold.ttf'; G.MED = 'Poppins-Medium.ttf'
F = G.font; B = 'Poppins-Bold.ttf'; M = 'Poppins-Medium.ttf'
# Palet Nuancier A3 (dikunci Jers 12 Nov 2026): Tinta, Kertas, Plum (penuh), Sinabar (peringatan), Merah Muda (sorot)
NAV = '#15171C'; NAV2 = '#2A2D36'; PAPER = '#F3F1EC'; INK = '#15171C'; WHITE = '#FFFFFF'
SIN = '#E2472B'; OKR = '#F7B9AE'; KOB = '#4A2545'; LIGHT = '#B9BECB'; GREY = '#8A8F9C'
SPR = os.path.join(ROOT, 'assets', 'sprites') + '/'
IC = os.path.join(HERE, 'ic') + '/'
LEAD = .45

# ---------------- waktu kata ----------------
WORDS = json.load(open('words.json'))['words']
WORDS = [dict(w=w['text'], t0=w['start'] + LEAD, t1=w['end'] + LEAD) for w in WORDS if w.get('type', 'word') == 'word']
LINES = [l for l in open('lines.txt').read().split('\n') if l.strip()]
SENT = []; k = 0
for l in LINES:
    n = len(l.split()); SENT.append(list(range(k, k + n))); k += n
assert k == len(WORDS), (k, len(WORDS))
def wt(i, j): return WORDS[SENT[i][j]]['t0']
SC = [wt(i, 0) - .18 for i in range(len(SENT))]; SC[0] = 0
TOTAL = WORDS[-1]['t1'] + 1.6
SC.append(TOTAL)

# frasa caption: maks 3 kata, putus di koma/titik
PHR = []
for idx in SENT:
    cur = []
    for j in idx:
        cur.append(j)
        if len(cur) == 3 or WORDS[j]['w'][-1] in ',.?!':
            PHR.append(cur); cur = []
    if cur: PHR.append(cur)

# ---------------- aset ----------------
_SP = {}
def sprite(name, k=1):
    key = (name, k)
    if key not in _SP:
        im = Image.open(SPR + name + '.png').convert('RGBA'); im = im.crop(im.getbbox())
        _SP[key] = im.resize((im.width * S * k, im.height * S * k), Image.NEAREST)
    return _SP[key]
def spr(fr, name, cx, foot, a=1., dy=0):
    im = sprite(name); old = fr.kind; fr.kind = 'tokoh'
    fr.put(im, a, (int(cx * S - im.width / 2), int((foot + dy) * S - im.height))); fr.kind = old

_IM = {}
def icon(name):
    if name not in _IM: _IM[name] = Image.open(IC + name + '.png').convert('RGBA')
    return _IM[name]
def put_icon(fr, name, cx, cy, size, a=1., rot=0):
    im = icon(name).resize((int(size * S), int(size * S)), Image.LANCZOS)
    if rot: im = im.rotate(rot, expand=True, resample=Image.BICUBIC)
    fr.put(im, a, (cx * S - im.width / 2, cy * S - im.height / 2))

def hx(h): h = h.lstrip('#'); return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))

# ---- logo fiktif (digambar bertahap supaya bisa dibongkar) ----
def logo_detail(px, rays=1., waves=1., txt=1., ring=1., sun=1., ray_spread=0., wave_drop=0., txt_drop=0.):
    """px = ukuran sisi di kanvas 2x."""
    im = Image.new('RGBA', (px, px), (0, 0, 0, 0)); d = ImageDraw.Draw(im); c = px / 2; s = px
    ink = hx(INK)
    if ring > 0:
        a = int(255 * ring)
        d.ellipse([s * .04, s * .04, s * .96, s * .96], outline=ink + (a,), width=max(2, int(s * .018)))
        d.ellipse([s * .09, s * .09, s * .91, s * .91], outline=ink + (a,), width=max(1, int(s * .006)))
    if rays > 0:
        for i in range(13):
            an = math.pi + math.pi * i / 12; r1 = s * (.2 + ray_spread * .3); r2 = s * (.33 + ray_spread * .5)
            d.line([c + r1 * math.cos(an), c * 1.02 + r1 * math.sin(an), c + r2 * math.cos(an), c * 1.02 + r2 * math.sin(an)],
                   fill=ink + (int(255 * rays),), width=max(1, int(s * .007)))
    if sun > 0:
        d.pieslice([c - s * .16, c * 1.02 - s * .16, c + s * .16, c * 1.02 + s * .16], 180, 360, fill=hx(SIN) + (int(255 * sun),))
    if waves > 0:
        for j in range(4):
            y = c * 1.06 + j * s * .045 + wave_drop * s * .4
            pts = [(c - s * .3 + x, y + math.sin(x / (s * .03)) * s * .008) for x in range(0, int(s * .6), max(2, s // 300))]
            d.line(pts, fill=hx(KOB) + (int(255 * waves),), width=max(1, int(s * .006)))
    if txt > 0:
        f = G.ImageFont.truetype(G.os.path.join(G.FD, M), max(6, int(s * .06)))
        t = 'KEDAI SENJA'; w = d.textlength(t, font=f); y = s * .71 + txt_drop * s * .4
        d.text((c - w / 2, y), t, font=f, fill=ink + (int(255 * txt),))
        f2 = G.ImageFont.truetype(G.os.path.join(G.FD, 'Poppins-Regular.ttf'), max(5, int(s * .03)))
        t = 'kopi · teh · roti · sejak hari ini'; w = d.textlength(t, font=f2)
        d.text((c - w / 2, y + s * .085), t, font=f2, fill=hx(GREY) + (int(255 * txt),))
    return im

def logo_simple(px, box=1., sun=1., bar=1., rays=0.):
    im = Image.new('RGBA', (px, px), (0, 0, 0, 0)); d = ImageDraw.Draw(im); c = px / 2; s = px
    if box > 0:
        k = out_back(box); m = s * (1 - k) / 2
        d.rounded_rectangle([m, m, s - m, s - m], radius=s * .22 * k, fill=hx(INK))
    if rays > 0:
        for i in range(9):
            an = math.pi + math.pi * (i + .5) / 9
            d.line([c + s * .36 * math.cos(an), s * .52 + s * .36 * math.sin(an), c + s * .43 * math.cos(an), s * .52 + s * .43 * math.sin(an)],
                   fill=hx(OKR) + (int(255 * rays),), width=max(1, int(s * .012)))
    if sun > 0:
        r = s * .32 * out_back(sun)
        d.pieslice([c - r, s * .52 - r, c + r, s * .52 + r], 180, 360, fill=hx(SIN))
    if bar > 0:
        d.rectangle([s * .18, s * .58, s * .18 + s * .64 * out_cubic(bar), s * .70], fill=hx(OKR))
    return im

def down(im, n, bg=(255, 255, 255)):
    b = Image.new('RGBA', im.size, bg + (255,)); b.alpha_composite(im)
    return b.convert('RGB').resize((n, n), Image.LANCZOS)

BIG_DETAIL = logo_detail(1024)
PIX16 = down(BIG_DETAIL, 16)           # versi 16 px yang sesungguhnya
SIMPLE = logo_simple(1024)

def put_img(fr, im, x, y, a=1., kind=None):
    old = fr.kind
    if kind: fr.kind = kind
    fr.put(im, a, (int(x * S), int(y * S))); fr.kind = old

def pixel_grid(fr, src, x, y, size, p, gap=2, wave=True, a=1.):
    """src: gambar RGB n x n. Sel muncul bergelombang diagonal (p 0..1)."""
    n = src.width; cell = size / n; px = src.load()
    L = Image.new('RGBA', (int(size * S), int(size * S)), (0, 0, 0, 0)); d = ImageDraw.Draw(L)
    for j in range(n):
        for i in range(n):
            q = cl((p * (2 * n + 6) - (i + j)) / 6) if wave else 1
            if q <= 0: continue
            k = out_back(q); c = cell * S; m = (c - gap * S) * (1 - k) / 2
            x0 = i * c + m; y0 = j * c + m
            d.rectangle([x0, y0, x0 + c - gap * S - 2 * m, y0 + c - gap * S - 2 * m], fill=px[i, j] + (255,))
    put_img(fr, L, x, y, a)

def cursor(fr, x, y, a=1.):
    L = Image.new('RGBA', (60 * S, 70 * S), (0, 0, 0, 0)); d = ImageDraw.Draw(L)
    pts = [(4, 4), (4, 52), (17, 40), (27, 62), (36, 58), (26, 37), (44, 37)]
    d.polygon([(px * S, py * S) for px, py in pts], fill=hx(INK) + (255,), outline=(255, 255, 255, 255))
    d.line([(px * S, py * S) for px, py in pts + [pts[0]]], fill=(255, 255, 255, 255), width=3 * S)
    fr.put(L, a, (int(x * S - 4 * S), int(y * S - 4 * S)), rec=False)

def chip(fr, cx, cy, t, bg, fg, size=28, a=1., anchor='m'):
    f = F(B, size); w = tw(t, f) + 44; h = size * 1.9
    x0 = cx - w / 2 if anchor == 'm' else cx
    rrect(fr, (x0, cy - h / 2, x0 + w, cy + h / 2), h / 2, bg, a)
    text(fr, x0 + w / 2, cy + 1, t, f, fg, a, anchor='mm')
    return w

def heart_img(n, col, a):
    big = n * 4; L = Image.new('RGBA', (big, big), (0, 0, 0, 0)); d = ImageDraw.Draw(L); c = hx(col) + (int(255 * a),)
    r = big * .27
    d.ellipse([big * .04, big * .08, big * .04 + 2 * r, big * .08 + 2 * r], fill=c)
    d.ellipse([big * .96 - 2 * r, big * .08, big * .96, big * .08 + 2 * r], fill=c)
    d.polygon([(big * .055, big * .42), (big * .945, big * .42), (big * .5, big * .93)], fill=c)
    return L.resize((n, n), Image.LANCZOS)

# ---------------- krom (game HUD) ----------------
KIND = ['navy']
def krom(fr, t, level, hearts, dark, hpop=-1):
    old = fr.kind; fr.kind = 'krom'
    bg, fg = (WHITE, INK) if dark else (INK, WHITE)
    chip(fr, G.X0, G.TOPY + 22, 'LEVEL %d' % level, bg, fg, 22, anchor='l')
    for i in range(3):
        on = i < hearts; sz = 34
        k = 1 + .35 * math.sin(math.pi * cl((t - hpop) / .35)) if (hpop >= 0 and i == hearts - 1 and 0 < t - hpop < .35) else 1
        im = heart_img(int(sz * k * S), (WHITE if KIND[0] == 'sin' else SIN) if on else ('#FFFFFF' if dark else INK), 1. if on else .25)
        fr.put(im, 1., (int((G.X1 - 34 - i * 46) * S - im.width / 2 + 17 * S), int((G.TOPY + 22) * S - im.height / 2)))
    mute = '#FFFFFF' if dark else INK
    rrect(fr, (G.X0, G.BARY, G.X1, G.BARY + 6), 3, mute, .22)
    rrect(fr, (G.X0, G.BARY, G.X0 + max(6, (G.X1 - G.X0) * cl(t / TOTAL)), G.BARY + 6), 3, OKR)
    fr.kind = old

def capt(fr, t, dark):
    for ph in PHR:
        a, b = WORDS[ph[0]]['t0'] - .08, WORDS[ph[-1]]['t1'] + .12
        nxt = [p for p in PHR if WORDS[p[0]]['t0'] > WORDS[ph[0]]['t0']]
        if nxt: b = max(b, min(WORDS[nxt[0][0]]['t0'] - .08, b + .5))
        if a <= t < b:
            act = max([k for k, j in enumerate(ph) if WORDS[j]['t0'] - .03 <= t] or [0])
            pal = dict(pill_bg=WHITE if dark else INK, pill_fg=INK if dark else WHITE, pill_hl=SIN if dark else OKR, ink=INK, paper=WHITE, acc=OKR)
            G.caption(fr, [WORDS[j]['w'] for j in ph], act, a, t, pal)
            return

def judul(fr, x, y, baris, t, t0, size, head, acc2, hl=(), anchor='ma', step=.09):
    return G.judul(fr, x, y, baris, t, t0, F(B, size), dict(head=head, acc2=acc2), hl=hl, step=step, anchor=anchor)

def stiker(fr, cx, cy, t, t0, s, bg, fg, rot=-7, size=32):
    G.stiker(fr, cx, cy, t, t0, s, dict(acc=bg, ink=fg), rot=rot, bg=bg, fg=fg, size=size)

def card(fr, box, col=WHITE, r=28, a=1., shadow=18):
    rrect(fr, box, r, col, a, shadow=shadow)

def bgframe(kind):
    if kind == 'navy': return G.Frame(NAV, '#24272F')
    if kind == 'paper': return G.Frame(PAPER, '#DCD8CF')
    if kind == 'sin': return G.Frame(SIN, '#EE6A50')
    if kind == 'kob': return G.Frame(KOB, '#5A3355')
    return G.Frame(kind)

# ---------------- adegan ----------------
def s1(t):  # Logo kamu, lolos uji enam belas piksel?
    fr = bgframe('navy'); t0 = SC[0]
    judul(fr, 540, 360, ['Logo kamu', 'lolos uji', '16 piksel?'], t, .1, 104, WHITE, OKR, hl=('16', 'piksel?'), step=.12)
    # kisi 16x16 kosong digambar bergelombang, lalu terisi titik-titik
    p = seg(t, wt(0, 4) - .2, wt(0, 6) + .5)
    gx, gy, gs = 214, 840, 400
    if p > 0:
        L = Image.new('RGBA', (gs * S, gs * S), (0, 0, 0, 0)); d = ImageDraw.Draw(L); c = gs / 16 * S
        for i in range(17):
            q = cl(p * 2 - i / 16)
            if q <= 0: continue
            d.line([(i * c, 0), (i * c, gs * S * out_cubic(q))], fill=hx(LIGHT) + (150,), width=2 * S)
            d.line([(0, i * c), (gs * S * out_cubic(q), i * c)], fill=hx(LIGHT) + (150,), width=2 * S)
        put_img(fr, L, gx, gy)
        pf = seg(t, wt(0, 6) + .2, wt(0, 6) + 1.4)
        if pf > 0:
            pixel_grid(fr, Image.new('RGB', (16, 16), hx(NAV2)), gx, gy, gs, pf * .4, gap=6)
        text(fr, gx + gs / 2, gy + gs + 22, '16 x 16 piksel', F(M, 26), LIGHT, out_cubic(p), anchor='ma')
    # Sonya masuk dari kanan
    q = out_cubic(seg(t, .6, 1.5)); bob = -abs(math.sin(t * 5)) * 8 if t > 1.5 else 0
    frm = 'sonya_w_%d' % (int(t * 8) % 4) if q < 1 else 'sonya_h_0'
    spr(fr, frm, lerp(1100, 800, q), 1300, dy=bob * 0)
    return fr, 'navy', 1, 3

def billboard(fr, t, zoom=0., appear=1.):
    """papan baliho dengan logo fiktif; zoom 0..1 mendorong kamera ke logo."""
    k = out_back(appear) if appear < 1 else 1
    if k <= 0: return
    cw = lerp(540, 800, out_cubic(zoom)); cx = lerp(590, 540, out_cubic(zoom)); cy = lerp(610, 690, out_cubic(zoom))
    yoff = (1 - k) * 260
    if zoom < .99:
        for px in (cx - cw * .3, cx + cw * .3):
            rrect(fr, (px - 12, cy + cw / 2 - 10 + yoff, px + 12, 1300), 6, '#3A3F4C', 1 - zoom)
    card(fr, (cx - cw / 2, cy - cw / 2 + yoff, cx + cw / 2, cy + cw / 2 + yoff), WHITE, 26, cl(appear * 3))
    lg = logo_detail(int(cw * .9 * S)); fr.put(lg, cl(appear * 3), (int((cx - cw * .45) * S), int((cy - cw * .46 + yoff) * S)))
    text(fr, cx + cw / 2 - 24, cy + cw / 2 - 22 + yoff, 'LOGO FIKTIF', F(M, 18), GREY, cl(appear * 3), anchor='rs')
    return cx, cy, cw

def s2(t):  # Di baliho, logo ini kelihatan aman.
    fr = bgframe('paper'); t0 = SC[1]
    billboard(fr, t, 0, seg(t, t0, t0 + .55))
    q = out_cubic(seg(t, t0 + .1, t0 + 1.0))
    frm = 'herman_w_%d' % (int(t * 8) % 4) if q < 1 else 'herman_h_0'
    spr(fr, frm, lerp(-120, 222, q), 1300)
    stiker(fr, 770, 1010, t, wt(1, 5) - .05, '✓ aman', OKR, INK, rot=-8, size=40)
    return fr, 'paper', 1, 3

def s3(t):  # Semua garis tipisnya terlihat jelas.
    fr = bgframe('paper'); t0 = SC[2]
    z = seg(t, t0, t0 + .7)
    r = billboard(fr, t, z, 1)
    cx, cy, cw = r
    # sorotan detail
    ox, oy, s = cx - cw * .45, cy - cw * .46, cw * .9
    c = s / 2
    feats = [  # (titik di logo, label, waktu)
        ((ox + c + s * .27 * math.cos(math.radians(225)), oy + c * 1.02 + s * .27 * math.sin(math.radians(225))), 'garis tipis', wt(2, 1)),
        ((ox + c + s * .2, oy + c * 1.06 + s * .07), 'gelombang tipis', wt(2, 3)),
        ((ox + c, oy + s * .8), 'tulisan kecil', wt(2, 4)),
    ]
    slots = [(300, 1180), (580, 1180), (820, 1180)]
    for (pt, lab, tt), (lx, ly) in zip(feats, slots):
        p = seg(t, tt - .1, tt + .35)
        if p <= 0: continue
        rr = 58 * out_back(p)
        fr.draw().ellipse(P(pt[0] - rr, pt[1] - rr, pt[0] + rr, pt[1] + rr), outline=rgba(SIN), width=int(6 * S))
    for (pt, lab, tt), (lx, ly) in zip(feats, [(250, 1170), (830, 1170), (540, 1240)]):
        p = seg(t, tt - .1, tt + .35)
        if p <= 0: continue
        w = tw(lab, F(B, 26)) + 44; lx = min(max(lx, G.X0 + w / 2), G.X1 - w / 2)
        G.coret  # (tidak dipakai)
        fr.draw().line(P(pt[0], pt[1] + 58, lx, ly - 26), fill=rgba(SIN, .8 * p), width=int(3 * S))
        chip(fr, lx, ly + 8 * (1 - out_cubic(p)), lab, INK, WHITE, 26, cl(p * 2))
    return fr, 'paper', 1, 3

BROWSER = (160, 360, 920, 900)
FAV = (214, 404, 32)  # x, y, ukuran favicon di tab
def browser(fr, a=1.):
    x0, y0, x1, y1 = BROWSER
    card(fr, BROWSER, WHITE, 22, a)
    rrect(fr, (x0, y0, x1, y0 + 92), 22, '#E4E6EE', a)
    rrect(fr, (x0, y0 + 60, x1, y0 + 92), 0, '#E4E6EE', a)
    for i, col in enumerate(('#FF6159', '#FFBD2E', '#28C941')):
        fr.draw().ellipse(P(x0 + 30 + i * 26 - 8, y0 + 26 - 8, x0 + 30 + i * 26 + 8, y0 + 26 + 8), fill=rgba(col, a))
    rrect(fr, (x0 + 120 - 30, y0 + 40, x0 + 420, y0 + 92), 14, WHITE, a)
    text(fr, FAV[0] + 46, FAV[1] + 16, 'Kedai Senja', F(M, 24), INK, a, anchor='lm')
    rrect(fr, (x0 + 30, y0 + 112, x1 - 30, y0 + 160), 24, '#EEF0F5', a)
    text(fr, x0 + 60, y0 + 136, 'kedaisenja.contoh', F(M, 22), GREY, a, anchor='lm')
    for i, w in enumerate((.82, .64, .74, .5)):
        rrect(fr, (x0 + 40, y0 + 210 + i * 64, x0 + 40 + (x1 - x0 - 80) * w, y0 + 240 + i * 64), 12, '#EEF0F5', a)

def s4(t):  # Tapi coba kecilkan, jadi ikon di tab browser.
    fr = bgframe('paper'); t0 = SC[3]
    browser(fr, cl(seg(t, t0, t0 + .3) * 1.5))
    p = in_out(seg(t, wt(3, 2) - .1, wt(3, 5) + .1))
    size = lerp(360, FAV[2], p); x = lerp(540 - 180, FAV[0], p); y = lerp(450, FAV[1], p)
    lg = BIG_DETAIL if p < .97 else None
    if p < .97:
        im = Image.new('RGBA', (int(size * S), int(size * S)), (255, 255, 255, 0))
        dd = ImageDraw.Draw(im); dd.ellipse([0, 0, im.width - 1, im.height - 1], fill=(255, 255, 255, 255))
        im.alpha_composite(BIG_DETAIL.resize(im.size, Image.LANCZOS)); put_img(fr, im, x, y)
    else:
        put_img(fr, PIX16.resize((FAV[2] * S, FAV[2] * S), Image.LANCZOS).convert('RGBA'), FAV[0], FAV[1])
    # kursor menunjuk tab
    q = out_cubic(seg(t, wt(3, 6) - .3, wt(3, 7) + .1))
    if q > 0:
        cursor(fr, lerp(700, FAV[0] + 26, q), lerp(1100, FAV[1] + 26, q))
    pr = seg(t, wt(3, 7), wt(3, 7) + .4)
    if pr > 0:
        rr = 44 * out_back(pr)
        fr.draw().ellipse(P(FAV[0] + 16 - rr, FAV[1] + 16 - rr, FAV[0] + 16 + rr, FAV[1] + 16 + rr), outline=rgba(SIN), width=int(5 * S))
    judul(fr, 540, 1000, ['Kecilkan.'], t, wt(3, 2) - .1, 96, INK, SIN)
    text(fr, 540, 1130, 'favicon: 16 x 16 piksel', F(M, 30), GREY, out_cubic(seg(t, wt(3, 4), wt(3, 4) + .4)), anchor='ma')
    return fr, 'paper', 2, 3

def s5(t):  # Enam belas kali enam belas piksel. Hancur.
    fr = bgframe('sin'); t0 = SC[4]
    sh = math.sin(t * 70) * 14 * (1 - seg(t, wt(4, 6), wt(4, 6) + .45)) if t > wt(4, 6) else 0
    gx, gy, gs = 220 + sh, 330, 640
    card(fr, (gx - 16, gy - 16, gx + gs + 16, gy + gs + 16), WHITE, 20, 1, shadow=24)
    pixel_grid(fr, PIX16, gx, gy, gs, seg(t, t0, wt(4, 5) + .2), gap=2)
    chip(fr, 540, 1060, '16 x 16 = 256 piksel', INK, WHITE, 30, out_cubic(seg(t, wt(4, 2), wt(4, 2) + .3)))
    stiker(fr, 800, 930, t, wt(4, 6) - .02, '× hancur', INK, WHITE, rot=-9, size=46)
    hearts = 3 if t < wt(4, 6) else 1
    return fr, 'sin', 2, hearts

def s6(t):  # Garis tipis dan tulisan kecil, berubah jadi noda.
    fr = bgframe('sin'); t0 = SC[5]
    a = out_cubic(seg(t, t0, t0 + .35))
    # kiri: potongan asli; kanan: potongan 16 px
    crop = (0, 0, 1024, 1024)
    L = BIG_DETAIL.crop(crop); bgl = Image.new('RGBA', L.size, (255, 255, 255, 255)); bgl.alpha_composite(L)
    for i, (x, im, lab) in enumerate(((150, bgl.convert('RGB').resize((340 * S, 340 * S), Image.LANCZOS), 'asli'),
                                      (590, PIX16.resize((340 * S, 340 * S), Image.NEAREST), '16 px'))):
        ai = out_cubic(seg(t, t0 + i * .25, t0 + i * .25 + .4))
        card(fr, (x - 12, 360 - 12 + 30 * (1 - ai), x + 352, 712 + 30 * (1 - ai)), WHITE, 18, ai)
        fr.put(im.convert('RGBA'), ai, (int(x * S), int((360 + 30 * (1 - ai)) * S)))
        text(fr, x + 170, 750, lab, F(B, 28), WHITE, ai, anchor='ma')
    pa = out_cubic(seg(t, t0 + .3, t0 + .7))
    if pa > 0:
        d = fr.draw(); y = 530; x0, x1 = 510, lerp(510, 572, pa)
        d.line(P(x0, y, x1, y), fill=rgba(WHITE), width=int(8 * S))
        d.polygon([tuple(P(x1 + 6, y)), tuple(P(x1 - 14, y - 16)), tuple(P(x1 - 14, y + 16))], fill=rgba(WHITE))
    # label masalah lalu dicoret
    for k, (lab, tt) in enumerate((('garis tipis', wt(5, 0)), ('tulisan kecil', wt(5, 3)))):
        p = seg(t, tt - .05, tt + .3)
        if p <= 0: continue
        y = 860 + k * 84; w = chip(fr, 540, y, lab, INK, WHITE, 30, out_cubic(p))
        G.coret(fr, 540 - w / 2 - 10, y + 2, 540 + w / 2 + 10, seg(t, wt(5, 5), wt(5, 5) + .35), WHITE, 6)
    judul(fr, 540, 1060, ['= noda.'], t, wt(5, 7) - .05, 110, WHITE, INK, hl=('noda.',))
    return fr, 'sin', 2, 1

def s7(t):  # Solusinya, sederhanakan jadi satu bentuk inti.
    fr = bgframe('paper'); t0 = SC[6]
    ps = seg(t, wt(6, 1), wt(6, 1) + .8)      # bongkar detail
    pb = seg(t, wt(6, 3) - .1, wt(6, 5) + .1)  # susun bentuk inti
    size = 560
    if pb < 1:
        lg = logo_detail(size * S, rays=1 - ps, waves=1 - ps, txt=1 - ps, ring=1 - ps, sun=1 - pb,
                         ray_spread=out_cubic(ps), wave_drop=out_cubic(ps), txt_drop=out_cubic(ps))
        put_img(fr, lg, 540 - size / 2, 300)
    if pb > 0:
        sl = logo_simple(size * S, box=cl(pb * 2.2), sun=cl(pb * 2.2 - .5), bar=cl(pb * 2.2 - 1.1))
        put_img(fr, sl, 540 - size / 2, 300)
    judul(fr, 540, 950, ['Sederhanakan.'], t, wt(6, 1) - .1, 72, GREY, SIN)
    judul(fr, 540, 1050, ['Satu bentuk inti.'], t, wt(6, 3) - .05, 92, INK, SIN, hl=('inti.',))
    return fr, 'paper', 3, 1

def s8(t):  # Detail boleh ada, tapi cuma bonus di ukuran besar.
    fr = bgframe('kob'); t0 = SC[7]
    a = out_cubic(seg(t, t0, t0 + .35))
    card(fr, (150, 330, 530, 710), WHITE, 26, a)
    bonus = seg(t, wt(7, 0), wt(7, 2))
    put_img(fr, logo_simple(340 * S, rays=bonus), 170, 350, a)
    text(fr, 340, 740, '512 px', F(B, 30), WHITE, a, anchor='ma')
    stiker(fr, 440, 330, t, wt(7, 5) - .05, '+ bonus', OKR, INK, rot=8, size=34)
    for i, n in enumerate((64, 32, 16)):
        y = 330 + i * 140; p = out_cubic(seg(t, wt(7, 3) + i * .22, wt(7, 3) + i * .22 + .4))
        if p <= 0: continue
        card(fr, (600, y, 720, y + 120), WHITE, 18, p, shadow=10)
        im = down(SIMPLE, n).resize((100 * S, 100 * S), Image.NEAREST).convert('RGBA')
        put_img(fr, im, 610, y + 10, p)
        text(fr, 750, y + 60, '%d px' % n, F(B, 30), WHITE, p, anchor='lm')
        put_icon(fr, 'check_cFFFFFF', 900, y + 60, 40, p)
    judul(fr, 540, 900, ['Detail = bonus', 'di ukuran besar.'], t, wt(7, 0), 76, WHITE, OKR, hl=('bonus',), step=.08)
    hearts = 1 + (t > wt(7, 3) + .4) + (t > wt(7, 3) + .85)
    return fr, 'kob', 3, hearts

CONF = [(random.Random(i).uniform(160, 920), random.Random(i + 99).uniform(0, 1), random.Random(i + 7).choice([SIN, OKR, WHITE, LIGHT])) for i in range(40)]
def s9(t):  # Simpan video ini, lalu uji logomu sendiri.
    fr = bgframe('navy'); t0 = SC[8]
    for x, ph, col in CONF:
        y = 450 + ((t - t0) * 260 + ph * 850) % 850
        if y < 1290 and not (360 <= x <= 720 and 470 <= y <= 880): fr.draw().rectangle(P(x, y, x + 12, y + 12), fill=rgba(col, .85))
    judul(fr, 540, 330, ['LEVEL CLEAR!'], t, t0, 100, OKR, OKR, step=.05)
    p = seg(t, wt(8, 0) - .05, wt(8, 0) + .4)
    if p > 0:
        r = 92 * out_back(p)
        fr.draw().ellipse(P(540 - r, 590 - r, 540 + r, 590 + r), fill=rgba(SIN))
        put_icon(fr, 'bookmark_cFFFFFF', 540, 590, 96 * out_back(p))
    text(fr, 540, 700, 'simpan dulu', F(M, 30), LIGHT, out_cubic(p), anchor='ma')
    for nm, x, ph in (('herman_h_0', 400, 0), ('sonya_h_0', 680, .9)):
        j = abs(math.sin((t - t0) * 6 + ph)) * 40 if t > t0 + .2 else 0
        spr(fr, nm, x, 1300, dy=-j)
    stiker(fr, 540, 810, t, wt(8, 4) - .05, 'uji logomu sendiri', WHITE, INK, rot=-4, size=40)
    return fr, 'navy', 3, 3

def s10(t):  # Ikuti Nuancier Studio, untuk tips logo berikutnya.
    fr = bgframe('navy'); t0 = SC[9]
    a0 = out_cubic(seg(t, t0, t0 + .4))
    rrect(fr, (473, 288, 607, 422), 30, PAPER, a0)
    put_img(fr, logo_simple(110 * S), 485, 300, a0)
    judul(fr, 540, 450, ['Nuancier Studio'], t, wt(9, 1) - .1, 92, WHITE, OKR, step=.1)
    text(fr, 540, 585, '@nuancierstudio', F(M, 40), OKR, out_cubic(seg(t, wt(9, 2), wt(9, 2) + .4)), anchor='ma')
    p = seg(t, wt(9, 0) - .05, wt(9, 0) + .4)
    if p > 0:
        k = out_back(p); w, h = 300 * k, 92 * k
        rrect(fr, (540 - w / 2, 720 - h / 2, 540 + w / 2, 720 + h / 2), h / 2, WHITE)
        if k > .8:
            put_icon(fr, 'user-plus_c15171C', 540 - 70, 720, 40)
            text(fr, 540 - 40, 721, 'Ikuti', F(B, 36), INK, anchor='lm')
    text(fr, 540, 810, 'tips logo berikutnya', F(M, 30), LIGHT, out_cubic(seg(t, wt(9, 4), wt(9, 4) + .4)), anchor='ma')
    for nm, x in (('herman_h_0', 400), ('sonya_h_0', 680)):
        spr(fr, nm, x, 1300, dy=-abs(math.sin(t * 3 + x)) * 6)
    return fr, 'navy', 3, 3

SCENES = [s1, s2, s3, s4, s5, s6, s7, s8, s9, s10]
WIPE = {3: (KOB, OKR, PAPER), 6: (INK, SIN, PAPER), 8: (OKR, KOB, NAV)}  # sapuan masuk ke adegan i

def frame(t, check=False):
    i = max(k for k in range(len(SCENES)) if SC[k] <= t)
    # sapuan: dimulai .25 s sebelum adegan i, ganti adegan di p=.5
    for j, cols in WIPE.items():
        a = SC[j] - .25; b = SC[j] + .25
        if a <= t < b:
            p = (t - a) / (b - a)
            fr, kind, lv, hh = SCENES[j - 1 if p < .5 else j](t if p >= .5 else min(t, SC[j] - .001))
            dark = kind in ('navy', 'sin', 'kob'); KIND[0] = kind; krom(fr, t, lv, hh, dark); capt(fr, t, dark)
            G.sapuan(fr, p, cols); return fr.out()
    fr, kind, lv, hh = SCENES[i](t)
    dark = kind in ('navy', 'sin', 'kob'); KIND[0] = kind
    hpop = wt(7, 3) + .4 if i == 7 else -1
    krom(fr, t, lv, hh, dark, hpop)
    capt(fr, t, dark)
    if check: return fr
    return fr.out()

def audio():
    SR = ST.SR; n = int(TOTAL * SR) + SR
    vo = ST.normalize(ST.load_wav('vo.wav')); V = np.zeros(n); ST.place(V, vo, LEAD)
    mus = np.zeros(n); bpm = 104; beat = 60 / bpm
    bass = [45, 45, 41, 43]; mel = [69, 72, 76, 74, 72, 69, 67, 69]
    k = 0; tb = 0.
    while tb < TOTAL - .6:
        bar = int(tb / (beat * 4))
        if k % 2 == 0: ST.place(mus, ST.Synth.note('tri', bass[bar % 4] - 12, beat * .9, .2, r=.05), tb)
        ST.place(mus, ST.Synth.note('square', mel[k % 8] + (0 if bar % 2 == 0 else -2), beat * .42, .028, duty=.25, r=.07), tb)
        if k % 2 == 1: ST.place(mus, ST.Synth.hat(.035), tb)
        tb += beat / 2; k += 1
    fx = np.zeros(n)
    def blip(t, m=84, v=.06): ST.place(fx, ST.Synth.note('square', m, .05, v, duty=.25), t)
    for tt in (wt(1, 5), wt(4, 6), wt(7, 5), wt(8, 4), wt(9, 0)): blip(tt, 88)
    ST.place(fx, np.concatenate([ST.Synth.note('square', m, .07, .1) for m in (55, 51, 47, 43)]), wt(4, 6))
    for m, dt in zip((72, 76, 79, 84), (0, .09, .18, .27)): ST.place(fx, ST.Synth.note('square', m, .12, .08, duty=.25), SC[8] + dt)
    for j in WIPE:
        nz = ST.Synth.lowpass(np.random.uniform(-1, 1, int(.45 * SR)), 30) * np.hanning(int(.45 * SR)) * .5
        ST.place(fx, nz, SC[j] - .25)
    spans = [(w['t0'], w['t1']) for w in WORDS]
    mus = ST.duck(mus, spans, depth=.4)
    au = ST.mix(V * .95, mus, fx)[:int(TOTAL * SR)]
    with wave.open('mix2.wav', 'wb') as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR); w.writeframes((au * 32767).astype('<i2').tobytes())

if __name__ == '__main__':
    mode = sys.argv[1] if len(sys.argv) > 1 else 'video'
    if mode == 'still':
        ts = [float(x) for x in sys.argv[2:]]
        for k, tt in enumerate(ts): frame(tt).save('chk/st_%02d.jpg' % k, quality=88)
    elif mode == 'check':
        bad = []
        for i in range(len(SCENES)):
            tt = (SC[i] + SC[i + 1]) / 2 + .6
            fr = frame(tt, check=True)
            try: G.cek_gerak(fr, str(i + 1))
            except ValueError as e: bad.append(str(e))
        print('\n'.join(bad) or 'cek_gerak: semua lolos')
    else:
        audio()
        with ST.VideoWriter('final2.mp4', audio='mix2.wav') as vw:
            for f in range(int(TOTAL * FPS)): vw.write(frame(f / FPS))
        print('ok', round(TOTAL, 2))
