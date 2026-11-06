"""Satu perintah reproduksi tim: data mentah -> Silver -> Gold -> validasi.

    python unduh_data.py --kasus <N>     # sekali, isi data/raw/
    python pipeline.py

Urutan tahap tidak diubah; isi tiap tahap di src/<tahap>/. Tahap 7 (skala, arsip WDI) ditulis
sebagai skrip terpisah di src/skala/ karena memakai unduhan tambahan.
"""
import sys
import time

from src import ekstraksi, gold, silver, validasi
from src.common.manifest import periksa


def main():
    n, salah = periksa()
    if salah:
        sys.exit(f"data/raw tidak cocok dengan MANIFEST.csv ({len(salah)} berkas). Jalankan ulang unduh_data.py.")
    print(f"data/raw: {n} berkas cocok dengan MANIFEST.csv")
    for nama, langkah in [("ekstraksi", lambda h: ekstraksi.jalankan()),
                          ("silver", lambda h: silver.jalankan(h["ekstraksi"])),
                          ("gold", lambda h: gold.jalankan(h["silver"])),
                          ("validasi", lambda h: validasi.jalankan(h["silver"], h["gold"]))]:
        mulai = time.time()
        hasil[nama] = langkah(hasil)
        print(f"{nama:<10} selesai dalam {time.time() - mulai:.1f} s")
    print("Periksa skema minimal: python -m src.common.skema data/silver/silver.parquet")


hasil = {}

if __name__ == "__main__":
    main()
