# Laporan Validasi Silver dan Gold

Dibuat otomatis saat `python pipeline.py` dijalankan.

| Aturan | Hasil | Keterangan |
|---|---|---|
| Nilai persen berada pada rentang 0--100 | Lolos | 4830 observasi diperiksa. |
| Kunci observasi Silver unik | Lolos | 0 baris duplikat ditemukan. |
| Satuan seri konsisten | Lolos | Semua satuan adalah persen. |
| Total bahan bakar per provinsi-tahun mendekati 100 | Lolos | 545 grup lengkap diperiksa; 0 grup meleset lebih dari ±1.0; 0 grup dikecualikan karena nilai kosong. |
| Setiap jenis bahan bakar memiliki satu kategori | Lolos | 6 jenis bahan bakar diperiksa. |
| Kolom wajib Gold tersedia | Lolos | Semua kolom wajib tersedia. |
| Kunci provinsi-periode-indikator Gold unik | Lolos | 0 baris duplikat ditemukan. |
| Penanda outlier dan patahan Gold tersedia | Lolos | 135 baris ditandai outlier; status patahan dan catatannya tersedia. |
| Seluruh referensi lineage Gold cocok dengan Silver | Lolos | 4157 referensi diperiksa; 0 tidak cocok; 0 JSON lineage tidak valid. |
| Nilai Gold tersedia memiliki lineage | Lolos | 0 baris tersedia tanpa lineage. |
| Komponen pembentuk nilai Gold tersedia dan lengkap | Lolos | 0 komponen pada nilai Gold tersedia tidak memiliki sumber bernilai. |
