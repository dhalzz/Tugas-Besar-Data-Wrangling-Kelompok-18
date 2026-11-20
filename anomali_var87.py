import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path

# Membaca data hasil ekstraksi
df = pd.read_csv("data/raw/bps/var87_long.csv")

# Memisahkan data provinsi dan nasional
df = df[df["wilayah"] != "INDONESIA"].copy()

# Mengubah tipe data
df["tahun"] = pd.to_numeric(df["tahun"])
df["nilai"] = pd.to_numeric(df["nilai"])

# Membuat folder penyimpanan
Path("reports/gambar").mkdir(parents=True, exist_ok=True)

# =====================================
# 1. MEMBUAT BOXPLOT
# =====================================

plt.figure(figsize=(18, 8))

df.boxplot(
    column="nilai",
    by="wilayah",
    rot=90,
    grid=False
)

plt.title("Boxplot Persentase Rumah Tangga dengan Penerangan Utama PLN")
plt.suptitle("")
plt.xlabel("Provinsi")
plt.ylabel("Persentase (%)")
plt.tight_layout()

plt.savefig(
    "reports/gambar/boxplot_var87.png",
    dpi=300
)

plt.close()

# =====================================
# 2. DETEKSI ANOMALI IQR DAN Z-SCORE
# =====================================

hasil = []
wilayah_diperiksa = 0
wilayah_tidak_diperiksa = []

for wilayah, grup in df.groupby("wilayah"):

    # Menghindari deteksi pada kelompok dengan data terlalu sedikit
    if len(grup) < 8:
        wilayah_tidak_diperiksa.append(wilayah)
        continue

    wilayah_diperiksa += 1

    q1 = grup["nilai"].quantile(0.25)
    q3 = grup["nilai"].quantile(0.75)
    iqr = q3 - q1

    batas_bawah = q1 - 1.5 * iqr
    batas_atas = q3 + 1.5 * iqr

    rata_rata = grup["nilai"].mean()
    standar_deviasi = grup["nilai"].std()

    for _, baris in grup.iterrows():

        nilai = baris["nilai"]

        # Pemeriksaan IQR
        anomali_iqr = (
            nilai < batas_bawah or nilai > batas_atas
        )

        # Pemeriksaan Z-score
        if standar_deviasi != 0:
            z_score = (nilai - rata_rata) / standar_deviasi
        else:
            z_score = 0

        anomali_z = abs(z_score) > 3

        if anomali_iqr or anomali_z:

            alasan = []

            if anomali_iqr:
                alasan.append("Di luar batas IQR")

            if anomali_z:
                alasan.append("Z-score lebih dari 3")

            hasil.append({
                "wilayah": wilayah,
                "tahun": int(baris["tahun"]),
                "nilai": nilai,
                "z_score": z_score,
                "batas_bawah_IQR": batas_bawah,
                "batas_atas_IQR": batas_atas,
                "metode": " dan ".join(alasan)
            })

# Membuat tabel calon anomali
kolom = [
    "wilayah", "tahun", "nilai", "z_score",
    "batas_bawah_IQR", "batas_atas_IQR", "metode"
]

anomali = pd.DataFrame(hasil, columns=kolom)

anomali.to_csv(
    "reports/calon_anomali_var87.csv",
    index=False
)

# =====================================
# 3. MENAMPILKAN HASIL
# =====================================

print("=== HASIL DETEKSI ANOMALI VAR87 ===")
print("Jumlah provinsi diperiksa:", wilayah_diperiksa)
print("Provinsi dengan data kurang dari 8:", wilayah_tidak_diperiksa)
print("Jumlah calon anomali:", len(anomali))

print("\n=== DAFTAR CALON ANOMALI ===")

if len(anomali) > 0:
    print(anomali.round(2).to_string(index=False))
else:
    print("Tidak ditemukan calon anomali.")

print("\nFile boxplot tersimpan:")
print("reports/gambar/boxplot_var87.png")

print("\nFile calon anomali tersimpan:")
print("reports/calon_anomali_var87.csv")
