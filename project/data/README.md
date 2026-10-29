# Data

Semua data di project ini simulasi (karangan), dibuat oleh generator dengan seed tetap. Tidak ada dataset publik atau data perusahaan, jadi tidak ada masalah lisensi.

| | |
|---|---|
| Versi data | v3 (v2: tanpa data kotor dan rework_log, stasiun Frame Painting terburuk, nama stasiun berbeda) |
| Tanggal dibuat | v2: 28 Okt 2026, v3: 29 Okt 2026 |
| Seed | 21260302 |
| Cara membuat ulang | `python3 code/1-data-preparation/python/00_generate_data.py` (dari folder project) |
| Hasil v3 | 4.500 baris produksi (112 kotor), 5.728 baris defect, 8.702 baris rework |

Isi folder ini tidak di-commit (lihat `.gitignore`). Jejak pembuatan (seed, commit, SHA-256 hasil) dicatat di repo [DataCenter](https://github.com/bagusbernadi/DataCenter/tree/main/simulasi) dan diverifikasi oleh `01_verify_fingerprint.py` terhadap `project/docs/datacenter_fingerprint.csv`. Jika generator, seed, atau versi library berubah, hasil berubah dan versi data harus dinaikkan.
