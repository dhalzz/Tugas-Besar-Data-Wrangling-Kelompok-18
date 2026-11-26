
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


## data/gold/panel.parquet

Satu baris Gold merepresentasikan satu kombinasi provinsi × tahun × indikator. Gold dibentuk dari grid Silver dan nilai observasi Silver. Baris struktural sebelum provinsi terbentuk dan tahun yang tidak diterbitkan tidak dimasukkan.

### Struktur kolom Gold

| Kolom | Tipe | Satuan/format | Boleh kosong | Rentang atau nilai sah | Asal (berkas/aturan) | Keterangan |
|---|---|---|---|---|---|---|
| `wilayah_kode` | int | kode BPS × 100 | tidak | kode provinsi | grid Silver dan dim_provinsi_38.csv | Identitas provinsi. Agregat nasional 9999 tidak dimasukkan. |
| `nama_provinsi` | string | nama provinsi resmi | tidak | nama provinsi | grid Silver | Nama provinsi sesuai referensi. |
| `periode` | string | YYYY | tidak | tahun pengamatan | grid Silver | Tahun observasi. |
| `indikator` | string | kode indikator Gold | tidak | `elektrifikasi`, `bahan_bakar_bersih`, `bahan_bakar_tidak_bersih`, `bahan_bakar_lainnya` | aturan transformasi Gold | Identitas indikator setelah reshape dan agregasi. |
| `nilai` | float | persen | ya | 0–100 | nilai Silver atau hasil agregasi | Nilai asli untuk elektrifikasi dan Lainnya; hasil penjumlahan komponen untuk kategori bahan bakar. Missing sejati tetap kosong. |
| `satuan` | string | nama satuan | tidak | `persen` | metadata seri Silver | Satuan indikator. Satuan berbeda tidak boleh dicampur dalam satu indikator. |
| `_lineage_silver` | string | JSON array | ya | daftar identitas baris Silver beserta berkas dan hash asal | Silver dan MANIFEST.csv | Menyimpan seluruh baris Silver yang membentuk nilai Gold. |
| `status_data` | string | kategori status | tidak | `tersedia`, `missing_sejati` | grid Silver | Membedakan nilai observasi tersedia dan sel kosong dalam tahun terbit. |

### Aturan pembentukan Gold

#### 1. Grain dan bentuk panel

Gold disimpan dalam bentuk panjang (*long format*). Satu baris mewakili satu provinsi × periode tahunan × indikator.

Kunci unik Gold:

`wilayah_kode × periode × indikator`

#### 2. Aturan pemilihan snapshot

- Snapshot harus berasal dari berkas sumber yang tercatat dalam MANIFEST.
- Jika tersedia beberapa snapshot untuk kunci observasi yang sama, Gold memilih snapshot dengan tanggal terbaru berdasarkan tanggal yang tercantum pada `_berkas_raw`.
- Jika tanggal snapshot sama, `_berkas_raw` digunakan sebagai pengurutan tambahan secara alfabetis menurun agar pemilihan bersifat deterministik.
- Baris yang tidak terpilih tetap dipertahankan di Silver.
- Pemilihan snapshot dilakukan sebelum agregasi Gold.

#### 3. Aturan transformasi indikator

**Listrik**
- Sumber: seri `var87`.
- `rincian` Silver `elektrifikasi` menjadi indikator Gold `elektrifikasi`.
- Nilai dan satuan dipertahankan.

**Bahan bakar bersih**
- Sumber: seri `tabel:sdg7_bahan_bakar`.
- Pemetaan: `Listrik` + `Gas/Elpiji`.
- Nilai Gold merupakan penjumlahan kedua komponen dalam satu provinsi dan tahun.

**Bahan bakar tidak bersih**
- Pemetaan: `Kayu` + `Arang/Briket` + `Minyak Tanah`.
- Nilai Gold merupakan penjumlahan ketiga komponen dalam satu provinsi dan tahun.

**Bahan bakar lainnya**
- Rincian `Lainnya` dipertahankan sebagai indikator tersendiri.
- Tidak digabungkan ke kategori bersih maupun tidak bersih.

**Rincian Jumlah**
- Dikeluarkan dari agregasi karena merupakan total seluruh kategori dan dapat menyebabkan penghitungan ganda (K-006).

#### 4. Penanganan missing

- Baris dengan `sebelum_provinsi_ada = True` tidak dimasukkan.
- Baris dengan `tahun_tidak_diterbitkan = True` tidak dimasukkan.
- Missing sejati tetap menjadi baris Gold dengan `nilai` kosong dan `status_data = missing_sejati`.
- Jika satu atau lebih komponen agregasi tidak tersedia, nilai agregat menjadi kosong. Komponen yang tidak tersedia tidak dianggap nol.
- Nilai asli tidak diimputasi atau dikoreksi.

#### 5. Aturan granularitas periode

- `tahun`: digunakan langsung dalam panel tahunan.
- `semester`, `triwulan`, dan `bulan`: tidak digabung otomatis menjadi tahunan.
- Data dengan granularitas selain tahunan tetap dipertahankan di Silver sampai tersedia aturan agregasi yang memiliki dasar metodologis.
- Fungsi Gold harus menolak granularitas yang tidak sesuai dengan panel tahunan, bukan mengubahnya secara diam-diam.

#### 6. Lineage

- Setiap nilai Gold harus dapat ditelusuri ke seluruh baris Silver pembentuknya.
- Untuk indikator hasil agregasi, lineage mencakup seluruh komponen Silver yang tersedia dan digunakan sebagai sumber agregasi.
- Informasi berkas mentah dan SHA-256 setiap komponen disimpan dalam `_lineage_silver`.
- Jika tidak ada komponen Silver yang tersedia, `_lineage_silver` berisi daftar kosong.

#### 7. Audit anomali dan patahan

- Nilai kandidat anomali tidak dihapus, dikoreksi, atau diinterpolasi.
- Kandidat anomali listrik ditelusuri berdasarkan wilayah dan tahun.
- Kandidat anomali bahan bakar ditelusuri berdasarkan wilayah, tahun, dan rincian bahan bakar.
- Tidak ada patahan seri nasional yang terkonfirmasi berdasarkan audit Sprint 1.
- Perubahan lokal tetap dipertahankan dan tidak diklaim sebagai patahan yang telah terkonfirmasi.

#### 8. Pencatatan keputusan

Setiap aturan seleksi dan agregasi Gold dicatat dalam `log-keputusan.csv` dengan `tahap=gold`.

Setiap catatan harus mencantumkan:
- kunci dan aturan pemilihan;
- alternatif yang ditolak;
- alasan keputusan;
- jumlah baris Silver yang tidak terpilih.

Fungsi pembentukan Gold berada di `src/gold/` dan dipanggil melalui `pipeline.py`.

#### 9. Kunci unik dan satuan

- Kombinasi `wilayah_kode`, `periode`, dan `indikator` harus unik.
- Seluruh indikator pada tabel Gold menggunakan satuan persen.
