"""Generator Report v2 (Project 21). Dijalankan paling akhir, setelah seluruh pipeline dijalankan ulang dari nol.

Input : design-and-report/src/page_v1.html (rancangan, pane Design TIDAK diubah), project/results/*.
Output: design-and-report/index.html
Angka di teks Report berasal dari CSV lewat helper report_lib (I, D, P, cs). audit() memeriksa token angka tak terdaftar.
"""
import re
import sys
from html import escape as esc
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
ROOT = REPO / "project"
sys.path.insert(0, str(ROOT / "code"))
sys.path.insert(0, str(HERE))
import pandas as pd
import common as C
import report_lib as R
from report_lib import I, D, P, cs, pill, BLUE, GREY, table, qa, legend, gbars, audit

SRC = (HERE / "page_v1.html").read_text(encoding="utf-8")
CSS_EXTRA = (HERE / "report.css").read_text(encoding="utf-8")
r1, r2, r3 = C.RES1, C.RES2, C.RES3
rd = lambda d, n, **k: pd.read_csv(d / n, **k)

dbt = rd(r1, "db_tables.csv").set_index("objek").baris; fp = rd(r1, "fingerprint_check.csv")
acc = rd(r2, "accuracy_config.csv").set_index("config"); typ = rd(r2, "accuracy_type.csv"); lang = rd(r2, "accuracy_language.csv"); cmpc = rd(r2, "config_compare.csv")
gcomp = rd(r2, "golden_composition.csv"); gref = rd(r2, "golden_reference.csv"); ev = rd(r2, "eval_results.csv", keep_default_na=False)
rt = rd(r2, "guardrail_redteam.csv"); gint = rd(r2, "guardrail_integrity.csv"); gload = rd(r2, "guardrail_load.csv"); gs = rd(r2, "guardrail_summary.csv").iloc[0]; qlim = rd(r2, "query_limit.csv").set_index("config")
fcat = rd(r2, "failure_categories.csv"); fdet = rd(r2, "failure_detail.csv", keep_default_na=False); clar = rd(r2, "clarification.csv").set_index("config")
lat = rd(r2, "latency_summary.csv").set_index("config"); cost = rd(r2, "cost.csv"); hs = rd(r2, "hours_saved.csv"); core = rd(r2, "core_crosscheck.csv", keep_default_na=False)
cx = rd(r2, "crosscheck.csv"); fct = rd(r2, "design_facts.csv", keep_default_na=False).set_index("fakta"); gx = rd(r2, "ground_truth_extra.csv"); pyt = rd(r2, "pytest_result.csv")
atest = rd(r3, "app_test.csv")
prod_head = pd.read_csv(C.SIM / "production_daily.csv").head(5)

LAB = C.CONFIG_LABEL
n_cx, n_cx_ok = int(cx.dibandingkan.sum()), int(cx.cocok.sum())
n_py, n_py_ok = len(pyt), int((pyt.hasil == "lulus").sum())
n_at, n_at_ok = len(atest), int((atest.hasil == "lulus").sum())
n_fp, n_fp_ok = int(fp.berkas.sum()), int(fp.cocok.sum())
n_core, n_core_ok = len(core), int(core.sama.sum())
a3 = acc.loc["skema_kpi"]; a2 = acc.loc["skema"]; a1 = acc.loc["tanpa_skema"]
tk = lambda c, t: typ[(typ.config == c) & (typ.type == t)].iloc[0]
lg = lambda c, l: lang[(lang.config == c) & (lang.language == l)].iloc[0]
fc = lambda c, k: int(fcat[(fcat.config == c) & (fcat.kategori == k)].jumlah.iloc[0])
cm = lambda a, b: cmpc[(cmpc.konfigurasi_a == a) & (cmpc.konfigurasi_b == b)].iloc[0]
cs_ = lambda c, m: cost[(cost.config == c) & (cost.pengali_harga == m)].iloc[0]
h5 = hs[hs.dasar == 1].iloc[0]
TYPES = ["agregasi", "filter tanggal", "join", "definisi KPI", "ambigu"]
fails3 = fdet[fdet.config == "skema_kpi"]


def pv(p):
    p = float(p)
    return "< 0,001" if p < 0.001 else D(p, 3)


def kp(v, l, d, color):
    return f'<div class="card kpi" style="--h:var(--{color})"><span class="v">{v}</span><span class="l">{l}</span><span class="d">{d}</span></div>'


cic = lambda r: f"{D(r.ci_low * 100, 1)}% sampai {D(r.ci_high * 100, 1)}%"
weak_skema = [t for t in TYPES if tk("skema", t).akurasi == 0]
weak3 = ", ".join(f"{r.question_id} ({r.type}, {r.failure})" for r in fails3.itertuples())
n_blocked_noschema = fc("tanpa_skema", "diblokir guardrail")

chart_type = gbars([t for t in TYPES], [(LAB[c], col, [float(tk(c, t).akurasi) * 100 for t in TYPES]) for c, col in (("tanpa_skema", GREY), ("skema", "#E8710A"), ("skema_kpi", BLUE))],
                   lambda v: D(v, 0) + "%", "Grafik execution accuracy per tipe pertanyaan dan konfigurasi prompt", rot=0, ymax=100)

QS = [
    (1, "Berapa execution accuracy asisten pada golden set 30 pertanyaan?", "Utama"),
    (2, "Tipe pertanyaan apa yang paling sering salah: agregasi, filter tanggal, join, definisi KPI, atau ambigu?", "Utama"),
    (3, "Apakah menambahkan dokumentasi skema dan definisi KPI ke prompt menaikkan akurasi?", "Utama"),
    (4, "Apakah akurasi berbeda antara pertanyaan bahasa Indonesia dan bahasa Inggris?", "Pendukung"),
    (5, "Apakah semua percobaan query berbahaya (UPDATE, DELETE, tabel di luar daftar) tertolak?", "Utama"),
    (6, "Berapa persen query yang kena LIMIT otomatis atau timeout?", "Pendukung"),
    (7, "Apa pola kegagalan utama: SQL error, query jalan tetapi hasil salah, atau pertanyaan ambigu?", "Utama"),
    (8, "Apakah asisten meminta klarifikasi saat pertanyaan ambigu, bukan menebak?", "Pendukung"),
    (9, "Berapa waktu jawab rata-rata asisten dibanding query manual analis?", "Utama"),
    (10, "Berapa biaya API per 100 pertanyaan?", "Pendukung"),
    (11, "Berapa jam kerja analis per bulan yang bisa dihemat?", "Tambahan"),
    (12, "Apakah jawaban asisten untuk 5 pertanyaan bisnis inti sama dengan dashboard KPI?", "Utama"),
]
WARN = set(range(1, 13))
STAND = "Penulis SQL adalah pengganti aturan lokal, bukan Claude."
ANS = {
    1: (f"Pada konfigurasi skema + definisi KPI: {I(a3.benar)} dari {I(a3.n)} benar, execution accuracy {P(a3.akurasi, 1)} (CI Wilson {cic(a3)}), di atas target {P(C.ACC_TARGET, 0)} pada estimasi titik tetapi batas bawah CI di bawah target. "
        f"Skema saja {P(a2.akurasi, 1)}, tanpa skema {P(a1.akurasi, 1)}. {STAND} Angka menggambarkan stand-in dan golden set yang ditulis oleh orang yang sama, bukan akurasi Claude."),
    2: (f"Pada skema + KPI, kegagalan hanya di tipe join ({I(tk('skema_kpi', 'join').benar)} dari {I(tk('skema_kpi', 'join').n)}): {weak3}. Pada konfigurasi skema saja, tipe terlemah adalah " + " dan ".join(f"{t} ({I(tk('skema', t).benar)} dari {I(tk('skema', t).n)})" for t in weak_skema) + f". Tanpa skema semua tipe 0. Satu kegagalan join berasal dari aturan stand-in yang dibiarkan (referensi kolom ambigu), jadi bukan pola LLM."),
    3: (f"Ya pada stand-in: {I(a1.benar)} menjadi {I(a2.benar)} lalu {I(a3.benar)} dari {I(a3.n)} (McNemar eksak p {pv(cm('tanpa_skema', 'skema').p_mcnemar_eksak)} dan {pv(cm('skema', 'skema_kpi').p_mcnemar_eksak)}). "
        f"Perbedaan konfigurasi adalah pilihan pemodelan stand-in (docs/llm_standin.md), sehingga ini belum bukti bahwa dokumentasi skema menaikkan akurasi Claude."),
    4: (f"Pada skema + KPI: bahasa Indonesia {I(lg('skema_kpi', 'id').benar)} dari {I(lg('skema_kpi', 'id').n)} ({cic(lg('skema_kpi', 'id'))}), bahasa Inggris {I(lg('skema_kpi', 'en').benar)} dari {I(lg('skema_kpi', 'en').n)} ({cic(lg('skema_kpi', 'en'))}); Fisher p {pv(lg('skema_kpi', 'id').p_fisher)}. "
        f"Tidak ada perbedaan yang terbukti; satu-satunya kegagalan ada pada pertanyaan berbahasa Inggris tetapi bukan karena bahasa. Sampel per bahasa kecil dan kosakata stand-in untuk dua bahasa ditulis penulis."),
    5: (f"{I(gs.ditolak_guardrail)} dari {I(gs.percobaan)} percobaan berbahaya ditolak guardrail (CI Wilson batas bawah {P(gs.ci_low, 1)}); checksum {I(len(gint))} tabel sama sebelum dan sesudah, tabel berubah {I(gs.tabel_berubah)}. "
        f"Tanpa guardrail, koneksi read-only saja menolak {I(gs.ditolak_read_only_saja)} dari {I(gs.percobaan)} (SELECT berbahaya seperti membaca file masih lolos); dengan akses file dimatikan {I(gs.ditolak_akses_file_mati)} dari {I(gs.percobaan)}. Red-team set ditulis penulis yang sama dengan guardrail."),
    6: (f"Pada skema + KPI, {I(qlim.loc['skema_kpi', 'limit_otomatis'])} dari {I(qlim.loc['skema_kpi', 'query_dijalankan'])} query dijalankan kena LIMIT otomatis ({P(qlim.loc['skema_kpi', 'limit_otomatis'] / qlim.loc['skema_kpi', 'query_dijalankan'], 1)}); hasil terpotong {I(qlim.loc['skema_kpi', 'terpotong'])} dan timeout {I(qlim.loc['skema_kpi', 'timeout'])}. "
        f"Uji beban terpisah: query berat kena timeout {D(C.TIMEOUT_S, 0)} detik dan SELECT tanpa LIMIT terpotong di {I(gload.baris.max())} baris. LIMIT dan timeout adalah asumsi (docs/definitions.md)."),
    7: (f"Skema + KPI: {I(fc('skema_kpi', 'SQL error'))} SQL error dan {I(fc('skema_kpi', 'hasil salah'))} hasil salah. Skema saja: {I(fc('skema', 'hasil salah'))} hasil salah (definisi KPI dan kalender), {I(fc('skema', 'ambigu tidak diklarifikasi'))} ambigu tidak diklarifikasi, {I(fc('skema', 'SQL error'))} SQL error. "
        f"Tanpa skema: {I(n_blocked_noschema)} diblokir guardrail karena nama tabel tebakan tidak ada di daftar, dan {I(fc('tanpa_skema', 'ambigu tidak diklarifikasi'))} ambigu tidak diklarifikasi. Pola utama: query jalan tetapi hasil salah akibat definisi, bukan SQL error. Pola ditentukan aturan stand-in."),
    8: (f"Pada skema + KPI, {I(clar.loc['skema_kpi', 'diklarifikasi'])} dari {I(clar.loc['skema_kpi', 'ambigu'])} pertanyaan ambigu diminta klarifikasi dan {I(clar.loc['skema_kpi', 'klarifikasi_pada_pertanyaan_jelas'])} pertanyaan jelas salah dikira ambigu. Pada skema saja dan tanpa skema: {I(clar.loc['skema', 'diklarifikasi'])} dari {I(clar.loc['skema', 'ambigu'])} (menebak). "
        f"Perilaku ini ditentukan instruksi klarifikasi yang hanya ada di konfigurasi skema + KPI; hanya {I(clar.loc['skema_kpi', 'ambigu'])} pertanyaan ambigu."),
    9: (f"Komponen lokal (stand-in, guardrail, database) selesai dalam kelas {I(lat.loc['skema_kpi', 'maks_komponen_lokal_ms'])} ms. Dengan asumsi latency API LLM {I(lat.loc['skema_kpi', 'asumsi_llm_detik'])} detik (tidak diukur), total sekitar {D(lat.loc['skema_kpi', 'total_asumsi_detik'], 1)} detik dibanding {I(lat.loc['skema_kpi', 'manual_menit'])} menit query manual (asumsi); rasio sekitar {D(lat.loc['skema_kpi', 'rasio_manual_vs_asisten'], 0)} kali. Latency LLM nyata belum diukur."),
    10: (f"Estimasi (estimated) {D(cs_('skema_kpi', 1.0).usd_per_100_pertanyaan, 2)} USD per 100 pertanyaan pada skema + KPI ({D(cs_('skema_kpi', 0.5).usd_per_100_pertanyaan, 2)} sampai {D(cs_('skema_kpi', 2.0).usd_per_100_pertanyaan, 2)} bila harga x0,5 sampai x2); skema saja {D(cs_('skema', 1.0).usd_per_100_pertanyaan, 2)} dan tanpa skema {D(cs_('tanpa_skema', 1.0).usd_per_100_pertanyaan, 2)}. "
         f"Token dihitung dari panjang teks / 4 dan harga {I(C.PRICE_IN_PER_M)} serta {I(C.PRICE_OUT_PER_M)} USD per juta token adalah asumsi, bukan tagihan API."),
    11: (f"Estimasi (estimated) {D(h5.jam_hemat_per_bulan, 1)} jam per bulan: {I(h5.pertanyaan_per_bulan)} pertanyaan x {P(h5.akurasi_skema_kpi, 1)} benar x {I(h5.menit_manual)} menit / 60 (rentang {D(hs.jam_hemat_per_bulan.min(), 1)} sampai {D(hs.jam_hemat_per_bulan.max(), 1)} jam untuk {I(hs.menit_manual.min())} sampai {I(hs.menit_manual.max())} menit). Volume dan menit per query adalah asumsi."),
    12: (f"{I(n_core_ok)} dari {I(n_core)} pertanyaan inti sama persis dengan view KPI (" + ", ".join(f"{r.topik}: {'sama' if r.sama else 'beda'}" for r in core.itertuples()) + f"). Yang beda adalah pengelompokan mingguan dan RTY per model yang tidak didukung stand-in; view sendiri cocok dengan pandas ({I(cx[cx.cek.str.startswith('view')].cocok.sum())} dari {I(cx[cx.cek.str.startswith('view')].dibandingkan.sum())})."),
}
n_ans = len(QS)


def qchip(n, t):
    return f'<a class="qc{" w" if n in WARN else ""}" href="#sec2{n}" title="{esc(t)}">Q{n}</a>'


def block(qs):
    return "".join(f'<span id="sec2{n}"></span>' + qa(f"Q{n}", t, p, ANS[n], status="Dengan catatan" if n in WARN else "Terjawab", warn=n in WARN) for n, t, p in QS if n in qs)


n_main = sum(1 for q in QS if q[2] == "Utama"); n_sup = sum(1 for q in QS if q[2] == "Pendukung"); n_add = sum(1 for q in QS if q[2] == "Tambahan")
sec2 = []
sec2.append(f'<div class="card"><h3>Jawaban singkat</h3><p>Semua {I(n_ans)} pertanyaan terjawab dengan angka dari data ({I(n_main)} Utama, {I(n_sup)} Pendukung, {I(n_add)} Tambahan). Semua {I(len(WARN))} jawaban diberi catatan kuning karena penulis SQL adalah pengganti aturan lokal (bukan Claude), golden set dan red-team set ditulis oleh penulis yang sama, dan sebagian angka memakai asumsi. '
            f'Pertanyaan utama project dijawab di bagian 7. Rancangan tidak memuat hipotesis formal; lima fakta data diuji di bagian 3.</p>'
            f'<p class="how">Klik nomor pertanyaan untuk melompat. Q hijau = terjawab. Q kuning = terjawab dengan catatan.</p><div class="qchips">' + "".join(qchip(n, t) for n, t, _ in QS) + '</div></div>')
sec2.append('<h3>2.1 Execution accuracy</h3><div class="card"><p>Grafik 2.1a: execution accuracy per tipe pertanyaan dan konfigurasi prompt.</p>' + chart_type + legend([(GREY, "Tanpa skema"), ("#E8710A", "Skema"), (BLUE, "Skema + definisi KPI")])
            + '<p>Tabel 2.1b: execution accuracy per konfigurasi (target 85%).</p>'
            + table(["Konfigurasi", "Benar", "Pertanyaan", "Akurasi", "CI 95% (Wilson)", "Capai target"], [[LAB[c], I(r.benar), I(r.n), P(r.akurasi, 1), cic(r), "ya" if r.capai_target else "tidak"] for c, r in acc.iterrows()])
            + '<p>Tabel 2.1c: akurasi per tipe pertanyaan.</p>'
            + table(["Konfigurasi", "Tipe", "Benar", "Pertanyaan", "Akurasi", "CI 95%"], [[LAB[r.config], r.type, I(r.benar), I(r.n), P(r.akurasi, 1), cic(r)] for r in typ.itertuples()]) + '</div>')
sec2.append(block([1, 2]))
sec2.append('<h3>2.2 Perbandingan konfigurasi dan bahasa</h3><div class="card"><p>Tabel 2.2a: perbandingan konfigurasi berpasangan (uji McNemar eksak pada 30 pertanyaan sama).</p>'
            + table(["Konfigurasi A", "Konfigurasi B", "Benar hanya A", "Benar hanya B", "Selisih akurasi", "p"], [[LAB[r.konfigurasi_a], LAB[r.konfigurasi_b], I(r.benar_hanya_a), I(r.benar_hanya_b), P(r.selisih_akurasi, 1), pv(r.p_mcnemar_eksak)] for r in cmpc.itertuples()])
            + '<p>Tabel 2.2b: akurasi per bahasa pertanyaan (Fisher eksak antar bahasa per konfigurasi).</p>'
            + table(["Konfigurasi", "Bahasa", "Benar", "Pertanyaan", "Akurasi", "CI 95%", "p Fisher"], [[LAB[r.config], "Indonesia" if r.language == "id" else "Inggris", I(r.benar), I(r.n), P(r.akurasi, 1), cic(r), pv(r.p_fisher)] for r in lang.itertuples()])
            + '<p>Tabel 2.2c: komposisi golden set.</p>' + table(["Tipe", "Pertanyaan", "Bahasa Indonesia", "Bahasa Inggris"], [[r.type, I(r.pertanyaan), I(r.indonesia), I(r.inggris)] for r in gcomp.itertuples()]) + '</div>')
sec2.append(block([3, 4]))
sec2.append('<h3>2.3 Guardrail dan batas query</h3><div class="card"><p>Tabel 2.3a: red-team set, hasil guardrail dan hasil bila guardrail dilewati.</p>'
            + table(["ID", "Jenis", "SQL", "Ditolak guardrail", "Alasan", "Read-only saja", "Read-only + akses file mati"],
                    [[r.attempt_id, r.type, f"<code>{esc(r.sql)}</code>", "ya" if r.ditolak_guardrail else "tidak", cs(r.alasan), r.read_only_saja.replace("ditolak database: ", "ditolak: "), r.read_only_akses_file_mati.replace("ditolak database: ", "ditolak: ")] for r in rt.itertuples()])
            + '<p>Tabel 2.3b: integritas tabel setelah red-team (jumlah baris dan checksum).</p>'
            + table(["Tabel", "Baris sebelum", "Baris sesudah", "Checksum sama"], [[r.tabel, I(r.baris_sebelum), I(r.baris_sesudah), "ya" if r.checksum_sama else "tidak"] for r in gint.itertuples()])
            + '<p>Tabel 2.3c: uji beban (bukan percobaan berbahaya).</p>'
            + table(["ID", "SQL", "Diizinkan", "LIMIT otomatis", "Status", "Baris", "Terpotong"], [[r.attempt_id, f"<code>{esc(r.sql)}</code>", "ya" if r.diizinkan else "tidak", "ya" if r.limit_otomatis else "tidak", r.status_eksekusi, I(r.baris), "ya" if r.terpotong else "tidak"] for r in gload.itertuples()])
            + '<p>Tabel 2.3d: LIMIT otomatis dan timeout pada query golden set yang dijalankan.</p>'
            + table(["Konfigurasi", "Query dijalankan", "LIMIT otomatis", "Terpotong", "Timeout"], [[LAB[c], I(r.query_dijalankan), I(r.limit_otomatis), I(r.terpotong), I(r.timeout)] for c, r in qlim.iterrows()]) + '</div>')
sec2.append(block([5, 6]))
sec2.append('<h3>2.4 Kegagalan dan klarifikasi</h3><div class="card"><p>Tabel 2.4a: jumlah jawaban salah menurut kategori.</p>'
            + table(["Kategori", *[LAB[c] for c in C.CONFIGS]], [[k, *[I(fc(c, k)) for c in C.CONFIGS]] for k in ["diblokir guardrail", "SQL error", "hasil salah", "ambigu tidak diklarifikasi", "klarifikasi keliru", "timeout"]])
            + '<p>Tabel 2.4b: jawaban salah pada skema + definisi KPI.</p>'
            + table(["Pertanyaan", "Tipe", "Bahasa", "Kategori", "Penyebab"], [[r.question_id, r.type, r.language, r.failure, esc(cs(r.error or r.block_reason))] for r in fails3.itertuples()])
            + '<p>Tabel 2.4c: klarifikasi pada pertanyaan ambigu.</p>'
            + table(["Konfigurasi", "Pertanyaan ambigu", "Diklarifikasi", "Klarifikasi pada pertanyaan jelas"], [[LAB[c], I(r.ambigu), I(r.diklarifikasi), I(r.klarifikasi_pada_pertanyaan_jelas)] for c, r in clar.iterrows()]) + '</div>')
sec2.append(block([7, 8]))
sec2.append('<h3>2.5 Latency, biaya, dan waktu dihemat</h3><div class="card"><p>Tabel 2.5a: latency (komponen lokal terukur, API LLM asumsi).</p>'
            + table(["Konfigurasi", "Komponen lokal maks (ms, kelas)", "Latency API (asumsi, detik)", "Total (detik)", "Query manual (menit, asumsi)", "Rasio"], [[LAB[c], I(r.maks_komponen_lokal_ms), I(r.asumsi_llm_detik), D(r.total_asumsi_detik, 1), I(r.manual_menit), D(r.rasio_manual_vs_asisten, 0)] for c, r in lat.iterrows()])
            + '<p>Tabel 2.5b: biaya per 100 pertanyaan (estimated; token dari panjang teks / 4, harga asumsi).</p>'
            + table(["Konfigurasi", "Pengali harga", "Token masukan rata-rata", "Token keluaran rata-rata", "USD per 100 pertanyaan", "Label"], [[LAB[r.config], D(r.pengali_harga, 1), D(r.token_masukan_rata, 0), D(r.token_keluaran_rata, 0), D(r.usd_per_100_pertanyaan, 2), r.label] for r in cost.itertuples()])
            + '<p>Tabel 2.5c: jam dihemat per bulan (estimated).</p>'
            + table(["Menit per query manual", "Pertanyaan per bulan", "Akurasi skema + KPI", "Jam hemat (jawaban benar)", "Jam hemat (kotor)", "Label"], [[I(r.menit_manual), I(r.pertanyaan_per_bulan), P(r.akurasi_skema_kpi, 1), D(r.jam_hemat_per_bulan, 1), D(r.jam_hemat_per_bulan_kotor, 1), r.label] for r in hs.itertuples()]) + '</div>')
sec2.append(block([9, 10, 11]))
sec2.append('<h3>2.6 Cek silang dan uji</h3><div class="card"><p>Tabel 2.6a: lima pertanyaan inti, jawaban asisten dibanding view KPI.</p>'
            + table(["ID", "Topik", "Pertanyaan", "Status", "Baris asisten", "Baris view", "Sama"], [[r.id, r.topik, esc(r.pertanyaan), r.status, I(r.baris_asisten), I(r.baris_view), pill("ya") if r.sama else pill("tidak", "d")] for r in core.itertuples()])
            + '<p>Tabel 2.6b: cek silang SQL referensi dan view KPI terhadap pandas.</p>' + table(["Pembanding", "Dibandingkan", "Cocok"], [[g, I(d.dibandingkan.sum()), I(d.cocok.sum())] for g, d in cx.groupby("cek")])
            + '<p>Tabel 2.6c: pytest.</p>' + table(["Tes", "Hasil"], [[esc(r.tes), pill("lulus") if r.hasil == "lulus" else pill(r.hasil, "d")] for r in pyt.itertuples()])
            + '<p>Tabel 2.6d: uji aplikasi (AppTest).</p>' + table(["Pemeriksaan", "Hasil"], [[esc(r.pemeriksaan), pill("lulus") if r.hasil == "lulus" else pill(r.hasil, "d")] for r in atest.itertuples()]) + '</div>')
sec2.append(block([12]))

REP = []
REP.append('<div class="callout a"><h4>Data dan penulis SQL pada project ini adalah simulasi</h4>Data produksi dibuat generator (docs/simulation_spec.md). <b>Komponen "LLM" adalah pengganti aturan lokal, bukan Claude API</b> (tidak ada API key di sesi pengerjaan; docs/llm_standin.md). Akurasi, latency LLM, dan biaya menggambarkan pengganti itu dan asumsi, bukan model nyata.</div>')
REP.append('<h2 id="rp1">1. Data yang berhasil didapatkan<small>Isi data mentah, tabel di database, dan data hasil analisis</small></h2>')
REP.append('<div class="kpis">' + kp(I(dbt["production_daily"]), "baris produksi", "10 stasiun, 3 model, 2 shift.", "navyH") + kp(I(dbt["defect_log"]), "baris defect", "20 kode defect.", "tealH")
           + kp(I(gcomp.pertanyaan.sum()), "pertanyaan golden set", "5 tipe, dua bahasa.", "amberH") + kp(I(len(rt)), "percobaan red-team", "UPDATE, DELETE, DROP, tabel luar daftar.", "plumH")
           + kp(I(n_cx), "cek silang", f"{I(n_cx_ok)} cocok.", "roseH") + kp(I(n_fp_ok), "sidik jari cocok", f"Dari {I(n_fp)} berkas, dicocokkan dengan repo DataCenter.", "skyH") + '</div>')
REP.append('<h3>1.1 Data mentah</h3><div class="card"><p>Tabel 1.1a: lima baris pertama production_daily (data simulasi).</p>'
           + table(["Tanggal", "Shift", "Stasiun", "Model", "Operator", "Input", "OK pertama", "NG"], [[r.date, r["shift"], r.station, r.model, r.operator_id, I(r.input_qty), I(r.ok_first_pass), I(r.ng_qty)] for _, r in prod_head.iterrows()])
           + '<p>Tabel 1.1b: kualitas data. Data simulasi bersih, tidak ada nilai kosong atau baris tidak valid.</p>'
           + table(["Pemeriksaan", "Hasil"], [["Baris production_daily", I(dbt["production_daily"])], ["Baris lolos view v_production", I(dbt["v_production"])], ["Baris tidak valid", I(fct.loc[5, "nilai"])]]) + '</div>')
FILES = {
    "accuracy_config.csv": "execution accuracy per konfigurasi", "accuracy_language.csv": "akurasi per bahasa", "accuracy_type.csv": "akurasi per tipe pertanyaan", "clarification.csv": "klarifikasi pertanyaan ambigu",
    "config_compare.csv": "perbandingan konfigurasi (McNemar)", "core_crosscheck.csv": "lima pertanyaan inti vs view KPI", "cost.csv": "biaya per 100 pertanyaan (estimated)", "crosscheck.csv": "cek silang SQL, view, pandas",
    "design_facts.csv": "lima fakta data rancangan", "eval_results.csv": "hasil per pertanyaan dan konfigurasi", "failure_categories.csv": "kegagalan menurut kategori", "failure_detail.csv": "detail jawaban salah",
    "golden_composition.csv": "komposisi golden set", "golden_reference.csv": "hasil SQL referensi", "ground_truth_extra.csv": "efek tertanam tambahan", "guardrail_integrity.csv": "integritas tabel setelah red-team",
    "guardrail_load.csv": "uji beban", "guardrail_redteam.csv": "hasil red-team set", "guardrail_summary.csv": "ringkasan guardrail", "hours_saved.csv": "jam dihemat (estimated)", "latency_summary.csv": "latency",
    "pytest_result.csv": "hasil pytest", "query_limit.csv": "LIMIT otomatis dan timeout"}
real = sorted(p.name for p in r2.glob("*.csv"))
assert set(real) == set(FILES), ("CSV belum terdokumentasi / tidak ada:", set(real) ^ set(FILES))
REP.append('<h3>1.2 Tabel hasil</h3><div class="card"><p>Tabel 1.2a: objek di database DuckDB (production.duckdb; golden_set dan query_log ada di evaluation.duckdb).</p>'
           + table(["Objek", "Baris"], [[k, I(v)] for k, v in dbt.items()])
           + f'<p>Tabel 1.2b: uji otomatis. pytest {I(n_py_ok)} dari {I(n_py)} lulus; aplikasi AppTest {I(n_at_ok)} dari {I(n_at)} lulus.</p>'
           + table(["Uji", "Lulus", "Jumlah"], [["pytest", I(n_py_ok), I(n_py)], ["AppTest aplikasi", I(n_at_ok), I(n_at)], ["Cek silang", I(n_cx_ok), I(n_cx)]])
           + f'<p>Tabel 1.2c: {I(len(FILES))} file hasil analisis di results/2-analysis.</p>' + table(["File", "Isi"], [[f, FILES[f]] for f in sorted(FILES)]) + '</div>')
REP.append('<h3>1.3 Angka kunci (KPI)</h3><div class="card"><p>Tabel 1.3: lima KPI.</p>'
           + table(["KPI", "Rumus ringkas", "Hasil", "Jumlah data"], [
               ["Execution accuracy (skema + KPI)", "jawaban benar / pertanyaan", P(a3.akurasi, 1), f"{I(a3.n)} pertanyaan"],
               ["Guardrail block rate", "percobaan ditolak / percobaan", P(gs.block_rate, 0), f"{I(gs.percobaan)} percobaan"],
               ["Latency (komponen lokal)", "waktu stand-in, guardrail, database", f"kelas {I(lat.loc['skema_kpi', 'maks_komponen_lokal_ms'])} ms", f"{I(a3.n)} pertanyaan"],
               ["Kegagalan per tipe", "salah / pertanyaan per tipe", f"terlemah join {P(tk('skema_kpi', 'join').akurasi, 1)}", f"{I(tk('skema_kpi', 'join').n)} pertanyaan join"],
               ["Biaya per 100 pertanyaan", "token x harga (asumsi)", f"{D(cs_('skema_kpi', 1.0).usd_per_100_pertanyaan, 2)} USD (estimated)", f"{I(a3.n)} pertanyaan"]]) + '</div>')
REP.append('<h2 id="rp2">2. Apakah business question terjawab?<small>' + f'{I(n_ans)} pertanyaan pada Design Project, dijawab dengan data' + '</small></h2>')
REP.extend(sec2)

# ---------- rp3 ----------
f1, f2, f3, f4, f5 = (fct.loc[i] for i in (1, 2, 3, 4, 5))
REP.append('<h2 id="rp3">3. Apakah dataset sesuai dengan Design Project?<small>Perbandingan rancangan dengan realisasi</small></h2>')
REP.append('<div class="card"><p class="how">Tabel 3a. Rancangan dan realisasi dataset.</p>'
           + table(["Hal", "Rancangan", "Realisasi", "Verdict"], [
               ["Sumber data", "simulasi buatan sendiri dari scripts/generate_data.py", f"00_generate_data.py (seed tetap), dibuat ulang dan dicocokkan dengan sidik jari repo DataCenter ({I(n_fp_ok)} dari {I(n_fp)} berkas)", pill("Sesuai", "")],
               ["Ukuran", "±4.500 baris produksi, ±6.000 baris defect, golden set 30, red-team ±15", f"{I(dbt['production_daily'])} baris produksi, {I(dbt['defect_log'])} baris defect, golden set {I(gcomp.pertanyaan.sum())}, red-team {I(len(rt))}", pill("Sesuai", "")],
               ["Tabel", "production_daily, defect_log, rework_log, dim_defect, golden_set, query_log", "rework_log tidak ada (generator tidak membuatnya); dim_station tambahan; golden_set dan query_log di evaluation.duckdb", pill("Sesuai + penyesuaian", "p")],
               ["Stasiun dan model", "10 stasiun dengan nama tertentu; model Matic, Bebek, Sport", "10 stasiun dengan sebagian nama berbeda (mis. Wiring Harness Install, Performance Test (Dyno)); model Matic 110, Bebek 125, Sport 150", pill("Sesuai + penyesuaian", "p")],
               ["Fakta 1: satu stasiun (Engine Assembly) paling sering NG", "Engine Assembly", f"{f1.nilai_teks} paling tinggi ({P(f1.nilai, 2)}); {f1.keterangan} ({P(f1.nilai2, 2)})", pill("Berubah", "d")],
               ["Fakta 2: lonjakan defect ±1 minggu di bulan kedua", "satu lonjakan ±1 minggu", f"lonjakan Body Panel Assembly mulai {f2.nilai_teks} (bulan data ke-{I(2)}), NG rate mingguan {P(f2.nilai, 2)} dibanding median {P(f2.nilai2, 2)}", pill("Sesuai", "")],
               ["Fakta 3: 3 pertanyaan ambigu di golden set", "3 pertanyaan", f"{I(f3.nilai)} dari {I(f3.nilai2)} pertanyaan bertipe ambigu", pill("Sesuai", "")],
               ["Fakta 4: red-team memuat UPDATE, DELETE, DROP, tabel luar daftar", "empat jenis perintah", f"{I(f4.nilai)} percobaan; jenis: {f4.nilai_teks}; {I(f4.nilai2)} percobaan tabel di luar daftar", pill("Sesuai", "")],
               ["Fakta 5: 2% sampai 3% data kotor", "data kotor tetap ada", f"{I(f5.nilai)} baris tidak valid dari {I(f5.nilai2)}; data bersih", pill("Berubah", "d")],
               ["Efek tertanam tambahan", "tidak ada di rancangan", f"NG rate Frame Painting Shift 2 {D(gx.nilai[0], 2)} kali Shift 1 (tertanam {D(gx.tertanam[0], 1)}); Sport 150 {D(gx.nilai[1], 2)} kali Matic 110 (tertanam {D(gx.tertanam[1], 2)})", pill("Tambahan", "")],
               ["Hipotesis", "tidak ada hipotesis formal pada rancangan", "lima fakta data di atas diperlakukan sebagai klaim yang diuji", pill("Tidak berlaku", "d")]]) + '</div>')

# ---------- rp4 ----------
REP.append('<h2 id="rp4">4. Apakah tools yang digunakan sesuai?<small>Perbandingan rancangan dengan eksekusi</small></h2>')
REP.append('<div class="card"><p class="how">Tabel 4a. Tools rancangan dan realisasi.</p>' + table(["Tool", "Rancangan", "Realisasi", "Verdict"], [
    ["Claude API", "LLM menulis satu query SELECT dari pertanyaan dan dokumentasi skema", "tidak dipanggil (tidak ada API key); diganti pengganti aturan lokal (StandIn) dengan antarmuka yang sama; hasil bukan akurasi Claude", pill("Diganti stand-in lokal", "d")],
    ["DuckDB + SQL", "database read-only dan view KPI", "empat tabel, lima view, koneksi read-only dengan akses file dimatikan; file database tidak di-commit", pill("Sesuai + tambahan", "")],
    ["Python (pandas)", "guardrail, eksekusi, perbandingan hasil", f"guardrail memakai parser DuckDB (json_serialize_sql), LIMIT otomatis, timeout; pandas untuk cek silang ({I(n_cx_ok)} dari {I(n_cx)} cocok)", pill("Sesuai + penyesuaian", "p")],
    ["Streamlit + Plotly", "aplikasi tanya-jawab di-deploy lewat link", f"aplikasi dua halaman diuji AppTest ({I(n_at_ok)} dari {I(n_at)} lulus); belum di-deploy", pill("Sebagian", "p")],
    ["pytest", "golden set dan red-team set sebagai tes otomatis", f"{I(n_py_ok)} dari {I(n_py)} tes lulus (guardrail, red-team, golden set, integritas)", pill("Sesuai", "")],
    ["Docker", "opsional", "tidak dibuat", pill("Tidak dibuat", "d")]]) + '</div>')
STEPS = [("1", "Menulis dokumentasi skema dan definisi KPI", "docs/schema.md", "Sesuai", ""), ("2", "Menyusun golden set", "eval/golden_set.yaml, 03_validate_golden.py", "Sesuai", ""),
         ("3", "Membuat data simulasi", "00_generate_data.py, 01_verify_fingerprint.py", "Sesuai", ""), ("4", "Memuat ke database dan membuat view KPI", "02_build_db.py, schema.sql, views.sql", "Sesuai", ""),
         ("5", "Menyusun red-team set", "eval/redteam_set.yaml", "Sesuai", ""), ("6", "Membangun pipeline text-to-SQL dan guardrail", "assistant_lib.py; LLM diganti stand-in", "Sebagian", "p"),
         ("7", "Mengevaluasi dengan golden set", "04_run_eval.py, 05_accuracy.py", "Sesuai", ""), ("8", "Menguji guardrail", "06_guardrail_test.py", "Sesuai", ""),
         ("9", "Menganalisis kegagalan", "07_failure_analysis.py", "Sesuai", ""), ("10", "Cek silang, latency, dan biaya", "08_core_cost_latency.py, 09_ground_truth_check.py", "Sesuai + tambahan", ""),
         ("11", "Membuat aplikasi tanya-jawab", "streamlit/app.py, 10_test_app.py; belum di-deploy", "Sebagian", "p"), ("12", "README dan finalisasi", "12_build_readme.py, build_report.py; branch belum di-merge", "Sebagian", "p")]
RENAMES = [("docs/schema.md", ["project/docs/schema.md"], True), ("eval/golden_set.yaml", ["project/eval/golden_set.yaml"], True), ("scripts/generate_data.py", ["project/code/1-data-preparation/python/00_generate_data.py"], True),
           ("data/raw/*.csv", ["project/data/sim"], False), ("data/ground_truth.json", ["project/data/sim/ground_truth.json"], False), ("production.duckdb", ["project/production.duckdb", "project/evaluation.duckdb"], False),
           ("eval/redteam_set.yaml", ["project/eval/redteam_set.yaml"], True), ("app/assistant.py", ["project/code/assistant_lib.py"], True), ("tests/test_eval.py", ["project/tests/test_eval.py"], True),
           ("outputs/eval_results.csv", ["project/results/2-analysis/eval_results.csv"], True), ("notebooks/analysis.ipynb", ["project/results/3-presentation/analysis.ipynb"], True),
           ("app/streamlit_app.py", ["project/code/3-presentation/streamlit/app.py"], True), (".streamlit/secrets.toml", [], True), ("requirements.txt", ["project/requirements.txt"], True),
           ("README.md", ["README.md"], True), ("index.html", ["design-and-report/index.html"], True), ("Dockerfile", [], True)]
for _, dest, committed in RENAMES:
    for d in dest:
        assert (REPO / d).exists() or d.endswith("index.html") or not committed, d
rn_rows = [[a, "(tidak dibuat)" if not dest else ", ".join(dest) + ("" if committed else " (tidak di-commit)")] for a, dest, committed in RENAMES]
REP.append('<h2 id="rp5">5. Apakah alur pengerjaan sesuai dengan Design Project?<small>' + f'{I(12)} langkah rancangan vs yang dijalankan' + '</small></h2>')
REP.append('<div class="card"><p class="how">Tabel 5a. Dua belas langkah rancangan dan yang dijalankan.</p>' + table(["No", "Langkah rancangan", "Realisasi", "Verdict"], [[n, t, r, pill(v, k)] for n, t, r, v, k in STEPS])
           + '<p>Tabel 5b: penyesuaian dan improvisasi yang tidak ada di rancangan.</p>' + table(["Penyesuaian", "Alasan"], [
               ["Pengganti LLM lokal", "tidak ada Claude API key; antarmuka dibuat sama agar LLM asli bisa dipasang (docs/llm_standin.md)"],
               ["Tiga konfigurasi sebagai model pengetahuan prompt", "perbedaan perilaku konfigurasi ditetapkan pada stand-in; hasil bukan bukti tentang LLM nyata"],
               ["Tanggal acuan, definisi yang dinilai benar, definisi KPI", "tidak ada di rancangan; asumsi di docs/definitions.md"],
               ["Koneksi read-only dengan akses file mati dan uji dua lapis", "read-only saja tidak mencegah baca file; ditemukan lewat uji tanpa guardrail"],
               ["Latency kelas 100 ms, API 3 detik, harga dan token asumsi", "hasil run ulang harus identik; LLM nyata tidak diukur"],
               ["Daftar lima pertanyaan inti", "rancangan menyebut sebagian saja (yield per stasiun, Pareto defect, tren)"],
               ["Stand-in dibekukan setelah hasil pertama", "mencegah penyetelan aturan agar akurasi naik"]])
           + '<p>Tabel 5c: perubahan nama dan lokasi file terhadap rancangan.</p>' + table(["Rancangan", "Realisasi"], rn_rows) + '</div>')
docs_list = [(a, d[0] if d else "", c) for a, d, c in RENAMES if a != "index.html"]


def doc_status(a, committed, path):
    if not path:
        return pill("Tidak dibuat", "d")
    if not committed:
        return pill("Tidak di-commit", "d")
    return pill("Ada", "") if (REPO / path).exists() else pill("Belum ada", "d")


REP.append('<h2 id="rp6">6. Apakah project output tercapai?<small>Output pada Design Project, bagian 7</small></h2>')
REP.append('<div class="card"><p class="how">Tabel 6a. Status output rancangan.</p>' + table(["Output", "Label", "Status", "Bukti"], [
    ["Aplikasi tanya-jawab data", "Utama", pill("Sebagian", "p"), f"streamlit/app.py diuji AppTest ({I(n_at_ok)} dari {I(n_at)}); belum di-deploy; penulis SQL stand-in"],
    ["Laporan evaluasi", "Utama", pill("Tercapai", ""), "halaman Hasil evaluasi di aplikasi dan CSV di results/2-analysis"],
    ["Golden set dan red-team set", "Utama", pill("Tercapai", ""), "eval/golden_set.yaml dan eval/redteam_set.yaml"],
    ["Database dan dokumentasi skema", "Utama", pill("Tercapai", ""), "schema.sql, views.sql, docs/schema.md; file .duckdb tidak di-commit"],
    ["Notebook analisis", "Utama", pill("Tercapai", ""), "results/3-presentation/analysis.ipynb"],
    ["Laporan temuan dan rekomendasi", "Utama", pill("Tercapai", ""), "README dan Report"],
    ["Repositori GitHub", "Utama", pill("Sebagian", "p"), "branch belum di-merge ke main; tanpa API key di kode"],
    ["Image Docker", "Opsional", pill("Tidak dibuat", "d"), "-"]])
    + '<p>Tabel 6b: daftar dokumen rancangan dan status pada repositori.</p>' + table(["Dokumen", "Status"], [[a, doc_status(a, c, p)] for a, p, c in docs_list]) + '</div>')

crit = [("Ketujuh pertanyaan Utama terjawab dengan angka dari evaluasi", "Terpenuhi", f"{I(n_main)} dari {I(n_main)} terjawab; semua dengan catatan stand-in dan asumsi"),
        ("Execution accuracy golden set minimal 85%, tercatat per tipe", "Sebagian", f"stand-in {P(a3.akurasi, 1)} (batas bawah CI {P(a3.ci_low, 1)}); per tipe tercatat; bukan akurasi Claude"),
        ("100% red-team set tertolak, tanpa data berubah", "Terpenuhi", f"{I(gs.ditolak_guardrail)} dari {I(gs.percobaan)} ditolak; tabel berubah {I(gs.tabel_berubah)}"),
        ("Jawaban 5 pertanyaan bisnis inti sama persis dengan view KPI", "Tidak terpenuhi", f"{I(n_core_ok)} dari {I(n_core)} sama; stand-in tidak mendukung pengelompokan mingguan dan RTY per model"),
        ("Orang awam bertanya dan membaca jawaban dalam 1 menit", "Belum diuji", "belum ada uji dengan pembaca awam; aplikasi belum di-deploy"),
        ("Checklist standar terpenuhi", "Sebagian", "aplikasi belum di-deploy; LLM nyata belum dipakai; branch belum di-merge ke main")]
n_ok_crit = sum(1 for c in crit if c[1] == "Terpenuhi")
REP.append('<h2 id="rp7">7. Kesimpulan<small>Hasil analisis, Impact, success criteria, rekomendasi, saran perbaikan, dan batasan</small></h2>')
REP.append('<h4>7.1 Hasil analisis</h4><div class="card"><p><b>Pertanyaan utama:</b> bagaimana orang non-teknis bisa bertanya data produksi dengan bahasa biasa dan mendapat angka yang benar dari database tanpa menulis SQL, dan seberapa akurat jawabannya dibanding SQL tulisan manual?</p>'
           f'<p>Alur lengkap bekerja: pertanyaan menjadi SQL, guardrail kode memeriksa, database read-only menghitung, dan hasil dibandingkan dengan SQL referensi. Dengan pengganti LLM lokal, execution accuracy {P(a3.akurasi, 1)} ({I(a3.benar)} dari {I(a3.n)}) pada skema + definisi KPI, {P(a2.akurasi, 1)} pada skema saja, dan {P(a1.akurasi, 1)} tanpa skema; '
           f'kegagalan utama adalah hasil salah akibat definisi KPI dan kalender, bukan SQL error. Semua {I(gs.percobaan)} percobaan berbahaya ditolak dan tabel tidak berubah. '
           f'Jawaban untuk {I(n_core_ok)} dari {I(n_core)} pertanyaan inti sama dengan view KPI. <b>Angka akurasi menggambarkan pengganti lokal, bukan Claude</b>; akurasi LLM nyata belum diukur.</p></div>')
REP.append('<h4>7.2 Impact</h4><div class="card">' f'<p>Estimasi (estimated): sekitar {D(h5.jam_hemat_per_bulan, 1)} jam analis per bulan ({I(h5.pertanyaan_per_bulan)} pertanyaan x {P(h5.akurasi_skema_kpi, 1)} benar x {I(h5.menit_manual)} menit / 60) dan sekitar {D(cs_("skema_kpi", 1.0).usd_per_100_pertanyaan, 2)} USD per 100 pertanyaan. '
           'Semua bergantung pada asumsi (volume, menit manual, harga, token) dan pada stand-in.</p><p>Nilai praktis: pola jawaban dengan SQL yang bisa diaudit dan guardrail berlapis. Nilai analitis: kerangka evaluasi (golden set, red-team set, perbandingan konfigurasi) yang bisa dipakai ulang untuk LLM asli. Nilai portofolio: dari data sampai aplikasi dengan uji otomatis. Belum terukur: akurasi dan latency LLM nyata, serta dampak di lantai produksi.</p></div>')
REP.append('<h4>7.3 Success criteria</h4><div class="card">' + table(["Kriteria", "Status", "Bukti"], [[k, pill(s, "" if s == "Terpenuhi" else ("p" if s in ("Sebagian", "Belum diuji") else "d")), cs(b)] for k, s, b in crit]) + f'<p>Hasil: {I(n_ok_crit)} dari {I(len(crit))} kriteria tercapai.</p></div>')
REP.append('<h4>7.4 Rekomendasi</h4><div class="card"><ul class="tight">'
           '<li>Pasang Claude API pada antarmuka StandIn.generate dan jalankan ulang golden set dan red-team set sebelum menyimpulkan akurasi.</li>'
           '<li>Pertahankan guardrail kode, koneksi read-only dengan akses file dimatikan, dan tampilkan SQL pada setiap jawaban.</li>'
           '<li>Kirim dokumentasi skema dan definisi KPI (termasuk kalender dan instruksi klarifikasi) pada prompt; jangan kirim isi data.</li>'
           '<li>Verifikasi angka kritis dengan view KPI sebelum dipakai untuk keputusan.</li></ul></div>')
REP.append('<h4>7.5 Saran perbaikan</h4><div class="card"><ul class="tight">'
           '<li>Uji dengan Claude API dan golden set yang disusun oleh orang lain, lalu perbesar golden set di atas 30 pertanyaan.</li><li>Tambahkan dukungan pengelompokan mingguan dan RTY per model, serta pertanyaan lanjutan.</li>'
           '<li>Deploy aplikasi dan uji ke pembaca awam (kriteria 1 menit); ukur latency API dan token sebenarnya.</li><li>Tambahkan tabel rework_log dan data kotor ke generator agar fakta rancangan terpenuhi.</li></ul></div>')
REP.append('<h4>7.6 Batasan</h4><div class="card"><ul class="tight">'
           '<li><b>Data adalah simulasi;</b> angka menggambarkan simulasi, bukan lini produksi.</li>'
           f'<li><b>Penulis SQL adalah pengganti aturan lokal, bukan Claude.</b> Akurasi ({P(a3.akurasi, 1)}, {P(a2.akurasi, 1)}, {P(a1.akurasi, 1)}), klarifikasi, dan pola kegagalan ditentukan aturan stand-in; latency API, token, harga, menit manual, dan volume adalah asumsi.</li>'
           f'<li>Golden set kecil ({I(a3.n)} pertanyaan; batas bawah CI {P(a3.ci_low, 1)}) dan ditulis oleh orang yang sama dengan stand-in dan guardrail; hasil optimistis. Red-team set hanya {I(len(rt))} percobaan.</li>'
           f'<li>Fakta data rancangan hanya sebagian ditanam: stasiun terburuk Frame Painting (bukan Engine Assembly), tidak ada data kotor, tidak ada tabel rework_log. {I(n_core - n_core_ok)} dari {I(n_core)} pertanyaan inti tidak sama dengan view KPI.</li>'
           '<li>Aplikasi belum di-deploy; kriteria pembaca awam belum diuji; Docker dan slide tidak dibuat; branch belum di-merge ke main. Lisensi data tidak berlaku (data karangan).</li></ul></div>')

REPORT_PANE = ('<div class="pane" id="report" data-tab="report" hidden>\n<div class="callout g"><h4>Report Project versi 2: evaluasi hasil terhadap Design Project</h4>'
               f'Cek silang: {I(n_cx_ok)} dari {I(n_cx)} cocok (SQL, view, pandas); pytest {I(n_py_ok)} dari {I(n_py)} lulus; aplikasi AppTest {I(n_at_ok)} dari {I(n_at)}. Angka diaudit dari CSV hasil. <b>Data dan penulis SQL pada project ini adalah simulasi (bukan Claude).</b></div>\n'
               + '<div class="card"><p class="how">Ringkasan tujuh pertanyaan evaluasi. Klik untuk melompat ke bagian.</p>' + table(["No", "Pertanyaan evaluasi", "Verdict", "Ringkasan"], [
                   [f'<span class="en">{i}</span>', f'<a href="#rp{i}">{t}</a>', pill(v[0], v[1]), v[2]] for i, (t, v) in enumerate([
                       ("Data yang berhasil didapatkan", ("Berhasil", "", f"{I(dbt['production_daily'])} baris produksi, {I(dbt['defect_log'])} baris defect")),
                       ("Apakah business question terjawab?", ("Sesuai", "", f"{I(n_ans)} dari {I(n_ans)} terjawab, semua dengan catatan stand-in")),
                       ("Apakah dataset sesuai dengan Design Project?", ("Sebagian", "p", "dua dari lima fakta data berubah, rework_log tidak ada")),
                       ("Apakah tools yang digunakan sesuai?", ("Berubah", "d", "Claude API diganti stand-in lokal; aplikasi belum di-deploy")),
                       ("Apakah alur pengerjaan sesuai dengan Design Project?", ("Sesuai + tambahan", "", "dua belas langkah dijalankan, tiga sebagian")),
                       ("Apakah project output tercapai?", ("Sebagian", "p", "aplikasi belum di-deploy, Docker tidak dibuat")),
                       ("Kesimpulan", ("Simulasi", "", f"akurasi {P(a3.akurasi, 1)} pada stand-in, bukan Claude"))], 1)]) + '</div>\n' + "\n".join(REP) + '\n</div>\n')

nav_src = SRC[SRC.index('<nav aria-label="Project navigation">'):SRC.index('</nav>') + 6]
btn_design = re.search(r'<button[^>]*data-t="design"[^>]*>.*?</button>', nav_src, re.S).group(0)
btn_report = re.search(r'<button[^>]*data-t="report"[^>]*>.*?</button>', nav_src, re.S).group(0)
links_design = re.search(r'<div class="links" data-tab="design">.*?</div>', nav_src, re.S).group(0)
new_report_links = ('<div class="links" data-tab="report" hidden>' + "".join(f'<a href="#rp{i}">{t}</a>' for i, t in enumerate(["Data", "Business Questions", "Dataset", "Tools", "Alur Kerja", "Project Output", "Kesimpulan"], 1)) + '</div>')
nav_new = '<nav aria-label="Project navigation">' + btn_design + btn_report + links_design + new_report_links + '</nav>'
design_pane = SRC[SRC.index('<header class="banner">'):SRC.index('<div class="pane" id="report"')]
head_end = SRC.index('</style>'); body_start = SRC.index('<body>')
hub_link = SRC[body_start:SRC.index('<main>')]
html = SRC[:head_end] + CSS_EXTRA + "\n" + SRC[head_end:body_start] + hub_link + '<main>\n' + nav_new + '\n' + design_pane + REPORT_PANE + SRC[SRC.index('</main>'):]
assert design_pane in html, "pane Design berubah"

STATIC = {str(i) for i in range(0, 41)} | {"2026", "4.500", "6.000", "85", "100", "1.1", "1.2", "1.3", "2.1", "2.2", "2.3", "2.4", "2.5", "2.6", "7.1", "7.2", "7.3", "7.4", "7.5", "7.6",
                                           "00", "01", "02", "03", "04", "05", "06", "07", "08", "09", "10", "3a", "3b", "95", "5", "3", "2,0", "0,5", "1,0", "1.000", "110", "125", "150", "0,05", "50", "60", "70", "1.0"}
n_tok, bad = audit(REPORT_PANE, STATIC)
print(f"token angka diperiksa: {n_tok}; tidak terdaftar: {len(bad)}")
if bad:
    vt = R.visible_text(REPORT_PANE)
    print("TIDAK TERDAFTAR:", bad[:80])
    for t in bad[:40]:
        m = re.search(r"(?<![\d.,])" + re.escape(t) + r"(?![\d,])", vt)
        if m:
            print("  ", t, "|", vt[max(0, m.start() - 60):m.end() + 30].replace("\n", " "))
    raise SystemExit("audit gagal: ada angka yang tidak berasal dari data")
out = HERE.parent / "index.html"
out.write_text(html, encoding="utf-8")
print("written", out, len(html))
