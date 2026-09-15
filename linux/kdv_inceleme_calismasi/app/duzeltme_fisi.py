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
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.properties import PageSetupProperties

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

# Sutun genisligi sinirlari (Excel "karakter" birimi). Alt sinir dar sayilarin
# baslik altinda kaybolmasini, ust sinir uzun bir metnin sayfayi yatay olarak
# tasirmasini onler.
EN_DAR = 10
EN_GENIS = 24
PAY = 2          # kenar boslugu; icerik hucre cizgisine yapismasin

# Kunye (mukellef bilgileri) alani. Etiket sutunu UC sutuna yayilir: iki sutunda
# "Vergilendirme Dönemi" ve "Düzenlenme Nedeni" satira sigmiyor, alt satira
# kayiyordu. Birlestirilmis hucrede Excel satir yuksekligini kendiliginden
# buyutmez; kayan ikinci satir gorunmez oluyordu.
KUNYE_ETIKET_SON = 3
SATIR_YUKSEKLIGI = 15.0   # Excel varsayilani; sarma oldukca kati ile carpilir
KALIN_PAYI = 1.15         # kalin yazi normalden genis; olcuye pay birakilir


def _sutun_no(kod):
    """Dokum sutununun sayfadaki numarasi (A = donem, B'den itibaren tutarlar)."""
    for i, (alan, _etiket) in enumerate(SUTUNLAR):
        if alan == kod:
            return 2 + i
    return GENISLIK


def _sayfa_kur(ws):
    """Sayfa duzeni: A4 YATAY ve genislik olarak TEK sayfaya sigar.

    Fis dokumu dokuz sutun; dikey A4'e sigmaz, bolunup okunmaz hale gelirdi.
    fitToWidth=1 / fitToHeight=0 ile sutunlar tek sayfaya sikistirilir, satir
    sayisi arttikca alta sayfa eklenir.
    """
    ws.sheet_view.showGridLines = False
    ws.page_setup.orientation = "landscape"
    ws.page_setup.paperSize = ws.PAPERSIZE_A4
    ws.sheet_properties.pageSetUpPr = PageSetupProperties(fitToPage=True)
    ws.page_setup.fitToWidth = 1
    ws.page_setup.fitToHeight = 0
    ws.page_margins.left = ws.page_margins.right = 0.4
    ws.page_margins.top = ws.page_margins.bottom = 0.5


def _olcum_kur(ws):
    """Sutun genisliklerini olcmek icin sayaci hazirlar."""
    ws._fis_olcum = {}
    return ws._fis_olcum


def _olc(ws, sutun, deger):
    """Hucre iceriginin goruntulenecek uzunlugunu sutun olcusune isler.

    Birlesik hucreler cagrilmaz: onlarin metni birden cok sutuna yayilir,
    olcuye katilirsa sutunlar gereksiz genisler.
    """
    if deger is None or deger == "":
        return
    if isinstance(deger, (int, float)):
        metin = "{:,.2f}".format(float(deger))
    else:
        metin = str(deger)
    olcum = getattr(ws, "_fis_olcum", None)
    if olcum is None:
        olcum = _olcum_kur(ws)
    uzunluk = max(len(parca) for parca in metin.split("\n"))
    if uzunluk > olcum.get(sutun, 0):
        olcum[sutun] = uzunluk


def _genislikleri_uygula(ws):
    """Olculen en uzun iceriklere gore sutun genisliklerini yazar."""
    olcum = getattr(ws, "_fis_olcum", {}) or {}
    for sutun in range(1, GENISLIK + 1):
        uzunluk = olcum.get(sutun, EN_DAR)
        genislik = min(max(uzunluk + PAY, EN_DAR), EN_GENIS)
        ws.column_dimensions[get_column_letter(sutun)].width = genislik


def _alani_cercevele(ws, satir, bas, son, dolgu=None):
    """Birlestirilmis bir alanin her hucresine kenarlik (ve dolgu) yazar.

    openpyxl birlestirmede kapsanan hucreleri yeniden olusturur; bicim
    birlestirmeden ONCE yazilirsa kaybolur. Bu yuzden cerceve sonradan
    cekilir, yoksa alan yalnizca sol ust hucrede cizgili gorunur.
    """
    for sutun in range(bas, son + 1):
        hucre = ws.cell(satir, sutun)
        hucre.border = BORDER
        if dolgu:
            hucre.fill = dolgu


def _kunye_satiri(ws, satir, etiket, deger, genislik=GENISLIK):
    """Kunye satiri: etiket ilk UC sutuna, deger kalanina yayilir.

    Etiket birlestirilmezse ("Vergilendirme Dönemi" gibi uzun olanlar) A
    sutununu genisletmek gerekirdi; oysa A sutunu asagidaki dokum tablosunun
    "Dönem" sutunu ve dar kalmali. Bu yuzden etiket birlestirilir; alan uc
    sutun olunca en uzun etiket bile tek satira sigar.
    """
    etiket_son = min(KUNYE_ETIKET_SON, genislik - 1)
    _yaz(ws, satir, 1, etiket, FONT_BOLD, SOL, DOLGU_BASLIK, bicim=None)
    _yaz(ws, satir, etiket_son + 1, deger or "", FONT, SOL, bicim=None)
    ws.merge_cells(start_row=satir, start_column=1, end_row=satir,
                   end_column=etiket_son)
    ws.merge_cells(start_row=satir, start_column=etiket_son + 1, end_row=satir,
                   end_column=genislik)
    # Kenarlik ve dolgu BIRLESTIRMEDEN SONRA yazilir. merge_cells kapsanan
    # hucreleri yeniden olusturuyor; once yazilan bicim siliniyor ve kunyenin
    # sag ucu cercevesiz kaliyordu. Sirasi boyle olmali.
    _alani_cercevele(ws, satir, 1, etiket_son, DOLGU_BASLIK)
    _alani_cercevele(ws, satir, etiket_son + 1, genislik)
    _kunye_kaydet(ws, satir, etiket, deger, etiket_son, genislik)
    return satir + 1


def _kunye_kaydet(ws, satir, etiket, deger, etiket_son, genislik):
    """Kunye satirini yukseklik hesabi icin saklar (genislikler henuz belli degil)."""
    kayit = getattr(ws, "_fis_kunye", None)
    if kayit is None:
        kayit = ws._fis_kunye = []
    kayit.append((satir, etiket, deger, etiket_son, genislik))


def _yukseklikleri_uygula(ws):
    """Kunye satirlarinin yuksekligini sarma sonrasi satir sayisina gore ayarlar.

    Birlestirilmis hucrede Excel, metin sarinca satir yuksekligini kendiliginden
    buyutmez; tasan kisim gorunmez olur. Genislikler yazildiktan SONRA cagrilir,
    cunku kac satira sardigi genislige bagli.
    """
    for satir, etiket, deger, etiket_son, genislik in getattr(ws, "_fis_kunye", []):
        satir_sayisi = max(
            _sarma_satiri(ws, etiket, 1, etiket_son, KALIN_PAYI),
            _sarma_satiri(ws, deger, etiket_son + 1, genislik, 1.0),
        )
        if satir_sayisi > 1:
            ws.row_dimensions[satir].height = SATIR_YUKSEKLIGI * satir_sayisi


def _sarma_satiri(ws, metin, bas, son, kat):
    """Metnin bas..son sutunlarina yayilmis halde kac satira sardigini verir."""
    metin = "" if metin is None else str(metin)
    if not metin:
        return 1
    alan = sum(ws.column_dimensions[get_column_letter(s)].width or EN_DAR
               for s in range(bas, son + 1))
    if alan <= 0:
        return 1
    gereken = len(metin) * kat
    return max(1, int(gereken / alan) + (1 if gereken % alan else 0))


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
    _olc(ws, 1, "Dönem")
    for i, (_kod, etiket) in enumerate(SUTUNLAR):
        _yaz(ws, satir, 2 + i, etiket, FONT_BOLD, ORTA, DOLGU_BASLIK, bicim=None)
        # Baslik iki satira sarabilir; olcuye en uzun sozcugu girer, boylece
        # baslik yuzunden sutun gereksiz genislemez.
        _olc(ws, 2 + i, max(etiket.split(), key=len))
    satir += 1

    toplamlar = [0.0] * len(SUTUNLAR)
    for d in donemler:
        kaynak = d[alan_adi]
        _yaz(ws, satir, 1, d["ay_adi"], FONT, SOL, dolgu, bicim=None)
        _olc(ws, 1, d["ay_adi"])
        for i, (kod, _etiket) in enumerate(SUTUNLAR):
            deger = float(kaynak.get(kod) or 0.0)
            toplamlar[i] += deger
            _yaz(ws, satir, 2 + i, deger, FONT, SAG, dolgu)
            _olc(ws, 2 + i, deger)
        satir += 1

    _yaz(ws, satir, 1, "Toplam", FONT_BOLD, SOL, DOLGU_TOPLAM, bicim=None)
    _olc(ws, 1, "Toplam")
    for i, toplam in enumerate(toplamlar):
        _yaz(ws, satir, 2 + i, round(toplam, 2), FONT_BOLD, SAG, DOLGU_TOPLAM)
        _olc(ws, 2 + i, round(toplam, 2))
    return satir + 1


def _ek_satir(ws, satir, etiket, deger, sutun, vurgu=False):
    """Olmasi gereken tablonun altina eklenen tek tutarli satir.

    Tutar, ustteki tablonun HANGI sutununa ait ise oraya yazilir; boylece
    satir tablonun kolonlariyla hizali okunur. Etiket, tutarin sutununa kadar
    olan alana yayilir - tutar hucresi birlesime GIRMEZ, yoksa sayi gorunmez.
    """
    font = FONT_FARK if vurgu else FONT_BOLD
    _yaz(ws, satir, 1, etiket, font, SOL, DOLGU_TOPLAM, bicim=None)
    if sutun > 2:
        ws.merge_cells(start_row=satir, start_column=1, end_row=satir,
                       end_column=sutun - 1)
        # Birlestirme kapsanan hucreleri yeniden olusturuyor; cerceve sonradan
        # cekilmezse etiket kutusunun ust/alt cizgisi B'den itibaren kopuyor.
        _alani_cercevele(ws, satir, 1, sutun - 1, DOLGU_TOPLAM)
    tutar = round(float(deger or 0.0), 2)
    _yaz(ws, satir, sutun, tutar, font, SAG, DOLGU_TOPLAM)
    _olc(ws, sutun, tutar)
    # Tutarin sagindaki sutunlar bos kalmasin; tablo cercevesi surer.
    for bos in range(sutun + 1, GENISLIK + 1):
        _yaz(ws, satir, bos, None, font, SAG, DOLGU_TOPLAM, bicim=None)
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
    _olcum_kur(ws)
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
                      _sutun_no("odenecek"), vurgu=abs(tarhi_gereken) > 0.005)

    # Fazla ve yersiz devredilen KDV: yilin SON doneminde beyandaki devir ile
    # olmasi gereken devir arasindaki fark. Toplam alinmaz - devir bir stok
    # kalemidir, aylik farklarin toplami bir yil devri anlamina gelmez.
    son = donemler[-1]
    uyumsuzluk = (float(son["beyan"].get("sonraki_devir") or 0.0)
                  - float(son["elestirili"].get("sonraki_devir") or 0.0))
    satir = _ek_satir(ws, satir, "Sonraki Dön. Dev. KDV Uyumsuzluk Tutarı",
                      round(uyumsuzluk, 2), _sutun_no("sonraki_devir"),
                      vurgu=abs(uyumsuzluk) > 0.005)
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
    _genislikleri_uygula(ws)
    _yukseklikleri_uygula(ws)   # genislikler yazildiktan SONRA; sirasi onemli
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
