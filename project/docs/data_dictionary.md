# Kamus data

Skema tabel dan definisi KPI yang dikirim ke asisten ada di `docs/schema.md` (sumber tunggal). Tabel `golden_set` dan `query_log` ada di `evaluation.duckdb` dan tidak terlihat oleh asisten.

| Tabel | Isi (1 baris = ...) | Kolom |
|---|---|---|
| production_daily | satu tanggal, shift, model, stasiun | date, shift, station, model, operator_id, input_qty, ok_first_pass, ng_qty |
| defect_log | satu jenis defect per tanggal, shift, model, stasiun | date, shift, station, model, defect_code, qty |
| rework_log | satu unit NG yang masuk rework | rework_id, date_in, date_out, station_origin, model, defect_code, result |
| dim_defect | satu kode defect | defect_code, defect_name, station, category |
| dim_station | satu stasiun | station, seq |
| golden_set | satu pertanyaan uji | question_id, question, type, language, reference_sql |
| query_log | satu pertanyaan yang dijawab asisten | log_id, config, question_id, question, generated_sql, status, rows, latency_bucket_ms, tokens, is_correct |

`production_daily` memuat 2 sampai 3% baris kotor (ditanam generator); `v_production` menyaringnya. Tabel `rework_log` tidak dipakai KPI atau golden set.
