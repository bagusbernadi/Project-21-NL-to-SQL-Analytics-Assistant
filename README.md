[← Back to portfolio](https://bagusbernadi.github.io/)

# Project 21: Natural Language to SQL Analytics Assistant

**Status: Design (rancangan).**

**Tujuan:** Membangun asisten yang menjawab pertanyaan data produksi dalam bahasa biasa dengan cara menulis SQL lalu menjalankannya di database read-only, dan mengukur akurasinya terhadap jawaban SQL manual, sehingga tim non-teknis bisa mendapat angka yang benar dan bisa diaudit tanpa menunggu analis.


| | |
|---|---|
| Kategori | Manufaktur (perakitan sepeda motor) |
| Tingkat | Menengah |
| Data | Simulasi: data produksi 10 stasiun, 3 model (struktur sama dengan Project 3) + golden set 30 pertanyaan |
| Tools | DuckDB + SQL, Claude API, Python (pandas), Streamlit + Plotly, pytest, Docker (opsional) |

## 1. Problem
Bagaimana orang non-teknis bisa bertanya data produksi dengan bahasa biasa dan mendapat angka yang benar dari database tanpa menulis SQL, dan seberapa akurat jawabannya dibanding SQL tulisan manual?

## 2. Data
Data produksi simulasi dibuat oleh `scripts/generate_data.py` (seed tetap). Perkiraan ±4.500 baris produksi harian dan ±6.000 baris defect. Golden set 30 pertanyaan dan red-team set ±15 permintaan berbahaya disusun manual. Hanya skema yang dikirim ke LLM API, bukan isi data.

## 3. Analysis
Rencana: execution accuracy per tipe pertanyaan dan konfigurasi prompt, uji guardrail, analisis pola kegagalan, latency dan biaya. Belum dikerjakan.

## 4. Recommendation
Belum dikerjakan.

## 5. Impact
Belum dikerjakan. Angka dampak akan diberi label `estimated` / `simulated`.

## Batasan yang sudah diketahui
- LLM bisa salah dengan yakin; SQL selalu ditampilkan dan hasil penting tetap diverifikasi.
- Golden set 30 pertanyaan cukup untuk melihat pola, belum untuk klaim akurasi umum.
- Akurasi dan biaya dicatat bersama nama model dan tanggal uji.

## Struktur repository (rencana)
```
docs/            # dokumentasi skema dan definisi KPI
eval/            # golden set dan red-team set
scripts/         # generator data simulasi
app/             # asisten (prompt, guardrail) dan aplikasi Streamlit
tests/           # evaluasi otomatis
notebooks/       # analisis akurasi
index.html       # halaman rancangan (GitHub Pages)
README.md
```
