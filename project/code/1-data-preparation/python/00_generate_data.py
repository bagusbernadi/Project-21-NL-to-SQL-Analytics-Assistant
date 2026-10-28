"""Project 21: data produksi simulasi lini perakitan sepeda motor (10 stasiun, 3 model, skema tabel seperti Project 3). Seed tetap.

Hasil (data/sim/): production_daily.csv, defect_log.csv, dim_defect.csv, dim_station.csv, ground_truth.json.
Golden set 30 pertanyaan dan red-team set disusun manual (folder eval/), bukan dari skrip ini.
Jalankan: python3 code/1-data-preparation/python/00_generate_data.py (dari folder project)   (versi data: v2)
"""
import json
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / "data" / "sim"
START_DATE = "2026-03-02"      # Senin
N_DAYS = 75                    # hari kerja Senin-Jumat
MODELS = ["Matic 110", "Bebek 125", "Sport 150"]
SHIFTS = ["Shift 1", "Shift 2"]
STATIONS = ["Frame Welding", "Frame Painting", "Engine Assembly", "Wiring Harness Install",
            "Wheel & Suspension", "Body Panel Assembly", "Electrical Test", "Final Inspection",
            "Performance Test (Dyno)", "Packing"]
# kode defect: (kode, nama, indeks stasiun, kategori, bobot di stasiun)
DEFECTS = [
    ("FWD-01", "Porositas las", 0, "Las", 0.55),
    ("FWD-02", "Dimensi frame meleset", 0, "Las", 0.45),
    ("PNT-01", "Cat tipis", 1, "Cat", 0.45),
    ("PNT-02", "Cat berkulit jeruk", 1, "Cat", 0.35),
    ("PNT-03", "Debu pada cat", 1, "Cat", 0.20),
    ("ENG-01", "Torsi baut kurang", 2, "Mesin", 0.50),
    ("ENG-02", "Rembes oli", 2, "Mesin", 0.50),
    ("WRH-01", "Konektor tidak masuk penuh", 3, "Kelistrikan", 0.60),
    ("WRH-02", "Kabel terjepit", 3, "Kelistrikan", 0.40),
    ("WHL-01", "Velg oleng", 4, "Roda", 0.50),
    ("WHL-02", "Suspensi bocor", 4, "Roda", 0.50),
    ("BDY-01", "Gores panel body", 5, "Body", 0.55),
    ("BDY-02", "Celah panel tidak rata", 5, "Body", 0.45),
    ("ELT-01", "Lampu tidak menyala", 6, "Kelistrikan", 0.45),
    ("ELT-02", "Starter gagal", 6, "Kelistrikan", 0.55),
    ("FIN-01", "Cacat kosmetik", 7, "Kosmetik", 0.60),
    ("FIN-02", "Stiker salah", 7, "Kosmetik", 0.40),
    ("DYN-01", "Akselerasi di bawah spec", 8, "Performa", 0.50),
    ("DYN-02", "Rem tidak sesuai tes", 8, "Performa", 0.50),
    ("PKG-01", "Label atau kemasan rusak", 9, "Label", 1.00),
]
BASE_NG = [0.014, 0.040, 0.013, 0.011, 0.012, 0.015, 0.018, 0.010, 0.016, 0.003]
MODEL_FACTOR = {"Matic 110": 0.85, "Bebek 125": 1.00, "Sport 150": 1.25}
START_QTY = {"Matic 110": 300, "Bebek 125": 240, "Sport 150": 150}
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
DATA_VERSION = "v2"
rng = np.random.default_rng(SEED)

# Fakta tertanam (dipakai menilai jawaban asisten, bukan dibaca oleh asisten)
SHIFT2_STATION, SHIFT2_FACTOR = 1, 1.8           # Shift 2 di Frame Painting
SPIKE_STATION, SPIKE_DAYS, SPIKE_FACTOR = 5, range(40, 45), 2.6   # lonjakan Body Panel Assembly 1 minggu


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
          {"id": 1, "fact": "Frame Painting paling banyak NG", "station": STATIONS[1]},
          {"id": 2, "fact": "Shift 2 lebih tinggi NG di Frame Painting", "factor": SHIFT2_FACTOR},
          {"id": 3, "fact": "Lonjakan NG Body Panel Assembly", "start": str(DATES[SPIKE_DAYS[0]].date()),
           "end": str(DATES[SPIKE_DAYS[-1]].date()), "factor": SPIKE_FACTOR},
          {"id": 4, "fact": "Sport 150 NG rate lebih tinggi dari Matic 110", "factors": MODEL_FACTOR}]}
(OUT / "ground_truth.json").write_text(json.dumps(gt, indent=2, ensure_ascii=False), encoding="utf-8")
print(f"production_daily {len(prod)} baris, defect_log {len(dlog)} baris -> {OUT}")
