# Profil Seri Pembanding

## 1. Tujuan

Profil ini dibuat untuk memeriksa ketersediaan seri pembanding
terhadap seri utama BPS `var87`, yaitu persentase rumah tangga
menurut wilayah dan sumber penerangan utama dari listrik PLN.

Pemeriksaan mencakup periode, rincian indikator, satuan,
dan irisan tahun dengan seri utama.

## 2. Profil seri utama

- File: `data/raw/bps/var87_long.csv`
- Jumlah baris: 1036
- Kolom: wilayah, tahun, nilai
- Periode tahun: 1993-2025
- Jumlah tahun yang memiliki data: 32
- Tahun yang tersedia: 1993, 1994, 1995, 1996, 1997, 1998, 1999, 2000, 2001, 2002, 2003, 2004, 2006, 2007, 2008, 2009, 2010, 2011, 2012, 2013, 2014, 2015, 2016, 2017, 2018, 2019, 2020, 2021, 2022, 2023, 2024, 2025

## 3. Ketersediaan seri pembanding

| Kode | Nama indikator | Seluruh observasi | Bernilai | Periode | Tahun beririsan |
|---|---|---:|---:|---|---:|
| EG.ELC.ACCS.ZS | Access to electricity (% of population) | 66 | 34 | 1991-2024 | 31 |
| EG.ELC.ACCS.UR.ZS | Access to electricity, urban (% of urban population) | 66 | 34 | 1991-2024 | 31 |
| EG.ELC.ACCS.RU.ZS | Access to electricity, rural (% of rural population) | 66 | 34 | 1991-2024 | 31 |
| EG.CFT.ACCS.ZS | Access to clean fuels and technologies for cooking (% of population) | 66 | 25 | 2000-2024 | 24 |
| EG.CFT.ACCS.UR.ZS | Access to clean fuels and technologies for cooking, urban (% of urban population) | 0 | 0 | Belum tersedia | 0 |
| EG.CFT.ACCS.RU.ZS | Access to clean fuels and technologies for cooking, rural (% of rural population) | 0 | 0 | Belum tersedia | 0 |

Catatan:
- Satuan pada metadata WDI tercatat kosong.
- Informasi persentase tercantum pada nama indikator.
- Periode dihitung dari tahun yang memiliki nilai, bukan sekadar
  rentang tahun pada seluruh baris observasi.
- Tahun beririsan dihitung terhadap tahun yang tersedia pada var87.

## 4. Rincian indikator

Indikator akses listrik tersedia dalam tiga rincian:
nasional, perkotaan, dan perdesaan.

Indikator bahan bakar bersih juga tercantum dalam metadata
untuk rincian nasional, perkotaan, dan perdesaan. Namun,
pada file observasi yang diperiksa, hanya indikator nasional
yang ditemukan.

Tidak ditemukan rincian berdasarkan jenis kelamin atau kelompok
umur pada enam indikator yang menjadi fokus pemeriksaan ini.

## 5. Penilaian kandidat pembanding

### Akses listrik

`EG.ELC.ACCS.ZS` merupakan kandidat pembanding konseptual
karena sama-sama berkaitan dengan akses listrik.

Namun, kedua indikator tidak identik:
- `var87` menggunakan rumah tangga sebagai dasar pengukuran
  dan khusus mengukur sumber penerangan utama dari listrik PLN.
- WDI mengukur persentase penduduk yang memiliki akses listrik.

Indikator perkotaan dan perdesaan dapat digunakan sebagai
konteks tambahan. Keduanya tidak dapat langsung dipasangkan
dengan rincian var87 karena var87 dalam file ini dibagi
berdasarkan wilayah, bukan klasifikasi perkotaan/perdesaan.

### Bahan bakar bersih

Indikator `EG.CFT.ACCS.ZS` mengukur proporsi penduduk yang
terutama menggunakan bahan bakar dan teknologi memasak bersih.
Menurut catatan metadata, minyak tanah tidak termasuk bahan
bakar memasak bersih berdasarkan pedoman WHO.

Indikator ini bukan pembanding langsung untuk var87 karena
mengukur penggunaan energi untuk memasak, bukan sumber
penerangan atau akses listrik. Indikator ini hanya dapat
digunakan sebagai konteks tambahan mengenai kondisi energi.

## 6. Kesimpulan

Seri akses listrik WDI merupakan kandidat pembanding konseptual
yang paling relevan, tetapi perbedaan unit analisis dan definisi
harus diperhatikan dalam analisis lanjutan.

Rincian perkotaan dan perdesaan dapat menjadi konteks tambahan,
sedangkan seri bahan bakar bersih tidak digunakan sebagai
pembanding langsung.

Hasil ini dapat menjadi dasar pemilihan rincian yang sebanding
pada tahap 6.
