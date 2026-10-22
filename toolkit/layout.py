"""Alat kerapian tata letak Studio Sonya.

Masalah yang pernah lolos dan HARUS dicegah alat ini:
  - kata yang di-highlight menempel ke kata sebelah ("itu[tangan]tim"),
  - teks keluar dari gelembung/kartu (highlight menyembul di bawah gelembung),
  - label ticker terpotong di tepi layar ("REAKING"),
  - ikon menimpa teks tombol,
  - kartu yang terbang menutupi sebagian teks kartu lain ("JERS" jadi "ERS"),
  - wadah kosong tampil sebelum isinya.

Cara pakai per frame:
    from toolkit.layout import Layout, rich_text, fit_text, icon_label
    L = Layout(1080, 1920)                      # satu per frame
    card = L.box('kartu_jers', (x0, y0, x1, y1), kind='card')
    rich_text(draw, L, 'judul', 'Logo itu *bentuk* yang diingat', (80, 300), max_w=920,
              font_path=FONT_BOLD, size=64, fill='#fff', hl_fill='#F7C948', hl_text='#111', parent=None)
    fit_text(draw, L, 'isi_jers', 'restu?', card, font_path=FONT, max_size=40, parent='kartu_jers')
    icon_label(img, draw, L, 'btn_carousel', icon_img, 'carousel', (x, y), font_path=FONT, size=34)
    ...
    issues = L.check()                          # [] berarti rapi
Kumpulkan issues semua frame (atau tiap 3 frame) SEBELUM ekspor; perbaiki sampai kosong.
"""
from PIL import ImageFont

SAFE = dict(top=220, bottom=420, left=60, right=140)   # zona aman Instagram Reels (1080x1920)


def _font(path, size):
    return ImageFont.truetype(path, size)


def _inter(a, b):
    x0, y0 = max(a[0], b[0]), max(a[1], b[1]); x1, y1 = min(a[2], b[2]), min(a[3], b[3])
    return max(0, x1 - x0) * max(0, y1 - y0)


def _inside(a, b, pad=0):
    return a[0] >= b[0] + pad - 0.5 and a[1] >= b[1] + pad - 0.5 and a[2] <= b[2] - pad + 0.5 and a[3] <= b[3] - pad + 0.5


class Layout:
    """Daftar kotak elemen dalam satu frame + pemeriksa tabrakan/keluar batas."""
    def __init__(self, W=1080, H=1920, safe=SAFE):
        self.W, self.H, self.safe, self.items = W, H, safe, {}

    def box(self, name, bbox, kind='card', parent=None, pad=0, allow=(), safe=True, moving=False):
        """kind: text | icon | card | sprite | line | marker | deco.
        line = garis, penggaris, garis putus-putus, sumbu, garis waktu (daftarkan bbox tiap ruas);
        marker = titik/simpul/ujung garis waktu, centang, bintang kecil. Keduanya TIDAK boleh menyentuh teks, ikon, atau kartu.
        deco = latar/tekstur yang memang di belakang semuanya (tidak diperiksa). parent: nama wadah (teks/ikon harus di dalamnya dengan jarak pad).
        allow: nama elemen yang SENGAJA boleh bertumpuk. safe=False untuk elemen dekoratif yang boleh ke tepi.
        moving=True untuk elemen yang sedang masuk/keluar (tetap diperiksa terhadap teks)."""
        self.items[name] = dict(name=name, bbox=tuple(map(float, bbox)), kind=kind, parent=parent, pad=pad, allow=set(allow), safe=safe, moving=moving)
        return self.items[name]['bbox']

    def check(self, tol=0.02):
        """Kembalikan daftar masalah (string). Aturan:
        1. teks/ikon wajib di dalam wadahnya (parent) dengan jarak pad;
        2. teks/ikon/kartu tidak boleh keluar layar; teks tidak boleh masuk zona tidak aman;
        3. teks tidak boleh tertimpa elemen lain (kecuali parent/anak atau allow);
        4. ikon tidak boleh menimpa teks; kartu tidak boleh saling menimpa sebagian (>2%) kecuali allow;
        5. garis (line) dan penanda (marker) tidak boleh menyentuh teks, ikon, atau kartu (beri jarak)."""
        out = []; it = self.items; W, H, s = self.W, self.H, self.safe
        for n, e in it.items():
            b = e['bbox']
            if e['kind'] in ('text', 'icon', 'card') and (b[0] < -0.5 or b[1] < -0.5 or b[2] > W + 0.5 or b[3] > H + 0.5):
                out.append('%s keluar layar %s' % (n, _r(b)))
            if e['kind'] == 'text' and e['safe'] and (b[1] < s['top'] or b[3] > H - s['bottom'] or b[0] < s['left'] or b[2] > W - s['right']):
                out.append('%s masuk zona tidak aman %s' % (n, _r(b)))
            if e['parent']:
                p = it.get(e['parent'])
                if p is None: out.append('%s: wadah %s tidak terdaftar' % (n, e['parent']))
                elif not _inside(b, p['bbox'], e['pad']): out.append('%s keluar dari %s (pad %d) %s vs %s' % (n, e['parent'], e['pad'], _r(b), _r(p['bbox'])))
        names = list(it)
        for i in range(len(names)):
            for j in range(i + 1, len(names)):
                a, c = it[names[i]], it[names[j]]
                if c['name'] in a['allow'] or a['name'] in c['allow']: continue
                if a['parent'] == c['name'] or c['parent'] == a['name']: continue
                if a['parent'] and a['parent'] == c['parent'] and 'deco' in (a['kind'], c['kind']): continue
                ov = _inter(a['bbox'], c['bbox'])
                if ov <= 0: continue
                kinds = {a['kind'], c['kind']}
                small = min(_area(a['bbox']), _area(c['bbox'])) or 1
                if kinds & {'line', 'marker'} and kinds & {'text', 'icon', 'card'}:
                    if _anc(it, a, c['name']) or _anc(it, c, a['name']): continue
                    out.append('garis/penanda menabrak: %s x %s' % (a['name'], c['name'])); continue
                if 'text' in kinds and 'deco' not in kinds:
                    # teks tertimpa sesuatu yang bukan wadahnya
                    if _anc(it, a, c['name']) or _anc(it, c, a['name']): continue
                    out.append('tumpang tindih: %s x %s' % (a['name'], c['name']))
                elif kinds == {'icon'} or kinds == {'icon', 'card'} and ov / small > tol:
                    if _anc(it, a, c['name']) or _anc(it, c, a['name']): continue
                    out.append('tumpang tindih: %s x %s' % (a['name'], c['name']))
                elif kinds == {'card'} and ov / small > tol:
                    out.append('kartu bertumpuk sebagian: %s x %s' % (a['name'], c['name']))
        return out


def _anc(it, e, name):
    p = e.get('parent')
    while p:
        if p == name: return True
        p = it.get(p, {}).get('parent')
    return False


def _area(b): return max(0, b[2] - b[0]) * max(0, b[3] - b[1])
def _r(b): return '(%d,%d,%d,%d)' % tuple(int(round(v)) for v in b)


# ------------------------------------------------------------------ teks
def text_bbox(draw, xy, text, font):
    return draw.textbbox(xy, text, font=font)


def layout_words(text, font, max_w, hl_pad=(14, 6), space=None):
    """Pecah teks bertanda *kata* menjadi baris; hasil list baris berisi (kata, highlight, lebar).
    Kata highlight diberi padding horizontal hl_pad[0] di KEDUA sisi dan tetap dipisah spasi normal."""
    space = space if space is not None else font.getlength(' ')
    tokens = []
    for part in text.replace('**', '*').split('*'):
        pass
    hl = False; buf = ''
    for ch in text:
        if ch == '*':
            if buf: tokens += [(w, hl) for w in buf.split(' ') if w]
            buf = ''; hl = not hl
        else:
            buf += ch
    if buf: tokens += [(w, hl) for w in buf.split(' ') if w]
    lines, cur, cw = [], [], 0
    for w, h in tokens:
        ww = font.getlength(w) + (2 * hl_pad[0] if h else 0)
        add = ww + (space if cur else 0)
        if cur and cw + add > max_w:
            lines.append(cur); cur, cw = [], 0; add = ww
        cur.append((w, h, ww)); cw += add
    if cur: lines.append(cur)
    return lines, space


def rich_text(draw, L, name, text, xy, max_w, font_path, size, fill, hl_fill, hl_text=None, parent=None, pad=0,
              align='left', line_gap=1.18, hl_pad=(14, 6), radius=10, safe=True, draw_it=True):
    """Tulis teks dengan kata *highlight* yang rapi (spasi terjaga, padding seragam). Mendaftarkan kotak ke L.
    Kembalikan bbox seluruh blok."""
    f = _font(font_path, size)
    lines, space = layout_words(text, f, max_w, hl_pad)
    asc, desc = f.getmetrics(); lh = int((asc + desc) * line_gap)
    x0, y0 = xy; boxes = []
    for li, line in enumerate(lines):
        lw = sum(w[2] for w in line) + space * (len(line) - 1)
        x = x0 if align == 'left' else (x0 + (max_w - lw) / 2 if align == 'center' else x0 + max_w - lw)
        y = y0 + li * lh
        for w, h, ww in line:
            if h:
                bb = (x, y - hl_pad[1] + 2, x + ww, y + asc + desc + hl_pad[1] - 4)
                if draw_it: draw.rounded_rectangle(bb, radius=radius, fill=hl_fill)
                if draw_it: draw.text((x + hl_pad[0], y), w, font=f, fill=hl_text or fill)
                boxes.append(bb)
            else:
                if draw_it: draw.text((x, y), w, font=f, fill=fill)
                boxes.append(draw.textbbox((x, y), w, font=f))
            x += ww + space
    bb = (min(b[0] for b in boxes), min(b[1] for b in boxes), max(b[2] for b in boxes), max(b[3] for b in boxes)) if boxes else (x0, y0, x0, y0)
    if L is not None: L.box(name, bb, kind='text', parent=parent, pad=pad, safe=safe)
    return bb


def fit_text(draw, L, name, text, box, font_path, max_size=64, min_size=22, fill='#fff', pad=24, align='center',
             valign='center', parent=None, hl_fill='#F7C948', hl_text='#111', line_gap=1.15):
    """Pas-kan teks (boleh *highlight*) di dalam kotak dengan padding; mengecil otomatis sampai muat."""
    bx0, by0, bx1, by1 = box; mw = bx1 - bx0 - 2 * pad; mh = by1 - by0 - 2 * pad
    size = max_size
    while size >= min_size:
        f = _font(font_path, size); lines, _ = layout_words(text, f, mw)
        asc, desc = f.getmetrics(); h = int((asc + desc) * line_gap) * len(lines)
        if h <= mh and all(sum(w[2] for w in l) + f.getlength(' ') * (len(l) - 1) <= mw for l in lines): break
        size -= 2
    f = _font(font_path, size); lines, _ = layout_words(text, f, mw); asc, desc = f.getmetrics()
    h = int((asc + desc) * line_gap) * len(lines)
    y = by0 + pad + (mh - h) / 2 if valign == 'center' else by0 + pad
    return rich_text(draw, L, name, text, (bx0 + pad, y), mw, font_path, size, fill, hl_fill, hl_text, parent=parent, pad=0, align=align, line_gap=line_gap)


def icon_label(img, draw, L, name, icon, label, xy, font_path, size=34, fill='#111', gap=14, pad=(22, 12), bg=None,
               radius=14, parent=None):
    """Tombol/label berikon: [pad][ikon][gap][teks][pad]. Ikon diskalakan ke tinggi teks. Mendaftarkan semua kotak."""
    f = _font(font_path, size); asc, desc = f.getmetrics(); th = asc + desc
    ih = int(th * 0.95); iw = int(icon.width * ih / icon.height) if icon is not None else 0
    tw = f.getlength(label)
    x0, y0 = xy; w = pad[0] * 2 + iw + (gap if icon is not None else 0) + tw; h = pad[1] * 2 + th
    bb = (x0, y0, x0 + w, y0 + h)
    if bg: draw.rounded_rectangle(bb, radius=radius, fill=bg)
    L.box(name, bb, kind='card', parent=parent)
    if icon is not None:
        ic = icon.resize((iw, ih)); ix, iy = int(x0 + pad[0]), int(y0 + pad[1] + (th - ih) / 2)
        img.alpha_composite(ic.convert('RGBA'), (ix, iy)); L.box(name + '.ikon', (ix, iy, ix + iw, iy + ih), kind='icon', parent=name)
    tx = x0 + pad[0] + iw + (gap if icon is not None else 0)
    draw.text((tx, y0 + pad[1]), label, font=f, fill=fill)
    L.box(name + '.teks', draw.textbbox((tx, y0 + pad[1]), label, font=f), kind='text', parent=name, safe=False)
    return bb


def ticker(img, draw, L, name, label, items, y, t, font_path, size=30, speed=120, W=1080, h=56, margin=0,
           label_bg='#E2463A', bar_bg='#F7C948', label_fill='#fff', fill='#111', sep='  •  '):
    """Ticker berita yang rapi: label utuh di dalam layar (tidak terpotong), teks berjalan HANYA di kanan label."""
    from PIL import Image, ImageDraw
    f = _font(font_path, size); lab_w = int(f.getlength(label)) + 36
    draw.rectangle((margin, y, W - margin, y + h), fill=bar_bg)
    strip = Image.new('RGBA', (W - margin * 2 - lab_w, h), (0, 0, 0, 0)); sd = ImageDraw.Draw(strip)
    txt = sep.join(items) + sep; tw = f.getlength(txt); off = -(t * speed) % tw
    x = -off
    while x < strip.width:
        sd.text((x, (h - size) / 2 - 4), txt, font=f, fill=fill); x += tw
    img.alpha_composite(strip, (margin + lab_w, y))
    draw.rectangle((margin, y, margin + lab_w, y + h), fill=label_bg)
    draw.text((margin + 18, y + (h - size) / 2 - 4), label, font=f, fill=label_fill)
    L.box(name, (margin, y, W - margin, y + h), kind='deco', safe=False)
    L.box(name + '.label', (margin, y, margin + lab_w, y + h), kind='card', parent=name)
    return (margin, y, W - margin, y + h)
