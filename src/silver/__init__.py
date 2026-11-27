"""Tahap Silver: penyusunan dan penyimpanan data Silver."""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
from src.silver import grid

SILVER = ROOT / "data" / "silver" / "silver.parquet"


def jalankan(mentah):
    dim, mulai = grid.muat_referensi()

    silver = grid.silver_minimal(dim)
    SILVER.parent.mkdir(parents=True, exist_ok=True)
    silver.to_parquet(SILVER, index=False)

    print(f"Silver: {len(silver):,} baris -> {SILVER.relative_to(ROOT)}")

    return silver