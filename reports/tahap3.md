# Tahap 3 — Pembentukan Grid Panel dan Kelengkapan Data

## 1. Tujuan

Tahap 3 dilakukan untuk membentuk grid panel yang mencakup wilayah dan rentang waktu sesuai dengan cakupan masing-masing seri data. Pembentukan grid bertujuan memastikan struktur data memiliki kombinasi wilayah, tahun, dan rincian kategori yang konsisten sehingga dapat digunakan untuk analisis lebih lanjut.

Selain pembentukan grid, tahap ini juga melakukan pengukuran kelengkapan panel serta mendokumentasikan keputusan penanganan missing data melalui `log-keputusan.csv`.

## 2. Pembentukan Grid

Grid dibentuk dengan mengombinasikan dimensi wilayah, tahun, dan rincian kategori tetap untuk masing-masing seri.

Seri yang digunakan:

| Seri | Rentang Tahun | Cakupan Wilayah | Rincian |
|---|---|---|---|
| Listrik (`var87`) | 1993–2025 | 38 provinsi | Wilayah × tahun |
| Bahan bakar (`sdg7`) | 2001–2021 | 34 wilayah dalam cakupan seri | Wilayah × tahun × 7 kategori bahan bakar |

Untuk seri listrik, grid mencakup seluruh 38 provinsi. Sementara itu, seri bahan bakar menggunakan 34 wilayah yang berada dalam cakupan seri sumber dengan 7 rincian kategori bahan bakar yang tetap agar struktur grid konsisten sepanjang periode pengamatan. Empat provinsi hasil pemekaran yang belum termasuk dalam cakupan seri bahan bakar tidak dipaksakan ke dalam grid historis.

Provinsi hasil pemekaran tidak diberikan nilai historis secara artifisial sebelum wilayah tersebut terbentuk. Sel historis provinsi baru ditandai sebagai `sebelum_provinsi_ada`, sedangkan data wilayah induk tetap dipertahankan sesuai sumber.

Baris agregat Indonesia dipisahkan dari grid provinsi dan tidak dimasukkan ke dalam kombinasi wilayah × tahun. Baris agregat tersebut tetap dipertahankan pada data Silver sesuai aturan yang ditetapkan pada Sprint 0.

## 3. Penanganan Missing Data

Missing data dibedakan menjadi tiga kondisi:

1. **Sebelum provinsi ada (`sebelum_provinsi_ada`)**
   Sel pada provinsi hasil pemekaran sebelum tahun pembentukannya ditandai sebagai kondisi struktural dan tidak dihitung sebagai sel relevan.

2. **Tahun tidak diterbitkan (`tahun_tidak_diterbitkan`)**
   Tahun yang tidak tersedia dalam publikasi sumber ditandai secara terpisah dan tidak dianggap sebagai missing data sejati.

3. **Sel kosong dalam tahun terbit (`sel_kosong_dalam_terbitan`)**
   Sel yang kosong pada tahun yang memang diterbitkan oleh sumber dikategorikan sebagai missing data sejati (`missing_sejati`).

Missing data sejati tidak diisi dengan nilai nol, rata-rata, interpolasi, maupun estimasi lainnya pada tahap ini. Keputusan tersebut diambil untuk menghindari perubahan nilai yang tidak didukung oleh sumber data.

## 4. Keputusan Missing Data

Keputusan penanganan missing data didokumentasikan dalam `log-keputusan.csv`.

| ID Keputusan | Keputusan | Alasan |
|---|---|---|
| K-002 | Data historis provinsi hasil pemekaran tidak di-backcast | Menghindari pembagian atau estimasi data historis yang tidak didukung sumber |
| K-003 | Seri bahan bakar dibatasi pada tahun 2001–2021 | Mengikuti periode ketersediaan seri sumber |
| K-007 | Tahun 2005 pada seri listrik ditandai sebagai tahun tidak diterbitkan | Tahun tersebut tidak tersedia pada sumber, sehingga tidak dianggap sebagai missing sejati |
| K-008 | Tahun 2002–2006 pada seri bahan bakar ditandai sebagai tahun tidak diterbitkan | Tidak terdapat publikasi seri pada periode tersebut |
| K-009 | Sel kosong dalam tahun terbit dipertahankan sebagai missing sejati | Tidak dilakukan imputasi karena tidak terdapat informasi pendukung |
| K-010 | Rincian kategori bahan bakar dibuat tetap | Menjaga konsistensi dimensi grid sepanjang periode |

Keputusan tambahan terkait pemetaan wilayah, alias nama provinsi, pemisahan agregat Indonesia, dan kategori `Jumlah` juga dicatat dalam log keputusan.

### 4.1 Dampak Keputusan terhadap Data

| ID Keputusan | Dampak terhadap Data |
|---|---|
| K-002 | Wilayah hasil pemekaran tidak memiliki data historis sebelum tahun pembentukannya. Data historis tetap menggunakan wilayah induk dan tidak dilakukan backcasting atau pembagian nilai. |
| K-003 | Empat provinsi yang belum tercakup dalam seri bahan bakar dikeluarkan dari grid bahan bakar. |
| K-007 | Tahun 2005 pada seri listrik tidak memiliki sel relevan karena data tidak diterbitkan oleh sumber. |
| K-008 | Tahun 2002–2006 pada seri bahan bakar tidak memiliki data terbitan sehingga tidak dilakukan interpolasi atau pengisian nilai. |
| K-009 | Missing value pada tahun yang diterbitkan tetap dipertahankan. Terdapat 15 sel missing sejati pada seri listrik dan 56 sel missing sejati pada seri bahan bakar. |
| K-010 | Grid bahan bakar menggunakan 7 kategori bahan bakar yang tetap untuk menjaga konsistensi struktur data sepanjang periode pengamatan. |

Dampak keputusan terhadap data juga dicatat dalam `log-keputusan.csv` melalui kolom `dampak_baris`, sehingga perubahan dan pengecualian pada grid dapat ditelusuri.

## 5. Kelengkapan Panel

Kelengkapan panel dihitung dengan membandingkan jumlah sel terisi terhadap jumlah sel relevan pada setiap tahun.

Rumus persentase kelengkapan:

\[
\text{Persentase Kelengkapan}
=
\frac{\text{Jumlah Sel Terisi}}
{\text{Jumlah Sel Relevan}}
\times 100\%
\]

Sel yang termasuk `sebelum_provinsi_ada` dan `tahun_tidak_diterbitkan` tidak dimasukkan ke dalam denominator.

### 5.1 Seri Listrik

Seri listrik memiliki periode pengamatan 1993–2025. Tahun 2005 tidak memiliki sel relevan karena data tidak diterbitkan pada tahun tersebut.

| Tahun | Persentase Terisi |
|---|---:|
| 1993–1999 | 100% |
| 2000 | 88,89% |
| 2001 | 96,67% |
| 2002 | 96,77% |
| 2003–2004 | 93,75% |
| 2005 | Tidak diterbitkan |
| 2006–2012 | 100% |
| 2013–2014 | 97,06% |
| 2015–2022 | 100% |
| 2023 | 89,47% |
| 2024–2025 | 100% |

Rata-rata persentase kelengkapan pada tahun yang diterbitkan adalah sekitar **98,54%**.

Missing data sejati pada seri listrik ditemukan pada tahun 2000, 2001, 2002, 2003, 2004, 2013, 2014, dan 2023.

Jumlah missing data sejati pada seri listrik adalah **15 sel**.

### 5.2 Seri Bahan Bakar

Seri bahan bakar memiliki periode pengamatan 2001–2021. Tahun 2002–2006 tidak diterbitkan oleh sumber sehingga tidak dimasukkan dalam perhitungan kelengkapan.

| Tahun | Persentase Terisi |
|---|---:|
| 2001 | 86,67% |
| 2002–2006 | Tidak diterbitkan |
| 2007–2010 | 100% |
| 2011 | 97,40% |
| 2012 | 100% |
| 2013 | 97,06% |
| 2014 | 94,12% |
| 2015–2020 | 100% |
| 2021 | 99,58% |

Rata-rata persentase kelengkapan pada tahun yang diterbitkan adalah sekitar **98,43%**.

Missing data sejati pada seri bahan bakar ditemukan pada tahun 2001, 2011, 2013, 2014, dan 2021.

Jumlah missing data sejati pada seri bahan bakar adalah **56 sel**.

## 6. Ringkasan Hasil

| Seri | Tahun Terbit | Rata-rata Kelengkapan |
|---|---:|---:|
| Listrik | 32 tahun | 98,54% |
| Bahan bakar | 16 tahun | 98,43% |

Hasil pembentukan grid menunjukkan bahwa sebagian besar sel relevan telah terisi. Missing data yang ditemukan dipertahankan sesuai kondisi sumber dan tidak dilakukan imputasi pada tahap ini.

Kelengkapan panel dihitung dengan mengecualikan sel struktural akibat pemekaran provinsi dan tahun yang tidak diterbitkan. Dengan demikian, persentase kelengkapan mencerminkan ketersediaan data pada sel yang memang relevan untuk dianalisis.

Secara keseluruhan, terdapat 71 sel missing sejati, terdiri atas 15 sel pada seri listrik dan 56 sel pada seri bahan bakar. Missing sejati tersebut dipertahankan tanpa imputasi.

## 7. Artefak

Artefak yang dihasilkan pada tahap ini meliputi:

- `data/silver/grid_listrik.parquet`
- `data/silver/grid_bahan_bakar.parquet`
- `results/124450066/kelengkapan_panel_per_seri.csv`
- `log-keputusan.csv`
- `reports/tahap3.md`

File `kelengkapan_panel_per_seri.csv` memuat jumlah sel grid, jumlah sel relevan, jumlah sel terisi, dan persentase kelengkapan per tahun untuk masing-masing seri.
