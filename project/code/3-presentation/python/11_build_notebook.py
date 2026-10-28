"""11: Notebook analisis Q1-Q12 (analysis.ipynb), dieksekusi tanpa error. Membaca CSV hasil."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
import nbformat as nbf
from nbclient import NotebookClient
import common as CM

nb = nbf.v4.new_notebook()
md = lambda t: nbf.v4.new_markdown_cell(t); code = lambda t: nbf.v4.new_code_cell(t)
cells = [md("# Project 21: Natural Language to SQL Analytics Assistant\nData simulasi. Penulis SQL adalah pengganti aturan lokal (bukan Claude API). Notebook membaca CSV hasil; angka tidak dihitung ulang."),
         code("from pathlib import Path\nimport pandas as pd\nR2 = Path('..') / '2-analysis'\nrd = lambda n: pd.read_csv(R2 / n)\n")]
SEC = [("Q1 sampai Q4: execution accuracy", ["accuracy_config.csv", "accuracy_type.csv", "accuracy_language.csv", "config_compare.csv"]),
       ("Q5 dan Q6: guardrail dan LIMIT", ["guardrail_summary.csv", "guardrail_redteam.csv", "guardrail_load.csv", "query_limit.csv"]),
       ("Q7 dan Q8: kegagalan dan klarifikasi", ["failure_categories.csv", "failure_detail.csv", "clarification.csv"]),
       ("Q9 sampai Q11: latency, biaya, jam dihemat (estimated)", ["latency_summary.csv", "cost.csv", "hours_saved.csv"]),
       ("Q12 dan cek silang", ["core_crosscheck.csv", "crosscheck.csv", "pytest_result.csv", "design_facts.csv"])]
for t, files in SEC:
    cells.append(md(f"## {t}"))
    for f in files:
        cells.append(code(f"print('{f}'); display(rd('{f}'))"))
cells.append(md("Akurasi per konfigurasi dan tipe"))
cells.append(code("import matplotlib.pyplot as plt\nd = rd('accuracy_type.csv').pivot(index='type', columns='config', values='akurasi')\nd.plot.bar(); plt.ylabel('execution accuracy'); plt.tight_layout(); plt.show()"))
nb.cells = cells
NotebookClient(nb, timeout=300, kernel_name="python3", resources={"metadata": {"path": str(CM.RES3)}}).execute()
nbf.write(nb, CM.RES3 / "analysis.ipynb")
print("notebook ditulis")
