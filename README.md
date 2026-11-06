# Capstone Data Wrangling — starter tim

Template repositori tim untuk **Capstone Data Wrangling: Indikator SDG Indonesia dari Banyak Sumber**
(Program Studi Sains Data ITERA, Data Science Workbench). Satu tim = satu repositori yang dibuat
dari template ini.

Setiap tim mengerjakan **satu kasus** dari 23 kasus. Nomor kasus, seri yang dipakai, dan tautan
dataset tercatat di kartu *Kasus tim* pada Papan Tim Workbench. Data berasal dari BPS, BNPB,
World Bank (WDI), WHO GHO, dan ILOSTAT, persis seperti diunduh dari sumbernya pada 17–20 Oktober
2026 (lapis Bronze). Tugas tim adalah membangun pipeline yang dapat diulang dari data mentah sampai
tabel Silver (rapi, ber-provenans) dan Gold (panel siap analisis), lalu memvalidasi dan
mendokumentasikannya.

## Mulai

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python unduh_data.py --kasus <N>        # N = nomor di kartu Kasus tim
```

`unduh_data.py` mengisi `data/raw/` dan memeriksa sha256 setiap berkas terhadap
`data/raw/MANIFEST.csv`. Baca `data/KASUS.md`: seri utama, pembanding, dan hal yang perlu
diperhatikan untuk kasus Anda. `data/raw/` tidak di-commit; anggota lain cukup mengunduh ulang.

## Struktur

```text
unduh_data.py          milik starter — unduh paket kasus dari Release dan periksa sha256
pipeline.py            satu perintah reproduksi: ekstraksi -> silver -> gold -> validasi
src/common/            milik starter — jangan diubah: manifest (lineage sha256), skema (pemeriksa Silver),
                       hasil (results/<nim>/metrics.json untuk bukti artefak di Workbench)
src/ekstraksi/         tahap 1: pembaca tiap format
src/silver/            tahap 2–4: profil, pembersihan, penyeragaman
src/gold/              tahap 4–6: reshape panel, integrasi pembanding, penyimpanan SQL
src/skala/             tahap 7: arsip WDI 142 rilis (buat sendiri)
src/validasi/          tahap 8: skema pandera/Great Expectations
data/silver/, data/gold/   keluaran (boleh di-commit bila < 20 MB)
log-keputusan.csv      setiap keputusan wrangling: apa, alternatif yang ditolak, alasan, dampak baris
docs/data-dictionary.md    kamus data Silver dan Gold
results/<nim>/metrics.json   angka hasil komponen Anda: python -m src.common.hasil <nim> nama=angka ...
reports/tim.md, reports/individu/<nim>.md, AI_LOG.md
```

## Tahapan

| Tahap | Pertemuan | Keluaran minimal |
|---|---|---|
| 1. Ekstraksi | X | Pembaca CSV, JSON, XLSX, SDMX; opsional tarik ulang lewat API dan bandingkan dengan snapshot |
| 2. Profil dan anomali | II–III | Statistik deskriptif, boxplot, z-score/IQR per seri |
| 3. Pembersihan | IV–VI | Strategi missing, penanganan outlier dan patahan seri, deduplikasi, format periode dan wilayah |
| 4. Transformasi | VII, IX | Normalisasi/standarisasi, encoding rincian, reshape ke panel |
| 5. Penyimpanan | XI | Silver dan Gold di SQL; mentah sebagai dokumen; alasan pilihannya |
| 6. Integrasi | XII | Seri utama + pembanding nasional; selisih dijelaskan, bukan dihapus |
| 7. Skala | XIII | `python unduh_data.py --arsip-wdi`; revisi seri pembanding antar-142 rilis; pandas vs DuckDB/Dask |
| 8. Dokumentasi dan validasi | XIV–XV | Lineage ke berkas mentah, data dictionary, skema validasi otomatis |

## Yang dibakukan untuk semua tim

- **Skema minimal Silver** (`src/common/skema.py`): `sumber, seri_kode, wilayah_kode, nama_wilayah,
  periode, jenis_periode, rincian, nilai, satuan, _berkas_raw, _sha256_raw`. Kunci unik:
  sumber + seri + wilayah + periode + rincian + berkas. Periksa dengan
  `python -m src.common.skema data/silver/silver.parquet`.
- **Wilayah**: `wilayah_kode` 9999 = Indonesia; provinsi = kode dua digit BPS x 100 (1100 = Aceh),
  susunan 38 provinsi tahun 2025. Aturan pemetaan provinsi pemekaran ditulis di `log-keputusan.csv`.
- **Periode**: `2020` (tahun), `2020-S1` (semester), `2020-Q3` (triwulan), `2020-07` (bulan).
- **Lineage**: `_sha256_raw` diambil dari `src.common.manifest.sha256_raw`, tidak ditulis tangan.
- **Satu perintah**: `python pipeline.py` dari `data/raw/` yang baru diunduh harus menghasilkan
  ulang Silver dan Gold yang di-commit.

## Pembagian peran yang disarankan

Satu anggota memiliki satu komponen dan bertanggung jawab atas keputusannya di log; laporan tim
mengintegrasikan semuanya. Sesuaikan dengan parameter capstone di Workbench.

| Komponen | Isi |
|---|---|
| Ekstraksi dan lineage | tahap 1, `_berkas_raw`/`_sha256_raw`, tarik ulang API |
| Pembersihan | tahap 2–3: missing, outlier, patahan seri, duplikat |
| Transformasi dan panel | tahap 4: format, encoding, reshape, normalisasi |
| Integrasi dan penyimpanan | tahap 5–7: SQL, pembanding nasional, arsip WDI |
| Validasi dan dokumentasi | tahap 8: skema validasi, data dictionary, README |

## Lisensi

Kode starter: MIT. Data: lihat `data/LISENSI.md` setelah mengunduh; basis data turunan yang
diterbitkan memakai ODbL 1.0 dengan atribusi BPS, BNPB, World Bank, WHO, dan ILO.
