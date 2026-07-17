"""PDF'ten metin cikarma.

Once gomulu pypdf ile metin katmani denenir. Sayfa basina anlamli metin
yoksa PDF taranmis kabul edilir ve OCR katmanina (ocr.py) devredilir.
"""
import io

from . import ocr

# Sayfa basina bu kadar karakterden az metin cikarsa "taranmis" sayilir
MIN_KARAKTER_SAYFA = 40


def metin_katmani_oku(pdf_bytes):
    """(metin, sayfa_sayisi) dondurur; okunamazsa ValueError firlatir."""
    import pypdf

    okuyucu = pypdf.PdfReader(io.BytesIO(pdf_bytes))
    sayfalar = [(sayfa.extract_text() or "") for sayfa in okuyucu.pages]
    return "\n".join(sayfalar), max(len(sayfalar), 1)


def pdf_oku(pdf_bytes):
    """PDF iceriginden metin cikarir.

    Donus: (metin, kaynak, hata)
      kaynak: 'metin' | 'ocr' | ''
      hata  : bos degilse metin cikarilamama nedeni (OCR araci yok vb.)
    """
    if not pdf_bytes.startswith(b"%PDF"):
        return "", "", "Dosya bir PDF degil."

    try:
        metin, sayfa_sayisi = metin_katmani_oku(pdf_bytes)
    except Exception as exc:  # noqa: BLE001 - bozuk PDF'ler OCR'a dussun
        metin, sayfa_sayisi = "", 1
        okuma_hatasi = f"Metin katmani okunamadi: {exc}"
    else:
        okuma_hatasi = ""

    if len(metin.strip()) >= MIN_KARAKTER_SAYFA * sayfa_sayisi:
        return metin, "metin", ""

    # Metin katmani yok/yetersiz -> taranmis PDF, OCR dene
    ocr_metin, ocr_hata = ocr.pdf_ocr(pdf_bytes)
    if ocr_metin:
        return ocr_metin, "ocr", ""
    return "", "", ocr_hata or okuma_hatasi or "PDF'te okunabilir metin bulunamadi."
