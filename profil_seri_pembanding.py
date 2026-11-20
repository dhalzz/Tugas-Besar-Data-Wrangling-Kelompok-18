import json
import csv
from pathlib import Path

import pandas as pd

# =====================================================
# 1. LOKASI DATA
# =====================================================
data_wdi = Path("data/raw/wdi")
data_var87 = Path("data/raw/bps/var87_long.csv")
folder_reports = Path("reports")
folder_reports.mkdir(exist_ok=True)

# =====================================================
# 2. INDIKATOR YANG DIPERIKSA
# =====================================================
kode_target = {
    "EG.ELC.ACCS.ZS": "Akses listrik nasional",
    "EG.ELC.ACCS.UR.ZS": "Akses listrik perkotaan",
    "EG.ELC.ACCS.RU.ZS": "Akses listrik perdesaan",
    "EG.CFT.ACCS.ZS": "Bahan bakar bersih nasional",
    "EG.CFT.ACCS.UR.ZS": "Bahan bakar bersih perkotaan",
    "EG.CFT.ACCS.RU.ZS": "Bahan bakar bersih perdesaan",
}

# =====================================================
# 3. BACA DATA UTAMA VAR87
# =====================================================
df_var87 = pd.read_csv(data_var87)
tahun_var87 = set(
    pd.to_numeric(df_var87["tahun"], errors="coerce")
    .dropna()
    .astype(int)
    .unique()
)

# =====================================================
# 4. BACA METADATA WDI
# =====================================================
file_metadata = list(data_wdi.rglob("sumber2_indikator.json"))

if not file_metadata:
    raise FileNotFoundError("File sumber2_indikator.json tidak ditemukan.")

with open(file_metadata[0], encoding="utf-8") as f:
    metadata_json = json.load(f)

metadata_records = metadata_json[1]

metadata = {
    r.get("id"): r
    for r in metadata_records
    if isinstance(r, dict) and r.get("id") in kode_target
}

# =====================================================
# 5. BACA OBSERVASI WDI
# =====================================================
observasi = {kode: {} for kode in kode_target}

for path in data_wdi.rglob("*.json"):
    if "metadata" in path.parts:
        continue

    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)

        if not isinstance(data, list) or len(data) < 2:
            continue

        records = data[1]

        if not isinstance(records, list):
            continue

        for r in records:
            if not isinstance(r, dict):
                continue

            kode = r.get("indicator", {}).get("id")

            if kode not in kode_target:
                continue

            try:
                tahun = int(r.get("date"))
            except (TypeError, ValueError):
                continue

            negara = r.get("country", {}).get("value", "")
            nilai = r.get("value")

            # Satu observasi unik per kode, negara, dan tahun
            kunci = (negara, tahun)
            observasi[kode][kunci] = nilai

    except (json.JSONDecodeError, OSError) as e:
        print("File dilewati:", path, "|", e)

# =====================================================
# 6. SUSUN TABEL KETERSEDIAAN SERI
# =====================================================
hasil_ketersediaan = []

for kode, nama_singkat in kode_target.items():
    meta = metadata.get(kode, {})
    rows = observasi[kode]

    tahun_bernilai = sorted({
        tahun
        for (negara, tahun), nilai in rows.items()
        if nilai is not None
    })

    irisan = sorted(set(tahun_bernilai) & tahun_var87)

    nama = meta.get("name", nama_singkat)
    satuan = meta.get("unit", "")
    catatan = meta.get("sourceNote", "")

    if tahun_bernilai:
        periode = f"{min(tahun_bernilai)}-{max(tahun_bernilai)}"
    else:
        periode = "Belum tersedia"

    hasil_ketersediaan.append({
        "kode_indikator": kode,
        "nama_indikator": nama,
        "sumber": meta.get("source", {}).get("value", ""),
        "satuan_metadata": satuan,
        "jumlah_observasi": len(rows),
        "jumlah_nilai_tersedia": sum(
            nilai is not None for nilai in rows.values()
        ),
        "periode_nilai_tersedia": periode,
        "tahun_tersedia": ";".join(map(str, tahun_bernilai)),
        "jumlah_tahun_beririsan_var87": len(irisan),
        "tahun_beririsan_var87": ";".join(map(str, irisan)),
        "catatan_definisi": catatan,
    })

df_ketersediaan = pd.DataFrame(hasil_ketersediaan)
df_ketersediaan.to_csv(
    folder_reports / "ketersediaan_seri_pembanding.csv",
    index=False,
    encoding="utf-8-sig"
)

# =====================================================
# 7. SUSUN TABEL KANDIDAT RINCIAN
# =====================================================
kandidat = [
    {
        "kode_indikator": "EG.ELC.ACCS.ZS",
        "rincian": "Nasional",
        "status_observasi": "Tersedia",
        "status_kandidat": "Kandidat pembanding konseptual",
        "alasan": (
            "Sama-sama berkaitan dengan akses listrik, tetapi WDI "
            "mengukur persentase penduduk yang memiliki akses listrik, "
            "sedangkan var87 mengukur persentase rumah tangga dengan "
            "sumber penerangan utama listrik PLN."
        )
    },
    {
        "kode_indikator": "EG.ELC.ACCS.UR.ZS",
        "rincian": "Perkotaan",
        "status_observasi": "Tersedia",
        "status_kandidat": "Konteks tambahan",
        "alasan": (
            "Menggambarkan akses listrik penduduk perkotaan. "
            "Var87 tidak memiliki rincian perkotaan sehingga "
            "tidak dapat dicocokkan secara langsung."
        )
    },
    {
        "kode_indikator": "EG.ELC.ACCS.RU.ZS",
        "rincian": "Perdesaan",
        "status_observasi": "Tersedia",
        "status_kandidat": "Konteks tambahan",
        "alasan": (
            "Menggambarkan akses listrik penduduk perdesaan. "
            "Var87 tidak memiliki rincian perdesaan sehingga "
            "tidak dapat dicocokkan secara langsung."
        )
    },
    {
        "kode_indikator": "EG.CFT.ACCS.ZS",
        "rincian": "Nasional",
        "status_observasi": "Tersedia",
        "status_kandidat": "Bukan pembanding langsung",
        "alasan": (
            "Mengukur penggunaan bahan bakar dan teknologi memasak "
            "bersih, bukan akses listrik atau sumber penerangan."
        )
    },
    {
        "kode_indikator": "EG.CFT.ACCS.UR.ZS",
        "rincian": "Perkotaan",
        "status_observasi": "Metadata tersedia; observasi belum ditemukan",
        "status_kandidat": "Bukan pembanding langsung",
        "alasan": (
            "Mengukur penggunaan bahan bakar memasak bersih penduduk "
            "perkotaan. Konsepnya berbeda dari var87 dan observasi "
            "belum ditemukan dalam file yang diperiksa."
        )
    },
    {
        "kode_indikator": "EG.CFT.ACCS.RU.ZS",
        "rincian": "Perdesaan",
        "status_observasi": "Metadata tersedia; observasi belum ditemukan",
        "status_kandidat": "Bukan pembanding langsung",
        "alasan": (
            "Mengukur penggunaan bahan bakar memasak bersih penduduk "
            "perdesaan. Konsepnya berbeda dari var87 dan observasi "
            "belum ditemukan dalam file yang diperiksa."
        )
    },
]

df_kandidat = pd.DataFrame(kandidat)
df_kandidat.to_csv(
    folder_reports / "kandidat_rincian_pembanding.csv",
    index=False,
    encoding="utf-8-sig"
)

# =====================================================
# 8. BUAT LAPORAN MARKDOWN
# =====================================================
baris_tabel = []

for r in hasil_ketersediaan:
    baris_tabel.append(
        f"| {r['kode_indikator']} | {r['nama_indikator']} "
        f"| {r['jumlah_observasi']} | {r['jumlah_nilai_tersedia']} "
        f"| {r['periode_nilai_tersedia']} "
        f"| {r['jumlah_tahun_beririsan_var87']} |"
    )

tahun_var87_urut = sorted(tahun_var87)

isi_laporan = f"""# Profil Seri Pembanding

## 1. Tujuan

Profil ini dibuat untuk memeriksa ketersediaan seri pembanding
terhadap seri utama BPS `var87`, yaitu persentase rumah tangga
menurut wilayah dan sumber penerangan utama dari listrik PLN.

Pemeriksaan mencakup periode, rincian indikator, satuan,
dan irisan tahun dengan seri utama.

## 2. Profil seri utama

- File: `data/raw/bps/var87_long.csv`
- Jumlah baris: {len(df_var87)}
- Kolom: wilayah, tahun, nilai
- Periode tahun: {min(tahun_var87_urut)}-{max(tahun_var87_urut)}
- Jumlah tahun yang memiliki data: {len(tahun_var87_urut)}
- Tahun yang tersedia: {", ".join(map(str, tahun_var87_urut))}

## 3. Ketersediaan seri pembanding

| Kode | Nama indikator | Seluruh observasi | Bernilai | Periode | Tahun beririsan |
|---|---|---:|---:|---|---:|
{chr(10).join(baris_tabel)}

Catatan:
- Satuan pada metadata WDI tercatat kosong.
- Informasi persentase tercantum pada nama indikator.
- Periode dihitung dari tahun yang memiliki nilai, bukan sekadar
  rentang tahun pada seluruh baris observasi.
- Tahun beririsan dihitung terhadap tahun yang tersedia pada var87.

## 4. Rincian indikator

Indikator akses listrik tersedia dalam tiga rincian:
nasional, perkotaan, dan perdesaan.

Indikator bahan bakar bersih juga tercantum dalam metadata
untuk rincian nasional, perkotaan, dan perdesaan. Namun,
pada file observasi yang diperiksa, hanya indikator nasional
yang ditemukan.

Tidak ditemukan rincian berdasarkan jenis kelamin atau kelompok
umur pada enam indikator yang menjadi fokus pemeriksaan ini.

## 5. Penilaian kandidat pembanding

### Akses listrik

`EG.ELC.ACCS.ZS` merupakan kandidat pembanding konseptual
karena sama-sama berkaitan dengan akses listrik.

Namun, kedua indikator tidak identik:
- `var87` menggunakan rumah tangga sebagai dasar pengukuran
  dan khusus mengukur sumber penerangan utama dari listrik PLN.
- WDI mengukur persentase penduduk yang memiliki akses listrik.

Indikator perkotaan dan perdesaan dapat digunakan sebagai
konteks tambahan. Keduanya tidak dapat langsung dipasangkan
dengan rincian var87 karena var87 dalam file ini dibagi
berdasarkan wilayah, bukan klasifikasi perkotaan/perdesaan.

### Bahan bakar bersih

Indikator `EG.CFT.ACCS.ZS` mengukur proporsi penduduk yang
terutama menggunakan bahan bakar dan teknologi memasak bersih.
Menurut catatan metadata, minyak tanah tidak termasuk bahan
bakar memasak bersih berdasarkan pedoman WHO.

Indikator ini bukan pembanding langsung untuk var87 karena
mengukur penggunaan energi untuk memasak, bukan sumber
penerangan atau akses listrik. Indikator ini hanya dapat
digunakan sebagai konteks tambahan mengenai kondisi energi.

## 6. Kesimpulan

Seri akses listrik WDI merupakan kandidat pembanding konseptual
yang paling relevan, tetapi perbedaan unit analisis dan definisi
harus diperhatikan dalam analisis lanjutan.

Rincian perkotaan dan perdesaan dapat menjadi konteks tambahan,
sedangkan seri bahan bakar bersih tidak digunakan sebagai
pembanding langsung.

Hasil ini dapat menjadi dasar pemilihan rincian yang sebanding
pada tahap 6.
"""

(folder_reports / "profil_seri_pembanding.md").write_text(
    isi_laporan, encoding="utf-8"
)

# =====================================================
# 9. TAMPILKAN HASIL
# =====================================================
print("\n=== KETERSEDIAAN SERI PEMBANDING ===")
print(df_ketersediaan[
    [
        "kode_indikator",
        "jumlah_observasi",
        "jumlah_nilai_tersedia",
        "periode_nilai_tersedia",
        "jumlah_tahun_beririsan_var87"
    ]
].to_string(index=False))

print("\n=== KANDIDAT RINCIAN ===")
print(df_kandidat[
    ["kode_indikator", "rincian", "status_observasi", "status_kandidat"]
].to_string(index=False))

print("\nFile berhasil dibuat:")
print("- reports/ketersediaan_seri_pembanding.csv")
print("- reports/kandidat_rincian_pembanding.csv")
print("- reports/profil_seri_pembanding.md")
