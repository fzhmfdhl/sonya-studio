"""Alat kerja Studio Sonya.

Ini ALAT, bukan template: tidak ada yang menentukan tampilan video di sini.
Pakai sebagai pustaka (import) atau dari baris perintah:

  python3 toolkit/studio.py vo-split  <audio.mp3> <lines.json> <outdir>
  python3 toolkit/studio.py sheet     <out.jpg> <frame1.png> [frame2.png ...]
  python3 toolkit/studio.py upload    <file> <sign.json> [image|video]
  python3 toolkit/studio.py probe     <file>
  python3 toolkit/studio.py audit     <video.mp4> <outdir> [interval_detik=0.33]
      -> potong video jadi lembar periksa besar (6 frame per lembar, 360x640 per frame)
         untuk DILIHAT satu per satu (Read). Wajib sebelum unggah.

Pustaka:
  from toolkit.studio import VideoWriter, load_wav, split_voice, Synth, mix, duck, contact_sheet, font
"""
import json, math, os, subprocess, sys, wave
import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SR = 44100


# ------------------------------------------------------------------ fonts
def font(weight='Bold', size=40):
    """Poppins (Regular/Medium/Bold) bawaan repo; jatuh ke DejaVu bila tak ada."""
    from PIL import ImageFont
    p = os.path.join(ROOT, 'assets', 'fonts', 'Poppins-%s.ttf' % weight)
    if os.path.exists(p):
        return ImageFont.truetype(p, size)
    return ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', size)


# ------------------------------------------------------------------ audio io
def load_wav(path, sr=SR):
    """Baca audio apa pun (mp3/wav) -> numpy float mono di sr."""
    tmp = path + '.tmp.wav'
    subprocess.run(['ffmpeg', '-loglevel', 'error', '-y', '-i', path, '-ac', '1', '-ar', str(sr), tmp], check=True)
    with wave.open(tmp) as w:
        a = np.frombuffer(w.readframes(w.getnframes()), '<i2').astype(float) / 32768
    os.remove(tmp)
    return a


def save_wav(path, a, sr=SR):
    a = np.clip(a, -1, 1)
    with wave.open(path, 'w') as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(sr)
        w.writeframes((a * 32000).astype('<i2').tobytes())


def normalize(a, peak=.85):
    m = np.abs(a).max()
    return a / m * peak if m > 0 else a


def envelope(a, sr=SR, hop_s=.01):
    hop = int(sr * hop_s); n = len(a) // hop
    return np.sqrt((a[:n * hop].reshape(n, hop) ** 2).mean(1))


# ------------------------------------------------------------------ voice split
def split_voice(a, lines, sr=SR, thr=None):
    """Potong satu rekaman VO (banyak kalimat) menjadi segmen per baris naskah.
    Memilih jeda (diam) sebagai batas memakai pemrograman dinamis, sehingga durasi
    tiap segmen sebanding dengan panjang teksnya. Hasil: list (mulai, selesai) detik."""
    e = envelope(a, sr)
    if thr is None:
        thr = max(.006, float(np.percentile(e, 60)) * .35)
    on = e > thr
    idx = np.where(on)[0]
    if not len(idx):
        raise ValueError('audio kosong')
    s, en = idx[0] * .01, idx[-1] * .01
    G = []; i = idx[0]
    while i < idx[-1]:
        if not on[i]:
            j = i
            while j < idx[-1] and not on[j]: j += 1
            if j - i >= 12: G.append((i * .01, j * .01))
            i = j
        else:
            i += 1
    W = np.array([max(1, len(l.replace(' ', ''))) for l in lines], float)
    n = len(lines); m = len(G)
    total = (en - s) - sum(b - a_ for a_, b in G)
    rate = total / W.sum()
    def speech(a_, b):
        return (b - a_) - sum(max(0, min(b, g1) - max(a_, g0)) for g0, g1 in G)
    INF = 1e18
    dp = [[INF] * (m + 2) for _ in range(n + 1)]; pr = [[None] * (m + 2) for _ in range(n + 1)]
    dp[0][0] = 0
    def cost(i, j, li):
        a_ = s if i == 0 else G[i - 1][1]; b = en if j == m + 1 else G[j - 1][0]
        if b <= a_: return INF
        ex = W[li] * rate; L = speech(a_, b)
        gb = 0 if j == m + 1 else (G[j - 1][1] - G[j - 1][0])
        return ((L - ex) / ex) ** 2 * 4 - gb * 3
    for li in range(n):
        for i in range(m + 2):
            if dp[li][i] >= INF: continue
            for j in range(i + 1, m + 2):
                if li < n - 1 and j == m + 1: continue
                if li == n - 1 and j != m + 1: continue
                c = dp[li][i] + cost(i, j, li)
                if c < dp[li + 1][j]: dp[li + 1][j] = c; pr[li + 1][j] = i
    j = m + 1; path = []
    for li in range(n, 0, -1):
        i = pr[li][j]; path.append((i, j)); j = i
    path = path[::-1]
    return [((s if i == 0 else G[i - 1][1]), (en if j == m + 1 else G[j - 1][0])) for i, j in path]


def voice_segments(path, lines, pad=(.04, .08)):
    """Muat VO, normalkan, potong per baris. Hasil list dict {text, audio, dur, env}."""
    a = normalize(load_wav(path))
    segs = split_voice(a, lines)
    out = []
    for text, (s, e) in zip(lines, segs):
        s = max(0, s - pad[0]); e = e + pad[1]
        seg = a[int(s * SR):int(e * SR)]
        out.append(dict(text=text, audio=seg, dur=len(seg) / SR, env=envelope(seg)))
    return out


# ------------------------------------------------------------------ synth (bahan musik, bukan lagu jadi)
class Synth:
    """Bahan membuat musik sendiri (bebas hak cipta). Susun sendiri lagunya per konsep."""
    @staticmethod
    def midi(m): return 440 * 2 ** ((m - 69) / 12)

    @staticmethod
    def env(n, a=.005, r=.08, sr=SR):
        e = np.ones(n); ai = int(a * sr); ri = int(r * sr)
        if ai: e[:ai] = np.linspace(0, 1, ai)
        if 0 < ri < n: e[-ri:] *= np.linspace(1, 0, ri)
        return e

    @staticmethod
    def osc(kind, f, dur, sr=SR, duty=.5):
        t = np.arange(int(dur * sr)) / sr
        if kind == 'sine': return np.sin(2 * np.pi * f * t)
        if kind == 'square': return np.where((t * f) % 1 < duty, 1.0, -1.0)
        if kind == 'saw': return 2 * ((t * f) % 1) - 1
        if kind == 'tri': return 2 * np.abs(2 * ((t * f) % 1) - 1) - 1
        if kind == 'noise': return np.random.uniform(-1, 1, len(t))
        raise ValueError(kind)

    @staticmethod
    def note(kind, m, dur, vol=.1, a=.005, r=.1, duty=.5):
        x = Synth.osc(kind, Synth.midi(m), dur, duty=duty)
        return x * Synth.env(len(x), a, r) * vol

    @staticmethod
    def kick(vol=.4):
        n = int(.18 * SR); t = np.arange(n) / SR
        f = 120 * np.exp(-t * 25) + 40
        return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 18) * vol

    @staticmethod
    def hat(vol=.08):
        n = int(.04 * SR); return np.random.uniform(-1, 1, n) * np.exp(-np.arange(n) / SR * 90) * vol

    @staticmethod
    def lowpass(x, k=8):
        return np.convolve(x, np.ones(k) / k, 'same')


def place(dst, src, t, sr=SR, gain=1.0):
    i = int(t * sr); m = min(len(src), len(dst) - i)
    if m > 0 and i >= 0: dst[i:i + m] += src[:m] * gain
    return dst


def duck(music, spans, depth=.45, sr=SR, fade=.12):
    """Kecilkan musik di rentang (mulai, selesai) saat suara bicara."""
    g = np.ones(len(music))
    for s, e in spans:
        g[max(0, int((s - .05) * sr)):min(len(g), int((e + .1) * sr))] = depth
    k = max(1, int(fade * sr)); g = np.convolve(g, np.ones(k) / k, 'same')
    return music * g


def mix(*tracks):
    n = max(len(t) for t in tracks); out = np.zeros(n)
    for t in tracks: out[:len(t)] += t
    return np.clip(out, -1, 1)


# ------------------------------------------------------------------ video
class VideoWriter:
    """Tulis frame PIL/numpy langsung ke MP4 (H.264 + AAC), 1080x1920 30fps bawaan.
       with VideoWriter('out.mp4', audio='mix.wav') as vw: vw.write(img)"""
    def __init__(self, path, size=(1080, 1920), fps=30, audio=None, crf=19):
        self.size = size
        cmd = ['ffmpeg', '-loglevel', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', '%dx%d' % size, '-r', str(fps), '-i', '-']
        if audio: cmd += ['-i', audio, '-c:a', 'aac', '-b:a', '192k', '-shortest']
        cmd += ['-c:v', 'libx264', '-preset', 'medium', '-crf', str(crf), '-pix_fmt', 'yuv420p', '-movflags', '+faststart', path]
        self.p = subprocess.Popen(cmd, stdin=subprocess.PIPE)

    def write(self, img):
        from PIL import Image
        if not isinstance(img, Image.Image): img = Image.fromarray(np.asarray(img).astype('uint8'))
        if img.size != self.size: img = img.resize(self.size)
        self.p.stdin.write(img.convert('RGB').tobytes())

    def close(self):
        self.p.stdin.close(); self.p.wait()
        if self.p.returncode: raise RuntimeError('ffmpeg gagal')

    def __enter__(self): return self
    def __exit__(self, *a): self.close()


def probe(path):
    r = subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'format=duration,size', '-of', 'json', path], capture_output=True, text=True)
    return json.loads(r.stdout).get('format', {})


def preview_copy(src, dst, max_mb=14):
    """Salinan ringan (720p) bila file asli terlalu besar untuk aset artifact."""
    if os.path.getsize(src) <= max_mb * 1e6:
        if src != dst: subprocess.run(['cp', src, dst], check=True)
        return dst
    subprocess.run(['ffmpeg', '-loglevel', 'error', '-y', '-i', src, '-vf', 'scale=720:-2', '-c:v', 'libx264', '-crf', '24', '-c:a', 'aac', '-b:a', '128k', '-movflags', '+faststart', dst], check=True)
    return dst


def contact_sheet(out, frames, cols=4, w=270):
    """Gabung beberapa frame menjadi satu gambar bernomor untuk diperiksa (Read gambarnya)."""
    from PIL import Image, ImageDraw
    ims = [f if not isinstance(f, str) else Image.open(f) for f in frames]
    h = int(w * ims[0].height / ims[0].width)
    rows = math.ceil(len(ims) / cols)
    c = Image.new('RGB', (cols * w + (cols + 1) * 8, rows * h + (rows + 1) * 8), (120, 120, 120)); d = ImageDraw.Draw(c)
    for i, im in enumerate(ims):
        x = 8 + (i % cols) * (w + 8); y = 8 + (i // cols) * (h + 8)
        c.paste(im.convert('RGB').resize((w, h)), (x, y)); d.rectangle([x, y, x + 26, y + 20], fill=(0, 0, 0)); d.text((x + 6, y + 4), str(i + 1), fill=(255, 255, 255))
    c.save(out, quality=85)
    return out


# ------------------------------------------------------------------ cloudinary
def cloud_upload(path, sign, resource_type='video'):
    """Unggah file ke Cloudinary memakai hasil alat Cloudinary `sign-upload` (satu objek).
    Semua kunci upload_params dikirim apa adanya. Mengembalikan secure_url."""
    if isinstance(sign, list): sign = sign[0]
    cmd = ['curl', '-sS', 'https://%s/v1_1/%s/%s/upload' % (sign.get('host', 'api.cloudinary.com'), sign['cloud_name'], resource_type),
           '-F', 'file=@%s' % path, '-F', 'api_key=%s' % sign['api_key'], '-F', 'signature=%s' % sign['signature']]
    for k, v in sign['upload_params'].items():
        if isinstance(v, bool): v = 'true' if v else 'false'
        cmd += ['-F', '%s=%s' % (k, v)]
    r = subprocess.run(cmd, capture_output=True, text=True)
    d = json.loads(r.stdout or '{}')
    if 'secure_url' not in d: raise RuntimeError('Cloudinary: %s' % (d.get('error') or r.stderr))
    return d['secure_url']


# ------------------------------------------------------------------ sprites kantor
def sprite(name):
    """Sprite karakter kantor (herman_*, sonya_*) + titik kaki (ax, ay)."""
    from PIL import Image
    anch = json.load(open(os.path.join(ROOT, 'assets', 'sprites', 'anchors.json')))
    im = Image.open(os.path.join(ROOT, 'assets', 'sprites', name + '.png')).convert('RGBA')
    a = anch.get(name, [im.width / 2, im.height])
    return im, a[0], a[1]


def audit(video, outdir, step=0.33):
    import glob
    os.makedirs(outdir, exist_ok=True); fr = os.path.join(outdir, 'fr'); os.makedirs(fr, exist_ok=True)
    for f in glob.glob(os.path.join(fr, '*.png')): os.remove(f)
    subprocess.run(['ffmpeg', '-loglevel', 'error', '-y', '-i', video, '-vf', 'fps=%f,scale=360:640' % (1 / step), os.path.join(fr, 'f%04d.png')], check=True)
    fs = sorted(glob.glob(os.path.join(fr, '*.png'))); sheets = []
    for k in range(0, len(fs), 6):
        out = os.path.join(outdir, 'periksa_%03d.jpg' % (k // 6)); contact_sheet(out, fs[k:k + 6], cols=3, w=360)
        sheets.append((out, round(k * step, 2), round(min(len(fs), k + 6) * step, 2)))
    return sheets


if __name__ == '__main__':
    cmd = sys.argv[1] if len(sys.argv) > 1 else ''
    if cmd == 'vo-split':
        lines = json.load(open(sys.argv[3])); od = sys.argv[4]; os.makedirs(od, exist_ok=True)
        segs = voice_segments(sys.argv[2], lines); meta = []
        for i, s in enumerate(segs):
            p = os.path.join(od, 'line_%02d.wav' % i); save_wav(p, s['audio']); meta.append(dict(i=i, text=s['text'], dur=round(s['dur'], 3), file=p))
        json.dump(meta, open(os.path.join(od, 'lines.json'), 'w'), ensure_ascii=False, indent=1); print(json.dumps(meta, ensure_ascii=False))
    elif cmd == 'sheet':
        print(contact_sheet(sys.argv[2], sys.argv[3:]))
    elif cmd == 'upload':
        rt = sys.argv[4] if len(sys.argv) > 4 else 'video'
        print(cloud_upload(sys.argv[2], json.load(open(sys.argv[3])), rt))
    elif cmd == 'audit':
        for o, a, b in audit(sys.argv[2], sys.argv[3], float(sys.argv[4]) if len(sys.argv) > 4 else .33): print('%s  detik %.2f-%.2f' % (o, a, b))
    elif cmd == 'probe':
        print(json.dumps(probe(sys.argv[2])))
    else:
        print(__doc__)
