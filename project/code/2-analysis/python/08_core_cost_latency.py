"""08: Cek silang 5 pertanyaan bisnis inti terhadap view KPI (Q12), latency (Q9), biaya per 100 pertanyaan (Q10), dan jam dihemat (Q11).

ASUMSI (docs/definitions.md): token = panjang teks / 4; harga 3 dan 15 USD per juta token (masukan, keluaran); latency API LLM 3 detik (tidak diukur);
15 menit per query manual; 200 pertanyaan per bulan. Semuanya berlabel estimated dan diuji sensitivitasnya.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
import pandas as pd
import assistant_lib as A
import common as CM

con = A.open_readonly()
CORE = [("C1", "yield per stasiun", "Berapa FPY per stasiun?", "SELECT station, fpy FROM v_kpi_station"),
        ("C2", "Pareto defect", "Berapa total defect menurut nama defect?", "SELECT defect_name, qty FROM v_pareto_defect"),
        ("C3", "tren NG rate mingguan", "Berapa NG rate per minggu?", "SELECT week_start, ng_rate FROM v_trend_week"),
        ("C4", "RTY per model", "Berapa RTY per model?", "SELECT model, rty FROM v_rty_model"),
        ("C5", "FPY satu stasiun per shift", "Berapa FPY Frame Painting per shift?", "SELECT shift, fpy FROM v_kpi_station_shift WHERE station = 'Frame Painting'")]
rows = []
for cid, nama, q, view in CORE:
    log, df = A.answer(con, q, "skema_kpi")
    ref = con.execute(view).df()
    ok = log["status"] == "ok" and A.same_result(ref, df)
    rows.append(dict(id=cid, topik=nama, pertanyaan=q, status=log["status"], baris_asisten=log["rows"], baris_view=len(ref), sama=int(ok), generated_sql=log["generated_sql"]))
core = pd.DataFrame(rows)
core.to_csv(CM.RES2 / "core_crosscheck.csv", index=False)

E = pd.read_csv(CM.RES2 / "eval_results.csv", keep_default_na=False)
LLM_S = 3.0
lat = []
for c in CM.CONFIGS:
    d = E[E.config == c]
    lat.append(dict(config=c, rata_komponen_lokal_ms=d.latency_bucket_ms.mean(), maks_komponen_lokal_ms=d.latency_bucket_ms.max(), asumsi_llm_detik=LLM_S, total_asumsi_detik=LLM_S + d.latency_bucket_ms.mean() / 1000,
                    manual_menit=CM.MANUAL_MIN_PER_QUERY, rasio_manual_vs_asisten=CM.MANUAL_MIN_PER_QUERY * 60 / (LLM_S + d.latency_bucket_ms.mean() / 1000)))
pd.DataFrame(lat).to_csv(CM.RES2 / "latency_summary.csv", index=False, float_format="%.10g")
cost = []
for c in CM.CONFIGS:
    d = E[E.config == c]
    for m in (0.5, 1.0, 2.0):
        usd = 100 * (d.prompt_tokens.mean() * CM.PRICE_IN_PER_M * m + d.completion_tokens.mean() * CM.PRICE_OUT_PER_M * m) / 1e6
        cost.append(dict(config=c, pengali_harga=m, token_masukan_rata=d.prompt_tokens.mean(), token_keluaran_rata=d.completion_tokens.mean(), usd_per_100_pertanyaan=usd, label="estimated"))
pd.DataFrame(cost).to_csv(CM.RES2 / "cost.csv", index=False, float_format="%.10g")
acc = E[E.config == "skema_kpi"].is_correct.mean()
hs = []
for mm in (5.0, CM.MANUAL_MIN_PER_QUERY, 30.0):
    hs.append(dict(menit_manual=mm, pertanyaan_per_bulan=CM.QUESTIONS_PER_MONTH, akurasi_skema_kpi=acc, jam_hemat_per_bulan=CM.QUESTIONS_PER_MONTH * acc * mm / 60,
                   jam_hemat_per_bulan_kotor=CM.QUESTIONS_PER_MONTH * mm / 60, dasar=int(mm == CM.MANUAL_MIN_PER_QUERY), label="estimated"))
pd.DataFrame(hs).to_csv(CM.RES2 / "hours_saved.csv", index=False, float_format="%.10g")
print(core.drop(columns="generated_sql")); print(pd.DataFrame(lat)); print(pd.DataFrame(cost)); print(pd.DataFrame(hs))
