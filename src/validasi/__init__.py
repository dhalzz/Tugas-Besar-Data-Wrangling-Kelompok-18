"""Tahap Validasi: pemeriksaan dasar Silver dan Gold."""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
REPORT_DIR = ROOT / "reports"


def jalankan(silver, gold):
    """Validasi dasar Silver dan Gold, lalu tulis laporan."""
    REPORT_DIR.mkdir(parents=True, exist_ok=True)

    hasil = []

    # Validasi Silver
    hasil.append(f"Jumlah baris Silver: {len(silver):,}")
    hasil.append(f"Jumlah kolom Silver: {len(silver.columns)}")

    kolom_wajib = [
        "sumber",
        "seri_kode",
        "wilayah_kode",
        "nama_wilayah",
        "periode",
        "nilai",
        "satuan",
        "_berkas_raw",
        "_sha256_raw",
    ]

    kolom_hilang = [kolom for kolom in kolom_wajib if kolom not in silver.columns]

    if kolom_hilang:
        hasil.append(f"FAIL: Kolom Silver hilang: {kolom_hilang}")
    else:
        hasil.append("PASS: Kolom wajib Silver tersedia")

    if silver["_berkas_raw"].isna().any():
        hasil.append("FAIL: Terdapat lineage berkas raw kosong")
    else:
        hasil.append("PASS: Lineage berkas raw lengkap")

    if silver["_sha256_raw"].isna().any():
        hasil.append("FAIL: Terdapat SHA256 kosong")
    else:
        hasil.append("PASS: SHA256 tersedia")

    # Validasi Gold
    hasil.append(f"Jumlah tabel Gold: {len(gold)}")

    for nama, df in gold.items():
        hasil.append(f"Tabel Gold '{nama}': {len(df):,} baris")

        if df.empty:
            hasil.append(f"FAIL: Tabel Gold '{nama}' kosong")
        else:
            hasil.append(f"PASS: Tabel Gold '{nama}' tidak kosong")

    laporan = "\n".join(hasil)

    jalur_laporan = REPORT_DIR / "validasi.md"
    jalur_laporan.write_text(
        "# Laporan Validasi\n\n" + laporan + "\n",
        encoding="utf-8",
    )

    print(laporan)
    print(f"Laporan validasi: {jalur_laporan.relative_to(ROOT)}")

    return {"laporan": laporan}
