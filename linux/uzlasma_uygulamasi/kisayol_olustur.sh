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
Name=Uzlaşma Takip
Comment=VUK uzlaşma sürecini takip uygulaması
Exec=\"$KLASOR/calistir.sh\"
Icon=$KLASOR/ikon.png
Terminal=true
Categories=Office;"

echo "$DESKTOP_ICERIK" > "$MENU_DIZINI/uzlasma-takip.desktop"
chmod +x "$MENU_DIZINI/uzlasma-takip.desktop"

if [ -d "$MASAUSTU" ]; then
    echo "$DESKTOP_ICERIK" > "$MASAUSTU/uzlasma-takip.desktop"
    chmod +x "$MASAUSTU/uzlasma-takip.desktop"
    # GNOME tabanli masaustlerinde "guvenilir" isaretle (varsa)
    command -v gio >/dev/null 2>&1 && gio set "$MASAUSTU/uzlasma-takip.desktop" metadata::trusted true 2>/dev/null || true
    echo "Kisayol olusturuldu: $MASAUSTU/uzlasma-takip.desktop"
else
    echo "Masaustu klasoru bulunamadi; yalnizca uygulama menusune eklendi."
fi
echo "Uygulama menusune eklendi: $MENU_DIZINI/uzlasma-takip.desktop"
echo "Not: Masaustundeki kisayol ilk kullanimda 'Calistirmaya izin ver' onayi isteyebilir."
