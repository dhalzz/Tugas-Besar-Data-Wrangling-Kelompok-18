"""Pemeriksa skema minimal tabel Silver tim. Milik starter — jangan diubah.

    python -m src.common.skema data/silver/silver.parquet

Ini pemeriksaan lantai, bukan pengganti validasi tim (tahap 8, pandera/Great Expectations).
"""
import sys
from pathlib import Path

import pandas as pd

from src.common.manifest import baca

KOLOM = ["sumber", "seri_kode", "wilayah_kode", "nama_wilayah", "periode", "jenis_periode",
         "rincian", "nilai", "satuan", "_berkas_raw", "_sha256_raw"]
KUNCI = ["sumber", "seri_kode", "wilayah_kode", "periode", "rincian", "_berkas_raw"]
JENIS_PERIODE = {"tahun": r"^\d{4}$", "semester": r"^\d{4}-S[12]$",
                 "triwulan": r"^\d{4}-Q[1-4]$", "bulan": r"^\d{4}-(0[1-9]|1[0-2])$"}


def periksa_silver(df, manifest=None):
    """Daftar pelanggaran (kosong = lolos)."""
    salah = []
    kurang = [k for k in KOLOM if k not in df.columns]
    if kurang:
        return [f"kolom wajib tidak ada: {kurang}"]
    if df.empty:
        return ["tabel kosong"]
    dup = df.duplicated(KUNCI).sum()
    if dup:
        salah.append(f"{dup} baris kembar pada kunci {KUNCI}")
    if not pd.api.types.is_numeric_dtype(df["nilai"]):
        salah.append("kolom nilai bukan numerik")
    elif df["nilai"].isna().any():
        salah.append(f"{df['nilai'].isna().sum()} nilai kosong: Silver hanya memuat observasi yang ada")
    if not pd.api.types.is_integer_dtype(df["wilayah_kode"]):
        salah.append("wilayah_kode bukan bilangan bulat (9999 = Indonesia, provinsi = kode BPS x 100)")
    for kol in KOLOM:
        if kol != "nilai" and df[kol].isna().any():
            salah.append(f"kolom {kol} punya {df[kol].isna().sum()} sel kosong")
    tak_dikenal = set(df["jenis_periode"].dropna()) - set(JENIS_PERIODE)
    if tak_dikenal:
        salah.append(f"jenis_periode tidak dikenal: {sorted(tak_dikenal)}")
    for jenis, pola in JENIS_PERIODE.items():
        bagian = df.loc[df["jenis_periode"] == jenis, "periode"].astype(str)
        buruk = (~bagian.str.match(pola)).sum()
        if buruk:
            salah.append(f"{buruk} periode tidak sesuai format {jenis} ({pola})")
    if manifest is not None:
        pasangan = df[["_berkas_raw", "_sha256_raw"]].drop_duplicates()
        beda = [b for b, h in pasangan.itertuples(index=False) if manifest.get(b) != h]
        if beda:
            salah.append(f"{len(beda)} berkas sumber tidak cocok dengan MANIFEST.csv, mis. {beda[:3]}")
    return salah


def main():
    jalur = Path(sys.argv[1] if len(sys.argv) > 1 else "data/silver/silver.parquet")
    df = pd.read_parquet(jalur)
    try:
        manifest = baca()
    except FileNotFoundError:
        manifest = None
        print("Peringatan: data/raw/MANIFEST.csv belum ada, lineage tidak diperiksa.")
    salah = periksa_silver(df, manifest)
    for s in salah:
        print(f"GAGAL  {s}")
    if salah:
        sys.exit(1)
    print(f"LOLOS  {len(df):,} baris, {df['seri_kode'].nunique()} seri, "
          f"{df['wilayah_kode'].nunique()} wilayah, {df['_berkas_raw'].nunique()} berkas sumber")


if __name__ == "__main__":
    main()
