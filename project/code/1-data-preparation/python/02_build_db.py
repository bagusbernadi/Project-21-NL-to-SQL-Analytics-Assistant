"""02: Bangun production.duckdb (4 tabel produksi + 5 view KPI) dari CSV simulasi. Database ini dibuka read-only oleh asisten.

Data simulasi bersih (tanpa data kotor); view tetap menyaring baris tidak valid. Hasil: results/1-data-preparation/db_tables.csv.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
import duckdb
import pandas as pd
import common as CM

CM.DB_PATH.unlink(missing_ok=True)
con = duckdb.connect(str(CM.DB_PATH))
con.execute((CM.SQL_DIR1 / "schema.sql").read_text(encoding="utf-8"))
for t in ("dim_station", "dim_defect", "production_daily", "defect_log"):
    con.execute(f"INSERT INTO {t} SELECT * FROM read_csv('{(CM.SIM / (t + '.csv')).as_posix()}', header=true)")
con.execute((CM.SQL_DIR1 / "views.sql").read_text(encoding="utf-8"))
rows = [(t, con.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]) for t in ("dim_station", "dim_defect", "production_daily", "defect_log", "v_production", "v_kpi_station", "v_pareto_defect", "v_trend_week", "v_rty_model")]
out = pd.DataFrame(rows, columns=["objek", "baris"])
out.to_csv(CM.RES1 / "db_tables.csv", index=False)
print(out.to_string(index=False))
assert out.set_index("objek").baris["v_production"] == out.set_index("objek").baris["production_daily"], "ada baris produksi tidak valid"
con.close()
