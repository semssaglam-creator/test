#!/usr/bin/env python3
"""Linux icin calisir uygulama paketi uretir.

Kullanim:
    python3 linux/paketle_linux.py hedef.tar.gz [kdv|uzlasma|hepsi]
    python3 linux/paketle_linux.py hedef.zip    [kdv|uzlasma|hepsi]

Bicim dosya uzantisindan secilir. Linux'ta olagan olan tar.gz'dir; tar
dosya kiplerini kendiliginden tasidigi icin calistirma biti de korunur.

Depo artik platformlara gore ayrildigi icin (bkz. kokteki OKUBENI.md)
bu betigin Windows dosyasi ayiklamasi gerekmiyor; yalnizca kullanici
verisi, onbellek ve gelistirme cikitlari disarida birakilir.

Not: zip yolunda izinler kendiliginden YAZILMAZ. calistir.sh gibi betikler
zip'ten calistirma bitini kaybederse kullanici cift tikladiginda hicbir
sey olmaz; bu yuzden her girdinin kipi external_attr'a acikca konur.
"""
import os
import re
import stat
import sys
import tarfile
import zipfile

BURASI = os.path.dirname(os.path.abspath(__file__))
UYGULAMALAR = {
    # Kullanicinin gercekte calistirdigi soy. Klasor adi "KDV Inceleme
    # Calismasi" (bosluklu); paketler de o adla acilmali, yoksa guncelleme
    # onun klasorune hic ulasmaz.
    "inceleme": "kdv_inceleme_calismasi",
    "kdv": "kdv_uygulamasi",
    "uzlasma": "uzlasma_uygulamasi",
}

# Paket acilinca gorunecek ust klasor adlari (depo icindeki ada gore).
KLASOR_ADLARI = {"kdv_inceleme_calismasi": "KDV Inceleme Calismasi"}

# Calisan bir kuruluma uygulanacak guncelleme paketi: yalnizca uygulama kodu.
# Baslatici, lib/ ve main.py disarida kalir - kullanicinin calisan duzenine
# dokunulmaz. Kullanici paketi kendi klasorunun uzerine acar ve uygulamayi
# her zamanki gibi (calistir.sh) baslatir. Baslatma yontemini degistirmek
# defalarca ise yaramadi; calisan duzene dokunmamak en emniyetli yol.
GUNCELLEME_ALT_DIZINLER = ("app", "web")


def _surum(klasor="kdv_uygulamasi"):
    """app/__init__.py icindeki SURUM degerini okur (ice aktarmadan)."""
    yol = os.path.join(BURASI, klasor, "app", "__init__.py")
    try:
        with open(yol, encoding="utf-8") as f:
            for satir in f:
                # Belge metninde de "SURUM" gectigi icin atama araniyor.
                esles = re.match(r"""^SURUM\s*=\s*['"]([^'"]+)['"]""", satir)
                if esles:
                    return esles.group(1)
    except OSError:
        pass
    return ""

DISARIDA_DIZIN = {"__pycache__", ".git", "onbellek", "veritabani"}
DISARIDA_DOSYA = {".gitignore"}
DISARIDA_UZANTI = (".pyc", ".db", ".xlsx", ".docx", ".bat")


def _dosyalar(klasorler, yalnizca=None):
    """Pakete girecek (tam yol, paket icindeki yol) ciftlerini uretir.

    `yalnizca` verilirse uygulama klasorunun yalnizca o alt dizinleri alinir
    (guncelleme paketi).
    """
    for klasor in klasorler:
        koklar = ([os.path.join(BURASI, klasor, alt) for alt in yalnizca]
                  if yalnizca else [os.path.join(BURASI, klasor)])
        for kaynak in koklar:
            for kok, dizinler, dosyalar in os.walk(kaynak):
                dizinler[:] = [d for d in dizinler if d not in DISARIDA_DIZIN]
                for d in sorted(dosyalar):
                    if d in DISARIDA_DOSYA or d.endswith(DISARIDA_UZANTI):
                        continue
                    if "baslatma_kaydi" in d or "baslatma_hatasi" in d:
                        continue
                    tam = os.path.join(kok, d)
                    yield tam, os.path.relpath(tam, BURASI)


def _sahipsiz(bilgi):
    """Arsivdeki dosyayi uretim makinesinin kullanicisina baglamaz.

    tar, uid/gid ve kullanici adini da tasir; root olarak acilirsa dosyalar
    baskasinin adina gecebilir. Sifirlanip adlari bosaltilarak acan
    kullanicinin kendi kimligiyle olusmasi saglanir.
    """
    bilgi.uid = bilgi.gid = 0
    bilgi.uname = bilgi.gname = ""
    return bilgi


def paketle(hedef, klasorler, yalnizca=None, klasor_adi=None):
    """`klasor_adi` verilirse paketin ust klasoru o adla acilir.

    Tam pakette ust klasore surum eklenir (kdv_uygulamasi_2026.09.07).
    Sebep: paket, kullanicinin var olan "kdv_uygulamasi" klasorunun yanina
    acildiginda dosya yoneticisi "birlestir mi, degistir mi" diye soruyor.
    "Degistir" secilirse eski klasorun icerigi silinir - main.py, lib/ ve
    calistir.sh gider, uygulama hic acilmaz. Ad farkli olunca cakisma da
    soru da ortadan kalkar; eski klasore hicbir sey olmaz.
    """
    alinan, calisir = [], []
    tar_mi = hedef.endswith((".tar.gz", ".tgz"))
    arsiv = (tarfile.open(hedef, "w:gz") if tar_mi
             else zipfile.ZipFile(hedef, "w", zipfile.ZIP_DEFLATED))
    with arsiv as a:
        for tam, bagil in _dosyalar(klasorler, yalnizca):
            if klasor_adi:
                ilk, _ayrac, kalan = bagil.partition("/")
                bagil = "%s/%s" % (klasor_adi, kalan) if kalan else klasor_adi
            kip = os.stat(tam).st_mode
            if tar_mi:
                # tar dosya kipini kendisi tasir; ayrica ayarlamak gerekmez.
                a.add(tam, arcname=bagil, recursive=False, filter=_sahipsiz)
            else:
                bilgi = zipfile.ZipInfo.from_file(tam, bagil)
                bilgi.external_attr = (kip & 0xFFFF) << 16
                bilgi.compress_type = zipfile.ZIP_DEFLATED
                with open(tam, "rb") as f:
                    a.writestr(bilgi, f.read())
            alinan.append(bagil)
            if kip & stat.S_IXUSR:
                calisir.append(bagil)
    return alinan, calisir


if __name__ == "__main__":
    hedef = sys.argv[1] if len(sys.argv) > 1 else "kdv_uygulamasi_linux.tar.gz"
    hangi = sys.argv[2] if len(sys.argv) > 2 else "kdv"
    yalnizca = None
    if hangi.endswith("-guncelleme"):
        hangi = hangi[: -len("-guncelleme")]
        yalnizca = GUNCELLEME_ALT_DIZINLER
    if hangi == "hepsi":
        klasorler = list(UYGULAMALAR.values())
    elif hangi in UYGULAMALAR:
        klasorler = [UYGULAMALAR[hangi]]
    else:
        sys.exit("bilinmeyen uygulama: %s "
                 "(kdv | uzlasma | hepsi; sonuna -guncelleme eklenebilir)" % hangi)

    # Tam pakette ust klasor surumle adlandirilir; guncelleme paketinde
    # ad ayni kalmali, cunku o zaten var olan klasorun uzerine acilir.
    klasor_adi = None
    if len(klasorler) == 1:
        s = _surum(klasorler[0])
        if yalnizca:
            # Guncelleme paketinin ust klasoru BILEREK "kdv_uygulamasi"
            # DEGIL. Ayni adi tasisaydi, kullanicinin klasorunun yanina
            # acilinca dosya yoneticisi "birlestir mi, degistir mi" diye
            # sorar; "degistir" secilirse klasorun icerigi silinir ve
            # main.py, lib/, calistir.sh gider - uygulama hic acilmaz.
            # Bir kez oldu. Ayri adla acilinca cakisma, app/ ve web/
            # seviyesine iner; orada iki cevap da guvenlidir, cunku paket
            # o klasorlerin TAMAMINI tasir.
            klasor_adi = "KDV_Guncelleme"
        else:
            temel = KLASOR_ADLARI.get(klasorler[0], klasorler[0])
            klasor_adi = "%s %s" % (temel, s) if s else temel
    alinan, calisir = paketle(hedef, klasorler, yalnizca, klasor_adi)
    print("%d dosya -> %s (%.1f MB)"
          % (len(alinan), hedef, os.path.getsize(hedef) / 1024 / 1024))
    ust = sorted({a.split("/")[1] for a in alinan if a.count("/") >= 1})
    print("\nKlasorde gorunecekler:")
    for u in ust:
        print("  " + u)
    print("\nCalistirilabilir:")
    for c in calisir:
        print("  " + c)
