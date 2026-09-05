#!/usr/bin/env python3
"""Mac icin "Beyanname Dokumu" paketini uretir.

Paket kendi kendine yeter: icinde pypdf de gelir, Mac'te hicbir sey
kurmak gerekmez (sistemdeki python3 yeterlidir).

Kullanim:
    python3 mac/paketle_mac.py mac/Beyanname_Dokumu_Mac.zip

Uretmekle kalmaz, DENETLER. Mac'te ancak kullanicida gorunen iki hata
paket uretilirken burada yakalanir:
  - .command dosyasinin calistirma biti dusmus olursa cift tiklayinca
    TextEdit'te acilir, calismaz.
  - .command dosyasi CRLF satir sonu tasirsa bash "command not found"
    verir; dosya gorunuste dogrudur ama calismaz.
zipfile izinleri kendiliginden yazmaz; her girdinin kipi external_attr'a
acikca konur, yoksa calistirma biti zip'te kaybolur.
"""
import os
import stat
import sys
import zipfile

BURASI = os.path.dirname(os.path.abspath(__file__))
KAYNAK = os.path.join(BURASI, "beyanname_dokumu")
PYPDF = os.path.join(BURASI, os.pardir, "linux", "kdv_uygulamasi", "lib", "pypdf")
KLASOR = "Beyanname Dokumu"          # zip acilinca gorunecek klasor adi
BASLATICI = "Beyanname Dokumu Al.command"


def _denetle():
    hatalar = []
    yol = os.path.join(KAYNAK, BASLATICI)
    if not os.path.isfile(yol):
        return ["baslatici yok: %s" % BASLATICI]
    if not os.stat(yol).st_mode & stat.S_IXUSR:
        hatalar.append("%s calistirilabilir degil (chmod +x)" % BASLATICI)
    with open(yol, "rb") as f:
        if b"\r\n" in f.read():
            hatalar.append("%s CRLF satir sonu tasiyor (LF olmali)" % BASLATICI)
    if not os.path.isdir(PYPDF):
        hatalar.append("pypdf bulunamadi: %s" % PYPDF)
    for gerekli in (BASLATICI, "beyanname_maskele.py", "OKUBENI.txt"):
        if not os.path.isfile(os.path.join(KAYNAK, gerekli)):
            hatalar.append("eksik dosya: %s" % gerekli)
    return hatalar


def _yaz(z, tam, bagil):
    kip = os.stat(tam).st_mode
    bilgi = zipfile.ZipInfo.from_file(tam, bagil)
    bilgi.external_attr = (kip & 0xFFFF) << 16
    bilgi.compress_type = zipfile.ZIP_DEFLATED
    with open(tam, "rb") as f:
        z.writestr(bilgi, f.read())
    return bool(kip & stat.S_IXUSR)


def paketle(hedef):
    n, calisir = 0, []
    with zipfile.ZipFile(hedef, "w", zipfile.ZIP_DEFLATED) as z:
        for ad in sorted(os.listdir(KAYNAK)):
            tam = os.path.join(KAYNAK, ad)
            if not os.path.isfile(tam) or ad.endswith((".pyc", ".txt.bak")):
                continue
            if ad in ("dokum.txt", "dokum_hata.txt"):
                continue
            if _yaz(z, tam, "%s/%s" % (KLASOR, ad)):
                calisir.append(ad)
            n += 1
        for kok, dizinler, dosyalar in os.walk(PYPDF):
            dizinler[:] = [d for d in dizinler if d != "__pycache__"]
            for d in sorted(dosyalar):
                if d.endswith(".pyc"):
                    continue
                tam = os.path.join(kok, d)
                bagil = os.path.relpath(tam, os.path.dirname(os.path.dirname(PYPDF)))
                _yaz(z, tam, "%s/%s" % (KLASOR, bagil))
                n += 1
    return n, calisir


if __name__ == "__main__":
    hatalar = _denetle()
    if hatalar:
        print("Denetimler basarisiz, paket URETILMEDI:")
        for h in hatalar:
            print("  - " + h)
        sys.exit(1)
    hedef = sys.argv[1] if len(sys.argv) > 1 else os.path.join(
        BURASI, "Beyanname_Dokumu_Mac.zip")
    n, calisir = paketle(hedef)
    print("%d dosya -> %s (%.1f MB)"
          % (n, hedef, os.path.getsize(hedef) / 1024 / 1024))
    print("calistirilabilir: " + (", ".join(calisir) or "YOK - SORUN"))
