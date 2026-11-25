"""Tabel nasional Gold (tugas #21): seri utama BPS dan pembanding WDI per periode."""
import csv
import pandas as pd
from src.silver.grid import LOG, tulis_log

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

def catat_keputusan():
    sudah = set()
    if LOG.exists():
        with open(LOG, encoding="utf-8") as f:
            sudah = {r["keputusan"] for r in csv.DictReader(f)}
    entri = [
        dict(tanggal="2026-11-25", seri="var87+bahan_bakar(sdg7)",
             keputusan="Tabel nasional Gold memakai baris INDONESIA (wilayah_kode 9999) kedua seri BPS; tanpa agregat provinsi.",
             alternatif_ditolak="rata-rata sederhana atau tertimbang provinsi",
             alasan="Kedua seri menerbitkan baris Indonesia pada setiap tahun terbit; persentase rumah tangga butuh bobot yang tidak ada di sumber. Dijaga oleh tes di pipeline.",
             baris_terdampak="var87: 32 tahun; sdg7: 2001 dan 2007-2021"),
        dict(tanggal="2026-11-25", seri="bahan_bakar(sdg7)",
             keputusan="Baris rincian 'Jumlah' tidak masuk Gold; dipakai sebagai cek jumlah kategori ~100 (toleransi 0,05).",
             alternatif_ditolak="memperlakukan Jumlah sebagai kategori",
             alasan="Jumlah adalah total; selisih 100,01 pada 2020 adalah pembulatan.",
             baris_terdampak="1 baris per tahun terbit"),
        dict(tanggal="2026-11-25", seri="gold_nasional",
             keputusan="Kunci Gold = periode x seri_kode x rincian; asal_angka membedakan baris_indonesia dan pembanding_wdi.",
             alternatif_ditolak="satu baris per periode x seri tanpa rincian",
             alasan="Seri bahan bakar punya 6 kategori per tahun.",
             baris_terdampak="seluruh tabel Gold nasional"),
        dict(tanggal="2026-11-25", seri="EG.ELC.ACCS.ZS+EG.CFT.ACCS.ZS",
             keputusan="Baris WDI dengan value kosong tidak dimasukkan ke Gold nasional.",
             alternatif_ditolak="memasukkan baris kosong; mengisi dari tahun tetangga",
             alasan="Kosong di WDI berarti tidak ada estimasi, bukan nilai hilang di terbitan BPS; mengisinya mengarang angka.",
             baris_terdampak="tahun WDI tanpa estimasi (dihitung saat pipeline dijalankan)"),
        dict(tanggal="2026-11-25", seri="EG.ELC.ACCS.ZS+EG.CFT.ACCS.ZS",
             keputusan="Pembanding dipasangkan: EG.ELC.ACCS.ZS dengan var87, EG.CFT.ACCS.ZS dengan sdg7_bahan_bakar; definisi tidak disamakan.",
             alternatif_ditolak="menggabungkan kedua sumber menjadi satu seri",
             alasan="WDI mengukur persentase penduduk dengan akses; basis hitung BPS belum diverifikasi sama. Gold hanya menyandingkan.",
             baris_terdampak="seluruh baris pembanding_wdi"),
    ]
    tulis_log([e for e in entri if e["keputusan"] not in sudah])