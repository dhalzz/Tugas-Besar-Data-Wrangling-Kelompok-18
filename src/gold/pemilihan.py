
"""Aturan pemilihan data untuk tahap Gold."""

import re

import pandas as pd


KOLOM_KUNCI = [
    "wilayah_kode",
    "periode",
    "seri_kode",
    "rincian",
]

PEMETAAN_BAHAN_BAKAR = {
    "Listrik": "bersih",
    "Gas/Elpiji": "bersih",
    "Kayu": "tidak_bersih",
    "Arang/Briket": "tidak_bersih",
    "Minyak Tanah": "tidak_bersih",
    "Lainnya": "tidak_diklasifikasikan",
    "Jumlah": "dikecualikan",
}


ALIAS_PROVINSI = {
    "KEP. RIAU": "KEPULAUAN RIAU",
}


def normalisasi_wilayah(nilai):
    """Samakan format nama provinsi untuk pencocokan."""
    nama = str(nilai).strip().upper()
    return ALIAS_PROVINSI.get(nama, nama)


def tanggal_snapshot(berkas_raw):
    """Ambil tanggal snapshot dari jalur berkas raw."""
    cocok = re.search(r"(\d{4}-\d{2}-\d{2})", str(berkas_raw))

    if not cocok:
        raise ValueError(
            f"Tanggal snapshot tidak ditemukan: {berkas_raw}"
        )

    return pd.to_datetime(cocok.group(1))


def pilih_snapshot(df):
    """Pilih snapshot terbaru untuk setiap kunci data."""
    hasil = df.copy()

    hasil["_tanggal_snapshot"] = hasil["_berkas_raw"].apply(
        tanggal_snapshot
    )

    hasil = hasil.sort_values(
        by=["_tanggal_snapshot", "_berkas_raw"],
        ascending=[False, False],
    )

    hasil = hasil.drop_duplicates(
        subset=KOLOM_KUNCI,
        keep="first",
    )

    return hasil.drop(columns="_tanggal_snapshot")


def validasi_periode_tahunan(df):
    """Pastikan Gold hanya menggunakan periode tahunan."""
    bukan_tahunan = df["jenis_periode"] != "tahun"

    if bukan_tahunan.any():
        contoh = (
            df.loc[bukan_tahunan, "periode"]
            .drop_duplicates()
            .tolist()[:5]
        )

        raise ValueError(
            "Gold hanya menerima periode tahunan. "
            f"Contoh periode tidak didukung: {contoh}"
        )

    return df.copy()


def pastikan_unik(df):
    """Pastikan satu baris per provinsi, periode, seri, dan rincian."""
    duplikat = df.duplicated(
        subset=KOLOM_KUNCI,
        keep=False,
    )

    if duplikat.any():
        contoh = df.loc[duplikat, KOLOM_KUNCI].head(10)

        raise ValueError(
            "Masih ada kunci data yang duplikat:\n"
            f"{contoh.to_string(index=False)}"
        )

    return df


def hitung_baris_tidak_terpilih(jumlah_silver, jumlah_terpilih):
    """Hitung baris Silver yang tidak terpilih."""
    return jumlah_silver - jumlah_terpilih


def agregasi_bahan_bakar(df, grid):
    """Agregasikan bahan bakar dari grid lengkap untuk panel Gold."""

    aturan = {
        "bersih": ["Listrik", "Gas/Elpiji"],
        "tidak_bersih": ["Kayu", "Arang/Briket", "Minyak Tanah"],
    }

    hasil = []

    for kategori, rincian_wajib in aturan.items():
        bagian = grid[
            grid["rincian"].isin(rincian_wajib)
        ].copy()

        kunci = ["wilayah_kode", "nama_provinsi", "periode"]

        lebar = bagian.pivot(
            index=kunci,
            columns="rincian",
            values="nilai",
        ).reindex(columns=rincian_wajib)

        nilai_agregat = lebar.sum(
            axis=1,
            min_count=len(rincian_wajib),
        )

        tabel = nilai_agregat.rename("nilai").reset_index()
        tabel = tabel.rename(columns={"nama_provinsi": "nama_wilayah"})

        tabel["indikator"] = f"bahan_bakar_{kategori}"
        tabel["kategori"] = kategori
        tabel["satuan"] = "%"
        tabel["jenis_periode"] = "tahun"

        ringkasan = (
            bagian.groupby(["wilayah_kode", "periode"])
            .agg(
                sebelum_provinsi_ada=("sebelum_provinsi_ada", "any"),
                tahun_tidak_diterbitkan=("tahun_tidak_diterbitkan", "any"),
                sel_kosong_dalam_terbitan=("sel_kosong_dalam_terbitan", "any"),
                missing_sejati=("missing_sejati", "any"),
            )
            .reset_index()
        )

        rincian_missing = (
            bagian[bagian["missing_sejati"]]
            .groupby(["wilayah_kode", "periode"])["rincian"]
            .agg(lambda x: ", ".join(sorted(set(x))))
            .reset_index(name="rincian_missing")
        )

        tabel = tabel.merge(
            ringkasan,
            on=["wilayah_kode", "periode"],
            how="left",
        )

        tabel = tabel.merge(
            rincian_missing,
            on=["wilayah_kode", "periode"],
            how="left",
        )

        tabel["rincian_missing"] = tabel["rincian_missing"].fillna("")

        hasil.append(tabel)

    return pd.concat(hasil, ignore_index=True)


def tandai_outlier(gold, root):
    """Bawa kandidat outlier Sprint 1 ke tabel Gold."""
    hasil = gold.copy()

    hasil["wilayah_normal"] = hasil["nama_provinsi"].apply(
        normalisasi_wilayah
    )

    listrik = pd.read_csv(
        root / "reports" / "calon_anomali_var87.csv"
    )
    listrik["wilayah_normal"] = listrik["wilayah"].apply(
        normalisasi_wilayah
    )

    kunci_listrik = set(
        zip(
            listrik["wilayah_normal"],
            listrik["tahun"].astype(int),
        )
    )

    bahan = pd.read_csv(
        root / "reports" / "calon_anomali_bahan_bakar.csv"
    )
    bahan["wilayah_normal"] = bahan["wilayah"].apply(
        normalisasi_wilayah
    )

    kunci_bahan = set(
        zip(
            bahan["wilayah_normal"],
            bahan["tahun"].astype(int),
            bahan["bahan_bakar"],
        )
    )

    def cek_outlier(baris):
        wilayah = baris["wilayah_normal"]
        tahun = int(baris["periode"])

        if baris["indikator"] == "elektrifikasi":
            return (wilayah, tahun) in kunci_listrik

        if baris["indikator"] == "bahan_bakar_bersih":
            rincian = ["Listrik", "Gas/Elpiji"]
        elif baris["indikator"] == "bahan_bakar_tidak_bersih":
            rincian = [
                "Kayu",
                "Arang/Briket",
                "Minyak Tanah",
            ]
        elif baris["indikator"] == "bahan_bakar_lainnya":
            rincian = ["Lainnya"]
        else:
            return False

        return any(
            (wilayah, tahun, nama) in kunci_bahan
            for nama in rincian
        )

    hasil["outlier"] = hasil.apply(cek_outlier, axis=1)
    hasil = hasil.drop(columns="wilayah_normal")

    return hasil
