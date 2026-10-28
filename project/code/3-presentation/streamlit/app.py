"""Aplikasi tanya-jawab data produksi (Streamlit + Plotly). 2 halaman: Tanya data dan Hasil evaluasi.

PENTING: komponen "LLM" adalah pengganti aturan lokal (stand-in), bukan Claude API. Angka evaluasi menggambarkan stand-in dan data simulasi.
Database dibuka read-only; semua SQL melewati guardrail dan ditampilkan.
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "code"))
import pandas as pd
import plotly.express as px
import streamlit as st
import assistant_lib as A
import common as CM

RES = ROOT / "results" / "2-analysis"
EXAMPLES = ["Berapa total NG Engine Assembly minggu lalu?", "Which station has the lowest FPY?", "Berapa FPY per stasiun?", "What is the overall yield of the line?", "Berapa total defect kategori Las?", "Yield kemarin bagus nggak?"]


@st.cache_resource
def conn():
    return A.open_readonly()


def chart(df):
    if len(df) > 1 and df.shape[1] == 2 and df.iloc[:, 1].dtype.kind in "if":
        f = px.bar(df, x=df.columns[0], y=df.columns[1])
        f.update_layout(height=320)
        st.plotly_chart(f, width="stretch")


st.set_page_config(page_title="Asisten data produksi", layout="wide")
st.title("Asisten data produksi: pertanyaan biasa menjadi SQL")
st.caption("Data produksi simulasi. Penulis SQL adalah pengganti aturan lokal, bukan Claude API; angka akurasi menggambarkan pengganti itu. Angka selalu dihitung database dan SQL ditampilkan agar bisa dicek.")
page = st.sidebar.radio("Halaman", ["Tanya data", "Hasil evaluasi"])

if page == "Tanya data":
    ex = st.selectbox("Contoh pertanyaan", EXAMPLES)
    q = st.text_input("Pertanyaan", value=ex)
    cfg = st.selectbox("Konfigurasi prompt", CM.CONFIGS, index=2, format_func=lambda c: CM.CONFIG_LABEL[c])
    if st.button("Tanya"):
        log, df = A.answer(conn(), q, cfg)
        st.write(f"Status: {log['status']}")
        if log["status"] == "clarification":
            st.warning("Pertanyaan belum jelas: ukuran (misalnya FPY atau NG rate), stasiun, dan periode apa yang dimaksud?")
        elif log["status"] == "blocked":
            st.error(f"Query diblokir guardrail: {log['block_reason']}")
        elif log["status"] != "ok":
            st.error(f"Query gagal: {log['error']}")
        if log["generated_sql"]:
            st.code(log["generated_sql"], language="sql")
        if df is not None:
            st.write(f"{len(df)} baris")
            st.dataframe(df, hide_index=True, width="stretch")
            chart(df)
    with st.expander("Uji guardrail: tempel SQL apa pun"):
        raw = st.text_area("SQL", value="DELETE FROM production_daily")
        if st.button("Periksa SQL"):
            c = A.check_sql(raw)
            st.write("Diizinkan" if c["ok"] else f"Ditolak: {c['reason']}")
else:
    acc, typ = pd.read_csv(RES / "accuracy_config.csv"), pd.read_csv(RES / "accuracy_type.csv")
    fc, gs = pd.read_csv(RES / "failure_categories.csv"), pd.read_csv(RES / "guardrail_summary.csv").iloc[0]
    best = acc[acc.config == "skema_kpi"].iloc[0]
    a, b, c = st.columns(3)
    a.metric("Akurasi skema + KPI", f"{best.akurasi * 100:.1f}%")
    b.metric("Benar dari 30", f"{int(best.benar)}")
    c.metric("Red-team ditolak", f"{int(gs.ditolak_guardrail)} dari {int(gs.percobaan)}")
    st.write(f"Akurasi skema + KPI {best.akurasi * 100:.1f}% (CI 95% Wilson {best.ci_low * 100:.1f}% sampai {best.ci_high * 100:.1f}%), dari {int(best.n)} pertanyaan.")
    f = px.bar(typ, x="type", y="akurasi", color="config", barmode="group")
    f.update_layout(yaxis_tickformat=".0%", height=340)
    st.plotly_chart(f, width="stretch")
    st.dataframe(acc[["config", "benar", "n", "akurasi", "ci_low", "ci_high"]], hide_index=True, width="stretch")
    st.dataframe(fc[fc.jumlah > 0], hide_index=True, width="stretch")
