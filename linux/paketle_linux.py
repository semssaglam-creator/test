#!/usr/bin/env python3
"""Linux icin calisir uygulama paketi uretir.

Kullanim:
    python3 linux/paketle_linux.py hedef.zip [kdv|uzlasma|hepsi]

Depo artik platformlara gore ayrildigi icin (bkz. kokteki OKUBENI.md)
bu betigin Windows dosyasi ayiklamasi gerekmiyor; yalnizca kullanici
verisi, onbellek ve gelistirme cikitlari disarida birakilir.

Not: zipfile izinleri kendiliginden yazmaz. calistir.sh gibi betikler
zip'ten calistirma bitini kaybederse kullanici cift tikladiginda hicbir
sey olmaz; bu yuzden her girdinin kipi external_attr'a acikca konur.
"""
import os
import stat
import sys
import zipfile

BURASI = os.path.dirname(os.path.abspath(__file__))
UYGULAMALAR = {
    "kdv": "kdv_uygulamasi",
    "uzlasma": "uzlasma_uygulamasi",
}

DISARIDA_DIZIN = {"__pycache__", ".git", "onbellek", "veritabani"}
DISARIDA_DOSYA = {".gitignore"}
DISARIDA_UZANTI = (".pyc", ".db", ".xlsx", ".docx", ".bat")


def paketle(hedef, klasorler):
    alinan, calisir = [], []
    with zipfile.ZipFile(hedef, "w", zipfile.ZIP_DEFLATED) as z:
        for klasor in klasorler:
            kaynak = os.path.join(BURASI, klasor)
            for kok, dizinler, dosyalar in os.walk(kaynak):
                dizinler[:] = [d for d in dizinler if d not in DISARIDA_DIZIN]
                for d in sorted(dosyalar):
                    if d in DISARIDA_DOSYA or d.endswith(DISARIDA_UZANTI):
                        continue
                    if "baslatma_kaydi" in d or "baslatma_hatasi" in d:
                        continue
                    tam = os.path.join(kok, d)
                    bagil = os.path.relpath(tam, BURASI)
                    kip = os.stat(tam).st_mode
                    bilgi = zipfile.ZipInfo.from_file(tam, bagil)
                    bilgi.external_attr = (kip & 0xFFFF) << 16
                    bilgi.compress_type = zipfile.ZIP_DEFLATED
                    with open(tam, "rb") as f:
                        z.writestr(bilgi, f.read())
                    alinan.append(bagil)
                    if kip & stat.S_IXUSR:
                        calisir.append(bagil)
    return alinan, calisir


if __name__ == "__main__":
    hedef = sys.argv[1] if len(sys.argv) > 1 else "kdv_uygulamasi_linux.zip"
    hangi = sys.argv[2] if len(sys.argv) > 2 else "kdv"
    if hangi == "hepsi":
        klasorler = list(UYGULAMALAR.values())
    elif hangi in UYGULAMALAR:
        klasorler = [UYGULAMALAR[hangi]]
    else:
        sys.exit("bilinmeyen uygulama: %s (kdv | uzlasma | hepsi)" % hangi)

    alinan, calisir = paketle(hedef, klasorler)
    print("%d dosya -> %s (%.1f MB)"
          % (len(alinan), hedef, os.path.getsize(hedef) / 1024 / 1024))
    ust = sorted({a.split("/")[1] for a in alinan if a.count("/") >= 1})
    print("\nKlasorde gorunecekler:")
    for u in ust:
        print("  " + u)
    print("\nCalistirilabilir:")
    for c in calisir:
        print("  " + c)
