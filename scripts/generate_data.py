"""Project 21: data produksi simulasi 10 stasiun, 3 model (skema sama dengan Project 3). Seed tetap.

Hasil (data/sim/): production_daily.csv, defect_log.csv, dim_defect.csv, dim_station.csv, ground_truth.json.
Golden set 30 pertanyaan dan red-team set disusun manual (folder eval/), bukan dari skrip ini.
Jalankan: python scripts/generate_data.py   (versi data: v1)
"""
import json
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "sim"
START_DATE = "2026-03-02"      # Senin
N_DAYS = 75                    # hari kerja Senin-Jumat
MODELS = ["Basic", "Plus", "Pro"]
SHIFTS = ["Shift 1", "Shift 2"]
STATIONS = ["Solder Paste Printing", "Component Placement", "Reflow Soldering", "AOI Inspection",
            "Board Test (ICT)", "Screen Assembly", "Housing Assembly", "Final Inspection",
            "Functional Test", "Packaging"]
# kode defect: (kode, nama, indeks stasiun, kategori, bobot di stasiun)
DEFECTS = [
    ("SPP-01", "Pasta solder kurang", 0, "Solder", 1.00),
    ("CPL-01", "Missing component", 1, "Komponen", 0.60),
    ("CPL-02", "Komponen terbalik", 1, "Komponen", 0.40),
    ("RFL-01", "Solder bridge", 2, "Solder", 0.68),
    ("RFL-02", "Cold solder", 2, "Solder", 0.32),
    ("AOI-01", "Komponen bergeser", 3, "Komponen", 1.00),
    ("ICT-01", "Short circuit", 4, "Elektrikal", 0.55),
    ("ICT-02", "Open circuit", 4, "Elektrikal", 0.45),
    ("SCR-01", "Layar retak", 5, "Layar", 0.50),
    ("SCR-02", "Dead pixel", 5, "Layar", 0.50),
    ("HSG-01", "Gores casing", 6, "Casing", 0.60),
    ("HSG-02", "Celah casing", 6, "Casing", 0.40),
    ("FIN-01", "Cacat kosmetik", 7, "Kosmetik", 1.00),
    ("FCT-01", "Kamera gagal tes", 8, "Fungsi", 0.40),
    ("FCT-02", "Sensor gagal tes", 8, "Fungsi", 0.35),
    ("FCT-03", "Baterai gagal tes", 8, "Fungsi", 0.25),
    ("PKG-01", "Label salah", 9, "Label", 1.00),
]
BASE_NG = [0.012, 0.011, 0.040, 0.008, 0.013, 0.010, 0.015, 0.012, 0.020, 0.003]
MODEL_FACTOR = {"Basic": 0.85, "Plus": 1.00, "Pro": 1.25}
START_QTY = {"Basic": 460, "Plus": 420, "Pro": 360}
OPERATOR = {(s, sh): f"OP{2 * s + j + 1:02d}" for s in range(len(STATIONS)) for j, sh in enumerate(SHIFTS)}
DATES = pd.bdate_range(START_DATE, periods=N_DAYS)


def make_production(rng, ng_scale=1.0, extra_factor=None):
    """Satu baris per tanggal x shift x model x stasiun (4.500 baris).

    extra_factor(t, station, model, shift) -> pengali peluang NG (untuk kejadian tertanam).
    Hasil: (prod, defect_log) tanpa data kotor.
    """
    by_station = {s: [d for d in DEFECTS if d[2] == s] for s in range(len(STATIONS))}
    prod, dlog = [], []
    for t, day in enumerate(DATES):
        noise = np.exp(rng.normal(0, 0.15, len(STATIONS)))
        for m in MODELS:
            for sh in SHIFTS:
                qty = int(round(START_QTY[m] * rng.normal(1, 0.05)))
                for s, st in enumerate(STATIONS):
                    p = BASE_NG[s] * MODEL_FACTOR[m] * noise[s] * ng_scale
                    if extra_factor:
                        p *= extra_factor(t, s, m, sh)
                    ng = int(rng.binomial(qty, min(p, 0.5)))
                    cds = by_station[s]
                    w = np.array([c[4] for c in cds])
                    split = rng.multinomial(ng, w / w.sum())
                    prod.append([day.date(), sh, st, m, OPERATOR[(s, sh)], qty, qty - ng, ng])
                    for c, q in zip(cds, split):
                        if q:
                            dlog.append([day.date(), sh, st, m, c[0], int(q)])
                    qty -= ng
    prod = pd.DataFrame(prod, columns=["date", "shift", "station", "model", "operator_id",
                                       "input_qty", "ok_first_pass", "ng_qty"])
    dlog = pd.DataFrame(dlog, columns=["date", "shift", "station", "model", "defect_code", "qty"])
    return prod, dlog


def write_reference():
    pd.DataFrame([(d[0], d[1], STATIONS[d[2]], d[3]) for d in DEFECTS],
                 columns=["defect_code", "defect_name", "station", "category"]).to_csv(OUT / "dim_defect.csv", index=False)
    pd.DataFrame({"station": STATIONS, "seq": range(1, len(STATIONS) + 1)}).to_csv(OUT / "dim_station.csv", index=False)

SEED = 21260302
DATA_VERSION = "v1"
rng = np.random.default_rng(SEED)

# Fakta tertanam (dipakai menilai jawaban asisten, bukan dibaca oleh asisten)
SHIFT2_STATION, SHIFT2_FACTOR = 1, 1.8           # Shift 2 di Component Placement
SPIKE_STATION, SPIKE_DAYS, SPIKE_FACTOR = 5, range(40, 45), 2.6   # lonjakan Screen Assembly 1 minggu


def extra(t, s, m, sh):
    f = 1.0
    if s == SHIFT2_STATION and sh == "Shift 2":
        f *= SHIFT2_FACTOR
    if s == SPIKE_STATION and t in SPIKE_DAYS:
        f *= SPIKE_FACTOR
    return f


OUT.mkdir(parents=True, exist_ok=True)
prod, dlog = make_production(rng, ng_scale=0.70, extra_factor=extra)
prod.to_csv(OUT / "production_daily.csv", index=False)
dlog.to_csv(OUT / "defect_log.csv", index=False)
write_reference()
gt = {"seed": SEED, "version": DATA_VERSION, "start_date": START_DATE, "n_days": N_DAYS,
      "facts": [
          {"id": 1, "fact": "Reflow Soldering paling banyak NG", "station": STATIONS[2]},
          {"id": 2, "fact": "Shift 2 lebih tinggi NG di Component Placement", "factor": SHIFT2_FACTOR},
          {"id": 3, "fact": "Lonjakan NG Screen Assembly", "start": str(DATES[SPIKE_DAYS[0]].date()),
           "end": str(DATES[SPIKE_DAYS[-1]].date()), "factor": SPIKE_FACTOR},
          {"id": 4, "fact": "Model Pro NG rate lebih tinggi dari Basic", "factors": MODEL_FACTOR}]}
(OUT / "ground_truth.json").write_text(json.dumps(gt, indent=2, ensure_ascii=False), encoding="utf-8")
print(f"production_daily {len(prod)} baris, defect_log {len(dlog)} baris -> {OUT}")
