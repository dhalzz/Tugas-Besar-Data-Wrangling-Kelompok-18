import json
import pandas as pd

path = "data/raw/bps/2026-10-17/json/sdg7_listrik_pln.json"

with open(path, encoding="utf-8") as f:
    data = json.load(f)

hasil = []

for obj in data:
    for wilayah in obj["vervar"]:
        for var in obj["var"]:
            for turvar in obj["turvar"]:
                for tahun in obj["tahun"]:
                    for turtahun in obj["turtahun"]:

                        key = (
                            str(wilayah["val"])
                            + str(var["val"])
                            + str(turvar["val"])
                            + str(tahun["val"])
                            + str(turtahun["val"])
                        )

                        if key in obj["datacontent"]:
                            hasil.append({
                                "wilayah": wilayah["label"],
                                "tahun": tahun["label"],
                                "nilai": obj["datacontent"][key]
                            })

df = pd.DataFrame(hasil)

df["tahun"] = pd.to_numeric(df["tahun"], errors="coerce")
df["nilai"] = pd.to_numeric(df["nilai"], errors="coerce")

df = df.sort_values(["wilayah", "tahun"])

df.to_csv(
    "data/raw/bps/var87_long.csv",
    index=False,
    encoding="utf-8-sig"
)

print("HASIL EKSTRAKSI VAR87")
print("Jumlah baris:", len(df))
print("Jumlah wilayah:", df["wilayah"].nunique())
print("Rentang tahun:", df["tahun"].min(), "-", df["tahun"].max())
print("Jumlah nilai kosong:", df["nilai"].isna().sum())

print("\nContoh hasil:")
print(df.head(10).to_string(index=False))
