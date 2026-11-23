
import pandas as pd

# Membaca data asli dan daftar calon anomali
df = pd.read_csv("data/raw/bps/2026-10-17/sdg7_bahan_bakar.csv")
anomali = pd.read_csv("reports/calon_anomali_bahan_bakar.csv")

df["tahun"] = pd.to_numeric(df["tahun"], errors="coerce")
df["nilai"] = pd.to_numeric(df["nilai"], errors="coerce")

# Mengambil 14 data yang terdeteksi IQR dan Z-score
anomali_keduanya = anomali[
    anomali["alasan"].str.contains("Z-score", na=False)
]

hasil = []

for _, baris in anomali_keduanya.iterrows():
    wilayah = baris["wilayah"]
    bahan_bakar = baris["bahan_bakar"]
    tahun_anomali = int(baris["tahun"])

    # Mengambil data wilayah dan kategori yang sama
    konteks = df[
        (df["wilayah"] == wilayah) &
        (df["bahan_bakar"] == bahan_bakar) &
        (df["tahun"].between(tahun_anomali - 2, tahun_anomali + 2))
    ].copy()

    konteks["tahun_anomali"] = tahun_anomali
    konteks["status"] = konteks["tahun"].apply(
        lambda x: "CALON ANOMALI" if x == tahun_anomali
        else "Pembanding"
    )

    hasil.append(konteks)

# Menggabungkan hasil pemeriksaan
hasil_df = pd.concat(hasil, ignore_index=True)

hasil_df = hasil_df[
    ["wilayah", "bahan_bakar", "tahun", "nilai",
     "tahun_anomali", "status"]
].sort_values(["wilayah", "bahan_bakar", "tahun"])

# Menyimpan hasil
hasil_df.to_csv(
    "reports/konteks_anomali_bahan_bakar.csv",
    index=False,
    encoding="utf-8-sig"
)

print("=== PEMERIKSAAN KONTEKS CALON ANOMALI ===")
print(hasil_df.to_string(index=False))

print("\nFile tersimpan:")
print("reports/konteks_anomali_bahan_bakar.csv")
