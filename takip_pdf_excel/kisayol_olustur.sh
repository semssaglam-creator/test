#!/bin/sh
# Masaüstüne ve uygulama menüsüne kısayol ekler.
# Uygulama klasörü taşınırsa bu betiği yeniden çalıştırmak yeterlidir.
KLASOR="$(cd "$(dirname "$0")" && pwd)"
MASAUSTU="$(xdg-user-dir DESKTOP 2>/dev/null || echo "$HOME/Desktop")"
MENU="$HOME/.local/share/applications"
mkdir -p "$MENU"
chmod +x "$KLASOR/calistir.sh" 2>/dev/null

ICERIK="[Desktop Entry]
Type=Application
Name=Takip PDF → Excel
Comment=Takip listesi PDF'ini sütunlara ayırıp Excel'e aktarır
Exec=\"$KLASOR/calistir.sh\"
Icon=x-office-spreadsheet
Terminal=false
Categories=Office;"

printf '%s\n' "$ICERIK" > "$MENU/takip-pdf-excel.desktop"
chmod +x "$MENU/takip-pdf-excel.desktop"
echo "Uygulama menüsüne eklendi."
if [ -d "$MASAUSTU" ]; then
    printf '%s\n' "$ICERIK" > "$MASAUSTU/takip-pdf-excel.desktop"
    chmod +x "$MASAUSTU/takip-pdf-excel.desktop"
    command -v gio >/dev/null 2>&1 && gio set "$MASAUSTU/takip-pdf-excel.desktop" metadata::trusted true 2>/dev/null
    echo "Masaüstüne kısayol eklendi. İlk açılışta sağ tık → 'Çalıştırmaya izin ver' gerekebilir."
fi
