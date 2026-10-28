# Spesifikasi simulasi

Data dibuat `00_generate_data.py` (seed 21260302, versi data v2). Parameter ada di skrip: 75 hari kerja dari 2026-03-02, 3 model, 2 shift, 10 stasiun, 20 kode defect. Data tidak di-commit; dibuat ulang dan diverifikasi dengan sidik jari SHA-256 repo DataCenter (`01_verify_fingerprint.py`).

Fakta yang ditanam generator (dipakai hanya di `09_ground_truth_check.py`):
1. Frame Painting NG rate dasar paling tinggi (0,040), faktor Shift 2 x1,8.
2. Lonjakan NG Body Panel Assembly x2,6 selama 5 hari kerja (2026-04-27 sampai 2026-05-01).
3. Faktor model: Matic 110 x0,85, Bebek 125 x1,00, Sport 150 x1,25.

Tidak ditanam: data kotor 2 sampai 3% (nilai nol, negatif, NG melebihi input), tabel rework_log, jenis uji lain. Golden set (30 pertanyaan) dan red-team set (15 percobaan, 2 uji beban) ditulis manual di `project/eval/`.
