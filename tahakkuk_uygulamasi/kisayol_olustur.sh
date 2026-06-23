#!/bin/bash
# Masaustune ve uygulama menusune ikonlu kisayol ekler.
# Uygulama klasoru tasinirsa bu betigi yeniden calistirmak yeterlidir.
set -e
KLASOR="$(cd "$(dirname "$0")" && pwd)"

MASAUSTU="$(xdg-user-dir DESKTOP 2>/dev/null || echo "$HOME/Desktop")"
MENU_DIZINI="$HOME/.local/share/applications"
mkdir -p "$MENU_DIZINI"

DESKTOP_ICERIK="[Desktop Entry]
Type=Application
Name=Toplu Tahakkuk Sorgulama
Comment=Toplu tahakkuk Excel dosyalarini sorgulama uygulamasi
Exec=\"$KLASOR/calistir.sh\"
Icon=$KLASOR/ikon.png
Terminal=true
Categories=Office;"

echo "$DESKTOP_ICERIK" > "$MENU_DIZINI/tahakkuk-sorgulama.desktop"
chmod +x "$MENU_DIZINI/tahakkuk-sorgulama.desktop"

if [ -d "$MASAUSTU" ]; then
    echo "$DESKTOP_ICERIK" > "$MASAUSTU/tahakkuk-sorgulama.desktop"
    chmod +x "$MASAUSTU/tahakkuk-sorgulama.desktop"
    # GNOME tabanli masaustlerinde "guvenilir" isaretle (varsa)
    command -v gio >/dev/null 2>&1 && gio set "$MASAUSTU/tahakkuk-sorgulama.desktop" metadata::trusted true 2>/dev/null || true
    echo "Kisayol olusturuldu: $MASAUSTU/tahakkuk-sorgulama.desktop"
else
    echo "Masaustu klasoru bulunamadi; yalnizca uygulama menusune eklendi."
fi
echo "Uygulama menusune eklendi: $MENU_DIZINI/tahakkuk-sorgulama.desktop"
echo "Not: Masaustundeki kisayol ilk kullanimda 'Calistirmaya izin ver' onayi isteyebilir."
