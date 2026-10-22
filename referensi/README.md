# Referensi desain Sonya (disetujui Jers, 22 Okt 2026)

Dari enam arah visual yang diuji, Jers memilih **dua**. Semua konten Nuancier dibangun dari dua arah ini.
Lihat (Read) keempat gambar di folder ini sebelum merancang konsep. Ini acuan **rasa dan kualitas**, bukan template:
komposisi, kata, dan adegan tetap dirancang ulang untuk setiap pesanan.

Kode yang membuat frame-frame ini ada di `render_referensi.py` (teknik sobekan kertas, teks ikut miring, cahaya, vignette, butiran).
Boleh dipelajari dan dipakai fungsinya; jangan menyalin komposisinya mentah.

---------------------------------------------------------------------------------------------------
## A. Kolase kertas rapi (`kolase/`)

Kertas warna Nuancier ditempel lapis demi lapis di atas latar putih hangat `#F7F7F5` atau blok warna pilar penuh.

**Yang membuatnya "rapi" (catatan Jers: kolase harus rapi):**
- Kertas berbentuk persegi yang **dipotong lurus**. Hanya **satu sisi** (paling banyak dua) yang disobek, dan sobekannya halus
  (gelombang lembut, amplitudo sekitar 5 px), dengan serat putih kertas `#F6F4EF` terlihat di tepi sobekan. Tidak ada gerigi acak di semua sisi.
- Semua lembar **sejajar pada margin yang sama** (x = 70) dan memakai lebar yang konsisten. Jarak antar lembar sama.
- Miring kecil, **maksimal 1,5°**, berganti arah antar lembar. Teks **ikut miring bersama kertasnya** (seolah tercetak di kertas).
- Bayangan tipis dan konsisten (offset sekitar 4/9 px, blur 9 px, gelap 25–30%). Butiran kertas halus.
- Teks hanya di atas satu lembar dan tidak pernah melintasi tepi kertas. Padding teks ke tepi ≥ 50 px.
- Warna teks: putih di Kobalt atau Sinabar; Tinta di Oker dan di kertas putih.

**Gerak (motion):** lembar meluncur masuk atau jatuh lalu menempel bergantian mengikuti ucapan (ease-out 0,4–0,6 detik),
bayangan menyusul sesaat setelah kertas mendarat, sedikit memantul (maksimal 1°). Bunyi: desis kertas, tap lembut.
Lembar yang sudah ditempel tidak bergerak acak lagi.

**Cocok untuk:** identitas merek, elemen merek (warna, huruf, bentuk), tips bertahap, dan **carousel grafis**.

**Dilarang:** potongan bergerigi acak di semua sisi, kemiringan besar, lembar yang tidak sejajar tanpa alasan,
teks yang melintasi sobekan, kolase penuh sesak dengan banyak potongan kecil.

---------------------------------------------------------------------------------------------------
## B. Close-up sinematik (`sinematik/`)

Latar Tinta gelap. Kamera sangat dekat pada satu bagian bentuk (lengkung, potongan, titik) lalu mundur perlahan mengungkap logo utuh.

- Cahaya utama satu arah (lembut, dari kiri atas), **vignette** di tepi, butiran film halus, blur tipis pada bagian yang tidak fokus.
- Bentuk besar berwarna pilar (Kobalt paling sering) dengan **glow** lembut. Logo utuh tampil di tengah dengan ruang kosong lega.
- Teks sedikit: satu kalimat pendek, putih, rata tengah, di sepertiga bawah area aman. Garis tipis abu boleh jadi pemisah.
- Palet: Tinta + satu warna pilar. Jangan memakai tiga warna sekaligus.

**Gerak (motion):** satu tarikan kamera panjang per adegan (zoom-out pelan 3–6 detik, ease in-out), fokus berpindah (blur ke tajam),
cahaya bergeser sedikit. Transisi lewat gelap (fade ke Tinta) atau whip pendek. Bunyi: dengung rendah, swell halus.

**Cocok untuk:** **video portofolio**, peluncuran logo klien, hook dramatis, cerita detail desain.

**Dilarang:** teks banyak, kartu atau panel UI, gerak cepat berulang, cahaya neon berlebihan.

---------------------------------------------------------------------------------------------------
## Cara memakai

- Setiap pesanan punya dua konsep: biasanya **satu kolase dan satu sinematik**, supaya Jers memilih di antara dua rasa yang jelas berbeda.
- Pesanan portofolio: konsep motion = **sinematik** (karya klien sebagai bintang), konsep grafis/carousel = **kolase rapi**.
- Variasi antar pesanan datang dari dalam arah: warna pilar dominan, komposisi, metafora, dan gerak kamera. Jangan kembali ke kartu UI.
- Arah lain (poster kata raksasa, risograph, metamorfosis geometri, grid editorial) **tidak dipakai** kecuali Jers memintanya di `catatan`.
