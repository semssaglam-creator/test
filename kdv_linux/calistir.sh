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

# Acilis kaydi.
#
# Masaustu kisayolundan ya da dosya yoneticisinden calistirildiginda konsol
# yoktur: python3 bir hata verse bile ekrana hicbir sey gelmez ve uygulama
# "hic tepki vermedi" gorunur. Konsol yoksa cikti dosyaya yazilir.
#
# Bu dosyanin HIC olusmamasi da bir bilgidir: betik calistirilamamis
# demektir (calistirma izni yok ya da dosya yoneticisi .sh dosyalarini
# calistirmiyor). Kullanicinin bakacagi ilk sey budur.
KAYIT="$UYG_DIZIN/ACILIS KAYDI.txt"
{
    printf 'KDV Inceleme Calismasi - acilis kaydi\n'
    printf 'Tarih  : %s\n' "$(date '+%d.%m.%Y %H:%M:%S' 2>/dev/null)"
    printf 'Klasor : %s\n' "$UYG_DIZIN"
    printf 'Python : %s\n' "$(command -v python3)"
    printf '\n'
} >"$KAYIT" 2>/dev/null || true

if [ -t 1 ]; then
    # Terminalden calistirildi; ciktiyi kullanici zaten goruyor.
    exec python3 main.py
fi

# Konsol yok: ciktiyi kayda yaz ki bir aksilikte okunabilsin.
python3 main.py >>"$KAYIT" 2>&1
SONUC=$?
printf '\n[cikis kodu: %s]\n' "$SONUC" >>"$KAYIT" 2>/dev/null || true
exit "$SONUC"
