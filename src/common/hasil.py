"""Berkas hasil anggota untuk Workbench: results/<nim>/metrics.json. Milik starter — jangan diubah.

    from src.common.hasil import tulis_hasil
    tulis_hasil("122450001", {"baris_masuk": 5120, "baris_silver": 4980, "keputusan_dicatat": 7})

atau dari terminal:

    python -m src.common.hasil 122450001 baris_masuk=5120 baris_silver=4980 keputusan_dicatat=7

Isinya mengikuti skema baku Workbench: `metrik` (angka hasil komponen Anda), `seed` (0 bila
langkah Anda deterministik; isi seed KNN/MICE bila memakainya), `data_hash` (sidik MANIFEST.csv,
yaitu berkas mentah yang dipakai), `durasi_detik`, dan `perangkat`. Commit berkas ini, lalu kirim
dari Workbench (Papan Tim) agar tercatat sebagai bukti artefak sprint.
"""
import hashlib
import json
import platform
import sys
from pathlib import Path

from src.common.manifest import RAW, baca

ROOT = Path(__file__).resolve().parents[2]


def data_hash(raw=RAW):
    """sha256 dari pasangan berkas:sha256 di MANIFEST.csv, terurut."""
    h = hashlib.sha256()
    for berkas, sha in sorted(baca(Path(raw)).items()):
        h.update(f"{berkas}:{sha}\n".encode())
    return h.hexdigest()


def tulis_hasil(nim, metrik, seed=0, durasi_detik=None, raw=RAW):
    if not metrik or not all(isinstance(v, (int, float)) and not isinstance(v, bool) for v in metrik.values()):
        raise ValueError("metrik harus berisi minimal satu angka, dan semua nilainya angka")
    isi = {"metrik": metrik, "seed": int(seed), "data_hash": data_hash(raw),
           "perangkat": f"{platform.system()} {platform.machine()} Python {platform.python_version()}"}
    if durasi_detik is not None:
        isi["durasi_detik"] = round(float(durasi_detik), 2)
    tujuan = ROOT / "results" / str(nim) / "metrics.json"
    tujuan.parent.mkdir(parents=True, exist_ok=True)
    tujuan.write_text(json.dumps(isi, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return tujuan


if __name__ == "__main__":
    if len(sys.argv) < 3:
        sys.exit("pakai: python -m src.common.hasil <nim> nama=angka [nama=angka ...] [seed=N]")
    nim, pasangan = sys.argv[1], dict(a.split("=", 1) for a in sys.argv[2:])
    seed = int(pasangan.pop("seed", 0))
    print(tulis_hasil(nim, {k: float(v) if "." in v else int(v) for k, v in pasangan.items()}, seed=seed))
