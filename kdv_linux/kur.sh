#!/bin/sh
# KDV Inceleme Calismasi - masaustu kurulumu
#
# Uygulamayi bulundugu yerden calistirir; dosyalari sisteme kopyalamaz.
# Yalnizca uygulama menusune ve masaustune birer kisayol ekler; boylece
# uygulama tiklanarak baslatilabilir. Yonetici (root) yetkisi gerekmez.

set -e

UYG_DIZIN=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
KISAYOL_ADI="kdv-inceleme"
UYG_DIR="${XDG_DATA_HOME:-$HOME/.local/share}/applications"
IKON_DIR="${XDG_DATA_HOME:-$HOME/.local/share}/icons/hicolor/256x256/apps"

echo "KDV Inceleme Calismasi kuruluyor..."
echo "  Uygulama klasoru : $UYG_DIZIN"

# --- On kosul: Python 3 -----------------------------------------------------
if ! command -v python3 >/dev/null 2>&1; then
    echo ""
    echo "HATA: Python 3 bulunamadi. Once Python 3 kurun:"
    echo "  Ubuntu / Debian / Mint : sudo apt install python3"
    echo "  Fedora                 : sudo dnf install python3"
    echo "  openSUSE               : sudo zypper install python3"
    echo "  Arch / Manjaro         : sudo pacman -S python"
    exit 1
fi

# --- Betikleri calistirilabilir yap -----------------------------------------
chmod +x "$UYG_DIZIN/calistir.sh" "$UYG_DIZIN/kur.sh" "$UYG_DIZIN/kaldir.sh" 2>/dev/null || true

# --- Ikonu yerlestir --------------------------------------------------------
mkdir -p "$IKON_DIR"
cp -f "$UYG_DIZIN/ikon.png" "$IKON_DIR/$KISAYOL_ADI.png"

# --- Masaustu girdisini olustur ---------------------------------------------
#
# Kisayol calistir.sh'i degil dogrudan "python3 main.py" komutunu calistirir.
# Sebep: dosyalar kopyalanip yapistirilarak guncellendiginde calistir.sh'in
# "calistirilabilir" isareti kaybolabiliyor; kisayol o zaman betigi
# calistiramiyor ve ekranda hicbir sey olmuyor. main.py'nin boyle bir isarete
# ihtiyaci yok, python3 zaten PATH uzerinde. Path= satiri calisma klasorunu
# belirledigi icin goreli komut yeterlidir.
mkdir -p "$UYG_DIR"
MASAUSTU_GIRDI="$UYG_DIR/$KISAYOL_ADI.desktop"
cat > "$MASAUSTU_GIRDI" <<GIRDI
[Desktop Entry]
Type=Application
Version=1.0
Name=KDV İnceleme Çalışması
GenericName=KDV beyan kontrolü
Comment=KDV beyannamelerini kontrol eder, matrah ve indirim eleştirilerini dönemler arası devir zinciriyle hesaplar
Exec=python3 main.py
Path=$UYG_DIZIN
Icon=$KISAYOL_ADI
Terminal=false
Categories=Office;Finance;Spreadsheet;
Keywords=KDV;vergi;beyanname;inceleme;matrah;devir;
StartupNotify=true
GIRDI
chmod +x "$MASAUSTU_GIRDI"

# --- Masaustune kisayol koy -------------------------------------------------
MASAUSTU_DIZIN=""
if command -v xdg-user-dir >/dev/null 2>&1; then
    MASAUSTU_DIZIN=$(xdg-user-dir DESKTOP 2>/dev/null || true)
fi
if [ -z "$MASAUSTU_DIZIN" ] || [ ! -d "$MASAUSTU_DIZIN" ]; then
    for aday in "$HOME/Masaüstü" "$HOME/Desktop" "$HOME/Masaustu"; do
        [ -d "$aday" ] && MASAUSTU_DIZIN="$aday" && break
    done
fi

if [ -n "$MASAUSTU_DIZIN" ] && [ -d "$MASAUSTU_DIZIN" ]; then
    cp -f "$MASAUSTU_GIRDI" "$MASAUSTU_DIZIN/$KISAYOL_ADI.desktop"
    chmod +x "$MASAUSTU_DIZIN/$KISAYOL_ADI.desktop"
    # GNOME/Nautilus kisayolu "guvenilir" isaretlenmedikce calistirmaz
    if command -v gio >/dev/null 2>&1; then
        gio set "$MASAUSTU_DIZIN/$KISAYOL_ADI.desktop" metadata::trusted true 2>/dev/null || true
    fi
    echo "  Masaustu kisayolu: $MASAUSTU_DIZIN/$KISAYOL_ADI.desktop"
fi

# --- Onbellekleri tazele ----------------------------------------------------
command -v update-desktop-database >/dev/null 2>&1 && \
    update-desktop-database "$UYG_DIR" 2>/dev/null || true
command -v gtk-update-icon-cache >/dev/null 2>&1 && \
    gtk-update-icon-cache -f -t "${XDG_DATA_HOME:-$HOME/.local/share}/icons/hicolor" 2>/dev/null || true

echo ""
echo "Kurulum tamamlandi."
echo ""
echo "Uygulamayi su yollardan baslatabilirsiniz:"
echo "  - Uygulamalar menusunde \"KDV Inceleme Calismasi\""
[ -n "$MASAUSTU_DIZIN" ] && echo "  - Masaustundeki kisayola cift tiklayarak"
echo ""
echo "NOT: Cogu masaustunde calistir.sh dosyasina CIFT TIKLAMAK ise yaramaz;"
echo "dosya yoneticisi betikleri calistirmaz, metin duzenleyicide acar ya da"
echo "hicbir sey yapmaz. Bu yuzden kisayol kullanin."
echo ""
echo "Menude gorunmezse oturumu kapatip acin."
echo "Kaldirmak icin: ./kaldir.sh"

# --- Kurulumdan sonra uygulamayi hemen ac -----------------------------------
#
# Boylece tek bir komut hem kurar hem acar; kullanicinin ayrica bir sey
# tiklamasi gerekmez ve kurulumun ise yarayip yaramadigi aninda gorunur.
# set -e devrede oldugu icin basarisizlik kurulumu gecersiz kilmasin diye
# ayri bir kabukta ve korumali calistirilir.
echo ""
echo "Uygulama baslatiliyor..."
exec "$UYG_DIZIN/calistir.sh"
