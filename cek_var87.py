import json

path = "data/raw/bps/2026-10-17/json/sdg7_listrik_pln.json"

with open(path, encoding="utf-8") as f:
    data = json.load(f)

total_nilai = 0
total_cocok = 0
tidak_cocok = []

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

                        total_nilai += 1

                        if key in obj["datacontent"]:
                            total_cocok += 1
                        else:
                            tidak_cocok.append(key)

print("Total kombinasi yang diperiksa:", total_nilai)
print("Kombinasi yang cocok:", total_cocok)
print("Kombinasi tanpa nilai:", len(tidak_cocok))
print("Contoh kombinasi tanpa nilai:", tidak_cocok[:10])
print("Total nilai dalam JSON:", sum(len(o["datacontent"]) for o in data))
