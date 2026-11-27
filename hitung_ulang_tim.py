import glob
import os
import sys

import pandas as pd

# Folder yang berisi data/silver dan data/gold (salinan integrasi-sprint1)
B = sys.argv[1] if len(sys.argv) > 1 else r"..\wt-integrasi"

sv = pd.read_parquet(os.path.join(B, "data", "silver", "silver.parquet"))
gb = pd.read_parquet(os.path.join(B, "data", "silver", "grid_bahan_bakar.parquet"))
gl = pd.read_parquet(os.path.join(B, "data", "silver", "grid_listrik.parquet"))


def p(kode, label, nilai, asal):
    print(f"{kode:6} | {label:55} | {nilai!s:12} | {asal}")


print("== UKURAN ==")
p("-", "baris silver", len(sv), "silver.parquet")
for k, d in sv.groupby("seri_kode"):
    p("-", f"  silver {k}: baris / wilayah / periode",
      f"{len(d)}/{d.wilayah_kode.nunique()}/{d.periode.nunique()}", "silver.parquet")
p("-", "baris grid bahan bakar", len(gb), "grid_bahan_bakar.parquet")
p("-", "baris grid listrik", len(gl), "grid_listrik.parquet")

print("\n== CELAH PANEL (K-002, K-003, K-007, K-008, K-009) ==")
for nama, g in [("listrik", gl), ("bahan bakar", gb)]:
    for flag in ["sebelum_provinsi_ada", "tahun_tidak_diterbitkan",
                 "sel_kosong_dalam_terbitan", "missing_sejati"]:
        p("-", f"{nama}: sel {flag}", int(g[flag].sum()), "grid")
    thn = sorted(g.loc[g.tahun_tidak_diterbitkan, "tahun"].unique())
    p("-", f"{nama}: tahun tidak diterbitkan", thn, "grid")
    p("-", f"{nama}: rentang tahun grid", f"{g.tahun.min()}-{g.tahun.max()}", "grid")
    p("-", f"{nama}: provinsi dgn sebelum_provinsi_ada",
      g.loc[g.sebelum_provinsi_ada, "nama_provinsi"].nunique(), "grid")

print("\nSel kosong dalam terbitan per tahun (bahan bakar), cocokkan K-009:")
print(gb[gb.sel_kosong_dalam_terbitan].groupby("tahun").size().to_string())
print("\nSel kosong dalam terbitan per tahun (listrik):")
print(gl[gl.sel_kosong_dalam_terbitan].groupby("tahun").size().to_string())
print("\nMissing sejati bahan bakar per provinsi (5 teratas):")
print(gb[gb.missing_sejati].groupby("nama_provinsi").size()
      .sort_values(ascending=False).head(5).to_string())
print("\nSel per tahun terbit bahan bakar (K-010 menyebut 238):")
print(gb[~gb.tahun_tidak_diterbitkan & ~gb.sebelum_provinsi_ada]
      .groupby("tahun").size().describe().to_string())

print("\n== PATAHAN (K-017): provinsi dgn |selisih| > 10 poin per tahun, var87 ==")
v = sv[sv.seri_kode == "var87"].copy()
v["tahun"] = v.periode.astype(int)
w = v.pivot_table(index="tahun", columns="wilayah_kode", values="nilai")
n = (w.diff().abs() > 10).sum(axis=1)
print(n[n > 0].to_string())
print("jumlah provinsi:", w.shape[1])

print("\n== REVISI (K-016, K-018): snapshot ==")
print(sorted(sv["_berkas_raw"].str.extract(r"(\d{4}-\d{2}-\d{2})")[0].dropna().unique()))

print("\n== KATALOG (K-001, K-004, K-005, K-006) ==")
p("K-005", "baris INDONESIA (9999) di silver", int((sv.wilayah_kode == 9999).sum()), "silver")
p("K-006", "baris rincian Jumlah di silver", int((sv.rincian == "Jumlah").sum()), "silver")
p("K-001", "wilayah unik di silver", sv.wilayah_kode.nunique(), "silver")
print(sorted(sv.nama_wilayah.unique())[:60])

print("\n== BERKAS KANDIDAT ANOMALI ==")
for f in glob.glob(os.path.join(B, "**", "calon_anomali*.csv"), recursive=True):
    d = pd.read_csv(f)
    p("-", os.path.relpath(f, B), d.shape, "kolom: " + ", ".join(d.columns[:6]))
print("\n== REKONSILIASI (harus cocok) ==")
fl = ["sebelum_provinsi_ada", "tahun_tidak_diterbitkan", "sel_kosong_dalam_terbitan"]
for nama, g, seri in [("listrik", gl, "var87"), ("bahan bakar", gb, "tabel:sdg7_bahan_bakar")]:
    terisi = int((~g[fl].any(axis=1)).sum())
    prov = int(((sv.seri_kode == seri) & (sv.wilayah_kode != 9999)).sum())
    tumpang = int(g[fl[:2]].all(axis=1).sum())
    print(f"{nama}: sel grid={len(g)}, sel tanpa penanda={terisi}, baris silver non-INDONESIA={prov}, cocok={terisi == prov}, tumpang tindih={tumpang}")
sel70 = int((gb.sebelum_provinsi_ada & ~gb.tahun_tidak_diterbitkan).sum())
nbb = int((sv.seri_kode == "tabel:sdg7_bahan_bakar").sum())
print("bahan bakar: 3920 - silver =", 3920 - nbb, "; sebelum ada dalam tahun terbit + missing sejati =", sel70 + int(gb.missing_sejati.sum()))
kt = gb[gb.nama_provinsi == "Kalimantan Utara"]
print("Kalimantan Utara: missing sejati =", int(kt.missing_sejati.sum()), "; sebelum ada dalam tahun terbit =", int((kt.sebelum_provinsi_ada & ~kt.tahun_tidak_diterbitkan).sum()))
