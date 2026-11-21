"""Tahap 1 - Ekstraksi. Milik tim.

Baca setiap berkas yang terdaftar di data/raw/MANIFEST.csv menjadi DataFrame mentah yang
setia pada sumbernya: tidak ada pembersihan, hanya meratakan struktur dan mencatat asal tiap
baris (`_berkas_raw` relatif data/raw/, `_sha256_raw` dari src.common.manifest, `_seri`).
Penyeragaman nama, satuan, dan wilayah dikerjakan di tahap berikutnya.
"""
from __future__ import annotations

import json

import pandas as pd

from src.common.manifest import RAW, baca, periksa
from src.ekstraksi.baca_bps import _decode, _tempel, baca_csv_bps, baca_json_bps
from src.ekstraksi.baca_wdi import baca_json_wdi


def _daun(obj, jalur="$"):
    if isinstance(obj, dict):
        for k, v in obj.items():
            yield from _daun(v, f"{jalur}.{k}")
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            yield from _daun(v, f"{jalur}[{i}]")
    else:
        yield jalur, obj


def baca_json_polos(path, seri=None):
    """JSON apa pun -> tabel panjang (satu baris per nilai daun: jalur_json, nilai)."""
    teks, enc = _decode(path.read_bytes())
    obj = json.loads(teks)
    df = pd.DataFrame([{"baris_ke": i, "jalur_json": j, "nilai": v}
                       for i, (j, v) in enumerate(_daun(obj), start=1)])
    df = _tempel(df, path, seri or f"json:{path.stem}")
    df.attrs["encoding"] = enc
    return df


def _baca_berkas(berkas):
    """{seri: DataFrame} untuk satu berkas di MANIFEST. Tanpa pembaca -> galat, bukan dilewati."""
    path = RAW / berkas
    sumber, ekstensi = berkas.split("/")[0], path.suffix.lower()
    if sumber == "bps" and ekstensi == ".csv":
        seri = f"csv:{path.stem}"
        return {seri: baca_csv_bps(path, seri)}
    if sumber == "bps" and ekstensi == ".json":
        if path.name.startswith("manifest"):  # catatan asal unduhan, tetap dibaca utuh
            return {f"json:{path.stem}": baca_json_polos(path)}
        return baca_json_bps(path)
    if sumber == "wdi" and ekstensi == ".json":
        return baca_json_wdi(path)
    raise ValueError(f"tidak ada pembaca untuk {berkas}")


def jalankan():
    """Kembalikan {"<berkas>::<seri>": DataFrame mentah}, satu entri per (berkas, seri)."""
    n, salah = periksa()
    if salah:
        raise RuntimeError(f"data/raw tidak cocok dengan MANIFEST.csv: {salah}")
    manifest = baca(RAW)
    hasil, dibaca = {}, set()
    for berkas in sorted(manifest):
        frames = _baca_berkas(berkas)
        if not frames:
            raise RuntimeError(f"{berkas}: pembaca tidak menghasilkan tabel")
        for seri, df in frames.items():
            if len(df) and not (df["_berkas_raw"] == berkas).all():
                raise RuntimeError(f"{berkas} [{seri}]: _berkas_raw tidak sama dengan jalur MANIFEST")
            hasil[f"{berkas}::{seri}"] = df
        dibaca.add(berkas)
    terlewat = sorted(set(manifest) - dibaca)
    if terlewat:
        raise RuntimeError(f"berkas MANIFEST yang terlewat: {terlewat}")
    return hasil


def ringkasan(hasil):
    """Angka untuk results/<nim>/metrics.json: berkas_dibaca, baris_mentah, format."""
    berkas = {k.split("::")[0] for k in hasil}
    return {
        "berkas_dibaca": len(berkas),
        "baris_mentah": int(sum(len(df) for df in hasil.values())),
        "format": len({b.rsplit(".", 1)[-1].lower() for b in berkas}),
    }
