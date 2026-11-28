
"""Tahap Gold: pembentukan panel provinsi x tahun x indikator."""

from pathlib import Path
from . import nasional, rekonsiliasi, muat_sql
import json

import pandas as pd

from src.silver import grid
from src.gold.pemilihan import tandai_outlier

ROOT = Path(__file__).resolve().parents[2]
GOLD_DIR = ROOT / "data" / "gold"

KOMPONEN = {
    "bahan_bakar_bersih": [
        "Listrik",
        "Gas/Elpiji",
    ],
    "bahan_bakar_tidak_bersih": [
        "Kayu",
        "Arang/Briket",
        "Minyak Tanah",
    ],
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
    """Bentuk panel elektrifikasi dengan mempertahankan penanda grid."""
    cfg = grid.SERI["var87"]

    panel = grid.grid_seri(
        silver,
        dim,
        mulai,
        cfg,
    )

    hasil = []

    kolom_penanda = [
        "sebelum_provinsi_ada",
        "tahun_tidak_diterbitkan",
        "sel_kosong_dalam_terbitan",
        "missing_sejati",
    ]

    for _, r in panel.iterrows():
        kunci = (
            int(r["wilayah_kode"]),
            str(r["periode"]),
            "elektrifikasi",
        )

        lineage = peta_lineage.get(kunci, [])

        baris = {
            "wilayah_kode": int(r["wilayah_kode"]),
            "nama_provinsi": r["nama_provinsi"],
            "periode": str(r["periode"]),
            "indikator": "elektrifikasi",
            "nilai": r["nilai"],
            "satuan": "persen",
            "_lineage_silver": _simpan_lineage(lineage),
        }

        for kolom in kolom_penanda:
            baris[kolom] = bool(r[kolom])

        if baris["sebelum_provinsi_ada"]:
            baris["status_data"] = "sebelum_provinsi_ada"
        elif baris["tahun_tidak_diterbitkan"]:
            baris["status_data"] = "tahun_tidak_diterbitkan"
        elif baris["missing_sejati"]:
            baris["status_data"] = "missing_sejati"
        else:
            baris["status_data"] = "tersedia"

        hasil.append(baris)

    return pd.DataFrame(hasil)


def _buat_bahan_bakar(silver, dim, mulai, peta_lineage):
    """Bentuk indikator bahan bakar dengan mempertahankan penanda grid."""
    cfg = grid.SERI["sdg7_bahan_bakar"]

    panel = grid.grid_seri(
        silver,
        dim,
        mulai,
        cfg,
    )

    hasil = []

    kolom_penanda = [
        "sebelum_provinsi_ada",
        "tahun_tidak_diterbitkan",
        "sel_kosong_dalam_terbitan",
        "missing_sejati",
    ]

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

            bagian = grup[
                grup["rincian"].isin(komponen)
            ]

            lineage = []
            for jenis in komponen:
                kunci = (int(kode), str(periode), jenis)
                lineage.extend(peta_lineage.get(kunci, []))

            baris = {
                "wilayah_kode": int(kode),
                "nama_provinsi": nama,
                "periode": str(periode),
                "indikator": indikator,
                "nilai": nilai_gold,
                "satuan": "persen",
                "_lineage_silver": _simpan_lineage(lineage),
            }

            for kolom in kolom_penanda:
                baris[kolom] = bool(bagian[kolom].any())

            if baris["sebelum_provinsi_ada"]:
                baris["status_data"] = "sebelum_provinsi_ada"
            elif baris["tahun_tidak_diterbitkan"]:
                baris["status_data"] = "tahun_tidak_diterbitkan"
            elif baris["missing_sejati"]:
                baris["status_data"] = "missing_sejati"
            elif lengkap:
                baris["status_data"] = "tersedia"
            else:
                baris["status_data"] = "komponen_tidak_lengkap"

            hasil.append(baris)

    return pd.DataFrame(hasil)

import pandas as pd


def jalankan(silver, mentah):
    """Bentuk panel Gold, tabel nasional, rekonsiliasi, dan SQLite."""
    GOLD_DIR.mkdir(parents=True, exist_ok=True)

    dim, mulai = grid.muat_referensi()
    peta_lineage = _buat_peta_lineage(silver)

    listrik = _buat_listrik(
        silver, dim, mulai, peta_lineage
    )

    bahan_bakar = _buat_bahan_bakar(
        silver, dim, mulai, peta_lineage
    )

    gold = pd.concat(
        [listrik, bahan_bakar],
        ignore_index=True,
    )

    gold = gold.sort_values(
        ["wilayah_kode", "periode", "indikator"]
    ).reset_index(drop=True)

    # Pastikan kunci panel Gold unik.
    kunci = ["wilayah_kode", "periode", "indikator"]
    if gold.duplicated(subset=kunci).any():
        raise ValueError("Kunci panel Gold tidak unik.")

    # Tambahkan status audit patahan Sprint 1.
    gold["status_patahan"] = "tidak_terkonfirmasi"
    gold["catatan_patahan"] = (
        "Tidak ditemukan bukti patahan seri yang terkonfirmasi "
        "berdasarkan audit Sprint 1. Perubahan ekstrem lokal "
        "dipertahankan dan ditandai sebagai kandidat outlier "
        "sesuai keputusan K-017, K-020, dan K-021."
    )

    # Tandai kandidat outlier Sprint 1.
    gold = tandai_outlier(gold, ROOT)

    # Simpan panel Gold.
    gold.to_parquet(GOLD_DIR / "panel.parquet", index=False)

    # Bangun tabel nasional dari Silver dan hasil ekstraksi.
    nas = nasional.bangun_nasional(silver, mentah)

    nas.to_parquet(
        GOLD_DIR / "tabel_nasional.parquet",
        index=False,
    )
    nas.to_csv(
        GOLD_DIR / "tabel_nasional.csv",
        index=False,
    )

    # Bangun tabel rekonsiliasi BPS-WDI.
    rek = rekonsiliasi.bangun_rekonsiliasi(nas)

    rek.to_parquet(
        GOLD_DIR / "tabel_rekonsiliasi.parquet",
        index=False,
    )
    rek.to_csv(
        GOLD_DIR / "tabel_rekonsiliasi.csv",
        index=False,
    )

    # Muat seluruh tabel ke SQLite.
    hasil_gold = {
        "panel": gold,
        "nasional": nas,
        "rekonsiliasi": rek,
    }

    ringkasan_sql = muat_sql.muat_semua(
        silver,
        hasil_gold,
    )

    print(
        f"Gold panel: {len(gold):,} baris"
    )
    print(
        f"Gold nasional: {len(nas):,} baris"
    )
    print(
        f"Gold rekonsiliasi: {len(rek):,} baris"
    )
    print(
        "SQLite:",
        ringkasan_sql,
    )

    print(
        "Ringkasan status:",
        gold["status_data"].value_counts().to_dict(),
    )
    print(
        "Jumlah indikator:",
        gold["indikator"].nunique(),
    )

    return hasil_gold
