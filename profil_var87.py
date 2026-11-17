import pandas as pd
from pathlib import Path

# Membaca hasil ekstraksi
df = pd.read_csv("data/raw/bps/var87_long.csv")

# Memisahkan data provinsi dan Indonesia
df_provinsi = df[df["wilayah"] != "INDONESIA"].copy()
df_nasional = df[df["wilayah"] == "INDONESIA"].copy()

# Statistik deskriptif setiap provinsi
profil_provinsi = df_provinsi.groupby("wilayah")["nilai"].agg(
    jumlah_data="count",
    rata_rata="mean",
    median="median",
    minimum="min",
    maksimum="max",
    standar_deviasi="std",
    Q1=lambda x: x.quantile(0.25),
    Q3=lambda x: x.quantile(0.75)
).reset_index()

profil_provinsi["IQR"] = profil_provinsi["Q3"] - profil_provinsi["Q1"]

# Statistik deskriptif nasional
profil_nasional = df_nasional["nilai"].describe()

# Tahun yang tersedia
tahun_tersedia = sorted(df["tahun"].dropna().unique())
tahun_seharusnya = list(range(1993, 2026))
tahun_tidak_tersedia = sorted(set(tahun_seharusnya) - set(tahun_tersedia))

# Membuat folder laporan jika belum ada
Path("reports").mkdir(exist_ok=True)

# Menyimpan hasil statistik
profil_provinsi.to_csv(
    "reports/profil_var87_per_provinsi.csv",
    index=False
)

print("=== PROFIL DATA VAR87 ===")
print("Jumlah seluruh baris:", len(df))
print("Jumlah provinsi:", df_provinsi["wilayah"].nunique())
print("Jumlah data nasional:", len(df_nasional))
print("Jumlah tahun tersedia:", len(tahun_tersedia))
print("Tahun tidak tersedia:", tahun_tidak_tersedia)

print("\n=== STATISTIK KESELURUHAN PROVINSI ===")
print(df_provinsi["nilai"].describe())

print("\n=== STATISTIK NASIONAL ===")
print(profil_nasional)

print("\n=== STATISTIK PER PROVINSI ===")
print(profil_provinsi.round(2).to_string(index=False))

print("\nHasil disimpan di reports/profil_var87_per_provinsi.csv")
