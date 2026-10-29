# Pengganti LLM lokal (stand-in)

Sesi pengerjaan tidak punya Claude API key. Rancangan memakai Claude API untuk menulis SQL. Penggantinya adalah pengurai aturan deterministik (`StandIn.generate`).

**Yang diuji nyata:** guardrail (`check_sql`), eksekusi read-only dengan LIMIT dan timeout (`execute`), perbandingan hasil (`same_result`), golden set, red-team set, aplikasi, dan jalur log. Semua tidak berubah bila LLM asli dipasang.

**Yang tidak diuji:** kemampuan LLM menulis SQL. Angka akurasi menggambarkan aturan stand-in, bukan Claude. Penulis stand-in dan golden set adalah orang yang sama, dan aturan dilihat terhadap golden set selama pengembangan, sehingga akurasi cenderung optimistis. Setelah hasil pertama keluar, aturan dibekukan; hasil run pertama itulah yang dilaporkan.

## Cara kerja
Pertanyaan dipecah menjadi ukuran (total input, NG, defect, FPY, NG rate, RTY, defect per 1.000), kelompok (stasiun, model, shift, nama defect, urutan stasiun), filter (stasiun, model, shift, kategori, tanggal), dan pengurutan (tertinggi, terendah). Slot disusun menjadi satu SELECT.

## Perbedaan tiga konfigurasi (model pengetahuan prompt)
| Konfigurasi | Pengetahuan | Perilaku stand-in |
|---|---|---|
| Tanpa skema | tidak tahu nama tabel dan kolom ukuran | menebak nama umum (`production`, `defects`, `total_input`, `ng_count`); tidak diinstruksikan meminta klarifikasi, jadi menebak |
| Skema | nama tabel dan kolom benar | KPI dihitung dengan tebakan literal (rata-rata rasio baris, yield lini = rasio jumlah, 7 hari terakhir untuk minggu lalu, join langsung untuk defect per 1.000 unit); menebak pada pertanyaan ambigu |
| Skema + definisi KPI | skema, definisi KPI, kalender, peringatan data kotor, dan instruksi klarifikasi | memakai definisi di `docs/schema.md` dan view `v_production` (bersih); meminta klarifikasi bila ukuran atau periode tidak jelas |

Perbedaan antar konfigurasi adalah pilihan pemodelan, jadi selisih akurasinya hasil rancangan stand-in dan bukan bukti tentang LLM nyata. Bukti bahwa dokumentasi skema menaikkan akurasi LLM memerlukan uji dengan Claude API.

## Tidak didukung stand-in (batas yang diketahui)
Pengelompokan per minggu, RTY per model, pertanyaan lanjutan, dan percakapan. Satu aturan join (urutan stasiun) menghasilkan referensi kolom ambigu; tidak diperbaiki setelah hasil pertama agar hasil tidak disetel.

## Riwayat perubahan stand-in
Data v3 (29 Okt 2026) menambah data kotor 2,5% pada `production_daily`, tabel `rework_log`, dan nama stasiun sesuai rancangan. Satu aturan stand-in diubah karena itu: konfigurasi skema + KPI memakai `v_production`, sebab dokumentasi KPI kini menyebut `production_daily` kotor. Konfigurasi skema dan tanpa skema tidak diubah (tetap memakai `production_daily`, jadi jawabannya ikut salah pada baris kotor). Jawaban benar golden set dialihkan ke `v_production`. Aturan lain tidak diubah, dan aturan dibekukan lagi setelah hasil run v3 pertama; hasil run itulah yang dilaporkan.
