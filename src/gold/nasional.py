"""Tabel nasional Gold (tugas #21): seri utama BPS dan pembanding WDI per periode."""
import pandas as pd

KODE_NAS = 9999
SERI_UTAMA = ["var87", "tabel:sdg7_bahan_bakar"]
# pasangan mengikuti urutan di tugas; koreksi bila tim memasangkan lain
PEMBANDING = {"EG.ELC.ACCS.ZS": "var87", "EG.CFT.ACCS.ZS": "tabel:sdg7_bahan_bakar"}
TOLERANSI_JUMLAH = 0.05
KOLOM = ["periode", "seri_kode", "rincian", "nilai", "satuan", "peran", "pasangan_utama",
         "asal_angka", "sumber", "keterangan", "_berkas_raw", "_sha256_raw"]

def _periode(s):
    return s.astype(str).str.strip().str[:4]

def _total(s):
    return s.astype(str).str.strip().str.lower() == "jumlah"

def _cek_jumlah(nas):
    bb = nas[nas["seri_kode"] == "tabel:sdg7_bahan_bakar"]
    tot = bb[_total(bb["rincian"])].set_index("periode")["nilai"]
    jml = bb[~_total(bb["rincian"])].groupby("periode")["nilai"].sum()
    selisih = (jml - tot).abs().dropna()
    assert (selisih <= TOLERANSI_JUMLAH).all(), selisih[selisih > TOLERANSI_JUMLAH]

def _utama(silver):
    nas = silver[(silver["wilayah_kode"] == KODE_NAS) & silver["seri_kode"].isin(SERI_UTAMA)].copy()
    nas["periode"] = _periode(nas["periode"])
    _cek_jumlah(nas)

    # aturan "tanpa agregat" dijadikan tes: gagal keras bila tahun terbit tak punya baris Indonesia
    prov = silver[(silver["wilayah_kode"] != KODE_NAS) & silver["seri_kode"].isin(SERI_UTAMA)
                  & silver["nilai"].notna()]
    for seri in SERI_UTAMA:
        p = set(_periode(prov.loc[prov["seri_kode"] == seri, "periode"]))
        n = set(nas.loc[nas["seri_kode"] == seri, "periode"])
        assert p <= n, f"{seri}: tahun tanpa baris Indonesia {sorted(p - n)}"

    u = nas[~_total(nas["rincian"])].copy()
    u["peran"], u["pasangan_utama"] = "utama", None
    u["asal_angka"], u["keterangan"] = "baris_indonesia", None
    return u

def _pembanding(mentah):
    bagian = []
    for kunci, tabel in mentah.items():
        kode = kunci.split("::")[-1]
        if not (kunci.startswith("wdi/") and "/data/" in kunci and kode in PEMBANDING):
            continue
        t = tabel[tabel["countryiso3code"] == "IDN"]
        out = pd.DataFrame({
            "periode": _periode(t["date"]), "seri_kode": kode, "rincian": None,
            "nilai": pd.to_numeric(t["value"], errors="coerce"),
            "satuan": "persen", "peran": "pembanding", "pasangan_utama": PEMBANDING[kode],
            "asal_angka": "pembanding_wdi", "sumber": "wdi",
            "keterangan": t["indicator.value"],
            "_berkas_raw": t["_berkas_raw"], "_sha256_raw": t["_sha256_raw"]})
        print(f"  WDI {kode}: {len(out)} baris, {int(out['nilai'].isna().sum())} tanpa nilai di sumber (tidak dimasukkan)")
        bagian.append(out[out["nilai"].notna()])
    assert len(bagian) == len(PEMBANDING), "seri WDI tidak lengkap di hasil ekstraksi"
    return pd.concat(bagian, ignore_index=True)

def bangun_nasional(silver, mentah):
    gold = pd.concat([_utama(silver), _pembanding(mentah)], ignore_index=True)[KOLOM]
    kunci = ["periode", "seri_kode", "rincian"]
    assert not gold.duplicated(kunci).any(), "kunci periode x seri x rincian tidak unik"
    assert gold["_berkas_raw"].notna().all(), "ada baris tanpa _berkas_raw"
    gold = gold.sort_values(kunci, na_position="first").reset_index(drop=True)
    print(gold.groupby(["seri_kode", "asal_angka"]).size().to_string())
    return gold
