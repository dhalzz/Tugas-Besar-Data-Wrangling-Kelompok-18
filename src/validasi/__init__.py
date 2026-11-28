"""Validasi otomatis Silver, Gold, dan rekonsiliasi untuk Capstone Data Wrangling."""

from __future__ import annotations

import json
from pathlib import Path
import json
import pandas as pd
import pandera.pandas as pa
from pandera import Check


ROOT = Path(__file__).resolve().parents[2]
REPORT_PATH = ROOT / "reports" / "validasi.md"

# Nilai 100.01 diterima sebagai toleransi pembulatan pada sumber BPS.
BATAS_PERSEN_MIN = 0.0
BATAS_PERSEN_MAKS = 100.01
TOLERANSI_TOTAL_BAHAN_BAKAR = 1.0

KATEGORI_BAHAN_BAKAR = {
    "listrik": "bersih",
    "gas/elpiji": "bersih",
    "kayu": "tidak_bersih",
    "arang/briket": "tidak_bersih",
    "minyak tanah": "tidak_bersih",
    "lainnya": "lainnya",
}

KOLOM_SILVER = {
    "seri_kode",
    "wilayah_kode",
    "periode",
    "rincian",
    "nilai",
    "satuan",
    "_berkas_raw",
    "_sha256_raw",
}

KOLOM_GOLD = {
    "wilayah_kode",
    "nama_provinsi",
    "periode",
    "indikator",
    "nilai",
    "satuan",
    "_lineage_silver",
    "status_data",
    "outlier",
    "status_patahan",
    "catatan_patahan",
    "sebelum_provinsi_ada",
    "tahun_tidak_diterbitkan",
    "sel_kosong_dalam_terbitan",
    "missing_sejati",
}


def normalisasi_rincian(nilai: object) -> str:
    """Normalisasi teks kategori bahan bakar untuk pemeriksaan aturan."""
    return " ".join(str(nilai).strip().casefold().split())


def tambah_hasil(
    hasil: list[dict],
    aturan: str,
    lolos: bool,
    diperiksa: int,
    pelanggaran: int,
    keterangan: str,
) -> None:
    """Tambahkan hasil satu aturan ke daftar laporan."""
    hasil.append(
        {
            "aturan": aturan,
            "lolos": bool(lolos),
            "diperiksa": int(diperiksa),
            "pelanggaran": int(pelanggaran),
            "keterangan": keterangan,
        }
    )


def buat_laporan(hasil: list[dict]) -> Path:
    """Tulis laporan Markdown yang dapat dibaca tim dan pembimbing."""
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)

    aturan_lolos = sum(item["lolos"] for item in hasil)
    aturan_gagal = len(hasil) - aturan_lolos

    isi = [
        "# Laporan Validasi Silver, Gold, dan Rekonsiliasi",
        "",
        "Dibuat otomatis saat `python pipeline.py` dijalankan.",
        "",
        f"- Jumlah aturan: **{len(hasil)}**",
        f"- Lolos: **{aturan_lolos}**",
        f"- Gagal: **{aturan_gagal}**",
        "",
        "| Aturan | Status | Baris diperiksa | Pelanggaran | Keterangan |",
        "|---|---|---:|---:|---|",
    ]

    for item in hasil:
        status = "Lolos" if item["lolos"] else "Gagal"
        keterangan = str(item["keterangan"]).replace("\n", " ")
        isi.append(
            f"| {item['aturan']} | {status} | {item['diperiksa']} | "
            f"{item['pelanggaran']} | {keterangan} |"
        )

    REPORT_PATH.write_text("\n".join(isi) + "\n", encoding="utf-8")
    return REPORT_PATH


def periksa_silver(silver: pd.DataFrame, hasil: list[dict]) -> None:
    """Jalankan aturan validasi pada keluaran Silver."""
    kolom_hilang = sorted(KOLOM_SILVER - set(silver.columns))
    if kolom_hilang:
        raise ValueError(
            "Kolom Silver belum lengkap: " + ", ".join(kolom_hilang)
        )

    # Aturan 1: nilai persen berada dalam batas yang diterima.
    data_persen = silver[silver["satuan"].eq("persen")].copy()

    skema_persen = pa.DataFrameSchema(
        {
            "nilai": pa.Column(
                float,
                nullable=True,
                checks=Check.in_range(BATAS_PERSEN_MIN, BATAS_PERSEN_MAKS),
            )
    },
    strict=False,
    coerce=True,
)

    try:
        skema_persen.validate(data_persen, lazy=True)
        tambah_hasil(
            hasil,
            "Nilai persen Silver berada pada rentang 0 sampai 100.01",
            True,
            len(data_persen),
            0,
            "Seluruh nilai persen memenuhi batas termasuk toleransi pembulatan 100.01.",
        )
    except pa.errors.SchemaErrors as error:
        pelanggaran = len(error.failure_cases)
        tambah_hasil(
            hasil,
            "Nilai persen Silver berada pada rentang 0 sampai 100.01",
            False,
            len(data_persen),
            pelanggaran,
            f"{pelanggaran} pelanggaran rentang nilai ditemukan.",
        )

    # Aturan 2: satu observasi Silver tidak boleh mempunyai kunci ganda.
    kunci_silver = ["seri_kode", "wilayah_kode", "periode", "rincian"]
    duplikat = int(silver.duplicated(kunci_silver, keep=False).sum())

    tambah_hasil(
        hasil,
        "Kunci observasi Silver unik",
        duplikat == 0,
        len(silver),
        duplikat,
        (
            "Tidak ada kombinasi seri, wilayah, periode, dan rincian yang ganda."
            if duplikat == 0
            else f"Ditemukan {duplikat} baris Silver dengan kunci ganda."
        ),
    )

    # Aturan 3: seluruh keluaran kasus ini menggunakan satuan persen.
    satuan_lain = sorted(
        silver.loc[
            silver["satuan"].notna() & ~silver["satuan"].eq("persen"),
            "satuan",
        ]
        .astype(str)
        .unique()
    )

    tambah_hasil(
        hasil,
        "Satuan Silver konsisten",
        not satuan_lain,
        len(silver),
        len(satuan_lain),
        (
            "Semua observasi Silver memakai satuan persen."
            if not satuan_lain
            else "Satuan di luar persen: " + ", ".join(satuan_lain)
        ),
    )

    # Aturan 4: kategori bahan bakar harus dapat dipetakan.
    bahan_bakar = silver[
        silver["seri_kode"].eq("tabel:sdg7_bahan_bakar")
    ].copy()

    rincian = sorted(
        {
            normalisasi_rincian(nilai)
            for nilai in bahan_bakar["rincian"].dropna()
            if normalisasi_rincian(nilai) != "jumlah"
        }
    )

    belum_terpetakan = [
        rincian_bakar
        for rincian_bakar in rincian
        if rincian_bakar not in KATEGORI_BAHAN_BAKAR
    ]

    tambah_hasil(
        hasil,
        "Kategori bahan bakar Silver terpetakan",
        not belum_terpetakan,
        len(rincian),
        len(belum_terpetakan),
        (
            f"{len(rincian)} kategori bahan bakar terpetakan."
            if not belum_terpetakan
            else "Kategori belum dipetakan: " + ", ".join(belum_terpetakan)
        ),
    )

    # Aturan 5: pada provinsi-tahun dengan data lengkap, total kategori
    # bahan bakar non-agregat harus mendekati 100 persen.
    bahan_bakar = bahan_bakar[
        bahan_bakar["rincian"]
        .map(normalisasi_rincian)
        .ne("jumlah")
    ].copy()

    grup = (
        bahan_bakar.groupby(["wilayah_kode", "periode"])["nilai"]
        .agg(["sum", "count", "size"])
    )
    grup_lengkap = grup[grup["count"].eq(grup["size"])]
    dikecualikan = len(grup) - len(grup_lengkap)

    meleset = int(
        (
            grup_lengkap["sum"]
            .sub(100)
            .abs()
            .gt(TOLERANSI_TOTAL_BAHAN_BAKAR)
        ).sum()
    )

    tambah_hasil(
        hasil,
        "Total kategori bahan bakar lengkap mendekati 100 persen",
        meleset == 0,
        len(grup_lengkap),
        meleset,
        (
            f"{len(grup_lengkap)} grup lengkap diperiksa; "
            f"{dikecualikan} grup dikecualikan karena ada nilai kosong."
            if meleset == 0
            else f"{meleset} grup meleset lebih dari "
            f"+/-{TOLERANSI_TOTAL_BAHAN_BAKAR} persen."
        ),
    )


def periksa_gold(
    silver: pd.DataFrame,
    gold: pd.DataFrame,
    hasil: list[dict],
) -> None:
    """Jalankan aturan validasi panel Gold dan lineage ke Silver."""
    kolom_hilang = sorted(KOLOM_GOLD - set(gold.columns))
    if kolom_hilang:
        raise ValueError(
            "Kolom Gold belum lengkap: " + ", ".join(kolom_hilang)
        )

    # Aturan 6: satu nilai saja untuk satu sel panel Gold.
    kunci_gold = ["wilayah_kode", "periode", "indikator"]
    duplikat = int(gold.duplicated(kunci_gold, keep=False).sum())

    tambah_hasil(
        hasil,
        "Kunci panel Gold unik",
        duplikat == 0,
        len(gold),
        duplikat,
        (
            "Tidak ada kombinasi wilayah, periode, dan indikator yang ganda."
            if duplikat == 0
            else f"Ditemukan {duplikat} baris Gold dengan kunci ganda."
        ),
    )

    # Aturan 7: setiap indikator hanya memakai satu satuan.
    satuan_per_indikator = gold.groupby("indikator")["satuan"].nunique(
        dropna=False
    )
    indikator_tidak_konsisten = satuan_per_indikator[
        satuan_per_indikator.ne(1)
    ]

    tambah_hasil(
        hasil,
        "Satuan per indikator Gold konsisten",
        indikator_tidak_konsisten.empty,
        len(satuan_per_indikator),
        len(indikator_tidak_konsisten),
        (
            "Setiap indikator Gold memiliki satu satuan yang konsisten."
            if indikator_tidak_konsisten.empty
            else "Indikator dengan satuan tidak konsisten: "
            + ", ".join(indikator_tidak_konsisten.index.astype(str))
        ),
    )

    # Aturan 8: nilai dan status Gold harus konsisten.
    nilai_tersedia = gold.loc[
        gold["status_data"].eq("tersedia"), "nilai"
    ]
    nilai_hilang = gold.loc[
        gold["status_data"].ne("tersedia"), "nilai"
    ]

    pelanggaran_tersedia = int(
        nilai_tersedia.isna().sum()
        + (
            (nilai_tersedia < BATAS_PERSEN_MIN)
            | (nilai_tersedia > BATAS_PERSEN_MAKS)
        ).sum()
    )
    pelanggaran_hilang = int(nilai_hilang.notna().sum())
    pelanggaran_status = pelanggaran_tersedia + pelanggaran_hilang

    tambah_hasil(
        hasil,
        "Nilai dan status_data Gold konsisten",
        pelanggaran_status == 0,
        len(gold),
        pelanggaran_status,
        (
            "Baris tersedia memiliki nilai sah; baris non-tersedia tidak memuat nilai."
            if pelanggaran_status == 0
            else f"{pelanggaran_status} ketidaksesuaian nilai dan status ditemukan."
        ),
    )

    # Aturan 10: penanda outlier, patahan, dan grid Gold harus valid.
    kolom_boolean = [
        "outlier",
        "sebelum_provinsi_ada",
        "tahun_tidak_diterbitkan",
        "sel_kosong_dalam_terbitan",
        "missing_sejati",
    ]

    pelanggaran_boolean = 0
    for kolom in kolom_boolean:
        if not pd.api.types.is_bool_dtype(gold[kolom]):
            pelanggaran_boolean += len(gold)
        else:
            pelanggaran_boolean += int(gold[kolom].isna().sum())

    status_patahan_valid = (
        gold["status_patahan"].notna()
        & gold["status_patahan"].astype(str).str.strip().ne("")
    )
    catatan_patahan_valid = (
        gold["catatan_patahan"].notna()
        & gold["catatan_patahan"].astype(str).str.strip().ne("")
    )

    pelanggaran_penanda = (
        pelanggaran_boolean
        + int((~status_patahan_valid).sum())
        + int((~catatan_patahan_valid).sum())
    )

    tambah_hasil(
        hasil,
        "Penanda outlier, patahan, dan grid Gold valid",
        pelanggaran_penanda == 0,
        len(gold),
        pelanggaran_penanda,
        (
            "Penanda outlier, patahan, dan empat penanda grid terisi dengan tipe yang valid."
            if pelanggaran_penanda == 0
            else f"Ditemukan {pelanggaran_penanda} pelanggaran pada penanda Gold."
        ),
    )
    # Aturan 9: setiap nilai Gold yang tersedia harus menaut ke Silver.
    kolom_kunci_lineage = [
        "wilayah_kode",
        "periode",
        "seri_kode",
        "rincian",
        "_berkas_raw",
        "_sha256_raw",
    ]

    kunci_silver = {
        tuple(str(nilai) for nilai in baris)
        for baris in silver[kolom_kunci_lineage].itertuples(
            index=False,
            name=None,
        )
    }

    pelanggaran_lineage = 0
    baris_tersedia = gold[gold["status_data"].eq("tersedia")]

    for _, baris in baris_tersedia.iterrows():
        try:
            lineage = json.loads(baris["_lineage_silver"])
        except (TypeError, json.JSONDecodeError):
            pelanggaran_lineage += 1
            continue

        if not isinstance(lineage, list) or not lineage:
            pelanggaran_lineage += 1
            continue

        cocok = True

        for sumber in lineage:
            if not isinstance(sumber, dict):
                cocok = False
                break

            kunci = (
                str(baris["wilayah_kode"]),
                str(baris["periode"]),
                str(sumber.get("seri_kode")),
                str(sumber.get("rincian")),
                str(sumber.get("_berkas_raw")),
                str(sumber.get("_sha256_raw")),
            )

            if kunci not in kunci_silver:
                cocok = False
                break

        if not cocok:
            pelanggaran_lineage += 1

    tambah_hasil(
        hasil,
        "Setiap nilai Gold tersedia memiliki lineage Silver yang sah",
        pelanggaran_lineage == 0,
        len(baris_tersedia),
        pelanggaran_lineage,
        (
            "Seluruh nilai Gold tersedia dapat ditelusuri ke baris Silver."
            if pelanggaran_lineage == 0
            else f"{pelanggaran_lineage} baris Gold tidak memiliki lineage Silver yang sah."
        ),
    )


def periksa_rekonsiliasi(hasil: list[dict]) -> None:
    """
    Periksa tabel rekonsiliasi pasangan seri utama dan pembanding nasional.

    Tabel yang diharapkan berbentuk satu baris per pasangan, misalnya:
    tahun, indikator, nilai_bps, nilai_wdi, selisih, kategori_selisih
    """
    kandidat = [
        ROOT / "data" / "gold" / "tabel_rekonsiliasi.parquet",
        ROOT / "data" / "gold" / "tabel_rekonsiliasi.csv",
        ROOT / "data" / "gold" / "rekonsiliasi.parquet",
        ROOT / "data" / "gold" / "rekonsiliasi.csv",
]

    path = next((item for item in kandidat if item.exists()), None)

    if path is None:
        tambah_hasil(
            hasil,
            "Pasangan rekonsiliasi memiliki kategori selisih",
            False,
            0,
            1,
            (
                "Tabel rekonsiliasi berpasangan belum tersedia di data/gold. "
                "CSV laporan nasional saat ini masih berbentuk panjang, bukan pasangan BPS-WDI."
            ),
        )
        return

    if path.suffix == ".parquet":
        rekonsiliasi = pd.read_parquet(path)
    else:
        rekonsiliasi = pd.read_csv(path)

    kandidat_utama = ["nilai_bps", "nilai_utama", "seri_utama"]
    kandidat_pembanding = ["nilai_wdi", "nilai_pembanding", "seri_pembanding"]
    kandidat_kategori = [
        "kategori_penjelasan",
        "kategori_selisih",
        "kategori",
        "status_rekonsiliasi",
    ]

    kolom_utama = next(
        (kolom for kolom in kandidat_utama if kolom in rekonsiliasi.columns),
        None,
    )
    kolom_pembanding = next(
        (
            kolom
            for kolom in kandidat_pembanding
            if kolom in rekonsiliasi.columns
        ),
        None,
    )
    kolom_kategori = next(
        (
            kolom
            for kolom in kandidat_kategori
            if kolom in rekonsiliasi.columns
        ),
        None,
    )

    if None in [kolom_utama, kolom_pembanding, kolom_kategori]:
        tambah_hasil(
            hasil,
            "Pasangan rekonsiliasi memiliki kategori selisih",
            False,
            len(rekonsiliasi),
            1,
            (
                "Kolom pasangan BPS-WDI atau kategori_selisih belum lengkap pada "
                f"{path.relative_to(ROOT)}."
            ),
        )
        return

    berpasangan = (
        rekonsiliasi[kolom_utama].notna()
        & rekonsiliasi[kolom_pembanding].notna()
    )
    kategori_kosong = (
        rekonsiliasi.loc[berpasangan, kolom_kategori]
        .isna()
        .sum()
    )
    kategori_kosong += int(
        rekonsiliasi.loc[berpasangan, kolom_kategori]
        .astype(str)
        .str.strip()
        .eq("")
        .sum()
    )

    tambah_hasil(
        hasil,
        "Pasangan rekonsiliasi memiliki kategori selisih",
        kategori_kosong == 0,
        int(berpasangan.sum()),
        int(kategori_kosong),
        (
            "Seluruh pasangan seri utama dan pembanding memiliki kategori selisih."
            if kategori_kosong == 0
            else f"{kategori_kosong} pasangan belum memiliki kategori selisih."
        ),
    )


def jalankan(silver: pd.DataFrame, gold: dict | pd.DataFrame | None = None) -> dict:
    """Jalankan seluruh validasi dan tulis laporan ke reports/validasi.md."""
    if not isinstance(silver, pd.DataFrame):
        raise TypeError("Validasi membutuhkan DataFrame keluaran tahap Silver.")

    if isinstance(gold, dict):
        gold_df = gold.get("panel")
    else:
        gold_df = gold

    if not isinstance(gold_df, pd.DataFrame):
        panel_path = ROOT / "data" / "gold" / "panel.parquet"

        if panel_path.exists():
            gold_df = pd.read_parquet(panel_path)
        else:
            raise TypeError(
                "Validasi membutuhkan DataFrame panel Gold atau data/gold/panel.parquet."
            )

    hasil: list[dict] = []

    periksa_silver(silver, hasil)
    periksa_gold(silver, gold_df, hasil)
    periksa_rekonsiliasi(hasil)

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
