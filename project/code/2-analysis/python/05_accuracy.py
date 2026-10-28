"""05: Execution accuracy (Q1-Q4): per konfigurasi, tipe, bahasa, dengan CI Wilson; perbandingan konfigurasi berpasangan (uji McNemar eksak).

Hasil: accuracy_config.csv, accuracy_type.csv, accuracy_language.csv, config_compare.csv.
"""
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
import pandas as pd
from scipy import stats
import common as CM

E = pd.read_csv(CM.RES2 / "eval_results.csv")


def wilson(k, n, z=1.959964):
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return max(0.0, c - h), min(1.0, c + h)


def acc(g):
    k, n = int(g.is_correct.sum()), len(g)
    lo, hi = wilson(k, n)
    return pd.Series(dict(benar=k, n=n, akurasi=k / n, ci_low=lo, ci_high=hi))


a1 = E.groupby("config").apply(acc, include_groups=False).reset_index().set_index("config").loc[CM.CONFIGS].reset_index()
a1["target"] = CM.ACC_TARGET
a1["capai_target"] = (a1.akurasi >= CM.ACC_TARGET).astype(int)
a1["ci_bawah_di_atas_target"] = (a1.ci_low >= CM.ACC_TARGET).astype(int)
a1.to_csv(CM.RES2 / "accuracy_config.csv", index=False, float_format="%.10g")
order = ["agregasi", "filter tanggal", "join", "definisi KPI", "ambigu"]
a2 = E.groupby(["config", "type"]).apply(acc, include_groups=False).reset_index()
a2["_c"] = a2.config.map({c: i for i, c in enumerate(CM.CONFIGS)}); a2["_t"] = a2.type.map({t: i for i, t in enumerate(order)})
a2.sort_values(["_c", "_t"]).drop(columns=["_c", "_t"]).to_csv(CM.RES2 / "accuracy_type.csv", index=False, float_format="%.10g")
a3 = E.groupby(["config", "language"]).apply(acc, include_groups=False).reset_index()
rows = []
for c in CM.CONFIGS:
    d = E[E.config == c]
    t = [[int(((d.language == l) & (d.is_correct == 1)).sum()), int(((d.language == l) & (d.is_correct == 0)).sum())] for l in ("id", "en")]
    rows.append(dict(config=c, p_fisher=stats.fisher_exact(t)[1]))
a3 = a3.merge(pd.DataFrame(rows), on="config")
a3["_c"] = a3.config.map({c: i for i, c in enumerate(CM.CONFIGS)}); a3.sort_values(["_c", "language"]).drop(columns="_c").to_csv(CM.RES2 / "accuracy_language.csv", index=False, float_format="%.10g")
cmp_ = []
for a, b in (("tanpa_skema", "skema"), ("skema", "skema_kpi"), ("tanpa_skema", "skema_kpi")):
    x = E[E.config == a].set_index("question_id").is_correct; y = E[E.config == b].set_index("question_id").is_correct
    b_only, a_only = int(((y == 1) & (x == 0)).sum()), int(((x == 1) & (y == 0)).sum())
    n = a_only + b_only
    p = stats.binomtest(min(a_only, b_only), n, 0.5).pvalue if n else 1.0
    cmp_.append(dict(konfigurasi_a=a, konfigurasi_b=b, benar_hanya_a=a_only, benar_hanya_b=b_only, selisih_akurasi=float(y.mean() - x.mean()), p_mcnemar_eksak=p))
pd.DataFrame(cmp_).to_csv(CM.RES2 / "config_compare.csv", index=False, float_format="%.10g")
print(a1.to_string(index=False)); print(a2.to_string(index=False)); print(a3.to_string(index=False)); print(pd.DataFrame(cmp_).to_string(index=False))
