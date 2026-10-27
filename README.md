# WasteWhistle
PBP Group B9 - Ganjil 26/27

## Menjalankan project lokal

Jalankan perintah dari folder hasil **git clone** yang berisi `manage.py` dan `.git`.
Gunakan branch `feature/reporting` untuk pekerjaan modul laporan.

```powershell
python -m pip install -r requirements.txt
python manage.py migrate
python manage.py runserver 8001
```

Buka `http://127.0.0.1:8001/` untuk membuat akun lokal, lalu masuk.
Dashboard dan `/reporting/create/` memerlukan login. Form laporan saat ini
memvalidasi detail dan lokasi, lalu menampilkan preview. Laporan belum disimpan ke database.
Jika mengakses form saat belum login, setelah login pengguna kembali ke form.

### Reporting tahap 3: pilih lokasi

- Isi judul, deskripsi, dan patokan lokasi (opsional).
- Klik peta OpenStreetMap untuk memilih titik. Pin bisa digeser; koordinat terisi otomatis.
- Gaya peta HOT, tampilan awal Jakarta, dan tombol zoom memakai pola dari branch
  `feature/map`. Pin laporan tetap dipilih sendiri, tidak dipasang otomatis.
- Untuk akses keyboard, gunakan tombol zoom, geser
  peta dengan tombol panah lalu tekan **Gunakan titik tengah peta**, atau isi koordinat manual.
- Latitude dan longitude wajib diisi, maksimal 6 angka desimal. Server memvalidasi
  rentang latitude -90 sampai 90 dan longitude -180 sampai 180.
- Klik **Lihat preview** untuk melihat koordinat dan tautan ke OpenStreetMap.
  Jika ada error form, isian dan titik yang valid tetap ditampilkan.
- Peta menggunakan Leaflet 1.9.4 dari CDN dan tile HOT dari OpenStreetMap France, sehingga memerlukan
  internet. Jika peta gagal dimuat, koordinat tetap dapat diisi manual. Tidak ada
  pencarian alamat atau permintaan lokasi perangkat pada tahap ini.
- Tile memakai `referrerPolicy: "strict-origin-when-cross-origin"` untuk mengirim
  hanya origin aplikasi saat meminta gambar peta. Pengaturan ini hanya berlaku
  untuk gambar tile, bukan perubahan kebijakan global Django.

Referensi: [Leaflet](https://leafletjs.com/examples/quick-start/) dan
[tile HOT OpenStreetMap France](https://wiki.openstreetmap.org/wiki/FR:Serveurs/tile.openstreetmap.fr#Fond_de_carte_"Humanitaire").

## CSS dan integrasi Reporting

Tampilan mengikuti branch `chore/html_css_refactor`, memakai **Tailwind CSS 3.4.17**.
Navbar bersama berada di `templates/topbar.html`. Reporting menggunakannya juga.
Edit `static/css/input.css` atau kelas di template, bukan CSS hasil build langsung.

Dengan Node.js/npm terpasang, jalankan:

```powershell
npm ci
npm run build:css
```

Untuk otomatis membangun ulang CSS selama mengedit, jalankan `npm run watch:css`
di terminal kedua. Hasil build `static/css/style.css` ikut di-commit, sehingga
menjalankan Django saja tidak memerlukan npm. Jangan memasukkan `node_modules`.
Konfigurasi memindai template project, template app, dan widget Reporting.

```powershell
python manage.py check
python manage.py test reporting
```

## Anggota
- Ahmad Rafa Robyan 2506620721
- Justin Lie 2506591961
- Priskila Abigail Magaini 2506590252
- Syakira Aqilah Amru 2506541622
- Adriel Raynard Davis Sihotang 2506587150

## Deskripsi Aplikasi
Aplikasi WasteWhistle adalah aplikasi melacak dan menetapkan keberadaan sampah yang dilaporkan oleh pengguna aplikasi.

## Daftar Modul

- (Justin) Authentication, menggunakan OAuth.
- (Syakira) Landing Page, menggunakan OAuth.
- (Adriel) Reporting and Timer, modul ini akan menggunakan API OpenStreetMap
- (Rafa) Display Report, modul ini juga akan menggunakan API OpenStreetMap
- (Priskila) Customer Service, menggunakan OAuth, sebagai sarana untuk melaporkan bug atau error pada aplikasi.

## Dokumentasi
Aplikasi ini akan menggunakan API dari OpenStreetMap untuk memberikan feedback pada user terkait dengan laporan sampah yang telah di laporkan.

Untuk sistem authentication akan menggunakan API OAuth dari google.

## Peran Pengguna
Siapapun yang menggunakan aplikasi ini dapat melaporkan adanya sampah yang terlihat di sekeliling mereka dan memberikan peringatan di aplikasi dengan keberadaan sampah lainnya.
