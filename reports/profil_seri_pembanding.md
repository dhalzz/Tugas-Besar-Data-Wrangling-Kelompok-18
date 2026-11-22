# Profil Seri Pembanding

## 1. Tujuan

Profil seri pembanding dilakukan untuk memeriksa ketersediaan dan kesesuaian indikator World Development Indicators (WDI) yang berpotensi digunakan sebagai pembanding terhadap seri utama BPS `var87`.

Seri utama `var87` merupakan data persentase rumah tangga menurut wilayah dan sumber penerangan utama dari listrik PLN. Pemeriksaan seri pembanding dilakukan dengan memperhatikan ketersediaan periode, rincian indikator, satuan, definisi indikator, serta tahun yang beririsan dengan seri utama.

Tujuan analisis ini adalah mengidentifikasi seri dan rincian yang berpotensi menjadi pembanding, sekaligus menjelaskan keterbatasan kesesuaiannya agar dapat digunakan secara tepat pada analisis lanjutan.

## 2. Profil Seri Utama

Seri utama yang digunakan dalam pemeriksaan adalah `var87` dari BPS.

| Informasi | Keterangan |
|---|---|
| File | `data/raw/bps/var87_long.csv` |
| Jumlah baris | 1036 |
| Kolom | wilayah, tahun, nilai |
| Periode | 1993–2025 |
| Jumlah tahun tersedia | 32 tahun |
| Tahun yang tersedia | 1993–2004, 2006–2025 |
| Variabel | Persentase rumah tangga menurut wilayah dan sumber penerangan utama dari listrik PLN |

Data `var87` memiliki 32 tahun yang tersedia dalam periode 1993–2025. Tahun 2005 tidak ditemukan dalam data yang diperiksa.

## 3. Ketersediaan Seri Pembanding

Pemeriksaan dilakukan terhadap enam indikator WDI yang berkaitan dengan akses listrik dan penggunaan bahan bakar serta teknologi memasak bersih. Indikator mencakup rincian nasional, perkotaan, dan perdesaan apabila tersedia.

| Kode Indikator | Nama Indikator | Jumlah Observasi | Nilai Tersedia | Periode Nilai Tersedia | Tahun Beririsan dengan var87 |
|---|---|---:|---:|---|---:|
| EG.ELC.ACCS.ZS | Access to electricity (% of population) | 66 | 34 | 1991–2024 | 31 |
| EG.ELC.ACCS.UR.ZS | Access to electricity, urban (% of urban population) | 66 | 34 | 1991–2024 | 31 |
| EG.ELC.ACCS.RU.ZS | Access to electricity, rural (% of rural population) | 66 | 34 | 1991–2024 | 31 |
| EG.CFT.ACCS.ZS | Access to clean fuels and technologies for cooking (% of population) | 66 | 25 | 2000–2024 | 24 |
| EG.CFT.ACCS.UR.ZS | Access to clean fuels and technologies for cooking, urban (% of urban population) | 0 | 0 | Belum tersedia | 0 |
| EG.CFT.ACCS.RU.ZS | Access to clean fuels and technologies for cooking, rural (% of rural population) | 0 | 0 | Belum tersedia | 0 |

Tabel ketersediaan secara lengkap, termasuk tahun yang memiliki nilai dan tahun yang beririsan dengan `var87`, disimpan pada:

- `reports/ketersediaan_seri_pembanding.csv`

### Catatan Ketersediaan Data

- Jumlah observasi menunjukkan jumlah baris yang diperiksa pada file data.
- Jumlah nilai tersedia menunjukkan banyaknya observasi yang memiliki nilai non-null.
- Periode nilai tersedia dihitung berdasarkan tahun yang memiliki nilai, bukan hanya rentang tahun pada seluruh baris observasi.
- Tahun beririsan dihitung berdasarkan tahun yang tersedia pada seri `var87` dan seri pembanding.
- Satuan pada metadata WDI yang diperiksa tercatat kosong. Informasi persentase terdapat pada nama indikator.
- Indikator bahan bakar bersih untuk rincian perkotaan dan perdesaan tercantum dalam metadata, tetapi observasi belum ditemukan pada file yang diperiksa.

## 4. Rincian Indikator yang Tersedia

### 4.1 Akses Listrik

Indikator akses listrik tersedia dalam tiga rincian:

| Kode Indikator | Rincian | Status |
|---|---|---|
| EG.ELC.ACCS.ZS | Nasional | Tersedia |
| EG.ELC.ACCS.UR.ZS | Perkotaan | Tersedia |
| EG.ELC.ACCS.RU.ZS | Perdesaan | Tersedia |

Ketiga indikator memiliki 34 nilai tersedia pada periode 1991–2024, dengan 31 tahun yang beririsan dengan seri utama `var87`.

### 4.2 Bahan Bakar dan Teknologi Memasak Bersih

Indikator bahan bakar dan teknologi memasak bersih tercantum dalam metadata untuk tiga rincian:

| Kode Indikator | Rincian | Status |
|---|---|---|
| EG.CFT.ACCS.ZS | Nasional | Tersedia |
| EG.CFT.ACCS.UR.ZS | Perkotaan | Metadata tersedia, observasi belum ditemukan |
| EG.CFT.ACCS.RU.ZS | Perdesaan | Metadata tersedia, observasi belum ditemukan |

Indikator nasional memiliki 25 nilai tersedia pada periode 2000–2024, dengan 24 tahun yang beririsan dengan seri utama `var87`.

Menurut catatan metadata, indikator ini mengukur proporsi penduduk yang terutama menggunakan bahan bakar dan teknologi memasak bersih. Minyak tanah tidak termasuk bahan bakar memasak bersih berdasarkan pedoman WHO.

Tidak ditemukan rincian berdasarkan jenis kelamin atau kelompok umur pada enam indikator yang menjadi fokus pemeriksaan ini.

## 5. Penilaian Kandidat Pembanding

Pemilihan kandidat pembanding dilakukan berdasarkan kesesuaian konsep indikator, unit analisis, rincian, periode, dan ketersediaan data. Kandidat pembanding tidak hanya ditentukan berdasarkan kesamaan nama indikator, tetapi juga berdasarkan kesesuaian definisi dan cakupan pengukurannya dengan seri utama `var87`.

### 5.1 Indikator Akses Listrik

#### Kandidat Pembanding Utama: EG.ELC.ACCS.ZS

Indikator `EG.ELC.ACCS.ZS` merupakan kandidat pembanding konseptual utama karena sama-sama berkaitan dengan akses listrik.

Indikator WDI tersebut mengukur persentase penduduk yang memiliki akses listrik, sedangkan `var87` mengukur persentase rumah tangga yang menggunakan listrik PLN sebagai sumber penerangan utama.

Dengan demikian, kedua indikator memiliki kesamaan konsep secara umum, tetapi tidak identik dalam definisi dan unit analisis.

| Aspek | var87 | EG.ELC.ACCS.ZS |
|---|---|---|
| Konsep | Sumber penerangan utama rumah tangga | Akses penduduk terhadap listrik |
| Unit analisis | Rumah tangga | Penduduk |
| Pengukuran | Persentase rumah tangga | Persentase penduduk |
| Cakupan | Sumber penerangan utama listrik PLN | Akses terhadap listrik |
| Periode tersedia | 1993–2025 | 1991–2024 |
| Tahun beririsan | - | 31 tahun |

Indikator ini dapat digunakan untuk membandingkan kecenderungan akses listrik secara kontekstual, tetapi nilai keduanya tidak dapat dianggap identik atau dibandingkan secara langsung tanpa mempertimbangkan perbedaan definisi dan unit analisis.

#### Kandidat Konteks Tambahan: EG.ELC.ACCS.UR.ZS dan EG.ELC.ACCS.RU.ZS

Indikator akses listrik perkotaan dan perdesaan dapat digunakan sebagai konteks tambahan untuk melihat perbedaan akses listrik berdasarkan karakteristik wilayah.

Namun, kedua indikator tidak dipilih sebagai pembanding langsung karena seri utama `var87` yang tersedia dalam file pemeriksaan ini tidak memiliki rincian perkotaan dan perdesaan yang sepadan.

| Kode Indikator | Rincian | Status Kandidat | Alasan |
|---|---|---|---|
| EG.ELC.ACCS.UR.ZS | Perkotaan | Konteks tambahan | Menggambarkan akses listrik penduduk perkotaan, tetapi tidak memiliki rincian perkotaan yang sepadan pada `var87`. |
| EG.ELC.ACCS.RU.ZS | Perdesaan | Konteks tambahan | Menggambarkan akses listrik penduduk perdesaan, tetapi tidak memiliki rincian perdesaan yang sepadan pada `var87`. |

### 5.2 Indikator Bahan Bakar dan Teknologi Memasak Bersih

#### EG.CFT.ACCS.ZS

Indikator `EG.CFT.ACCS.ZS` mengukur proporsi penduduk yang terutama menggunakan bahan bakar dan teknologi memasak bersih.

Indikator ini tidak dipilih sebagai pembanding langsung terhadap `var87` karena mengukur penggunaan energi untuk memasak, sedangkan `var87` mengukur sumber penerangan utama rumah tangga.

Oleh karena itu, indikator tersebut hanya dapat digunakan sebagai konteks tambahan untuk menggambarkan kondisi penggunaan energi masyarakat.

| Kode Indikator | Rincian | Status Kandidat | Alasan |
|---|---|---|---|
| EG.CFT.ACCS.ZS | Nasional | Bukan pembanding langsung | Mengukur penggunaan bahan bakar dan teknologi memasak bersih, bukan akses listrik atau sumber penerangan. |
| EG.CFT.ACCS.UR.ZS | Perkotaan | Bukan pembanding langsung | Konsep berbeda dari `var87` dan observasi belum ditemukan pada file yang diperiksa. |
| EG.CFT.ACCS.RU.ZS | Perdesaan | Bukan pembanding langsung | Konsep berbeda dari `var87` dan observasi belum ditemukan pada file yang diperiksa. |

## 6. Ringkasan Pemilihan Seri Pembanding

Berdasarkan pemeriksaan ketersediaan data, definisi indikator, periode, dan rincian, seri `EG.ELC.ACCS.ZS` dipilih sebagai kandidat pembanding konseptual utama untuk `var87`.

Seri `EG.ELC.ACCS.ZS` memiliki 34 nilai tersedia pada periode 1991–2024, dengan 31 tahun beririsan dengan periode data `var87`. Kedua indikator sama-sama berkaitan dengan akses listrik, tetapi memiliki perbedaan unit analisis dan definisi pengukuran. `var87` mengukur persentase rumah tangga yang menggunakan listrik PLN sebagai sumber penerangan utama, sedangkan WDI mengukur persentase penduduk yang memiliki akses listrik. Oleh karena itu, keduanya dapat digunakan untuk membandingkan kecenderungan secara kontekstual, tetapi tidak dianggap identik.

Rincian perkotaan (`EG.ELC.ACCS.UR.ZS`) dan perdesaan (`EG.ELC.ACCS.RU.ZS`) digunakan sebagai informasi tambahan mengenai akses listrik berdasarkan karakteristik wilayah. Rincian tersebut tidak dipilih sebagai pembanding langsung karena `var87` yang tersedia tidak memiliki klasifikasi perkotaan dan perdesaan yang sepadan.

Seri `EG.CFT.ACCS.ZS` tidak dipilih sebagai pembanding langsung karena mengukur akses terhadap bahan bakar dan teknologi memasak bersih, bukan akses listrik atau sumber penerangan. Seri tersebut hanya digunakan sebagai konteks tambahan mengenai kondisi energi.

Dengan demikian, pemilihan kandidat pembanding mempertimbangkan kesesuaian konsep dan ketersediaan periode, serta memperhatikan keterbatasan definisi dan rincian agar hasil perbandingan tidak menimbulkan interpretasi yang keliru.

## 7. Referensi Hasil

Dokumen dan tabel pendukung pemeriksaan seri pembanding tersedia pada folder `reports/`:

- [Tabel ketersediaan seri pembanding](ketersediaan_seri_pembanding.csv)
- [Tabel kandidat rincian pembanding beserta alasan](kandidat_rincian_pembanding.csv)
- [Profil seri pembanding](profil_seri_pembanding.md)

## 8. Kesimpulan

Pemeriksaan seri pembanding menunjukkan bahwa indikator akses listrik WDI merupakan kandidat pembanding konseptual yang paling relevan terhadap seri utama `var87`.

Namun, perbedaan unit analisis dan definisi pengukuran perlu diperhatikan dalam analisis lanjutan. Rincian perkotaan dan perdesaan dapat digunakan sebagai konteks tambahan, sedangkan indikator bahan bakar dan teknologi memasak bersih tidak digunakan sebagai pembanding langsung.

Tabel ketersediaan, periode, rincian indikator, tahun beririsan, serta alasan pemilihan kandidat pembanding telah disediakan untuk mendukung peninjauan dan pemilihan seri yang sesuai pada tahap analisis berikutnya.