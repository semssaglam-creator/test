#!/bin/sh
# KDV Inceleme Calismasi - baslatici
#
# Uygulamayi baslatir ve varsayilan tarayicida acar.
# Menuden veya masaustu kisayolundan tiklandiginda da bu betik calisir.

UYG_DIZIN=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
cd "$UYG_DIZIN" || exit 1

# Python 3 yoksa kullaniciya anlasilir bicimde bildir
if ! command -v python3 >/dev/null 2>&1; then
    MESAJ="Python 3 bulunamadi.

Bu uygulama Python 3 gerektirir. Kurmak icin:
  Ubuntu / Debian / Mint : sudo apt install python3
  Fedora                 : sudo dnf install python3
  openSUSE               : sudo zypper install python3
  Arch / Manjaro         : sudo pacman -S python"
    if command -v zenity >/dev/null 2>&1; then
        zenity --error --width=380 --title="KDV Inceleme" --text="$MESAJ"
    elif command -v kdialog >/dev/null 2>&1; then
        kdialog --error "$MESAJ"
    else
        printf '%s\n' "$MESAJ" >&2
        printf '\nKapatmak icin Enter tusuna basin.\n'
        read -r _
    fi
    exit 1
fi

exec python3 main.py
