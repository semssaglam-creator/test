#!/bin/sh
# Takip PDF -> Excel başlatıcı.
# Masaüstü kısayolundan çalışınca konsol yoktur; çıktı acilis_kaydi.txt'ye yazılır.
# O dosya HİÇ oluşmadıysa betik çalıştırılamamış demektir (bkz. OKUBENI.txt).
cd "$(dirname "$0")" || exit 1
KAYIT="$(pwd)/acilis_kaydi.txt"
export PYTHONIOENCODING=utf-8

if ! command -v python3 >/dev/null 2>&1; then
    MSG="Python 3 bulunamadı. Bu uygulama Python 3 gerektirir; bilgi işlem birimine başvurun."
    echo "$(date '+%Y-%m-%d %H:%M:%S') $MSG" >>"$KAYIT"
    if command -v zenity >/dev/null 2>&1; then zenity --error --text="$MSG"
    elif command -v kdialog >/dev/null 2>&1; then kdialog --error "$MSG"
    elif command -v notify-send >/dev/null 2>&1; then notify-send "Takip PDF → Excel" "$MSG"
    else echo "$MSG"; fi
    exit 1
fi

if [ -t 1 ]; then
    exec python3 main.py          # terminalden çalıştı, çıktı zaten görünüyor
fi
python3 main.py >>"$KAYIT" 2>&1   # konsol yok: çıktıyı dosyaya yaz
