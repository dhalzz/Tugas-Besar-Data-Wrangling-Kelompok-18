"""Memuat Silver, panel Gold, tabel nasional, dan tabel rekonsiliasi ke SQLite."""

from __future__ import annotations

import sqlite3
from pathlib import Path

import pandas as pd

from src.gold.sql_schema import SEMUA_DDL

ROOT = Path(__file__).resolve().parents[2]
DB_PATH = ROOT / "data" / "gold" / "gold.sqlite"


def _siapkan_tabel(conn: sqlite3.Connection, nama_tabel: str, ddl: str) -> None:
    """Bangun ulang tabel dengan DDL eksplisit agar tipe kolom dan PRIMARY KEY terjaga."""
    conn.execute(f"DROP TABLE IF EXISTS {nama_tabel};")
    conn.execute(ddl)


def _muat_dataframe(conn: sqlite3.Connection, nama_tabel: str, df: pd.DataFrame) -> int:
    """Masukkan DataFrame ke tabel SQLite yang sudah dibuat oleh DDL dan verifikasi jumlah baris."""
    _siapkan_tabel(conn, nama_tabel, SEMUA_DDL[nama_tabel])
    df_sql = df.copy()
    if nama_tabel == "gold_nasional" and "rincian" in df_sql.columns:
        # SQLite PRIMARY KEY tidak boleh NULL; baris WDI tanpa rincian diisi string kosong.
        df_sql["rincian"] = df_sql["rincian"].fillna("")
    df_sql.to_sql(nama_tabel, conn, if_exists="append", index=False)

    jml_sql = conn.execute(f"SELECT COUNT(*) FROM {nama_tabel};").fetchone()[0]
    jml_src = len(df_sql)
    assert jml_sql == jml_src, (
        f"Jumlah baris {nama_tabel} tidak cocok: SQL={jml_sql}, sumber={jml_src}"
    )
    return jml_sql


def muat_semua(
    silver: pd.DataFrame,
    gold: dict[str, pd.DataFrame],
    db_path: Path = DB_PATH,
) -> dict[str, int]:
    """Muat tabel Silver, panel Gold, nasional, dan rekonsiliasi ke SQLite.

    Mengembalikan {nama_tabel: jumlah_baris}.
    """
    db_path.parent.mkdir(parents=True, exist_ok=True)
    ringkasan: dict[str, int] = {}

    with sqlite3.connect(db_path) as conn:
        ringkasan["silver"] = _muat_dataframe(conn, "silver", silver)

        if "panel" in gold:
            ringkasan["gold_panel"] = _muat_dataframe(conn, "gold_panel", gold["panel"])

        if "nasional" in gold:
            ringkasan["gold_nasional"] = _muat_dataframe(conn, "gold_nasional", gold["nasional"])

        if "rekonsiliasi" in gold:
            ringkasan["gold_rekonsiliasi"] = _muat_dataframe(
                conn, "gold_rekonsiliasi", gold["rekonsiliasi"]
            )

        conn.commit()

    return ringkasan
