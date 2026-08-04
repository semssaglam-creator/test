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
    "$PY" -u main.py --tani
    printf '\nRapor: %s\n' "$KAYIT"
    printf 'Kapatmak icin Enter tusuna basin.\n'
    read -r _ 2>/dev/null || true
    exit 0
fi

# --- Uygulamayi calistir ----------------------------------------------------
#
# Cikti bir boru hattina verilmez: boru hatti hem tamponlama hem sinyal
# davranisini degistirir. Python dogrudan calistirilir; ekrana yazdiklari
# oldugu gibi gorunur, Ctrl+C beklendigi gibi isler.
#
# Yalnizca hata akisi (stderr) bir dosyaya alinir. Masaustu kisayolundan
# acildiginda (Terminal=false) ekrana yazilanlar hicbir yere gitmiyor; Python
# bir hatayla kapanirsa ekranda hicbir sey olmuyor ve "hic acilmiyor" gibi
# gorunuyordu. Artik gerekce hem dosyada duruyor hem pencereyle bildiriliyor.
HATA_DOSYASI="$UYG_DIZIN/baslatma_hatasi.txt"
{
    printf '===== baslatma: %s =====\n' "$(date '+%d.%m.%Y %H:%M:%S')"
    printf 'Klasor : %s\n' "$UYG_DIZIN"
    printf 'Python : %s (%s)\n' "$("$PY" -V 2>&1)" "$(command -v "$PY")"
} > "$HATA_DOSYASI" 2>/dev/null
cat "$HATA_DOSYASI" >> "$KAYIT" 2>/dev/null

# On denetim: uygulama modulleri yuklenebiliyor mu.
#
# "Hic acilmiyor" durumlarinin hemen hepsi yukleme aninda olusan bir hatadir.
# Uygulamayi exec ile calistirdigimizda (asagida) kabuk yerini Python'a
# birakir; sonrasinda hata penceresi acacak kimse kalmaz. Bu yuzden once
# ucuz bir yukleme denemesi yapilir ve hata varsa kullaniciya bildirilir.
if ! "$PY" -c "import sys, os
sys.path.insert(0, os.path.join('$UYG_DIZIN', 'lib'))
sys.path.insert(0, '$UYG_DIZIN')
import app.web_server" >> "$HATA_DOSYASI" 2>&1; then
    cat "$HATA_DOSYASI" >> "$KAYIT" 2>/dev/null
    bildir "KDV Inceleme - baslatilamadi" "Uygulama yuklenemedi.

Klasor: $UYG_DIZIN
Python: $("$PY" -V 2>&1)

$(tail -n 20 "$HATA_DOSYASI" 2>/dev/null)

Ayrinti: $HATA_DOSYASI"
    exit 1
fi

# Uygulamayi calistir. exec kullanilir: kabuk yerini Python'a birakir, boylece
# Ctrl+C ve pencere kapatma dogrudan uygulamaya ulasir (calisan surumdeki
# davranis). Hata akisi yine de dosyaya alinir ki beklenmedik bir cokme kayda
# gecsin.
exec "$PY" -u main.py 2>> "$HATA_DOSYASI"
