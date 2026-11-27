import os
import sys

import pandas as pd

B = sys.argv[1] if len(sys.argv) > 1 else r"..\wt-integrasi"
RAW_BB = 3920  # baris 2026-10-17_sdg7_bahan_bakar hasil ekstraksi

log = pd.read_csv(os.path.join(B, "log-keputusan.csv")).set_index("id")
sv = pd.read_parquet(os.path.join(B, "data", "silver", "silver.parquet"))
gb = pd.read_parquet(os.path.join(B, "data", "silver", "grid_bahan_bakar.parquet"))
gl = pd.read_parquet(os.path.join(B, "data", "silver", "grid_listrik.parquet"))
cv = pd.read_csv(os.path.join(B, "reports", "calon_anomali_var87.csv"))
cb = pd.read_csv(os.path.join(B, "reports", "calon_anomali_bahan_bakar.csv"))


def alt(*ids):
    hasil = []
    for i in ids:
        a = str(log.loc[i, "alternatif_ditolak"]).strip().replace("|", "/")
        if a and a.lower() != "nan":
            hasil.append(f"{a} ({i})")
    return "; ".join(hasil) if hasil else "-"


def ribu(x):
    return f"{int(x):,}".replace(",", ".")


tl = sorted(gl.loc[gl.tahun_tidak_diterbitkan, "tahun"].unique())
tb = sorted(gb.loc[gb.tahun_tidak_diterbitkan, "tahun"].unique())
n_tl, n_tb = int(gl.tahun_tidak_diterbitkan.sum()), int(gb.tahun_tidak_diterbitkan.sum())
prov_l, prov_b = gl.nama_provinsi.nunique(), gb.nama_provinsi.nunique()
sel_per_tahun = int((gb.tahun == tb[0]).sum())
n_pl = int(gl.sebelum_provinsi_ada.sum())
pv_l = gl.loc[gl.sebelum_provinsi_ada, "nama_provinsi"].nunique()
n_pb = int(gb.sebelum_provinsi_ada.sum())
pv_b = gb.loc[gb.sebelum_provinsi_ada, "nama_provinsi"].nunique()
n_pb_terbit = int((gb.sebelum_provinsi_ada & ~gb.tahun_tidak_diterbitkan).sum())
m_l, m_b = int(gl.missing_sejati.sum()), int(gb.missing_sejati.sum())
per_tahun = gb[gb.missing_sejati].groupby("tahun").size()
teks_tahun = ", ".join(f"{t}: {n}" for t, n in per_tahun.items())
top = gb[gb.missing_sejati].groupby("nama_provinsi").size().sort_values(ascending=False).head(4)
teks_top = ", ".join(f"{k} {v}" for k, v in top.items())
n_sv_bb = int((sv.seri_kode == "tabel:sdg7_bahan_bakar").sum())
selisih = RAW_BB - n_sv_bb
if selisih != n_pb_terbit + m_b:
    print("PERINGATAN: selisih mentah-Silver tidak sama dengan sel belum ada + missing sejati")

v = sv[sv.seri_kode == "var87"].copy()
v["tahun"] = v.periode.astype(int)
w = v.pivot_table(index="tahun", columns="wilayah_kode", values="nilai")
n = (w.diff().abs() > 10).sum(axis=1)
n = n[n > 0]
teks_patahan = ", ".join(f"{t}: {k}" for t, k in n.items())
maks_thn, maks_n, n_wil = int(n.idxmax()), int(n.max()), w.shape[1]

snap = sorted(sv["_berkas_raw"].str.extract(r"(\d{4}-\d{2}-\d{2})")[0].dropna().unique())
n_idn = int((sv.wilayah_kode == 9999).sum())
n_jml = int((sv.rincian == "Jumlah").sum())

L = []
L.append("## Masalah data dan penanganannya\n")
L.append(
    f"Temuan Sprint 1 berasal dari Silver ({ribu(len(sv))} baris) dan `log-keputusan.csv` "
    "(K-001 s.d. K-021). Setiap angka dapat dihitung ulang dengan `hitung_ulang_tim.py`.\n"
)
L.append("| Masalah | Temuan dan jumlah terdampak | Penanganan | Alternatif ditolak | Log |")
L.append("|---|---|---|---|---|")
L.append(
    f"| Celah panel: tahun tidak diterbitkan | Listrik tahun {', '.join(map(str, tl))}: {ribu(n_tl)} sel "
    f"({prov_l} provinsi x {len(tl)} tahun). Bahan bakar tahun {tb[0]}-{tb[-1]}: {ribu(n_tb)} sel "
    f"({len(tb)} tahun x {sel_per_tahun} sel). | Ditandai `tahun_tidak_diterbitkan`, bukan missing sejati; tidak diimputasi. "
    f"| {alt('K-007', 'K-008')} | K-007, K-008 |"
)
L.append(
    f"| Celah panel: provinsi belum ada | Listrik {ribu(n_pl)} sel ({pv_l} provinsi). Bahan bakar {ribu(n_pb)} sel "
    f"({pv_b} provinsi), {ribu(n_pb_terbit)} di antaranya pada tahun terbit. | Dikosongkan sebelum `tahun_mulai`; "
    f"provinsi induk memakai nilai historis penuh. | {alt('K-002', 'K-003')} | K-002, K-003 |"
)
L.append(
    f"| Missing sejati | Bahan bakar {m_b} sel ({teks_tahun}; terbanyak: {teks_top}). Listrik {m_l} sel. "
    f"Selisih baris CSV mentah ({ribu(RAW_BB)}) dan Silver ({ribu(n_sv_bb)}) = {selisih} = {m_b} missing sejati "
    f"+ {n_pb_terbit} sel provinsi belum ada. | Dipertahankan sebagai kosong, tidak diimputasi. | {alt('K-009')} | K-009 |"
)
L.append(
    f"| Kandidat anomali | var87: {len(cv)} kandidat (`reports/calon_anomali_var87.csv`). Bahan bakar: {len(cb)} kandidat "
    "(`reports/calon_anomali_bahan_bakar.csv`). Nilai Raw BPS dan Silver identik. | Seluruhnya ditinjau dan dikategorikan "
    f"kandidat anomali lokal; tidak ada nilai diubah atau dihapus. | {alt('K-011', 'K-012', 'K-013', 'K-014', 'K-019', 'K-020', 'K-021')} "
    "| K-011 s.d. K-014, K-019 s.d. K-021 |"
)
L.append(
    f"| Patahan seri | Perubahan >10 poin per tahun pada var87 (jumlah wilayah dari {n_wil}): {teks_patahan}. "
    f"Terbanyak {maks_n} wilayah pada {maks_thn}. | Tidak ada indikasi patahan serentak; nilai dipertahankan. "
    f"| {alt('K-017')} | K-017 |"
)
L.append(
    f"| Revisi antar-snapshot | Snapshot Raw BPS tersedia: {len(snap)} ({', '.join(snap)}). | Audit revisi belum dapat dilakukan; "
    f"aturan deduplikasi ditetapkan. | {alt('K-016', 'K-018')} | K-016, K-018 |"
)
L.append(
    f"| Koreksi katalog wilayah dan rincian | {sv.wilayah_kode.nunique()} wilayah di Silver; baris INDONESIA: {n_idn}; "
    f"baris rincian Jumlah: {n_jml}. | Nama distandarkan lewat `dim_provinsi_38`; alias Bangka Belitung dan Kepulauan Riau disatukan; "
    f"INDONESIA dan Jumlah dipisah dari grid. | {alt('K-001', 'K-004', 'K-005', 'K-006')} | K-001, K-004 s.d. K-006 |"
)
L.append("")
L.append("### Temuan terpenting (bahan demo Sprint 1)\n")
L.append(f"1. Tidak semua sel kosong adalah data hilang: dari {selisih} baris yang hilang di bahan bakar, hanya {m_b} yang missing sejati.")
L.append(f"2. Tahun tidak terbit (listrik {', '.join(map(str, tl))}; bahan bakar {tb[0]}-{tb[-1]}) dibedakan dari missing, sehingga tidak diimputasi.")
L.append(f"3. Lonjakan ekstrem hanya menyangkut sedikit wilayah (maksimum {maks_n} dari {n_wil} pada {maks_thn}), jadi bukan patahan seri.")
L.append(f"4. Hanya {len(snap)} snapshot Raw BPS, sehingga revisi antar-snapshot belum dapat diaudit.")
L.append("")
L.append("### Cara menarik ulang angka\n")
L.append("Jalankan `python hitung_ulang_tim.py <folder berisi data/silver dan log-keputusan.csv>`; "
         "`python bangun_draf_masalah.py <folder yang sama>` menulis ulang tabel ini.")

with open("draf_masalah_data.md", "w", encoding="utf-8") as f:
    f.write("\n".join(L) + "\n")
print("draf_masalah_data.md ditulis")