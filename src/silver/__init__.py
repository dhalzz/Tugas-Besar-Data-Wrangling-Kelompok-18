"""Tahap 2–4 — Profil, pembersihan, dan penyeragaman ke Silver (pertemuan II–VII). Milik tim.

Keluaran: data/silver/silver.parquet dengan skema minimal di src/common/skema.py.
Satu baris = satu seri x wilayah x periode x rincian x berkas sumber. Nilai dari sumber berbeda
TIDAK digabung di sini. Setiap keputusan pembersihan dicatat di log-keputusan.csv.
"""


def jalankan(mentah):
    """Terima keluaran tahap 1, tulis dan kembalikan DataFrame Silver."""
    raise NotImplementedError("Tahap 2–4: profil, missing, outlier/patahan, duplikat, format periode dan wilayah")
