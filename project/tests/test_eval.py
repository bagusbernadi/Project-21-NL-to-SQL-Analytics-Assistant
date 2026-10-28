"""Tes otomatis Project 21: guardrail, red-team set, golden set, dan integritas database. Dijalankan lewat pytest (dan oleh 09_ground_truth_check.py)."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "code"))
import pandas as pd
import pytest
import yaml
import assistant_lib as A
import common as CM

GOLD = yaml.safe_load((CM.EVAL / "golden_set.yaml").read_text(encoding="utf-8"))
RT = yaml.safe_load((CM.EVAL / "redteam_set.yaml").read_text(encoding="utf-8"))
WRITE = ("UPDATE", "DELETE", "DROP", "INSERT", "COPY", "ATTACH", "SET", "CREATE")


@pytest.fixture(scope="module")
def con():
    c = A.open_readonly()
    yield c
    c.close()


def test_golden_set_composition():
    t = pd.Series([q["type"] for q in GOLD]).value_counts().to_dict()
    assert len(GOLD) == 30 and t == {"agregasi": 8, "filter tanggal": 7, "join": 6, "definisi KPI": 6, "ambigu": 3}


@pytest.mark.parametrize("q", [q for q in GOLD if q["reference_sql"]], ids=lambda q: q["question_id"])
def test_reference_sql_runs(con, q):
    c = A.check_sql(q["reference_sql"])
    assert c["ok"], c["reason"]
    assert A.execute(con, c["sql"])[1] == "ok"


@pytest.mark.parametrize("r", RT["redteam"], ids=lambda r: r["attempt_id"])
def test_redteam_blocked(r):
    assert not A.check_sql(r["sql"])["ok"]


@pytest.mark.parametrize("r", [r for r in RT["redteam"] if r["sql"].split(None, 1)[0].upper() in WRITE], ids=lambda r: r["attempt_id"])
def test_readonly_connection_refuses_writes(r):
    c = A.open_readonly()
    with pytest.raises(Exception):
        c.execute(r["sql"])
    c.close()


def test_auto_limit_added_and_kept():
    assert A.check_sql("SELECT * FROM production_daily")["sql"].endswith(f"LIMIT {CM.AUTO_LIMIT}")
    assert A.check_sql("SELECT * FROM production_daily LIMIT 5")["auto_limit"] is False


def test_cte_name_not_treated_as_table():
    assert A.check_sql("WITH x AS (SELECT * FROM defect_log) SELECT COUNT(*) FROM x")["ok"]


def test_timeout_stops_heavy_query(con):
    df, st, _ = A.execute(con, "SELECT COUNT(*) FROM production_daily a, production_daily b, production_daily c, production_daily d")
    assert st == "timeout" and df is None


def test_ambiguous_questions_clarified_with_kpi_docs(con):
    for q in [q for q in GOLD if q["type"] == "ambigu"]:
        assert A.answer(con, q["question"], "skema_kpi")[0]["status"] == "clarification"


def test_schema_doc_contains_no_data_rows():
    assert "2026-03-02" not in A.schema_doc("skema_kpi")


def test_same_result_ignores_order_and_names():
    a = pd.DataFrame({"x": ["a", "b"], "y": [1.0, 2.0]}); b = pd.DataFrame({"p": ["b", "a"], "q": [2.0, 1.0]})
    assert A.same_result(a, b) and not A.same_result(a, b.iloc[:1])
