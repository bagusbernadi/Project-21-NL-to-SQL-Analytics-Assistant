# Data

Semua data di project ini simulasi (karangan), dibuat oleh generator dengan seed tetap. Tidak ada dataset publik atau data perusahaan, jadi tidak ada masalah lisensi.

| | |
|---|---|
| Versi data | v2 |
| Tanggal dibuat | 28 Okt 2026 |
| Seed | 21260302 |
| Cara membuat ulang | `python3 code/1-data-preparation/python/00_generate_data.py` (dari folder project) |
| Hasil v2 | 4.500 baris produksi, 5.874 baris defect |

Isi folder ini tidak di-commit (lihat `.gitignore`). Jejak pembuatan (seed, commit, SHA-256 hasil) dicatat di repo [DataCenter](https://github.com/bagusbernadi/DataCenter/tree/main/simulasi) dan diverifikasi oleh `01_verify_fingerprint.py` terhadap `project/docs/datacenter_fingerprint.csv`. Jika generator, seed, atau versi library berubah, hasil berubah dan versi data harus dinaikkan.
