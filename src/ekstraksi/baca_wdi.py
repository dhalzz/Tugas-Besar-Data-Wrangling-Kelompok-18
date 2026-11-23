"""Tahap 1 - pembaca berkas mentah WDI (JSON data dan metadata).

Aturan: pembaca TIDAK membersihkan apa pun. Nilai dibiarkan seperti di JSON
(null tetap kosong, angka tetap angka, teks tetap teks). Tugasnya:
  1. membaca [header_halaman, [rekaman...]] dan meratakan rekaman bersarang
     menjadi kolom bertitik (mis. `indicator.id`, `country.value`),
  2. menyaring menurut `indicator.id` (data) atau `id` (metadata indikator),
  3. menempelkan `_berkas_raw` dan `_sha256_raw` (lewat baca_bps._tempel).

Seri dalam berkas ini: `EG.ELC.ACCS.ZS`, `EG.CFT.ACCS.ZS`.
Berkas tanpa id indikator (mis. metadata/sumber.json) dibaca utuh sebagai
seri `referensi:<nama berkas>`.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import pandas as pd

from src.ekstraksi.baca_bps import _decode, _manifest, _tampil, _tempel

SERI_WDI = ("EG.ELC.ACCS.ZS", "EG.CFT.ACCS.ZS")


def _ratakan(rek: dict, awalan: str = "") -> dict:
    """{'indicator': {'id': 'X'}} -> {'indicator.id': 'X'}; list disimpan sebagai teks JSON."""
    keluar = {}
    for k, v in rek.items():
        nama = f"{awalan}{k}"
        if isinstance(v, dict):
            keluar.update(_ratakan(v, nama + "."))
        elif isinstance(v, list):
            keluar[nama] = json.dumps(v, ensure_ascii=False)
        else:
            keluar[nama] = v
    return keluar


def _id_indikator(rek: dict):
    ind = rek.get("indicator")
    if isinstance(ind, dict):
        return ind.get("id")
    return rek.get("id")


def _membawa_indikator(rek: dict) -> bool:
    return "indicator" in rek or "sourceNote" in rek


def baca_json_wdi(path: str | Path, indikator=SERI_WDI) -> dict[str, pd.DataFrame]:
    """Kembalikan {seri: DataFrame}. `indikator=None` -> semua rekaman sebagai seri `semua`."""
    path = Path(path)
    teks, enc = _decode(path.read_bytes())
    obj = json.loads(teks)
    if not (isinstance(obj, list) and len(obj) == 2 and isinstance(obj[1], list)):
        raise ValueError(f"{path.name}: bukan bentuk [header, [rekaman...]] (mungkin respons galat WDI)")
    header, rekaman = obj
    if not all(isinstance(r, dict) for r in rekaman):
        raise ValueError(f"{path.name}: ada rekaman yang bukan objek JSON")

    baris = [{"baris_ke": i, **_ratakan(r)} for i, r in enumerate(rekaman, start=1)]
    total = header.get("total") if isinstance(header, dict) else None
    meta = dict(
        encoding=enc, header_halaman=header, n_rekaman_berkas=len(rekaman),
        total_deklarasi=total,
        cocok_total=(total is None) or str(total) == str(len(rekaman)),
        n_indikator_berbeda=len({_id_indikator(r) for r in rekaman}) if rekaman else 0,
    )

    def bangun(sub, seri):
        df = _tempel(pd.DataFrame(sub), path, seri)
        df.attrs.update(meta, n_disaring=len(df))
        return df

    if not rekaman or not _membawa_indikator(rekaman[0]):
        seri = f"referensi:{path.stem}"
        return {seri: bangun(baris, seri)}
    if indikator is None:
        return {"semua": bangun(baris, "semua")}
    return {
        ind: bangun([b for b, r in zip(baris, rekaman) if _id_indikator(r) == ind], ind)
        for ind in indikator
    }


def baca_semua_wdi(direktori=None, pola: str = "wdi/**/*.json") -> tuple[dict, dict]:
    """-> (hasil {(berkas, seri): df}, galat {berkas: pesan})."""
    akar = Path(direktori) if direktori else _manifest.RAW
    hasil, galat = {}, {}
    for p in sorted(akar.glob(pola)):
        if not p.is_file():
            continue
        try:
            for seri, df in baca_json_wdi(p).items():
                hasil[(_tampil(p), seri)] = df
        except Exception as e:
            galat[_tampil(p)] = f"{type(e).__name__}: {e}"
    return hasil, galat


def komentar_jumlah_baris(hasil: dict) -> str:
    baris = ["# Jumlah baris per berkas (tabel panjang, hasil pembaca WDI Tahap 1)"]
    for (berkas, seri), df in hasil.items():
        a = df.attrs
        tambahan = ""
        if not seri.startswith("referensi:"):
            tambahan = f" (dari {a['n_rekaman_berkas']} rekaman berkas, {a['n_indikator_berbeda']} indikator berbeda)"
        baris.append(f"# - {berkas} [{seri}]: {len(df)} baris{tambahan}")
    return "\n".join(baris)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("direktori", nargs="?", default=None, help="default: data/raw")
    ap.add_argument("--pola", default="wdi/**/*.json")
    a = ap.parse_args()
    hasil, galat = baca_semua_wdi(a.direktori, a.pola)
    print(komentar_jumlah_baris(hasil))
    for b, m in galat.items():
        print(f"GALAT {b}: {m}", file=sys.stderr)
    tak_cocok = [(b, s) for (b, s), df in hasil.items() if not df.attrs["cocok_total"]]
    for b, s in tak_cocok:
        print(f"PERINGATAN {b} [{s}]: total di header tidak sama dengan jumlah rekaman", file=sys.stderr)
    sys.exit(1 if galat or not hasil else 0)
