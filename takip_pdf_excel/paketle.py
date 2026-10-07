#!/usr/bin/env python3
"""Kullanıcıya verilecek paketi üretir: dist/takip_pdf_excel-<sürüm>.tar.gz

Paket ÜRETMEDEN ÖNCE DENETLER; bir koşul bozuksa paket vermez. Her denetim,
kullanıcıda bir kez yaşanmış ya da yaşanabilecek bir arızayı önler. Yeni bir
kural öğrenildiğinde buraya denetim ekleyin ve tests/test_paketle.py içinde
o denetimi BİLEREK BOZUP attığını sınayın.

.zip değil .tar.gz: zip çalıştırma iznini her arşivleyicide korumaz.
"""
import os
import re
import subprocess
import sys
import tarfile

KOK = os.path.dirname(os.path.abspath(__file__))
PAKET_ADI = "takip_pdf_excel"

ZORUNLU = [
    "main.py", "calistir.sh", "kisayol_olustur.sh", "Takip PDF Excel.desktop", "OKUBENI.txt",
    "app/__init__.py", "app/ayristirici.py", "app/excel.py", "app/pdf_kelime.py", "app/sunucu.py",
    "web/index.html", "lib/pypdf/__init__.py", "lib/openpyxl/__init__.py",
    "lib/et_xmlfile/__init__.py", "lib_ek/typing_extensions.py",
]
CALISTIRILABILIR = ["calistir.sh", "kisayol_olustur.sh", "Takip PDF Excel.desktop"]
# Pakete girmeyecekler: geliştirme dosyaları ve kullanıcı verisi.
DISARIDA_DIZIN = {"tests", "dist", "__pycache__", ".git"}
DISARIDA_DOSYA = {"paketle.py", "GELISTIRME_NOTLARI.md", ".gitignore", "acilis_kaydi.txt"}
VERI_UZANTILARI = (".pdf", ".xlsx", ".xls", ".ods", ".csv", ".db", ".json")
DERLENMIS = (".so", ".pyd", ".dll", ".pyc")


def paket_dosyalari(kok):
    """Pakete girecek dosyaların göreli yolları."""
    sonuc = []
    for dizin, alt, dosyalar in os.walk(kok):
        alt[:] = sorted(a for a in alt if a not in DISARIDA_DIZIN)
        for d in sorted(dosyalar):
            yol = os.path.relpath(os.path.join(dizin, d), kok).replace(os.sep, "/")
            if yol in DISARIDA_DOSYA or d in DISARIDA_DOSYA:
                continue
            sonuc.append(yol)
    return sonuc


def denetle(kok):
    """Hata listesi döndürür; boşsa paket üretilebilir."""
    hatalar = []
    dosyalar = paket_dosyalari(kok)
    kume = set(dosyalar)

    for z in ZORUNLU:
        if z not in kume:
            hatalar.append("Zorunlu dosya yok: " + z)

    for c in CALISTIRILABILIR:
        yol = os.path.join(kok, c)
        if os.path.exists(yol) and not os.access(yol, os.X_OK):
            hatalar.append("Çalıştırılabilir değil (kullanıcıda 'hiç açılmıyor' olur): " + c)

    for d in dosyalar:
        if d.endswith((".sh", ".desktop")):
            with open(os.path.join(kok, d), "rb") as f:
                if b"\r" in f.read():
                    hatalar.append("CRLF satır sonu var (Linux'ta betik bozulur): " + d)
        if d.endswith(".sh"):
            r = subprocess.run(["sh", "-n", os.path.join(kok, d)], capture_output=True, text=True)
            if r.returncode != 0:
                hatalar.append("Kabuk sözdizimi hatası: {}: {}".format(d, r.stderr.strip()))
        low = d.lower()
        if low.endswith(VERI_UZANTILARI) or os.path.basename(d) == "acilis_kaydi.txt":
            hatalar.append("Kullanıcı verisi / çıktı pakete sızıyor: " + d)
        if low.endswith(DERLENMIS):
            hatalar.append("Derlenmiş dosya var (o makinede çalışmaz): " + d)
        if "GELISTIRME" in d.upper() or d.startswith("tests/"):
            hatalar.append("Geliştirme dosyası pakete sızıyor: " + d)

    html = os.path.join(kok, "web", "index.html")
    if os.path.exists(html):
        with open(html, encoding="utf-8") as f:
            dis = re.findall(r"""(?:src|href)\s*=\s*["']?(https?://[^"' >]+)""", f.read())
        if dis:
            hatalar.append("Arayüz internetten dosya çekiyor (kurumsal ağda açılmaz): " + ", ".join(dis))

    main = os.path.join(kok, "main.py")
    if os.path.exists(main):
        with open(main, encoding="utf-8") as f:
            m = f.read()
        if not re.search(r"sys\.path\.append\(os\.path\.join\(BASE_DIR,\s*\"lib_ek\"\)\)", m):
            hatalar.append("lib_ek sys.path'in SONUNA eklenmiyor (sistem paketini gölgeler; "
                           "Pillow/openpyxl arızası)")
    return hatalar


def testleri_calistir(kok):
    r = subprocess.run([sys.executable, "-m", "unittest", "discover", "-s", "tests"],
                       cwd=kok, capture_output=True, text=True)
    return r.returncode == 0, r.stderr[-3000:]


def paketle(kok=KOK):
    hatalar = denetle(kok)
    tamam, cikti = testleri_calistir(kok)
    if not tamam:
        hatalar.append("Gerileme testleri geçmedi:\n" + cikti)
    if hatalar:
        print("PAKET ÜRETİLMEDİ:")
        for h in hatalar:
            print("  -", h)
        return None

    sys.path.insert(0, kok)
    from app import SURUM
    os.makedirs(os.path.join(kok, "dist"), exist_ok=True)
    hedef = os.path.join(kok, "dist", "{}-{}.tar.gz".format(PAKET_ADI, SURUM))

    def filtre(ti):
        ti.uid = ti.gid = 0
        ti.uname = ti.gname = ""
        if ti.isfile():
            ti.mode = 0o755 if os.path.basename(ti.name) in CALISTIRILABILIR or ti.name.endswith("main.py") else 0o644
        return ti

    with tarfile.open(hedef, "w:gz") as tar:
        for d in paket_dosyalari(kok):
            tar.add(os.path.join(kok, d), arcname=PAKET_ADI + "/" + d, filter=filtre)

    # Üretilen arşivi de denetle: izinler gerçekten taşındı mı?
    with tarfile.open(hedef) as tar:
        for c in CALISTIRILABILIR:
            if not tar.getmember(PAKET_ADI + "/" + c).mode & 0o100:
                os.remove(hedef)
                print("PAKET ÜRETİLMEDİ: arşivde çalıştırma izni yok:", c)
                return None
    print("Paket hazır:", hedef)
    return hedef


if __name__ == "__main__":
    sys.exit(0 if paketle() else 1)
