# Laporan tim — <Nama tim>, kasus <18> <judul kasus>

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
- `gold_panel`: `PRIMARY KEY (wilayah_kode, periode, indikator)`
- `gold_nasional`: `PRIMARY KEY (periode, seri_kode, rincian)`
- `gold_rekonsiliasi`: `PRIMARY KEY (pasangan, periode)`

Tabel `gold_panel` menyimpan panel provinsi × tahun × indikator hasil transformasi Silver. Kolomnya meliputi `wilayah_kode`, `nama_provinsi`, `periode`, `indikator`, `nilai`, `satuan`, `_lineage_silver`, dan `status_data`.

**Perbandingan dengan penyimpanan dokumen JSON mentah:**
- **Lapis Bronze (data mentah di `data/raw/`):** Cocok disimpan sebagai dokumen JSON/CSV mentah apa adanya. Struktur respons WebAPI BPS (HTML yang di-*escape* maupun `datacontent`) dan API World Bank (array `[header, records]` bersarang) bersifat heterogen antar-sumber. Menyimpan dokumen mentah mempertahankan bentuk asli sumber untuk auditabilitas dan verifikasi sidik SHA-256 (`MANIFEST.csv`).
- **Lapis Silver dan Gold (`gold.sqlite` + Parquet):** Cocok disimpan dalam basis data relasional SQLite (dan Parquet untuk pertukaran analitik). Pada lapis ini, skema sudah seragam dan terstruktur; tipe data numerik (`REAL`, `INTEGER`) dan teks (`TEXT`) terdefinisi jelas, serta **Primary Key** menjamin keunikan observasi (mencegah duplikasi baris saat penggabungan maupun pemuatan ulang). Kueri lintas tabel (*JOIN* seri utama vs pembanding nasional, agregasi per provinsi/tahun) jauh lebih cepat, ringkas, dan dapat divalidasi langsung dibanding mem-parsing ulang dokumen JSON bersarang.
- **Alasan memilih SQLite dibanding server terpisah (PostgreSQL):** SQLite bersifat *serverless*, terintegrasi langsung di pustaka standar Python (`sqlite3`), dan tersimpan dalam satu berkas lokal yang dibangun ulang otomatis oleh `python pipeline.py` (tidak di-*commit* ke repositori), sehingga memenuhi syarat reproduksi dari nol di laptop biasa tanpa konfigurasi layanan tambahan.

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
Rekonsiliasi tingkat nasional menyandingkan seri utama BPS (menggunakan baris `INDONESIA` berkode `9999`, tanpa agregasi provinsi; `K-031`) dengan seri pembanding World Development Indicators (WDI) dari `data/gold/tabel_nasional.parquet` (187 baris; `K-033` s.d. `K-035`). Hasilnya disimpan pada `data/gold/tabel_rekonsiliasi.parquet` dan `data/gold/tabel_rekonsiliasi.csv` (60 baris total: 47 baris berpasangan dan 13 baris tanpa pasangan; `K-036`, `K-037`), serta dimuat ke tabel `gold_rekonsiliasi` pada `data/gold/gold.sqlite`. Selisih dihitung sebagai `nilai_utama - nilai_pembanding` (dalam poin persentase) dan **tidak dihapus atau disesuaikan** agar perbedaan antar-sumber tetap transparan (`K-035`, `K-037`).

### Pasangan yang dibandingkan
| Pasangan | Seri utama (BPS) | Seri pembanding (WDI) | Periode tersedia | Total baris | Berpasangan | Tanpa pasangan | Log |
|---|---|---|---|---:|---:|---:|---|
| `listrik` | `var87`: persentase rumah tangga dengan sumber penerangan utama listrik PLN (Susenas Maret) | `EG.ELC.ACCS.ZS`: persentase penduduk dengan akses listrik dari seluruh sumber | BPS: 1993–2025 (32 tahun, tanpa 2005); WDI: 1991–2024 (34 tahun; 32 dari 66 baris mentah kosong dikeluarkan) | 35 | 31 (1993–2004, 2006–2024) | 4 (1991, 1992, 2005 hanya WDI; 2025 hanya BPS) | K-031, K-034, K-035 |
| `bahan_bakar_bersih` | `tabel:sdg7_bahan_bakar (Listrik + Gas/Elpiji)`: penjumlahan rincian `Listrik` dan `Gas/Elpiji` (% rumah tangga); mengecualikan `Minyak Tanah`, `Kayu`, `Arang/Briket`, `Lainnya`, dan `Jumlah` | `EG.CFT.ACCS.ZS`: persentase penduduk dengan bahan bakar dan teknologi memasak bersih (pedoman WHO / Tracking SDG 7; mengecualikan minyak tanah) | BPS: 2001, 2007–2021 (16 tahun terbit; 96 baris rincian di `tabel_nasional`); WDI: 2000–2024 (25 tahun; 41 dari 66 baris mentah kosong dikeluarkan) | 25 | 16 (2001, 2007–2021) | 9 (2000, 2002–2006, 2022–2024 hanya WDI) | K-032, K-034, K-036 |

### Besar selisih (`nilai_utama - nilai_pembanding`)
| Pasangan | Baris berpasangan | Arah selisih | Minimum (periode; BPS vs WDI) | Maksimum (periode; BPS vs WDI) | Rata-rata selisih | Median selisih | Rata-rata \|selisih\| |
|---|---:|---|---|---|---|---|---|
| `listrik` | 31 | 31 negatif, 0 positif (`var87` selalu di bawah WDI) | -6,53 poin (1997; 73,77% vs 80,30%) | -0,05 poin (2020; 96,95% vs 97,00%) | -2,97 poin | -2,82 poin | 2,97 poin |
| `bahan_bakar_bersih` | 16 | 8 negatif, 8 positif | -9,57 poin (2007; 12,43% vs 22,00%) | +5,14 poin (2001; 11,14% vs 6,00%) | -0,77 poin | -0,02 poin | 2,23 poin |

- **Pasangan `listrik`:** Selisih terbesar terjadi pada awal seri (`1997`: -6,53 poin; `1994`: -5,29 poin), kemudian menyempit seiring naiknya elektrifikasi nasional menjadi -2,27 s.d. -1,47 poin pada 2021–2024 (`2021`: -1,94; `2022`: -2,27; `2023`: -1,47; `2024`: -1,66; sejalan dengan catatan `K-035`).
- **Pasangan `bahan_bakar_bersih`:** Selisih absolut terbesar muncul pada awal seri dan transisi cepat elpiji (`2001`: +5,14 poin; `2007`: -9,57 poin; `2008`: -8,26 poin). Mulai 2009–2021, kedua seri bergerak sangat rapat dengan selisih antara -1,88 poin (`2021`) hingga +1,97 poin (`2009`), dan selisih absolut terkecil 0,23 poin pada 2016 (73,23% vs 73,00%).

### Penjelasan setiap kategori rekonsiliasi
| Kategori (`kategori_penjelasan`) | Jumlah baris | Pasangan & periode | Rentang selisih (rata-rata; median) | Penjelasan |
|---|---:|---|---|---|
| `definisi berbeda` | 41 | `listrik`: 28 baris (1993–1999, 2003–2004, 2006–2024); `bahan_bakar_bersih`: 13 baris (2009–2021) | `listrik`: -6,53 s.d. -0,05 (-3,03; -2,86); `bahan_bakar_bersih`: -1,88 s.d. +1,97 (+0,02; +0,23) | Perbedaan definisi konsep dan denominator. `var87` hanya menghitung penerangan utama listrik PLN per rumah tangga, sedangkan `EG.ELC.ACCS.ZS` menghitung seluruh sumber listrik per penduduk. Pada bahan bakar bersih, agregat BPS (`Listrik + Gas/Elpiji`) berdenominator rumah tangga, sedangkan `EG.CFT.ACCS.ZS` berdenominator penduduk dan memakai model Tracking SDG 7/WHO. |
| `cakupan berbeda` | 3 | `listrik`: 3 baris (2000, 2001, 2002) | -2,82 s.d. -2,22 (-2,46; -2,33) — `2000`: -2,33; `2001`: -2,82; `2002`: -2,22 | Catatan Susenas BPS pada periode tersebut memiliki cakupan pencacahan wilayah tidak penuh: 2000 tidak mencacah Aceh dan Maluku, 2001 tanpa Aceh, dan 2002 hanya ibu kota provinsi untuk Aceh, Maluku, Maluku Utara, serta Papua—ditambah perbedaan definisi PLN/rumah tangga vs seluruh listrik/penduduk. |
| `metode berbeda` | 3 | `bahan_bakar_bersih`: 3 baris (2001, 2007, 2008) | -9,57 s.d. +5,14 (-4,23; -8,26) — `2001`: +5,14; `2007`: -9,57; `2008`: -8,26 | Terjadi pada awal seri dan masa transisi cepat konversi minyak tanah ke elpiji (pada `tabel_nasional`, `Gas/Elpiji` naik dari 10,57% pada 2007 menjadi 18,68% pada 2008 dan 35,54% pada 2009, sementara `Minyak Tanah` turun dari 36,57% ke 30,89% dan 18,14%). BPS mencatat hasil survei Susenas tahunan langsung, sedangkan WDI/WHO memakai estimasi model yang dimuluskan (*smoothed*). |
| `vintage berbeda` | 0 | — | — | Kategori disediakan dalam skema (`src/gold/rekonsiliasi.py`), namun belum dapat diuji karena hanya tersedia satu snapshot WDI (20 Oktober 2026) dan satu snapshot BPS (17 Oktober 2026). |
| `belum terjelaskan` | 0 | — | — | Seluruh 47 baris berpasangan telah terklasifikasi ke kategori di atas. |
| *(Tanpa kategori / tidak berpasangan)* | 13 | `listrik`: 4 baris (1991, 1992, 2005, 2025); `bahan_bakar_bersih`: 9 baris (2000, 2002–2006, 2022–2024) | Selisih kosong | Salah satu sumber tidak menerbitkan data pada periode tersebut (`var87` tidak terbit pada 1991–1992 dan 2005; WDI `EG.ELC.ACCS.ZS` belum terbit untuk 2025; `sdg7_bahan_bakar` hanya terbit 2001 dan 2007–2021). Baris tetap dipertahankan dengan selisih kosong (`K-037`). |

Analisis revisi antar-snapshot WDI belum dapat dilakukan karena arsip rilis WDI versi sebelumnya belum tersedia pada paket data yang diperiksa. Oleh karena itu, rekonsiliasi menggunakan snapshot WDI tanggal 20 Oktober 2026 sebagai pembanding, dan pengaruh perubahan revisi antarversi (`vintage berbeda`) menjadi keterbatasan yang dicatat untuk tahap skala berikutnya.

### Temuan terpenting (bahan demo Sprint 2)
1. **Akses listrik BPS selalu di bawah WDI:** Pada semua 31 tahun berpasangan (1993–2004, 2006–2024), `var87` lebih rendah 0,05 s.d. 6,53 poin (rata-rata -2,97 poin) karena hanya mencakup listrik PLN per rumah tangga, sedangkan WDI mencakup seluruh sumber listrik per penduduk.
2. **Transisi konversi minyak tanah ke elpiji memicu selisih metode terbesar:** Selisih bahan bakar bersih memuncak hingga -9,57 poin (2007) dan -8,26 poin (2008) akibat perbedaan survei langsung BPS vs kurva model *smoothed* WDI/WHO saat transisi cepat, lalu menyempit ke -1,88 s.d. +1,97 poin pada 2009–2021.
3. **Cakupan Susenas 2000–2002 terdokumentasi eksplisit:** Tiga baris berpasangan listrik pada 2000–2002 dipisahkan ke kategori `cakupan berbeda` (selisih -2,22 s.d. -2,82 poin) sesuai catatan pencacahan tidak penuh pada wilayah Aceh, Maluku, Maluku Utara, dan Papua.
4. **Tidak ada koreksi paksa antar-sumber:** Seluruh 47 baris berpasangan dijelaskan per kategori dan 13 periode tanpa pasangan tetap dipertahankan dengan selisih kosong (`K-037`).

### Cara menarik ulang angka
Seluruh angka pada bagian ini dapat ditarik langsung dari `data/gold/tabel_rekonsiliasi.csv` (atau `.parquet`), `data/gold/tabel_nasional.csv` (atau `.parquet`), dan `log-keputusan.csv` (`K-031` s.d. `K-037`), atau dibentuk ulang dari nol melalui `python pipeline.py` (`src/gold/nasional.py` dan `src/gold/rekonsiliasi.py`).

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
| Faizatun Najmi | 124450126 | Transformasi data Silver menjadi panel Gold provinsi × tahun × indikator, termasuk agregasi bahan bakar dan lineage | Pengujian pipeline, pemeriksaan keunikan kunci panel, pemeriksaan missing data, dan verifikasi hasil Gold | Transformasi dan Panel Gold, Masalah Data dan Penanganannya, Validasi Hasil Gold |
