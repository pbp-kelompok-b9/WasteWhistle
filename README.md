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
Dashboard dan halaman reporting memerlukan login. Tombol **Lapor Sampah** membuka
`/reporting/` (Laporan Saya). Klik **Tambah laporan** untuk membuka `/reporting/create/`.
Jika mengakses form saat belum login, setelah login pengguna kembali ke form.

### Reporting tahap 4: Laporan Saya dan penyimpanan laporan

- **Laporan Saya** menampilkan laporan milik akun yang sedang login, terbaru di atas,
  dengan 10 laporan per halaman. Akun yang belum punya laporan melihat tampilan kosong.
- **Lihat preview** memvalidasi form tanpa menyimpan. **Kirim laporan** memvalidasi
  ulang, menyimpan ke database, lalu kembali ke Laporan Saya dengan pesan berhasil.
- Tanggal dan jam dibuat tampil dalam WIB. Refresh halaman daftar tidak mengirim
  ulang form, dan laporan tetap tersedia setelah logout lalu login kembali.
- Setiap form baru memiliki identitas pengiriman yang terikat ke akun login.
  Pengiriman ulang dari form yang sama tidak membuat laporan ganda atau mengubah
  waktu dibuat. Untuk laporan baru, buka **Tambah laporan** lagi.
- Jika isian diubah lewat tombol Back setelah laporan terkirim, aplikasi meminta
  pengguna mengirim kembali sebagai laporan baru; laporan sebelumnya tetap utuh.
- Model `reporting.models.Report` berisi `reporter` (relasi user), `title`,
  `description`, `location_note`, `latitude`, `longitude`, dan `created_at`.
  Pelapor dan waktu dibuat ditentukan server, bukan input pengguna. Model ini dapat
  dipakai saat integrasi modul Display Report; halaman ini khusus riwayat pribadi.
- Field internal `submission_id` mencegah pengiriman ganda lewat batasan unik di
  database. Laporan lama tetap didukung dengan nilai kosong pada field ini.
- Setelah menarik perubahan, jalankan `python manage.py migrate` sebelum membuka
  reporting. Preview dari versi sebelumnya belum tersimpan, jadi tidak menjadi riwayat.

Pengecekan alur demo: **Lapor Sampah → Tambah laporan → isi detail dan pilih pin →
Lihat preview → Kirim laporan → Laporan Saya**. Pastikan laporan tetap ada setelah
refresh/login ulang dan akun lain tidak melihatnya. Preview saja tidak menyimpan.

### Mengedit dan menghapus laporan sendiri

- Akun yang sudah login dapat memakai tombol **Edit** atau **Hapus** pada kartu
  laporannya di **Laporan Saya**. Pemeriksaan pemilik juga dilakukan di server:
  URL laporan akun lain atau ID yang tidak ada mengembalikan **404**.
- **Edit** (`/reporting/<id>/edit/`, `reporting:edit`) mengisi form dan pin dengan
  data tersimpan. Judul, deskripsi, patokan, serta koordinat dapat diperbarui.
  Preview dan Batal tidak menyimpan; **Simpan perubahan** memperbarui laporan
  yang sama. ID, pelapor, waktu dibuat, dan identitas pengiriman tetap.
- **Hapus** (`/reporting/<id>/delete/`, `reporting:delete`) membuka konfirmasi.
  GET tidak menghapus apa pun; hanya POST **Ya, hapus laporan** yang menghapus
  laporan tersebut secara permanen. Batal kembali ke daftar.
- Kedua aksi membutuhkan sesi login dan POST dengan token CSRF untuk menyimpan
  perubahan. Validasi form edit sama dengan tambah laporan. Input yang salah tetap
  ditampilkan untuk diperbaiki tanpa mengubah laporan tersimpan.
- Endpoint JSON langsung mencerminkan hasil edit/hapus pada permintaan berikutnya.
  Peta yang sudah terbuka perlu mengambil JSON kembali untuk memperbarui markernya.
  Fitur ini tidak memerlukan migration tambahan.

### JSON laporan untuk peta dashboard

Method `show_json` di `reporting/views.py` mengubah data model `Report` menjadi
`JsonResponse`. Endpoint **GET `/reporting/json/`**, nama URL **`reporting:show_json`**.

- Menggunakan sesi login Django yang sama dengan dashboard. Pengunjung yang belum
  login menerima HTTP **401** dengan JSON `{"error": "Silakan login untuk melihat laporan."}`,
  bukan redirect ke HTML login. Metode selain GET ditolak dengan **405**.
- Peta bersama mengambil **semua laporan yang sudah disimpan**, dari semua akun,
  urutan terbaru dahulu. Endpoint ini belum memakai pagination atau filter area;
  jika data membesar, tambahkan pagination/filter batas peta bersama konsumennya.
  Halaman **Laporan Saya** (`/reporting/`) tetap hanya menampilkan laporan akun sendiri.
- Respons memakai object `reports` berisi array. Saat kosong: `{"reports": []}`.
  Ini JSON biasa, bukan GeoJSON atau format serializer Django `pk`/`fields`.
- `latitude` dan `longitude` berupa **angka JSON**, siap digunakan di Leaflet dalam
  urutan `[latitude, longitude]`. `created_at` berupa string ISO 8601 dengan zona waktu;
  frontend dapat memformatnya menjadi WIB. Koordinat tetap disimpan sebagai Decimal di DB.
- Hanya field yang diperlukan untuk menampilkan laporan dikirim. Data akun pelapor
  dan `submission_id` tidak disertakan. Respons diberi `Cache-Control: no-store`.
- Tidak ada perubahan model/migration baru untuk endpoint ini. Sesudah merge, tetap
  jalankan `python manage.py migrate` bila migration reporting sebelumnya belum diterapkan.

Contoh respons (data ilustrasi):

```json
{
  "reports": [
    {
      "id": 12,
      "title": "Sampah dekat halte",
      "description": "Plastik berserakan.",
      "location_note": "Dekat gerbang",
      "latitude": -6.362,
      "longitude": 106.827,
      "created_at": "2026-10-28T03:00:00+00:00"
    }
  ]
}
```

Contoh integrasi untuk teman modul peta: letakkan di script **template Django**,
di dalam callback `DOMContentLoaded` setelah variabel Leaflet `map` dibuat.
Jika memakai file JS eksternal, teruskan URL melalui atribut `data-*` dari template.
Dashboard dan endpoint harus berada di origin yang sama agar sesi login dipakai.

```javascript
const reportMarkers = L.layerGroup().addTo(map);

async function loadReports() {
    const response = await fetch("{% url 'reporting:show_json' %}", {
        credentials: "same-origin",
        headers: { Accept: "application/json" },
    });
    if (response.status === 401) throw new Error("Silakan login kembali.");
    if (!response.ok) throw new Error("Laporan gagal dimuat.");

    const { reports } = await response.json();
    reportMarkers.clearLayers();
    for (const report of reports) {
        const popup = document.createElement("div");
        // Isi laporan adalah teks pengguna; jangan masukkan ke innerHTML.
        popup.textContent = `${report.title}: ${report.description}`;
        L.marker([report.latitude, report.longitude])
            .bindPopup(popup)
            .addTo(reportMarkers);
    }
}

loadReports().catch((error) => console.error(error.message));
```

Contoh ini belum dipasang ke dashboard; penggabungan marker dilakukan di modul peta.
Pengecekan: login, buka `/reporting/json/`, kirim laporan lewat form, lalu muat ulang
endpoint. Preview saja tidak muncul, dan pengiriman ulang tidak menambah objek ganda.

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

- (Justin) Membuat Directory Bank Sampah
- (Syakira) Landing Page, menggunakan OAuth.
- (Adriel) Reporting and Timer, modul ini akan menggunakan API OpenStreetMap
- (Rafa) Display Report, modul ini juga akan menggunakan API OpenStreetMap
- (Priskila) Customer Service, menggunakan OAuth, sebagai sarana untuk melaporkan bug atau error pada aplikasi.

## Dokumentasi
Aplikasi ini akan menggunakan API dari OpenStreetMap untuk memberikan feedback pada user terkait dengan laporan sampah yang telah di laporkan.

Untuk sistem authentication akan menggunakan API OAuth dari google.

## Peran Pengguna
Siapapun yang menggunakan aplikasi ini dapat melaporkan adanya sampah yang terlihat di sekeliling mereka dan memberikan peringatan di aplikasi dengan keberadaan sampah lainnya.
