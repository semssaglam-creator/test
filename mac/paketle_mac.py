#!/usr/bin/env python3
"""Mac icin "Beyanname Dokumu" paketini uretir.

Paket kendi kendine yeter: pypdf ve typing_extensions icinde gelir, Mac'te
hicbir sey kurmak gerekmez (sistemdeki python3 yeterlidir).

Kullanim:
    python3 mac/paketle_mac.py [hedef.zip]

Uretmekle kalmaz, DENETLER. Mac'te ancak kullanicida gorunen, gelistirme
makinesinde hic ortaya cikmayan hatalar burada yakalanir:

  - .command dosyasinin calistirma biti dusmusse cift tiklayinca TextEdit
    acilir, betik calismaz.
  - .command CRLF satir sonu tasirsa bash "command not found" verir; dosya
    gorunuste dogrudur.
  - ESKI PYTHON: macOS'un kendi python3'u 3.9'dur. pypdf, 3.11'den eskisinde
    `typing_extensions` modulunu ice aktarir. Gelistirme makinesinde Python
    3.11+ oldugu icin bu dal hic calismaz ve eksik bagimlilik fark edilmez;
    kullanicida ise "pypdf yuklenemedi" ile duser. Bu yuzden paket, makinede
    bulunan EN ESKI python3 ile ayrica denenir.

zipfile izinleri kendiliginden yazmaz; her girdinin kipi external_attr'a
acikca konur, yoksa calistirma biti zip'te kaybolur.
"""
import glob
import os
import re
import shutil
import stat
import subprocess
import sys
import tempfile
import zipfile

BURASI = os.path.dirname(os.path.abspath(__file__))
KAYNAK = os.path.join(BURASI, "beyanname_dokumu")
UYGULAMA = os.path.join(BURASI, os.pardir, "linux", "kdv_uygulamasi")
LIB = os.path.join(UYGULAMA, "lib")
LIB_EK = os.path.join(UYGULAMA, "lib_ek")
KLASOR = "Beyanname Dokumu"          # zip acilinca gorunecek klasor adi
BASLATICI = "Beyanname Dokumu Al.command"
DOSYALAR = (BASLATICI, "beyanname_maskele.py", "OKUBENI.txt")


def _on_denetim():
    hatalar = []
    yol = os.path.join(KAYNAK, BASLATICI)
    if not os.path.isfile(yol):
        return ["baslatici yok: %s" % BASLATICI]
    if not os.stat(yol).st_mode & stat.S_IXUSR:
        hatalar.append("%s calistirilabilir degil (chmod +x)" % BASLATICI)
    with open(yol, "rb") as f:
        if b"\r\n" in f.read():
            hatalar.append("%s CRLF satir sonu tasiyor (LF olmali)" % BASLATICI)
    if not os.path.isdir(os.path.join(LIB, "pypdf")):
        hatalar.append("pypdf bulunamadi: %s" % LIB)
    if not os.path.isfile(os.path.join(LIB_EK, "typing_extensions.py")):
        hatalar.append("typing_extensions bulunamadi: %s" % LIB_EK)
    for gerekli in DOSYALAR:
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


def _agac_ekle(z, kaynak_dizin, ust):
    """kaynak_dizin agacini paketin <ust>/ altina kopyalar."""
    n = 0
    for kok, dizinler, dosyalar in os.walk(kaynak_dizin):
        dizinler[:] = [d for d in dizinler if d != "__pycache__"]
        for d in sorted(dosyalar):
            if d.endswith(".pyc"):
                continue
            tam = os.path.join(kok, d)
            bagil = os.path.relpath(tam, kaynak_dizin)
            _yaz(z, tam, "%s/%s/%s" % (KLASOR, ust, bagil))
            n += 1
    return n


def paketle(hedef):
    n, calisir = 0, []
    with zipfile.ZipFile(hedef, "w", zipfile.ZIP_DEFLATED) as z:
        for ad in sorted(os.listdir(KAYNAK)):
            tam = os.path.join(KAYNAK, ad)
            if not os.path.isfile(tam) or ad.endswith(".pyc"):
                continue
            if ad in ("dokum.txt", "dokum_hata.txt"):
                continue
            if _yaz(z, tam, "%s/%s" % (KLASOR, ad)):
                calisir.append(ad)
            n += 1
        n += _agac_ekle(z, os.path.join(LIB, "pypdf"), "lib/pypdf")
        n += _agac_ekle(z, LIB_EK, "lib_ek")
    return n, calisir


def _yorumlayicilar():
    """Makinedeki python3 surumleri, eskiden yeniye."""
    aramalar = [
        "/usr/bin/python3.*",
        "/usr/local/bin/python3.*",
        # uv ile kurulan surumler: gelistirme makinesinde bulunmayan eski bir
        # surumu (ornegin macOS'un 3.9'u) boyle denemek mumkun olur.
        os.path.expanduser("~/.local/share/uv/python/*/bin/python3.*"),
    ]
    bulunan = {}
    for desen in aramalar:
        for yol in glob.glob(desen):
            m = re.match(r".*/python3\.(\d+)$", yol)
            if m:
                bulunan.setdefault(int(m.group(1)), yol)
    return [bulunan[k] for k in sorted(bulunan)]


def _calisma_denetimi(hedef):
    """Paketi gercekten acip, bulunan her Python surumuyle yuklemeyi dener.

    Onemli olan EN ESKI surum: Mac'te python3 = 3.9. Yalnizca gelistirme
    makinesinin surumuyle denemek, bu paketi bir kez zaten kirmisti.
    """
    hatalar, rapor = [], []
    gecici = tempfile.mkdtemp(prefix="mac_paket_")
    try:
        with zipfile.ZipFile(hedef) as z:
            z.extractall(gecici)
        klasor = os.path.join(gecici, KLASOR)
        kod = ("import importlib.util,sys;"
               "s=importlib.util.spec_from_file_location('bm','beyanname_maskele.py');"
               "m=importlib.util.module_from_spec(s);s.loader.exec_module(m);"
               "m._kripto_saglayicisini_ele();"
               "import pypdf;print(pypdf.__version__)")
        yorumlayicilar = _yorumlayicilar() or [sys.executable]
        for py in yorumlayicilar:
            sonuc = subprocess.run([py, "-c", kod], cwd=klasor,
                                   capture_output=True, text=True)
            ad = os.path.basename(py)
            if sonuc.returncode == 0:
                rapor.append("  %-12s pypdf %s" % (ad, sonuc.stdout.strip()))
            else:
                son = (sonuc.stderr.strip() or sonuc.stdout.strip()).splitlines()
                rapor.append("  %-12s BASARISIZ" % ad)
                hatalar.append("%s ile yuklenemedi: %s"
                               % (ad, son[-1] if son else "?"))
        eski = [os.path.basename(p) for p in yorumlayicilar
                if int(p.rsplit(".", 1)[1]) < 11]
        if not eski:
            rapor.append("  (uyari: 3.11'den eski python3 yok, Mac kosulu"
                         " denenemedi)")
    finally:
        shutil.rmtree(gecici, ignore_errors=True)
    return hatalar, rapor


if __name__ == "__main__":
    hatalar = _on_denetim()
    if hatalar:
        print("On denetimler basarisiz, paket URETILMEDI:")
        for h in hatalar:
            print("  - " + h)
        sys.exit(1)

    hedef = sys.argv[1] if len(sys.argv) > 1 else os.path.join(
        BURASI, "Beyanname_Dokumu_Mac.zip")
    n, calisir = paketle(hedef)

    hatalar, rapor = _calisma_denetimi(hedef)
    print("Yukleme denemesi:")
    for satir in rapor:
        print(satir)
    if hatalar:
        print("\nCalisma denetimi basarisiz, paket SILINDI:")
        for h in hatalar:
            print("  - " + h)
        os.remove(hedef)
        sys.exit(1)

    print("\n%d dosya -> %s (%.1f MB)"
          % (n, hedef, os.path.getsize(hedef) / 1024 / 1024))
    print("calistirilabilir: " + (", ".join(calisir) or "YOK - SORUN"))
