[← Back to portfolio](https://bagusbernadi.github.io/)

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

- Data simulasi (100% karangan), dibuat `00_generate_data.py` (seed 21260302): 4.500 baris produksi harian, 5.874 baris defect, 10 stasiun, 3 model, 2 shift. Data tidak di-commit; dibuat ulang dari generator dan diverifikasi dengan sidik jari SHA-256 di repo [DataCenter](https://github.com/bagusbernadi/DataCenter/tree/main/simulasi) (`01_verify_fingerprint.py`: 5 dari 5 berkas cocok).
- Golden set 30 pertanyaan (8 agregasi, 7 filter tanggal, 6 join, 6 definisi KPI, 3 ambigu) dan red-team set 15 percobaan ditulis manual di `project/eval/`. Dokumentasi skema yang dikirim ke LLM: `project/docs/schema.md`.

## 3. Analysis

Alur: pertanyaan, prompt (3 konfigurasi), penulis SQL (stand-in), guardrail kode, eksekusi read-only dengan LIMIT dan timeout, bandingkan dengan SQL referensi. Definisi dan asumsi: `project/docs/definitions.md`; pengganti LLM: `project/docs/llm_standin.md`.

| Konfigurasi prompt | Benar | Execution accuracy (CI 95% Wilson) |
|---|---|---|
| Tanpa skema | 0 dari 30 | 0,0% (0,0% sampai 11,4%) |
| Skema | 19 dari 30 | 63,3% (45,5% sampai 78,1%) |
| Skema + definisi KPI | 29 dari 30 | 96,7% (83,3% sampai 99,4%) |

- Konfigurasi dan stand-in dirancang bersama, jadi selisih antar konfigurasi adalah hasil rancangan, bukan bukti tentang LLM nyata.
- Red-team: 15 dari 15 percobaan ditolak guardrail; tabel produksi tidak berubah (checksum sama). Read-only saja menolak 12 dari 15; dengan akses file dimatikan 14 dari 15.
- Klarifikasi pertanyaan ambigu: 3 dari 3 pada skema + KPI, 0 dari 3 pada skema saja.
- Cek silang lima pertanyaan inti terhadap view KPI: 3 dari 5 sama persis (pengganti tidak mendukung pengelompokan mingguan dan RTY per model).

## 4. Recommendation

Pasang Claude API pada antarmuka `StandIn.generate` dan jalankan ulang golden set dan red-team set sebelum menyimpulkan akurasi; pertahankan guardrail kode dan koneksi read-only dengan akses file dimatikan; tampilkan SQL pada setiap jawaban; perluas golden set dari 30 pertanyaan.

## 5. Impact

Estimasi (`estimated`): sekitar 48,3 jam analis per bulan (200 pertanyaan x 96,7% benar x 15 menit / 60); menit per query manual adalah asumsi. Biaya API per 100 pertanyaan dengan token perkiraan dan harga asumsi: sekitar 0,22 USD (estimated).

```
jam hemat per bulan = pertanyaan per bulan x akurasi x menit manual per query / 60
```

## Batasan

- **Data adalah simulasi**; angka menggambarkan simulasi, bukan lini produksi.
- **Penulis SQL adalah pengganti aturan lokal, bukan Claude**; akurasi, latency LLM, dan biaya bukan pengukuran model nyata. Latency API (3 detik), harga token, token per teks, menit manual, dan volume pertanyaan adalah asumsi.
- Golden set kecil (30 pertanyaan) dan ditulis oleh orang yang sama dengan stand-in; akurasi cenderung optimistis.
- Fakta data rancangan hanya sebagian ditanam: stasiun terburuk Frame Painting (bukan Engine Assembly), tidak ada data kotor 2 sampai 3%, tidak ada tabel rework_log.
- Aplikasi belum di-deploy (diuji AppTest: 10 dari 10 lulus); success criteria "orang awam dalam 1 menit" belum diuji; Docker dan slide tidak dibuat; branch belum di-merge ke main.
- Cek silang: 75 dari 75 cocok; pytest 57 dari 57 lulus.

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
  code/                        common.py, assistant_lib.py; 1-data-preparation/{python,sql} (00 sampai 02); 2-analysis/python (03 sampai 09); 3-presentation/{python,streamlit} (10 sampai 12)
  eval/                        golden_set.yaml, redteam_set.yaml (ditulis manual)
  tests/                       test_eval.py (pytest)
  results/                     1-data-preparation/ 2-analysis/ 3-presentation/ (CSV hasil, analysis.ipynb)
  data/                        README.md (data tidak di-commit)
  docs/                        schema.md, data_dictionary.md, definitions.md, llm_standin.md, simulation_spec.md, datacenter_fingerprint.csv
  run21.sh, requirements.txt
```
