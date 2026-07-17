"""PDF'ten metin cikarma.

Once gomulu pypdf ile metin katmani denenir. Sayfa basina anlamli metin
yoksa PDF taranmis kabul edilir ve OCR katmanina (ocr.py) devredilir.
Metin sayfa sayfa dondurulur; boylece tek PDF icindeki birden fazla
fatura, sayfa kimliklerine gore ayristirilabilir (ayristirici.faturalari_bol).
"""
import io

from . import ocr

# Sayfa basina bu kadar karakterden az metin cikarsa "taranmis" sayilir
MIN_KARAKTER_SAYFA = 40


def metin_katmani_oku(pdf_bytes):
    """Sayfa metinlerinin listesini dondurur; okunamazsa hata firlatir."""
    import pypdf

    okuyucu = pypdf.PdfReader(io.BytesIO(pdf_bytes))
    return [(sayfa.extract_text() or "") for sayfa in okuyucu.pages]


def pdf_oku(pdf_bytes):
    """PDF iceriginden sayfa metinlerini cikarir.

    Donus: (sayfalar, kaynak, hata)
      sayfalar: sayfa basina metin listesi (bos liste = okunamadi)
      kaynak  : 'metin' | 'ocr' | ''
      hata    : bos degilse metin cikarilamama nedeni (OCR araci yok vb.)
    """
    if not pdf_bytes.startswith(b"%PDF"):
        return [], "", "Dosya bir PDF degil."

    try:
        sayfalar = metin_katmani_oku(pdf_bytes)
    except Exception as exc:  # noqa: BLE001 - bozuk PDF'ler OCR'a dussun
        sayfalar = []
        okuma_hatasi = f"Metin katmani okunamadi: {exc}"
    else:
        okuma_hatasi = ""

    toplam = sum(len(s.strip()) for s in sayfalar)
    if sayfalar and toplam >= MIN_KARAKTER_SAYFA * len(sayfalar):
        return sayfalar, "metin", ""

    # Metin katmani yok/yetersiz -> taranmis PDF, OCR dene
    ocr_sayfalar, ocr_hata = ocr.pdf_ocr(pdf_bytes)
    if ocr_sayfalar:
        return ocr_sayfalar, "ocr", ""
    return [], "", ocr_hata or okuma_hatasi or "PDF'te okunabilir metin bulunamadi."
