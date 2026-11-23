# Laporan tim — <Nama tim>, kasus <NN> <judul kasus>

Satu dokumen bersama, enam bagian. Angka harus dapat ditarik ulang dari `data/silver`, `data/gold`,
dan `log-keputusan.csv` yang sudah di-*commit*.

## Ringkasan
Kasus, seri yang ditangani, dan satu kalimat temuan utama tentang kualitas datanya.

## Data dan lineage
Sumber dan format mentah, jumlah berkas, cara `_berkas_raw`/`_sha256_raw` dibentuk, dan hasil tarik
ulang API (bila dilakukan): apa yang berubah sejak snapshot 17–20 Oktober 2026.

## Masalah data dan penanganannya

Pemeriksaan awal terhadap data mentah menemukan beberapa masalah kualitas data berupa nilai kosong, celah panel, perubahan cakupan wilayah, patahan nilai, dan perbedaan penamaan wilayah. Temuan berikut masih bersifat **provisional** karena tahap Silver belum selesai. Angka diambil dari pemeriksaan CSV dan JSON sumber, sedangkan keputusan standardisasi wilayah mengacu pada `log-keputusan.csv`.

| Masalah | Temuan dan jumlah terdampak | Penanganan | Alternatif yang ditolak |
|---|---|---|---|
| Missing value pada seri SDG 7 bahan bakar | Ditemukan 126 nilai kosong dari 3.920 baris (3,21%). Missing paling terkonsentrasi di Kalimantan Utara sebanyak 63 nilai. | Nilai kosong dipertahankan sebagai missing dan tidak diimputasi karena belum ditemukan dasar untuk menentukan nilai pengganti. | Mengisi nilai kosong dengan nol atau interpolasi tanpa dasar sumber. |
| Celah panel seri listrik PLN | Tahun 2005 tidak tersedia pada seri yang diperiksa. Jumlah wilayah juga berubah sepanjang periode pengamatan. | Tahun yang tidak tersedia dicatat sebagai celah panel. Perubahan cakupan wilayah dipertahankan dan perlu ditelusuri berdasarkan metadata sumber. | Menganggap tahun yang tidak tersedia sebagai nilai nol atau menyamakan cakupan wilayah antarperiode tanpa dasar. |
| Perubahan cakupan wilayah | Jumlah wilayah pada seri listrik PLN berubah dari 27 wilayah pada 1993–1999, menjadi 25 pada 2000, 30 pada 2001, 31 pada 2002–2004, 34 pada 2006–2014, 35 pada 2015–2023, dan 39 pada 2024–2025. | Perubahan jumlah dan nama wilayah dicatat sebagai perubahan cakupan panel. Penambahan wilayah tidak langsung dianggap sebagai kesalahan data. | Memaksakan panel seimbang dengan menghapus wilayah atau menambahkan nilai yang tidak tersedia. |
| Patahan/anomali nilai seri listrik PLN | Ditemukan perubahan besar antarperiode pada beberapa wilayah, antara lain Papua (100 pada 2002 menjadi 37,89 pada 2003), Maluku (100 pada 2002 menjadi 63,79 pada 2003), Maluku Utara (91,65 pada 2002 menjadi 49,26 pada 2003), dan Kepulauan Riau (57,69 pada 2009 menjadi 86,14 pada 2010). | Nilai diperiksa terhadap JSON sumber. Nilai pada titik-titik yang diperiksa sesuai dengan JSON sehingga tidak dikoreksi atau dihapus secara otomatis. Temuan tetap ditandai untuk verifikasi substantif terhadap definisi dan cakupan indikator. | Menghapus outlier atau mengubah nilai hanya berdasarkan besarnya perubahan antarperiode. |
| Standardisasi wilayah dan koreksi katalog | Nama wilayah pada data mentah berpotensi berbeda ejaan dan format antarseri. Terdapat agregat `INDONESIA` yang bukan wilayah provinsi. | Mengacu pada keputusan K-001: menggunakan tabel acuan `dim_provinsi_38`, kode BPS dua digit bertipe teks sebagai kunci utama, nama resmi Title Case, kunci wilayah uppercase tanpa tanda baca, dan slug lowercase dengan underscore. `INDONESIA` diperlakukan sebagai agregat nasional, bukan provinsi. | Join menggunakan nama mentah; menggunakan nama uppercase sebagai nama tampilan; menghapus baris `INDONESIA`. |
| Dampak keputusan katalog K-001 | Keputusan K-001 pada `log-keputusan.csv` menyatakan `JUMLAH_BARIS` tidak berubah. | Tidak ada baris ditambahkan atau dihapus. Agregasi dilakukan pada tahap Gold. | Menghapus agregat nasional dari data mentah atau mengubah jumlah baris pada tahap Silver. |

**Keterbatasan pemeriksaan:** Temuan di atas berasal dari pemeriksaan data mentah. Pemeriksaan duplikat, validasi skema Silver, dan penarikan ulang seluruh angka dari Silver belum dapat dinyatakan selesai sampai pipeline Silver berhasil dijalankan. Oleh karena itu, angka-angka ini perlu diverifikasi kembali setelah Silver terbentuk.
## Integrasi dan rekonsiliasi
Seri utama vs pembanding nasional: selisih, penjelasannya (definisi, metode, vintage, granularitas),
dan hasil analisis revisi dari arsip WDI.

## Validasi dan reproduksibilitas
Skema validasi (aturan, hasil lolos/gagal), waktu `python pipeline.py` dari nol, perbandingan pandas
vs DuckDB/Dask, dan keterbatasan yang tersisa.

## Pembagian kerja
| Anggota | NIM | Komponen | Tugas sampingan | Bagian laporan yang ditulis |
|---|---|---|---|---|
