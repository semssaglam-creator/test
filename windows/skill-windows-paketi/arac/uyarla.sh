#!/usr/bin/env bash
# ===========================================================================
#  windows-paketi skill'i - iskeleti projeye kurar
#
#  Kullanim:  uyarla.sh <proje_dizini>
#
#  Sorulari terminalden sorar. Terminal yoksa (betikten cagrildiginda)
#  ortam degiskenlerini kullanir:
#    UYGULAMA_ADI, KISAYOL_ACIKLAMA, PAKET_KLASOR, ARSIV_ADI,
#    PORT, TANI_DOSYASI, MIMARI
#
#  Kurulan dosyalar bundan sonra PROJENIN kendi dosyalaridir; skill'e geri
#  donmeden orada duzenlenir.
# ===========================================================================
set -euo pipefail

SKILL="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

if [[ $# -ne 1 ]]; then
  echo "Kullanim: $(basename "$0") <proje_dizini>" >&2
  exit 2
fi
PROJE="$(cd "$1" 2>/dev/null && pwd)" || {
  echo "hata: dizin bulunamadi: $1" >&2
  exit 1
}

sor() {
  # sor <degisken_adi> <soru> <varsayilan>
  local ad="$1" soru="$2" varsayilan="$3" cevap=""
  if [[ -n "${!ad:-}" ]]; then
    printf '  %-22s %s (ortamdan)\n' "$soru" "${!ad}"
    return
  fi
  if [[ -t 0 ]]; then
    read -r -p "  $soru [$varsayilan]: " cevap
  fi
  printf -v "$ad" '%s' "${cevap:-$varsayilan}"
  export "${ad?}"
}

VARSAYILAN_AD="$(basename "$PROJE")"
echo
echo "windows-paketi - iskelet kurulumu"
echo "Proje: $PROJE"
echo

sor UYGULAMA_ADI     "Uygulama adi"        "$VARSAYILAN_AD"
sor KISAYOL_ACIKLAMA "Kisayol aciklamasi"  "$UYGULAMA_ADI"
sor PAKET_KLASOR     "Paket klasoru"       "${VARSAYILAN_AD}_windows"
sor ARSIV_ADI        "Arsiv adi"           "${VARSAYILAN_AD}_windows.zip"
sor PORT             "Baslangic portu"     "8766"
sor TANI_DOSYASI     "Tani dosyasi adi"    "TANI RAPORU - BUNU GONDERIN.txt"
sor MIMARI           "Mimari"              "amd64"

if ! [[ "$PORT" =~ ^[0-9]+$ ]] || (( PORT < 1024 || PORT > 65000 )); then
  echo "hata: port 1024-65000 araliginda bir sayi olmali: $PORT" >&2
  exit 1
fi
if [[ "$MIMARI" != "amd64" && "$MIMARI" != "arm64" ]]; then
  echo "hata: mimari amd64 ya da arm64 olmali: $MIMARI" >&2
  exit 1
fi

# Yer tutuculari degistirerek kopyalar.
yerlestir() {
  local kaynak="$1" hedef="$2"
  mkdir -p "$(dirname "$hedef")"
  sed -e "s|{{UYGULAMA_ADI}}|$UYGULAMA_ADI|g" \
      -e "s|{{KISAYOL_ACIKLAMA}}|$KISAYOL_ACIKLAMA|g" \
      -e "s|{{PAKET_KLASOR}}|$PAKET_KLASOR|g" \
      -e "s|{{ARSIV_ADI}}|$ARSIV_ADI|g" \
      -e "s|{{PORT}}|$PORT|g" \
      -e "s|{{TANI_DOSYASI}}|$TANI_DOSYASI|g" \
      -e "s|{{MIMARI}}|$MIMARI|g" \
      "$kaynak" > "$hedef"
}

# Var olan dosyanin uzerine yazmadan once yedekle: proje kendi
# duzenlemelerini yapmis olabilir, sessizce kaybolmasin.
yedekle() {
  [[ -e "$1" ]] || return 0
  local yedek="$1.onceki"
  cp "$1" "$yedek"
  echo "    (onceki surum saklandi: $(basename "$yedek"))"
}

echo
echo "Kuruluyor..."

mkdir -p "$PROJE/windows" "$PROJE/arac" "$PROJE/app"

for bat in "$SKILL"/sablon/windows/*.bat; do
  ad="$(basename "$bat")"
  yedekle "$PROJE/windows/$ad"
  yerlestir "$bat" "$PROJE/windows/$ad"
  echo "  windows/$ad"
done

yedekle "$PROJE/windows/KURULUM.txt"
yerlestir "$SKILL/sablon/windows/KURULUM.txt" "$PROJE/windows/KURULUM.txt"
echo "  windows/KURULUM.txt"

yedekle "$PROJE/app/tani.py"
yerlestir "$SKILL/sablon/app/tani.py" "$PROJE/app/tani.py"
echo "  app/tani.py"

yedekle "$PROJE/paketle.sh"
yerlestir "$SKILL/sablon/paketle.sh" "$PROJE/paketle.sh"
chmod +x "$PROJE/paketle.sh"
echo "  paketle.sh"

for arac in png2ico.py belge_hazirla.py python_indir.sh; do
  cp "$SKILL/arac/$arac" "$PROJE/arac/$arac"
  echo "  arac/$arac"
done
chmod +x "$PROJE/arac/python_indir.sh"

# .bat ve KURULUM.txt CRLF olmali; LF ile biten .bat Windows'ta goto
# etiketlerini bozar. paketle.sh bunu denetler, burada bastan dogru yazilir.
python3 - "$PROJE" <<'PY'
import io, os, sys
proje = sys.argv[1]
hedefler = [os.path.join(proje, "windows", ad)
            for ad in os.listdir(os.path.join(proje, "windows"))]
for yol in hedefler:
    if not yol.endswith((".bat", ".txt")):
        continue
    with io.open(yol, encoding="utf-8", newline="") as f:
        metin = f.read().replace("\r\n", "\n")
    kodlama = "utf-8-sig" if yol.endswith(".txt") else "utf-8"
    with io.open(yol, "w", encoding=kodlama, newline="\r\n") as f:
        f.write(metin)
print("  (windows/ dosyalari CRLF'e cevrildi)")
PY

cat <<SON

Iskelet kuruldu.

Siradaki adimlar:
  1. references/windows-tuzaklari.md icindeki dort duzeltmeyi koda uygulayin
     (localhost adresi, ::1 cift dinleme, allow_reuse_address, Chrome).
  2. paketle.sh icindeki GEREKLI_DOSYALAR listesini projeye gore duzenleyin.
  3. ./paketle.sh $MIMARI

Not: windows/ altindaki dosyalar artik projenin kendi dosyalaridir.
Duzeltmeleri orada yapin; paket klasorunu ($PAKET_KLASOR) elle duzenlemeyin,
bir sonraki uretimde uzerine yazilir.
SON
