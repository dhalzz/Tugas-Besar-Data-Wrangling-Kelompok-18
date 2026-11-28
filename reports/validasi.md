# Laporan Validasi Silver, Gold, dan Rekonsiliasi

Dibuat otomatis saat `python pipeline.py` dijalankan.

- Jumlah aturan: **11**
- Lolos: **11**
- Gagal: **0**

| Aturan | Status | Baris diperiksa | Pelanggaran | Keterangan |
|---|---|---:|---:|---|
| Nilai persen Silver berada pada rentang 0 sampai 100.01 | Lolos | 4830 | 0 | Seluruh nilai persen memenuhi batas termasuk toleransi pembulatan 100.01. |
| Kunci observasi Silver unik | Lolos | 4830 | 0 | Tidak ada kombinasi seri, wilayah, periode, dan rincian yang ganda. |
| Satuan Silver konsisten | Lolos | 4830 | 0 | Semua observasi Silver memakai satuan persen. |
| Kategori bahan bakar Silver terpetakan | Lolos | 6 | 0 | 6 kategori bahan bakar terpetakan. |
| Total kategori bahan bakar lengkap mendekati 100 persen | Lolos | 545 | 0 | 545 grup lengkap diperiksa; 0 grup dikecualikan karena ada nilai kosong. |
| Kunci panel Gold unik | Lolos | 2682 | 0 | Tidak ada kombinasi wilayah, periode, dan indikator yang ganda. |
| Satuan per indikator Gold konsisten | Lolos | 3 | 0 | Setiap indikator Gold memiliki satu satuan yang konsisten. |
| Nilai dan status_data Gold konsisten | Lolos | 2682 | 0 | Baris tersedia memiliki nilai sah; baris non-tersedia tidak memuat nilai. |
| Penanda outlier, patahan, dan grid Gold valid | Lolos | 2682 | 0 | Penanda outlier, patahan, dan empat penanda grid terisi dengan tipe yang valid. |
| Setiap nilai Gold tersedia memiliki lineage Silver yang sah | Lolos | 2041 | 0 | Seluruh nilai Gold tersedia dapat ditelusuri ke baris Silver. |
| Pasangan rekonsiliasi memiliki kategori selisih | Lolos | 47 | 0 | Seluruh pasangan seri utama dan pembanding memiliki kategori selisih. |
