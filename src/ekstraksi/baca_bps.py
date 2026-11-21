"""Tahap 1 - pembaca berkas mentah BPS (CSV dan JSON).

Aturan: pembaca TIDAK membersihkan apa pun. Semua nilai CSV tetap string apa
adanya (spasi, koma desimal, "-", "..." tidak disentuh). Tugasnya hanya:
  1. menebak pengodean karakter dan pemisah kolom,
  2. mengubah berkas menjadi tabel panjang dengan kolom asal,
  3. menempelkan `_berkas_raw` dan `_sha256_raw`.

Seri dalam berkas: `var87`, `tabel:sdg7_bahan_bakar`.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import html
import io
import json
import re
import sys
from collections import Counter
from html.parser import HTMLParser
from pathlib import Path

import pandas as pd

try:  # jejak berkas dari manifest kelompok
    from src.common import manifest as _manifest
except Exception:  # pragma: no cover
    _manifest = None

ENCODINGS = ("utf-8-sig", "utf-8", "cp1252", "latin-1")  # latin-1 tak pernah gagal
PEMBATAS = ",;\t|"
RE_TAHUN = re.compile(r"\s*(19|20)\d{2}\s*")


# --------------------------------------------------------------------------
# Jejak berkas mentah
# --------------------------------------------------------------------------
def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for blok in iter(lambda: f.read(1 << 20), b""):
            h.update(blok)
    return h.hexdigest()


def _jejak(path: Path) -> tuple[str, str]:
    """(_berkas_raw, _sha256_raw): jalur relatif terhadap data/raw + sha256 dari
    MANIFEST.csv lewat src.common.manifest.sha256_raw."""
    path = Path(path).resolve()
    if _manifest is None:
        return path.as_posix(), _sha256(path)
    rel = path.relative_to(_manifest.RAW.resolve()).as_posix()
    return rel, _manifest.sha256_raw(rel)


def _tempel(df: pd.DataFrame, path: Path, seri: str) -> pd.DataFrame:
    berkas, sha = _jejak(path)
    df = df.copy()
    df["_seri"] = seri
    df["_berkas_raw"] = berkas
    df["_sha256_raw"] = sha
    return df


# --------------------------------------------------------------------------
# Pengodean, pemisah, desimal
# --------------------------------------------------------------------------
def _decode(raw: bytes) -> tuple[str, str]:
    for enc in ENCODINGS:
        try:
            return raw.decode(enc), enc
        except UnicodeDecodeError:
            continue
    raise UnicodeDecodeError("latin-1", raw, 0, 1, "tak terbaca")  # tak tercapai


def _tebak_pembatas(teks: str) -> str:
    baris = [b for b in teks.splitlines()[:200] if b.strip()]
    terbaik, skor = ",", -1
    for d in PEMBATAS:
        panjang = [len(next(csv.reader([b], delimiter=d))) for b in baris]
        panjang = [n for n in panjang if n > 1]  # baris judul/catatan tak dihitung
        s = Counter(panjang).most_common(1)[0][1] if panjang else 0
        if s > skor:
            terbaik, skor = d, s
    return terbaik


def _tebak_desimal(sel: list[str]) -> str:
    koma = sum(bool(re.fullmatch(r"\s*-?\d+,\d+\s*", s)) for s in sel)
    titik = sum(bool(re.fullmatch(r"\s*-?\d+\.\d+\s*", s)) for s in sel)
    return "," if koma > titik else "."


# --------------------------------------------------------------------------
# CSV
# --------------------------------------------------------------------------
def baca_csv_bps(path: str | Path, seri: str | None = None) -> pd.DataFrame:
    """CSV BPS -> tabel panjang. Judul/catatan di luar tabel disimpan di attrs."""
    path = Path(path)
    teks, enc = _decode(path.read_bytes())
    d = _tebak_pembatas(teks)
    baris = list(csv.reader(io.StringIO(teks, newline=""), delimiter=d))

    tak_kosong = [(n, r) for n, r in enumerate(baris, start=1) if any(c.strip() for c in r)]
    if not tak_kosong:
        raise ValueError(f"{path.name}: berkas kosong")
    panjang = Counter(len(r) for _, r in tak_kosong if len(r) > 1)
    ncol = max(panjang, key=lambda k: (panjang[k], k)) if panjang else 1

    idx_hdr = next(i for i, (_, r) in enumerate(tak_kosong) if len(r) == ncol)
    hdr = tak_kosong[idx_hdr][1]
    sebelum = [r for _, r in tak_kosong[:idx_hdr]]
    data = [(n, r) for n, r in tak_kosong[idx_hdr + 1:] if len(r) == ncol]
    sesudah = [r for n, r in tak_kosong[idx_hdr + 1:] if len(r) != ncol]

    th_tahun = [i for i, h in enumerate(hdr) if RE_TAHUN.fullmatch(h)]
    if th_tahun:  # tabel lebar (kolom = tahun) -> panjang
        id_idx = [i for i in range(ncol) if i not in th_tahun]
        nama_id = {}
        for i in id_idx:
            nama = hdr[i] or f"kolom_{i}"
            nama_id[i] = nama if nama not in nama_id.values() else f"{nama}_{i}"
        rec = []
        for n, r in data:
            ids = {nama_id[i]: r[i] for i in id_idx}
            for i in range(ncol):
                if i in id_idx:
                    continue
                rec.append({"baris_ke": n, **ids, "kolom_ke": i,
                            "kolom_asal": hdr[i], "nilai": r[i]})
        df = pd.DataFrame(rec)
    else:  # sudah panjang: satu baris per rekaman, kolom asli dipertahankan
        nama = []
        for i, h in enumerate(hdr):
            n_ = h or f"kolom_{i}"
            nama.append(n_ if n_ not in nama else f"{n_}_{i}")
        df = pd.DataFrame([{"baris_ke": n, **dict(zip(nama, r))} for n, r in data])
    df = _tempel(df, path, seri or f"csv:{path.stem}")
    df.attrs.update(
        encoding=enc, pembatas=d,
        desimal=_tebak_desimal([r[i] for _, r in data for i in range(ncol)]),
        sebelum_header=sebelum, sesudah_tabel=sesudah, n_baris_data=len(data),
    )
    return df


# --------------------------------------------------------------------------
# JSON: datacontent bersarang
# --------------------------------------------------------------------------
def _cari_dict(obj, kunci: str):
    if isinstance(obj, dict):
        if kunci in obj:
            return obj
        for v in obj.values():
            hit = _cari_dict(v, kunci)
            if hit is not None:
                return hit
    elif isinstance(obj, list):
        for v in obj:
            hit = _cari_dict(v, kunci)
            if hit is not None:
                return hit
    return None


def _kamus(daftar) -> dict[str, str]:
    """[{'val': 3100, 'label': 'DKI'}] -> {'3100': 'DKI'} (val dipaksa string)."""
    if not daftar:
        return {}
    return {str(x.get("val")): x.get("label") for x in daftar if isinstance(x, dict)}


def _pecah(k: str, komponen: list) -> list:
    if not komponen:
        return [()] if k == "" else []
    nama, kam = komponen[0]
    hasil = []
    for val, label in kam.items():
        if k.startswith(val):
            for sisa in _pecah(k[len(val):], komponen[1:]):
                hasil.append(((nama, val, label),) + sisa)
    return hasil


def _datacontent_ke_panjang(obj: dict) -> pd.DataFrame:
    # Urutan kunci datacontent BPS: vervar + var + turvar + tahun + turtahun
    komponen = [(n, _kamus(obj.get(n))) for n in ("vervar", "var", "turvar", "tahun", "turtahun")]
    komponen = [(n, k) for n, k in komponen if k]
    rec = []
    for kunci, nilai in obj["datacontent"].items():
        kunci = str(kunci)
        hit = _pecah(kunci, komponen)
        baris = {"kunci_datacontent": kunci, "nilai": nilai,
                 "_kunci_ambigu": len(hit) > 1, "_kunci_tak_terurai": not hit}
        for nama, val, label in (hit[0] if hit else ()):
            baris[f"{nama}_val"] = val
            baris[f"{nama}_label"] = label
        rec.append(baris)
    return pd.DataFrame(rec)


# --------------------------------------------------------------------------
# JSON: tabel HTML ter-escape
# --------------------------------------------------------------------------
def _cari_html(obj, jalur="$"):
    if isinstance(obj, str):
        if re.search(r"(&lt;|<)\s*table", obj, re.I):
            yield jalur, obj
    elif isinstance(obj, dict):
        for k, v in obj.items():
            yield from _cari_html(v, f"{jalur}.{k}")
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            yield from _cari_html(v, f"{jalur}[{i}]")


def _unescape(s: str) -> str:
    for _ in range(3):  # tangani escape ganda
        if "&lt;" not in s and "&gt;" not in s:
            break
        s = html.unescape(s)
    return s


class _PenguraiTabel(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.tabel, self._tbl, self._baris, self._sel, self._dalam = [], None, None, None, 0

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == "table":
            self._dalam += 1
            if self._dalam == 1:
                self._tbl = []
        elif self._dalam == 1 and tag == "tr":
            self._baris = []
        elif self._dalam == 1 and tag in ("td", "th") and self._baris is not None:
            def angka(v):
                try:
                    return max(1, int(v))
                except (TypeError, ValueError):
                    return 1
            self._sel = {"teks": [], "th": tag == "th",
                         "cs": angka(a.get("colspan")), "rs": angka(a.get("rowspan"))}
        elif tag == "br" and self._sel is not None:
            self._sel["teks"].append(" ")

    def handle_data(self, data):
        if self._sel is not None:
            self._sel["teks"].append(data)

    def handle_endtag(self, tag):
        if tag in ("td", "th") and self._sel is not None and self._baris is not None:
            self._sel["teks"] = " ".join("".join(self._sel["teks"]).split())
            self._baris.append(self._sel)
            self._sel = None
        elif tag == "tr" and self._baris is not None and self._tbl is not None:
            self._tbl.append(self._baris)
            self._baris = None
        elif tag == "table":
            if self._dalam == 1 and self._tbl is not None:
                self.tabel.append(self._tbl)
                self._tbl = None
            self._dalam = max(0, self._dalam - 1)


def _grid(baris_html: list) -> tuple[dict, int, int]:
    g, maxc, maxr = {}, 0, 0
    for r, baris in enumerate(baris_html):
        c = 0
        for sel in baris:
            while (r, c) in g:
                c += 1
            for dr in range(sel["rs"]):
                for dc in range(sel["cs"]):
                    g[(r + dr, c + dc)] = (sel["teks"], sel["th"])
            c += sel["cs"]
        maxc = max(maxc, c)
        maxr = max(maxr, r + max((s["rs"] for s in baris), default=1))
    return g, maxr, maxc


_RE_ANGKA = re.compile(r"\s*(-|\u2013|\u2014|\.{2,3}|\u2026|[-+]?\d[\d.,]*)\s*")


def tabel_html_ke_panjang(teks_html: str) -> pd.DataFrame:
    """Tabel HTML (sudah di-unescape) -> tabel panjang jenis bahan bakar x tahun.

    Header berlapis diratakan: header_0, header_1, ... (urut atas ke bawah) dan
    `kolom_asal` = gabungan semua lapis. Nama lapis (jenis vs tahun) diberikan
    setelah dilihat isi aslinya; pembaca tidak menebak.

    Tabel ber-<th>: header = baris awal yang seluruhnya <th>. Tabel tanpa <th>
    (kasus sdg7_bahan_bakar): baris dikelompokkan menurut isinya (header /
    data / lainnya); judul dan catatan kaki disimpan di attrs, tidak dibuang.
    """
    p = _PenguraiTabel()
    p.feed(teks_html)
    if not p.tabel:
        raise ValueError("tidak ada <table> pada HTML")
    g, nr, nc = _grid(p.tabel[0])
    teks = lambda r, c: g.get((r, c), ("", False))[0]  # noqa: E731
    cth = lambda r, c: g.get((r, c), ("", False))[1]  # noqa: E731

    if any(th for _, th in g.values()):
        n_hdr = 0
        while n_hdr < nr and all(cth(n_hdr, c) for c in range(nc) if (n_hdr, c) in g):
            n_hdr += 1
        n_hdr = max(n_hdr, 1)
        hdr_rows, data_rows = list(range(n_hdr)), list(range(n_hdr, nr))
        stub = ([c for c in range(nc) if len({teks(r, c) for r in hdr_rows}) == 1]
                if n_hdr > 1 else []) or [0]
    else:
        def jenis(r):
            sel = [teks(r, c) for c in range(1, nc) if teks(r, c)]
            if not sel:
                return "kosong"
            if sum(bool(RE_TAHUN.fullmatch(t)) for t in sel) >= 0.5 * len(sel):
                return "header"
            if sum(bool(_RE_ANGKA.fullmatch(t)) for t in sel) >= 0.5 * len(sel):
                return "data"
            return "header" if len(set(sel)) >= 2 else "teks"

        j = [jenis(r) for r in range(nr)]
        if "data" not in j:
            raise ValueError("tabel HTML tanpa <th> dan tanpa baris data terdeteksi")
        r0 = j.index("data")
        hdr_rows = []
        r = r0 - 1
        while r >= 0 and j[r] == "header":
            hdr_rows.insert(0, r)
            r -= 1
        if not hdr_rows:
            raise ValueError("header tak terdeteksi di atas baris data pertama")
        data_rows = [r for r in range(r0, nr) if j[r] == "data"]
        stub = [0]

    nama_stub = [teks(hdr_rows[0], c) or f"stub_{c}" for c in stub]
    rec = []
    for r in data_rows:
        ids = {nama_stub[i]: teks(r, c) for i, c in enumerate(stub)}
        for c in range(nc):
            if c in stub:
                continue
            lapis = [teks(h, c) for h in hdr_rows]
            baris = {"baris_ke": r + 1, **ids, "kolom_ke": c + 1}
            baris.update({f"header_{i}": t for i, t in enumerate(lapis)})
            baris["kolom_asal"] = " | ".join(lapis)
            baris["nilai"] = teks(r, c)
            rec.append(baris)
    df = pd.DataFrame(rec)
    lain = [r for r in range(nr) if r not in hdr_rows and r not in data_rows]
    df.attrs.update(
        n_header=len(hdr_rows), kolom_stub=nama_stub, baris_header=[r + 1 for r in hdr_rows],
        teks_lain=[(r + 1, teks(r, 0)) for r in lain if teks(r, 0)],  # judul + catatan kaki
    )
    return df


# --------------------------------------------------------------------------
# JSON: pintu masuk
# --------------------------------------------------------------------------
def baca_json_bps(path: str | Path, nama_tabel_html: str = "sdg7_bahan_bakar") -> dict[str, pd.DataFrame]:
    """Kembalikan {seri: DataFrame}: `var<val>` dari datacontent dan
    `tabel:<nama>` untuk tiap tabel HTML ter-escape."""
    path = Path(path)
    teks, enc = _decode(path.read_bytes())
    obj = json.loads(teks)
    hasil: dict[str, pd.DataFrame] = {}

    dc = _cari_dict(obj, "datacontent")
    if dc is not None and dc["datacontent"]:
        panjang = _datacontent_ke_panjang(dc)
        if "var_val" in panjang:
            tak = panjang["var_val"].isna()  # kunci tak terurai: jangan dibuang
            for v, sub in panjang[~tak].groupby("var_val", sort=False):
                seri = f"var{v}"
                hasil[seri] = _tempel(sub.reset_index(drop=True), path, seri)
            if tak.any():
                hasil["datacontent_tak_terurai"] = _tempel(
                    panjang[tak].reset_index(drop=True), path, "datacontent_tak_terurai")
        else:
            hasil["datacontent"] = _tempel(panjang, path, "datacontent")

    for i, (jalur, s) in enumerate(_cari_html(obj)):
        df = tabel_html_ke_panjang(_unescape(s))
        seri = f"tabel:{nama_tabel_html}" + (f"_{i}" if i else "")
        df = _tempel(df, path, seri)
        df.attrs["jalur_json"] = jalur
        hasil[seri] = df

    if not hasil:
        raise ValueError(f"{path.name}: tak ada datacontent maupun tabel HTML")
    for df in hasil.values():
        df.attrs["encoding"] = enc
    return hasil


# --------------------------------------------------------------------------
# Banding HTML vs CSV pratampil (hanya untuk laporan, tidak mengubah data)
# --------------------------------------------------------------------------
def _norm(s) -> str:
    return re.sub(r"\s+", "", str(s)).lower().replace(",", ".")


def bandingkan_html_csv(df_html: pd.DataFrame, df_csv: pd.DataFrame) -> dict:
    a, b = Counter(map(_norm, df_html["nilai"])), Counter(map(_norm, df_csv["nilai"]))
    return {
        "sel_html": len(df_html), "sel_csv": len(df_csv),
        "header_html": sorted(df_html["kolom_asal"].unique())[:20],
        "header_csv": sorted(df_csv["kolom_asal"].unique())[:20],
        "nilai_hanya_di_html": list((a - b).items())[:10],
        "nilai_hanya_di_csv": list((b - a).items())[:10],
    }


# --------------------------------------------------------------------------
# Semua berkas
# --------------------------------------------------------------------------
def _tampil(p: Path) -> str:
    """Jalur relatif terhadap data/raw bila bisa (sama dengan _berkas_raw)."""
    try:
        return p.resolve().relative_to(_manifest.RAW.resolve()).as_posix()
    except Exception:
        return p.as_posix()


def baca_semua(direktori: str | Path, pola: str = "bps/**/*") -> tuple[dict, dict]:
    """-> (hasil {(berkas, seri): df}, galat {berkas: pesan})."""
    hasil, galat = {}, {}
    for p in sorted(Path(direktori).glob(pola)):
        if not p.is_file() or p.suffix.lower() not in (".csv", ".json"):
            continue
        if p.name.lower().startswith("manifest"):
            continue  # catatan asal unduhan, bukan data BPS
        try:
            if p.suffix.lower() == ".csv":
                df = baca_csv_bps(p)
                hasil[(_tampil(p), df["_seri"].iat[0] if len(df) else p.stem)] = df
            else:
                for seri, df in baca_json_bps(p).items():
                    hasil[(_tampil(p), seri)] = df
        except Exception as e:  # dicatat, pembacaan berkas lain lanjut
            galat[_tampil(p)] = f"{type(e).__name__}: {e}"
    return hasil, galat


def komentar_jumlah_baris(hasil: dict) -> str:
    baris = ["# Jumlah baris per berkas (tabel panjang, hasil pembaca Tahap 1)"]
    for (berkas, seri), df in hasil.items():
        baris.append(f"# - {berkas} [{seri}]: {len(df)} baris")
    return "\n".join(baris)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("direktori", nargs="?", default=None)
    ap.add_argument("--pola", default="bps/**/*")
    a = ap.parse_args()
    akar = a.direktori or (_manifest.RAW if _manifest else "data/raw")
    hasil, galat = baca_semua(akar, a.pola)
    print(komentar_jumlah_baris(hasil))
    for b, m in galat.items():
        print(f"GALAT {b}: {m}", file=sys.stderr)
    sys.exit(1 if galat or not hasil else 0)
