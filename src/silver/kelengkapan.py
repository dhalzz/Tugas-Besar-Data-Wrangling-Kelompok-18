"""v4: hitung n_sel_relevan langsung dari grid (hindari double count sebelum-ada vs tahun-absen)."""
from __future__ import annotations
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
NIM = "124450066"

def hitung():
    semua = []
    for jenis in ("listrik", "bahan_bakar"):
        g = pd.read_parquet(ROOT / "data" / "silver" / f"grid_{jenis}.parquet")
        g["relevan"] = ~g["sebelum_provinsi_ada"] & ~g["tahun_tidak_diterbitkan"]
        rows = []
        for tahun, sub in g.groupby("tahun"):
            rel = sub[sub["relevan"]]
            n_rel = len(rel)
            n_isi = int(rel["nilai"].notna().sum())
            rows.append({
                "tahun": int(tahun),
                "n_sel_grid": len(sub),
                "n_sel_relevan": n_rel,
                "n_terisi": n_isi,
                "persen_terisi": round(100 * n_isi / n_rel, 2) if n_rel else None,
                "seri": jenis,
            })
        semua.append(pd.DataFrame(rows))
    kel = pd.concat(semua, ignore_index=True)
    kel.to_csv(ROOT / "results" / NIM / "kelengkapan_panel_per_seri.csv", index=False)
    print(kel.to_string(index=False))
    # ringkasan: persen rata-rata per seri pada tahun terbit saja
    for jenis, sub in kel.groupby("seri"):
        terbit = sub[sub["n_sel_relevan"] > 0]
        rata = round(terbit["persen_terisi"].mean(), 2)
        print(f"[{jenis}] tahun terbit={len(terbit)}, rata-rata persen terisi={rata}")

if __name__ == "__main__":
    hitung()
