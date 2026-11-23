"""Memuat data Silver Parquet ke database SQLite."""

import sqlite3
from pathlib import Path

import pandas as pd

from src.gold.sql_silver import DDL_SILVER


ROOT = Path(__file__).resolve().parents[2]
DATA_SILVER = ROOT / "data" / "silver"
DB_PATH = DATA_SILVER / "silver.db"


def muat_parquet(conn, jalur, jenis_grid):
    """Memuat satu file Parquet ke tabel silver_grid."""
    df = pd.read_parquet(jalur)

    df.insert(0, "jenis_grid", jenis_grid)

    kolom = [
        "jenis_grid",
        "wilayah_kode",
        "tahun",
        "rincian",
        "nama_provinsi",
        "periode",
        "seri_kode",
        "nilai_terisi",
        "nilai",
        "sebelum_provinsi_ada",
        "tahun_tidak_diterbitkan",
        "sel_kosong_dalam_terbitan",
        "missing_sejati",
    ]

    df = df[kolom]

    df.to_sql(
        "silver_grid",
        conn,
        if_exists="append",
        index=False,
    )

    return len(df)


def main():
    DATA_SILVER.mkdir(parents=True, exist_ok=True)

    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(DDL_SILVER)

        jumlah = muat_parquet(
            conn,
            DATA_SILVER / "grid_listrik.parquet",
            "listrik",
        )

        print(f"Berhasil memuat {jumlah:,} baris grid listrik.")
        print(f"Database: {DB_PATH}")


if __name__ == "__main__":
    main()