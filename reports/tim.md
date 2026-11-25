# Laporan tim — <Nama tim>, kasus <NN> <judul kasus>

Satu dokumen bersama, enam bagian. Angka harus dapat ditarik ulang dari `data/silver`, `data/gold`,
dan `log-keputusan.csv` yang sudah di-*commit*.

## Ringkasan
Kasus, seri yang ditangani, dan satu kalimat temuan utama tentang kualitas datanya.

## Data dan lineage
Sumber dan format mentah, jumlah berkas, cara `_berkas_raw`/`_sha256_raw` dibentuk, dan hasil tarik
ulang API (bila dilakukan): apa yang berubah sejak snapshot 17–20 Oktober 2026.

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
Seri utama vs pembanding nasional: selisih, penjelasannya (definisi, metode, vintage, granularitas),
dan hasil analisis revisi dari arsip WDI.

## Validasi dan reproduksibilitas
Skema validasi (aturan, hasil lolos/gagal), waktu `python pipeline.py` dari nol, perbandingan pandas
vs DuckDB/Dask, dan keterbatasan yang tersisa.

## Pembagian kerja
| Anggota | NIM | Komponen | Tugas sampingan | Bagian laporan yang ditulis |
|---|---|---|---|---|
