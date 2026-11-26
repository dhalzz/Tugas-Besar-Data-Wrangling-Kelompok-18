
"""Tahap Gold: membentuk panel provinsi x tahun dan menyimpan hasil analisis."""

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
            "wilayah_kode",
            "nama_wilayah",
            "periode",
            "indikator",
            "kategori",
            "nilai",
            "satuan",
            "jenis_periode",
            "sebelum_provinsi_ada",
            "tahun_tidak_diterbitkan",
            "sel_kosong_dalam_terbitan",
            "missing_sejati",
            "rincian_missing",
        ]
    ]


def jalankan(silver, mentah=None):
    """Bentuk panel Gold, tabel nasional, rekonsiliasi, dan SQLite."""
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

    # 5. Gabungkan seluruh indikator.
    gold = pd.concat(
        [listrik, bahan_bakar],
        ignore_index=True,
    )

    # 6. Bawa status audit patahan Sprint 1.
    gold["status_patahan"] = "tidak_terkonfirmasi"
    gold["catatan_patahan"] = (
        "Tidak ditemukan patahan seri nasional terkonfirmasi. "
        "Perubahan lokal dipertahankan sesuai keputusan K-017."
    )

    # 7. Bawa kandidat outlier Sprint 1.
    gold = tandai_outlier(gold, ROOT)

    # 8. Validasi kunci akhir Gold.
    kunci_gold = ["wilayah_kode", "periode", "indikator"]
    duplikat = gold.duplicated(
        subset=kunci_gold, keep=False
    )

    if duplikat.any():
        raise ValueError(
            "Ditemukan duplikasi kunci panel Gold:\n"
            + gold.loc[duplikat, kunci_gold]
            .head(10)
            .to_string(index=False)
        )

    # 9. Simpan panel Gold.
    jalur = GOLD_DIR / "panel.parquet"
    gold.to_parquet(jalur, index=False)

    print(
        f"Gold: {len(gold):,} baris "
        f"-> {jalur.relative_to(ROOT)}"
    )
    print(gold.groupby("indikator").size())

    # 10. Siapkan hasil Gold untuk integrasi.
    hasil = {"panel": gold}

    # 11. Bentuk tabel nasional dan rekonsiliasi.
    if mentah is not None:
        from src.gold.nasional import bangun_nasional
        from src.gold.rekonsiliasi import bangun_rekonsiliasi

        nas = bangun_nasional(silver, mentah)

        nas.to_parquet(
            GOLD_DIR / "tabel_nasional.parquet",
            index=False,
        )
        nas.to_csv(
            GOLD_DIR / "tabel_nasional.csv",
            index=False,
        )

        print(
            f"Gold nasional: {len(nas):,} baris "
            "-> data/gold/tabel_nasional.parquet (+ .csv)"
        )
        hasil["nasional"] = nas

        rek = bangun_rekonsiliasi(nas)

        rek.to_parquet(
            GOLD_DIR / "tabel_rekonsiliasi.parquet",
            index=False,
        )
        rek.to_csv(
            GOLD_DIR / "tabel_rekonsiliasi.csv",
            index=False,
        )

        n_pair = int(
            (
                rek["nilai_utama"].notna()
                & rek["nilai_pembanding"].notna()
            ).sum()
        )

        print(
            f"Gold rekonsiliasi: {len(rek):,} baris "
            f"({n_pair} berpasangan) "
            "-> data/gold/tabel_rekonsiliasi.parquet (+ .csv)"
        )

        hasil["rekonsiliasi"] = rek

    # 12. Muat Silver dan hasil Gold ke SQLite.
    from src.gold.muat_sql import DB_PATH, muat_semua

    ringkasan_sql = muat_semua(silver, hasil)

    rincian_sql = ", ".join(
        f"{t}={n:,}"
        for t, n in ringkasan_sql.items()
    )

    print(
        f"SQLite: {DB_PATH.relative_to(ROOT)} "
        f"({rincian_sql})"
    )

    return hasil
