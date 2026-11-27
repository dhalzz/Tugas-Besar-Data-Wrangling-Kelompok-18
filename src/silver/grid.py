"""Tahap 3: bentuk grid lengkap provinsi x periode (38 provinsi) sebelum missing.

Perbaikan v2:
- Sumbu rincian TETAP (semua kategori yang pernah muncul di seri), bukan per tahun.
- Tiga kategori kosong: sebelum_provinsi_ada / tahun_tidak_diterbitkan / sel_kosong_dalam_terbitan.
- missing_sejati = sel_kosong_dalam_terbitan saja.
- Metrik dipecah agar tidak menyesatkan.
"""
from __future__ import annotations

import csv
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
RAW = ROOT / "data" / "raw"
REF = ROOT / "data" / "referensi"
SILVER = ROOT / "data" / "silver"
LOG = ROOT / "log-keputusan.csv"
NIM = "124450066"

SERI = {
    "var87": {
        "sumber": "bps", "seri_kode": "var87", "satuan": "persen",
        "tahun_awal": 1993, "tahun_akhir": 2025,
        "berkas_raw": "bps/2026-10-17/sdg7_listrik_pln.csv", "jenis": "listrik",
    },
    "sdg7_bahan_bakar": {
        "sumber": "bps", "seri_kode": "tabel:sdg7_bahan_bakar", "satuan": "persen",
        "tahun_awal": 2001, "tahun_akhir": 2021,
        "berkas_raw": "bps/2026-10-17/sdg7_bahan_bakar.csv", "jenis": "bahan_bakar",
    },
}

PROVINSI_2023 = {"Papua Selatan", "Papua Tengah", "Papua Pegunungan", "Papua Barat Daya"}
ALIAS = {
    "KEPULAUANBANGKABELITUNG": "KEPBANGKABELITUNG",
    "KEPULAUANRIAU": "KEPRIAU",
    "DIYOGYAKARTA3": "DIYOGYAKARTA",
}


def norm(s: str) -> str:
    return str(s).replace(".", "").replace(" ", "").upper()


def muat_referensi():
    dim = pd.read_csv(REF / "dim_provinsi_38.csv", dtype={"kode_bps": str})
    dim["kunci_norm"] = dim["kunci_wilayah"].map(norm)
    aturan = pd.read_csv(REF / "aturan_tahun_provinsi.csv", dtype={"tahun_mulai": int})
    mulai = dict(zip(aturan["nama_provinsi"], aturan["tahun_mulai"]))
    return dim, mulai


def peta_wilayah(nama: str, dim: pd.DataFrame):
    n = ALIAS.get(norm(nama), norm(nama))
    if n == "INDONESIA":
        return 9999, "INDONESIA"
    hit = dim.loc[dim["kunci_norm"] == n]
    if hit.empty:
        raise KeyError(f"wilayah tidak terpetakan: {nama!r} (norm={n})")
    row = hit.iloc[0]
    return int(row["wilayah_kode"]), row["nama_provinsi"]


def silver_minimal(dim: pd.DataFrame) -> pd.DataFrame:
    baris = []
    v = pd.read_csv(RAW / SERI["var87"]["berkas_raw"])
    for r in v.itertuples(index=False):
        if pd.isna(r.nilai):
            continue
        wk, nama = peta_wilayah(r.wilayah, dim)
        baris.append({"sumber": "bps", "seri_kode": "var87", "wilayah_kode": wk,
                      "nama_wilayah": nama, "periode": f"{int(r.tahun):04d}",
                      "jenis_periode": "tahun", "rincian": "elektrifikasi",
                      "nilai": float(r.nilai), "satuan": "persen",
                      "_berkas_raw": SERI["var87"]["berkas_raw"]})
    b = pd.read_csv(RAW / SERI["sdg7_bahan_bakar"]["berkas_raw"])
    for r in b.itertuples(index=False):
        if pd.isna(r.nilai):
            continue
        wk, nama = peta_wilayah(r.wilayah, dim)
        baris.append({"sumber": "bps", "seri_kode": "tabel:sdg7_bahan_bakar", "wilayah_kode": wk,
                      "nama_wilayah": nama, "periode": f"{int(r.tahun):04d}",
                      "jenis_periode": "tahun", "rincian": str(r.bahan_bakar),
                      "nilai": float(r.nilai), "satuan": "persen",
                      "_berkas_raw": SERI["sdg7_bahan_bakar"]["berkas_raw"]})
    df = pd.DataFrame(baris)
    man = {}
    with open(RAW / "MANIFEST.csv", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            man[row["berkas"]] = row["sha256"]
    df["_sha256_raw"] = df["_berkas_raw"].map(man)
    return df


def rincian_tetap(df_silver: pd.DataFrame, seri_kode: str) -> list[str]:
    sub = df_silver[(df_silver["seri_kode"] == seri_kode) & (df_silver["wilayah_kode"] != 9999)]
    return sorted(sub["rincian"].dropna().unique())


def tahun_terbit_riil(df_silver: pd.DataFrame, seri_kode: str) -> set[int]:
    sub = df_silver[(df_silver["seri_kode"] == seri_kode) & (df_silver["wilayah_kode"] != 9999)]
    return set(sub["periode"].astype(int).unique())


def grid_seri(df_silver: pd.DataFrame, dim: pd.DataFrame, mulai: dict, cfg: dict):
    sub = df_silver[(df_silver["seri_kode"] == cfg["seri_kode"]) & (df_silver["wilayah_kode"] != 9999)]
    rincian_unik = rincian_tetap(df_silver, cfg["seri_kode"])
    tahun_terbit = tahun_terbit_riil(df_silver, cfg["seri_kode"])
    tahun = list(range(cfg["tahun_awal"], cfg["tahun_akhir"] + 1))

    daftar_prov = dim.copy()
    if cfg["jenis"] == "bahan_bakar":
        daftar_prov = daftar_prov[~daftar_prov["nama_provinsi"].isin(PROVINSI_2023)]

    idx = pd.MultiIndex.from_product(
        [daftar_prov["wilayah_kode"], tahun, rincian_unik],
        names=["wilayah_kode", "tahun", "rincian"]).to_frame(index=False)
    idx = idx.merge(daftar_prov[["wilayah_kode", "nama_provinsi"]], on="wilayah_kode", how="left")
    idx["periode"] = idx["tahun"].map(lambda t: f"{t:04d}")
    idx["seri_kode"] = cfg["seri_kode"]

    data = sub[["wilayah_kode", "periode", "rincian", "nilai"]].rename(columns={"nilai": "nilai_terisi"})
    grid = idx.merge(data, on=["wilayah_kode", "periode", "rincian"], how="left")
    grid["nilai"] = grid["nilai_terisi"]

    grid["sebelum_provinsi_ada"] = grid.apply(lambda r: r["tahun"] < mulai.get(r["nama_provinsi"], 0), axis=1)
    grid["tahun_tidak_diterbitkan"] = ~grid["tahun"].isin(tahun_terbit)
    grid["sel_kosong_dalam_terbitan"] = grid["nilai"].isna() & ~grid["sebelum_provinsi_ada"] & ~grid["tahun_tidak_diterbitkan"]
    grid["missing_sejati"] = grid["sel_kosong_dalam_terbitan"]
    return grid


def kelengkapan(grid: pd.DataFrame, cfg: dict) -> pd.DataFrame:
    # kelengkapan dihitung terhadap sel yang relevan: provinsi sudah ada & tahun terbit
    relevan = grid[~grid["sebelum_provinsi_ada"] & ~grid["tahun_tidak_diterbitkan"]]
    out = (relevan.groupby("tahun")
           .agg(n_sel=("nilai", "size"), n_terisi=("nilai", lambda s: s.notna().sum()))
           .reset_index())
    out["persen_terisi"] = (100 * out["n_terisi"] / out["n_sel"]).round(2)
    out["seri"] = cfg["jenis"]
    return out


def tulis_log(entries):
    kolom = ["tanggal", "seri", "keputusan", "alternatif_ditolak", "alasan", "baris_terdampak"]
    ada = LOG.exists()
    with open(LOG, "a", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=kolom)
        if not ada:
            w.writeheader()
        for e in entries:
            w.writerow({k: e.get(k, "") for k in kolom})


def main():
    dim, mulai = muat_referensi()
    df_silver = silver_minimal(dim)
    SILVER.mkdir(parents=True, exist_ok=True)
    (ROOT / "results" / NIM).mkdir(parents=True, exist_ok=True)

    semua_kel, ringkas = [], []
    for cfg in SERI.values():
        g = grid_seri(df_silver, dim, mulai, cfg)
        g.to_parquet(SILVER / f"grid_{cfg['jenis']}.parquet", index=False)
        k = kelengkapan(g, cfg)
        semua_kel.append(k)
        n_tahun_absen = int((g["tahun_tidak_diterbitkan"]).sum())
        n_sebelum = int(g["sebelum_provinsi_ada"].sum())
        n_missing = int(g["missing_sejati"].sum())
        ringkas.append({"seri": cfg["jenis"], "grid": len(g),
                        "tahun_tidak_diterbitkan": n_tahun_absen,
                        "sebelum_provinsi_ada": n_sebelum,
                        "sel_kosong_dalam_terbitan": n_missing})
        print(f"[{cfg['jenis']}] grid={len(g):,} | tahun_tidak_diterbitkan={n_tahun_absen:,} | "
              f"sebelum_provinsi_ada={n_sebelum:,} | sel_kosong_dalam_terbitan={n_missing:,}")

    kel = pd.concat(semua_kel, ignore_index=True)
    kel.to_csv(ROOT / "results" / NIM / "kelengkapan_panel_per_seri.csv", index=False)
    print(kel.to_string(index=False))

    tulis_log([
        dict(tanggal="2026-11-19", seri="listrik(var87)",
             keputusan="Tahun 2005 tidak diterbitkan di var87_long.csv -> ditandai tahun_tidak_diterbitkan, bukan missing sejati.",
             alternatif_ditolak="imputasi/interpolasi 2005 dari 2004 & 2006",
             alasan="Sumber tidak memuat baris 2005 sama sekali.",
             baris_terdampak="seluruh 33 sel listrik tahun 2005 di grid"),
        dict(tanggal="2026-11-19", seri="bahan_bakar(sdg7)",
             keputusan="Tahun 2002-2006 tidak diterbitkan di sdg7_bahan_bakar.csv -> ditandai tahun_tidak_diterbitkan.",
             alternatif_ditolak="imputasi/interpolasi 2002-2006",
             alasan="Sumber hanya memuat baris 2001 dan 2007 pada rentang itu.",
             baris_terdampak="seluruh sel bahan bakar 2002-2006 di grid"),
        dict(tanggal="2026-11-19", seri="bahan_bakar(sdg7)",
             keputusan="Sel kosong dalam tahun terbit (2001: 56 kosong; 2007: 7 kosong) = missing sejati, tidak diimputasi.",
             alternatif_ditolak="mengisi dengan 0 atau rata-rata",
             alasan="Baris ada di sumber tetapi nilai kosong; dibiarkan kosong dan dilaporkan kelengkapannya.",
             baris_terdampak="sel kosong pada tahun terbit bahan bakar"),
        dict(tanggal="2026-11-19", seri="listrik(var87)",
             keputusan="Provinsi baru = kosong sebelum tahun_mulai; provinsi induk memakai nilai historis penuh.",
             alternatif_ditolak="(a) backcast proporsional; (b) membagi nilai induk; (c) mengisi rata-rata",
             alasan="Batas wilayah statistik berubah saat pemekaran.",
             baris_terdampak="12 provinsi baru x tahun < tahun_mulai"),
        dict(tanggal="2026-11-19", seri="bahan_bakar(sdg7)",
             keputusan="Batas akhir tabel bahan bakar = 2021; 4 provinsi 2023 tidak masuk grid seri ini.",
             alternatif_ditolak="memasukkan 4 provinsi 2023 lalu menandainya missing",
             alasan="Di luar cakupan data (bukan missing).",
             baris_terdampak="Papua Selatan, Papua Tengah, Papua Pegunungan, Papua Barat Daya"),
        dict(tanggal="2026-11-19", seri="bahan_bakar(sdg7)",
             keputusan="Alias KEPULAUAN BANGKA BELITUNG -> KEP. BANGKA BELITUNG; KEPULAUAN RIAU -> KEP. RIAU.",
             alternatif_ditolak="membiarkan tidak terpetakan",
             alasan="Perbedaan penulisan antar sumber BPS.",
             baris_terdampak="seluruh baris kedua wilayah"),
        dict(tanggal="2026-11-19", seri="listrik(var87)+bahan_bakar",
             keputusan="Baris INDONESIA (9999) dipisah dari grid provinsi.",
             alternatif_ditolak="memasukkan INDONESIA ke sumbu provinsi",
             alasan="Agregat nasional bukan unit provinsi.",
             baris_terdampak="baris INDONESIA di kedua seri"),
        dict(tanggal="2026-11-19", seri="bahan_bakar(sdg7)",
             keputusan="Sumbu rincian ditetapkan tetap (semua kategori yang pernah muncul), bukan per tahun.",
             alternatif_ditolak="rincian per tahun (n_sel berubah-ubah)",
             alasan="Grid harus benar-benar lengkap provinsi x periode x rincian.",
             baris_terdampak="seluruh grid bahan bakar"),
    ])

    from src.common.hasil import tulis_hasil
    tulis_hasil(NIM, {
        "baris_silver": int(len(df_silver)),
        "sel_kosong_grid": int(sum(r["sel_kosong_dalam_terbitan"] for r in ringkas)),
        "tahun_tidak_diterbitkan": int(sum(r["tahun_tidak_diterbitkan"] for r in ringkas)),
        "outlier_ditandai": 0,
    })
    print("metrics.json ditulis.")


if __name__ == "__main__":
    main()
