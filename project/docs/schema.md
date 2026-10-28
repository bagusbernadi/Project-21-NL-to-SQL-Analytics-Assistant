# Dokumentasi skema untuk asisten (dikirim ke LLM)

Dokumen ini dikirim sebagai bagian prompt. Hanya nama tabel, kolom, dan definisi yang dikirim, tidak ada isi data.
Bagian `SKEMA` dikirim pada konfigurasi "skema" dan "skema + definisi KPI". Bagian `KPI` hanya pada "skema + definisi KPI".

<!-- SKEMA -->
Database DuckDB (read-only, hanya SELECT). Tabel yang boleh dipakai:

- production_daily(date DATE, shift, station, model, operator_id, input_qty, ok_first_pass, ng_qty): satu baris per tanggal, shift, model, stasiun. input_qty = unit masuk stasiun, ok_first_pass = unit lolos pertama kali, ng_qty = unit NG. Contoh nilai: shift 'Shift 1' atau 'Shift 2'; model 'Matic 110', 'Bebek 125', 'Sport 150'.
- defect_log(date DATE, shift, station, model, defect_code, qty): jumlah satu jenis defect per tanggal, shift, model, stasiun.
- dim_defect(defect_code, defect_name, station, category): daftar kode defect. Kategori: Las, Cat, Mesin, Kelistrikan, Roda, Body, Kosmetik, Performa, Label.
- dim_station(station, seq): urutan stasiun di lini (seq 1 sampai 10).
- Stasiun: Frame Welding, Frame Painting, Engine Assembly, Wiring Harness Install, Wheel & Suspension, Body Panel Assembly, Electrical Test, Final Inspection, Performance Test (Dyno), Packing.
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
- Pertanyaan yang tidak menyebut ukuran atau periode yang jelas (misalnya "bagus?") tidak dijawab dengan tebakan: minta klarifikasi.
<!-- /KPI -->
