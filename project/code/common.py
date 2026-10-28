"""Konstanta dan path bersama Project 21 (NL to SQL Analytics Assistant).

ROOT = folder project/. Semua skrip memakai path dari sini. Folder hasil dibuat otomatis.
Definisi yang tidak ada di rancangan ditulis di project/docs/definitions.md dengan label ASUMSI.
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
SIM = DATA / "sim"                            # hasil generator (tidak di-commit)
DB_PATH = ROOT / "production.duckdb"          # tabel produksi dan view KPI, dibuka read-only oleh asisten (tidak di-commit)
EVAL_DB_PATH = ROOT / "evaluation.duckdb"     # golden_set dan query_log, tidak terlihat oleh asisten (tidak di-commit)
EVAL = ROOT / "eval"                          # golden_set.yaml, redteam_set.yaml (ditulis manual, di-commit)
SQL_DIR1 = ROOT / "code" / "1-data-preparation" / "sql"
RES1 = ROOT / "results" / "1-data-preparation"
RES2 = ROOT / "results" / "2-analysis"
RES3 = ROOT / "results" / "3-presentation"
OUTPUTS = ROOT / "outputs"
DOCS = ROOT / "docs"
TESTS = ROOT / "tests"
for _d in (DATA, SIM, RES1, RES2, RES3, OUTPUTS):
    _d.mkdir(parents=True, exist_ok=True)

SEED = 21
BOOT_B = 2000
ACC_TARGET = 0.85                  # rancangan: execution accuracy minimal 85%
CONFIGS = ["tanpa_skema", "skema", "skema_kpi"]
CONFIG_LABEL = {"tanpa_skema": "Tanpa skema", "skema": "Skema", "skema_kpi": "Skema + definisi KPI"}
TODAY = "2026-06-17"               # ASUMSI: tanggal acuan "hari ini" (Rabu) untuk "minggu lalu", "bulan ini", "kemarin"
AUTO_LIMIT = 1000                  # ASUMSI: LIMIT otomatis bila query tidak punya LIMIT
TIMEOUT_S = 5.0                    # ASUMSI: batas waktu eksekusi query
ALLOWED_TABLES = ["production_daily", "defect_log", "dim_defect", "dim_station",
                  "v_production", "v_kpi_station", "v_kpi_station_shift", "v_pareto_defect", "v_trend_week", "v_rty_model"]
CHARS_PER_TOKEN = 4.0              # ASUMSI: perkiraan token = panjang teks / 4
PRICE_IN_PER_M, PRICE_OUT_PER_M = 3.0, 15.0   # ASUMSI: USD per juta token (bukan harga resmi model mana pun)
MANUAL_MIN_PER_QUERY = 15.0        # ASUMSI: menit analis menulis dan menjalankan satu query manual
QUESTIONS_PER_MONTH = 200          # ASUMSI: pertanyaan data per bulan yang dijawab asisten
