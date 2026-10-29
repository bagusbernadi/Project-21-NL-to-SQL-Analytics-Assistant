# Spesifikasi simulasi

Data dibuat `00_generate_data.py` (seed 21260302, versi data v3). Parameter ada di skrip: 75 hari kerja dari 2026-03-02, 3 model, 2 shift, 10 stasiun, 20 kode defect. Data tidak di-commit; dibuat ulang dan diverifikasi dengan sidik jari SHA-256 repo DataCenter (`01_verify_fingerprint.py`).

Fakta yang ditanam generator (dipakai hanya di `09_ground_truth_check.py`; seluruh lima fakta data rancangan ditanam):
1. Engine Assembly NG rate dasar paling tinggi (0,040), stasiun lain 0,003 sampai 0,018. Frame Painting punya faktor Shift 2 x1,8.
2. Lonjakan NG Main Line Assembly x2,6 selama 5 hari kerja (2026-04-27 sampai 2026-05-01).
3. Faktor model: Matic 110 x0,85, Bebek 125 x1,00, Sport 150 x1,25.
4. Data kotor 2,5% baris production_daily (112 baris), empat jenis sama banyak: input nol, NG negatif, NG melebihi input, OK + NG tidak sama dengan input. defect_log dan rework_log tidak dikotori.
5. rework_log: 80% unit NG masuk rework (satu baris per unit), selesai 0 sampai 3 hari kerja kemudian, 90% berhasil diperbaiki.

Nama dan urutan 10 stasiun sama dengan rancangan. Golden set (30 pertanyaan) dan red-team set (15 percobaan, 2 uji beban) ditulis manual di `project/eval/`. Jawaban benar golden set memakai view `v_production` (baris kotor disaring).
