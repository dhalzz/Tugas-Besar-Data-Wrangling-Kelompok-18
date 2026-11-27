
"""Tahap Gold: pembentukan panel provinsi x tahun x indikator."""

from pathlib import Path
import json

import pandas as pd

from src.silver import grid
from src.gold.pemilihan import (
    pilih_snapshot,
    validasi_periode_tahunan,
    pastikan_unik,
    tandai_outlier,
)

ROOT = Path(__file__).resolve().parents[2]
GOLD_DIR = ROOT / "data" / "gold"

KOMPONEN = {
    "bahan_bakar_bersih": ["Listrik", "Gas/Elpiji"],
    "bahan_bakar_tidak_bersih": [
        "Kayu",
        "Arang/Briket",
        "Minyak Tanah",
    ],
    "bahan_bakar_lainnya": ["Lainnya"],
}


def _buat_peta_lineage(silver):
    """Petakan baris Silver berdasarkan provinsi, periode, dan rincian."""
    peta = {}

    sumber = silver[
        silver["wilayah_kode"] != 9999
    ]

    for _, r in sumber.iterrows():
        kunci = (
            int(r["wilayah_kode"]),
            str(r["periode"]),
            str(r["rincian"]),
        )

        peta.setdefault(kunci, []).append({
            "seri_kode": str(r["seri_kode"]),
            "rincian": str(r["rincian"]),
            "_berkas_raw": str(r["_berkas_raw"]),
            "_sha256_raw": str(r["_sha256_raw"]),
        })

    return peta


def _simpan_lineage(baris_sumber):
    """Ubah seluruh sumber Silver menjadi JSON."""
    return json.dumps(
        baris_sumber,
        ensure_ascii=False,
    )


def _buat_listrik(silver, dim, mulai, peta_lineage):
    """Bentuk panel indikator elektrifikasi dari grid listrik."""
    cfg = grid.SERI["var87"]

    panel = grid.grid_seri(
        silver,
        dim,
        mulai,
        cfg,
    )

    # Hanya ambil provinsi yang sudah terbentuk dan tahun yang diterbitkan.
    panel = panel[
        ~panel["sebelum_provinsi_ada"]
        & ~panel["tahun_tidak_diterbitkan"]
    ].copy()

    hasil = []

    for _, r in panel.iterrows():
        kunci = (
            int(r["wilayah_kode"]),
            str(r["periode"]),
            "elektrifikasi",
        )

        lineage = peta_lineage.get(kunci, [])

        hasil.append({
            "wilayah_kode": int(r["wilayah_kode"]),
            "nama_provinsi": r["nama_provinsi"],
            "periode": str(r["periode"]),
            "indikator": "elektrifikasi",
            "nilai": r["nilai"],
            "satuan": "persen",
            "_lineage_silver": _simpan_lineage(lineage),
            "status_data": (
                "tersedia"
                if pd.notna(r["nilai"])
                else "missing_sejati"
            ),
        })

    return pd.DataFrame(hasil)


def _buat_bahan_bakar(silver, dim, mulai, peta_lineage):
    """Bentuk panel bahan bakar bersih, tidak bersih, dan lainnya."""
    cfg = grid.SERI["sdg7_bahan_bakar"]

    panel = grid.grid_seri(
        silver,
        dim,
        mulai,
        cfg,
    )

    # Tahun yang tidak diterbitkan dan periode sebelum provinsi ada dikeluarkan.
    panel = panel[
        ~panel["sebelum_provinsi_ada"]
        & ~panel["tahun_tidak_diterbitkan"]
    ].copy()

    hasil = []

    for (kode, nama, periode), grup in panel.groupby(
        ["wilayah_kode", "nama_provinsi", "periode"],
        sort=True,
    ):
        nilai_per_jenis = dict(
            zip(grup["rincian"], grup["nilai"])
        )

        for indikator, komponen in KOMPONEN.items():
            nilai_komponen = [
                nilai_per_jenis.get(jenis, float("nan"))
                for jenis in komponen
            ]

            lengkap = all(
                pd.notna(nilai)
                for nilai in nilai_komponen
            )

            nilai_gold = (
                sum(float(nilai) for nilai in nilai_komponen)
                if lengkap
                else float("nan")
            )

            lineage = []

            for jenis in komponen:
                kunci = (
                    int(kode),
                    str(periode),
                    jenis,
                )
                lineage.extend(
                    peta_lineage.get(kunci, [])
                )

            hasil.append({
                "wilayah_kode": int(kode),
                "nama_provinsi": nama,
                "periode": str(periode),
                "indikator": indikator,
                "nilai": nilai_gold,
                "satuan": "persen",
                "_lineage_silver": _simpan_lineage(lineage),
                "status_data": (
                    "tersedia"
                    if lengkap
                    else "missing_sejati"
                ),
            })

    return pd.DataFrame(hasil)


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

    # 1. Pilih snapshot dan validasi data Silver.
    terpilih = pilih_snapshot(silver)
    terpilih = validasi_periode_tahunan(terpilih)
    pastikan_unik(terpilih)

    # 2. Siapkan referensi dan lineage dari Silver terpilih.
    dim, mulai = grid.muat_referensi()
    peta_lineage = _buat_peta_lineage(terpilih)

    # 3. Bentuk indikator elektrifikasi.
    listrik = _buat_listrik(
        terpilih, dim, mulai, peta_lineage
    )

    # 4. Bentuk tiga indikator bahan bakar.
    bahan_bakar = _buat_bahan_bakar(
        terpilih, dim, mulai, peta_lineage
    )

    # 5. Gabungkan seluruh indikator Gold.
    gold = pd.concat(
        [listrik, bahan_bakar],
        ignore_index=True,
    )

    gold = gold.sort_values(
        ["wilayah_kode", "periode", "indikator"]
    ).reset_index(drop=True)

    # 6. Pastikan kunci panel Gold unik.
    kunci = ["wilayah_kode", "periode", "indikator"]
    duplikat = gold.duplicated(subset=kunci, keep=False)

    if duplikat.any():
        raise ValueError(
            "Ditemukan duplikasi kunci panel Gold:\n"
            + gold.loc[duplikat, kunci]
            .head(10)
            .to_string(index=False)
        )

    # 7. Tambahkan status audit patahan Sprint 1.
    gold["status_patahan"] = "tidak_terkonfirmasi"
    gold["catatan_patahan"] = (
        "Tidak ditemukan patahan seri nasional terkonfirmasi. "
        "Perubahan lokal dipertahankan sesuai keputusan K-017."
    )

    # 8. Tandai kandidat outlier berdasarkan hasil audit Sprint 1.
    gold = tandai_outlier(gold, ROOT)


    # 9. Simpan panel Gold.
    jalur = GOLD_DIR / "panel.parquet"
    gold.to_parquet(jalur, index=False)

    print(
        f"Gold: {len(gold):,} baris -> "
        f"{jalur.relative_to(ROOT)}"
    )
    print(
        "Ringkasan status:",
        gold["status_data"].value_counts().to_dict(),
    )
    print("Jumlah indikator:", gold["indikator"].nunique())

    hasil = {"panel": gold}

    # 10. Bangun tabel nasional dan rekonsiliasi.
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

        print(f"Gold nasional: {len(nas):,} baris")
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
            f"({n_pair} berpasangan)"
        )

        hasil["rekonsiliasi"] = rek

    # 11. Muat Silver dan seluruh hasil Gold ke SQLite.
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
