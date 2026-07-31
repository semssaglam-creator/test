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

from .satirlar import (AYLAR, AYLAR_BUYUK, BEYAN_SATIRLARI, BEYAN_TOPLAM_TURLERI,
                       ELESTIRI_ALANLARI, OZET_KOLONLARI, TARHIYAT_KOLONLARI,
                       TOPLAM_TURLERI)

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
# Tarhiyat tablosunun vurgu renkleri (elde kullanilan tablodaki gibi)
DOLGU_SARI = PatternFill("solid", fgColor="FFFF99")
DOLGU_YESIL = PatternFill("solid", fgColor="C6E0B4")

SAYI_BICIMI = "#,##0.00"


def _yaz(ws, satir, sutun, deger, font=FONT, hiza=SAG, dolgu=None, bicim=SAYI_BICIMI):
    h = ws.cell(satir, sutun, deger)
    h.font = font
    h.alignment = hiza
    h.border = BORDER
    if dolgu:
        h.fill = dolgu
    if isinstance(deger, (int, float)) and bicim:
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

    # --- Toplam satiri (bkz. satirlar.TOPLAM_TURLERI)
    kodlar = [alan for alan, _e in OZET_KOLONLARI]
    harfler = {alan: get_column_letter(i + 2) for i, alan in enumerate(kodlar)}
    son_veri = satir - 1
    _yaz(ws, satir, 1, "Toplam", FONT_BOLD, SOL, DOLGU_TOPLAM)
    for i, alan in enumerate(kodlar):
        harf = harfler[alan]
        tur = TOPLAM_TURLERI.get(alan)
        if tur == "acilis":
            # Devir stok kalemidir; serinin acilis degeri gosterilir
            formul = f"={harf}{ilk_veri}"
        elif tur == "kapanis":
            formul = f"={harf}{son_veri}"
        elif tur == "duzeltilmis":
            # Indirimler her donemde onceki devri de icerir; sutun oldugu gibi
            # toplanirsa tasinan devir her ay yeniden sayilir. Acilis devri ile
            # donemlerde dogan indirimlerin toplami yazilir.
            onc = harfler.get("onceki_devir")
            bu = harfler.get("bu_donem_indirim_toplam")
            formul = (f"={onc}{ilk_veri}+SUM({bu}{ilk_veri}:{bu}{son_veri})"
                      if onc and bu else f"=SUM({harf}{ilk_veri}:{harf}{son_veri})")
        else:
            formul = f"=SUM({harf}{ilk_veri}:{harf}{son_veri})"
        _yaz(ws, satir, i + 2, formul, FONT_BOLD, SAG, DOLGU_TOPLAM)
    satir += 1

    _yaz(ws, satir, 1,
         "Toplam satırı: devir sütunları stok kalemidir, toplanmaz — önceki devir "
         "için serinin açılış, sonraki devir için kapanış değeri yazılır. İndirimler "
         "toplamı her dönemde önceki devri de içerdiğinden sütun toplamı taşınan "
         "devri tekrar tekrar sayar; bu nedenle açılış devri ile dönem indirimlerinin "
         "toplamı olarak hesaplanır.", FONT, SOL, bicim=None)
    ws.merge_cells(start_row=satir, start_column=1, end_row=satir,
                   end_column=len(OZET_KOLONLARI) + 1)
    ws.row_dimensions[satir].height = 28
    return satir + 2


def _satir_toplami(alan, satir, son_harf, satir_no, turler, bu_alan, diger_alan, onc_alan):
    """Bir satirin TOPLAM hucresine yazilacak formulu uretir.

    Devir ve kumulatif satirlar toplanmaz; acilis (ilk ay) veya kapanis (son ay)
    degeri gosterilir. Indirimler toplami her ay onceki devri de icerdiginden
    duz toplami tasinan devri tekrar sayar; acilis devri ile donem indirimleri
    toplanarak yazilir.
    """
    tur = turler.get(alan)
    if tur == "acilis":
        return f"=B{satir}"
    if tur == "kapanis":
        return f"={son_harf}{satir}"
    if tur == "duzeltilmis":
        onc = satir_no.get(onc_alan)
        bu = satir_no.get(bu_alan)
        diger = satir_no.get(diger_alan)
        if onc and bu:
            formul = f"=B{onc}+SUM(B{bu}:{son_harf}{bu})"
            if diger:
                formul += f"+SUM(B{diger}:{son_harf}{diger})"
            return formul
    return f"=SUM(B{satir}:{son_harf}{satir})"


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
    son_harf = get_column_letter(1 + max(len(yil_donemleri), 1))
    satir_no = {}
    for alan, etiket in elestirili_alanlar:
        _yaz(ws, satir, 1, etiket, FONT, SOL)
        for i, d in enumerate(yil_donemleri):
            _yaz(ws, satir, i + 2, d["elestirili"].get(alan, 0.0))
        satir_no[alan] = satir
        _yaz(ws, satir, 14, _satir_toplami(alan, satir, son_harf, satir_no,
                                           TOPLAM_TURLERI, "bu_donem_indirim",
                                           "diger_indirim", "onceki_devir"),
             FONT_BOLD, SAG, DOLGU_TOPLAM)
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
    beyan_satir_no = {}
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
        beyan_satir_no[kod] = satir
        _yaz(ws, satir, 14,
             _satir_toplami(kod, satir, "M", beyan_satir_no, BEYAN_TOPLAM_TURLERI,
                            "bu_donem_indirilecek", "diger_indirimler_toplami",
                            "onceki_donem_devreden"),
             FONT_BOLD, SAG, DOLGU_TOPLAM)
        satir += 1
    _yaz(ws, satir, 1,
         "TOPLAM sütunu: devir ve kümülatif satırlar toplanmaz — açılış ya da "
         "kapanış değeri yazılır. İndirimler toplamı, taşınan devri tekrar saymamak "
         "için açılış devri ile dönem indirimlerinin toplamı olarak hesaplanır.",
         FONT, SOL, bicim=None)
    ws.merge_cells(start_row=satir, start_column=1, end_row=satir, end_column=14)
    ws.row_dimensions[satir].height = 28
    satir += 2

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


def _tarhiyat_sayfasi(wb, inceleme, sonuc):
    """Elde kullanilan tarhiyat ozeti tablosunun karsiligi."""
    ws = wb.create_sheet("Tarhiyat Özeti")
    ws.column_dimensions["A"].width = 14
    for i in range(2, len(TARHIYAT_KOLONLARI) + 2):
        ws.column_dimensions[get_column_letter(i)].width = 16

    satir = 1
    _yaz(ws, satir, 1, "TARHİYAT ÖZETİ", FONT_BASLIK, SOL, DOLGU_BASLIK)
    ws.merge_cells(start_row=satir, start_column=1, end_row=satir,
                   end_column=len(TARHIYAT_KOLONLARI) + 1)
    satir += 2

    # Gruplanmis ust baslik
    _yaz(ws, satir, 1, "Dönemi", FONT_BOLD, ORTA, DOLGU_BASLIK)
    ws.merge_cells(start_row=satir, start_column=1, end_row=satir + 1, end_column=1)
    i = 0
    while i < len(TARHIYAT_KOLONLARI):
        j = i
        while (j + 1 < len(TARHIYAT_KOLONLARI)
               and TARHIYAT_KOLONLARI[j + 1][0] == TARHIYAT_KOLONLARI[i][0]):
            j += 1
        dolgu = _tarhiyat_dolgu(TARHIYAT_KOLONLARI[i][3]) or DOLGU_BASLIK
        # Once tum hucreler bicimlendirilir, birlestirme en sonda yapilir:
        # birlestirilen hucrelere sonradan yazilamaz
        for k in range(i + 2, j + 3):
            _yaz(ws, satir, k, "", FONT_BOLD, ORTA, dolgu, bicim=None)
        _yaz(ws, satir, i + 2, TARHIYAT_KOLONLARI[i][0], FONT_BOLD, ORTA, dolgu, bicim=None)
        if j > i:
            ws.merge_cells(start_row=satir, start_column=i + 2, end_row=satir, end_column=j + 2)
        i = j + 1
    satir += 1
    for idx, (grup, _kod, etiket, vurgu) in enumerate(TARHIYAT_KOLONLARI):
        dolgu = _tarhiyat_dolgu(vurgu) or DOLGU_BASLIK
        _yaz(ws, satir, idx + 2, "" if etiket == grup else etiket, FONT_BOLD, ORTA,
             dolgu, bicim=None)
    satir += 1

    ilk_veri = satir
    onceki_yil = None
    for d in sonuc["donemler"]:
        if d["yil"] != onceki_yil:
            _yaz(ws, satir, 1, f"{d['yil']} Dönemi", FONT_BOLD, SOL, DOLGU_BASLIK, bicim=None)
            for k in range(2, len(TARHIYAT_KOLONLARI) + 2):
                _yaz(ws, satir, k, "", FONT_BOLD, ORTA, DOLGU_BASLIK, bicim=None)
            satir += 1
            onceki_yil = d["yil"]
        _yaz(ws, satir, 1, d["ay_adi"], FONT, SOL)
        for idx, (_g, kod, _e, vurgu) in enumerate(TARHIYAT_KOLONLARI):
            font = FONT_FARK if vurgu == "vurgu1" else (FONT_BOLD if vurgu == "vurgu2" else FONT)
            _yaz(ws, satir, idx + 2, d["tarhiyat"][kod], font, SAG, _tarhiyat_dolgu(vurgu))
        satir += 1

    _yaz(ws, satir, 1, "Toplam", FONT_BOLD, SOL, DOLGU_TOPLAM, bicim=None)
    for idx, (_g, _kod, _e, vurgu) in enumerate(TARHIYAT_KOLONLARI):
        harf = get_column_letter(idx + 2)
        _yaz(ws, satir, idx + 2, f"=SUM({harf}{ilk_veri}:{harf}{satir - 1})",
             FONT_BOLD, SAG, _tarhiyat_dolgu(vurgu) or DOLGU_TOPLAM)
    satir += 2

    t = sonuc.get("tarhiyat_toplami") or {}
    for etiket, kod in (("Mükellefin fazladan beyan ettiği ödenecek KDV", "fazla_beyan_odenecek"),
                        ("Mükellefin talep etmediği iade tutarı", "eksik_talep_iade")):
        if t.get(kod, 0):
            _yaz(ws, satir, 1, etiket, FONT, SOL, DOLGU_FARK, bicim=None)
            ws.merge_cells(start_row=satir, start_column=1, end_row=satir, end_column=4)
            _yaz(ws, satir, 5, t[kod], FONT_BOLD, SAG, DOLGU_FARK)
            _yaz(ws, satir, 6, "(tarhiyata dahil edilmemiştir)", FONT, SOL, DOLGU_FARK, bicim=None)
            satir += 1
    return ws


def _tarhiyat_dolgu(vurgu):
    if vurgu == "vurgu1":
        return DOLGU_SARI
    if vurgu == "vurgu2":
        return DOLGU_YESIL
    return None


def _yil_uyum_sayfasi(wb, sonuc):
    """Cok yilli incelemelerde yil bazinda beyan uyumu."""
    ws = wb.create_sheet("Yıl Uyumu")
    basliklar = [("Yıl", 8), ("Dönem", 8), ("Tespitli dönem", 14), ("Beyan matrah", 16),
                 ("Olması gereken matrah", 20), ("Matrah farkı", 16), ("Beyan ödenecek", 16),
                 ("Olması gereken ödenecek", 21), ("Re'sen tarhı gereken", 19),
                 ("Tespit etkisi", 15), ("Devir etkisi", 15), ("Beyan aritmetik farkı", 20),
                 ("Yıl sonu devir (beyan)", 20), ("Yıl sonu devir (olması gereken)", 26)]
    for i, (_ad, genislik) in enumerate(basliklar, start=1):
        ws.column_dimensions[get_column_letter(i)].width = genislik
    for i, (ad, _g) in enumerate(basliklar, start=1):
        _yaz(ws, 1, i, ad, FONT_BOLD, ORTA, DOLGU_BASLIK, bicim=None)
    kodlar = ["yil", "donem_sayisi", "tespit_donem_sayisi", "matrah_beyan",
              "matrah_olmasi_gereken", "matrah_farki", "odenecek_beyan",
              "odenecek_olmasi_gereken", "resen_tarhi_gereken", "tespit_etkisi",
              "devir_etkisi", "beyan_hatasi_etkisi", "devir_cikis_beyan", "devir_cikis"]
    tamsayi = {"yil", "donem_sayisi", "tespit_donem_sayisi"}
    satir = 2
    for s in sonuc.get("yil_uyumu") or []:
        for i, kod in enumerate(kodlar, start=1):
            sayim = kod in tamsayi
            _yaz(ws, satir, i, s[kod], FONT, ORTA if sayim else SAG,
                 bicim="0" if sayim else SAYI_BICIMI)
        satir += 1
    return ws


def _etki_sayfasi(wb, sonuc):
    """Her tespitin donem donem ayri ayri katkisi."""
    analiz = sonuc.get("kaynak_analizi") or {}
    kaynaklar = analiz.get("kaynaklar") or []
    if not kaynaklar:
        return None
    ws = wb.create_sheet("Tespit Etkisi")
    ws.column_dimensions["A"].width = 16
    for i in range(2, len(kaynaklar) + 4):
        ws.column_dimensions[get_column_letter(i)].width = 17

    satir = 1
    _yaz(ws, satir, 1, "TESPİTLERİN KAYNAK BAZINDA ETKİSİ", FONT_BASLIK, SOL, DOLGU_BASLIK)
    ws.merge_cells(start_row=satir, start_column=1, end_row=satir, end_column=len(kaynaklar) + 3)
    satir += 2

    _yaz(ws, satir, 1, "Tespit dönemi", FONT_BOLD, ORTA, DOLGU_BASLIK, bicim=None)
    for i, ad in enumerate(["Matrah ilavesi", "Hesaplanan KDV ilavesi", "İndirim reddi",
                            "Devir çıkarması", "Yüklenilen reddi", "Etkilenen dönem",
                            "Seri geneli ödenecek etkisi"], start=2):
        _yaz(ws, satir, i, ad, FONT_BOLD, ORTA, DOLGU_BASLIK, bicim=None)
    satir += 1
    for k in kaynaklar:
        _yaz(ws, satir, 1, k["etiket"], FONT_BOLD, SOL, DOLGU_ELESTIRI, bicim=None)
        for i, kod in enumerate(["matrah_ilave", "hesaplanan_kdv_ilave", "indirim_cikar",
                                 "devir_cikar", "yuklenilen_cikar"], start=2):
            _yaz(ws, satir, i, k[kod], FONT, SAG, DOLGU_ELESTIRI)
        _yaz(ws, satir, 7, k["etkilenen_donem_sayisi"], FONT, ORTA, DOLGU_ELESTIRI, bicim=None)
        _yaz(ws, satir, 8, k["toplam_odenecek_etkisi"], FONT_BOLD, SAG, DOLGU_FARK)
        satir += 1
    satir += 1

    etkilesim_var = analiz.get("etkilesim_var")
    for alan, baslik in (("odenecek", "ÖDENMESİ GEREKEN KDV'YE KATKI"),
                         ("sonraki_devir", "SONRAKİ DÖNEME DEVREDEN KDV'YE KATKI")):
        satir = _baslik_satiri(ws, satir, baslik, len(kaynaklar) + 3)
        _yaz(ws, satir, 1, "Dönem", FONT_BOLD, ORTA, DOLGU_BASLIK, bicim=None)
        for i, k in enumerate(kaynaklar, start=2):
            _yaz(ws, satir, i, k["etiket"], FONT_BOLD, ORTA, DOLGU_BASLIK, bicim=None)
        sutun = len(kaynaklar) + 2
        if etkilesim_var:
            _yaz(ws, satir, sutun, "Etkileşim", FONT_BOLD, ORTA, DOLGU_BASLIK, bicim=None)
            sutun += 1
        _yaz(ws, satir, sutun, "Toplam", FONT_BOLD, ORTA, DOLGU_TOPLAM, bicim=None)
        satir += 1
        for d in analiz.get("donemler") or []:
            if abs(d["toplam"].get(alan, 0)) < 0.005 and not any(
                    abs(d["paylar"][k["anahtar"]].get(alan, 0)) > 0.005 for k in kaynaklar):
                continue
            _yaz(ws, satir, 1, d["etiket"], FONT, SOL, bicim=None)
            for i, k in enumerate(kaynaklar, start=2):
                _yaz(ws, satir, i, d["paylar"][k["anahtar"]][alan], FONT, SAG)
            sutun = len(kaynaklar) + 2
            if etkilesim_var:
                _yaz(ws, satir, sutun, d["etkilesim"][alan], FONT, SAG)
                sutun += 1
            _yaz(ws, satir, sutun, d["toplam"][alan], FONT_BOLD, SAG, DOLGU_TOPLAM)
            satir += 1
        satir += 1

    if etkilesim_var:
        _yaz(ws, satir, 1,
             "Etkileşim: KDV hesabı doğrusal olmadığından (ödenecek/devreden eşiğinde "
             "alt-üst sınır) tespitlerin tek tek etkilerinin toplamı, hepsi birlikte "
             "uygulandığındaki farkı tam vermeyebilir. Aradaki bakiye kaynaklara "
             "dağıtılmaz, ayrıca gösterilir.", FONT, SOL, DOLGU_FARK, bicim=None)
        ws.merge_cells(start_row=satir, start_column=1, end_row=satir,
                       end_column=len(kaynaklar) + 3)
    return ws


def calisma_olustur(dosya_yolu, inceleme, yillar, sonuc, bulgular=None):
    """Excel calisma dosyasini uretir ve yola yazar."""
    wb = Workbook()
    wb.remove(wb.active)
    for yil_kaydi in sorted(yillar, key=lambda y: y["yil"]):
        _yil_sayfasi(wb, yil_kaydi, sonuc["donemler"])
    _etki_sayfasi(wb, sonuc)
    _yil_uyum_sayfasi(wb, sonuc)
    _tarhiyat_sayfasi(wb, inceleme, sonuc)
    _ozet_sayfasi(wb, inceleme, sonuc, bulgular or [])
    os.makedirs(os.path.dirname(dosya_yolu), exist_ok=True)
    wb.save(dosya_yolu)
    return dosya_yolu
