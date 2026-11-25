"""Tahap Gold: penyimpanan hasil Silver ke format siap analisis."""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
GOLD_DIR = ROOT / "data" / "gold"


def jalankan(silver, mentah=None):
    """Terima Silver (dan hasil ekstraksi), simpan hasil Gold, dan kembalikan tabel Gold."""
    GOLD_DIR.mkdir(parents=True, exist_ok=True)

    gold = silver.copy()
    jalur = GOLD_DIR / "panel.parquet"
    gold.to_parquet(jalur, index=False)
    print(f"Gold: {len(gold):,} baris -> {jalur.relative_to(ROOT)}")
    hasil = {"panel": gold}

    if mentah is not None:
        from src.gold.nasional import bangun_nasional
        nas = bangun_nasional(silver, mentah)
        nas.to_parquet(GOLD_DIR / "tabel_nasional.parquet", index=False)
        nas.to_csv(GOLD_DIR / "tabel_nasional.csv", index=False)
        print(f"Gold nasional: {len(nas):,} baris -> data/gold/tabel_nasional.parquet (+ .csv)")
        hasil["nasional"] = nas

    from src.gold.muat_sql import DB_PATH, muat_semua
    ringkasan_sql = muat_semua(silver, hasil)
    rincian_sql = ", ".join(f"{t}={n:,}" for t, n in ringkasan_sql.items())
    print(f"SQLite: {DB_PATH.relative_to(ROOT)} ({rincian_sql})")

    return hasil