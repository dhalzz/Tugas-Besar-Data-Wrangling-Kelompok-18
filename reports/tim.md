# Laporan tim — <Nama tim>, kasus <NN> <judul kasus>

Satu dokumen bersama, enam bagian. Angka harus dapat ditarik ulang dari `data/silver`, `data/gold`,
dan `log-keputusan.csv` yang sudah di-*commit*.

## Ringkasan
Kasus, seri yang ditangani, dan satu kalimat temuan utama tentang kualitas datanya.

## Data dan lineage
Data yang digunakan pada Case 18 berasal dari dua sumber, yaitu Badan Pusat Statistik (BPS) dan World Bank melalui indikator World Development Indicators (WDI). Data BPS mencakup indikator ketenagalistrikan dan bahan bakar, sedangkan data WDI digunakan sebagai data pembanding pada tingkat nasional.

Data mentah yang digunakan berjumlah 9 berkas dan disimpan di dalam direktori `data/raw/`. Berkas tersebut menggunakan dua format, yaitu CSV dan JSON. Data CSV digunakan untuk menyimpan data tabular, sedangkan JSON digunakan untuk menyimpan respons API beserta struktur dan metadata sumber aslinya.

Untuk menjaga keterlacakan data, setiap baris hasil ekstraksi dilengkapi dengan kolom `_berkas_raw` dan `_sha256_raw`. Kolom `_berkas_raw` berisi lokasi relatif berkas asal terhadap direktori `data/raw/`, sedangkan `_sha256_raw` berisi nilai hash SHA-256 yang diperoleh melalui fungsi `sha256_raw()` pada `src/common/manifest.py`. Nilai hash diambil berdasarkan pencatatan pada `data/raw/MANIFEST.csv`, sehingga tidak ditulis secara manual. Pemeriksaan manifest dilakukan sebelum pipeline dijalankan untuk memastikan berkas mentah sesuai dengan nilai SHA-256 yang tercatat.

Snapshot data yang digunakan berasal dari BPS tanggal 17 Oktober 2026 dan WDI tanggal 20 Oktober 2026. Dalam proses reproduksi, pipeline menggunakan berkas mentah yang telah diarsipkan tersebut. Belum terdapat bukti pengukuran perbandingan hasil penarikan ulang API terhadap snapshot sebelumnya, sehingga perubahan nilai akibat pembaruan API belum dapat disimpulkan.

### Pilihan Basis Data dan Perbandingan dengan Dokumen JSON Mentah
Pada tahap penyimpanan (Tahap 5), Silver dan Gold dimuat ke basis data relasional **SQLite** (`data/gold/gold.sqlite`) melalui `python pipeline.py` (`src/gold/sql_schema.py` dan `src/gold/muat_sql.py`) dengan empat tabel bertipe kolom eksplisit dan kunci primer komposit:
- `silver`: `PRIMARY KEY (sumber, seri_kode, wilayah_kode, periode, rincian, _berkas_raw)`
- `gold_panel`: `PRIMARY KEY (sumber, seri_kode, wilayah_kode, periode, rincian, _berkas_raw)`
- `gold_nasional`: `PRIMARY KEY (periode, seri_kode, rincian)`
- `gold_rekonsiliasi`: `PRIMARY KEY (pasangan, periode)`

**Perbandingan dengan penyimpanan dokumen JSON mentah:**
- **Lapis Bronze (data mentah di `data/raw/`):** Cocok disimpan sebagai dokumen JSON/CSV mentah apa adanya. Struktur respons WebAPI BPS (HTML yang di-*escape* maupun `datacontent`) dan API World Bank (array `[header, records]` bersarang) bersifat heterogen antar-sumber. Menyimpan dokumen mentah mempertahankan bentuk asli sumber untuk auditabilitas dan verifikasi sidik SHA-256 (`MANIFEST.csv`).
- **Lapis Silver dan Gold (`gold.sqlite` + Parquet):** Cocok disimpan dalam basis data relasional SQLite (dan Parquet untuk pertukaran analitik). Pada lapis ini, skema sudah seragam dan terstruktur; tipe data numerik (`REAL`, `INTEGER`) dan teks (`TEXT`) terdefinisi jelas, serta **Primary Key** menjamin keunikan observasi (mencegah duplikasi baris saat penggabungan maupun pemuatan ulang). Kueri lintas tabel (*JOIN* seri utama vs pembanding nasional, agregasi per provinsi/tahun) jauh lebih cepat, ringkas, dan dapat divalidasi langsung dibanding mem-parsing ulang dokumen JSON bersarang.
- **Alasan memilih SQLite dibanding server terpisah (PostgreSQL):** SQLite bersifat *serverless*, terintegrasi langsung di pustaka standar Python (`sqlite3`), dan tersimpan dalam satu berkas lokal yang dibangun ulang otomatis oleh `python pipeline.py` (tidak di-*commit* ke repositori), sehingga memenuhi syarat reproduksi dari nol di laptop biasa tanpa konfigurasi layanan tambahan.

## Masalah data dan penanganannya
Tabel masalah yang ditemukan (missing, outlier, patahan seri, duplikat, format, wilayah) dengan
jumlah baris terdampak, keputusan, dan alternatif yang ditolak. Rujuk id di `log-keputusan.csv`.

## Integrasi dan rekonsiliasi
Rekonsiliasi dilakukan dengan membandingkan seri utama BPS dan seri pembanding dari World Development Indicators (WDI). Dua pasangan indikator yang digunakan adalah `var87` dengan `EG.ELC.ACCS.ZS` untuk indikator akses listrik, serta agregat bahan bakar bersih BPS (Listrik + Gas/Elpiji) dengan `EG.CFT.ACCS.ZS` dari WDI.

Hasil rekonsiliasi menghasilkan 60 baris, terdiri dari 35 baris pasangan indikator listrik dan 25 baris pasangan indikator bahan bakar bersih. Dari seluruh baris tersebut, terdapat 47 periode yang memiliki kedua nilai sehingga dapat dihitung selisihnya, sedangkan 13 baris lainnya tetap dipertahankan karena salah satu sumber tidak menerbitkan data pada periode tersebut.

Pada periode yang memiliki pasangan nilai, selisih dihitung dari nilai seri utama dikurangi nilai seri pembanding. Hasil klasifikasi menunjukkan 41 baris dengan perbedaan definisi, 3 baris dengan perbedaan cakupan, dan 3 baris dengan perbedaan metode. Sebanyak 13 baris tanpa pasangan tidak memiliki nilai selisih maupun kategori penjelasan karena tidak tersedia dua nilai untuk dibandingkan.

Hasil rekonsiliasi disimpan dalam `data/gold/tabel_rekonsiliasi.parquet` dan `data/gold/tabel_rekonsiliasi.csv`. Setiap baris juga menyimpan informasi sumber berkas asal untuk mendukung keterlacakan data.

Analisis revisi WDI belum dapat dilakukan karena arsip snapshot versi sebelumnya belum ditemukan pada berkas tambahan yang diperiksa. Oleh karena itu, rekonsiliasi menggunakan snapshot WDI tanggal 20 Oktober 2026 sebagai data pembanding. Perubahan nilai antarversi WDI belum dapat disimpulkan dan menjadi keterbatasan analisis.

## Validasi dan reproduksibilitas
Pipeline dijalankan menggunakan perintah `python pipeline.py` setelah pemeriksaan kesesuaian berkas mentah dengan `MANIFEST.csv`. Dari 9 berkas mentah yang diperiksa, seluruhnya dinyatakan sesuai dengan nilai SHA-256 pada manifest.

Proses reproduksi berhasil menjalankan empat tahap, yaitu ekstraksi, Silver, Gold, dan validasi. Hasilnya menghasilkan 4.830 baris Silver, 4.830 baris Gold panel, 187 baris Gold nasional, dan 60 baris tabel rekonsiliasi. Penyimpanan ke SQLite juga berhasil dilakukan dengan jumlah baris yang sesuai pada setiap tabel.

Tahap validasi menghasilkan 5 dari 5 aturan lolos. Waktu eksekusi pipeline secara keseluruhan sekitar 3,5 detik berdasarkan penjumlahan waktu setiap tahap yang tercatat pada terminal.

Penyimpanan analitik menggunakan pandas dan Parquet, sedangkan SQLite digunakan untuk penyimpanan relasional. Perbandingan kinerja dengan DuckDB dan Dask belum dilakukan secara langsung, sehingga belum dapat disimpulkan metode mana yang lebih cepat untuk kasus ini.

Keterbatasan yang masih ada adalah belum tersedianya arsip WDI versi sebelumnya untuk analisis revisi antar-snapshot.
## Pembagian kerja
| Anggota | NIM | Komponen | Tugas sampingan | Bagian laporan yang ditulis |
|---|---|---|---|---|
| Afdhal Rahmad Setiawan | 124450126 | Implementasi penyimpanan SQLite, DDL Silver dan Gold, loader SQL, serta tabel rekonsiliasi | Pengujian pipeline, pemeriksaan jumlah baris SQL dan Parquet, serta pemeriksaan hasil rekonsiliasi | Data dan Lineage, Integrasi dan Rekonsiliasi, Validasi dan Reproduksibilitas |