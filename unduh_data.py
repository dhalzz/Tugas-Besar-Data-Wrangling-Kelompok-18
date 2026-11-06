"""Unduh paket data mentah kasus tim dari Release repositori starter, lalu periksa sha256-nya.

    python unduh_data.py --kasus 7              # paket kasus 07 ke data/raw/
    python unduh_data.py --arsip-wdi            # arsip WDI 142 rilis (tahap 7) ke data/raw/wdi_arsip/

Isi paket: data/raw/<sumber>/<snapshot>/..., data/raw/MANIFEST.csv, data/KASUS.md, data/LISENSI.md.
Folder data/raw/ tidak di-commit; siapa pun di tim dapat mengunduh ulang dan mendapat berkas yang sama.
"""
import argparse
import io
import json
import shutil
import sys
import urllib.request
import zipfile
from pathlib import Path

from src.common.manifest import periksa

RILIS = "https://github.com/sains-data/capstone-dw-2026-starter/releases/download/data-2026.1"
AKAR = Path(__file__).resolve().parent
DATA = AKAR / "data"


def ambil(nama):
    print(f"Mengunduh {nama} ...", file=sys.stderr)
    with urllib.request.urlopen(f"{RILIS}/{nama}", timeout=120) as r:
        return zipfile.ZipFile(io.BytesIO(r.read()))


def bongkar(z, ke_raw, lain=None):
    """Salin isi ZIP (tanpa folder akar) — data/raw/... ke data/raw/, berkas lain sesuai peta `lain`."""
    for info in z.infolist():
        if info.is_dir():
            continue
        rel = info.filename.split("/", 1)[1]
        if rel.startswith("data/raw/"):
            tujuan = ke_raw / rel.removeprefix("data/raw/")
        elif lain and rel in lain:
            tujuan = lain[rel]
        else:
            continue
        tujuan.parent.mkdir(parents=True, exist_ok=True)
        with z.open(info) as sumber, open(tujuan, "wb") as f:
            shutil.copyfileobj(sumber, f)


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--kasus", type=int, help="nomor kasus di kartu Kasus tim (1–23)")
    ap.add_argument("--arsip-wdi", action="store_true", help="unduh arsip WDI 142 rilis")
    a = ap.parse_args()
    if not a.kasus and not a.arsip_wdi:
        ap.error("pilih --kasus N dan/atau --arsip-wdi")

    raw = DATA / "raw"
    if a.kasus:
        kasus = {k["no"]: k for k in json.loads((DATA / "kasus.json").read_text(encoding="utf-8"))}
        if a.kasus not in kasus:
            ap.error(f"kasus {a.kasus} tidak ada; pilihan 1–{max(kasus)}")
        k = kasus[a.kasus]
        bongkar(ambil(k["paket"]), raw, {"README.md": DATA / "KASUS.md",
                                         "MANIFEST.csv": raw / "MANIFEST.csv",
                                         "LISENSI.md": DATA / "LISENSI.md"})
        n, salah = periksa(raw)
        if salah:
            sys.exit(f"{len(salah)} berkas tidak cocok dengan MANIFEST.csv: {salah[:5]}")
        print(f"Kasus {a.kasus:02d} {k['judul']}: {n} berkas cocok dengan MANIFEST.csv. Baca data/KASUS.md.")
    if a.arsip_wdi:
        bongkar(ambil("wdi-arsip-raw.zip"), raw)
        n = sum(1 for _ in (raw / "wdi_arsip").rglob("*.tar.gz"))
        print(f"Arsip WDI: {n} rilis di data/raw/wdi_arsip/.")


if __name__ == "__main__":
    main()
