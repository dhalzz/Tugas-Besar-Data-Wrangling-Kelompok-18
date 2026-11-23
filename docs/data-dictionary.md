
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
