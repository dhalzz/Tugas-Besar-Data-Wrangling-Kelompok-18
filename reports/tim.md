# Laporan tim — <Nama tim>, kasus <NN> <judul kasus>

Satu dokumen bersama, enam bagian. Angka harus dapat ditarik ulang dari `data/silver`, `data/gold`,
dan `log-keputusan.csv` yang sudah di-*commit*.

## Ringkasan
Kasus, seri yang ditangani, dan satu kalimat temuan utama tentang kualitas datanya.

## Data dan lineage
Sumber dan format mentah, jumlah berkas, cara `_berkas_raw`/`_sha256_raw` dibentuk, dan hasil tarik
ulang API (bila dilakukan): apa yang berubah sejak snapshot 17–20 Oktober 2026.

## Masalah data dan penanganannya

Temuan Sprint 1 berasal dari Silver (4.830 baris) dan `log-keputusan.csv` (K-001 s.d. K-021). Setiap angka dapat dihitung ulang dengan `hitung_ulang_tim.py`.

| Masalah | Temuan dan jumlah terdampak | Penanganan | Alternatif ditolak | Log |
|---|---|---|---|---|
| Celah panel: tahun tidak diterbitkan | Listrik tahun 2005: 38 sel (38 provinsi x 1 tahun). Bahan bakar tahun 2002-2006: 1.190 sel (5 tahun x 238 sel). | Ditandai `tahun_tidak_diterbitkan`, bukan missing sejati; tidak diimputasi. | imputasi/interpolasi 2005 dari 2004 & 2006 (K-007); imputasi/interpolasi 2002-2006 (K-008) | K-007, K-008 |
| Celah panel: provinsi belum ada | Listrik 202 sel (12 provinsi). Bahan bakar 133 sel (4 provinsi), 70 di antaranya pada tahun terbit. | Dikosongkan sebelum `tahun_mulai`; provinsi induk memakai nilai historis penuh. | (a) backcast proporsional; (b) membagi nilai induk; (c) mengisi rata-rata (K-002); memasukkan 4 provinsi 2023 ke grid lalu menandainya missing (K-003) | K-002, K-003 |
| Missing sejati | Bahan bakar 56 sel (2001: 28, 2011: 6, 2013: 7, 2014: 14, 2021: 1; terbanyak: Kalimantan Utara 14, Maluku 9, Aceh 8, Maluku Utara 8). Listrik 15 sel. Selisih baris CSV mentah (3.920) dan Silver (3.794) = 126 = 56 missing sejati + 70 sel provinsi belum ada. | Dipertahankan sebagai kosong, tidak diimputasi. | mengisi dengan 0 atau rata-rata (K-009) | K-009 |
| Kandidat anomali | var87: 42 kandidat (`reports/calon_anomali_var87.csv`). Bahan bakar: 104 kandidat (`reports/calon_anomali_bahan_bakar.csv`). Nilai Raw BPS dan Silver identik. | Seluruhnya ditinjau dan dikategorikan kandidat anomali lokal; tidak ada nilai diubah atau dihapus. | Menghapus, mengubah, atau menginterpolasi nilai yang mengalami perubahan drastis (K-011); Menghapus, mengubah, atau menginterpolasi nilai yang mengalami perubahan drastis (K-012); Menghapus, mengubah, atau menginterpolasi nilai (K-013); Menghapus, mengubah, atau menginterpolasi nilai (K-014); Menghapus, mengubah, atau menginterpolasi nilai Aceh tahun 2003 (K-019); Mengoreksi, menghapus, atau menginterpolasi nilai kandidat anomali tanpa bukti galat input atau patahan seri. (K-020); Mengoreksi atau menghapus kandidat anomali berdasarkan profil statistik tanpa bukti galat input atau patahan seri. (K-021) | K-011 s.d. K-014, K-019 s.d. K-021 |
| Patahan seri | Perubahan >10 poin per tahun pada var87 (jumlah wilayah dari 39): 1997: 1, 1998: 1, 2002: 3, 2003: 4, 2009: 1, 2010: 3, 2024: 1. Terbanyak 4 wilayah pada 2003. | Tidak ada indikasi patahan serentak; nilai dipertahankan. | Mengategorikan perubahan ekstrem sebagai patahan seri nasional atau galat input tanpa bukti pendukung (K-017) | K-017 |
| Revisi antar-snapshot | Snapshot Raw BPS tersedia: 1 (2026-10-17). | Audit revisi belum dapat dilakukan; aturan deduplikasi ditetapkan. | Membandingkan revisi antar-snapshot tanpa snapshot pembanding (K-016); Menghapus data hanya karena angka sama antar-snapshot atau menghapus revisi data tanpa pemeriksaan (K-018) | K-016, K-018 |
| Koreksi katalog wilayah dan rincian | 39 wilayah di Silver; baris INDONESIA: 144; baris rincian Jumlah: 545. | Nama distandarkan lewat `dim_provinsi_38`; alias Bangka Belitung dan Kepulauan Riau disatukan; INDONESIA dan Jumlah dipisah dari grid. | Join memakai nama mentah tanpa kode; memakai nama huruf kapital apa adanya sebagai nama tampilan; menghapus baris INDONESIA (K-001); membiarkan tidak terpetakan (baris hilang) (K-004); memasukkan INDONESIA ke sumbu provinsi (K-005); menggabungkan Jumlah dengan jenis (double count) (K-006) | K-001, K-004 s.d. K-006 |

### Temuan terpenting (bahan demo Sprint 1)

1. Tidak semua sel kosong adalah data hilang: dari 126 baris yang hilang di bahan bakar, hanya 56 yang missing sejati.
2. Tahun tidak terbit (listrik 2005; bahan bakar 2002-2006) dibedakan dari missing, sehingga tidak diimputasi.
3. Lonjakan ekstrem hanya menyangkut sedikit wilayah (maksimum 4 dari 39 pada 2003), jadi bukan patahan seri.
4. Hanya 1 snapshot Raw BPS, sehingga revisi antar-snapshot belum dapat diaudit.

### Cara menarik ulang angka

Jalankan `python hitung_ulang_tim.py <folder berisi data/silver dan log-keputusan.csv>`; `python bangun_draf_masalah.py <folder yang sama>` menulis ulang tabel ini.

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
