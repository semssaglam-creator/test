#!/usr/bin/env bash
# ===========================================================================
#  KDV Inceleme Calismasi - Windows GUNCELLEME paketini uretir
#
#  Kullanim:  ./guncelleme_paketle.sh
#
#  Tam paketin (paketle.sh) kucuk kardesi: gomulu Python'u ve kurulum
#  malzemesini tasimaz, yalnizca PROGRAM dosyalarini (main.py, app/, web/)
#  ve bunlari kurulu uygulamanin uzerine koyan guncelle.bat'i tasir.
#  Kullanicinin makinesinde calisan bir kurulum VARSA ise yarar.
#
#  lib/ ve lib_ek/ bilerek disarida: ucuncu taraf kodu ve degismiyor.
#  Degistigi gun buraya eklenmeli, yoksa paket sessizce eksik kalir.
#
#  Uretmekle kalmaz DENETLER; bir kosul bozulursa paket vermez. Denetimler
#  yontemin kalbidir: Windows'ta ancak kullanicida gorunen hatalari, paket
#  daha uretilirken yakalarlar.
# ===========================================================================
set -euo pipefail

KOK="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$KOK"

PAKET="KDV Guncelleme"
ARSIV="KDV_Guncelleme_Windows.zip"
SABLON="$KOK/arac/guncelleme"

# Guncellemenin tasidigi program dosyalari
TASINAN=(main.py app web)

# Pakette bulunmasi ZORUNLU dosyalar
GEREKLI_DOSYALAR=(
  "guncelle.bat" "OKUBENI - ONCE BUNU OKUYUN.txt"
  "yeni/main.py" "yeni/app/web_server.py" "yeni/app/pdf_beyanname.py"
  "yeni/app/beyannameler.py" "yeni/app/tani.py" "yeni/web/index.html"
)

# guncelle.bat kopyalama sonrasi bu isareti arar; isaret kaynakta yoksa
# betik her zaman "yeni surum taninmadi" der. Ikisi birlikte degismeli.
ISARET="YENI_BICIM_SIFIRLAR"

kirmizi() { printf '\033[31m%s\033[0m\n' "$*"; }
yesil()   { printf '\033[32m%s\033[0m\n' "$*"; }
baslik()  { printf '\n\033[1m== %s\033[0m\n' "$*"; }
HATA=0
denetim_basarisiz() { kirmizi "  HATA: $*"; HATA=1; }

# ------------------------------------------------------------- 1) Kopyala
baslik "Paket kuruluyor"
rm -rf "$PAKET" "$ARSIV"
mkdir -p "$PAKET/yeni"

DISARIDA=(
  '.git' '__pycache__' '*.pyc' '.DS_Store' '*.sh' '*.zip' '*.tmp' '*.db'
  'ACILIS KAYDI.txt' '*BUNU GONDERIN*'
)
haric=()
for desen in "${DISARIDA[@]}"; do haric+=(--exclude="$desen"); done
tar -cf - "${haric[@]}" "${TASINAN[@]}" | (cd "$PAKET/yeni" && tar -xf -)
cp "$SABLON/guncelle.bat" "$SABLON/OKUBENI - ONCE BUNU OKUYUN.txt" "$PAKET/"
echo "  Program dosyalari kopyalandi: ${TASINAN[*]}"

# ------------------------------------------------------------ 2) DENETIMLER
baslik "Denetimler"

for dosya in "${GEREKLI_DOSYALAR[@]}"; do
  [[ -e "$PAKET/$dosya" ]] || denetim_basarisiz "eksik dosya: $dosya"
done

# Sizmamasi gerekenler. Guncelleme kullanicinin klasorune dogrudan
# kopyalandigi icin buraya sizan bir sey onun verisinin ustune yazar.
for desen in '*.sh' '*.db' '*.desktop' '.DS_Store' '__pycache__' '*.pyc'; do
  bulunan="$(find "$PAKET" -name "$desen" 2>/dev/null | head -5 || true)"
  [[ -z "$bulunan" ]] || { denetim_basarisiz "pakete '$desen' sizmis:"
                           echo "$bulunan" | sed 's/^/    /'; }
done

# Kullanici verisi tasiyan klasorler guncellemede HIC yer almamali:
# ciktilar, veritabani ve yedekler kullanicinin kendi calismasidir.
for klasor in ciktilar veritabani yedekler; do
  [[ ! -e "$PAKET/yeni/$klasor" ]] \
    || denetim_basarisiz "kullanici klasoru pakete girmis: $klasor"
done

# LF ile biten bir .bat Windows'ta goto etiketlerini bozar.
for bat in "$PAKET"/*.bat; do
  head -c 4000 "$bat" | grep -q $'\r' \
    || denetim_basarisiz "CRLF yok: $(basename "$bat")"
done

# Kullaniciya okutulan .txt dosyalari CRLF ve UTF-8 BOM'lu olmali:
# BOM'suz bir dosyayi eski Notepad ANSI sanar ve Turkce harfler bozuk
# gorunur - kullanici da kilavuzu okuyamaz. Agactaki KURULUM.txt boyle.
for metin in "$PAKET"/*.txt; do
  head -c 4000 "$metin" | grep -q $'\r' \
    || denetim_basarisiz "CRLF yok: $(basename "$metin")"
  head -c 3 "$metin" | grep -q $'\xef\xbb\xbf' \
    || denetim_basarisiz "UTF-8 BOM yok (Notepad Turkce harfleri bozar): $(basename "$metin")"
done

# Proxy tuzagi: kullaniciya gosterilen adres localhost olmali.
# app/tani.py haric; o, iki adresi BILEREK karsilastirir.
sizinti="$(grep -rn 'http://127\.0\.0\.1:' "$PAKET" --include='*.py' \
  --include='*.html' --include='*.js' --include='*.txt' --include='*.md' \
  2>/dev/null | grep -v 'app/tani.py' || true)"
[[ -z "$sizinti" ]] || { denetim_basarisiz "adres 127.0.0.1 (proxy tuzagi):"
                         echo "$sizinti" | sed 's/^/    /'; }

grep -rq '"::1"' "$PAKET/yeni/app" 2>/dev/null \
  || denetim_basarisiz "sunucu ::1 dinlemiyor (localhost Windows'ta once ::1)"
grep -rq 'allow_reuse_address = False' "$PAKET/yeni/app" 2>/dev/null \
  || denetim_basarisiz "allow_reuse_address kapatilmamis (dolu port calinir)"

# (i) ::1 dinleyen kod, "IPv6 yok" ile "port dolu" durumlarini AYIRMALI.
#     Ayrilmazsa ::1'e baglanamayan bir makinede butun portlar dolu gorunur
#     ve uygulama "Uygun port bulunamadi" deyip kapanir. Bu, tuzagi kapatan
#     duzeltmenin kendisinin actigi bir arizadir; sahada boyle cikti.
if grep -rq '"::1"' "$PAKET/yeni/app" 2>/dev/null \
   && ! grep -rq 'EADDRINUSE' "$PAKET/yeni/app" 2>/dev/null; then
  denetim_basarisiz "::1 dinleniyor ama EADDRINUSE ayrimi yok (butun portlar dolu gorunur)"
fi

# guncelle.bat'in kopyalama sonrasi aradigi isaret gercekten pakette mi.
# Bu denetim olmazsa betik her calistirmada "yeni surum taninmadi" der ve
# kullanici basarili bir guncellemeyi basarisiz sanip geri alir.
grep -rq "$ISARET" "$PAKET/yeni/app" 2>/dev/null \
  || denetim_basarisiz "guncelle.bat'in aradigi isaret ($ISARET) pakette yok"
grep -q "$ISARET" "$PAKET/guncelle.bat" 2>/dev/null \
  || denetim_basarisiz "guncelle.bat isareti ($ISARET) aramiyor"

# Guncellemenin en tehlikeli hatasi, yedek almadan uzerine yazmaktir.
grep -q 'yedekOlmadi' "$PAKET/guncelle.bat" \
  || denetim_basarisiz "guncelle.bat yedek alinamayinca durmuyor"

# Yollarda bosluk var ("KDV Inceleme Calismasi"); tirnaksiz %HEDEF% cmd
# tarafindan ilk boslukta kesilir. Uc bicim zararsizdir ve elenir:
#   - ekrana ya da kayda YAZAN satirlar (echo / rem): cmd orada komut aramaz
#   - set "VAR=%HEDEF%..." : tirnak butun atamayi sariyor
#   - %HEDEF%'ten hemen once tirnak gelen kullanimlar
# Geriye kalan, komut satirinda ciplak duran %HEDEF%'tir; aranan da odur.
tirnaksiz="$(grep -nE '(^|[^"%])%HEDEF%' "$PAKET/guncelle.bat" 2>/dev/null \
  | grep -viE '(echo|rem)[^%]*%HEDEF%' \
  | grep -viE '^[0-9]+:[[:space:]]*set "[A-Z_]+=' || true)"
[[ -z "$tirnaksiz" ]] || { denetim_basarisiz "tirnaksiz %HEDEF% (bosluklu yolda kirilir):"
                           echo "$tirnaksiz" | sed 's/^/    /'; }

# Paket, kaynak agacla ayni olmali: yanlislikla eski bir kopya girmesin.
for dosya in main.py app/pdf_beyanname.py app/beyannameler.py web/index.html; do
  cmp -s "$KOK/$dosya" "$PAKET/yeni/$dosya" \
    || denetim_basarisiz "paketteki $dosya kaynaktan farkli"
done

if [[ $HATA -ne 0 ]]; then
  echo
  kirmizi "Denetimler basarisiz. Paket URETILMEDI."
  kirmizi "Duzeltmeyi KAYNAKTA yapin, sonra betigi yeniden calistirin."
  rm -rf "$PAKET"
  exit 1
fi
yesil "  Tum denetimler gecti."

# ---------------------------------------------------------------- 3) Arsiv
baslik "Arsiv"
zip -qr "$ARSIV" "$PAKET"
rm -rf "$PAKET"
yesil "  $ARSIV  ($(du -h "$ARSIV" | cut -f1))"

echo
echo "Kullanicinin yapacagi:"
echo "  1. Zip'e sag tikla > Tumunu ayikla"
echo "  2. Uygulamayi kapat"
echo "  3. Cikan klasorde guncelle.bat'a cift tikla"
