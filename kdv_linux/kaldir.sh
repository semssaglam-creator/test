#!/bin/sh
# KDV Inceleme Calismasi - kisayollari kaldirir
#
# Yalnizca menu ve masaustu kisayollarini siler. Uygulama klasoru, veritabani
# ve yedekler oldugu gibi kalir; klasoru silmek isterseniz elle silin.

KISAYOL_ADI="kdv-inceleme"
UYG_DIR="${XDG_DATA_HOME:-$HOME/.local/share}/applications"
IKON_DIR="${XDG_DATA_HOME:-$HOME/.local/share}/icons/hicolor/256x256/apps"

rm -f "$UYG_DIR/$KISAYOL_ADI.desktop"
rm -f "$IKON_DIR/$KISAYOL_ADI.png"

MASAUSTU_DIZIN=""
if command -v xdg-user-dir >/dev/null 2>&1; then
    MASAUSTU_DIZIN=$(xdg-user-dir DESKTOP 2>/dev/null || true)
fi
if [ -z "$MASAUSTU_DIZIN" ] || [ ! -d "$MASAUSTU_DIZIN" ]; then
    for aday in "$HOME/Masaüstü" "$HOME/Desktop" "$HOME/Masaustu"; do
        [ -d "$aday" ] && MASAUSTU_DIZIN="$aday" && break
    done
fi
[ -n "$MASAUSTU_DIZIN" ] && rm -f "$MASAUSTU_DIZIN/$KISAYOL_ADI.desktop"

command -v update-desktop-database >/dev/null 2>&1 && \
    update-desktop-database "$UYG_DIR" 2>/dev/null || true

echo "Kisayollar kaldirildi."
echo "Uygulama klasoru ve verileriniz duruyor: $(CDPATH= cd -- "$(dirname -- "$0")" && pwd)"
