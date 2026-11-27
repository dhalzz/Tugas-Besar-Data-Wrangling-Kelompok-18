# Aturan Pembentukan Tabel Nasional Gold

## 1. Tujuan

Tabel nasional Gold menyimpan seri utama BPS dan seri pembanding World Development Indicators (WDI) untuk analisis akses energi di Indonesia.

## 2. Seri yang Digunakan

| Seri | Peran | Sumber |
|---|---|---|
| var87 | Utama | BPS |
| tabel:sdg7_bahan_bakar | Utama | BPS |
| EG.ELC.ACCS.ZS | Pembanding | WDI |
| EG.CFT.ACCS.ZS | Pembanding | WDI |

## 3. Aturan Pemilihan Angka Nasional

Angka utama BPS diambil dari baris Indonesia dengan kode wilayah 9999.

Nilai provinsi tidak dijumlahkan atau dirata-ratakan untuk membentuk angka nasional. Alasannya, agregasi memerlukan dasar pembobotan dan definisi statistik yang sesuai. Tanpa dasar tersebut, agregasi berisiko menghasilkan angka nasional yang tidak sebanding dengan angka resmi BPS.

Apabila suatu periode memiliki data provinsi tetapi tidak memiliki baris Indonesia, proses pembentukan tabel nasional harus gagal dan menampilkan periode yang bermasalah. Kondisi ini ditangani melalui pemeriksaan pada fungsi `_utama()`.

## 4. Aturan Seri Bahan Bakar

Seri `tabel:sdg7_bahan_bakar` mempertahankan rincian kategori bahan bakar, yaitu Arang/Briket, Gas/Elpiji, Kayu, Lainnya, Listrik, dan Minyak Tanah.

Kategori tidak digabungkan menjadi satu nilai karena masing-masing menunjukkan komposisi sumber bahan bakar rumah tangga.

Baris dengan rincian `Jumlah` tidak dimasukkan ke tabel nasional akhir. Sebagai gantinya, jumlah seluruh kategori diperiksa terhadap nilai total dengan toleransi 0,05 poin persentase.

## 5. Aturan Seri Pembanding WDI

Seri pembanding hanya mengambil observasi Indonesia dengan kode negara `IDN`.

- `EG.ELC.ACCS.ZS` dipasangkan dengan `var87`.
- `EG.CFT.ACCS.ZS` dipasangkan dengan `tabel:sdg7_bahan_bakar`.

Nilai yang kosong pada sumber WDI tidak dimasukkan ke tabel nasional. Perbedaan definisi, cakupan, dan denominator antara BPS dan WDI tetap harus diperhatikan dalam interpretasi.

## 6. Kunci dan Lineage

Kunci unik tabel adalah kombinasi:

`periode + seri_kode + rincian`

Kolom `_berkas_raw` dan `_sha256_raw` dipertahankan untuk menelusuri sumber setiap angka.

Setiap baris wajib memiliki `_berkas_raw` yang tidak kosong.

## 7. Validasi

Pembentukan tabel nasional memeriksa:

1. Kelengkapan seri utama dan seri pembanding.
2. Ketersediaan baris Indonesia untuk periode yang memiliki observasi provinsi.
3. Kesesuaian jumlah kategori bahan bakar terhadap total.
4. Keunikan kombinasi periode, seri, dan rincian.
5. Kelengkapan lineage sumber data.
