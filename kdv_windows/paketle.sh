#!/usr/bin/env bash
# ===========================================================================
#  KDV Inceleme Calismasi - Windows paketini uretir
#
#  Kullanim:  ./paketle.sh [--gomulusuz] [amd64|arm64]
#
#  Bu agacin KENDISI Windows surumudur; paket, agacin paketleme
#  malzemesi cikarilmis kopyasidir. Uretmekle kalmaz DENETLER; bir kosul
#  bozulursa paket vermez. Denetimler yontemin kalbidir: Windows'ta ancak
#  kullanicida gorunen hatalari, paket daha uretilirken yakalarlar.
#  Yeni bir kural ogrenildiginde buraya denetim ekleyin.
# ===========================================================================
set -euo pipefail

KOK="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$KOK"

MIMARI="amd64"
GOMULU="evet"
for arg in "$@"; do
  case "$arg" in
    amd64|arm64) MIMARI="$arg" ;;
    # Gomulu Python'u pakete koymadan uretir; Python ilk calistirmada
    # indirilir. Kullanicinin makinesinde internet YOKSA paket acilmaz.
    --gomulusuz) GOMULU="hayir" ;;
    *) echo "bilinmeyen secenek: $arg" >&2; exit 2 ;;
  esac
done

PYSURUM="3.12.8"
PAKET="KDV Inceleme Calismasi"
ARSIV="KDV_Inceleme_Calismasi_Windows.zip"
TANI_DOSYASI="TANI RAPORU - BUNU GONDERIN.txt"
ONBELLEK="$KOK/arac/onbellek"
PYZIP="python-${PYSURUM}-embed-${MIMARI}.zip"
PYURL="https://www.python.org/ftp/python/${PYSURUM}/${PYZIP}"

# Pakette bulunmasi ZORUNLU dosyalar. Yeni bir modul eklendiginde buraya da
# yazin, yoksa eksik paket sessizce cikar.
GEREKLI_DOSYALAR=(
  "main.py" "app/tani.py" "app/web_server.py" "app/hesap.py" "app/db.py"
  "app/belge_docx.py" "app/tutanak.py" "app/sahte_belge_raporu.py"
  "app/excel_export.py" "app/fatura_oku.py" "app/pdf_beyanname.py"
  "app/vergi_beyannamesi.py" "app/beyannameler.py" "app/faturalar.py"
  "web/index.html" "lib/openpyxl/__init__.py" "lib/pypdf/__init__.py"
  "lib_ek/typing_extensions.py"
  "calistir.bat" "kur.bat" "kaldir.bat" "tani.bat" "_python_bul.bat"
  "KURULUM.txt" "KULLANIM.md"
)
[[ "$GOMULU" == "evet" ]] && GEREKLI_DOSYALAR+=("python/python.exe")

kirmizi() { printf '\033[31m%s\033[0m\n' "$*"; }
yesil()   { printf '\033[32m%s\033[0m\n' "$*"; }
baslik()  { printf '\n\033[1m== %s\033[0m\n' "$*"; }
HATA=0
denetim_basarisiz() { kirmizi "  HATA: $*"; HATA=1; }

# ---------------------------------------------------------------- 1) Python
baslik "Gomulu Python (${MIMARI})"
if [[ "$GOMULU" != "evet" ]]; then
  echo "  ATLANDI (--gomulusuz): Python ilk calistirmada indirilecek."
else
  mkdir -p "$ONBELLEK"
  if [[ ! -f "$ONBELLEK/$PYZIP" ]]; then
    echo "  Indiriliyor: $PYURL"
    if ! curl -fsSL -o "$ONBELLEK/$PYZIP.gecici" "$PYURL"; then
      rm -f "$ONBELLEK/$PYZIP.gecici"
      kirmizi "  Indirilemedi. Zip'i elle su konuma koyun:"
      kirmizi "    $ONBELLEK/$PYZIP"
      exit 1
    fi
    mv "$ONBELLEK/$PYZIP.gecici" "$ONBELLEK/$PYZIP"
  fi
  echo "  Hazir: $PYZIP"
fi

# ------------------------------------------------------------- 2) Kopyala
baslik "Paket kuruluyor"
rm -rf "$PAKET" "$ARSIV"
mkdir -p "$PAKET"

# Pakete GIRMEYECEKLER: paketleme malzemesi, gelistirme notlari, kullanici
# verisi. Not: bu agacta *.sh yalnizca paketleme betigidir; uygulamanin
# Linux surumu ayri agacta (kdv_linux) durur.
DISARIDA=(
  '.git' '__pycache__' '*.pyc' '.DS_Store' '*.sh' '*.zip' '*.tmp' '.gitignore'
  'arac' "$PAKET" 'ciktilar/*' 'yedekler/*' 'veritabani/*' '*.db'
  "$TANI_DOSYASI" '*BUNU GONDERIN*' 'ACILIS KAYDI.txt'
)
haric=()
for desen in "${DISARIDA[@]}"; do haric+=(--exclude="$desen"); done
tar -cf - "${haric[@]}" . | (cd "$PAKET" && tar -xf -)
echo "  Kaynak kopyalandi."

PTH=""
if [[ "$GOMULU" == "evet" ]]; then
  mkdir -p "$PAKET/python"
  unzip -q "$ONBELLEK/$PYZIP" -d "$PAKET/python"
  # Gomulu Python kendi klasorunun disini gormez; uygulama klasorleri
  # ._pth dosyasina yazilmazsa "ModuleNotFoundError: app" alinir.
  PTH="$(find "$PAKET/python" -maxdepth 1 -name 'python*._pth' | head -1)"
  [[ -n "$PTH" ]] || { kirmizi "  ._pth bulunamadi"; exit 1; }
  { echo ".."; echo "..\\lib"; echo "..\\lib_ek"; echo "import site"; } >> "$PTH"
  echo "  Gomulu Python konuldu."
fi

# ------------------------------------------------------------ 3) DENETIMLER
baslik "Denetimler"

for desen in '*.sh' '*.db' '*.desktop' '.DS_Store' '__pycache__'; do
  bulunan="$(find "$PAKET" -name "$desen" -not -path "$PAKET/python/*" \
             2>/dev/null | head -5 || true)"
  [[ -z "$bulunan" ]] || { denetim_basarisiz "pakete '$desen' sizmis:"
                           echo "$bulunan" | sed 's/^/    /'; }
done

for dosya in "${GEREKLI_DOSYALAR[@]}"; do
  [[ -e "$PAKET/$dosya" ]] || denetim_basarisiz "eksik dosya: $dosya"
done

# LF ile biten bir .bat Windows'ta goto etiketlerini bozar.
for bat in "$PAKET"/*.bat; do
  head -c 4000 "$bat" | grep -q $'\r' \
    || denetim_basarisiz "CRLF yok: $(basename "$bat")"
done

grep -qiE 'terminal|chmod|\./calistir\.sh|sudo|apt install' "$PAKET/KURULUM.txt" \
  2>/dev/null && denetim_basarisiz "KURULUM.txt icinde Linux anlatimi kalmis"

# Proxy tuzagi: kullaniciya gosterilen adres localhost olmali.
# app/tani.py haric; o, iki adresi BILEREK karsilastirir.
sizinti="$(grep -rn 'http://127\.0\.0\.1:' "$PAKET" --include='*.py' \
  --include='*.html' --include='*.js' --include='*.txt' --include='*.md' \
  2>/dev/null | grep -v "$PAKET/python/" | grep -v "$PAKET/lib/" \
  | grep -v 'app/tani.py' || true)"
[[ -z "$sizinti" ]] || { denetim_basarisiz "adres 127.0.0.1 (proxy tuzagi):"
                         echo "$sizinti" | sed 's/^/    /'; }

grep -rq '"::1"' "$PAKET/app" 2>/dev/null \
  || denetim_basarisiz "sunucu ::1 dinlemiyor (localhost Windows'ta once ::1)"
grep -rq 'allow_reuse_address = False' "$PAKET/app" 2>/dev/null \
  || denetim_basarisiz "allow_reuse_address kapatilmamis (dolu port calinir)"
grep -rqi 'chrome' "$PAKET/app" "$PAKET/main.py" 2>/dev/null \
  || denetim_basarisiz "Chrome onceligi yok"

# .bat icindeki Python cagrilari tirnakli olmali: klasor yolunda BOSLUK
# olabilir ve tirnaksiz yazilirsa cmd yolu ilk boslukta keser.
# Desen satir basini da kapsamali; echo/rem satirlari zararsizdir.
# Ekrana ya da kayda YAZAN satirlar (echo / rem) zararsizdir: cmd orada
# komut aramaz. Elenen sey, %PYEXE%'den once echo ya da rem gecen satirdir.
tirnaksiz="$(grep -nE '(^|[^"])%PYEXE%' "$PAKET"/*.bat 2>/dev/null \
  | grep -viE '(echo|rem)[^%]*%PYEXE%' || true)"
[[ -z "$tirnaksiz" ]] || { denetim_basarisiz "tirnaksiz %PYEXE% (bosluklu yolda kirilir):"
                           echo "$tirnaksiz" | sed 's/^/    /'; }
eski_py="$(grep -n '%PY%' "$PAKET"/*.bat 2>/dev/null || true)"
[[ -z "$eski_py" ]] || { denetim_basarisiz "eski %PY% degiskeni kalmis:"
                         echo "$eski_py" | sed 's/^/    /'; }

# Yer tutucu kalmamali (sablondan uretilirken degistirilmeyen alan).
# lib/ ve lib_ek/ ucuncu taraf kodudur; icindeki {{ bizim yer tutucumuz
# degildir (typing_extensions tip sozdiziminde gecer).
kalan="$(grep -rl '{{' "$PAKET" --include='*.bat' --include='*.txt' \
         --include='*.py' 2>/dev/null \
         | grep -v "^$PAKET/lib" || true)"
[[ -z "$kalan" ]] || { denetim_basarisiz "yer tutucu kalmis:"
                       echo "$kalan" | sed 's/^/    /'; }

[[ -z "$PTH" ]] || grep -q '^\.\.$' "$PTH" \
  || denetim_basarisiz "._pth uygulama klasorunu gormuyor"

# (i) ::1 dinleyen kod, "IPv6 yok" ile "port dolu" durumlarini AYIRMALI.
#     Ayrilmazsa ::1'e baglanamayan bir makinede butun portlar dolu gorunur
#     ve uygulama "Uygun port bulunamadi" diyip kapanir. Bu, tuzagi kapatan
#     duzeltmenin kendisinin actigi bir arizadir; sahada boyle cikti.
if grep -rq '"::1"' "$PAKET/app" 2>/dev/null \
   && ! grep -rq 'EADDRINUSE' "$PAKET/app" 2>/dev/null; then
  denetim_basarisiz "::1 dinleniyor ama EADDRINUSE ayrimi yok (butun portlar dolu gorunur)"
fi

if [[ $HATA -ne 0 ]]; then
  echo
  kirmizi "Denetimler basarisiz. Paket URETILMEDI."
  kirmizi "Duzeltmeyi KAYNAKTA yapin, sonra betigi yeniden calistirin."
  rm -rf "$PAKET"
  exit 1
fi
yesil "  Tum denetimler gecti."

# ---------------------------------------------------------------- 4) Arsiv
baslik "Arsiv"
zip -qr "$ARSIV" "$PAKET"
yesil "  $ARSIV  ($(du -h "$ARSIV" | cut -f1))"

if [[ "$GOMULU" != "evet" ]]; then
  echo
  kirmizi "  DIKKAT: bu pakette gomulu Python YOK. Kullanicinin makinesinde"
  kirmizi "  Python 3.9+ kurulu olmali ya da ilk calistirmada indirilebilmeli."
fi

echo
echo "Duman testi:"
echo "  cp -r \"$PAKET\" /tmp/duman && cd /tmp/duman && python3 main.py"
