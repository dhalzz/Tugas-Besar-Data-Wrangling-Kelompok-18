from pathlib import PurePosixPath
from src import ekstraksi

h = ekstraksi.jalankan()

berkas = {k.split("::")[0] for k in h}
ringkasan = {
    "berkas_dibaca": len(berkas),
    "baris_mentah": int(sum(len(df) for df in h.values())),
    "format": len({PurePosixPath(b.replace("\\", "/")).suffix.lower() for b in berkas}),
}

print("Jumlah tabel:", len(h))
print("Ringkasan:", ringkasan)
for k, df in h.items():
    print(f"{k} -> {len(df)} baris")
