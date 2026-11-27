import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path

# =====================================================
# 1. MEMBACA DAN VALIDASI DATA
# =====================================================

df = pd.read_csv("data/raw/bps/var87_long.csv")

# Memisahkan data provinsi dan nasional
df = df[df["wilayah"] != "INDONESIA"].copy()

# Mengubah tipe data
df["tahun"] = pd.to_numeric(df["tahun"], errors="coerce")
df["nilai"] = pd.to_numeric(df["nilai"], errors="coerce")

# Menghapus data yang tidak memiliki tahun atau nilai
df = df.dropna(subset=["tahun", "nilai"])

# Mengurutkan data
df = df.sort_values(["wilayah", "tahun"]).reset_index(drop=True)

# Validasi duplikasi wilayah-tahun
duplikat = df.duplicated(subset=["wilayah", "tahun"])

print("=== VALIDASI DATA VAR87 ===")
print("Jumlah data:", len(df))
print("Jumlah wilayah:", df["wilayah"].nunique())
print("Jumlah data duplikat wilayah-tahun:", duplikat.sum())
print("Jumlah missing tahun:", df["tahun"].isna().sum())
print("Jumlah missing nilai:", df["nilai"].isna().sum())

# Membuat folder penyimpanan
Path("reports/gambar").mkdir(
    parents=True,
    exist_ok=True
)

Path("reports").mkdir(
    parents=True,
    exist_ok=True
)

# =====================================================
# 2. MEMBUAT BOXPLOT
# =====================================================

plt.figure(figsize=(18, 8))

df.boxplot(
    column="nilai",
    by="wilayah",
    rot=90,
    grid=False
)

plt.title(
    "Boxplot Persentase Rumah Tangga "
    "dengan Penerangan Utama PLN"
)

plt.suptitle("")
plt.xlabel("Provinsi")
plt.ylabel("Persentase (%)")
plt.tight_layout()

plt.savefig(
    "reports/gambar/boxplot_var87.png",
    dpi=300,
    bbox_inches="tight"
)

plt.close()

# =====================================================
# 3. DETEKSI CALON ANOMALI IQR DAN Z-SCORE
# =====================================================

hasil = []

wilayah_diperiksa = 0
wilayah_tidak_diperiksa = []

for wilayah, grup in df.groupby("wilayah"):

    grup = grup.sort_values("tahun").copy()

    # Menghindari deteksi pada kelompok dengan data terlalu sedikit
    if len(grup) < 8:
        wilayah_tidak_diperiksa.append(wilayah)
        continue

    wilayah_diperiksa += 1

    # Statistik IQR
    q1 = grup["nilai"].quantile(0.25)
    q3 = grup["nilai"].quantile(0.75)
    iqr = q3 - q1

    batas_bawah = q1 - 1.5 * iqr
    batas_atas = q3 + 1.5 * iqr

    # Statistik Z-Score
    rata_rata = grup["nilai"].mean()
    standar_deviasi = grup["nilai"].std()

    # Konteks tahun sebelumnya dan berikutnya
    grup["nilai_sebelumnya"] = grup["nilai"].shift(1)
    grup["tahun_sebelumnya"] = grup["tahun"].shift(1)

    grup["nilai_berikutnya"] = grup["nilai"].shift(-1)
    grup["tahun_berikutnya"] = grup["tahun"].shift(-1)

    grup["perubahan_sebelumnya"] = (
        grup["nilai"] - grup["nilai_sebelumnya"]
    )

    # Memeriksa setiap observasi
    for _, baris in grup.iterrows():

        nilai = baris["nilai"]

        # Deteksi IQR
        anomali_iqr = (
            nilai < batas_bawah
            or nilai > batas_atas
        )

        # Deteksi Z-Score
        if standar_deviasi != 0:
            z_score = (
                nilai - rata_rata
            ) / standar_deviasi
        else:
            z_score = 0

        anomali_z = abs(z_score) > 3

        # Hanya menyimpan nilai yang terdeteksi
        if anomali_iqr or anomali_z:

            metode = []

            if anomali_iqr:
                metode.append("IQR")

            if anomali_z:
                metode.append("Z-Score")

            alasan = []

            if anomali_iqr:
                alasan.append(
                    "Nilai berada di luar batas IQR"
                )

            if anomali_z:
                alasan.append(
                    "Nilai memiliki Z-Score lebih dari 3 "
                    "atau kurang dari -3"
                )

            # Konteks perubahan tahun sebelumnya
            if pd.notna(baris["nilai_sebelumnya"]):

                perubahan = baris["perubahan_sebelumnya"]

                if perubahan > 0:
                    konteks = (
                        f"Nilai meningkat {perubahan:.2f} "
                        "poin dibanding tahun sebelumnya"
                    )

                elif perubahan < 0:
                    konteks = (
                        f"Nilai menurun {abs(perubahan):.2f} "
                        "poin dibanding tahun sebelumnya"
                    )

                else:
                    konteks = (
                        "Nilai tidak berubah "
                        "dibanding tahun sebelumnya"
                    )

            else:
                konteks = (
                    "Tidak tersedia data tahun sebelumnya"
                )

            hasil.append({
                "wilayah": wilayah,
                "tahun": int(baris["tahun"]),
                "nilai": nilai,
                "z_score": z_score,
                "q1": q1,
                "q3": q3,
                "iqr": iqr,
                "batas_bawah_IQR": batas_bawah,
                "batas_atas_IQR": batas_atas,
                "metode": " dan ".join(metode),
                "alasan": "; ".join(alasan),
                "nilai_sebelumnya": baris["nilai_sebelumnya"],
                "tahun_sebelumnya": baris["tahun_sebelumnya"],
                "nilai_berikutnya": baris["nilai_berikutnya"],
                "tahun_berikutnya": baris["tahun_berikutnya"],
                "perubahan_sebelumnya": (
                    baris["perubahan_sebelumnya"]
                ),
                "konteks_perubahan": konteks
            })

# =====================================================
# 4. MENYIMPAN HASIL CALON ANOMALI
# =====================================================

kolom = [
    "wilayah",
    "tahun",
    "nilai",
    "z_score",
    "q1",
    "q3",
    "iqr",
    "batas_bawah_IQR",
    "batas_atas_IQR",
    "metode",
    "alasan",
    "nilai_sebelumnya",
    "tahun_sebelumnya",
    "nilai_berikutnya",
    "tahun_berikutnya",
    "perubahan_sebelumnya",
    "konteks_perubahan"
]

anomali = pd.DataFrame(
    hasil,
    columns=kolom
)

anomali = anomali.sort_values(
    ["wilayah", "tahun"]
)

anomali.to_csv(
    "reports/calon_anomali_var87.csv",
    index=False
)

# =====================================================
# 5. MENAMPILKAN HASIL
# =====================================================

print("\n=== HASIL DETEKSI ANOMALI VAR87 ===")

print(
    "Jumlah wilayah diperiksa:",
    wilayah_diperiksa
)

print(
    "Wilayah dengan data kurang dari 8:",
    wilayah_tidak_diperiksa
)

print(
    "Jumlah calon anomali:",
    len(anomali)
)

print("\n=== DAFTAR CALON ANOMALI ===")

if len(anomali) > 0:

    print(
        anomali.round(2).to_string(
            index=False
        )
    )

else:

    print("Tidak ditemukan calon anomali.")

print("\nFile boxplot tersimpan:")
print("reports/gambar/boxplot_var87.png")

print("\nFile calon anomali tersimpan:")
print("reports/calon_anomali_var87.csv")