#!/bin/sh
# KDV Inceleme Calismasi - baslatici
#
# Uygulamayi baslatir ve varsayilan tarayicida acar.
# Menuden veya masaustu kisayolundan tiklandiginda da bu betik calisir.
#
# ONEMLI: Masaustu kisayolundan acildiginda (Terminal=false) uygulamanin
# ekrana yazdiklari hicbir yere gitmez. Python bir hatayla kapanirsa ekranda
# hicbir sey olmaz ve "hic acilmiyor" gorunur. Bu yuzden butun cikti bir
# kayit dosyasina alinir ve hata durumunda kullaniciya pencereyle bildirilir.

UYG_DIZIN=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
cd "$UYG_DIZIN" || exit 1
KAYIT="$UYG_DIZIN/baslatma_kaydi.txt"

# --- Kullaniciya pencereyle (yoksa terminalde) mesaj gosterir ---------------
bildir() {
    BASLIK="$1"
    METIN="$2"
    if [ -n "$DISPLAY" ] || [ -n "$WAYLAND_DISPLAY" ]; then
        if command -v zenity >/dev/null 2>&1; then
            zenity --error --width=560 --title="$BASLIK" --text="$METIN" 2>/dev/null && return
        fi
        if command -v kdialog >/dev/null 2>&1; then
            kdialog --title "$BASLIK" --error "$METIN" 2>/dev/null && return
        fi
        if command -v xmessage >/dev/null 2>&1; then
            printf '%s\n' "$METIN" | xmessage -center -file - 2>/dev/null && return
        fi
        # Grafik araci yoksa bir terminal penceresi acmayi dene
        for T in x-terminal-emulator gnome-terminal konsole xfce4-terminal xterm; do
            if command -v "$T" >/dev/null 2>&1; then
                "$T" -e sh -c "printf '%s\n' \"\$1\"; printf '\nKapatmak icin Enter.\n'; read _" sh "$METIN" 2>/dev/null && return
            fi
        done
    fi
    printf '%s\n' "$METIN" >&2
}

# --- Python 3 var mi -------------------------------------------------------
PY=""
for ADAY in python3 python; do
    if command -v "$ADAY" >/dev/null 2>&1; then
        if "$ADAY" -c 'import sys; sys.exit(0 if sys.version_info >= (3, 8) else 1)' 2>/dev/null; then
            PY="$ADAY"
            break
        fi
    fi
done

if [ -z "$PY" ]; then
    bildir "KDV Inceleme" "Python 3 bulunamadi (ya da surumu cok eski).

Bu uygulama Python 3.8 veya uzerini gerektirir.
Beyanname PDF'lerini okuyabilmek icin 3.9 onerilir.

Kurmak icin:
  Ubuntu / Debian / Mint : sudo apt install python3
  Fedora                 : sudo dnf install python3
  openSUSE               : sudo zypper install python3
  Arch / Manjaro         : sudo pacman -S python"
    exit 1
fi

# --- Tani modu: TANI.sh buraya --tani ile gelir -----------------------------
if [ "$1" = "--tani" ]; then
    "$PY" main.py --tani
    printf '\nRapor: %s\n' "$KAYIT"
    printf 'Kapatmak icin Enter tusuna basin.\n'
    read -r _ 2>/dev/null || true
    exit 0
fi

# --- Uygulamayi calistir; ciktiyi hem ekrana hem kayda ver ------------------
{
    printf '===== baslatma: %s =====\n' "$(date '+%d.%m.%Y %H:%M:%S')"
    printf 'Klasor : %s\n' "$UYG_DIZIN"
    printf 'Python : %s (%s)\n' "$("$PY" -V 2>&1)" "$(command -v "$PY")"
} >> "$KAYIT" 2>/dev/null

# Cikti hem ekrana akar hem kayda yazilir. Komut ikamesi ($(...)) kullanilmaz:
# o, surec bitene kadar butun ciktiyi bekletir ve uygulama calisirken ekranda
# adres bile gorunmez. Cikis kodu ayri bir dosyayla tasinir (boru hattinda
# PIPESTATUS POSIX degildir).
DURUM_DOSYASI=$(mktemp 2>/dev/null || echo "$UYG_DIZIN/.cikis_kodu")
( "$PY" main.py 2>&1; echo $? > "$DURUM_DOSYASI" ) | tee -a "$KAYIT"
SONUC=$(cat "$DURUM_DOSYASI" 2>/dev/null || echo 1)
rm -f "$DURUM_DOSYASI"

if [ "$SONUC" -ne 0 ]; then
    bildir "KDV Inceleme - baslatilamadi" "Uygulama baslatilamadi (cikis kodu $SONUC).

Klasor: $UYG_DIZIN
Python: $("$PY" -V 2>&1)

$(tail -n 25 "$KAYIT" 2>/dev/null)

Ayrinti: $KAYIT"
    exit "$SONUC"
fi
