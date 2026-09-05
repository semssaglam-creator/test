#!/usr/bin/env bash
# ===========================================================================
#  Gomulu (embeddable) Python'u onbellege indirir.
#
#  Kullanim:  python_indir.sh [amd64|arm64] [surum]
#
#  paketle.sh bunu kendisi yapar; bu betik ag erisimi olan bir makinede
#  onceden indirip zip'i baska bir projeye ya da cevrimdisi bir makineye
#  tasimak icindir. Onbellek: arac/onbellek/
# ===========================================================================
set -euo pipefail

KOK="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MIMARI="${1:-amd64}"
SURUM="${2:-3.12.8}"
ONBELLEK="$KOK/onbellek"

if [[ "$MIMARI" != "amd64" && "$MIMARI" != "arm64" ]]; then
  echo "hata: mimari amd64 ya da arm64 olmali: $MIMARI" >&2
  exit 1
fi

ZIP="python-${SURUM}-embed-${MIMARI}.zip"
URL="https://www.python.org/ftp/python/${SURUM}/${ZIP}"

mkdir -p "$ONBELLEK"

if [[ -f "$ONBELLEK/$ZIP" ]]; then
  echo "Zaten onbellekte: $ONBELLEK/$ZIP"
  exit 0
fi

echo "Indiriliyor: $URL"
# Once gecici ada indirilir: yarim kalan bir indirme onbellekte gecerli
# bir dosya gibi durup sonraki uretimde bozuk paket uretmesin.
if ! curl -fSL --retry 3 --retry-delay 2 -o "$ONBELLEK/$ZIP.gecici" "$URL"; then
  rm -f "$ONBELLEK/$ZIP.gecici"
  echo >&2
  echo "Indirilemedi." >&2
  echo "Ag erisimi yoksa zip'i elle indirip su konuma koyun:" >&2
  echo "  $ONBELLEK/$ZIP" >&2
  exit 1
fi

# Gercekten zip mi? Proxy hata sayfasi da 200 ile gelebilir.
if ! unzip -tq "$ONBELLEK/$ZIP.gecici" >/dev/null 2>&1; then
  rm -f "$ONBELLEK/$ZIP.gecici"
  echo "hata: inen dosya gecerli bir zip degil (proxy hata sayfasi?)" >&2
  exit 1
fi

mv "$ONBELLEK/$ZIP.gecici" "$ONBELLEK/$ZIP"
echo "Onbellege alindi: $ONBELLEK/$ZIP ($(du -h "$ONBELLEK/$ZIP" | cut -f1))"
