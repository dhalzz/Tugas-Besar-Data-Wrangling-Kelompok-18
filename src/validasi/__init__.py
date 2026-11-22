"""Aturan validasi dasar untuk keluaran Silver."""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import pandera.pandas as pa
from pandera import Check


ROOT = Path(__file__).resolve().parents[2]
TOLERANSI_PERSEN = 1.0

# Isi dan sesuaikan nama bahan bakar dengan nilai rincian di data Silver Anda.
KATEGORI_BAHAN_BAKAR = {
    "listrik": "bersih",
    "gas": "bersih",
    "lpg": "bersih",
    "minyak tanah": "tidak_bersih",
    "kayu bakar": "tidak_bersih",
    "arang": "tidak_bersih",
    "biomassa": "tidak_bersih",
    "lainnya": "lainnya",
}


def normalisasi_rincian(nilai):
    return " ".join(str(nilai).strip().casefold().split())


def buat_laporan(hasil):
    tujuan = ROOT / "reports" / "validasi.md"
    tujuan.parent.mkdir(parents=True, exist_ok=True)

    isi = [
        "# Laporan Validasi Silver",
        "",
        "Dibuat otomatis saat `python pipeline.py` dijalankan.",
        "",
        "| Aturan | Hasil | Keterangan |",
        "|---|---|---|",
    ]

    for item in hasil:
        status = "Lolos" if item["lolos"] else "Gagal"
        isi.append(
            f"| {item['aturan']} | {status} | {item['keterangan']} |"
        )

    tujuan.write_text("\n".join(isi) + "\n", encoding="utf-8")
    return tujuan


def jalankan(silver, gold=None):
    if not isinstance(silver, pd.DataFrame):
        raise TypeError("Validasi membutuhkan DataFrame keluaran tahap Silver.")

    kolom_wajib = {
        "seri_kode",
        "wilayah_kode",
        "periode",
        "rincian",
        "nilai",
        "satuan",
    }

    kolom_hilang = sorted(kolom_wajib - set(silver.columns))
    if kolom_hilang:
        raise ValueError(
            "Kolom Silver belum lengkap: " + ", ".join(kolom_hilang)
        )

    hasil = []

    # Aturan 1: nilai persen harus berada pada rentang 0--100.
    data_persen = silver[silver["satuan"].eq("persen")].copy()

    skema_persen = pa.DataFrameSchema(
        {
            "nilai": pa.Column(
                float,
                nullable=True,
                checks=Check.in_range(0, 100),
            )
        },
        strict=False,
        coerce=True,
    )

    try:
        skema_persen.validate(data_persen)
        hasil.append(
            {
                "aturan": "Nilai persen berada pada rentang 0--100",
                "lolos": True,
                "keterangan": f"{len(data_persen)} observasi diperiksa.",
            }
        )
    except pa.errors.SchemaErrors as error:
        hasil.append(
            {
                "aturan": "Nilai persen berada pada rentang 0--100",
                "lolos": False,
                "keterangan": (
                    f"{len(error.failure_cases)} pelanggaran ditemukan."
                ),
            }
        )

    # Aturan 2: kunci observasi harus unik.
    kunci = ["seri_kode", "wilayah_kode", "periode", "rincian"]
    jumlah_duplikat = int(silver.duplicated(kunci, keep=False).sum())

    hasil.append(
        {
            "aturan": "Kunci observasi Silver unik",
            "lolos": jumlah_duplikat == 0,
            "keterangan": f"{jumlah_duplikat} baris duplikat ditemukan.",
        }
    )

    # Aturan 3: satuan harus konsisten.
    satuan_lain = sorted(
        silver.loc[
            silver["satuan"].notna()
            & ~silver["satuan"].eq("persen"),
            "satuan",
        ]
        .astype(str)
        .unique()
    )

    hasil.append(
        {
            "aturan": "Satuan seri konsisten",
            "lolos": len(satuan_lain) == 0,
            "keterangan": (
                "Semua satuan adalah persen."
                if not satuan_lain
                else "Satuan tidak sesuai: " + ", ".join(satuan_lain)
            ),
        }
    )

    # Aturan 4 dan 5: khusus seri bahan bakar.
    bahan_bakar = silver[
        silver["seri_kode"]
        .astype(str)
        .str.contains("bahan_bakar|sdg7", case=False, na=False)
    ].copy()

    if bahan_bakar.empty:
        hasil.append(
            {
                "aturan": "Total bahan bakar per provinsi-tahun mendekati 100",
                "lolos": False,
                "keterangan": "Tidak ada data bahan bakar untuk diperiksa.",
            }
        )
        hasil.append(
            {
                "aturan": "Setiap jenis bahan bakar memiliki satu kategori",
                "lolos": False,
                "keterangan": "Tidak ada data bahan bakar untuk diperiksa.",
            }
        )
    else:
        grup = (
            bahan_bakar.groupby(["wilayah_kode", "periode"])["nilai"]
            .agg(["sum", "count", "size"])
        )

        grup_lengkap = grup[grup["count"].eq(grup["size"])]
        dikecualikan = len(grup) - len(grup_lengkap)

        jumlah_meleset = int(
            (grup_lengkap["sum"].sub(100).abs() > TOLERANSI_PERSEN).sum()
        )

        hasil.append(
            {
                "aturan": "Total bahan bakar per provinsi-tahun mendekati 100",
                "lolos": jumlah_meleset == 0,
                "keterangan": (
                    f"{len(grup_lengkap)} grup lengkap diperiksa; "
                    f"{jumlah_meleset} grup meleset lebih dari "
                    f"±{TOLERANSI_PERSEN}; "
                    f"{dikecualikan} grup dikecualikan karena nilai kosong."
                ),
            }
        )

        rincian = sorted(
            {
                normalisasi_rincian(x)
                for x in bahan_bakar["rincian"].dropna()
            }
        )

        belum_terpetakan = [
            x for x in rincian if x not in KATEGORI_BAHAN_BAKAR
        ]

        hasil.append(
            {
                "aturan": "Setiap jenis bahan bakar memiliki satu kategori",
                "lolos": len(belum_terpetakan) == 0,
                "keterangan": (
                    f"{len(rincian)} jenis bahan bakar diperiksa."
                    if not belum_terpetakan
                    else "Belum dipetakan: "
                    + ", ".join(belum_terpetakan)
                ),
            }
        )

    laporan = buat_laporan(hasil)

    aturan_validasi = len(hasil)
    aturan_lolos = sum(item["lolos"] for item in hasil)

    print(
        f"validasi: {aturan_lolos}/{aturan_validasi} aturan lolos "
        f"dan laporan dibuat di {laporan}"
    )

    return {
        "aturan_validasi": aturan_validasi,
        "aturan_lolos": aturan_lolos,
        "laporan": str(laporan),
    }