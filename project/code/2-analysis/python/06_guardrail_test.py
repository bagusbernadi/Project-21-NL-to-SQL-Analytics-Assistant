"""06: Uji guardrail (Q5, Q6). Red-team set 15 percobaan SQL berbahaya harus tertolak; data tidak boleh berubah.

Dua lapis: (1) guardrail kode (SELECT tunggal, tabel dalam daftar, tanpa fungsi file); (2) database dibuka read-only. Lapis 2 diuji dengan
menjalankan percobaan langsung ke koneksi read-only tanpa guardrail. Integritas: jumlah baris dan checksum tabel sebelum dan sesudah.
Uji beban: query berat (timeout) dan SELECT tanpa LIMIT (LIMIT otomatis). Hasil: guardrail_redteam.csv, guardrail_load.csv, guardrail_integrity.csv, guardrail_summary.csv, query_limit.csv.
"""
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
import duckdb
import pandas as pd
import yaml
import assistant_lib as A
import common as CM

rt = yaml.safe_load((CM.EVAL / "redteam_set.yaml").read_text(encoding="utf-8"))
TABLES = ["production_daily", "defect_log", "dim_defect", "dim_station"]


def snap():
    con = A.open_readonly()
    try:
        return {t: tuple(con.execute(f"SELECT COUNT(*), SUM(hash(t)) FROM {t} t").fetchone()) for t in TABLES}
    finally:
        con.close()


before = snap()
rows = []
for r in rt["redteam"]:
    c = A.check_sql(r["sql"])
    res = {}
    for nama, hard in (("read_only_saja", False), ("read_only_akses_file_mati", True)):     # lapis 2: tanpa guardrail
        probe = A.open_readonly(hard)
        try:
            probe.execute(r["sql"]).fetchall()
            res[nama] = "dijalankan"
        except Exception as e:
            res[nama] = "ditolak database: " + type(e).__name__
        finally:
            probe.close()
    rows.append(dict(attempt_id=r["attempt_id"], type=r["type"], sql=r["sql"], ditolak_guardrail=int(not c["ok"]), alasan=c["reason"], **res))
Path("/tmp/keluar.csv").unlink(missing_ok=True)                    # R08 menulis file bila dijalankan tanpa guardrail
R = pd.DataFrame(rows)
R.to_csv(CM.RES2 / "guardrail_redteam.csv", index=False)
after = snap()
integ = pd.DataFrame([dict(tabel=t, baris_sebelum=before[t][0], baris_sesudah=after[t][0], checksum_sama=int(before[t][1] == after[t][1])) for t in TABLES])
integ.to_csv(CM.RES2 / "guardrail_integrity.csv", index=False)
L = []
con = A.open_readonly()
for r in rt["load"]:
    c = A.check_sql(r["sql"])
    df, st, msg = A.execute(con, c["sql"]) if c["ok"] else (None, "blocked", c["reason"])
    L.append(dict(attempt_id=r["attempt_id"], sql=r["sql"], diizinkan=int(c["ok"]), limit_otomatis=int(c["auto_limit"]), status_eksekusi=st, baris=0 if df is None else len(df), terpotong=int(df is not None and len(df) >= CM.AUTO_LIMIT)))
pd.DataFrame(L).to_csv(CM.RES2 / "guardrail_load.csv", index=False)
E = pd.read_csv(CM.RES2 / "eval_results.csv")
ex = E[E.status.isin(["ok", "error", "timeout"])]
ql = pd.DataFrame([dict(config=c, query_dijalankan=len(g), limit_otomatis=int(g.auto_limit.sum()), terpotong=int(g.truncated.sum()), timeout=int((g.status == "timeout").sum())) for c, g in ex.groupby("config")])
ql.to_csv(CM.RES2 / "query_limit.csv", index=False)
n, k = len(R), int(R.ditolak_guardrail.sum())
z = 1.959964; p = k / n; d = 1 + z * z / n; cc = (p + z * z / (2 * n)) / d; h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
pd.DataFrame([dict(percobaan=n, ditolak_guardrail=k, block_rate=p, ci_low=max(0.0, cc - h), ci_high=min(1.0, cc + h), ditolak_read_only_saja=int(R.read_only_saja.str.startswith("ditolak").sum()), ditolak_akses_file_mati=int(R.read_only_akses_file_mati.str.startswith("ditolak").sum()),
                   tabel_berubah=int((integ.checksum_sama == 0).sum()))]).to_csv(CM.RES2 / "guardrail_summary.csv", index=False, float_format="%.10g")
print(R[["attempt_id", "ditolak_guardrail", "alasan", "read_only_saja", "read_only_akses_file_mati"]].to_string(index=False)); print(integ); print(pd.DataFrame(L)); print(ql)
