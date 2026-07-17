"""Taranmis PDF'ler icin OCR katmani (istege bagli).

Harici iki arac kullanilir; ikisi de kurulu degilse fatura 'OCR bekliyor'
olarak isaretlenir, uygulama calismaya devam eder:

  - Poppler (pdftoppm): PDF sayfalarini goruntuye cevirir
  - Tesseract          : goruntudeki metni okur (tur dil paketiyle)

Araclar su siralamayla aranir:
  1. Uygulamanin yanindaki 'araclar' klasoru (Windows'ta kurulumsuz tasima:
     Tesseract ve Poppler zip'leri bu klasore acilir)
  2. PATH
  3. Bilinen kurulum yerleri (C:\\Program Files\\Tesseract-OCR vb.)
"""
import glob
import os
import shutil
import subprocess
import tempfile

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ARACLAR_DIR = os.path.join(BASE_DIR, "araclar")
GECICI_DIR = os.path.join(BASE_DIR, "gecici")

OCR_COZUNURLUK = 300  # dpi; dusurmek hizlandirir, dogrulugu azaltir
OCR_ZAMAN_ASIMI = 120  # saniye / sayfa


def _exe_bul(ad, ek_yollar):
    """Verilen adli calistirilabiliri araclar/, PATH ve bilinen yollarda arar."""
    exe = ad + (".exe" if os.name == "nt" else "")
    for kalip in (
        os.path.join(ARACLAR_DIR, exe),
        os.path.join(ARACLAR_DIR, "*", exe),
        os.path.join(ARACLAR_DIR, "*", "bin", exe),
        os.path.join(ARACLAR_DIR, "*", "*", "bin", exe),
    ):
        eslesen = glob.glob(kalip)
        if eslesen:
            return eslesen[0]
    yol = shutil.which(ad)
    if yol:
        return yol
    for aday in ek_yollar:
        if os.path.isfile(aday):
            return aday
    return ""


def tesseract_yolu():
    return _exe_bul("tesseract", [
        r"C:\Program Files\Tesseract-OCR\tesseract.exe",
        r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
        os.path.expanduser(r"~\AppData\Local\Programs\Tesseract-OCR\tesseract.exe"),
        os.path.expanduser(r"~\AppData\Local\Tesseract-OCR\tesseract.exe"),
    ])


def pdftoppm_yolu():
    return _exe_bul("pdftoppm", [
        r"C:\Program Files\poppler\Library\bin\pdftoppm.exe",
        "/usr/bin/pdftoppm",
        "/usr/local/bin/pdftoppm",
    ])


def _calistir(komut, zaman_asimi=OCR_ZAMAN_ASIMI):
    return subprocess.run(
        komut, capture_output=True, timeout=zaman_asimi,
        creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
    )


def _dil_secimi(tesseract):
    """Kurulu dillere gore -l parametresini belirler (tur varsa tur+eng)."""
    try:
        cikti = _calistir([tesseract, "--list-langs"], zaman_asimi=20)
        diller = cikti.stdout.decode("utf-8", "replace").lower()
    except Exception:  # noqa: BLE001
        return ""
    if "tur" in diller.split():
        return "tur+eng" if "eng" in diller.split() else "tur"
    return ""


def durum():
    """Arayuzde gosterilecek OCR hazirlik bilgisi."""
    tesseract = tesseract_yolu()
    pdftoppm = pdftoppm_yolu()
    bilgi = {
        "tesseract": tesseract, "pdftoppm": pdftoppm,
        "hazir": bool(tesseract and pdftoppm), "turkce": False,
    }
    if tesseract:
        bilgi["turkce"] = "tur" in _dil_secimi(tesseract)
    return bilgi


def pdf_ocr(pdf_bytes):
    """Taranmis PDF'i OCR ile metne cevirir. Donus: (sayfa_listesi, hata)."""
    tesseract = tesseract_yolu()
    pdftoppm = pdftoppm_yolu()
    if not tesseract or not pdftoppm:
        eksik = []
        if not tesseract:
            eksik.append("Tesseract")
        if not pdftoppm:
            eksik.append("Poppler (pdftoppm)")
        return [], ("Taranmis PDF icin OCR araci eksik: " + ", ".join(eksik) +
                    ". Kurulum icin kullanim kilavuzuna bakin.")

    os.makedirs(GECICI_DIR, exist_ok=True)
    dil = _dil_secimi(tesseract)
    with tempfile.TemporaryDirectory(dir=GECICI_DIR) as tmp:
        pdf_yolu = os.path.join(tmp, "belge.pdf")
        with open(pdf_yolu, "wb") as f:
            f.write(pdf_bytes)
        try:
            sonuc = _calistir(
                [pdftoppm, "-r", str(OCR_COZUNURLUK), "-gray", "-png",
                 pdf_yolu, os.path.join(tmp, "sayfa")],
                zaman_asimi=OCR_ZAMAN_ASIMI * 3,
            )
        except subprocess.TimeoutExpired:
            return [], "PDF goruntuye cevrilirken zaman asimi olustu."
        if sonuc.returncode != 0:
            return [], "PDF goruntuye cevrilemedi: " + \
                sonuc.stderr.decode("utf-8", "replace")[:200]

        sayfalar = sorted(glob.glob(os.path.join(tmp, "sayfa*.png")))
        if not sayfalar:
            return [], "PDF'ten goruntu uretilemedi."

        metinler = []
        for resim in sayfalar:
            komut = [tesseract, resim, "stdout"]
            if dil:
                komut += ["-l", dil]
            try:
                sonuc = _calistir(komut)
            except subprocess.TimeoutExpired:
                return [], "OCR sirasinda zaman asimi olustu."
            if sonuc.returncode != 0:
                return [], "OCR hatasi: " + sonuc.stderr.decode("utf-8", "replace")[:200]
            metinler.append(sonuc.stdout.decode("utf-8", "replace"))

    return metinler, ""
