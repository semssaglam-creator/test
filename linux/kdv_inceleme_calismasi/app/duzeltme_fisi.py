"""Vergi dairesinin duzeltme fisi formunu Excel olarak uretir.

Inceleme sonucunda sonraki vergilendirme donemlerinin KDV beyanlari "fazla ve
yersiz devredilen KDV" yonunden re'sen duzeltildiginde, vergi dairesi bir
duzeltme fisi duzenler (VUK 116 ve muteakip maddeler). Fis iki dokumu yan yana
koyar:

  ustte  - mukellefce suresinde BEYAN EDILEN KDV dokumu
  altta  - mukellef adina OLMASI GEREKEN KDV dokumu

Olmasi gereken tablonun sonuna iki satir eklenir:

  Tarhi gereken vergi              - tarhiyat ozetindeki "Re'sen Tarhi Gereken
                                     KDV" sutununun aynisi
  Sonraki don. dev. KDV uyumsuzluk - fazla ve yersiz devredilen KDV; beyandaki
                                     yil sonu devri ile olmasi gereken devir
                                     arasindaki fark

Her yil ayri bir sayfaya yazilir: fis donem donem degil, vergilendirme
donemleri itibariyla duzenlenir ve imza blogu her sayfanin altinda yer alir.

Kunye alanlari (duzenlenme nedeni, cilt/sira no, fis tarihi, gerekce metni ve
uc imza) calismayla birlikte saklanir; buraya hazir gelir.
"""
from openpyxl import Workbook

from .excel_export import (BORDER, DOLGU_BASLIK, DOLGU_TOPLAM, FONT, FONT_BASLIK,
                           FONT_BOLD, FONT_FARK, FONT_NOT, ORTA, SAG, SAYI_BICIMI,
                           SOL, _yaz)

# Dokum sutunlari: (donem kaydindaki alan, baslik)
# Beyanname duzeninin okunma sirasini izler; fisi elle kontrol eden kisi
# beyanname ile satir satir karsilastirabilsin diye.
SUTUNLAR = (
    ("matrah", "Matrah"),
    ("hesaplanan", "Hesaplanan KDV"),
    ("ilave_edilecek", "İlave Edilecek KDV"),
    ("toplam_kdv", "Toplam KDV"),
    ("onceki_devir", "Önceki Dönemden Devreden"),
    ("indirimler", "İndirimler Toplamı"),
    ("odenecek", "Ödenecek KDV"),
    ("sonraki_devir", "Sonraki Döneme Devreden"),
)

GENISLIK = 1 + len(SUTUNLAR)


def _sayfa_kur(ws):
    ws.column_dimensions["A"].width = 16
    for i in range(len(SUTUNLAR)):
        ws.column_dimensions[chr(ord("B") + i)].width = 16
    ws.sheet_view.showGridLines = False


def _kunye_satiri(ws, satir, etiket, deger, genislik=GENISLIK):
    _yaz(ws, satir, 1, etiket, FONT_BOLD, SOL, bicim=None)
    h = ws.cell(satir, 2, deger or "")
    h.font = FONT
    h.alignment = SOL
    ws.merge_cells(start_row=satir, start_column=2, end_row=satir,
                   end_column=genislik)
    return satir + 1


def _tablo(ws, satir, baslik, donemler, alan_adi, dolgu=None):
    """Bir dokum tablosu yazar; son satir yil toplamidir.

    `alan_adi` donem kaydindaki hangi senaryonun yazilacagini soyler:
    "beyan" (mukellefce beyan edilen) ya da "elestirili" (olmasi gereken).
    """
    _yaz(ws, satir, 1, baslik, FONT_BASLIK, SOL, bicim=None)
    ws.merge_cells(start_row=satir, start_column=1, end_row=satir,
                   end_column=GENISLIK)
    satir += 1

    _yaz(ws, satir, 1, "Dönem", FONT_BOLD, ORTA, DOLGU_BASLIK, bicim=None)
    for i, (_kod, etiket) in enumerate(SUTUNLAR):
        _yaz(ws, satir, 2 + i, etiket, FONT_BOLD, ORTA, DOLGU_BASLIK, bicim=None)
    satir += 1

    toplamlar = [0.0] * len(SUTUNLAR)
    for d in donemler:
        kaynak = d[alan_adi]
        _yaz(ws, satir, 1, d["ay_adi"], FONT, SOL, dolgu, bicim=None)
        for i, (kod, _etiket) in enumerate(SUTUNLAR):
            deger = float(kaynak.get(kod) or 0.0)
            toplamlar[i] += deger
            _yaz(ws, satir, 2 + i, deger, FONT, SAG, dolgu)
        satir += 1

    _yaz(ws, satir, 1, "Toplam", FONT_BOLD, SOL, DOLGU_TOPLAM, bicim=None)
    for i, toplam in enumerate(toplamlar):
        _yaz(ws, satir, 2 + i, round(toplam, 2), FONT_BOLD, SAG, DOLGU_TOPLAM)
    return satir + 1


def _ek_satir(ws, satir, etiket, deger, vurgu=False):
    """Olmasi gereken tablonun altina eklenen tek tutarli satir."""
    font = FONT_FARK if vurgu else FONT_BOLD
    _yaz(ws, satir, 1, etiket, font, SOL, DOLGU_TOPLAM, bicim=None)
    ws.merge_cells(start_row=satir, start_column=1, end_row=satir,
                   end_column=GENISLIK - 1)
    _yaz(ws, satir, GENISLIK, round(float(deger or 0.0), 2), font, SAG,
         DOLGU_TOPLAM)
    return satir + 1


def _imzalari_coz(fis):
    """Kunye alanlarindan imza listesi cikarir.

    Arayuz alanlari duz tutuluyor (ad1/unvan1, ad2/unvan2, ad3/unvan3); form
    alani ile kayit alani birebir ortusunce kaydetme ve geri yukleme
    basitlesiyor. Bicimi listeye cevirmek burasinin isi. Ad da unvan da bos
    olan imza yazilmaz - fiste bos bir imza yeri durmaz.
    """
    if fis.get("imzalar"):
        return fis["imzalar"]
    imzalar = []
    for sira in (1, 2, 3):
        ad = (fis.get("ad%d" % sira) or "").strip()
        unvan = (fis.get("unvan%d" % sira) or "").strip()
        if ad or unvan:
            imzalar.append({"ad": ad, "unvan": unvan})
    return imzalar


def _imza_blogu(ws, satir, imzalar):
    """Uc imza yan yana: ad soyad ustte, unvan altta.

    Fiste unvanin ustunde ad yer alir; imzayi atan kisinin adi once okunur.
    """
    satir += 1
    genislik = max(GENISLIK // 3, 2)
    for sira, imza in enumerate(imzalar[:3]):
        sutun = 1 + sira * genislik
        h = ws.cell(satir, sutun, (imza.get("ad") or "").strip())
        h.font = FONT_BOLD
        h.alignment = ORTA
        h2 = ws.cell(satir + 1, sutun, (imza.get("unvan") or "").strip())
        h2.font = FONT
        h2.alignment = ORTA
        for r in (satir, satir + 1):
            ws.merge_cells(start_row=r, start_column=sutun, end_row=r,
                           end_column=min(sutun + genislik - 1, GENISLIK))
    return satir + 2


def _yil_sayfasi(wb, yil, donemler, inceleme, fis):
    ws = wb.create_sheet(str(yil))
    _sayfa_kur(ws)
    satir = 1

    _yaz(ws, satir, 1, "DÜZELTME FİŞİ", FONT_BASLIK, ORTA, bicim=None)
    ws.merge_cells(start_row=satir, start_column=1, end_row=satir,
                   end_column=GENISLIK)
    satir += 2

    satir = _kunye_satiri(ws, satir, "Vergi Dairesi", inceleme.get("vergi_dairesi"))
    satir = _kunye_satiri(ws, satir, "Mükellef", inceleme.get("ad_unvan"))
    satir = _kunye_satiri(ws, satir, "VKN / TCKN", inceleme.get("vkn_tckn"))
    satir = _kunye_satiri(ws, satir, "Vergilendirme Dönemi", str(yil))
    satir = _kunye_satiri(ws, satir, "Cilt / Sıra No", fis.get("cilt_sira"))
    satir = _kunye_satiri(ws, satir, "Fiş Tarihi", fis.get("tarih"))
    satir = _kunye_satiri(ws, satir, "Düzenlenme Nedeni", fis.get("neden"))
    satir += 1

    satir = _tablo(ws, satir, "MÜKELLEFÇE SÜRESİNDE BEYAN EDİLEN", donemler,
                   "beyan")
    satir += 1
    satir = _tablo(ws, satir, "MÜKELLEF ADINA OLMASI GEREKEN", donemler,
                   "elestirili")

    # Tarhi gereken vergi: tarhiyat ozetindeki sutunun yil toplami.
    tarhi_gereken = sum(float((d.get("tarhiyat") or {}).get("resen_tarhi_gereken")
                              or 0.0) for d in donemler)
    satir = _ek_satir(ws, satir, "Tarhı Gereken Vergi", tarhi_gereken,
                      vurgu=abs(tarhi_gereken) > 0.005)

    # Fazla ve yersiz devredilen KDV: yilin SON doneminde beyandaki devir ile
    # olmasi gereken devir arasindaki fark. Toplam alinmaz - devir bir stok
    # kalemidir, aylik farklarin toplami bir yil devri anlamina gelmez.
    son = donemler[-1]
    uyumsuzluk = (float(son["beyan"].get("sonraki_devir") or 0.0)
                  - float(son["elestirili"].get("sonraki_devir") or 0.0))
    satir = _ek_satir(ws, satir, "Sonraki Dön. Dev. KDV Uyumsuzluk Tutarı",
                      round(uyumsuzluk, 2), vurgu=abs(uyumsuzluk) > 0.005)
    satir += 1

    gerekce = (fis.get("gerekce") or "").strip()
    if gerekce:
        h = ws.cell(satir, 1, gerekce)
        h.font = FONT
        h.alignment = SOL
        ws.merge_cells(start_row=satir, start_column=1, end_row=satir + 2,
                       end_column=GENISLIK)
        satir += 3

    _imza_blogu(ws, satir, _imzalari_coz(fis))
    return ws


def uret(yol, sonuc, inceleme, fis):
    """Duzeltme fisini `yol` dosyasina yazar. Her yil ayri sayfa.

    sonuc   : hesap.hesapla ciktisi ("donemler" listesi)
    inceleme: mukellef kunyesi
    fis     : {neden, cilt_sira, tarih, gerekce, imzalar:[{ad,unvan}, ...]}
    """
    donemler = sonuc.get("donemler") or []
    if not donemler:
        raise ValueError("Fiş için dönem verisi yok.")

    yillar = []
    for d in donemler:
        if not yillar or yillar[-1][0] != d["yil"]:
            yillar.append((d["yil"], []))
        yillar[-1][1].append(d)

    wb = Workbook()
    wb.remove(wb.active)
    for yil, yil_donemleri in yillar:
        _yil_sayfasi(wb, yil, yil_donemleri, inceleme, fis or {})
    wb.save(yol)
    return yol
