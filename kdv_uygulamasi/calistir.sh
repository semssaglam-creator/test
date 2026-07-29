#!/bin/sh
# KDV Inceleme Calismasi - baslatici
cd "$(dirname "$0")" || exit 1
exec python3 main.py
