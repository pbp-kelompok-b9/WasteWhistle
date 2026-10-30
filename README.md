# WasteWhistle

**PBP Group B9 · Ganjil 2026/2027**

## Anggota
- Ahmad Rafa Robyan 2506620721
- Justin Lie 2506591961
- Priskila Abigail Magaini 2506590252
- Syakira Aqilah Amru 2506541622
- Adriel Raynard Davis Sihotang 2506587150

## Deskripsi Aplikasi
Tumpukan sampah yang tidak kunjung hilang? Sudah melaporkannya ke pihak berwajib tetapi seringkali terlupakan? WasteWhistle adalah solusinya.
Aplikasi WasteWhistle adalah aplikasi melacak dan menetapkan keberadaan sampah yang dilaporkan oleh pengguna aplikasi. Pada aplikasi ini, para pengguna dapat melaporkan titik sampah yang belum dibersihkan dan menghasilkan poin yang dapat ditukarkan dengan hadiah. Laporan yang sudah dibuat akan diterima oleh para staf dan akan diatasi segera. 

Melalui aplikasi ini, pengguna dapat melacak kondisi dari laporan yang sudah dibuat. Selain itu, pengguna dapat mencari info mengenai lokasi bank sampah terdekat, serta mendapatkan edukasi tambahan mengenai pemilahan sampah.

## Daftar Modul
1. Dashboard - Menampilkan lokasi laporan dan bank sampah serta memiliki fitur komentar untuk para user (Rafa)
2. Directory - Menampilkan daftar lokasi bank sampah yang dapat diisi manual oleh staf atau diambil dari OpenStreetMap API (Justin)
3. Reporting - Membuat tiket report dari user agar titik lokasi sampah dapat diatasi oleh staf (Adriel)
4. Education - Membuat halaman edukasi bagi user, serta memperbolehkan staf untuk menambahkan informasi-informasi penting mengenai pengelolaan sampah (Syakira)
5. Rewards - Menghitung jumlah poin yang diperoleh oleh user dan menampilkan data hadiah yang dapat ditukarkan (Priskila)

## Peran Pengguna

- Pengguna Terdaftar: Dapat melaporkan adanya sampah yang terlihat di sekeliling mereka dan memberikan peringatan di aplikasi dengan keberadaan sampah lainnya, serta mengakses informasi mengenai lokasi bank sampah, edukasi, dan hadiah.

- Staf & Superuser: Dapat menambahkan lokasi bank sampah, informasi edukasi, serta data hadiah. Dapat menetapkan kondisi laporan yang diterima menjadi 'selesai' atau 'belum selesai'.

## Tautan *deployment* PWS

> *template url*

## Tautan desain Figma

> https://www.figma.com/design/QfKI77MxBIhJvfUgibyrIF/WasteWhistle?node-id=65-2771&t=1MM78gijhXiaqsN4-1

## Menjalankan project lokal

Jalankan perintah dari folder hasil **git clone** yang berisi `manage.py`.

```powershell
python -m pip install -r requirements.txt
python manage.py migrate
python manage.py runserver 8001
```

Buka `http://127.0.0.1:8001/` untuk membuat akun lokal, lalu masuk.
Dashboard dan halaman reporting memerlukan login. Tombol **Lapor Sampah** membuka
`/reporting/` (Laporan Saya). Klik **Tambah laporan** untuk membuka `/reporting/create/`.
Jika mengakses form saat belum login, setelah login pengguna kembali ke form.

## Dokumentasi Modul

### 1. Dashboard

#### Tujuan dan fitur

Halaman ringkasan di `/dashboard/` menampilkan statistik total laporan, laporan milik pengguna, jumlah bank sampah, poin ringkasan, 10 laporan terbaru, dan komentar. Dashboard memakai data dari modul Reporting, Directory, dan Comment. Nilai poin di dashboard saat ini dihitung sederhana sebagai jumlah laporan pengguna dikali 10.

#### Halaman dan akses

Dashboard memerlukan login. Pengguna dapat menulis komentar; komentar milik sendiri dapat diedit atau dihapus, sedangkan staf dapat menghapus komentar pengguna lain.

#### API

Dashboard memakai Leaflet/OpenStreetMap. Endpoint komentar adalah `POST /comment/add/`, `POST /comment/edit/<id>/`, dan `POST /comment/delete/<id>/`; ketiganya memerlukan login dan CSRF. Endpoint laporan untuk peta dijelaskan pada [JSON laporan untuk peta dashboard](#json-laporan-untuk-peta-dashboard).

#### AI disclosure

[ai disclosure]

### 2. Directory

#### Tujuan dan fitur

Halaman `/directory/` menampilkan direktori bank sampah dengan nama, alamat, kontak, koordinat, dan penanda sumber data (Komunitas atau OpenStreetMap). Pencarian mencocokkan nama, alamat, nomor telepon, dan email.

#### Halaman dan akses

Daftar dapat dilihat tanpa login. Superuser dapat menambah lokasi lewat formulir; pengguna dalam grup `Staff` atau superuser dapat mengedit lokasi manual dan menyinkronkan data OpenStreetMap. Penghapusan manual dibatasi untuk superuser. Sinkronisasi memakai tombol **Perbarui data dari OpenStreetMap**; proses ini mengganti seluruh entri yang ditandai sebagai data OSM dengan hasil pencarian terbaru.

#### API

`GET /directory/api/?name=<kata>` mengembalikan daftar lokasi dan dapat mencari nama, alamat, nomor telepon, atau email. `POST /directory/api/create_waste_bank` menambah lokasi untuk Staff/superuser; endpoint memeriksa grup secara langsung. Formulir `/directory/create_waste_bank/` hanya mengizinkan superuser. Sinkronisasi `POST /directory/sync-osm/` memerlukan login serta grup Staff atau superuser. Nominatim dicari untuk Banten, Jawa Barat, Jawa Tengah, DI Yogyakarta, dan Jawa Timur dengan batas 40 hasil per provinsi.

#### AI disclosure

**Tools AI:** ChatGPT dan Gemini

**Tujuan pemakaian:** AI membantu mengevaluasi hasil kode yang sudah dibuat terlebih dahulu, serta membantu menjelaskan bagaimana untuk melakukan fetch API pada OpenStreetMap. Setelah mendapatkan hasil prompt AI, kode tersebut dicek kembali untuk memastikan berjalan sesuai yang diinginkan.

**Strategi prompt:**

- Meminta AI untuk mengubah CSS traditional yang sudah terlebih dahulu digunakan menjadi Tailwind CSS.
- Meminta penjelasan mengenai bagaimana untuk melakukan fetch API pada OpenStreetMap, serta menganalisis strukturnya untuk menemukan dan menjelaskan apabila ada kesalahan.
- Meminta bantuan AI untuk memeriksa kekurangan dari views dan models yang sudah dibuat secara manual dan apa yang dapat diubah agar alur program website dapat lebih efisien.
- Meminta penjelasan mengenai bagaimana untuk melakukan fetch API

**Link Prompt AI:**

- https://chatgpt.com/share/6ae491f6-3644-83ec-b4c5-1a784e59be2a
- https://share.gemini.google/hP3VBEchY8pW

### 3. Reporting

#### Tujuan dan fitur

Pengguna login dapat membuat laporan lokasi sampah, melihat laporan miliknya, memperbarui, dan menghapusnya. Data laporan juga disediakan untuk integrasi peta Dashboard.

#### Halaman dan akses

`/reporting/` menampilkan Laporan Saya dan `/reporting/create/` membuka formulir laporan. Rincian penyimpanan, edit/hapus, API peta, dan pemilihan lokasi dijelaskan di bawah.

#### API

Model utama: `reporting.models.Report`. Lihat [JSON laporan untuk peta dashboard](#json-laporan-untuk-peta-dashboard) untuk skema endpoint dan contoh integrasi.

#### Laporan Saya dan penyimpanan laporan

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

#### Mengedit dan menghapus laporan sendiri

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

#### JSON laporan untuk peta dashboard

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

#### Pemilihan lokasi

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

#### AI disclosure

[ai disclosure]

### 4. Education

#### Tujuan dan fitur

Halaman tersedia di **`/education/`**. Konten dibaca dari database dan mencakup:

- **Panduan sampah:** nama, kategori (organik, anorganik, kertas, residu, atau B3), deskripsi, dan instruksi penanganan. Daftar dapat dicari berdasarkan nama.
- **Informasi penguraian:** nama material dan estimasi waktu penguraian (dalam hari), yang ditampilkan sebagai hari, bulan, atau tahun.
- **Mitos atau fakta:** pernyataan, klasifikasi (mitos atau fakta), penjelasan, dan tautan sumber opsional untuk detail lebih lanjut.
- **Kuis harian “Which Bin?”:** tiga soal acak dari panduan yang memiliki soal kuis dan diperuntukkan pada pengguna yang sudah login. Server akan memeriksa jawaban dan menghitung skor.

Kuis memerlukan minimal tiga `QuizQuestion` yang terkait ke panduan. Set soal disimpan di sesi pengguna untuk hari itu, jawaban pertama per soal dikunci, dan kategori yang benar ditampilkan setelah menjawab. Setelah skor disimpan, pengguna dapat mencoba lagi pada tanggal berikutnya.

#### Halaman dan akses

Tambah, edit, dan hapus panduan, informasi penguraian, serta mitos/fakta tersedia pada halaman Education. Aksi ini memerlukan login dan permission Django **`education.manage_education_content`**; berikan permission hanya kepada staf yang berwenang. Form memeriksa kolom wajib dan menolak teks kosong atau yang hanya berisi tag HTML. Sumber mitos/fakta opsional. Menghapus panduan juga menghapus soal kuis terkait.

Untuk memberi permission kepada akun staf lokal, jalankan `python manage.py shell`:

```python
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from education.models import WasteGuide

user = get_user_model().objects.get(username="nama-akun")
content_type = ContentType.objects.get_for_model(WasteGuide)
permission = Permission.objects.get(
    content_type=content_type, codename="manage_education_content"
)
user.user_permissions.add(permission)
```

Buat soal kuis melalui Django Admin di **`/admin/`**, setelah membuat panduan. Login sebagai superuser dan tambahkan `QuizQuestion` dengan panduan yang sesuai. Untuk mencoba modul, buka `/education/`, tambahkan konten, lalu jawab tiga soal kuis sebagai pengguna yang sudah login.

#### API

| Method dan path | Nama URL | Perilaku |
| --- | --- | --- |
| `GET /education/api/waste-guides/?q=<kata>` | `waste_guide_api` | Respons `{"results": [...]}`; pencarian `q` opsional dan mencari nama tanpa membedakan kapitalisasi. Publik. |
| `POST /education/api/quiz/answer/` | `answer_question_api` | JSON `{"question_id":"<uuid>","answer":"<kategori>"}`; memeriksa soal pada sesi dan mengunci jawaban pertama. Login dan CSRF diperlukan. |
| `POST /education/api/quiz/submit/` | `submit_quiz_api` | Menyimpan skor setelah semua jawaban pada sesi terisi; skor dihitung server. Login dan CSRF diperlukan. |

Endpoint kuis memberi `401` untuk pengguna anonim, `400` untuk sesi/payload tidak valid, dan `409` jika pengguna sudah mengikuti kuis hari itu. Metode selain GET pada API panduan atau selain POST pada API kuis ditolak dengan `405`.

#### AI disclosure

**Tools AI:** ChatGPT dan Claude

**Tujuan pemakaian:** AI membantu memahami dan mengevaluasi implementasi modul Education meliputi models, views, session management, API, integrasi backend dengan JavaScript, serta tampilan halaman menggunakan HTML dan CSS.

**Strategi prompt:**

- Memberikan kode aktual dan meminta AI meninjau model, view, URL, form, template, JavaScript, HTML, CSS, dan test Education yang sudah ada dan menganalisis jika terdapat _error_ atau kesalahan logika.
- Mengajukan pertanyaan spesifik mengenai fungsi, relasi, dan alur program.
- Meminta AI memberikan penjelasan terkait struktur dan algoritma yang rumit untuk kemudian diterapkan setelah dianalisis lebih lanjut. 

### 5. Rewards

#### Tujuan dan fitur

Halaman `/rewards/` menampilkan saldo poin, level, katalog hadiah, voucher hasil penukaran, dan riwayat transaksi. Katalog dapat difilter menurut kategori dan harga maksimum. Kategori hadiah: transportasi, belanja, lingkungan, acara, dan lainnya. Level bertambah setiap 500 poin positif yang pernah diperoleh; menukar hadiah mengurangi saldo, tetapi tidak menurunkan level.

#### Halaman dan akses

Pengunjung dapat melihat katalog. Login diperlukan untuk menukar hadiah. Pengelolaan katalog hanya untuk pengguna Django dengan `is_staff`; staf dapat menambah atau mengubah hadiah dari halaman Rewards. Hadiah yang sudah pernah ditukar tidak dapat dihapus; stok dapat diubah menjadi nol untuk menandainya habis. Penukaran memeriksa level, stok, dan saldo poin, lalu membuat kode voucher.

#### API

Modelnya adalah `Reward`, `PointTransaction`, dan `Redemption`. API katalog `GET /rewards/api/rewards/?kategori=<kategori>&maks_poin=<angka>` dan API saldo/riwayat `GET /rewards/api/saya/` bersifat GET. Untuk pengguna anonim, endpoint saldo mengembalikan `authenticated: false`. Endpoint perubahan memakai POST: `/rewards/api/rewards/baru/`, `/rewards/api/rewards/<id>/ubah/`, `/rewards/api/rewards/<id>/hapus/`, dan `/rewards/api/rewards/<id>/tukar/`. Perubahan katalog memerlukan `is_staff`; penukaran memerlukan login.

Poin dicatat sebagai transaksi positif atau negatif. Fungsi ledger mendukung pemberian poin idempoten dengan referensi, tetapi saat ini pelaporan tidak otomatis membuat transaksi poin. Karena itu, poin ringkasan pada Dashboard (10 per laporan) berbeda dari saldo ledger Rewards.

#### AI disclosure

[ai disclosure]

## Layanan eksternal

- Data lokasi bank sampah dari [OpenStreetMap](https://www.openstreetmap.org/) diambil melalui layanan pencarian [Nominatim](https://nominatim.openstreetmap.org/ui/search.html); wilayah dan batas hasil sinkronisasi dijelaskan pada modul Directory.
- Peta pada formulir Reporting menggunakan [Leaflet](https://leafletjs.com/) dan tile HOT dari [OpenStreetMap France](https://wiki.openstreetmap.org/wiki/FR:Serveurs/tile.openstreetmap.fr#Fond_de_carte_"Humanitaire"). Leaflet dan tile peta dimuat dari layanan eksternal, jadi memerlukan koneksi internet.

## CSS

Proyek menggunakan **Tailwind CSS 4**. Navbar bersama berada di
`templates/topbar.html`. Edit CSS sumber `static/css/input_*.css` atau kelas di
template, bukan CSS hasil build langsung.

CSS hasil build (`static/css/output_*.css`) sudah ada di repositori. Untuk
membangun ulang Education dengan Node.js/npm terpasang:

```powershell
npm ci
npx @tailwindcss/cli -i ./static/css/input_education.css -o ./static/css/output_education.css
```

Tambahkan `--watch` untuk membangun ulang saat file berubah. Ganti nama input dan
output sesuai modul lain (`dashboard`, `directory`, `reporting`, atau `rewards`).
Menjalankan Django saja tidak memerlukan npm. Jangan commit `node_modules`.

## Test

Suite test Django tersedia untuk fitur **Directory, Comment, Education, Reporting,** dan **Rewards**. Jalankan seluruh suite dengan:

```powershell
python manage.py test
```

Untuk menjalankan suite modul tertentu, misalnya:

```powershell
python manage.py test directory comment education reporting rewards
```

Pemeriksaan konfigurasi Django dapat dijalankan terpisah dengan `python manage.py check`.
