"""07: Analisis kegagalan (Q7) dan klarifikasi pertanyaan ambigu (Q8). Hasil: failure_categories.csv, failure_detail.csv, clarification.csv."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
import pandas as pd
import common as CM

E = pd.read_csv(CM.RES2 / "eval_results.csv", keep_default_na=False)
F = E[E.is_correct == 0]
cats = ["diblokir guardrail", "SQL error", "hasil salah", "ambigu tidak diklarifikasi", "klarifikasi keliru", "timeout"]
tab = pd.DataFrame([dict(config=c, kategori=k, jumlah=int(((F.config == c) & (F.failure == k)).sum())) for c in CM.CONFIGS for k in cats])
tab.to_csv(CM.RES2 / "failure_categories.csv", index=False)
det = F[["config", "question_id", "type", "language", "failure", "block_reason", "error", "generated_sql"]]
det.to_csv(CM.RES2 / "failure_detail.csv", index=False)
A_ = E[E.type == "ambigu"]
cl = A_.groupby("config").agg(ambigu=("question_id", "size"), diklarifikasi=("status", lambda s: int((s == "clarification").sum()))).reset_index()
nonamb = E[E.type != "ambigu"]
cl["klarifikasi_pada_pertanyaan_jelas"] = [int(((nonamb.config == c) & (nonamb.status == "clarification")).sum()) for c in cl.config]
cl = cl.set_index("config").loc[CM.CONFIGS].reset_index()
cl.to_csv(CM.RES2 / "clarification.csv", index=False)
print(tab.pivot(index="kategori", columns="config", values="jumlah")); print(cl)
