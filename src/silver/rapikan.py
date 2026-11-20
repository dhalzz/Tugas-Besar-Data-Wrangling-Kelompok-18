"""Rapikan log-keputusan.csv: pertahankan header + baris tim (K-001),
buang semua baris 2026-11-19 hasil grid.py v1/v2, tulis ulang 8 entri final
dengan skema starter. Lalu regenerasi metrics.json final.
"""
from __future__ import annotations
import csv, json
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
LOG = ROOT / "log-keputusan.csv"
NIM = "124450066"

KOLOM = ["id","tanggal","nim","tahap","seri_kode","keputusan",
         "alternatif_ditolak","alasan","dampak_baris"]

# --- 1. baca log lama, pertahankan header + K-001 (baris tim lain) -------------
baris_tim = []
with open(LOG, encoding="utf-8") as f:
    r = csv.DictReader(f)
    for row in r:
        if row.get("id","").startswith("K-") and row.get("nim") != NIM:
            baris_tim.append(row)

# --- 2. 8 entri final kita, skema sama ----------------------------------------
entri = [
 dict(seri_kode="var87",
      keputusan="Provinsi baru = kosong sebelum tahun_mulai (aturan_tahun_provinsi.csv); provinsi induk memakai nilai historis penuh.",
      alternatif_ditolak="(a) backcast proporsional; (b) membagi nilai induk; (c) mengisi rata-rata",
      alasan="Batas wilayah statistik berubah saat pemekaran; nilai historis induk adalah nilai wilayah saat itu.",
      dampak_baris="12 provinsi baru x tahun < tahun_mulai pada grid_listrik"),
 dict(seri_kode="sdg7_bahan_bakar",
      keputusan="Batas akhir tabel bahan bakar = 2021; 4 provinsi 2023 tidak masuk grid seri ini.",
      alternatif_ditolak="memasukkan 4 provinsi 2023 ke grid lalu menandainya missing",
      alasan="Di luar cakupan data (bukan missing); pemekaran 2023 terjadi setelah data berakhir.",
      dampak_baris="Papua Selatan, Papua Tengah, Papua Pegunungan, Papua Barat Daya"),
 dict(seri_kode="sdg7_bahan_bakar",
      keputusan="Alias KEPULAUAN BANGKA BELITUNG -> KEP. BANGKA BELITUNG; KEPULAUAN RIAU -> KEP. RIAU.",
      alternatif_ditolak="membiarkan tidak terpetakan (baris hilang)",
      alasan="Perbedaan penulisan antar sumber BPS.",
      dampak_baris="seluruh baris kedua wilayah di sdg7_bahan_bakar.csv"),
 dict(seri_kode="var87+sdg7_bahan_bakar",
      keputusan="Baris INDONESIA (wilayah_kode 9999) dipisah dari grid provinsi.",
      alternatif_ditolak="memasukkan INDONESIA ke sumbu provinsi",
      alasan="Agregat nasional bukan unit provinsi; akan mendistorsi kelengkapan panel.",
      dampak_baris="baris INDONESIA di kedua seri"),
 dict(seri_kode="sdg7_bahan_bakar",
      keputusan="Baris rincian 'Jumlah' dipisah dari rincian jenis bahan bakar.",
      alternatif_ditolak="menggabungkan Jumlah dengan jenis (double count)",
      alasan="Jumlah adalah agregat, bukan kategori bahan bakar.",
      dampak_baris="semua baris rincian=Jumlah"),
 dict(seri_kode="var87",
      keputusan="Tahun 2005 tidak diterbitkan di var87_long.csv -> ditandai tahun_tidak_diterbitkan, bukan missing sejati.",
      alternatif_ditolak="imputasi/interpolasi 2005 dari 2004 & 2006",
      alasan="Sumber tidak memuat baris 2005 sama sekali.",
      dampak_baris="seluruh sel listrik tahun 2005 di grid (0 sel relevan)"),
 dict(seri_kode="sdg7_bahan_bakar",
      keputusan="Tahun 2002-2006 tidak diterbitkan di sdg7_bahan_bakar.csv -> ditandai tahun_tidak_diterbitkan.",
      alternatif_ditolak="imputasi/interpolasi 2002-2006",
      alasan="Sumber hanya memuat baris 2001 dan 2007 pada rentang itu.",
      dampak_baris="seluruh sel bahan bakar 2002-2006 di grid (0 sel relevan)"),
 dict(seri_kode="sdg7_bahan_bakar",
      keputusan="Sel kosong dalam tahun terbit (2001: 56 kosong; 2007: 7 kosong; 2011: 6; 2013: 7; 2014: 14; 2021: 1) = missing sejati, tidak diimputasi.",
      alternatif_ditolak="mengisi dengan 0 atau rata-rata",
      alasan="Baris ada di sumber tetapi nilai kosong; dibiarkan kosong dan dilaporkan kelengkapannya.",
      dampak_baris="56 sel kosong dalam terbitan (bahan bakar) + 15 sel (listrik)"),
 dict(seri_kode="sdg7_bahan_bakar",
      keputusan="Sumbu rincian ditetapkan tetap (7 kategori yang pernah muncul), bukan per tahun.",
      alternatif_ditolak="rincian per tahun (n_sel berubah-ubah)",
      alasan="Grid harus benar-benar lengkap provinsi x periode x rincian.",
      dampak_baris="seluruh grid bahan bakar (238 sel per tahun terbit)"),
]

# --- 3. tulis ulang log -------------------------------------------------------
with open(LOG, "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=KOLOM)
    w.writeheader()
    for row in baris_tim:
        w.writerow({k: row.get(k, "") for k in KOLOM})
    for i, e in enumerate(entri, start=2):
        w.writerow({
            "id": f"K-{i:03d}", "tanggal": "2026-11-19", "nim": NIM,
            "tahap": "silver", "seri_kode": e["seri_kode"],
            "keputusan": e["keputusan"], "alternatif_ditolak": e["alternatif_ditolak"],
            "alasan": e["alasan"], "dampak_baris": e["dampak_baris"],
        })
print("log-keputusan.csv ditulis ulang:", len(baris_tim)+len(entri), "baris data")

# --- 4. regenerasi metrics.json final ----------------------------------------
kel = pd.read_csv(ROOT/"results"/NIM/"kelengkapan_panel_per_seri.csv")
sel_kosong = int(kel["n_sel_relevan"].fillna(0).sum() - kel["n_terisi"].sum())
# baris_silver = baris di grid (bukan sel kosong); pakai total sel grid - sel kosong relevan
df_s = None
# hitung baris Silver-minimal dari dua grid: observasi yang benar-benar ada
n_obs = 0
for jenis in ("listrik","bahan_bakar"):
    g = pd.read_parquet(ROOT/"data"/"silver"/f"grid_{jenis}.parquet")
    n_obs += int(g["nilai"].notna().sum())
# tahun_tidak_diterbitkan = sel grid di tahun absen
n_absen = 0
for jenis in ("listrik","bahan_bakar"):
    g = pd.read_parquet(ROOT/"data"/"silver"/f"grid_{jenis}.parquet")
    n_absen += int(g["tahun_tidak_diterbitkan"].sum())

from src.common.hasil import tulis_hasil
tulis_hasil(NIM, {
    "baris_silver": int(n_obs),
    "sel_kosong_grid": int(kel["n_sel_relevan"].fillna(0).sum() - kel["n_terisi"].sum()),
    "tahun_tidak_diterbitkan": int(n_absen),
    "outlier_ditandai": 0,
})
print("metrics.json final ditulis.")
print(json.dumps(json.loads((ROOT/"results"/NIM/"metrics.json").read_text()), indent=2))
