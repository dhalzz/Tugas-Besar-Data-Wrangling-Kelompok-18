"""DDL tabel SQLite berkunci primer dan tipe kolom eksplisit untuk Silver dan Gold."""

DDL_SILVER = """
CREATE TABLE silver (
    sumber TEXT NOT NULL,
    seri_kode TEXT NOT NULL,
    wilayah_kode INTEGER NOT NULL,
    nama_wilayah TEXT NOT NULL,
    periode TEXT NOT NULL,
    jenis_periode TEXT NOT NULL,
    rincian TEXT NOT NULL,
    nilai REAL NOT NULL,
    satuan TEXT NOT NULL,
    _berkas_raw TEXT NOT NULL,
    _sha256_raw TEXT NOT NULL,
    PRIMARY KEY (sumber, seri_kode, wilayah_kode, periode, rincian, _berkas_raw)
);
"""

DDL_GOLD_PANEL = """
CREATE TABLE gold_panel (
    wilayah_kode INTEGER NOT NULL,
    nama_provinsi TEXT NOT NULL,
    periode TEXT NOT NULL,
    indikator TEXT NOT NULL,
    nilai REAL,
    satuan TEXT NOT NULL,
    _lineage_silver TEXT,
    status_data TEXT NOT NULL,
    PRIMARY KEY (wilayah_kode, periode, indikator)
);
"""

DDL_GOLD_NASIONAL = """
CREATE TABLE gold_nasional (
    periode TEXT NOT NULL,
    seri_kode TEXT NOT NULL,
    rincian TEXT NOT NULL,
    nilai REAL NOT NULL,
    satuan TEXT NOT NULL,
    peran TEXT NOT NULL,
    pasangan_utama TEXT,
    asal_angka TEXT NOT NULL,
    sumber TEXT NOT NULL,
    keterangan TEXT,
    _berkas_raw TEXT NOT NULL,
    _sha256_raw TEXT NOT NULL,
    PRIMARY KEY (periode, seri_kode, rincian)
);
"""

DDL_GOLD_REKONSILIASI = """
CREATE TABLE gold_rekonsiliasi (
    pasangan TEXT NOT NULL,
    seri_utama TEXT NOT NULL,
    seri_pembanding TEXT NOT NULL,
    periode TEXT NOT NULL,
    nilai_utama REAL,
    nilai_pembanding REAL,
    selisih REAL,
    kategori_penjelasan TEXT,
    catatan TEXT NOT NULL,
    _berkas_raw_utama TEXT,
    _berkas_raw_pembanding TEXT,
    PRIMARY KEY (pasangan, periode)
);
"""

SEMUA_DDL = {
    "silver": DDL_SILVER,
    "gold_panel": DDL_GOLD_PANEL,
    "gold_nasional": DDL_GOLD_NASIONAL,
    "gold_rekonsiliasi": DDL_GOLD_REKONSILIASI,
}
