"""12: README.md dari CSV hasil (angka tidak diketik). Dijalankan paling akhir sebelum build_report.py."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
import pandas as pd
import common as CM

R1, R2, R3 = CM.RES1, CM.RES2, CM.RES3
acc = pd.read_csv(R2 / "accuracy_config.csv").set_index("config"); typ = pd.read_csv(R2 / "accuracy_type.csv"); gs = pd.read_csv(R2 / "guardrail_summary.csv").iloc[0]
core = pd.read_csv(R2 / "core_crosscheck.csv"); cx = pd.read_csv(R2 / "crosscheck.csv"); pt = pd.read_csv(R2 / "pytest_result.csv"); at = pd.read_csv(R3 / "app_test.csv")
cost = pd.read_csv(R2 / "cost.csv"); hs = pd.read_csv(R2 / "hours_saved.csv"); hs = hs[hs.dasar == 1].iloc[0]; db = pd.read_csv(R1 / "db_tables.csv").set_index("objek").baris
fc = pd.read_csv(R2 / "failure_categories.csv"); cl = pd.read_csv(R2 / "clarification.csv").set_index("config"); lat = pd.read_csv(R2 / "latency_summary.csv").set_index("config")
fp = pd.read_csv(R1 / "fingerprint_check.csv")


def I(n): return f"{int(round(float(n))):,}".replace(",", ".")
def D(x, d=1): return f"{float(x):.{d}f}".replace(".", ",")
def P(x, d=1): return D(float(x) * 100, d) + "%"


rows = "\n".join(f"| {CM.CONFIG_LABEL[c]} | {I(r.benar)} dari {I(r.n)} | {P(r.akurasi, 1)} ({P(r.ci_low, 1)} sampai {P(r.ci_high, 1)}) |" for c, r in acc.iterrows())
c3 = cost[(cost.config == "skema_kpi") & (cost.pengali_harga == 1.0)].iloc[0]
core_ok = int(core.sama.sum())
txt = f"""[← Back to portfolio](https://bagusbernadi.github.io/)

# Project 21: Natural Language to SQL Analytics Assistant

**Status: Selesai di branch `project-21-build` (belum di-merge ke `main`).** Halaman rancangan dan laporan: [`design-and-report/index.html`](design-and-report/index.html) (tab Design Project dan Report Project).

**PENTING: komponen "LLM" pada project ini adalah pengganti aturan lokal, bukan Claude API** (tidak ada API key di sesi pengerjaan). Angka akurasi menggambarkan pengganti itu dan alat evaluasinya, bukan kemampuan Claude.

**Tujuan:** membangun asisten yang menjawab pertanyaan data produksi dalam bahasa biasa dengan menulis SQL lalu menjalankannya di database read-only, dan mengukur akurasinya terhadap jawaban SQL manual (golden set), sehingga hasilnya bisa diaudit.

| | |
|---|---|
| Kategori | Manufaktur (perakitan sepeda motor) |
| Tingkat | Menengah |
| Data | **Simulasi**: data produksi harian dan defect lini perakitan |
| Tools | Python (pandas), DuckDB + SQL, pengganti LLM lokal (Claude API tidak dipanggil), Streamlit + Plotly, pytest |

## 1. Problem

**Pertanyaan utama:** bagaimana orang non-teknis bisa bertanya data produksi dengan bahasa biasa dan mendapat angka yang benar dari database tanpa menulis SQL, dan seberapa akurat jawabannya dibanding SQL tulisan manual? Rancangan memecahnya menjadi 12 pertanyaan (7 Utama, 4 Pendukung, 1 Tambahan).

## 2. Data

- Data simulasi (100% karangan), dibuat `00_generate_data.py` (seed 21260302): {I(db['production_daily'])} baris produksi harian, {I(db['defect_log'])} baris defect, 10 stasiun, 3 model, 2 shift. Data tidak di-commit; dibuat ulang dari generator dan diverifikasi dengan sidik jari SHA-256 di repo [DataCenter](https://github.com/bagusbernadi/DataCenter/tree/main/simulasi) (`01_verify_fingerprint.py`: {I(fp.cocok.sum())} dari {I(fp.berkas.sum())} berkas cocok).
- Golden set 30 pertanyaan (8 agregasi, 7 filter tanggal, 6 join, 6 definisi KPI, 3 ambigu) dan red-team set 15 percobaan ditulis manual di `project/eval/`. Dokumentasi skema yang dikirim ke LLM: `project/docs/schema.md`.

## 3. Analysis

Alur: pertanyaan, prompt (3 konfigurasi), penulis SQL (stand-in), guardrail kode, eksekusi read-only dengan LIMIT dan timeout, bandingkan dengan SQL referensi. Definisi dan asumsi: `project/docs/definitions.md`; pengganti LLM: `project/docs/llm_standin.md`.

| Konfigurasi prompt | Benar | Execution accuracy (CI 95% Wilson) |
|---|---|---|
{rows}

- Konfigurasi dan stand-in dirancang bersama, jadi selisih antar konfigurasi adalah hasil rancangan, bukan bukti tentang LLM nyata.
- Red-team: {I(gs.ditolak_guardrail)} dari {I(gs.percobaan)} percobaan ditolak guardrail; tabel produksi tidak berubah (checksum sama). Read-only saja menolak {I(gs.ditolak_read_only_saja)} dari {I(gs.percobaan)}; dengan akses file dimatikan {I(gs.ditolak_akses_file_mati)} dari {I(gs.percobaan)}.
- Klarifikasi pertanyaan ambigu: {I(cl.loc['skema_kpi', 'diklarifikasi'])} dari {I(cl.loc['skema_kpi', 'ambigu'])} pada skema + KPI, {I(cl.loc['skema', 'diklarifikasi'])} dari {I(cl.loc['skema', 'ambigu'])} pada skema saja.
- Cek silang lima pertanyaan inti terhadap view KPI: {I(core_ok)} dari {I(len(core))} sama persis (pengganti tidak mendukung pengelompokan mingguan dan RTY per model).

## 4. Recommendation

Pasang Claude API pada antarmuka `StandIn.generate` dan jalankan ulang golden set dan red-team set sebelum menyimpulkan akurasi; pertahankan guardrail kode dan koneksi read-only dengan akses file dimatikan; tampilkan SQL pada setiap jawaban; perluas golden set dari 30 pertanyaan.

## 5. Impact

Estimasi (`estimated`): sekitar {D(hs.jam_hemat_per_bulan, 1)} jam analis per bulan ({I(hs.pertanyaan_per_bulan)} pertanyaan x {P(hs.akurasi_skema_kpi, 1)} benar x {D(hs.menit_manual, 0)} menit / 60); menit per query manual adalah asumsi. Biaya API per 100 pertanyaan dengan token perkiraan dan harga asumsi: sekitar {D(c3.usd_per_100_pertanyaan, 2)} USD (estimated).

```
jam hemat per bulan = pertanyaan per bulan x akurasi x menit manual per query / 60
```

## Batasan

- **Data adalah simulasi**; angka menggambarkan simulasi, bukan lini produksi.
- **Penulis SQL adalah pengganti aturan lokal, bukan Claude**; akurasi, latency LLM, dan biaya bukan pengukuran model nyata. Latency API (3 detik), harga token, token per teks, menit manual, dan volume pertanyaan adalah asumsi.
- Golden set kecil (30 pertanyaan) dan ditulis oleh orang yang sama dengan stand-in; akurasi cenderung optimistis.
- Kelima fakta data rancangan ditanam dan terdeteksi; generator, golden set, stand-in, dan guardrail ditulis oleh orang yang sama, jadi hasil optimistis.
- Aplikasi belum di-deploy (diuji AppTest: {I((at.hasil == 'lulus').sum())} dari {I(len(at))} lulus); success criteria "orang awam dalam 1 menit" belum diuji; Docker dan slide tidak dibuat; branch belum di-merge ke main.
- Cek silang: {I(cx.cocok.sum())} dari {I(cx.dibandingkan.sum())} cocok; pytest {I((pt.hasil == 'lulus').sum())} dari {I(len(pt))} lulus.

## Menjalankan

Dari folder `project/`:

```
pip install -r requirements.txt
bash run21.sh
streamlit run code/3-presentation/streamlit/app.py
```

## Struktur repository

```
README.md
index.html                     pengalihan ke design-and-report/
design-and-report/             index.html (tab Design + Report), src/ (page_v1.html, report.css, report_lib.py, build_report.py)
project/
  code/                        common.py, assistant_lib.py; 1-data-preparation/{{python,sql}} (00 sampai 02); 2-analysis/python (03 sampai 09); 3-presentation/{{python,streamlit}} (10 sampai 12)
  eval/                        golden_set.yaml, redteam_set.yaml (ditulis manual)
  tests/                       test_eval.py (pytest)
  results/                     1-data-preparation/ 2-analysis/ 3-presentation/ (CSV hasil, analysis.ipynb)
  data/                        README.md (data tidak di-commit)
  docs/                        schema.md, data_dictionary.md, definitions.md, llm_standin.md, simulation_spec.md, datacenter_fingerprint.csv
  run21.sh, requirements.txt
```
"""
(CM.ROOT.parent / "README.md").write_text(txt, encoding="utf-8")
print("README ditulis")
