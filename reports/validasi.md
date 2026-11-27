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
| Penanda outlier dan patahan Gold valid | Lolos | 124 baris ditandai outlier; tipe outlier valid: True; status patahan valid: True; catatan patahan valid: True. |
