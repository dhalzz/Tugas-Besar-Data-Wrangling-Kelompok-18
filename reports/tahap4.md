# Laporan Tahap 4 – Pembentukan Gold

## 1. Tujuan
Tahap 4 bertujuan membentuk data Gold dalam bentuk panel provinsi × periode × indikator dari data Silver. Pembentukan dilakukan melalui fungsi pada modul `src/gold` dan dijalankan melalui `pipeline.py`.

## 2. Aturan Pemilihan Data

### 2.1 Pemilihan Snapshot
Pemilihan snapshot dilakukan berdasarkan tanggal pada jalur berkas raw. Jika terdapat beberapa snapshot untuk kunci provinsi, periode, seri, dan rincian yang sama, snapshot terbaru dipilih.

Pada data yang tersedia, hanya terdapat satu snapshot Raw BPS bertanggal 2026-10-17. Oleh karena itu, seluruh 4.830 baris Silver terpilih dan tidak ada baris yang dikeluarkan akibat perbedaan snapshot.

### 2.2 Pemilihan Periode
Gold menggunakan data dengan jenis periode tahunan. Data semesteran, triwulanan, atau bulanan tidak dikonversi secara langsung karena belum tersedia aturan agregasi yang disepakati. Seluruh 4.830 baris Silver yang tersedia saat ini merupakan data tahunan.

### 2.3 Pemetaan Rincian Bahan Bakar
Rincian bahan bakar dikelompokkan menjadi:
- Bahan bakar bersih: Listrik dan Gas/Elpiji.
- Bahan bakar tidak bersih: Kayu, Arang/Briket, dan Minyak Tanah.
- Lainnya: tidak diklasifikasikan ke dalam panel agregat.
- Jumlah: dikecualikan karena merupakan total, bukan kategori bahan bakar.

Sebanyak 1.090 baris Silver tidak digunakan sebagai komponen panel agregat, terdiri atas 545 baris Lainnya dan 545 baris Jumlah. Kedua rincian tersebut tetap dipertahankan dalam Silver.

### 2.4 Pembentukan Agregat
Komponen bahan bakar yang terpilih diagregasikan menjadi indikator bahan bakar bersih dan tidak bersih. Agregasi dilakukan berdasarkan provinsi dan tahun. Jika komponen yang diperlukan tidak lengkap, nilai agregat diperlakukan sebagai missing dan penandanya tetap dipertahankan.

Sebanyak 2.704 baris komponen Silver digunakan untuk membentuk 1.428 baris agregat bahan bakar.

## 3. Pewarisan Penanda Outlier dan Patahan

Penanda outlier dari hasil audit Sprint 1 tetap dipertahankan pada Gold. Kandidat anomali diperiksa berdasarkan laporan `calon_anomali_var87.csv` dan `calon_anomali_bahan_bakar.csv`. Nilai tidak dihapus, dikoreksi, maupun diinterpolasi hanya karena ditandai sebagai outlier.

Berdasarkan keputusan K-017, K-020, dan K-021, tidak ditemukan bukti patahan seri yang terkonfirmasi. Perubahan ekstrem dipertahankan sebagai kandidat anomali lokal. Berdasarkan keputusan audit tersebut, seluruh baris Gold diberi status tidak_terkonfirmasi. Status ini menunjukkan bahwa audit Sprint 1 tidak menemukan bukti patahan seri yang terkonfirmasi, bukan berarti setiap baris telah diperiksa sebagai kasus patahan individual.

Hasil pemeriksaan Gold:
- Total baris: 2.682.
- Baris dengan outlier = True: 124.
- Baris dengan outlier = False: 2.558.
- Baris dengan status patahan tersedia: 2.682.
- Catatan patahan kosong: 0.

## 3.1 Pewarisan Penanda Grid dan Missing

Pembentukan Gold mempertahankan seluruh kombinasi provinsi dan periode yang dihasilkan dari grid Silver. Baris dengan kondisi sebelum provinsi terbentuk dan tahun tidak diterbitkan tidak dihapus dari panel Gold.

Empat penanda yang dipertahankan adalah:
- `sebelum_provinsi_ada`
- `tahun_tidak_diterbitkan`
- `sel_kosong_dalam_terbitan`
- `missing_sejati`

Penanda tersebut disimpan sebagai kolom Boolean pada panel Gold. Untuk indikator bahan bakar, penanda diwariskan dari komponen penyusunnya. Jika salah satu komponen memiliki penanda tertentu, informasi tersebut tetap dicatat pada indikator agregat.

Hasil pemeriksaan menunjukkan terdapat 240 baris dengan penanda sebelum provinsi ada, 378 baris dengan penanda tahun tidak diterbitkan, dan 46 baris dengan penanda missing sejati. Jumlah penanda dapat saling tumpang tindih sehingga tidak dijumlahkan sebagai jumlah baris unik.

Keempat kolom penanda berhasil disimpan pada `data/gold/panel.parquet` dan tabel `gold_panel` dalam `data/gold/gold.sqlite`.

## 4. Hasil Pembentukan Gold

Pembentukan panel Gold menghasilkan 2.682 baris dengan rincian:
- Elektrifikasi: 1.254 baris.
- Bahan bakar bersih: 714 baris.
- Bahan bakar tidak bersih: 714 baris.

Selain panel Gold, pipeline juga menghasilkan:
- Gold nasional: 187 baris.
- Gold rekonsiliasi: 60 baris, terdiri atas 47 pasangan berpasangan.
- Basis data SQLite: `data/gold/gold.sqlite`.

## 5. Hasil Pipeline dan Validasi

Pipeline dijalankan menggunakan perintah:

`.\.venv\Scripts\python.exe pipeline.py`

Hasil eksekusi:
- 9 berkas raw cocok dengan MANIFEST.csv.
- Ekstraksi berhasil.
- Silver berhasil dibentuk sebanyak 4.830 baris.
- Gold berhasil dibentuk sebanyak 2.682 baris.
- Gold nasional dan rekonsiliasi berhasil dibentuk.
- Data berhasil dimuat ke SQLite.
- Validasi berhasil dengan 8 dari 8 aturan lolos.

## 6. Kesimpulan

Tahap Gold berhasil membentuk panel data provinsi, periode, dan indikator melalui pipeline. Aturan pemilihan snapshot, periode, serta pemetaan rincian bahan bakar diterapkan melalui fungsi pada modul `src/gold`. Penanda outlier dan catatan hasil audit patahan tetap tersedia pada Gold. Seluruh proses pipeline berhasil dijalankan dan delapan aturan validasi dinyatakan lolos.