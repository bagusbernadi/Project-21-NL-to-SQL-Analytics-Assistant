"""10: Uji aplikasi Streamlit dengan AppTest: tiap halaman berjalan tanpa exception dan angka tampil sama dengan CSV hasil dan database."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
import assistant_lib as A
import pandas as pd
from streamlit.testing.v1 import AppTest
import common as CM

APP = CM.ROOT / "code" / "3-presentation" / "streamlit" / "app.py"
acc = pd.read_csv(CM.RES2 / "accuracy_config.csv").set_index("config"); gs = pd.read_csv(CM.RES2 / "guardrail_summary.csv").iloc[0]
con = A.open_readonly()
ref_ng = int(con.execute("SELECT SUM(ng_qty) FROM production_daily WHERE station = 'Engine Assembly' AND date BETWEEN DATE '2026-06-08' AND DATE '2026-06-14'").fetchone()[0])
low = con.execute("SELECT station FROM v_kpi_station ORDER BY fpy LIMIT 1").fetchone()[0]
res = {}
at = AppTest.from_file(str(APP), default_timeout=90).run()
res["halaman Tanya data tanpa error"] = not at.exception
at.text_input[0].set_value("Berapa total NG Engine Assembly minggu lalu?")
at.button[0].click().run()
res["pertanyaan biasa tanpa error"] = not at.exception
res["SQL ditampilkan"] = len(at.code) == 1 and "SELECT" in at.code[0].value
res["jawaban sama dengan database"] = any(f"{ref_ng}" in str(v) for d in at.dataframe for v in d.value.to_numpy().ravel())
at.text_input[0].set_value("Which station has the lowest FPY?")
at.button[0].click().run()
res["stasiun FPY terendah sama dengan view"] = any(low in str(d.value.to_numpy()) for d in at.dataframe)
at.text_input[0].set_value("Yield kemarin bagus nggak?")
at.button[0].click().run()
res["pertanyaan ambigu meminta klarifikasi"] = len(at.warning) == 1 and not at.exception
at.button[1].click().run()
res["guardrail menolak DELETE di aplikasi"] = any("Ditolak" in m.value for m in at.markdown)
at.sidebar.radio[0].set_value("Hasil evaluasi").run()
res["halaman Hasil evaluasi tanpa error"] = not at.exception
m = {x.label: x.value for x in at.metric}
res["akurasi sama dengan CSV"] = m["Akurasi skema + KPI"] == f"{acc.loc['skema_kpi', 'akurasi'] * 100:.1f}%"
res["red-team sama dengan CSV"] = m["Red-team ditolak"] == f"{int(gs.ditolak_guardrail)} dari {int(gs.percobaan)}"
out = pd.DataFrame(list(res.items()), columns=["pemeriksaan", "hasil"])
out["hasil"] = out.hasil.map({True: "lulus", False: "gagal"})
out.to_csv(CM.RES3 / "app_test.csv", index=False)
print(out.to_string(index=False))
assert (out.hasil == "lulus").all(), "uji aplikasi gagal"
