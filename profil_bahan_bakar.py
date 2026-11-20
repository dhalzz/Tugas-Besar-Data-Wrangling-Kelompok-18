import pandas as pd
from pathlib import Path

# Membaca data bahan bakar
path = "data/raw/bps/2026-10-17/sdg7_bahan_bakar.csv"
df = pd.read_csv(path)

# Memastikan nilai berbentuk numerik
df["nilai"] = pd.to_numeric(df["nilai"], errors="coerce")
df["tahun"] = pd.to_numeric(df["tahun"], errors="coerce")

# Membuat folder laporan
Path("reports").mkdir(exist_ok=True)

# Statistik berdasarkan jenis bahan bakar
profil_bahan_bakar = df.groupby("bahan_bakar")["nilai"].agg(
    jumlah_data="count",
    rata_rata="mean",
    median="median",
    minimum="min",
    maksimum="max",
    standar_deviasi="std",
    Q1=lambda x: x.quantile(0.25),
    Q3=lambda x: x.quantile(0.75)
).reset_index()

profil_bahan_bakar["IQR"] = (
    profil_bahan_bakar["Q3"] - profil_bahan_bakar["Q1"]
)

# Statistik berdasarkan wilayah dan jenis bahan bakar
profil_wilayah = df.groupby(
    ["wilayah", "bahan_bakar"]
)["nilai"].agg(
    jumlah_data="count",
    rata_rata="mean",
    median="median",
    minimum="min",
    maksimum="max",
    standar_deviasi="std",
    Q1=lambda x: x.quantile(0.25),
    Q3=lambda x: x.quantile(0.75)
).reset_index()

profil_wilayah["IQR"] = (
    profil_wilayah["Q3"] - profil_wilayah["Q1"]
)

# Memeriksa kelengkapan tahun
tahun_tersedia = sorted(df["tahun"].dropna().unique())
tahun_seharusnya = list(range(2001, 2022))
tahun_tidak_tersedia = sorted(
    set(tahun_seharusnya) - set(tahun_tersedia)
)

# Menyimpan hasil
profil_bahan_bakar.to_csv(
    "reports/profil_bahan_bakar_per_jenis.csv",
    index=False
)

profil_wilayah.to_csv(
    "reports/profil_bahan_bakar_per_wilayah.csv",
    index=False
)

print("=== PROFIL DATA BAHAN BAKAR ===")
print("Jumlah seluruh baris:", len(df))
print("Jumlah wilayah:", df["wilayah"].nunique())
print("Jumlah jenis bahan bakar:", df["bahan_bakar"].nunique())
print("Rentang tahun:", df["tahun"].min(), "-", df["tahun"].max())
print("Tahun tidak tersedia:", tahun_tidak_tersedia)

print("\n=== NILAI KOSONG ===")
print(df.isna().sum())

print("\n=== JUMLAH DATA TERSEDIA PER JENIS ===")
print(df.groupby("bahan_bakar")["nilai"].count())

print("\n=== STATISTIK PER JENIS BAHAN BAKAR ===")
print(profil_bahan_bakar.round(2).to_string(index=False))

print("\n=== STATISTIK PER WILAYAH DAN JENIS ===")
print(profil_wilayah.round(2).to_string(index=False))

print("\nHasil disimpan di folder reports.")
