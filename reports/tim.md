# Laporan tim — <Nama tim>, kasus <NN> <judul kasus>

Satu dokumen bersama, enam bagian. Angka harus dapat ditarik ulang dari `data/silver`, `data/gold`,
dan `log-keputusan.csv` yang sudah di-*commit*.

## Ringkasan
Kasus, seri yang ditangani, dan satu kalimat temuan utama tentang kualitas datanya.

## Data dan lineage
Sumber dan format mentah, jumlah berkas, cara `_berkas_raw`/`_sha256_raw` dibentuk, dan hasil tarik
ulang API (bila dilakukan): apa yang berubah sejak snapshot 17–20 Oktober 2026.

## Masalah data dan penanganannya
Tabel masalah yang ditemukan (missing, outlier, patahan seri, duplikat, format, wilayah) dengan
jumlah baris terdampak, keputusan, dan alternatif yang ditolak. Rujuk id di `log-keputusan.csv`.

## Integrasi dan rekonsiliasi
Seri utama vs pembanding nasional: selisih, penjelasannya (definisi, metode, vintage, granularitas),
dan hasil analisis revisi dari arsip WDI.

## Validasi dan reproduksibilitas
Skema validasi (aturan, hasil lolos/gagal), waktu `python pipeline.py` dari nol, perbandingan pandas
vs DuckDB/Dask, dan keterbatasan yang tersisa.
### Penyimpanan Silver dengan SQLite

Silver pertama yang diuji untuk penyimpanan SQL adalah `grid_listrik.parquet`. Data dimuat ke database SQLite menggunakan tabel `silver_grid` dengan tipe kolom yang ditentukan secara eksplisit. Primary Key menggunakan kombinasi `jenis_grid`, `wilayah_kode`, `tahun`, `rincian`, dan `seri_kode` untuk mengidentifikasi observasi secara unik.

SQLite dipilih karena ringan, tidak memerlukan server database terpisah, dan dapat diintegrasikan langsung dengan Python melalui modul `sqlite3`. Database tersimpan dalam satu file sehingga mudah direproduksi dan didistribusikan dalam lingkungan proyek.

Berbeda dengan JSON mentah yang mempertahankan struktur data sumber secara fleksibel, SQLite menyediakan skema kolom dan tipe data yang jelas, mendukung Primary Key untuk menjaga keunikan data, serta memudahkan query dan analisis terstruktur. JSON tetap sesuai untuk penyimpanan data mentah karena struktur sumber dapat bervariasi.

Pengujian pemuatan pertama menghasilkan **1.254 baris** pada tabel `silver_grid`, sesuai dengan jumlah baris pada `grid_listrik.parquet`. Pemeriksaan struktur tabel juga menunjukkan bahwa Primary Key gabungan telah diterapkan.

## Pembagian kerja
| Anggota | NIM | Komponen | Tugas sampingan | Bagian laporan yang ditulis |
|---|---|---|---|---|
