
"""Tahap Gold: pembentukan panel provinsi x tahun x indikator."""

from pathlib import Path
import json

import pandas as pd

from src.silver import grid

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


def jalankan(silver):
    """Bentuk dan simpan panel Gold dari DataFrame Silver."""
    GOLD_DIR.mkdir(parents=True, exist_ok=True)

    dim, mulai = grid.muat_referensi()
    peta_lineage = _buat_peta_lineage(silver)

    listrik = _buat_listrik(
        silver,
        dim,
        mulai,
        peta_lineage,
    )

    bahan_bakar = _buat_bahan_bakar(
        silver,
        dim,
        mulai,
        peta_lineage,
    )

    gold = pd.concat(
        [listrik, bahan_bakar],
        ignore_index=True,
    )

    gold = gold.sort_values(
        ["wilayah_kode", "periode", "indikator"]
    ).reset_index(drop=True)

    kunci = [
        "wilayah_kode",
        "periode",
        "indikator",
    ]

    if gold.duplicated(kunci).any():
        raise ValueError("Kunci panel Gold tidak unik.")

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

    print(
        "Jumlah indikator:",
        gold["indikator"].nunique(),
    )

    return {"panel": gold}
