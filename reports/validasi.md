# Laporan Validasi Silver, Gold, dan Rekonsiliasi

Dibuat otomatis saat `python pipeline.py` dijalankan.

- Jumlah aturan: **10**
- Lolos: **9**
- Gagal: **1**

| Aturan | Status | Baris diperiksa | Pelanggaran | Keterangan |
|---|---|---:|---:|---|
| Nilai persen Silver berada pada rentang 0 sampai 100.01 | Lolos | 4830 | 0 | Seluruh nilai persen memenuhi batas termasuk toleransi pembulatan 100.01. |
| Kunci observasi Silver unik | Lolos | 4830 | 0 | Tidak ada kombinasi seri, wilayah, periode, dan rincian yang ganda. |
| Satuan Silver konsisten | Lolos | 4830 | 0 | Semua observasi Silver memakai satuan persen. |
| Kategori bahan bakar Silver terpetakan | Lolos | 6 | 0 | 6 kategori bahan bakar terpetakan. |
| Total kategori bahan bakar lengkap mendekati 100 persen | Lolos | 545 | 0 | 545 grup lengkap diperiksa; 0 grup dikecualikan karena ada nilai kosong. |
| Kunci panel Gold unik | Lolos | 2621 | 0 | Tidak ada kombinasi wilayah, periode, dan indikator yang ganda. |
| Satuan per indikator Gold konsisten | Lolos | 4 | 0 | Setiap indikator Gold memiliki satu satuan yang konsisten. |
| Nilai dan status_data Gold konsisten | Lolos | 2621 | 0 | Baris tersedia memiliki nilai sah; baris non-tersedia tidak memuat nilai. |
| Setiap nilai Gold tersedia memiliki lineage Silver yang sah | Lolos | 2570 | 0 | Seluruh nilai Gold tersedia dapat ditelusuri ke baris Silver. |
| Pasangan rekonsiliasi memiliki kategori selisih | Gagal | 0 | 1 | Tabel rekonsiliasi berpasangan belum tersedia di data/gold. CSV laporan nasional saat ini masih berbentuk panjang, bukan pasangan BPS-WDI. |
