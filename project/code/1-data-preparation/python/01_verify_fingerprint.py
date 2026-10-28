"""01: Cocokkan data hasil generator dengan sidik jari SHA-256 di repo DataCenter (simulasi/fingerprints/project-21.sha256).

Hash sama berarti data identik dengan data yang dipakai di laporan. Daftar sidik jari: docs/datacenter_fingerprint.csv.
"""
import hashlib
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
import pandas as pd
from common import DOCS, RES1, ROOT

ref = pd.read_csv(DOCS / "datacenter_fingerprint.csv")
got = [hashlib.sha256((ROOT / p).read_bytes()).hexdigest() if (ROOT / p).exists() else "" for p in ref.project_path]
ref["hasil"] = ["cocok" if g == s else "beda" for g, s in zip(got, ref.sha256)]
ref["jenis"] = ["ground_truth" if "ground_truth" in p else "csv" for p in ref.project_path]
summ = ref.groupby("jenis").agg(berkas=("hasil", "size"), cocok=("hasil", lambda s: int((s == "cocok").sum()))).reset_index()
summ.to_csv(RES1 / "fingerprint_check.csv", index=False)
n_ok, n = int((ref.hasil == "cocok").sum()), len(ref)
print(f"sidik jari cocok: {n_ok} dari {n}")
assert n_ok == n, "data tidak identik dengan sidik jari DataCenter"
