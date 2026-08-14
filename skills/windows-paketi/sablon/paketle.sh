#!/usr/bin/env bash
# ===========================================================================
#  {{UYGULAMA_ADI}} - Windows paketi uretir
#
#  Kullanim:  ./paketle.sh [amd64|arm64]
#
#  Uretmekle kalmaz, DENETLER. Bir kosul bozulursa paket verilmez.
#  Denetimler yontemin kalbidir: Windows'ta ancak kullanicida gorunen
#  hatalari, paket daha uretilirken yakalarlar. Yeni bir kural
#  ogrenildiginde buraya denetim ekleyin.
# ===========================================================================
set -euo pipefail

KOK="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$KOK"

MIMARI="${1:-{{MIMARI}}}"
PYSURUM="3.12.8"
PAKET="{{PAKET_KLASOR}}"
ARSIV="{{ARSIV_ADI}}"
TANI_DOSYASI="{{TANI_DOSYASI}}"
ONBELLEK="$KOK/arac/onbellek"
PYZIP="python-${PYSURUM}-embed-${MIMARI}.zip"
PYURL="https://www.python.org/ftp/python/${PYSURUM}/${PYZIP}"

# Pakette bulunmasi ZORUNLU dosyalar. Projeye gore duzenleyin: yeni bir
# modul eklendiginde buraya da yazin, yoksa eksik paket sessizce cikar.
GEREKLI_DOSYALAR=(
  "main.py"
  "app/tani.py"
  "calistir.bat"
  "kur.bat"
  "kaldir.bat"
  "tani.bat"
  "_python_bul.bat"
  "KURULUM.txt"
  "python/python.exe"
)

kirmizi() { printf '\033[31m%s\033[0m\n' "$*"; }
yesil()   { printf '\033[32m%s\033[0m\n' "$*"; }
baslik()  { printf '\n\033[1m== %s\033[0m\n' "$*"; }

HATA=0
denetim_basarisiz() { kirmizi "  HATA: $*"; HATA=1; }

# ---------------------------------------------------------------- 1) Python
baslik "Gomulu Python (${MIMARI})"
mkdir -p "$ONBELLEK"
if [[ ! -f "$ONBELLEK/$PYZIP" ]]; then
  echo "  Indiriliyor: $PYURL"
  if ! curl -fsSL -o "$ONBELLEK/$PYZIP.gecici" "$PYURL"; then
    rm -f "$ONBELLEK/$PYZIP.gecici"
    kirmizi "  Indirilemedi. Ag erisimi yoksa zip'i elle su konuma koyun:"
    kirmizi "    $ONBELLEK/$PYZIP"
    exit 1
  fi
  mv "$ONBELLEK/$PYZIP.gecici" "$ONBELLEK/$PYZIP"
  echo "  Onbellege alindi."
else
  echo "  Onbellekten kullaniliyor: $PYZIP"
fi

# ------------------------------------------------------------- 2) Kopyala
baslik "Kaynak kopyalaniyor"
rm -rf "$PAKET"
mkdir -p "$PAKET"

# Linux'a ozgu dosyalar ve kullanici verisi disarida birakilir.
# .DS_Store macOS'ta surekli yeniden dogar; tek tek silmek yerine
# kopyalama sirasinda disarida birakmak kalici cozumdur.
DISARIDA=(
  '.git' '__pycache__' '*.pyc' '.DS_Store'
  '*.sh' '*.desktop' '*.db' '*.zip' '*.onceki' '*.tmp'
  'windows' 'arac' "$PAKET"
  'ciktilar/*' 'yedekler/*'
  # Tani ve hata raporlari kullanici verisidir: gelistirme sirasinda
  # olusanlar pakete girerse kullanici baskasinin makinesinin raporunu
  # gonderir ve teshis yanlis yere gider.
  "$TANI_DOSYASI" '*BUNU GONDERIN*'
)

if command -v rsync >/dev/null 2>&1; then
  haric=()
  for desen in "${DISARIDA[@]}"; do haric+=(--exclude="$desen"); done
  rsync -a "${haric[@]}" ./ "$PAKET/"
else
  # rsync her makinede kurulu degil; tar ile ayni isi yapar.
  haric=()
  for desen in "${DISARIDA[@]}"; do haric+=(--exclude="$desen"); done
  tar -cf - "${haric[@]}" . | (cd "$PAKET" && tar -xf -)
fi
echo "  Kaynak kopyalandi."

cp windows/*.bat "$PAKET/"
cp windows/KURULUM.txt "$PAKET/"
echo "  Windows dosyalari kondu."

if [[ -f ikon.png ]]; then
  python3 arac/png2ico.py ikon.png "$PAKET/ikon.ico" >/dev/null
  echo "  Ikon uretildi."
fi

# --------------------------------------------------------- 3) Gomulu Python
baslik "Gomulu Python yerlestiriliyor"
mkdir -p "$PAKET/python"
unzip -q "$ONBELLEK/$PYZIP" -d "$PAKET/python"

# Gomulu Python kendi klasorunun disini gormez. ._pth dosyasina uygulama
# klasorleri yazilmazsa "ModuleNotFoundError: app" alinir ve pencere
# okunacak bir sey birakmadan kapanir.
PTH="$(find "$PAKET/python" -maxdepth 1 -name 'python*._pth' | head -1)"
if [[ -z "$PTH" ]]; then
  kirmizi "  ._pth dosyasi bulunamadi; gomulu dagitim beklenenden farkli."
  exit 1
fi
{
  echo ".."
  echo "..\\lib"
  echo "..\\lib_ek"
  echo "import site"
} >> "$PTH"
echo "  ._pth genisletildi: $(basename "$PTH")"

# ------------------------------------------------------------ 4) DENETIMLER
baslik "Denetimler"

# (a) Sizmamasi gerekenler
for desen in '*.sh' '*.db' '*.desktop' '.DS_Store' '__pycache__'; do
  bulunan="$(find "$PAKET" -name "$desen" -not -path "$PAKET/python/*" \
             2>/dev/null | head -5 || true)"
  if [[ -n "$bulunan" ]]; then
    denetim_basarisiz "pakete '$desen' sizmis:"
    echo "$bulunan" | sed 's/^/    /'
  fi
done

# (b) Bulunmasi gerekenler
for dosya in "${GEREKLI_DOSYALAR[@]}"; do
  [[ -e "$PAKET/$dosya" ]] || denetim_basarisiz "eksik dosya: $dosya"
done

# (c) .bat dosyalari CRLF tasimali. LF ile biten bir .bat Windows'ta
#     "komut taninmiyor" hatalari verir; goto etiketleri bozulur.
for bat in "$PAKET"/*.bat; do
  if ! head -c 4000 "$bat" | grep -q $'\r'; then
    denetim_basarisiz "CRLF yok: $(basename "$bat")"
  fi
done

# (d) Kilavuzda Linux anlatimi kalmamali
if grep -qiE 'terminal|chmod|\./calistir\.sh|sudo|apt install' \
     "$PAKET/KURULUM.txt" 2>/dev/null; then
  denetim_basarisiz "KURULUM.txt icinde Linux anlatimi kalmis"
fi

# (e) Proxy tuzagi: kullaniciya gosterilen adres localhost olmali.
#     app/tani.py haric tutulur; o, iki adresi BILEREK karsilastirir.
sizinti="$(grep -rn 'http://127\.0\.0\.1:' "$PAKET" \
  --include='*.py' --include='*.html' --include='*.js' --include='*.txt' \
  --include='*.md' 2>/dev/null \
  | grep -v "$PAKET/python/" \
  | grep -v "$PAKET/lib/" \
  | grep -v 'app/tani.py' || true)"
if [[ -n "$sizinti" ]]; then
  denetim_basarisiz "kullaniciya gosterilen adres 127.0.0.1 (proxy tuzagi):"
  echo "$sizinti" | sed 's/^/    /'
fi

# (f) Sunucu kurallari
if ! grep -rq '"::1"' "$PAKET/app" 2>/dev/null; then
  denetim_basarisiz "sunucu ::1 dinlemiyor (localhost Windows'ta once ::1)"
fi
if ! grep -rq 'allow_reuse_address = False' "$PAKET/app" 2>/dev/null; then
  denetim_basarisiz "allow_reuse_address kapatilmamis (dolu port calinir)"
fi
if ! grep -rqi 'chrome' "$PAKET/app" "$PAKET/main.py" 2>/dev/null; then
  denetim_basarisiz "Chrome onceligi yok (kurumsal varsayilan IE olabilir)"
fi

# (g) ._pth uygulama klasorlerini gormeli
if ! grep -q '^\.\.$' "$PTH"; then
  denetim_basarisiz "._pth uygulama klasorunu gormuyor"
fi

if [[ $HATA -ne 0 ]]; then
  echo
  kirmizi "Denetimler basarisiz. Paket URETILMEDI."
  kirmizi "Duzeltmeyi KAYNAKTA yapin (paket klasorunde degil), sonra"
  kirmizi "bu betigi yeniden calistirin."
  rm -rf "$PAKET"
  exit 1
fi
yesil "  Tum denetimler gecti."

# ---------------------------------------------------------------- 5) Arsiv
baslik "Arsiv"
rm -f "$ARSIV"
zip -qr "$ARSIV" "$PAKET"
BOYUT="$(du -h "$ARSIV" | cut -f1)"
yesil "  $ARSIV  ($BOYUT)"

echo
echo "Siradaki adim: duman testi."
echo "  cp -r $PAKET /tmp/duman && cd /tmp/duman && python3 main.py"
echo "(Paketteki python/ Windows ikilisidir; burada sistem python3'u kullanin.)"
