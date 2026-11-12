"""Alat gerak untuk bagian MOTION JERSTALK (acuan editing Jers, Okt 2026).

Ini ALAT, bukan template tampilan: easing, kanvas halus (supersampling 2x), krom bagian
(label, penghitung bab, progress bar), caption pill karaoke, judul yang tersusun kata per kata,
stiker, kartu UI tiruan, mesin tik, coretan, sapuan pecahan (shard wipe), dan ikon Lucide.
Palet, metafora, dan isi tiap episode tetap kamu rancang sendiri.

Semua koordinat memakai ruang 1080x1920. Kanvas digambar 2x lalu diperkecil, jadi garis dan
lengkung halus (bagian motion TIDAK pixel; hanya karakter Jers dan Nabila yang pixel).
"""
import os, math
from PIL import Image, ImageDraw, ImageFont, ImageFilter

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
FD = os.path.join(ROOT, 'assets', 'fonts')
W, H, FPS, S = 1080, 1920, 30, 2
CX = 540
# Zona aman TikTok: atas 220, bawah 520, kanan 200. Teks di x 180-900.
X0, X1, TOPY, CAPY, BARY = 180, 900, 250, 1290, 1372

_FC = {}
def font(name, size):
    k = (name, size)
    if k not in _FC:
        _FC[k] = ImageFont.truetype(os.path.join(FD, name), int(size * S))
    return _FC[k]
BOLD = 'InterDisplay-Bold.otf'; MED = 'Inter-Medium.otf'; HEAVY = 'Poppins-Bold.ttf'; MONO = 'DejaVuSansMono.ttf'

# ---------- easing ----------
def cl(x): return max(0., min(1., x))
def seg(t, a, b): return cl((t - a) / (b - a)) if b > a else float(t >= a)
def out_cubic(x): x = cl(x); return 1 - (1 - x) ** 3
def out_expo(x): x = cl(x); return 1. if x >= 1 else 1 - 2 ** (-10 * x)
def out_back(x, s=1.9): x = cl(x) - 1; return 1 + (s + 1) * x ** 3 + s * x ** 2
def in_out(x): x = cl(x); return 4 * x ** 3 if x < .5 else 1 - (-2 * x + 2) ** 3 / 2
def lerp(a, b, p): return a + (b - a) * p

def rgba(h, a=1.):
    h = h.lstrip('#')
    return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16), int(255 * cl(a)))

# ---------- kanvas ----------
_BG = {}
class Frame:
    """Kanvas 2x. Elemen digambar di lapisan kecil seukuran kotaknya lalu ditumpuk (cepat)."""
    def __init__(s, bg, dot=None):
        k = (bg, dot)
        if k not in _BG:
            im = Image.new('RGBA', (W * S, H * S), rgba(bg))
            if dot:
                d = ImageDraw.Draw(im); c = rgba(dot)
                for y in range(0, H, 44):
                    for x in range(0, W, 44):
                        d.ellipse(P(x - 1.6, y - 1.6, x + 1.6, y + 1.6), fill=c)
            _BG[k] = im
        s.im = _BG[k].copy(); s.boxes = []; s.kind = 'isi'
    def put(s, L, a=1., xy=(0, 0), rec=True):
        if a <= 0: return
        if rec and s.kind: s.boxes.append((xy[0] / S, xy[1] / S, (xy[0] + L.width) / S, (xy[1] + L.height) / S, s.kind))
        if a < 1:
            al = L.getchannel('A').point(lambda v: int(v * a)); L = L.copy(); L.putalpha(al)
        x, y = int(xy[0]), int(xy[1])
        # potong bagian yang keluar kanvas
        x0, y0 = max(0, -x), max(0, -y); x1, y1 = min(L.width, s.im.width - x), min(L.height, s.im.height - y)
        if x1 <= x0 or y1 <= y0: return
        if (x0, y0, x1, y1) != (0, 0, L.width, L.height): L = L.crop((x0, y0, x1, y1))
        s.im.alpha_composite(L, (x + x0, y + y0))
    def draw(s): return ImageDraw.Draw(s.im)
    def out(s): return s.im.reduce(S).convert('RGB')

def P(*v): return [int(round(x * S)) for x in v]
def tw(t, f): return f.getbbox(t)[2] / S if t else 0

def text(fr, x, y, t, f, col, a=1., anchor='la'):
    if not t or a <= 0: return
    bx = f.getbbox(t, anchor=anchor); pad = 4
    L = Image.new('RGBA', (bx[2] - bx[0] + 2 * pad, bx[3] - bx[1] + 2 * pad), (0, 0, 0, 0))
    ImageDraw.Draw(L).text((pad - bx[0], pad - bx[1]), t, font=f, fill=rgba(col), anchor=anchor)
    fr.put(L, a, (x * S + bx[0] - pad, y * S + bx[1] - pad))

def rrect(fr, box, r, col, a=1., outline=None, ow=0, shadow=0):
    if a <= 0: return
    x0, y0, x1, y1 = P(*box); w, h = max(1, x1 - x0), max(1, y1 - y0)
    if shadow:
        m = int(shadow * S * 2); Sh = Image.new('RGBA', (w + 2 * m, h + 2 * m), (0, 0, 0, 0))
        ImageDraw.Draw(Sh).rounded_rectangle((m, m + shadow * S // 2, m + w, m + h + shadow * S // 2), r * S, fill=(10, 14, 40, 70))
        fr.put(Sh.filter(ImageFilter.GaussianBlur(shadow * S * .6)), a, (x0 - m, y0 - m), rec=False)
    L = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    ImageDraw.Draw(L).rounded_rectangle((0, 0, w - 1, h - 1), r * S, fill=rgba(col), outline=rgba(outline) if outline else None, width=int(ow * S))
    fr.put(L, a, (x0, y0))

# ---------- latar ----------
def latar(fr, t, dot=None, ring=None):
    """Grid titik sudah ada di Frame(bg, dot). Ini menambah lingkaran besar samar yang bernapas pelan."""
    if not ring: return
    d = fr.draw(); k = 1 + .03 * math.sin(t * 1.3)
    for cx, cy, r in ((300, 760, 330), (860, 1180, 260)):
        r *= k; d.ellipse(P(cx - r, cy - r, cx + r, cy + r), outline=rgba(ring), width=int(46 * S))

# ---------- krom bagian ----------
def krom(fr, t, p_total, bab, n_bab, pal, label=None):
    """Chip JERSTALK kiri atas, penghitung bab kanan atas, label mono, progress bar.
    Kunci palet opsional untuk adegan gelap/berwarna: chip_bg, chip_fg, cnt_bg, cnt_fg, bar."""
    cb, cf = pal.get('chip_bg', pal['ink']), pal.get('chip_fg', pal['paper'])
    nb, nf = pal.get('cnt_bg', pal['acc']), pal.get('cnt_fg', pal['ink'])
    bar = pal.get('bar', pal['acc']); old = fr.kind; fr.kind = 'krom'
    rrect(fr, (X0, TOPY, X0 + 150, TOPY + 44), 10, cb)
    text(fr, X0 + 75, TOPY + 22, 'JERSTALK', font(MONO, 20), cf, anchor='mm')
    rrect(fr, (X1 - 96, TOPY + 6, X1, TOPY + 38), 16, nb)
    text(fr, X1 - 48, TOPY + 22, '%d / %02d' % (bab, n_bab), font(MONO, 19), nf, anchor='mm')
    if label:
        text(fr, X0, TOPY + 70, label, font(MONO, 24), pal['mute'])
    rrect(fr, (X0, BARY, X1, BARY + 6), 3, pal['mute'], .35)
    rrect(fr, (X0, BARY, X0 + max(6, (X1 - X0) * cl(p_total)), BARY + 6), 3, bar); fr.kind = old

# ---------- caption pill karaoke (HANYA di bagian motion) ----------
def caption(fr, kata, aktif, t_in, t, pal, hl=()):
    """kata: 2-4 kata yang sedang diucapkan; aktif: indeks kata yang sedang terdengar.
    Kata dalam hl ditandai warna aksen. Pill pop kecil saat frasa berganti."""
    f = font(BOLD, 40); sp = tw(' ', f)
    ws = [tw(w, f) for w in kata]; tot = sum(ws) + sp * (len(kata) - 1)
    k = .9 + .1 * out_back(seg(t, t_in, t_in + .18))
    pw, ph = tot + 56, 76
    L = Image.new('RGBA', (int(pw * S), int(ph * S)), (0, 0, 0, 0)); d = ImageDraw.Draw(L)
    d.rounded_rectangle((0, 0, L.width - 1, L.height - 1), 14 * S, fill=rgba(pal.get('pill_bg', pal['ink'])))
    x = 28
    for i, w in enumerate(kata):
        c = pal.get('pill_hl', pal['acc']) if (i == aktif or w.lower().strip('.,?!') in hl) else pal.get('pill_fg', pal['paper'])
        d.text((int(x * S), int(ph / 2 * S)), w, font=f, fill=rgba(c), anchor='lm'); x += ws[i] + sp
    L = L.resize((max(1, int(L.width * k)), max(1, int(L.height * k))), Image.LANCZOS)
    old = fr.kind; fr.kind = 'cap'; fr.put(L, 1., (CX * S - L.width / 2, CAPY * S - L.height / 2)); fr.kind = old

# ---------- judul tersusun kata per kata ----------
def judul(fr, x, y, baris, t, t0, f, pal, hl=(), step=.11, rise=26, anchor='la'):
    """baris: daftar baris; tiap kata naik + muncul bergiliran. Kata dalam hl berwarna aksen-2."""
    i = 0; lh = f.size / S * 1.08
    for bi, b in enumerate(baris):
        ws = b.split(' '); sp = tw(' ', f); full = sum(tw(w, f) for w in ws) + sp * (len(ws) - 1)
        xx = x - full / 2 if anchor == 'ma' else x
        for w in ws:
            p = out_expo(seg(t, t0 + i * step, t0 + i * step + .45))
            if p > 0:
                c = pal['acc2'] if w.lower().strip('.,?!') in hl else pal['head']
                text(fr, xx, y + bi * lh + rise * (1 - p), w, f, c, p)
            xx += tw(w, f) + sp; i += 1
    return y + len(baris) * lh

# ---------- stiker ----------
def stiker(fr, cx, cy, t, t0, s, pal, rot=-6, bg=None, fg=None, size=30):
    p = seg(t, t0, t0 + .35)
    if p <= 0: return
    k = out_back(p); f = font(BOLD, size); w = tw(s, f) + 36; h = size * 1.75
    L = Image.new('RGBA', (int(w * S), int(h * S)), (0, 0, 0, 0)); d = ImageDraw.Draw(L)
    d.rounded_rectangle((0, 0, L.width - 1, L.height - 1), 10 * S, fill=rgba(bg or pal['acc']))
    d.text((L.width // 2, L.height // 2), s, font=f, fill=rgba(fg or pal['ink']), anchor='mm')
    L = L.rotate(rot + 8 * (1 - p), expand=True, resample=Image.BICUBIC)
    L = L.resize((max(1, int(L.width * k)), max(1, int(L.height * k))), Image.LANCZOS)
    fr.put(L, cl(p * 3), (cx * S - L.width / 2, cy * S - L.height / 2))

# ---------- mesin tik + coretan ----------
def ketik(s, t, t0, cps=26):
    n = int(max(0, t - t0) * cps); return s[:n], n < len(s)
def coret(fr, x0, y, x1, p, col, w=8):
    if p <= 0: return
    fr.draw().line(P(x0, y, lerp(x0, x1, out_cubic(p)), y), fill=rgba(col), width=int(w * S))

# ---------- sapuan pecahan (transisi antar adegan) ----------
def sapuan(fr, p, cols):
    """p 0->1. Tiga pita miring menyapu dari kanan ke kiri. Pita tengah menutup layar penuh
    sekitar p 0.42-0.52, jadi GANTI ADEGAN TEPAT DI p = 0.5."""
    if p <= 0 or p >= 1: return
    d = fr.draw()
    for i, c in enumerate(cols):
        q = in_out(cl((p - i * .12) / .76)); o = lerp(3300, -3300, q)
        pts = [(o - 1500, -200), (o + 2100, -200), (o + 1500, 2120), (o - 2100, 2120)]
        d.polygon([tuple(P(*pt)) for pt in pts], fill=rgba(c))

# ---------- ikon Lucide ----------
_IC = {}
def ikon(fr, path, cx, cy, size, a=1., rot=0., bebas=False):
    """bebas=True untuk watermark raksasa yang sengaja keluar tepi (tidak dihitung cek_gerak)."""
    if path not in _IC: _IC[path] = Image.open(path).convert('RGBA')
    im = _IC[path].resize((int(size * S), int(size * S)), Image.LANCZOS)
    if rot: im = im.rotate(rot, expand=True, resample=Image.BICUBIC)
    fr.put(im, a, (cx * S - im.width / 2, cy * S - im.height / 2), rec=not bebas)

def kursor(fr, path, x, y, a=1.):
    ikon(fr, path, x + 18, y + 18, 44, a)

# ---------- pemeriksa kerapian bagian motion ----------
def cek_gerak(fr, nama=''):
    """Panggil pada frame tengah setiap adegan (saat isinya lengkap). Menolak isi yang keluar zona aman
    TikTok, isi yang terlalu sedikit (rentang tinggi < 40% area), dan isi yang menimpa caption pill."""
    bad = []; isi = [b for b in fr.boxes if b[4] == 'isi']; cap = [b for b in fr.boxes if b[4] == 'cap']
    for b in isi:
        if b[0] < X0 - 24 or b[2] > X1 + 24: bad.append('isi keluar tepi kiri/kanan (%d..%d)' % (b[0], b[2])); break
    for b in isi:
        if b[1] < TOPY - 10 or b[3] > BARY + 10: bad.append('isi keluar atas/bawah (%d..%d)' % (b[1], b[3])); break
    if not isi: bad.append('adegan kosong')
    else:
        top = min(b[1] for b in isi); bot = max(b[3] for b in isi)
        if bot - top < .4 * (CAPY - 60 - TOPY - 100): bad.append('isi terlalu sedikit (rentang %d px)' % (bot - top))
    for c in cap:
        for b in isi:
            if b[3] > c[1] + 6 and b[1] < c[3] - 6 and b[2] > c[0] and b[0] < c[2]: bad.append('isi menimpa caption'); break
    if bad: raise ValueError('adegan %s: %s' % (nama, '; '.join(dict.fromkeys(bad))))
    return True
