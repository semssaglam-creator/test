"""KDV inceleme calismasini Excel'e aktarir.

Uretilen dosya, elde kullanilan calismanin duzenini korur:
    - Her yil icin bir sayfa: elestirili beyan / elestiri girisi / ham beyan
    - Uc ozet tablo: elestirili, beyan edilen ve ikisinin farki
    - Cok yilli dosyalarda ek bir "Ozet" sayfasi: tum donemler tek tabloda
"""
import os
import sys

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LIB_DIR = os.path.join(BASE_DIR, "lib")
if LIB_DIR not in sys.path:
    sys.path.insert(0, LIB_DIR)

from openpyxl import Workbook
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter

from .satirlar import AYLAR, AYLAR_BUYUK, BEYAN_SATIRLARI, ELESTIRI_ALANLARI, OZET_KOLONLARI

FONT = Font(name="Calibri", size=10)
FONT_BOLD = Font(name="Calibri", size=10, bold=True)
FONT_BASLIK = Font(name="Calibri", size=11, bold=True)
FONT_FARK = Font(name="Calibri", size=10, bold=True, color="C00000")

THIN = Side(style="thin", color="999999")
BORDER = Border(left=THIN, right=THIN, top=THIN, bottom=THIN)

SOL = Alignment(horizontal="left", vertical="center", wrap_text=True)
ORTA = Alignment(horizontal="center", vertical="center", wrap_text=True)
SAG = Alignment(horizontal="right", vertical="center")

DOLGU_BASLIK = PatternFill("solid", fgColor="D9E1F2")
DOLGU_ELESTIRI = PatternFill("solid", fgColor="FFF2CC")
DOLGU_FARK = PatternFill("solid", fgColor="FCE4D6")
DOLGU_TOPLAM = PatternFill("solid", fgColor="E2EFDA")

SAYI_BICIMI = "#,##0.00"


def _yaz(ws, satir, sutun, deger, font=FONT, hiza=SAG, dolgu=None, bicim=SAYI_BICIMI):
    h = ws.cell(satir, sutun, deger)
    h.font = font
    h.alignment = hiza
    h.border = BORDER
    if dolgu:
        h.fill = dolgu
    if isinstance(deger, (int, float)):
        h.number_format = bicim
    return h


def _baslik_satiri(ws, satir, metin, genislik=14):
    h = ws.cell(satir, 1, metin)
    h.font = FONT_BASLIK
    h.alignment = SOL
    ws.merge_cells(start_row=satir, start_column=1, end_row=satir, end_column=genislik)
    return satir + 1


def _ozet_tablo(ws, satir, baslik, donemler, blok, dolgu=None, fark_mi=False):
    """Ay x kolon ozet tablosu yazar (elestirili / beyan / fark bloklari)."""
    satir = _baslik_satiri(ws, satir, baslik, len(OZET_KOLONLARI) + 2)
    _yaz(ws, satir, 1, "Dönem", FONT_BOLD, ORTA, DOLGU_BASLIK)
    for i, (_alan, etiket) in enumerate(OZET_KOLONLARI):
        _yaz(ws, satir, i + 2, etiket, FONT_BOLD, ORTA, DOLGU_BASLIK)
    satir += 1

    ilk_veri = satir
    for d in donemler:
        _yaz(ws, satir, 1, f"{d['yil']}/{d['ay_adi']}", FONT, SOL, dolgu)
        for i, (alan, _etiket) in enumerate(OZET_KOLONLARI):
            deger = d[blok].get(alan, 0.0)
            font = FONT_FARK if (fark_mi and abs(deger) > 0.005) else FONT
            _yaz(ws, satir, i + 2, deger, font, SAG, dolgu)
        satir += 1

    _yaz(ws, satir, 1, "Toplam", FONT_BOLD, SOL, DOLGU_TOPLAM)
    for i, (alan, _etiket) in enumerate(OZET_KOLONLARI):
        harf = get_column_letter(i + 2)
        if alan in ("onceki_devir", "sonraki_devir"):
            # Devir stok kalemidir; toplanmaz, donem sonu degeri gosterilir
            formul = f"={harf}{satir - 1}" if alan == "sonraki_devir" else f"={harf}{ilk_veri}"
        else:
            formul = f"=SUM({harf}{ilk_veri}:{harf}{satir - 1})"
        _yaz(ws, satir, i + 2, formul, FONT_BOLD, SAG, DOLGU_TOPLAM)
    return satir + 2


def _yil_sayfasi(wb, yil_kaydi, donemler):
    yil = yil_kaydi["yil"]
    ws = wb.create_sheet(str(yil))
    ws.column_dimensions["A"].width = 48
    for i in range(2, 15):
        ws.column_dimensions[get_column_letter(i)].width = 14
    ws.freeze_panes = "B2"

    satir = 1
    _yaz(ws, satir, 1, f"{yil} Dönemi", FONT_BASLIK, SOL, DOLGU_BASLIK)
    for i, ay in enumerate(AYLAR_BUYUK):
        _yaz(ws, satir, i + 2, ay, FONT_BOLD, ORTA, DOLGU_BASLIK)
    _yaz(ws, satir, 14, "TOPLAM", FONT_BOLD, ORTA, DOLGU_BASLIK)
    satir += 1

    # --- Elestirili (yeniden hesaplanmis) beyan ---
    satir = _baslik_satiri(ws, satir, "ELEŞTİRİLİ (YENİDEN HESAPLANMIŞ) BEYAN")
    elestirili_alanlar = [
        ("matrah", "KDV Matrahı Toplamı"),
        ("hesaplanan", "Hesaplanan KDV"),
        ("ilave_edilecek", "İlave Edilecek KDV"),
        ("toplam_kdv", "Toplam KDV"),
        ("onceki_devir", "Önceki Dönemden Devreden İnd. KDV"),
        ("bu_donem_indirim", "Bu Döneme Ait İndirilecek KDV"),
        ("diger_indirim", "Bu Döneme Ait İnd. Diğer KDV"),
        ("indirimler", "İndirimler Toplamı"),
        ("odenecek", "Ödenmesi Gereken KDV"),
        ("sonraki_devir", "Sonraki Döneme Devreden KDV"),
        ("iade", "İade Edilmesi Gereken KDV"),
        ("tecil_edilecek", "Tecil Edilecek KDV"),
    ]
    yil_donemleri = [d for d in donemler if d["yil"] == yil]
    for alan, etiket in elestirili_alanlar:
        _yaz(ws, satir, 1, etiket, FONT, SOL)
        for i, d in enumerate(yil_donemleri):
            _yaz(ws, satir, i + 2, d["elestirili"].get(alan, 0.0))
        _yaz(ws, satir, 14, f"=SUM(B{satir}:M{satir})", FONT_BOLD, SAG, DOLGU_TOPLAM)
        satir += 1
    satir += 1

    # --- Elestiri girisi ---
    satir = _baslik_satiri(ws, satir, "İNCELEME TESPİTLERİ (ELEŞTİRİ)")
    elestiri = yil_kaydi.get("elestiri") or {}
    for alan, etiket in ELESTIRI_ALANLARI:
        _yaz(ws, satir, 1, etiket, FONT, SOL, DOLGU_ELESTIRI)
        dizi = elestiri.get(alan) or [0.0] * 12
        for i in range(len(yil_donemleri)):
            _yaz(ws, satir, i + 2, float(dizi[i] or 0), FONT, SAG, DOLGU_ELESTIRI)
        _yaz(ws, satir, 14, f"=SUM(B{satir}:M{satir})", FONT_BOLD, SAG, DOLGU_TOPLAM)
        satir += 1
    _yaz(ws, satir, 1, "Uygulanan KDV Oranı (%)", FONT, SOL, DOLGU_ELESTIRI)
    oranlar = elestiri.get("kdv_orani") or [None] * 12
    for i in range(len(yil_donemleri)):
        _yaz(ws, satir, i + 2, float(oranlar[i]) if oranlar[i] is not None else "",
             FONT, SAG, DOLGU_ELESTIRI, bicim="0.##")
    satir += 2

    # --- Ham beyan verisi ---
    satir = _baslik_satiri(ws, satir, "BEYAN EDİLEN DEĞERLER (SİSTEMDEN ALINAN)")
    _yaz(ws, satir, 1, "DÖNEMİ", FONT_BOLD, SOL, DOLGU_BASLIK)
    for i, ay in enumerate(AYLAR_BUYUK):
        _yaz(ws, satir, i + 2, ay, FONT_BOLD, ORTA, DOLGU_BASLIK)
    _yaz(ws, satir, 14, "TOPLAM", FONT_BOLD, ORTA, DOLGU_BASLIK)
    satir += 1
    beyan = yil_kaydi.get("beyan") or {}
    for kod, etiket, baslik in BEYAN_SATIRLARI:
        if baslik:
            _yaz(ws, satir, 1, etiket, FONT_BOLD, SOL, DOLGU_BASLIK)
            for i in range(1, 14):
                _yaz(ws, satir, i + 1, "", FONT, SAG, DOLGU_BASLIK)
            satir += 1
            continue
        _yaz(ws, satir, 1, etiket, FONT, SOL)
        dizi = beyan.get(kod) or [0.0] * 12
        for i in range(12):
            _yaz(ws, satir, i + 2, float(dizi[i] or 0))
        _yaz(ws, satir, 14, f"=SUM(B{satir}:M{satir})", FONT_BOLD, SAG, DOLGU_TOPLAM)
        satir += 1
    satir += 1

    # --- Uc ozet tablo ---
    satir = _ozet_tablo(ws, satir, "ÖZET — ELEŞTİRİLİ", yil_donemleri, "elestirili")
    satir = _ozet_tablo(ws, satir, "ÖZET — BEYAN EDİLEN", yil_donemleri, "beyan")
    _ozet_tablo(ws, satir, "FARK (ELEŞTİRİLİ − BEYAN)", yil_donemleri, "fark",
                DOLGU_FARK, fark_mi=True)
    return ws


def _ozet_sayfasi(wb, inceleme, sonuc, bulgular):
    ws = wb.create_sheet("Özet", 0)
    ws.column_dimensions["A"].width = 20
    for i in range(2, 11):
        ws.column_dimensions[get_column_letter(i)].width = 16

    satir = 1
    _yaz(ws, satir, 1, "KDV İNCELEME ÇALIŞMASI", FONT_BASLIK, SOL, DOLGU_BASLIK)
    ws.merge_cells(start_row=satir, start_column=1, end_row=satir, end_column=9)
    satir += 2
    for etiket, deger in (("Mükellef", inceleme.get("ad_unvan", "")),
                          ("VKN/TCKN", inceleme.get("vkn_tckn", "")),
                          ("Dosya", inceleme.get("ad", ""))):
        _yaz(ws, satir, 1, etiket, FONT_BOLD, SOL)
        _yaz(ws, satir, 2, deger, FONT, SOL)
        satir += 1
    satir += 1

    donemler = sonuc["donemler"]
    satir = _ozet_tablo(ws, satir, "TÜM DÖNEMLER — ELEŞTİRİLİ", donemler, "elestirili")
    satir = _ozet_tablo(ws, satir, "TÜM DÖNEMLER — BEYAN EDİLEN", donemler, "beyan")
    satir = _ozet_tablo(ws, satir, "TÜM DÖNEMLER — FARK", donemler, "fark",
                        DOLGU_FARK, fark_mi=True)

    if bulgular:
        satir = _baslik_satiri(ws, satir, "BEYAN TUTARLILIK BULGULARI", 9)
        for b in bulgular:
            _yaz(ws, satir, 1, b["donem"], FONT_BOLD, SOL, DOLGU_FARK)
            h = _yaz(ws, satir, 2, b["mesaj"], FONT, SOL, DOLGU_FARK)
            h.alignment = SOL
            ws.merge_cells(start_row=satir, start_column=2, end_row=satir, end_column=9)
            satir += 1
    return ws


def calisma_olustur(dosya_yolu, inceleme, yillar, sonuc, bulgular=None):
    """Excel calisma dosyasini uretir ve yola yazar."""
    wb = Workbook()
    wb.remove(wb.active)
    for yil_kaydi in sorted(yillar, key=lambda y: y["yil"]):
        _yil_sayfasi(wb, yil_kaydi, sonuc["donemler"])
    _ozet_sayfasi(wb, inceleme, sonuc, bulgular or [])
    os.makedirs(os.path.dirname(dosya_yolu), exist_ok=True)
    wb.save(dosya_yolu)
    return dosya_yolu
