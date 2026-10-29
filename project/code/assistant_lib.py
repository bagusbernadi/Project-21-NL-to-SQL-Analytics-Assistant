"""Pustaka asisten NL-to-SQL Project 21: prompt, pengganti LLM lokal (stand-in), guardrail, eksekusi, dan perbandingan hasil.

PENTING: tidak ada API key Claude di sesi pengerjaan, jadi komponen "LLM" diganti pengurai aturan lokal (StandIn) yang deterministik.
Angka akurasi dari stand-in menggambarkan alat evaluasi dan aturan stand-in, BUKAN akurasi Claude. Lihat docs/llm_standin.md.
Guardrail, eksekusi read-only, LIMIT otomatis, timeout, dan perbandingan hasil adalah kode nyata dan tidak berubah bila LLM asli dipasang.
"""
import json
import re
import threading
import time
from datetime import date, datetime, timedelta

import duckdb
import pandas as pd

import common as CM

# ---------------------------------------------------------------- prompt
SYSTEM = ("Kamu menulis tepat satu query SELECT DuckDB untuk menjawab pertanyaan data produksi. Jawab hanya dengan SQL. "
          "Jangan menulis perintah selain SELECT. Hanya gunakan tabel yang tersedia.")


def _section(text, tag):
    m = re.search(rf"<!-- {tag} -->(.*?)<!-- /{tag} -->", text, re.S)
    return m.group(1).strip() if m else ""


def schema_doc(config):
    doc = (CM.DOCS / "schema.md").read_text(encoding="utf-8")
    parts = []
    if config in ("skema", "skema_kpi"):
        parts.append(_section(doc, "SKEMA"))
    if config == "skema_kpi":
        parts.append(_section(doc, "KPI").replace("{TODAY}", CM.TODAY))
    return "\n\n".join(parts)


def build_prompt(config, question):
    d = schema_doc(config)
    return SYSTEM + ("\n\n" + d if d else "") + "\n\nPertanyaan: " + question


def est_tokens(text):
    return int(-(-len(text) // CM.CHARS_PER_TOKEN))


# ---------------------------------------------------------------- stand-in LLM
EVAL_WORDS = re.compile(r"\b(bagus|baik|buruk|bermasalah|good|well|bad|problem|nggak|ngga)\b", re.I)
MONTHS = {"januari": 1, "februari": 2, "maret": 3, "april": 4, "mei": 5, "juni": 6, "juli": 7, "agustus": 8, "september": 9, "oktober": 10, "november": 11, "desember": 12,
          "january": 1, "february": 2, "march": 3, "may": 5, "june": 6, "july": 7, "august": 8, "october": 10, "december": 12}
STATIONS = ["Frame Welding", "Frame Painting", "Engine Assembly", "Engine Bench Test", "Wheel & Suspension Assembly", "Main Line Assembly", "Electrical Check", "Roller Test", "Final Inspection", "Packaging"]
MODELS = {"matic 110": "Matic 110", "bebek 125": "Bebek 125", "sport 150": "Sport 150", "matic": "Matic 110", "bebek": "Bebek 125", "sport": "Sport 150"}
CATEGORIES = ["Las", "Cat", "Mesin", "Kelistrikan", "Roda", "Body", "Kosmetik", "Performa", "Label"]
# nama yang ditebak tanpa skema (ASUMSI di docs/llm_standin.md): tabel dan kolom ukuran tidak bisa diketahui
GUESS = dict(prod="production", defect="defects", dim_defect="defect_types", dim_station="stations", input="total_input", ok="ok_count", ng="ng_count", qty="defect_count", fpy_row=None)
REAL = dict(prod="production_daily", defect="defect_log", dim_defect="dim_defect", dim_station="dim_station", input="input_qty", ok="ok_first_pass", ng="ng_qty", qty="qty")


def _today():
    return datetime.strptime(CM.TODAY, "%Y-%m-%d").date()


def parse_dates(q, config):
    """Mengembalikan (kondisi_sql_template, deskripsi) memakai kolom {d}; atau None."""
    t = _today()
    iso = re.findall(r"\d{4}-\d{2}-\d{2}", q)
    ql = q.lower()
    if len(iso) >= 2 and re.search(r"between|antara", ql):
        return f"{{d}} BETWEEN DATE '{iso[0]}' AND DATE '{iso[1]}'"
    if len(iso) == 1:
        return f"{{d}} = DATE '{iso[0]}'"
    m = re.search(r"(" + "|".join(MONTHS) + r")\s+(\d{4})", ql)
    if m:
        y, mo = int(m.group(2)), MONTHS[m.group(1)]
        s = date(y, mo, 1)
        e = date(y + (mo == 12), mo % 12 + 1, 1)
        return f"{{d}} >= DATE '{s}' AND {{d}} < DATE '{e}'"
    if re.search(r"minggu lalu|last week", ql):
        if config == "skema_kpi":
            mon = t - timedelta(days=t.weekday())
            return f"{{d}} BETWEEN DATE '{mon - timedelta(days=7)}' AND DATE '{mon - timedelta(days=1)}'"
        return f"{{d}} BETWEEN DATE '{t - timedelta(days=7)}' AND DATE '{t - timedelta(days=1)}'"        # tebakan: 7 hari terakhir
    if re.search(r"bulan ini|this month", ql):
        return f"{{d}} >= DATE '{t.replace(day=1)}' AND {{d}} <= DATE '{t}'"
    if re.search(r"bulan lalu|last month", ql):
        e = t.replace(day=1)
        s = (e - timedelta(days=1)).replace(day=1)
        return f"{{d}} >= DATE '{s}' AND {{d}} < DATE '{e}'"
    if re.search(r"kemarin|yesterday", ql):
        return f"{{d}} = DATE '{t - timedelta(days=1)}'"
    return None


def detect_measure(ql):
    if re.search(r"hari produksi|production days|jumlah hari", ql):
        return "days"
    if re.search(r"\brty\b|rolled throughput|yield of the line|yield lini|overall yield|line yield", ql):
        return "rty"
    if re.search(r"defect per 1\.?000|per 1\.?000 unit", ql):
        return "defect_per_1000"
    if re.search(r"ng rate|rasio ng", ql):
        return "ng_rate"
    if re.search(r"\bfpy\b|first pass yield|yield", ql):
        return "fpy"
    if re.search(r"rata-rata|average|\bavg\b", ql) and re.search(r"input|masuk", ql):
        return "avg_input"
    if re.search(r"passed first pass|lolos", ql):
        return "ok"
    if re.search(r"\bng\b", ql):
        return "ng"
    if "defect" in ql:
        return "defect"
    if re.search(r"input|masuk", ql):
        return "input"
    return None


class StandIn:
    """Pengganti LLM: pengurai slot (ukuran, kelompok, filter, urutan) lalu penyusun SQL. Deterministik."""

    def generate(self, question, config):
        ql = question.lower()
        n = REAL if config != "tanpa_skema" else {**REAL, **{k: v for k, v in GUESS.items() if v}}
        if config == "skema_kpi":
            n = {**n, "prod": "v_production"}                 # data v3: dokumentasi KPI memberi tahu bahwa production_daily kotor, jadi memakai view bersih
        measure = detect_measure(ql)
        if EVAL_WORDS.search(question) or measure is None:
            if config == "skema_kpi":
                return dict(sql=None, clarification="Pertanyaan belum jelas: ukuran (misalnya FPY atau NG rate), stasiun, dan periode apa yang dimaksud?")
            measure = measure or "fpy"                                    # tanpa instruksi klarifikasi: menebak
            if re.search(r"stasiun|station|bermasalah|problem", ql) and not re.search(r"line|lini", ql):
                ql += " which station lowest"
        # filter
        where_p, where_d, joins_cat = [], [], False
        st = max((s for s in STATIONS if s.lower() in ql), key=len, default=None)
        mo = next((v for k, v in sorted(MODELS.items(), key=lambda kv: -len(kv[0])) if re.search(r"\b" + re.escape(k) + r"\b", ql)), None)
        sh = re.search(r"shift\s*([12])", ql)
        cat = re.search(r"(?:kategori|category)\s+(\w+)", question, re.I)
        cat = next((c for c in CATEGORIES if cat and c.lower() == cat.group(1).lower()), None)
        dt = parse_dates(question, config)
        group = None
        if re.search(r"menurut nama defect|by defect name|which defect name|defect name", ql):
            group = "defect_name"
        elif re.search(r"production order|urutan produksi", ql):
            group = "seq"
        elif re.search(r"per (station|stasiun)|each station|which station|stasiun mana", ql):
            group = "station"
        elif re.search(r"per model", ql):
            group = "model"
        elif re.search(r"per shift", ql):
            group = "shift"
        rank = "DESC" if re.search(r"highest|tertinggi|paling banyak|terbanyak|most", ql) else ("ASC" if re.search(r"lowest|terendah|terburuk|worst|least", ql) else None)
        if rank and group is None:
            group = "station"
        pk, dk = (lambda c: c), (lambda c: c)
        is_def = measure in ("defect",) or (cat is not None)
        tab = n["defect"] if is_def else n["prod"]
        pre = "d." if (is_def and (cat or group == "defect_name")) else ""
        conds = []
        if st:
            conds.append(f"{pre}station = '{st}'")
        if mo:
            conds.append(f"{pre}model = '{mo}'")
        if sh:
            conds.append(f"{pre}shift = 'Shift {sh.group(1)}'")
        if cat:
            conds.append(f"x.category = '{cat}'")
        if dt:
            conds.append(dt.format(d=f"{pre}date"))
        w = (" WHERE " + " AND ".join(conds)) if conds else ""
        gcol = {"station": f"{pre}station", "model": f"{pre}model", "shift": f"{pre}shift", "defect_name": "x.defect_name", "seq": "s.station"}.get(group)
        # ukuran
        I_, O_, N_, Q_ = n["input"], n["ok"], n["ng"], n["qty"]
        if measure == "rty":
            sel = None
            wf = " WHERE " + " AND ".join(c for c in conds) if conds else ""
            if config == "skema_kpi":
                sql = f"WITH f AS (SELECT station, SUM({O_}) * 1.0 / SUM({I_}) AS fpy FROM {n['prod']}{wf} GROUP BY station) SELECT EXP(SUM(LN(fpy))) AS rty FROM f"
            else:
                sql = f"SELECT SUM({O_}) * 1.0 / SUM({I_}) AS rty FROM {n['prod']}{wf}"      # tebakan: yield lini = rasio jumlah
            return dict(sql=sql, clarification=None)
        if measure == "defect_per_1000":
            if config == "skema_kpi":
                wd = (" WHERE " + " AND ".join(c.replace(pre, "") for c in conds)) if conds else ""
                sql = f"SELECT (SELECT SUM({Q_}) FROM {n['defect']}{wd}) * 1000.0 / (SELECT SUM({I_}) FROM {n['prod']}{wd}) AS defect_per_1000"
            else:
                wj = (" WHERE " + " AND ".join("p." + c for c in conds)) if conds else ""
                sql = f"SELECT SUM(d.{Q_}) * 1000.0 / SUM(p.{I_}) AS defect_per_1000 FROM {n['prod']} p JOIN {n['defect']} d ON d.station = p.station AND d.date = p.date{wj}"
            return dict(sql=sql, clarification=None)
        expr = {"input": f"SUM({I_})", "ng": f"SUM({N_})", "ok": f"SUM({O_})", "avg_input": f"AVG({I_})", "defect": f"SUM({Q_})", "days": "COUNT(DISTINCT date)",
                "fpy": f"SUM({O_}) * 1.0 / SUM({I_})" if config == "skema_kpi" else f"AVG({O_} * 1.0 / {I_})",
                "ng_rate": f"SUM({N_}) * 1.0 / SUM({I_})" if config == "skema_kpi" else f"AVG({N_} * 1.0 / {I_})"}[measure]
        alias = {"days": "hari_produksi"}.get(measure, measure)
        join = ""
        if is_def and (cat or group == "defect_name"):
            join = f" JOIN {n['dim_defect']} x ON x.defect_code = d.defect_code"
            tab = f"{n['defect']} d"
        if group == "seq":
            join = f" JOIN {n['dim_station']} s ON s.station = {('d.' if is_def else '')}station"
            if not is_def:
                tab = f"{n['prod']}"
        if gcol:
            order = f"ORDER BY {alias} {rank}, {gcol}" if rank else (f"ORDER BY s.seq" if group == "seq" else f"ORDER BY {gcol}")
            lim = " LIMIT 1" if rank else ""
            grp = f" GROUP BY {gcol}" + (", s.seq" if group == "seq" else "")
            sql = f"SELECT {gcol}, {expr} AS {alias} FROM {tab}{join}{w}{grp} {order}{lim}"
        else:
            sql = f"SELECT {expr} AS {alias} FROM {tab}{join}{w}"
        return dict(sql=sql, clarification=None)


# ---------------------------------------------------------------- guardrail
_MEM = None
BLOCK_FUNCS = {"glob", "getenv", "current_setting", "query", "query_table"}


def _walk(node, out):
    if isinstance(node, dict):
        if node.get("type") == "BASE_TABLE":
            out["tables"].append((node.get("schema_name") or "", node.get("table_name") or ""))
        if node.get("type") == "TABLE_FUNCTION":
            out["tfunc"].append(True)
        if node.get("class") == "FUNCTION" or "function_name" in node:
            fn = (node.get("function_name") or "").lower()
            if fn.startswith("read_") or fn.startswith("duckdb_") or fn in BLOCK_FUNCS:
                out["funcs"].append(fn)
        cm = node.get("cte_map")
        if isinstance(cm, dict):
            for e in cm.get("map", []):
                out["ctes"].add(e.get("key", ""))
        for v in node.values():
            _walk(v, out)
    elif isinstance(node, list):
        for v in node:
            _walk(v, out)


def check_sql(sql):
    """Guardrail: satu pernyataan SELECT, tabel hanya dari daftar, tanpa fungsi file; LIMIT otomatis bila tidak ada.

    Mengembalikan dict(ok, reason, sql, auto_limit). Kode biasa, tidak diserahkan ke LLM.
    """
    global _MEM
    _MEM = _MEM or duckdb.connect()
    s = (sql or "").strip().rstrip(";").strip()
    if not s:
        return dict(ok=False, reason="query kosong", sql=sql, auto_limit=False)
    try:
        stmts = _MEM.extract_statements(s)
    except Exception as e:
        return dict(ok=False, reason=f"gagal diurai: {str(e)[:60]}", sql=sql, auto_limit=False)
    if len(stmts) != 1:
        return dict(ok=False, reason="lebih dari satu pernyataan", sql=sql, auto_limit=False)
    j = json.loads(_MEM.execute("SELECT json_serialize_sql(?)", [s]).fetchone()[0])
    if j.get("error"):
        return dict(ok=False, reason="bukan SELECT", sql=sql, auto_limit=False)
    info = dict(tables=[], tfunc=[], funcs=[], ctes=set())
    _walk(j, info)
    if info["tfunc"]:
        return dict(ok=False, reason="fungsi tabel tidak diizinkan", sql=sql, auto_limit=False)
    if info["funcs"]:
        return dict(ok=False, reason=f"fungsi tidak diizinkan: {info['funcs'][0]}", sql=sql, auto_limit=False)
    for sch, t in info["tables"]:
        if t in info["ctes"] and not sch:
            continue
        if (sch not in ("", "main")) or t not in CM.ALLOWED_TABLES:
            return dict(ok=False, reason=f"tabel di luar daftar: {(sch + '.' if sch else '') + t}", sql=sql, auto_limit=False)
    top = j["statements"][0]["node"]
    has_limit = any(m.get("type") == "LIMIT_MODIFIER" for m in top.get("modifiers", []))
    out = s if has_limit else f"{s} LIMIT {CM.AUTO_LIMIT}"
    return dict(ok=True, reason="", sql=out, auto_limit=not has_limit)


# ---------------------------------------------------------------- eksekusi
def open_readonly(hardened=True):
    """Koneksi read-only. hardened=True juga mematikan akses file dan jaringan (enable_external_access=false)."""
    cfg = {"enable_external_access": False} if hardened else {}
    return duckdb.connect(str(CM.DB_PATH), read_only=True, config=cfg)


def execute(con, sql):
    """Jalankan satu query dengan batas waktu. Mengembalikan (DataFrame | None, status_eksekusi, pesan)."""
    cur = con.cursor()
    timer = threading.Timer(CM.TIMEOUT_S, cur.interrupt)
    timer.start()
    try:
        df = cur.execute(sql).df()
        return df, "ok", ""
    except duckdb.InterruptException:
        return None, "timeout", f"melebihi {CM.TIMEOUT_S:g} detik"
    except Exception as e:
        return None, "error", str(e).splitlines()[0][:120]
    finally:
        timer.cancel()
        cur.close()


def answer(con, question, config, model=None):
    """Satu pertanyaan: prompt, stand-in LLM, guardrail, eksekusi. Mengembalikan (log dict, DataFrame | None)."""
    model = model or StandIn()
    prompt = build_prompt(config, question)
    t0 = time.perf_counter()
    g = model.generate(question, config)
    log = dict(config=config, question=question, generated_sql=g["sql"] or "", status="", block_reason="", error="", rows=0, auto_limit=False, truncated=False,
               prompt_tokens=est_tokens(prompt), completion_tokens=est_tokens(g["sql"] or g["clarification"] or ""))
    df = None
    if g["sql"] is None:
        log["status"] = "clarification"
    else:
        c = check_sql(g["sql"])
        if not c["ok"]:
            log["status"], log["block_reason"] = "blocked", c["reason"]
        else:
            log["auto_limit"] = c["auto_limit"]
            df, st, msg = execute(con, c["sql"])
            log["status"], log["error"] = st, msg
            if df is not None:
                log["rows"] = len(df)
                log["truncated"] = bool(c["auto_limit"] and len(df) >= CM.AUTO_LIMIT)
    log["latency_ms"] = (time.perf_counter() - t0) * 1000
    log["tokens"] = log["prompt_tokens"] + log["completion_tokens"]
    return log, df


def same_result(a, b):
    """Dua hasil sama bila himpunan baris sama (urutan kolom nama diabaikan, desimal dibulatkan 6 angka)."""
    if a is None or b is None or a.shape != b.shape:
        return False

    def norm(df):
        rows = []
        for r in df.itertuples(index=False):
            rows.append(tuple("NULL" if (isinstance(v, float) and pd.isna(v)) or v is None else (round(float(v), 6) if isinstance(v, (int, float)) and not isinstance(v, bool) else str(v)) for v in r))
        return sorted(rows, key=lambda x: tuple(str(i) for i in x))
    return norm(a) == norm(b)
