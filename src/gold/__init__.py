"""Tahap Gold: penyimpanan hasil Silver ke format siap analisis."""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
GOLD_DIR = ROOT / "data" / "gold"


def jalankan(silver):
    """Terima Silver, simpan hasil Gold, dan kembalikan tabel Gold."""
    GOLD_DIR.mkdir(parents=True, exist_ok=True)

    gold = silver.copy()

    # Simpan tabel Gold minimal dalam format Parquet
    jalur = GOLD_DIR / "panel.parquet"
    gold.to_parquet(jalur, index=False)

    print(f"Gold: {len(gold):,} baris -> {jalur.relative_to(ROOT)}")

    return {"panel": gold}
