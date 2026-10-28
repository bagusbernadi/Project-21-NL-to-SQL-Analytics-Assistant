"""03: Validasi golden set: komposisi (30 pertanyaan, 5 tipe), SQL referensi dijalankan di DuckDB dan dicek silang dengan hitungan pandas independen.

Hasil: results/2-analysis/golden_composition.csv, golden_reference.csv (hasil SQL referensi), crosscheck.csv (SQL vs pandas).
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
import numpy as np
import pandas as pd
import yaml
import assistant_lib as A
import common as CM

gold = yaml.safe_load((CM.EVAL / "golden_set.yaml").read_text(encoding="utf-8"))
G = pd.DataFrame(gold)
comp = G.groupby("type").agg(pertanyaan=("question_id", "size"), indonesia=("language", lambda s: int((s == "id").sum())), inggris=("language", lambda s: int((s == "en").sum()))).reset_index()
comp = comp.set_index("type").loc[["agregasi", "filter tanggal", "join", "definisi KPI", "ambigu"]].reset_index()
comp.to_csv(CM.RES2 / "golden_composition.csv", index=False)

p = pd.read_csv(CM.SIM / "production_daily.csv", parse_dates=["date"]); d = pd.read_csv(CM.SIM / "defect_log.csv", parse_dates=["date"])
dd = pd.read_csv(CM.SIM / "dim_defect.csv"); ds = pd.read_csv(CM.SIM / "dim_station.csv")
D = lambda s: pd.Timestamp(s)
fr = lambda **k: pd.DataFrame(k)


def fpy(x):
    return x.ok_first_pass.sum() / x.input_qty.sum()


def rty(x):
    return float(np.prod([fpy(g) for _, g in x.groupby("station")]))


dj = d.merge(dd[["defect_code", "defect_name", "category"]], on="defect_code")
PD = {
    "G01": lambda: fr(v=[p[p.station == "Engine Assembly"].input_qty.sum()]), "G02": lambda: fr(v=[p[p.station == "Frame Painting"].ng_qty.sum()]),
    "G03": lambda: fr(v=[p[p.station == "Final Inspection"].ok_first_pass.sum()]), "G04": lambda: fr(v=[p[p.model == "Sport 150"].input_qty.mean()]),
    "G05": lambda: p.groupby("station").ng_qty.sum().reset_index(), "G06": lambda: d.groupby("model").qty.sum().reset_index(),
    "G07": lambda: p.groupby("station").ng_qty.sum().sort_values(ascending=False, kind="stable").head(1).reset_index(), "G08": lambda: fr(v=[p.date.nunique()]),
    "G09": lambda: fr(v=[p[(p.station == "Engine Assembly") & (p.date >= D("2026-06-08")) & (p.date <= D("2026-06-14"))].ng_qty.sum()]),
    "G10": lambda: fr(v=[p[(p.station == "Packing") & (p.date.dt.month == 5)].input_qty.sum()]), "G11": lambda: fr(v=[p[(p.station == "Frame Welding") & (p.date.dt.month == 4)].ng_qty.sum()]),
    "G12": lambda: fr(v=[d[d.date == D("2026-04-15")].qty.sum()]), "G13": lambda: fr(v=[p[(p["shift"] == "Shift 2") & (p.date >= D("2026-05-01")) & (p.date <= D("2026-05-15"))].ng_qty.sum()]),
    "G14": lambda: fr(v=[p[(p.date.dt.month == 6) & (p.date <= D("2026-06-17"))].ng_qty.sum()]), "G15": lambda: fr(v=[p[(p.station == "Wheel & Suspension") & (p.date.dt.month == 5)].input_qty.sum()]),
    "G16": lambda: fr(v=[dj[dj.category == "Las"].qty.sum()]), "G17": lambda: dj.groupby("defect_name").qty.sum().sort_values(ascending=False, kind="stable").head(1).reset_index(),
    "G18": lambda: dj[dj.station == "Frame Painting"].groupby("defect_name").qty.sum().reset_index(), "G19": lambda: fr(v=[dj[(dj.category == "Cat") & (dj.model == "Sport 150")].qty.sum()]),
    "G20": lambda: dj[dj.category == "Kelistrikan"].groupby("station").qty.sum().reset_index(), "G21": lambda: p.groupby("station").ng_qty.sum().reset_index(),
    "G22": lambda: fr(v=[fpy(p[p.station == "Engine Assembly"])]), "G23": lambda: p.groupby("station").apply(fpy, include_groups=False).sort_values(kind="stable").head(1).reset_index(),
    "G24": lambda: p.groupby("model").apply(lambda x: x.ng_qty.sum() / x.input_qty.sum(), include_groups=False).reset_index(), "G25": lambda: fr(v=[rty(p[p.model == "Bebek 125"])]),
    "G26": lambda: fr(v=[d[d.station == "Body Panel Assembly"].qty.sum() * 1000 / p[p.station == "Body Panel Assembly"].input_qty.sum()]), "G27": lambda: fr(v=[rty(p)])}
con = A.open_readonly()
cx, ref_rows = [], []
for q in gold:
    if not q["reference_sql"]:
        continue
    got = con.execute(q["reference_sql"]).df()
    exp = PD[q["question_id"]]()
    cx.append(dict(cek="SQL referensi vs pandas", item=q["question_id"], dibandingkan=1, cocok=int(A.same_result(got.reset_index(drop=True), exp.reset_index(drop=True)))))
    ref_rows.append(dict(question_id=q["question_id"], baris=len(got), nilai=" | ".join(str(round(v, 6) if isinstance(v, float) else v) for v in got.iloc[0].tolist())))
pd.DataFrame(ref_rows).to_csv(CM.RES2 / "golden_reference.csv", index=False)
# view KPI vs SQL manual (dasar cek silang pertanyaan inti, Q12)
v = con.execute("SELECT station, fpy FROM v_kpi_station ORDER BY station").df()
m = p.groupby("station").apply(fpy, include_groups=False).reset_index(name="fpy").sort_values("station")
cx.append(dict(cek="view v_kpi_station vs pandas", item="fpy per stasiun", dibandingkan=len(v), cocok=int(np.isclose(v.fpy.values, m.fpy.values, atol=1e-12).sum())))
v = con.execute("SELECT model, rty FROM v_rty_model ORDER BY model").df()
cx.append(dict(cek="view v_rty_model vs pandas", item="rty per model", dibandingkan=len(v), cocok=int(sum(np.isclose(r.rty, rty(p[p.model == r.model]), atol=1e-12) for r in v.itertuples()))))
v = con.execute("SELECT week_start, ng_rate FROM v_trend_week ORDER BY week_start").df()
w = p.groupby(p.date.dt.to_period("W-SUN").dt.start_time).apply(lambda x: x.ng_qty.sum() / x.input_qty.sum(), include_groups=False)
cx.append(dict(cek="view v_trend_week vs pandas", item="ng rate mingguan", dibandingkan=len(v), cocok=int(np.isclose(v.ng_rate.values, w.values, atol=1e-12).sum())))
v = con.execute("SELECT defect_name, qty FROM v_pareto_defect ORDER BY defect_name").df()
w = dj.groupby("defect_name").qty.sum().reset_index().sort_values("defect_name")
cx.append(dict(cek="view v_pareto_defect vs pandas", item="defect per nama", dibandingkan=len(v), cocok=int((v.qty.values == w.qty.values).sum())))
cx = pd.DataFrame(cx)
cx.to_csv(CM.RES2 / "crosscheck.csv", index=False)
print(comp.to_string(index=False)); print(cx.groupby("cek").agg(n=("dibandingkan", "sum"), cocok=("cocok", "sum")))
assert (cx.dibandingkan == cx.cocok).all(), "cek silang gagal"
