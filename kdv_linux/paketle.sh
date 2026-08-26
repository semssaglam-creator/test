#!/usr/bin/env bash
# ===========================================================================
#  KDV Inceleme Calismasi - Linux paketini uretir
#
#  Kullanim:  ./paketle.sh
#
#  Bu agacin KENDISI Linux surumudur; paket, agacin paketleme malzemesi
#  cikarilmis kopyasidir. Windows surumu ayri agacta durur (kdv_windows).
#
#  Cikti .tar.gz'dir, .zip degil: zip calistirma iznini her arsivleyicide
#  korumaz ve calistir.sh calistirilamaz halde acilirsa uygulama "hic
#  acilmiyor" gorunur. tar bu bilgiyi her zaman tasir.
#
#  Uretmekle kalmaz DENETLER; bir kosul bozulursa paket vermez.
# ===========================================================================
set -euo pipefail

KOK="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$KOK"

PAKET="KDV Inceleme Calismasi"
ARSIV="KDV_Inceleme_Calismasi_Linux.tar.gz"

# Pakette bulunmasi ZORUNLU dosyalar. Yeni bir modul eklendiginde buraya da
# yazin, yoksa eksik paket sessizce cikar.
GEREKLI_DOSYALAR=(
  "main.py" "app/web_server.py" "app/hesap.py" "app/db.py"
  "app/belge_docx.py" "app/tutanak.py" "app/sahte_belge_raporu.py"
  "app/excel_export.py" "app/fatura_oku.py" "app/pdf_beyanname.py"
  "app/vergi_beyannamesi.py" "app/beyannameler.py" "app/faturalar.py"
  "web/index.html" "lib/openpyxl/__init__.py" "lib/pypdf/__init__.py"
  "lib_ek/typing_extensions.py"
  "calistir.sh" "kur.sh" "kaldir.sh"
  "KDV Uygulamasini Baslat.desktop"
  "KURULUM.txt" "KULLANIM.md"
  "OKUBENI - ONCE BUNU OKUYUN.txt"
)

# Calistirilabilir olmasi ZORUNLU olanlar. Bu isaret kaybolursa masaustu
# kisayolu betigi calistiramaz, ekranda hicbir sey olmaz.
CALISTIRILABILIR=("calistir.sh" "kur.sh" "kaldir.sh")

kirmizi() { printf '\033[31m%s\033[0m\n' "$*"; }
yesil()   { printf '\033[32m%s\033[0m\n' "$*"; }
baslik()  { printf '\n\033[1m== %s\033[0m\n' "$*"; }
HATA=0
denetim_basarisiz() { kirmizi "  HATA: $*"; HATA=1; }

# ------------------------------------------------------------- 1) Kopyala
baslik "Paket kuruluyor"
rm -rf "$PAKET" "$ARSIV"
mkdir -p "$PAKET"

DISARIDA=(
  '.git' '__pycache__' '*.pyc' '.DS_Store' '*.tar.gz' '*.zip' '*.tmp'
  '.gitignore' 'paketle.sh' 'skill' 'GELISTIRME_NOTLARI.md'
  "$PAKET" 'ciktilar/*' 'yedekler/*' 'veritabani/*' '*.db'
  '*BUNU GONDERIN*' 'ACILIS KAYDI.txt'
)
haric=()
for desen in "${DISARIDA[@]}"; do haric+=(--exclude="$desen"); done
tar -cf - "${haric[@]}" . | (cd "$PAKET" && tar -xf -)
echo "  Kaynak kopyalandi."

# Calistirma izinleri kaynakta bozulmus olabilir (kopyala-yapistir, zip'ten
# acma); pakette her halukarda dogru olsun.
for dosya in "${CALISTIRILABILIR[@]}"; do
  [[ -f "$PAKET/$dosya" ]] && chmod +x "$PAKET/$dosya"
done
chmod +x "$PAKET/KDV Uygulamasini Baslat.desktop" 2>/dev/null || true

# ------------------------------------------------------------ 2) DENETIMLER
baslik "Denetimler"

# Windows'a ozgu dosyalar ve kullanici verisi sizmamis olmali.
for desen in '*.bat' '*.db' '*.ico' '.DS_Store' '__pycache__' 'tani.py'; do
  bulunan="$(find "$PAKET" -name "$desen" 2>/dev/null | head -5 || true)"
  [[ -z "$bulunan" ]] || { denetim_basarisiz "pakete '$desen' sizmis:"
                           echo "$bulunan" | sed 's/^/    /'; }
done

for dosya in "${GEREKLI_DOSYALAR[@]}"; do
  [[ -e "$PAKET/$dosya" ]] || denetim_basarisiz "eksik dosya: $dosya"
done

# Calistirma izni: bunu kaybetmek "uygulama hic acilmiyor"un en sessiz
# sebebidir, cunku masaustu kisayolu hicbir sey yazmadan basarisiz olur.
for dosya in "${CALISTIRILABILIR[@]}"; do
  [[ -x "$PAKET/$dosya" ]] \
    || denetim_basarisiz "calistirilabilir degil: $dosya"
done

# .sh dosyalari LF ile bitmeli: CRLF varsa cekirdek yorumlayiciyi
# "/bin/sh\r" diye arar ve "bad interpreter" hatasi verir.
for betik in "$PAKET"/*.sh; do
  [[ -f "$betik" ]] || continue
  ! head -c 4000 "$betik" | grep -q $'\r' \
    || denetim_basarisiz "CRLF var (Linux'ta bozar): $(basename "$betik")"
done

# Kilavuzda Windows ANLATIMI kalmamis olmali. Yalnizca ".bat" gecmesi olcut
# degildir: kilavuzun "bu paket Linux icindir, Windows surumu ayridir" diye
# uyarmasi gerekiyor ve o cumlede .bat gecer. Aranan sey, kullaniciyi Windows
# adimlarina yonlendiren ifadelerdir.
grep -qiE 'kur\.bat|calistir\.bat|SmartScreen|Program Files|Tumunu ayikla' \
  "$PAKET/KURULUM.txt" 2>/dev/null \
  && denetim_basarisiz "KURULUM.txt icinde Windows anlatimi kalmis"

# Kullaniciya gosterilen adres localhost olmali (Windows'takiyle ayni kural;
# iki surumun ayni davranmasi icin burada da denetlenir).
sizinti="$(grep -rn 'http://127\.0\.0\.1:' "$PAKET" --include='*.py' \
  --include='*.html' --include='*.js' --include='*.txt' --include='*.md' \
  2>/dev/null | grep -v "$PAKET/lib/" || true)"
[[ -z "$sizinti" ]] || { denetim_basarisiz "adres 127.0.0.1:"
                         echo "$sizinti" | sed 's/^/    /'; }

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
  rm -rf "$PAKET"
  exit 1
fi
yesil "  Tum denetimler gecti."

# ---------------------------------------------------------------- 3) Arsiv
baslik "Arsiv"
tar -czf "$ARSIV" "$PAKET"
yesil "  $ARSIV  ($(du -h "$ARSIV" | cut -f1))"

echo
echo "Kullanicinin yapacagi:"
echo "  tar -xzf $ARSIV"
echo "  cd \"$PAKET\" && ./kur.sh      # masaustu kisayolu"
echo "  ya da dogrudan: ./calistir.sh"
