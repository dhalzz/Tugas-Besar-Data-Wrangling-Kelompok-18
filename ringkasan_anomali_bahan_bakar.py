
import pandas as pd

df = pd.read_csv("reports/calon_anomali_bahan_bakar.csv")

print("=== RINGKASAN CALON ANOMALI ===")
print("Total calon anomali:", len(df))

print("\n=== BERDASARKAN ALASAN ===")
print(df["alasan"].value_counts())

print("\n=== 15 NILAI TERTINGGI ===")
print(
    df.sort_values("nilai", ascending=False)
    .head(15)
    .to_string(index=False)
)

print("\n=== 15 NILAI TERENDAH ===")
print(
    df.sort_values("nilai", ascending=True)
    .head(15)
    .to_string(index=False)
)


print("\n=== CALON ANOMALI YANG TERDETEKSI KEDUA METODE ===")

anomali_keduanya = df[
    df["alasan"].str.contains("Z-score", na=False)
]

print(
    anomali_keduanya.sort_values(
        ["bahan_bakar", "wilayah", "tahun"]
    ).to_string(index=False)
)
