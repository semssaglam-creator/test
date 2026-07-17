#!/usr/bin/env python3
"""OCR araclarini tek adimda kurar (Windows icin).

Ne yapar:
  1. Poppler'i (pdftoppm) indirir ve uygulamanin 'araclar' klasorune acar
     (kurulum/yonetici yetkisi GEREKMEZ).
  2. Tesseract kurulu degilse kurulum dosyasini indirip baslatir; kurulum
     sihirbazinda "Additional language data" altindan TURKISH isaretlenmelidir.
  3. Sonunda araclarin bulunup bulunmadigini raporlar.

Linux'ta calistirilirsa paket yoneticisi komutunu gosterir.
"""
import os
import platform
import subprocess
import sys
import tempfile
import urllib.request
import zipfile

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)
ARACLAR_DIR = os.path.join(BASE_DIR, "araclar")

from app import ocr  # noqa: E402

# Bilinen iyi surumler (adresler degisirse asagidaki 'latest' denemesi devreye girer)
POPPLER_SABIT = ("https://github.com/oschwartz10612/poppler-windows/releases/"
                 "download/v24.08.0-0/Release-24.08.0-0.zip")
POPPLER_API = ("https://api.github.com/repos/oschwartz10612/poppler-windows/"
               "releases/latest")
TESSERACT_SABIT = ("https://digi.bib.uni-mannheim.de/tesseract/"
                   "tesseract-ocr-w64-setup-5.5.0.20241111.exe")
TESSERACT_SAYFA = "https://github.com/UB-Mannheim/tesseract/wiki"


def indir(url, hedef, aciklama):
    print(f"  Indiriliyor: {aciklama}\n    {url}")

    def ilerleme(blok, boyut, toplam):
        if toplam > 0:
            yuzde = min(100, blok * boyut * 100 // toplam)
            print(f"\r    %{yuzde}", end="", flush=True)

    urllib.request.urlretrieve(url, hedef, reporthook=ilerleme)
    print("\r    Tamamlandi.        ")


def poppler_url_bul():
    """GitHub'dan en son surumun zip adresini dener; olmazsa sabit surum."""
    try:
        import json
        with urllib.request.urlopen(POPPLER_API, timeout=15) as y:
            veri = json.load(y)
        for v in veri.get("assets", []):
            if v.get("name", "").lower().endswith(".zip"):
                return v["browser_download_url"]
    except Exception:  # noqa: BLE001 - API erisilemezse sabit adrese dus
        pass
    return POPPLER_SABIT


def poppler_kur():
    if ocr.pdftoppm_yolu():
        print("+ Poppler zaten mevcut:", ocr.pdftoppm_yolu())
        return True
    print("- Poppler kuruluyor (kurulum yetkisi gerekmez)...")
    os.makedirs(ARACLAR_DIR, exist_ok=True)
    url = poppler_url_bul()
    try:
        with tempfile.TemporaryDirectory() as tmp:
            zip_yolu = os.path.join(tmp, "poppler.zip")
            indir(url, zip_yolu, "Poppler (PDF -> goruntu araci)")
            with zipfile.ZipFile(zip_yolu) as z:
                z.extractall(os.path.join(ARACLAR_DIR, "poppler"))
    except Exception as exc:  # noqa: BLE001
        print("  HATA: Poppler indirilemedi:", exc)
        print("  Elle kurulum: su zip'i indirip 'araclar' klasorune acin:")
        print("   ", POPPLER_SABIT)
        return False
    yol = ocr.pdftoppm_yolu()
    print("+ Poppler kuruldu:", yol or "(bulunamadi, klasoru kontrol edin)")
    return bool(yol)


def tesseract_kur():
    if ocr.tesseract_yolu():
        print("+ Tesseract zaten mevcut:", ocr.tesseract_yolu())
        return True
    print("- Tesseract kurulum dosyasi indiriliyor...")
    hedef = os.path.join(ARACLAR_DIR, "tesseract_kurulum.exe")
    os.makedirs(ARACLAR_DIR, exist_ok=True)
    try:
        indir(TESSERACT_SABIT, hedef, "Tesseract kurulum dosyasi")
    except Exception as exc:  # noqa: BLE001
        print("  HATA: Indirilemedi:", exc)
        print("  Elle kurulum: su sayfadan 64-bit kurulumu indirin:")
        print("   ", TESSERACT_SAYFA)
        return False
    print("""
  ONEMLI - Kurulum sihirbazinda:
    * "Additional language data (download)" bolumunu acin ve
      TURKISH kutusunu isaretleyin.
    * Kurulum yerini degistirmenize gerek yok.
  Kurulum bitince bu pencereye donup Enter'a basin.
""")
    try:
        subprocess.Popen([hedef])
    except OSError as exc:
        print("  Kurulum baslatilamadi:", exc, "\n  Su dosyayi elle calistirin:", hedef)
    input("  Tesseract kurulumu bittiginde Enter'a basin... ")
    try:
        os.remove(hedef)
    except OSError:
        pass
    yol = ocr.tesseract_yolu()
    print("+ Tesseract:", yol or "BULUNAMADI (kurulum tamamlanmamis olabilir)")
    return bool(yol)


def main():
    print("=" * 60)
    print("Fatura Inceleme - OCR Kurulumu")
    print("=" * 60)

    if platform.system() != "Windows":
        print("""Bu betik Windows icindir. Linux'ta OCR icin:
    sudo apt install tesseract-ocr tesseract-ocr-tur poppler-utils
Kurulum yetkiniz yoksa taranmis faturalari Windows makinede isleyin.""")
        return

    p = poppler_kur()
    t = tesseract_kur()

    print("-" * 60)
    d = ocr.durum()
    if d["hazir"]:
        print("SONUC: OCR HAZIR." + ("" if d["turkce"] else
              " (Uyari: Turkce dil paketi bulunamadi; Tesseract kurulumunu"
              " Turkish secenegiyle yineleyin.)"))
        print("Uygulamayi (yeniden) baslatin; taranmis faturalar artik okunur.")
        print("Bekleyenler icin: Ayarlar / Durum > 'Tumunu Simdi Oku'.")
    else:
        print("SONUC: Eksik kaldi -> Poppler:", "tamam" if p else "EKSIK",
              "| Tesseract:", "tamam" if t else "EKSIK")
        print("Ayrintili yardim: KULLANIM_KILAVUZU.md")


if __name__ == "__main__":
    try:
        main()
    finally:
        if platform.system() == "Windows":
            input("\nKapatmak icin Enter'a basin... ")
