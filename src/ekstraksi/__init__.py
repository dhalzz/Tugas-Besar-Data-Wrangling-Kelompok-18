"""Tahap 1 — Ekstraksi.

Membaca berkas mentah dari data/raw/ menjadi DataFrame.

Data tidak dibersihkan pada tahap ini.
Setiap baris dilengkapi:
- _berkas_raw
- _sha256_raw
"""

from pathlib import Path
import hashlib
import json

import pandas as pd

# ============================================================
# 1. MENENTUKAN LOKASI DATA
# ============================================================

ROOT = Path(__file__).resolve().parents[2]

RAW_DIR = ROOT / "data" / "raw"

# ============================================================
# 2. MENGHITUNG SHA-256 BERKAS
# ============================================================

def hitung_sha256(path: Path) -> str:
    """
    Menghitung SHA-256 dari berkas mentah.

    File dibaca dalam bentuk binary agar hash mencerminkan
    isi asli berkas.
    """

    hash_obj = hashlib.sha256()

    with open(path, "rb") as file:
        for chunk in iter(lambda: file.read(8192), b""):
            hash_obj.update(chunk)

    return hash_obj.hexdigest()

# ============================================================
# 3. MEMBACA CSV
# ============================================================

def baca_csv(path: Path) -> pd.DataFrame:
    """
    Membaca file CSV tanpa melakukan cleaning data.
    """

    try:
        df = pd.read_csv(
            path,
            dtype=str,
            sep=None,
            engine="python",
            encoding="utf-8-sig",
        )

    except Exception:
        df = pd.read_csv(
            path,
            dtype=str,
            encoding="latin-1",
        )

    return df

# ============================================================
# 4. MERATAKAN JSON
# ============================================================

def flatten_json(data):
    """
    Mengubah struktur JSON menjadi DataFrame.

    Menangani:
    - JSON berupa list
    - JSON berupa dictionary
    - Dictionary yang berisi list
    - JSON nested
    """

    # --------------------------------------------------------
    # JSON berupa list
    # --------------------------------------------------------

    if isinstance(data, list):

        if len(data) == 0:
            return pd.DataFrame()

        if all(isinstance(item, dict) for item in data):
            return pd.json_normalize(
                data,
                sep="_",
            )

        return pd.DataFrame({
            "data": data
        })

    # --------------------------------------------------------
    # JSON berupa dictionary
    # --------------------------------------------------------

    if isinstance(data, dict):

        # Mencari list di dalam dictionary
        for key, value in data.items():

            if isinstance(value, list):

                if len(value) == 0:
                    continue

                # List berisi dictionary
                if all(isinstance(item, dict) for item in value):

                    df = pd.json_normalize(
                        value,
                        sep="_",
                    )

                    # Menambahkan informasi dari parent JSON
                    for parent_key, parent_value in data.items():

                        if parent_key == key:
                            continue

                        if not isinstance(
                            parent_value,
                            (dict, list)
                        ):
                            df[parent_key] = parent_value

                    return df

                # List biasa
                return pd.DataFrame({
                    key: value
                })

        # Jika tidak terdapat list
        return pd.json_normalize(
            data,
            sep="_",
        )

    # --------------------------------------------------------
    # JSON berupa nilai tunggal
    # --------------------------------------------------------

    return pd.DataFrame({
        "data": [data]
    })

# ============================================================
# 5. MEMBACA JSON
# ============================================================

def baca_json(path: Path) -> pd.DataFrame:
    """
    Membaca JSON dan mengubahnya menjadi DataFrame.
    """

    with open(
        path,
        "r",
        encoding="utf-8"
    ) as file:

        data = json.load(file)

    df = flatten_json(data)

    return df

# ============================================================
# 6. MEMBACA BERKAS BERDASARKAN FORMAT
# ============================================================

def baca_berkas(path: Path) -> pd.DataFrame:
    """
    Membaca berkas berdasarkan ekstensi.
    """

    ekstensi = path.suffix.lower()

    # CSV
    if ekstensi == ".csv":

        return baca_csv(path)

    # JSON
    elif ekstensi == ".json":

        return baca_json(path)

    # Format lain belum didukung
    else:

        print(
            f"[SKIP] Format belum didukung: {path.name}"
        )

        return pd.DataFrame()

# ============================================================
# 7. FUNGSI UTAMA EKSTRAKSI
# ============================================================

def jalankan():
    """
    Mengembalikan dictionary:

    {
        nama_sumber: DataFrame mentah
    }
    """

    hasil = {}

    # --------------------------------------------------------
    # Memastikan folder raw tersedia
    # --------------------------------------------------------

    if not RAW_DIR.exists():

        raise FileNotFoundError(
            f"Folder data/raw tidak ditemukan: {RAW_DIR}"
        )

    # --------------------------------------------------------
    # Mengambil seluruh file dalam data/raw
    # --------------------------------------------------------

    daftar_berkas = sorted(
        path
        for path in RAW_DIR.rglob("*")
        if path.is_file()
        and path.name != "MANIFEST.csv"
    )

    print(
        f"Jumlah berkas raw ditemukan: "
        f"{len(daftar_berkas)}"
    )

    # --------------------------------------------------------
    # Membaca setiap berkas
    # --------------------------------------------------------

    for path in daftar_berkas:

        # Path relatif terhadap data/raw
        berkas_raw = path.relative_to(
            RAW_DIR
        ).as_posix()

        print(
            f"\nMembaca berkas: {berkas_raw}"
        )

        # Membaca data
        df = baca_berkas(path)

        # Jika format tidak didukung
        if df.empty:

            print(
                f"[INFO] Data kosong atau format tidak didukung: "
                f"{berkas_raw}"
            )

            continue

        # ----------------------------------------------------
        # Menambahkan lineage
        # ----------------------------------------------------

        df["_berkas_raw"] = berkas_raw

        df["_sha256_raw"] = hitung_sha256(path)

        # ----------------------------------------------------
        # Membuat nama sumber
        # ----------------------------------------------------

        nama_sumber = path.stem

        # Jika nama sumber sudah digunakan
        if nama_sumber in hasil:

            nama_sumber = (
                f"{path.parent.name}_{path.stem}"
            )

        # Menyimpan DataFrame
        hasil[nama_sumber] = df

        # ----------------------------------------------------
        # Informasi hasil pembacaan
        # ----------------------------------------------------

        print(
            f"[OK] {len(df)} baris "
            f"| {len(df.columns)} kolom"
        )

    # --------------------------------------------------------
    # Ringkasan
    # --------------------------------------------------------

    print("\n" + "=" * 50)
    print("EKSTRAKSI SELESAI")
    print("=" * 50)

    print(
        f"Jumlah DataFrame: {len(hasil)}"
    )

    for nama, df in hasil.items():

        print(
            f"{nama}: "
            f"{len(df)} baris, "
            f"{len(df.columns)} kolom"
        )

    return hasil