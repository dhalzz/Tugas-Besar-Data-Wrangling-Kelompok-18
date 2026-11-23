# Laporan Validasi Silver

Dibuat otomatis saat `python pipeline.py` dijalankan.

| Aturan | Hasil | Keterangan |
|---|---|---|
| Nilai persen berada pada rentang 0--100 | Lolos | 4830 observasi diperiksa. |
| Kunci observasi Silver unik | Lolos | 0 baris duplikat ditemukan. |
| Satuan seri konsisten | Lolos | Semua satuan adalah persen. |
| Total bahan bakar per provinsi-tahun mendekati 100 | Lolos | 545 grup lengkap diperiksa; 0 grup meleset lebih dari ±1.0; 0 grup dikecualikan karena nilai kosong. |
| Setiap jenis bahan bakar memiliki satu kategori | Lolos | 6 jenis bahan bakar diperiksa. |
