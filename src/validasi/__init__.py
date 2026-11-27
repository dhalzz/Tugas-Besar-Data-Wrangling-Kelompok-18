"""Aturan validasi dasar untuk keluaran Silver."""
from __future__ import annotations

from pathlib import Path
import json
import pandas as pd
import pandera.pandas as pa
from pandera import Check


ROOT = Path(__file__).resolve().parents[2]
TOLERANSI_PERSEN = 1.0

# Isi dan sesuaikan nama bahan bakar dengan nilai rincian di data Silver Anda.
KATEGORI_BAHAN_BAKAR = {
    "listrik": "bersih",
    "gas/elpiji": "bersih",
    "minyak tanah": "tidak_bersih",
    "kayu": "tidak_bersih",
    "arang/briket": "tidak_bersih",
    "lainnya": "lainnya",
}


def normalisasi_rincian(nilai):
    return " ".join(str(nilai).strip().casefold().split())


def buat_laporan(hasil):
    tujuan = ROOT / "reports" / "validasi.md"
    tujuan.parent.mkdir(parents=True, exist_ok=True)

    isi = [
        "# Laporan Validasi Silver dan Gold",
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
                checks=Check.in_range(0, 100.01),
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

    bahan_bakar = bahan_bakar[
        ~bahan_bakar["rincian"]
        .astype(str)
        .str.strip()
        .str.casefold()
        .eq("jumlah")
    ]

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

    
    # Aturan 6: validasi struktur dan kunci unik Gold.
    if gold is not None:
        kolom_gold = {
            "wilayah_kode",
            "periode",
            "indikator",
            "nilai",
            "outlier",
            "status_patahan",
            "catatan_patahan",
        }

        kolom_hilang = sorted(kolom_gold - set(gold.columns))
        kolom_lengkap = len(kolom_hilang) == 0

        hasil.append({
            "aturan": "Kolom wajib Gold tersedia",
            "lolos": kolom_lengkap,
            "keterangan": (
                "Semua kolom wajib tersedia."
                if kolom_lengkap
                else "Kolom hilang: " + ", ".join(kolom_hilang)
            ),
        })

        if kolom_lengkap:
            kunci_gold = ["wilayah_kode", "periode", "indikator"]
            duplikat_gold = int(
                gold.duplicated(kunci_gold, keep=False).sum()
            )

            hasil.append({
                "aturan": "Kunci provinsi-periode-indikator Gold unik",
                "lolos": duplikat_gold == 0,
                "keterangan": f"{duplikat_gold} baris duplikat ditemukan.",
            })

            hasil.append({
                "aturan": "Penanda outlier dan patahan Gold tersedia",
                "lolos": (
                    gold["outlier"].notna().all()
                    and gold["status_patahan"].notna().all()
                    and gold["catatan_patahan"].notna().all()
                ),
                "keterangan": (
                    f"{int(gold['outlier'].sum())} baris ditandai outlier; "
                    "status patahan dan catatannya tersedia."
                ),
            })
        else:
            hasil.append({
                "aturan": "Kunci provinsi-periode-indikator Gold unik",
                "lolos": False,
                "keterangan": "Tidak diperiksa karena kolom wajib belum lengkap.",
            })
            hasil.append({
                "aturan": "Penanda outlier dan patahan Gold tersedia",
                "lolos": False,
                "keterangan": "Tidak diperiksa karena kolom wajib belum lengkap.",
            })


    # Aturan 9, 10, dan 11: verifikasi lineage dan komponen Gold.
    if gold is not None:
        kolom_lineage = {
            "wilayah_kode",
            "periode",
            "seri_kode",
            "rincian",
            "_berkas_raw",
            "_sha256_raw",
        }

        kolom_silver_lineage = kolom_lineage

        struktur_lineage_lengkap = (
            kolom_silver_lineage.issubset(silver.columns)
            and {"_lineage_silver", "status_data", "indikator"}.issubset(
                gold.columns
            )
        )

        # Siapkan indeks identitas sumber Silver beserta nilainya.
        indeks_silver = {}

        if struktur_lineage_lengkap:
            for _, r in silver.iterrows():
                identitas = (
                    int(r["wilayah_kode"]),
                    str(r["periode"]),
                    str(r["seri_kode"]),
                    str(r["rincian"]),
                    str(r["_berkas_raw"]),
                    str(r["_sha256_raw"]),
                )
                indeks_silver.setdefault(identitas, []).append(r["nilai"])

        # Baca JSON lineage setiap baris Gold.
        lineage_gold = []
        jumlah_json_invalid = 0

        for raw in gold.get("_lineage_silver", pd.Series(dtype=object)):
            try:
                daftar = json.loads(raw) if isinstance(raw, str) else None

                if not isinstance(daftar, list):
                    raise ValueError("Lineage bukan daftar.")

                if not all(isinstance(x, dict) for x in daftar):
                    raise ValueError("Isi lineage tidak valid.")

                lineage_gold.append(daftar)

            except (ValueError, TypeError, json.JSONDecodeError):
                lineage_gold.append([])
                jumlah_json_invalid += 1

        # Aturan 9: setiap referensi lineage harus cocok dengan Silver.
        total_referensi = 0
        referensi_tidak_cocok = 0

        if struktur_lineage_lengkap:
            for i, daftar in enumerate(lineage_gold):
                wilayah = int(gold.iloc[i]["wilayah_kode"])
                periode = str(gold.iloc[i]["periode"])

                for sumber in daftar:
                    total_referensi += 1

                    try:
                        identitas = (
                            wilayah,
                            periode,
                            str(sumber["seri_kode"]),
                            str(sumber["rincian"]),
                            str(sumber["_berkas_raw"]),
                            str(sumber["_sha256_raw"]),
                        )

                        if identitas not in indeks_silver:
                            referensi_tidak_cocok += 1

                    except (KeyError, TypeError, ValueError):
                        referensi_tidak_cocok += 1

        else:
            referensi_tidak_cocok = 1

        referensi_valid = (
            struktur_lineage_lengkap
            and referensi_tidak_cocok == 0
            and jumlah_json_invalid == 0
        )

        hasil.append({
            "aturan": "Seluruh referensi lineage Gold cocok dengan Silver",
            "lolos": referensi_valid,
            "keterangan": (
                f"{total_referensi} referensi diperiksa; "
                f"{referensi_tidak_cocok} tidak cocok; "
                f"{jumlah_json_invalid} JSON lineage tidak valid."
            ),
        })

        # Aturan 10: setiap nilai tersedia wajib memiliki lineage.
        tanpa_lineage = 0

        if "status_data" in gold.columns:
            for i, (_, r) in enumerate(gold.iterrows()):
                if r["status_data"] == "tersedia":
                    if i >= len(lineage_gold) or not lineage_gold[i]:
                        tanpa_lineage += 1

        else:
            tanpa_lineage = len(gold)

        hasil.append({
            "aturan": "Nilai Gold tersedia memiliki lineage",
            "lolos": tanpa_lineage == 0,
            "keterangan": (
                f"{tanpa_lineage} baris tersedia tanpa lineage."
            ),
        })

        # Aturan 11: seluruh komponen indikator tersedia harus ditemukan.
        komponen_gold = {
            "elektrifikasi": ["elektrifikasi"],
            "bahan_bakar_bersih": ["Listrik", "Gas/Elpiji"],
            "bahan_bakar_lainnya": ["Lainnya"],
            "bahan_bakar_tidak_bersih": [
                "Kayu",
                "Arang/Briket",
                "Minyak Tanah",
            ],
        }

        komponen_tidak_lengkap = 0

        if struktur_lineage_lengkap:
            for i, (_, r) in enumerate(gold.iterrows()):
                if r["status_data"] != "tersedia":
                    continue

                daftar = (
                    lineage_gold[i]
                    if i < len(lineage_gold)
                    else []
                )

                wilayah = int(r["wilayah_kode"])
                periode = str(r["periode"])
                komponen = komponen_gold.get(r["indikator"], [])

                for rincian in komponen:
                    ditemukan = False

                    for sumber in daftar:
                        if str(sumber.get("rincian")) != rincian:
                            continue

                        identitas = (
                            wilayah,
                            periode,
                            str(sumber.get("seri_kode")),
                            str(sumber.get("rincian")),
                            str(sumber.get("_berkas_raw")),
                            str(sumber.get("_sha256_raw")),
                        )

                        nilai_silver = indeks_silver.get(identitas, [])

                        if any(pd.notna(nilai) for nilai in nilai_silver):
                            ditemukan = True
                            break

                    if not ditemukan:
                        komponen_tidak_lengkap += 1

        else:
            komponen_tidak_lengkap = 1

        hasil.append({
            "aturan": "Komponen pembentuk nilai Gold tersedia dan lengkap",
            "lolos": komponen_tidak_lengkap == 0,
            "keterangan": (
                f"{komponen_tidak_lengkap} komponen pada nilai Gold "
                "tersedia tidak memiliki sumber bernilai."
            ),
        })

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