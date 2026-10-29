# Dokumentasi skema untuk asisten (dikirim ke LLM)

Dokumen ini dikirim sebagai bagian prompt. Hanya nama tabel, kolom, dan definisi yang dikirim, tidak ada isi data.
Bagian `SKEMA` dikirim pada konfigurasi "skema" dan "skema + definisi KPI". Bagian `KPI` hanya pada "skema + definisi KPI".

<!-- SKEMA -->
Database DuckDB (read-only, hanya SELECT). Tabel yang boleh dipakai:

- production_daily(date DATE, shift, station, model, operator_id, input_qty, ok_first_pass, ng_qty): satu baris per tanggal, shift, model, stasiun. input_qty = unit masuk stasiun, ok_first_pass = unit lolos pertama kali, ng_qty = unit NG. Contoh nilai: shift 'Shift 1' atau 'Shift 2'; model 'Matic 110', 'Bebek 125', 'Sport 150'.
- defect_log(date DATE, shift, station, model, defect_code, qty): jumlah satu jenis defect per tanggal, shift, model, stasiun.
- rework_log(rework_id, date_in DATE, date_out DATE, station_origin, model, defect_code, result): satu baris per unit NG yang masuk rework; result 'repaired' atau 'scrap'.
- dim_defect(defect_code, defect_name, station, category): daftar kode defect. Kategori: Las, Cat, Mesin, Kelistrikan, Roda, Body, Kosmetik, Performa, Label.
- dim_station(station, seq): urutan stasiun di lini (seq 1 sampai 10).
- Stasiun: Frame Welding, Frame Painting, Engine Assembly, Engine Bench Test, Wheel & Suspension Assembly, Main Line Assembly, Electrical Check, Roller Test, Final Inspection, Packaging.
- View siap pakai: v_production, v_kpi_station, v_kpi_station_shift, v_pareto_defect, v_trend_week, v_rty_model.
<!-- /SKEMA -->

<!-- KPI -->
Definisi KPI dan kalender (ASUMSI di docs/definitions.md):

- FPY (first pass yield) sebuah stasiun = SUM(ok_first_pass) / SUM(input_qty) pada periode dan kelompok yang sama (rasio jumlah, bukan rata-rata rasio baris). "Yield" tanpa keterangan berarti FPY.
- NG rate = SUM(ng_qty) / SUM(input_qty).
- RTY (rolled throughput yield) = hasil kali FPY semua 10 stasiun, dihitung per model atau seluruh lini. "Yield lini" berarti RTY.
- Defect per 1.000 unit di sebuah stasiun = SUM(defect_log.qty) / SUM(production_daily.input_qty) x 1.000 untuk stasiun itu.
- Stasiun terburuk = FPY terendah.
- Tanggal acuan hari ini = {TODAY} (hanya sebagai konfigurasi). "Minggu lalu" = Senin sampai Minggu pada minggu ISO sebelum minggu hari ini. "Bulan ini" = bulan kalender hari ini sampai hari ini. "Bulan lalu" = bulan kalender sebelumnya. "Kemarin" = hari ini dikurangi 1.
- production_daily berisi baris tidak valid (input nol, NG negatif atau melebihi input, OK + NG tidak sama dengan input). Untuk KPI produksi pakai view v_production, yang sudah menyaringnya; jangan hitung dari production_daily.
- Pertanyaan yang tidak menyebut ukuran atau periode yang jelas (misalnya "bagus?") tidak dijawab dengan tebakan: minta klarifikasi.
<!-- /KPI -->
