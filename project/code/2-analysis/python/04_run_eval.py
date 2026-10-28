"""04: Jalankan golden set (30 pertanyaan) pada 3 konfigurasi prompt. Pengganti LLM lokal (lihat docs/llm_standin.md).

Setiap pertanyaan: prompt, stand-in, guardrail, eksekusi read-only, bandingkan dengan hasil SQL referensi. Log disimpan juga di tabel query_log (evaluation.duckdb).
Kebijakan: stand-in dibekukan sebelum hasil pertama; hasil run pertama adalah hasil yang dilaporkan (tidak ada penyetelan aturan setelah melihat hasil).
Latency disimpan sebagai kelas 100 ms (pembulatan ke atas) agar hasil run ulang identik.
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

gold = yaml.safe_load((CM.EVAL / "golden_set.yaml").read_text(encoding="utf-8"))
con = A.open_readonly()
refs = {q["question_id"]: con.execute(q["reference_sql"]).df() for q in gold if q["reference_sql"]}
A.answer(con, "warm up total NG", "skema_kpi")                    # pemanasan agar latency run pertama tidak berbeda
rows = []
for cfg in CM.CONFIGS:
    for q in gold:
        log, df = A.answer(con, q["question"], cfg)
        if q["reference_sql"]:
            ok = log["status"] == "ok" and A.same_result(refs[q["question_id"]], df)
            fail = "" if ok else {"blocked": "diblokir guardrail", "error": "SQL error", "ok": "hasil salah", "clarification": "klarifikasi keliru", "timeout": "timeout"}[log["status"]]
        else:
            ok = log["status"] == "clarification"
            fail = "" if ok else "ambigu tidak diklarifikasi"
        rows.append(dict(config=cfg, question_id=q["question_id"], type=q["type"], language=q["language"], question=q["question"], generated_sql=log["generated_sql"], status=log["status"],
                         block_reason=log["block_reason"], error=log["error"].replace("\n", " "), rows=log["rows"], auto_limit=int(log["auto_limit"]), truncated=int(log["truncated"]),
                         prompt_tokens=log["prompt_tokens"], completion_tokens=log["completion_tokens"], tokens=log["tokens"],
                         latency_bucket_ms=int(math.ceil(log["latency_ms"] / 100.0) * 100), is_correct=int(ok), failure=fail))
E = pd.DataFrame(rows)
E.to_csv(CM.RES2 / "eval_results.csv", index=False)
ev = duckdb.connect(str(CM.EVAL_DB_PATH))
ev.execute("DROP TABLE IF EXISTS golden_set"); ev.execute("DROP TABLE IF EXISTS query_log")
G = pd.DataFrame(gold)
ev.execute("CREATE TABLE golden_set AS SELECT question_id, question, type, language, reference_sql FROM G")
Q = E.rename(columns={"generated_sql": "generated_sql"}).assign(log_id=range(1, len(E) + 1))[["log_id", "config", "question_id", "question", "generated_sql", "status", "rows", "latency_bucket_ms", "tokens", "is_correct"]]
ev.execute("CREATE TABLE query_log AS SELECT * FROM Q")
ev.close()
print(E.groupby("config").is_correct.agg(["sum", "count"]))
