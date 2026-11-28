"""Tahap Silver: penyusunan dan penyimpanan data Silver."""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
from src.silver import grid

SILVER = ROOT / "data" / "silver" / "silver.parquet"


def jalankan(mentah):
    dim, mulai = grid.muat_referensi()

    silver = grid.silver_minimal(dim)
    # Perbaiki lineage data listrik berdasarkan sumber raw yang terdaftar di MANIFEST
    mask_listrik = silver["seri_kode"] == "var87"

    silver.loc[mask_listrik, "_berkas_raw"] = (
        "bps/2026-10-17/json/sdg7_listrik_pln.json"
    )

    silver.loc[mask_listrik, "_sha256_raw"] = (
        "88d2ddbd3ccfeb6cb395345f034be0e39b8e732996a2824ae414d90a6153828e"
    )
    SILVER.parent.mkdir(parents=True, exist_ok=True)
    silver.to_parquet(SILVER, index=False)

    print(f"Silver: {len(silver):,} baris -> {SILVER.relative_to(ROOT)}")

    return silver