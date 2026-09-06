# Absensi Pendidikan Akuntansi 2026 - Kelas C

Aplikasi web absensi mahasiswa berbasis **Python Flask + SQLite**.

## Fitur
- Form absensi (Gmail, Nama, NIM) dengan validasi:
  - Gmail harus format `@gmail.com`
  - NIM harus tepat 10 digit angka
- Data tersimpan: Gmail, Nama, NIM, Tanggal, Jam, Status Hadir
- Cek duplikat otomatis: 1 NIM/Gmail hanya bisa absen 1x per hari
- Halaman admin (dengan login password) untuk rekap per tanggal
- Export rekap ke CSV (bisa langsung dibuka di Excel)
- Tampilan mobile friendly, tema biru-putih kampus

## Struktur File
```
absensi-akuntansi/
├── app.py                  # Backend Flask (semua logika ada di sini)
├── requirements.txt        # Daftar library yang dibutuhkan
├── attendance.db           # Database SQLite (dibuat otomatis saat pertama jalan)
├── templates/
│   ├── index.html           # Form absensi mahasiswa
│   ├── admin_login.html      # Halaman login admin
│   └── admin.html            # Dashboard rekap admin
└── static/
    └── style.css             # Styling biru-putih
```

---

## 1. Menjalankan di Komputer Lokal (untuk testing)

### Syarat
- Python 3.9 atau lebih baru sudah terinstall

### Langkah
```bash
# 1. Masuk ke folder project
cd absensi-akuntansi

# 2. (Opsional tapi disarankan) buat virtual environment
python -m venv venv
source venv/bin/activate        # Mac/Linux
venv\Scripts\activate           # Windows

# 3. Install library yang dibutuhkan
pip install -r requirements.txt

# 4. Jalankan aplikasi
python app.py
```

Setelah berjalan, buka browser ke:
- Form absensi mahasiswa: `http://localhost:5000`
- Login admin: `http://localhost:5000/admin`

**Password admin default: `admin123`**
> Wajib diganti sebelum dipakai sungguhan (lihat bagian "Keamanan" di bawah).

---

## 2. Deploy Online (Gratis) - Render.com

Render.com adalah salah satu cara termudah & gratis untuk online-kan aplikasi Flask.

### Langkah
1. Buat akun di https://render.com (bisa login pakai GitHub)
2. Upload folder project ini ke repository GitHub (buat repo baru, push semua file)
3. Di dashboard Render, klik **New +** → **Web Service**
4. Hubungkan ke repository GitHub Anda
5. Isi konfigurasi:
   - **Environment**: Python 3
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn app:app`
6. Tambahkan Environment Variables (klik "Advanced"):
   - `ADMIN_PASSWORD` = password admin pilihan Anda
   - `SECRET_KEY` = teks acak apapun, misal `k9x8Lm2pQ7z`
7. Klik **Create Web Service**, tunggu proses build selesai
8. Aplikasi akan online di URL seperti `https://absensi-akuntansi.onrender.com`

> Catatan: Pada plan gratis Render, database SQLite (`attendance.db`) bisa terhapus saat server restart/redeploy karena disk-nya tidak permanen. Untuk penggunaan jangka panjang/produksi, disarankan upgrade ke plan berbayar dengan **Persistent Disk**, atau migrasi ke database eksternal seperti PostgreSQL (Render menyediakan gratis juga).

### Alternatif lain
- **PythonAnywhere** (https://www.pythonanywhere.com) - gratis, cocok untuk Flask, disk SQLite lebih persisten dibanding Render free tier.
- **Railway.app** - mirip Render, ada free trial credit.

---

## 3. Cara Pakai Halaman Admin

1. Buka `/admin` lalu login dengan password admin
2. Pilih tanggal yang ingin dilihat rekapnya
3. Klik **Export CSV/Excel** untuk mengunduh data hari itu (file `.csv` yang bisa langsung dibuka Excel/Google Sheets)
4. Klik **Keluar** untuk logout

---

## 4. Keamanan yang Perlu Diperhatikan Sebelum Dipakai Sungguhan

- **Ganti password admin default** (`admin123`) lewat environment variable `ADMIN_PASSWORD`
- **Ganti `SECRET_KEY`** ke string acak yang panjang, jangan pakai nilai default di kode
- Aplikasi ini memakai satu password admin sederhana (cocok untuk 1 dosen/asisten). Jika perlu multi-user admin dengan role berbeda, perlu penambahan sistem login per-user
- Data mahasiswa (nama, NIM, email) adalah data pribadi — pastikan hosting yang dipakai menggunakan HTTPS (Render & PythonAnywhere sudah otomatis HTTPS)

---

## 5. Kustomisasi Cepat

- **Ganti nama kelas/header**: edit variabel `KELAS_LABEL` di `app.py`
- **Ganti warna tema**: edit variabel warna di bagian atas `static/style.css` (`--biru-tua`, `--biru`, dll)
- **Tambah field baru** (misal: Program Studi): tambahkan `<input>` di `templates/index.html`, tambahkan kolom di `CREATE TABLE` pada `app.py`, dan sesuaikan query INSERT/SELECT
