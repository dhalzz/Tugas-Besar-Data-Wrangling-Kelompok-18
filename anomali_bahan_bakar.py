
import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path

# Membaca data
df = pd.read_csv("data/raw/bps/2026-10-17/sdg7_bahan_bakar.csv")

# Mengubah tipe data
df["nilai"] = pd.to_numeric(df["nilai"], errors="coerce")
df["tahun"] = pd.to_numeric(df["tahun"], errors="coerce")

# Mengeluarkan kategori Jumlah dan data nasional
df_provinsi = df[
    (df["wilayah"] != "INDONESIA") &
    (df["bahan_bakar"] != "Jumlah")
].copy()

# Menghapus nilai kosong untuk perhitungan
df_provinsi = df_provinsi.dropna(subset=["nilai"])

# Folder penyimpanan
Path("reports/gambar").mkdir(parents=True, exist_ok=True)

# ==========================
# 1. BOXPLOT BAHAN BAKAR
# ==========================

plt.figure(figsize=(12, 6))

df_provinsi.boxplot(
    column="nilai",
    by="bahan_bakar",
    rot=30
)

plt.title("Boxplot Persentase Jenis Bahan Bakar")
plt.suptitle("")
plt.xlabel("Jenis Bahan Bakar")
plt.ylabel("Persentase (%)")
plt.tight_layout()

plt.savefig("reports/gambar/boxplot_bahan_bakar.png")
plt.close()

# ==========================
# 2. DETEKSI IQR DAN Z-SCORE
# ==========================

hasil_anomali = []

for (wilayah, bahan_bakar), grup in df_provinsi.groupby(
    ["wilayah", "bahan_bakar"]
):

    nilai = grup["nilai"]

    # Minimal 8 data
    if len(nilai) < 8:
        continue

    Q1 = nilai.quantile(0.25)
    Q3 = nilai.quantile(0.75)
    IQR = Q3 - Q1

    batas_bawah = Q1 - 1.5 * IQR
    batas_atas = Q3 + 1.5 * IQR

    rata_rata = nilai.mean()
    standar_deviasi = nilai.std()

    for indeks, baris in grup.iterrows():

        alasan = []

        # Deteksi IQR
        if (
            baris["nilai"] < batas_bawah or
            baris["nilai"] > batas_atas
        ):
            alasan.append("IQR")

        # Deteksi Z-score
        if standar_deviasi > 0:
            z_score = (
                baris["nilai"] - rata_rata
            ) / standar_deviasi

            if abs(z_score) > 3:
                alasan.append("Z-score")

        if alasan:
            hasil_anomali.append({
                "wilayah": wilayah,
                "tahun": int(baris["tahun"]),
                "bahan_bakar": bahan_bakar,
                "nilai": baris["nilai"],
                "alasan": ", ".join(alasan)
            })

# Menyimpan hasil
df_anomali = pd.DataFrame(hasil_anomali)

df_anomali.to_csv(
    "reports/calon_anomali_bahan_bakar.csv",
    index=False,
    encoding="utf-8-sig"
)

# ==========================
# 3. MENAMPILKAN HASIL
# ==========================

print("=== HASIL DETEKSI ANOMALI BAHAN BAKAR ===")
print("Jumlah data diperiksa:", len(df_provinsi))
print("Jumlah calon anomali:", len(df_anomali))

print("\n=== JUMLAH ANOMALI PER JENIS ===")

if not df_anomali.empty:
    print(df_anomali["bahan_bakar"].value_counts())

    print("\n=== CONTOH CALON ANOMALI ===")
    print(df_anomali.head(20).to_string(index=False))
else:
    print("Tidak ditemukan calon anomali.")

print("\nHasil disimpan di folder reports.")
