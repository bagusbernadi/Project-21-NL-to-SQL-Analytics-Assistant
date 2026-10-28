-- Tabel produksi (sama strukturnya dengan Project 3). Dibuat oleh 02_build_db.py dari CSV di data/sim/.
CREATE TABLE dim_station (station VARCHAR PRIMARY KEY, seq INTEGER NOT NULL);
CREATE TABLE dim_defect (defect_code VARCHAR PRIMARY KEY, defect_name VARCHAR NOT NULL, station VARCHAR NOT NULL, category VARCHAR NOT NULL);
CREATE TABLE production_daily (
    date DATE NOT NULL, shift VARCHAR NOT NULL, station VARCHAR NOT NULL, model VARCHAR NOT NULL, operator_id VARCHAR NOT NULL,
    input_qty INTEGER NOT NULL, ok_first_pass INTEGER NOT NULL, ng_qty INTEGER NOT NULL);
CREATE TABLE defect_log (
    date DATE NOT NULL, shift VARCHAR NOT NULL, station VARCHAR NOT NULL, model VARCHAR NOT NULL, defect_code VARCHAR NOT NULL, qty INTEGER NOT NULL);
