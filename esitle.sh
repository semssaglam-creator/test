#!/usr/bin/env bash
# ===========================================================================
#  Ortak uygulama kodunu kdv_linux -> kdv_windows yonunde esitler.
#
#  Kullanim:
#    ./esitle.sh          # esitle
#    ./esitle.sh --denetle # yalnizca fark var mi diye bak (yazmaz)
#
#  Iki agac AYRI tutuluyor (Linux ve Windows surumleri birbirine
#  karismasin diye), ama uygulamanin kendisi ikisinde de ayni olmali.
#  Elle iki yerde duzenlemek er ya da gec unutulur ve surumler sessizce
#  ayrisir; bu betik o riski ortadan kaldirir.
#
#  ORTAK olan: uygulama kodu ve arayuz.
#  ORTAK OLMAYAN: baslaticilar (.sh / .bat), kurulum belgeleri, ikon
#  bicimi, tani araci ve paketleme. Onlar her agacin kendi dosyalaridir
#  ve bu betik onlara DOKUNMAZ.
# ===========================================================================
set -euo pipefail

KOK="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
KAYNAK="$KOK/kdv_linux"
HEDEF="$KOK/kdv_windows"

# Iki agacta da ayni olmasi gereken yollar.
ORTAK=(
  "main.py"
  "app"
  "web"
  "lib"
  "lib_ek"
  "KULLANIM.md"
)

# app/ icinde Windows'a ozgu olan; kopyalanmaz.
HARIC=("tani.py")

denetle=0
[[ "${1:-}" == "--denetle" ]] && denetle=1

for dizin in "$KAYNAK" "$HEDEF"; do
  [[ -d "$dizin" ]] || { echo "hata: dizin yok: $dizin" >&2; exit 1; }
done

haric_args=()
for ad in "${HARIC[@]}"; do haric_args+=(--exclude="$ad"); done
haric_args+=(--exclude="__pycache__" --exclude="*.pyc")

fark=0
for yol in "${ORTAK[@]}"; do
  kaynak="$KAYNAK/$yol"
  hedef="$HEDEF/$yol"
  [[ -e "$kaynak" ]] || { echo "hata: kaynakta yok: $yol" >&2; exit 1; }

  if [[ $denetle -eq 1 ]]; then
    if ! diff -rq "${haric_args[@]/--exclude=/-x}" "$kaynak" "$hedef" \
         >/dev/null 2>&1; then
      echo "  FARKLI: $yol"
      fark=1
    fi
    continue
  fi

  if [[ -d "$kaynak" ]]; then
    # Hedef klasor SILINMEZ. Silinirse hedefe ozgu dosyalar (app/tani.py
    # yalnizca Windows surumunde vardir) yok olur; HARIC listesi onlari
    # uzerine yazilmaktan korur ama silinmekten korumaz.
    mkdir -p "$hedef"
    tar -cf - "${haric_args[@]}" -C "$kaynak" . | (cd "$hedef" && tar -xf -)
    # Kaynakta artik olmayan dosyalari hedeften temizle (haric tutulanlar
    # ile __pycache__ disinda); yoksa silinen bir modul hedefte yasamaya
    # devam eder.
    while IFS= read -r goreli; do
      [[ -n "$goreli" ]] || continue
      ad="$(basename "$goreli")"
      atla=0
      for h in "${HARIC[@]}"; do [[ "$ad" == "$h" ]] && atla=1; done
      [[ "$goreli" == *__pycache__* || "$ad" == *.pyc ]] && atla=1
      [[ $atla -eq 1 ]] && continue
      [[ -e "$kaynak/$goreli" ]] || { rm -f "$hedef/$goreli"
                                      echo "    silindi: $yol/$goreli"; }
    done < <(cd "$hedef" && find . -type f -printf '%P\n' 2>/dev/null || true)
  else
    mkdir -p "$(dirname "$hedef")"
    cp "$kaynak" "$hedef"
  fi
  echo "  esitlendi: $yol"
done

if [[ $denetle -eq 1 ]]; then
  if [[ $fark -eq 0 ]]; then
    echo "Iki agac ortak dosyalarda ayni."
  else
    echo
    echo "Fark var. './esitle.sh' ile giderin." >&2
    exit 1
  fi
fi
