"""Kembalikan K-001 (milik tim, NIM 124450008) + perbaiki baris_silver."""
from __future__ import annotations
import csv
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
LOG = ROOT / "log-keputusan.csv"
NIM = "124450066"
KOLOM = ["id","tanggal","nim","tahap","seri_kode","keputusan",
         "alternatif_ditolak","alasan","dampak_baris"]

k001 = {
    "id": "K-001", "tanggal": "2026-11-08", "nim": "124450008", "tahap": "silver",
    "seri_kode": "sdg7",
    "keputusan": "Nama provinsi distandarkan lewat tabel acuan dim_provinsi_38; kode BPS 2 digit bertipe teks menjadi kunci utama; nama_provinsi memakai Title Case ejaan resmi (DKI dan DI tetap kapital); kunci_wilayah memakai HURUF KAPITAL tanpa tanda baca untuk join ke data mentah; slug memakai huruf kecil bergaris bawah; baris INDONESIA ditandai tingkat nasional dan tidak dihitung sebagai provinsi",
    "alternatif_ditolak": "Join memakai nama mentah tanpa kode; memakai nama huruf kapital apa adanya sebagai nama tampilan; menghapus baris INDONESIA",
    "alasan": "Nama mentah rentan berbeda ejaan antar sumber dan 4 provinsi baru belum ada di data; kode BPS stabil sehingga semua seri bisa dibandingkan dengan satu acuan wilayah; INDONESIA adalah agregat sehingga menggandakan hitungan bila dijumlah dengan provinsi",
    "dampak_baris": "JUMLAH_BARIS; tidak berubah (tidak ada baris dihapus atau ditambah); agregasi dilakukan di Gold",
}

# baca log sekarang (9 entri kita)
with open(LOG, encoding="utf-8") as f:
    rows = list(csv.DictReader(f))

# tulis ulang: K-001 dulu, lalu 9 entri kita
with open(LOG, "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=KOLOM)
    w.writeheader()
    w.writerow(k001)
    for r in rows:
        w.writerow({k: r.get(k, "") for k in KOLOM})
print("log-keputusan.csv:", len(rows)+1, "baris data (K-001 +", len(rows), "entri kita)")

# --- baris_silver dari Silver-minimal (termasuk Indonesia) --------------------
from src.silver.grid import muat_referensi, silver_minimal
dim, _ = muat_referensi()
df_s = silver_minimal(dim)
n_absen = 0
for jenis in ("listrik","bahan_bakar"):
    g = pd.read_parquet(ROOT/"data"/"silver"/f"grid_{jenis}.parquet")
    n_absen += int(g["tahun_tidak_diterbitkan"].sum())
kel = pd.read_csv(ROOT/"results"/NIM/"kelengkapan_panel_per_seri.csv")
sel_kosong = int(kel["n_sel_relevan"].fillna(0).sum() - kel["n_terisi"].sum())

from src.common.hasil import tulis_hasil
tulis_hasil(NIM, {
    "baris_silver": int(len(df_s)),
    "sel_kosong_grid": int(sel_kosong),
    "tahun_tidak_diterbitkan": int(n_absen),
    "outlier_ditandai": 0,
})
import json
print(json.dumps(json.loads((ROOT/"results"/NIM/"metrics.json").read_text()), indent=2))
