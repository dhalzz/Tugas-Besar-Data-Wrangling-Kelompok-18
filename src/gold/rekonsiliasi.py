"""Tahap 6: Tabel rekonsiliasi seri utama BPS vs pembanding nasional WDI dari Gold nasional."""

from __future__ import annotations

import pandas as pd

KATEGORI_SAH = {
    "definisi berbeda",
    "metode berbeda",
    "vintage berbeda",
    "cakupan berbeda",
    "belum terjelaskan",
    "tidak ada pasangan",
}

RINCIAN_BAHAN_BAKAR_BERSIH = ("Listrik", "Gas/Elpiji")

KOLOM = [
    "pasangan",
    "seri_utama",
    "seri_pembanding",
    "periode",
    "nilai_utama",
    "nilai_pembanding",
    "selisih",
    "kategori_penjelasan",
    "catatan",
    "_berkas_raw_utama",
    "_berkas_raw_pembanding",
]


def _klasifikasi_listrik(row: pd.Series) -> tuple[str, str]:
    p = str(row["periode"])
    ada_u = pd.notna(row["nilai_utama"])
    ada_p = pd.notna(row["nilai_pembanding"])

    if not ada_u:
        return (
            "tidak ada pasangan",
            "BPS var87 tidak menerbitkan data Indonesia pada periode ini; "
            "hanya WDI yang tersedia."
        )

    if not ada_p:
        return (
            "tidak ada pasangan",
            "WDI EG.ELC.ACCS.ZS belum menerbitkan data pada periode ini; "
            "hanya BPS var87 yang tersedia."
        )

    if p in {"2000", "2001", "2002"}:
        return (
            "cakupan berbeda",
            "Catatan Susenas BPS: tahun 2000 tidak mencacah Aceh & Maluku, "
            "2001 tanpa Aceh, 2002 hanya ibu kota provinsi "
            "(Aceh, Maluku, Malut, Papua); ditambah beda definisi "
            "PLN/rumah tangga vs semua listrik/penduduk.",
        )

    return (
        "definisi berbeda",
        "BPS var87 hanya mencakup listrik PLN dengan denominator rumah tangga "
        "(Susenas Maret), sedangkan WDI EG.ELC.ACCS.ZS mencakup seluruh "
        "sumber listrik dengan denominator penduduk.",
    )


def _klasifikasi_bahan_bakar(row: pd.Series) -> tuple[str, str]:
    p = str(row["periode"])
    ada_u = pd.notna(row["nilai_utama"])
    ada_p = pd.notna(row["nilai_pembanding"])

    if not ada_u:
        return (
            "tidak ada pasangan",
            "BPS sdg7_bahan_bakar tidak menyediakan nilai pada periode ini, "
            "sedangkan WDI tersedia."
        )

    if not ada_p:
        return (
            "tidak ada pasangan",
            "WDI EG.CFT.ACCS.ZS tidak menyediakan nilai pada periode ini, "
            "sedangkan BPS tersedia."
        )

    if p in {"2001", "2007", "2008"}:
        return (
            "metode berbeda",
            "Selisih besar pada awal seri dan masa transisi cepat konversi minyak tanah ke elpiji: "
            "BPS mencatat hasil survei Susenas tahunan langsung, sedangkan WDI/WHO memakai estimasi model yang dimuluskan.",
        )

    return (
        "definisi berbeda",
        "Agregat BPS (Listrik + Gas/Elpiji, mengecualikan minyak tanah sesuai pedoman WHO) memakai denominator rumah tangga, "
        "sedangkan WDI EG.CFT.ACCS.ZS memakai denominator penduduk dan model Tracking SDG 7.",
    )


def _pasangkan(
    df_utama: pd.DataFrame,
    df_pembanding: pd.DataFrame,
    pasangan: str,
    seri_utama: str,
    seri_pembanding: str,
    klasifikator,
) -> pd.DataFrame:
    u = df_utama[["periode", "nilai", "_berkas_raw"]].rename(
        columns={"nilai": "nilai_utama", "_berkas_raw": "_berkas_raw_utama"}
    )
    p = df_pembanding[["periode", "nilai", "_berkas_raw"]].rename(
        columns={"nilai": "nilai_pembanding", "_berkas_raw": "_berkas_raw_pembanding"}
    )
    gabung = pd.merge(u, p, on="periode", how="outer").sort_values("periode").reset_index(drop=True)
    gabung["pasangan"] = pasangan
    gabung["seri_utama"] = seri_utama
    gabung["seri_pembanding"] = seri_pembanding
    gabung["selisih"] = (gabung["nilai_utama"] - gabung["nilai_pembanding"]).round(4)

    hasil_kat = gabung.apply(klasifikator, axis=1, result_type="expand")
    gabung["kategori_penjelasan"] = hasil_kat[0]
    gabung["catatan"] = hasil_kat[1]
    return gabung[KOLOM]


def bangun_rekonsiliasi(nasional: pd.DataFrame) -> pd.DataFrame:
    """Bangun tabel rekonsiliasi seri utama BPS vs pembanding WDI dari tabel_nasional Gold."""

    # Pasangan 1: var87 (listrik PLN) vs EG.ELC.ACCS.ZS
    u_listrik = nasional[nasional["seri_kode"] == "var87"].copy()
    p_listrik = nasional[nasional["seri_kode"] == "EG.ELC.ACCS.ZS"].copy()

    rek_listrik = _pasangkan(
        u_listrik,
        p_listrik,
        pasangan="listrik",
        seri_utama="var87",
        seri_pembanding="EG.ELC.ACCS.ZS",
        klasifikator=_klasifikasi_listrik,
    )

    # Pasangan 2: agregat bahan bakar bersih vs EG.CFT.ACCS.ZS
    bb_bersih = (
        nasional[
            (nasional["seri_kode"] == "tabel:sdg7_bahan_bakar")
            & (nasional["rincian"].isin(RINCIAN_BAHAN_BAKAR_BERSIH))
        ]
        .groupby("periode", as_index=False)
        .agg(nilai=("nilai", "sum"), _berkas_raw=("_berkas_raw", "first"))
    )

    bb_bersih["nilai"] = bb_bersih["nilai"].round(4)

    p_bb = nasional[nasional["seri_kode"] == "EG.CFT.ACCS.ZS"].copy()

    rek_bb = _pasangkan(
        bb_bersih,
        p_bb,
        pasangan="bahan_bakar_bersih",
        seri_utama="tabel:sdg7_bahan_bakar (Listrik + Gas/Elpiji)",
        seri_pembanding="EG.CFT.ACCS.ZS",
        klasifikator=_klasifikasi_bahan_bakar,
    )

    # Gabungkan kedua pasangan
    rek = pd.concat([rek_listrik, rek_bb], ignore_index=True)

    # Pastikan kunci pasangan dan periode unik
    assert not rek.duplicated(["pasangan", "periode"]).any(), (
        "Kunci pasangan x periode tidak unik"
    )

    # Ambil baris yang memiliki kedua nilai
    berpasangan = rek[
        rek["nilai_utama"].notna()
        & rek["nilai_pembanding"].notna()
    ]

    # Periksa semua kategori rekonsiliasi
    kategori_tidak_sah = rek[
        ~rek["kategori_penjelasan"].isin(KATEGORI_SAH)
    ]

    if not kategori_tidak_sah.empty:
        print("\nBARIS DENGAN KATEGORI TIDAK SAH:")
        print(
            kategori_tidak_sah[
                [
                    "pasangan",
                    "periode",
                    "nilai_utama",
                    "nilai_pembanding",
                    "kategori_penjelasan",
                    "catatan",
                ]
            ].to_string(index=False)
        )

    # Semua baris wajib memiliki kategori yang sah
    assert rek["kategori_penjelasan"].isin(KATEGORI_SAH).all(), (
        "Ada baris rekonsiliasi tanpa kategori penjelasan yang sah"
    )

    # Semua baris berpasangan wajib memiliki selisih
    assert berpasangan["selisih"].notna().all(), (
        "Ada pasangan nilai tanpa selisih"
    )

    return rek
