#!/bin/sh
# KDV Inceleme Calismasi - sorun giderme raporu (Linux)
#
# Cift tiklayip "Calistir" deyin. Ekrana ve ayni klasordeki
# baslatma_kaydi.txt dosyasina ayrintili bir rapor yazar.
UYG_DIZIN=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
exec "$UYG_DIZIN/calistir.sh" --tani
