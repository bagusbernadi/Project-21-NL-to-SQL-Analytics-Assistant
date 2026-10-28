#!/usr/bin/env bash
# Jalankan seluruh pipeline Project 21 dari folder project/ (data, database, dan hasil dibuat ulang).
set -euo pipefail
cd "$(dirname "$0")"
for f in code/1-data-preparation/python/*.py code/2-analysis/python/*.py code/3-presentation/python/*.py; do
  echo ">> $f"; python3 "$f" > /dev/null
done
python3 ../design-and-report/src/build_report.py
