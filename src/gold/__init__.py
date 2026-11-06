"""Tahap 4–6 — Reshape, integrasi, dan penyimpanan ke Gold (pertemuan VII, IX, XI, XII). Milik tim.

Keluaran: data/gold/*.parquet (panel provinsi x tahun x indikator siap analisis, plus tabel
rekonsiliasi dengan pembanding nasional) dan basis data SQL (mis. data/gold/gold.sqlite).
"""


def jalankan(silver):
    """Terima Silver, tulis tabel Gold, kembalikan {nama_tabel: DataFrame}."""
    raise NotImplementedError("Tahap 4–6: grid lengkap, reshape panel, rekonsiliasi pembanding, simpan ke SQL")
