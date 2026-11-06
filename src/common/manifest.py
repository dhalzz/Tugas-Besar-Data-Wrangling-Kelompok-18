"""Lineage berkas mentah: sha256 tiap berkas di data/raw menurut MANIFEST.csv.

    from src.common.manifest import sha256_raw
    sha256_raw("bps/2026-10-20/sdg8_tpt.csv")   # -> isi kolom _sha256_raw

Jangan menulis sha256 dengan tangan; ambil dari fungsi ini agar Silver dapat dilacak ke berkas asalnya.
"""
import csv
import hashlib
from functools import lru_cache
from pathlib import Path

RAW = Path(__file__).resolve().parents[2] / "data" / "raw"


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for blok in iter(lambda: f.read(1 << 20), b""):
            h.update(blok)
    return h.hexdigest()


@lru_cache(maxsize=None)
def baca(raw=RAW):
    """{berkas relatif data/raw: sha256} dari MANIFEST.csv."""
    with open(Path(raw) / "MANIFEST.csv", encoding="utf-8") as f:
        return {r["berkas"]: r["sha256"] for r in csv.DictReader(f)}


def sha256_raw(berkas, raw=RAW):
    try:
        return baca(Path(raw))[str(berkas)]
    except KeyError:
        raise KeyError(f"{berkas} tidak ada di MANIFEST.csv; pakai jalur relatif terhadap data/raw/") from None


def periksa(raw=RAW):
    """Hitung ulang sha256 semua berkas di MANIFEST. Mengembalikan (jumlah, daftar yang tidak cocok)."""
    raw = Path(raw)
    manifest = baca(raw)
    salah = [b for b, h in manifest.items() if not (raw / b).exists() or sha256(raw / b) != h]
    return len(manifest), salah
