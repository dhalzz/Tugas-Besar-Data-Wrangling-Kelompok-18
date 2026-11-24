
# Data dictionary — Kelompok 18

## data/silver/silver.parquet
| Kolom | Tipe | Satuan/format | Boleh kosong | Rentang atau nilai sah | Asal (berkas/aturan) | Keterangan |
|---|---|---|---|---|---|---|
| `sumber` | string | — | tidak | `bps`, `wdi` | nama sumber pada data mentah | Instansi/sumber data observasi. |
| `seri_kode` | string | kode seri | tidak | `var87`, `tabel:sdg7_bahan_bakar`, kode WDI | metadata seri dan pembaca ekstraksi | Identitas indikator atau tabel sumber. |
| `wilayah_kode` | int | kode BPS × 100 | tidak | `9999` atau kode provinsi BPS | `data/referensi/dim_provinsi_38.csv` | `9999` berarti agregat nasional Indonesia. |
| `nama_wilayah` | string | nama wilayah resmi | tidak | nama provinsi atau `INDONESIA` | berkas mentah dan tabel referensi provinsi | Nama wilayah setelah penyeragaman. |
| `periode` | string | `YYYY`, `YYYY-S1`, `YYYY-Q1`, atau `YYYY-MM` | tidak | format periode standar | kolom periode pada berkas mentah | Waktu observasi. |
| `jenis_periode` | string | — | tidak | `tahun`, `semester`, `triwulan`, atau `bulan` | aturan normalisasi periode | Tingkat granularitas periode. |
| `rincian` | string | kategori | tidak | jenis bahan bakar atau `elektrifikasi` | kolom kategori dari berkas mentah | Rincian indikator dalam seri. |
| `nilai` | float | persen | ya | 0–100 untuk seri persen | kolom nilai berkas mentah setelah pembersihan | Nilai kosong tetap dipertahankan sebagai missing, bukan nol. |
| `satuan` | string | nama satuan | tidak | `persen` | metadata seri | Satuan dari kolom `nilai`. |
| `_berkas_raw` | string | path relatif | tidak | path berkas di `data/raw/` | pembaca pada `src/ekstraksi/` | Jejak lokasi berkas mentah asal observasi. |
| `_sha256_raw` | string | SHA-256 | tidak | hash SHA-256 valid | `data/raw/MANIFEST.csv` | Sidik berkas mentah untuk lineage dan reproduksibilitas. |

## Contoh lineage Silver

Contoh satu baris Silver dapat ditelusuri melalui:

1. Nilai `_berkas_raw` menunjukkan berkas asal di `data/raw/`.
2. Nilai `_sha256_raw` harus cocok dengan hash pada `data/raw/MANIFEST.csv`.
3. Bila nama wilayah, periode, atau nilai diubah saat pembersihan, alasan dan dampaknya dicari di `log-keputusan.csv`.

Contoh:

```text
seri_kode       : tabel:sdg7_bahan_bakar
wilayah_kode    : 1100
nama_wilayah    : Aceh
periode         : 2021
rincian         : LPG
nilai           : 15.4
satuan          : persen
_berkas_raw     : bps/2026-10-17/sdg7_bahan_bakar.csv
_sha256_raw     : hash yang cocok dengan MANIFEST.csv
```

## data/gold/<tabel>.parquet
Kolom Gold akan dilengkapi pada Sprint 2–3 setelah tabel Gold dibuat.


## Aturan pembentukan Gold — Tahap 4

### 1. Grain dan bentuk panel

Gold disimpan dalam bentuk panjang (*long format*). Satu baris mewakili satu provinsi × periode tahunan × indikator.

Indikator yang dimuat:
- `elektrifikasi`: persentase rumah tangga yang memiliki akses listrik.
- `bahan_bakar_bersih`: persentase rumah tangga dengan bahan bakar utama memasak yang termasuk kategori bersih.

Kunci unik Gold:
`wilayah_kode × periode × indikator`

### 2. Aturan pemilihan snapshot

- Snapshot harus berasal dari berkas sumber yang tercatat dalam MANIFEST.
- Jika tersedia beberapa snapshot untuk kunci observasi yang sama, Gold menggunakan snapshot bertanggal paling baru setelah pemeriksaan validitas sumber.
- Jika nilai sama pada beberapa snapshot, satu observasi dipilih dan sisanya dicatat sebagai baris yang tidak terpilih.
- Jika nilai berbeda, perbedaan diperlakukan sebagai revisi. Gold memilih snapshot terbaru, sedangkan riwayat revisi tetap dipertahankan di Silver.
- Jika tanggal snapshot tidak dapat ditentukan atau terdapat konflik yang tidak dapat diselesaikan, proses Gold harus gagal dengan pesan yang jelas.
- Kondisi saat ini: hanya tersedia satu snapshot BPS bertanggal 2026-10-17 sehingga belum ada perbandingan revisi antar-snapshot.

### 3. Aturan rincian bahan bakar

Pemetaan kategori berdasarkan klasifikasi bahan bakar memasak:

| Rincian BPS | Kategori Gold |
|---|---|
| Listrik | Bersih |
| Gas/Elpiji | Bersih |
| Kayu | Tidak bersih |
| Arang/Briket | Tidak bersih |
| Minyak Tanah | Tidak bersih |
| Lainnya | Tidak diklasifikasikan |
| Jumlah | Tidak diagregasikan |

Nilai `bahan_bakar_bersih` merupakan penjumlahan nilai Listrik dan Gas/Elpiji pada provinsi dan tahun yang sama.

Kategori tidak bersih dihitung dari Kayu, Arang/Briket, dan Minyak Tanah. Kategori ini disimpan sebagai hasil agregasi tambahan untuk keperluan analisis.

Kategori `Lainnya` tidak dimasukkan ke kedua agregasi karena mencakup rumah tangga yang tidak memasak dan kemungkinan bahan bakar lain. Kategori `Jumlah` tidak digunakan karena merupakan total, bukan rincian bahan bakar.

Agregasi hanya dilakukan jika seluruh rincian penyusun kategori tersedia. Nilai yang hilang tidak dianggap nol.

### 4. Aturan granularitas periode

- `tahun`: digunakan langsung dalam panel tahunan.
- `semester`, `triwulan`, dan `bulan`: tidak digabung otomatis menjadi tahunan.
- Data dengan granularitas selain tahunan tetap dipertahankan di Silver sampai tersedia aturan agregasi yang memiliki dasar metodologis.
- Fungsi Gold harus menolak granularitas yang tidak sesuai dengan panel tahunan, bukan mengubahnya secara diam-diam.

### 5. Pewarisan penanda anomali dan patahan

- Nilai kandidat anomali tidak dihapus, dikoreksi, atau diinterpolasi.
- Kandidat anomali listrik ditelusuri berdasarkan wilayah dan tahun.
- Kandidat anomali bahan bakar ditelusuri berdasarkan wilayah, tahun, dan rincian bahan bakar.
- Pada hasil agregasi, status kandidat anomali diteruskan jika salah satu rincian penyusun memiliki status kandidat anomali. Rincian sumbernya tetap dicatat.
- Status pembanding tidak boleh dianggap sebagai kandidat anomali.
- Tidak ada patahan seri nasional yang terkonfirmasi berdasarkan audit Sprint 1. Perubahan lokal yang belum diketahui penyebabnya tetap dipertahankan dan ditandai.

### 6. Pencatatan keputusan

Setiap aturan seleksi dan agregasi Gold dicatat dalam `log-keputusan.csv` dengan `tahap=gold`.

Setiap catatan harus mencantumkan:
- kunci dan aturan pemilihan;
- alternatif yang ditolak;
- alasan keputusan;
- jumlah baris Silver yang tidak terpilih.

Fungsi pembentukan Gold berada di `src/gold/` dan dipanggil melalui `pipeline.py`.
