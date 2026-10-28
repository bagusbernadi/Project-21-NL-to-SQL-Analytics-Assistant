# Definisi dan asumsi (label ASUMSI = tidak ada di rancangan)

- **ASUMSI** Pengganti LLM: tidak ada Claude API key di sesi pengerjaan, jadi penulis SQL adalah pengurai aturan lokal (`StandIn` di `code/assistant_lib.py`, dijelaskan di `docs/llm_standin.md`). Akurasi, latency LLM, dan biaya BUKAN pengukuran Claude.
- **ASUMSI** Tanggal acuan "hari ini" = 2026-06-17 (Rabu). "Minggu lalu" = Senin sampai Minggu minggu ISO sebelumnya (8 sampai 14 Juni). "Bulan ini" = 1 Juni sampai hari ini. "Bulan lalu" = Mei.
- **ASUMSI** "Yield" tanpa keterangan = FPY = SUM(ok_first_pass) / SUM(input_qty). "Yield lini" = RTY = hasil kali FPY 10 stasiun. Stasiun terburuk = FPY terendah. Defect per 1.000 unit = SUM(defect_log.qty) / SUM(input_qty) x 1.000 pada stasiun yang sama.
- **ASUMSI** Execution accuracy: hasil query sama dengan hasil SQL referensi (himpunan baris, desimal dibulatkan 6 angka, nama kolom dan urutan baris diabaikan). Pertanyaan ambigu benar bila asisten meminta klarifikasi.
- **ASUMSI** Guardrail: satu pernyataan SELECT, tabel hanya dari daftar (4 tabel, 6 view), tanpa fungsi tabel atau fungsi file; LIMIT 1.000 otomatis bila tidak ada LIMIT; batas waktu 5 detik.
- **ASUMSI** Token = panjang teks / 4. Harga 3 dan 15 USD per juta token (masukan dan keluaran), bukan harga resmi model mana pun; sensitivitas harga x0,5 dan x2.
- **ASUMSI** Latency API LLM 3 detik (tidak diukur). Waktu komponen lokal (stand-in, guardrail, database) dicatat dalam kelas 100 ms agar hasil run ulang identik.
- **ASUMSI** 15 menit per query manual analis (sensitivitas 5 dan 30 menit); 200 pertanyaan per bulan; hanya jawaban benar yang menghemat waktu.
- **ASUMSI** Lima pertanyaan inti untuk cek silang: yield per stasiun, Pareto defect, tren NG rate mingguan, RTY per model, FPY Frame Painting per shift (rancangan menyebut "yield per stasiun, Pareto defect, tren" tanpa daftar lengkap).
- Alpha 0,05; CI Wilson untuk proporsi; uji McNemar eksak untuk perbandingan konfigurasi berpasangan; uji Fisher untuk bahasa.
