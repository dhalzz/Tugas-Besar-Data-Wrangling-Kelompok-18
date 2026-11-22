"""DDL tabel SQL untuk penyimpanan Silver."""

DDL_SILVER = """
CREATE TABLE IF NOT EXISTS silver_grid (
    jenis_grid TEXT NOT NULL,
    wilayah_kode INTEGER NOT NULL,
    tahun INTEGER NOT NULL,
    rincian TEXT NOT NULL,
    nama_provinsi TEXT,
    periode TEXT,
    seri_kode TEXT NOT NULL,
    nilai_terisi REAL,
    nilai REAL,
    sebelum_provinsi_ada INTEGER,
    tahun_tidak_diterbitkan INTEGER,
    sel_kosong_dalam_terbitan INTEGER,
    missing_sejati INTEGER,

    PRIMARY KEY (
        jenis_grid,
        wilayah_kode,
        tahun,
        rincian,
        seri_kode
    )
);
"""