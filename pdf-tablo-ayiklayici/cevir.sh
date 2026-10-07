#!/usr/bin/env bash
# Kullanım:  ./cevir.sh liste.pdf      →  liste.xlsx
# İlk çalıştırmada gerekli paketleri kendi klasörüne kurar (sistemi değiştirmez).
set -e
VENV="$HOME/.tablo2excel"
if [ ! -x "$VENV/bin/python" ]; then
  echo "İlk kurulum yapılıyor (bir kez)…"
  python3 -m venv "$VENV" || { echo "python3-venv eksik. Kur:  sudo apt install python3-venv"; exit 1; }
  "$VENV/bin/pip" install -q pdfplumber openpyxl
fi
exec "$VENV/bin/python" "$(dirname "$(readlink -f "$0")")/tablo2excel.py" "$@"
