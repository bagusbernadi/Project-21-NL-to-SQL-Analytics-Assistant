"""09: Lima fakta data rancangan terhadap data (ground truth hanya dibaca di skrip ini) dan hasil pytest.

Fakta rancangan: (1) satu stasiun (usulan Engine Assembly) paling sering NG; (2) lonjakan defect +-1 minggu di bulan kedua; (3) 3 pertanyaan ambigu di golden set;
(4) red-team memuat UPDATE, DELETE, DROP, tabel di luar daftar; (5) 2-3% data kotor. Hasil: design_facts.csv, pytest_result.csv.
"""
import json
import subprocess
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
import pandas as pd
import yaml
import common as CM

gt = json.loads((CM.SIM / "ground_truth.json").read_text(encoding="utf-8"))
p = pd.read_csv(CM.SIM / "production_daily.csv", parse_dates=["date"]); d = pd.read_csv(CM.SIM / "defect_log.csv", parse_dates=["date"])
gold = pd.DataFrame(yaml.safe_load((CM.EVAL / "golden_set.yaml").read_text(encoding="utf-8")))
rt = pd.DataFrame(yaml.safe_load((CM.EVAL / "redteam_set.yaml").read_text(encoding="utf-8"))["redteam"])
g = p.groupby("station").agg(i=("input_qty", "sum"), n=("ng_qty", "sum")); g["r"] = g.n / g.i
top = g.r.idxmax(); ea = g.loc["Engine Assembly"]
rank_ea = int(g.r.rank(ascending=False).loc["Engine Assembly"])
sp = [f for f in gt["facts"] if f["id"] == 3][0]
bp = p[p.station == "Body Panel Assembly"]
wk = bp.groupby(bp.date.dt.to_period("W-SUN").dt.start_time).apply(lambda x: x.ng_qty.sum() / x.input_qty.sum(), include_groups=False)
peak = wk.idxmax()
base = wk[(wk.index != peak)].median()
sdt = pd.Timestamp(sp["start"])
month_index = (sdt.year - p.date.min().year) * 12 + sdt.month - p.date.min().month + 1
fp_ = p[p.station == "Frame Painting"].groupby("shift").apply(lambda x: x.ng_qty.sum() / x.input_qty.sum(), include_groups=False)
md = p.groupby("model").apply(lambda x: x.ng_qty.sum() / x.input_qty.sum(), include_groups=False)
bad = int(((p.input_qty <= 0) | (p.ng_qty < 0) | (p.ok_first_pass + p.ng_qty != p.input_qty) | p.isna().any(axis=1)).sum())
kinds = sorted({k for k in ("UPDATE", "DELETE", "DROP") if rt.sql.str.contains(k).any()})
facts = pd.DataFrame([
    dict(fakta=1, rancangan="satu stasiun (usulan Engine Assembly) paling sering NG", ukuran="stasiun dengan NG rate tertinggi", nilai_teks=top, nilai=float(g.r.max()), nilai2=float(ea.r), keterangan=f"Engine Assembly peringkat {rank_ea} dari {len(g)}"),
    dict(fakta=2, rancangan="satu lonjakan defect ±1 minggu di bulan kedua", ukuran="minggu NG rate tertinggi Body Panel Assembly (mulai)", nilai_teks=str(peak.date()), nilai=float(wk.max()), nilai2=float(base), keterangan=f"tanggal tertanam {sp['start']} sampai {sp['end']}; bulan data ke-{month_index}"),
    dict(fakta=3, rancangan="golden set memuat 3 pertanyaan ambigu", ukuran="pertanyaan ambigu di golden set", nilai_teks="", nilai=float((gold.type == "ambigu").sum()), nilai2=float(len(gold)), keterangan="ditulis manual"),
    dict(fakta=4, rancangan="red-team memuat UPDATE, DELETE, DROP, dan tabel di luar daftar", ukuran="jenis perintah di red-team set", nilai_teks=", ".join(kinds), nilai=float(len(rt)), nilai2=float(rt.type.eq("tabel di luar daftar").sum()), keterangan="percobaan; tabel di luar daftar"),
    dict(fakta=5, rancangan="2% sampai 3% data kotor", ukuran="baris produksi tidak valid", nilai_teks="", nilai=float(bad), nilai2=float(len(p)), keterangan="data simulasi bersih")])
facts.to_csv(CM.RES2 / "design_facts.csv", index=False, float_format="%.10g")
extra = pd.DataFrame([dict(ukuran="NG rate Frame Painting, Shift 2 dibanding Shift 1", nilai=float(fp_["Shift 2"] / fp_["Shift 1"]), tertanam=float(gt["facts"][1]["factor"])),
                      dict(ukuran="NG rate Sport 150 dibanding Matic 110", nilai=float(md["Sport 150"] / md["Matic 110"]), tertanam=float(gt["facts"][3]["factors"]["Sport 150"] / gt["facts"][3]["factors"]["Matic 110"]))])
extra.to_csv(CM.RES2 / "ground_truth_extra.csv", index=False, float_format="%.10g")
xml = CM.RES2 / "_pytest.xml"
subprocess.run([sys.executable, "-m", "pytest", "-q", str(CM.TESTS), f"--junitxml={xml}", "-p", "no:cacheprovider"], check=True, capture_output=True, cwd=CM.ROOT)
root = ET.parse(xml).getroot()
tc = [dict(tes=c.get("name"), hasil="gagal" if (c.find("failure") is not None or c.find("error") is not None) else "lulus") for c in root.iter("testcase")]
xml.unlink()
pd.DataFrame(tc).to_csv(CM.RES2 / "pytest_result.csv", index=False)
print(facts.to_string(index=False)); print(extra); print(pd.DataFrame(tc).hasil.value_counts())
