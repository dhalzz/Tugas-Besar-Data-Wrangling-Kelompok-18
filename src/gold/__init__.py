
"""Tahap Gold: membentuk panel provinsi x tahun."""

from pathlib import Path

import pandas as pd

from src.silver import grid
from src.gold.pemilihan import (
    pilih_snapshot,
    validasi_periode_tahunan,
    pastikan_unik,
    agregasi_bahan_bakar,
    tandai_outlier,
)

ROOT = Path(__file__).resolve().parents[2]
GOLD_DIR = ROOT / "data" / "gold"


def bentuk_panel_listrik(grid_listrik):
    """Bentuk panel listrik dari grid lengkap."""
    hasil = grid_listrik.copy()

    hasil = hasil.rename(
        columns={"nama_provinsi": "nama_wilayah"}
    )

    hasil["indikator"] = "elektrifikasi"
    hasil["kategori"] = "listrik"
    hasil["satuan"] = "%"
    hasil["jenis_periode"] = "tahun"
    hasil["rincian_missing"] = ""

    return hasil[
        [
            "wilayah_kode", "nama_wilayah", "periode",
            "indikator", "kategori", "nilai", "satuan",
            "jenis_periode", "sebelum_provinsi_ada",
            "tahun_tidak_diterbitkan",
            "sel_kosong_dalam_terbitan",
            "missing_sejati", "rincian_missing",
        ]
    ]


def jalankan(silver):
    """Bentuk, validasi, dan simpan panel Gold."""
    GOLD_DIR.mkdir(parents=True, exist_ok=True)

    # 1. Pilih snapshot dan validasi periode Silver.
    terpilih = pilih_snapshot(silver)
    terpilih = validasi_periode_tahunan(terpilih)
    pastikan_unik(terpilih)

    # 2. Bangun ulang grid dari Silver.
    dim, mulai = grid.muat_referensi()

    grid_listrik = grid.grid_seri(
        terpilih, dim, mulai, grid.SERI["var87"]
    )

    grid_bahan_bakar = grid.grid_seri(
        terpilih, dim, mulai, grid.SERI["sdg7_bahan_bakar"]
    )

    # 3. Bentuk panel listrik.
    listrik = bentuk_panel_listrik(grid_listrik)

    # 4. Agregasikan bahan bakar bersih dan tidak bersih.
    bahan_bakar = agregasi_bahan_bakar(
        terpilih, grid_bahan_bakar
    )

    # 5. Gabungkan semua indikator.
    gold = pd.concat(
        [listrik, bahan_bakar],
        ignore_index=True,
    )

    # 5a. Bawa status audit patahan Sprint 1.
    gold["status_patahan"] = "tidak_terkonfirmasi"
    gold["catatan_patahan"] = (
        "Tidak ditemukan patahan seri nasional terkonfirmasi. "
        "Perubahan lokal dipertahankan sesuai keputusan K-017."
    )

    # 6. Bawa kandidat outlier Sprint 1.
    gold = tandai_outlier(gold, ROOT)

    # 7. Validasi kunci akhir Gold.
    kunci_gold = ["wilayah_kode", "periode", "indikator"]

    duplikat = gold.duplicated(
        subset=kunci_gold, keep=False
    )

    if duplikat.any():
        raise ValueError(
            "Ditemukan duplikasi kunci panel Gold:\n"
            + gold.loc[duplikat, kunci_gold].head(10).to_string(index=False)
        )

    # 8. Simpan panel.
    jalur = GOLD_DIR / "panel.parquet"
    gold.to_parquet(jalur, index=False)

    print(f"Gold: {len(gold):,} baris -> {jalur.relative_to(ROOT)}")
    print(gold.groupby("indikator").size())

    return gold
