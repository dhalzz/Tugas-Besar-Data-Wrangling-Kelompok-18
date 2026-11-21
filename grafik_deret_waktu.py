
import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path

# Membuat folder penyimpanan grafik
Path("reports/gambar").mkdir(parents=True, exist_ok=True)


# ==========================================
# 1. GRAFIK DERET WAKTU VAR87
# ==========================================

df_var87 = pd.read_csv("data/raw/bps/var87_long.csv")

df_var87["tahun"] = pd.to_numeric(
    df_var87["tahun"], errors="coerce"
)
df_var87["nilai"] = pd.to_numeric(
    df_var87["nilai"], errors="coerce"
)

# Mengambil data nasional
nasional_var87 = df_var87[
    df_var87["wilayah"] == "INDONESIA"
].dropna(subset=["tahun", "nilai"])

nasional_var87 = nasional_var87.sort_values("tahun")

plt.figure(figsize=(12, 6))
plt.plot(
    nasional_var87["tahun"],
    nasional_var87["nilai"],
    marker="o"
)

plt.title("Deret Waktu Persentase Rumah Tangga dengan Listrik PLN")
plt.xlabel("Tahun")
plt.ylabel("Persentase (%)")
plt.grid(True)
plt.tight_layout()

plt.savefig("reports/gambar/deret_waktu_var87.png")
plt.close()


# ==========================================
# 2. GRAFIK DERET WAKTU BAHAN BAKAR
# ==========================================

df_bahan = pd.read_csv(
    "data/raw/bps/2026-10-17/sdg7_bahan_bakar.csv"
)

df_bahan["tahun"] = pd.to_numeric(
    df_bahan["tahun"], errors="coerce"
)
df_bahan["nilai"] = pd.to_numeric(
    df_bahan["nilai"], errors="coerce"
)

# Mengambil data nasional dan membuang kategori Jumlah
nasional_bahan = df_bahan[
    (df_bahan["wilayah"] == "INDONESIA") &
    (df_bahan["bahan_bakar"] != "Jumlah")
].dropna(subset=["tahun", "nilai"])

nasional_bahan = nasional_bahan.sort_values("tahun")

plt.figure(figsize=(12, 6))

for jenis, grup in nasional_bahan.groupby("bahan_bakar"):
    plt.plot(
        grup["tahun"],
        grup["nilai"],
        marker="o",
        label=jenis
    )

plt.title("Deret Waktu Persentase Jenis Bahan Bakar Nasional")
plt.xlabel("Tahun")
plt.ylabel("Persentase (%)")
plt.legend(title="Jenis Bahan Bakar")
plt.grid(True)
plt.tight_layout()

plt.savefig("reports/gambar/deret_waktu_bahan_bakar.png")
plt.close()


# ==========================================
# 3. INFORMASI HASIL
# ==========================================

print("=== GRAFIK DERET WAKTU BERHASIL DIBUAT ===")
print("1. reports/gambar/deret_waktu_var87.png")
print("2. reports/gambar/deret_waktu_bahan_bakar.png")

print("\nJumlah data nasional var87:", len(nasional_var87))
print("Jumlah data nasional bahan bakar:", len(nasional_bahan))
print(
    "Jenis bahan bakar:",
    nasional_bahan["bahan_bakar"].nunique()
)
