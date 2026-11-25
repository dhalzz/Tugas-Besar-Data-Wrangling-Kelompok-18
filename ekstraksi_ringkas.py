from collections import OrderedDict
from pathlib import PurePosixPath
import pandas as pd
from src import ekstraksi

mentah = ekstraksi.jalankan()

# kelompokkan per berkas (bagian sebelum "::")
kelompok = OrderedDict()
for kunci, df in mentah.items():
    berkas = kunci.split("::")[0]
    kelompok.setdefault(berkas, []).append(df)

# satu DataFrame per berkas; seri dalam satu berkas digabung
hasil = OrderedDict()
for berkas, daftar in kelompok.items():
    p = PurePosixPath(berkas.replace("\\", "/"))
    nama = f"{p.parent.name}_{p.stem}" if p.suffix.lower() == ".csv" else p.stem
    hasil[nama] = daftar[0] if len(daftar) == 1 else pd.concat(daftar, ignore_index=True)

print("=" * 50)
print("EKSTRAKSI SELESAI")
print("=" * 50)
print("Jumlah DataFrame:", len(hasil))
for nama, df in hasil.items():
    print(f"{nama}: {df.shape[0]} baris, {df.shape[1]} kolom")
print("Jumlah tabel:", len(hasil))
