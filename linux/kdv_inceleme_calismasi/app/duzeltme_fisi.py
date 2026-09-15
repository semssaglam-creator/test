"""Vergi dairesinin duzeltme fisi formunu Excel olarak uretir.

Inceleme sonucunda sonraki vergilendirme donemlerinin KDV beyanlari "fazla ve
yersiz devredilen KDV" yonunden re'sen duzeltildiginde, vergi dairesi bir
duzeltme fisi duzenler (VUK 116 ve muteakip maddeler). Fis iki dokumu yan yana
koyar:

  ustte  - mukellefce suresinde BEYAN EDILEN KDV dokumu
  altta  - mukellef adina OLMASI GEREKEN KDV dokumu

Olmasi gereken tablonun son satiri, fazla ve yersiz devredilen KDV'yi gosteren
"devreden KDV uyumsuzluk tutari"dir: beyandaki yil sonu devri ile olmasi
gereken devir arasindaki fark. Satir vurgulu (dolgulu ve kalin), cunku fisin
duzenlenme nedeni odur.

Tarhi gereken vergi ayri bir tablodur; ucu yan yana okunsun diye:

  Beyan Edilen Odenecek KDV   - mukellefin beyan ettigi
  Olmasi Gereken Odenecek KDV - inceleme sonucuna gore olmasi gereken
  Tarhi Gereken KDV           - tarhiyat ozetindeki "Re'sen Tarhi Gereken KDV"
                                sutununun aynisi

Her yil ayri bir sayfaya yazilir: fis donem donem degil, vergilendirme
donemleri itibariyla duzenlenir ve imza blogu her sayfanin altinda yer alir.

Kunye alanlari (duzenlenme nedeni, cilt/sira no, fis tarihi, gerekce metni ve
uc imza) calismayla birlikte saklanir; buraya hazir gelir.
"""
from openpyxl import Workbook
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.properties import PageSetupProperties

from .excel_export import (BORDER, DOLGU_BASLIK, DOLGU_FARK, DOLGU_TOPLAM, FONT,
                           FONT_BASLIK, FONT_BOLD, FONT_FARK, FONT_NOT, ORTA,
                           SAG, SAYI_BICIMI, SOL, _yaz)

# Tarhi gereken vergi tablosunun sutunlari: (donem kaydindaki yol, baslik).
# Yol bir cifttir: once senaryo/bolum, sonra alan adi.
TARHIYAT_SUTUNLARI = (
    (("beyan", "odenecek"), "Beyan Edilen Ödenecek KDV"),
    (("elestirili", "odenecek"), "Olması Gereken Ödenecek KDV"),
    (("tarhiyat", "resen_tarhi_gereken"), "Tarhı Gereken KDV"),
)

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
VARSAYILAN_YUKSEKLIK = 15.0   # Excel varsayilani (10 punto yaziya bol gelir)
SARMA_YUKSEKLIGI = 13.5       # sarilan her satirin kapladigi yukseklik
KALIN_PAYI = 1.15             # kalin yazi normalden genis; olcuye pay birakilir


def _sutun_no(kod):
    """Dokum sutununun sayfadaki numarasi (A = donem, B'den itibaren tutarlar)."""
    for i, (alan, _etiket) in enumerate(SUTUNLAR):
        if alan == kod:
            return 2 + i
    return GENISLIK


def _sayfa_kur(ws):
    """Sayfa duzeni: A4 DIKEY ve genislik olarak TEK sayfaya sigar.

    fitToWidth=1 / fitToHeight=0 ile dokuz sutun tek sayfa enine sikistirilir,
    satir sayisi arttikca alta sayfa eklenir. Dikey A4'te sutunlar dar kaldigi
    icin basliklar sarar; sarilan satirlarin yuksekligi _yukseklikleri_uygula
    ile buyutulur, yoksa ikinci satir gorunmez olur.
    """
    ws.sheet_view.showGridLines = False
    ws.page_setup.orientation = "portrait"
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


def _olc(ws, sutun, deger, kat=1.0):
    """Hucre iceriginin goruntulenecek uzunlugunu sutun olcusune isler.

    `kat` kalin yazi payidir; kalin metin ayni karakter sayisinda daha genis
    yer kaplar. Payi vermezsek sutun tam bir sozcuk kadar dar kalir ve baslik
    sozcugun ortasindan bolunur - "Dönemden" iki satira dagilirdi.

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
    uzunluk = max(len(parca) for parca in metin.split("\n")) * kat
    if uzunluk > olcum.get(sutun, 0):
        olcum[sutun] = uzunluk


def _genislikleri_uygula(ws):
    """Olculen en uzun iceriklere gore sutun genisliklerini yazar."""
    olcum = getattr(ws, "_fis_olcum", {}) or {}
    for sutun in range(1, GENISLIK + 1):
        uzunluk = olcum.get(sutun, EN_DAR)
        genislik = round(min(max(uzunluk + PAY, EN_DAR), EN_GENIS), 1)
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
    return satir + 1


def _sutun_genisligi(ws, sutun):
    ayar = ws.column_dimensions.get(get_column_letter(sutun))
    return (ayar.width if ayar is not None and ayar.width else EN_DAR)


def _sarma_satiri(metin, alan, kat):
    """Metin `alan` karakter genisligine sarilinca kac satir tuttugunu verir.

    Excel sozcuk sinirindan kirar; sigmayan tek bir sozcuk ortadan bolunur.
    Hesap ayni sirayi izler, yoksa uzun basliklar oldugundan az satir sayilir.
    """
    metin = "" if metin is None else str(metin)
    if not metin or alan <= 0:
        return 1
    toplam = 0
    for paragraf in metin.split("\n"):
        sozcukler = paragraf.split()
        if not sozcukler:
            toplam += 1
            continue
        sayi, dolu = 1, 0.0
        for sozcuk in sozcukler:
            en = len(sozcuk) * kat
            if dolu == 0:
                dolu = en
            elif dolu + kat + en <= alan:
                dolu += kat + en
            else:
                sayi += 1
                dolu = en
            while dolu > alan:      # tek basina sigmayan sozcuk bolunur
                sayi += 1
                dolu -= alan
        toplam += sayi
    return max(1, toplam)


def _yukseklikleri_uygula(ws):
    """Saran her satirin yuksekligini kendimiz hesaplar.

    Excel satir yuksekligini dosya acilirken yeniden olcmez, openpyxl de
    yukseklik yazmaz; butun satirlar varsayilan 15 puntoda kalir ve sarilan
    metnin ikinci satiri gorunmez olurdu - dikey sayfada sutunlar dar kaldigi
    icin once basliklarda ("Önceki Dönemden Devreden" gibi) ortaya cikiyordu.
    Genislikler yazildiktan SONRA cagrilir; kac satira sardigi genislige bagli.
    """
    # Birlesik alanlar: metin sol ust hucrede durur, genislik butun aralik
    # kadardir. Aralikta kalan diger hucreler olcuye girmemeli.
    alanlar, kapali = {}, set()
    for aralik in ws.merged_cells.ranges:
        alanlar[(aralik.min_row, aralik.min_col)] = (
            sum(_sutun_genisligi(ws, s)
                for s in range(aralik.min_col, aralik.max_col + 1)),
            aralik.max_row - aralik.min_row + 1)
        for r in range(aralik.min_row, aralik.max_row + 1):
            for s in range(aralik.min_col, aralik.max_col + 1):
                if (r, s) != (aralik.min_row, aralik.min_col):
                    kapali.add((r, s))

    gereken = {}
    for satir in ws.iter_rows():
        for hucre in satir:
            if hucre.value in (None, "") or (hucre.row, hucre.column) in kapali:
                continue
            hiza = hucre.alignment
            if not (hiza and hiza.wrap_text):
                continue    # sarmayan hucre (sayilar) satiri uzatmaz
            alan, kac_satir = alanlar.get(
                (hucre.row, hucre.column),
                (_sutun_genisligi(ws, hucre.column), 1))
            kat = KALIN_PAYI if (hucre.font and hucre.font.bold) else 1.0
            sayi = _sarma_satiri(hucre.value, alan - PAY, kat)
            if sayi <= kac_satir:
                continue
            # Cok satira yayilan birlesimde yuk satirlara bolunur.
            pay = -(-sayi // kac_satir)
            for r in range(hucre.row, hucre.row + kac_satir):
                if pay > gereken.get(r, 1):
                    gereken[r] = pay

    for r, kac in gereken.items():
        ws.row_dimensions[r].height = max(VARSAYILAN_YUKSEKLIK,
                                          SARMA_YUKSEKLIGI * kac)


def _tablo(ws, satir, baslik, donemler, alan_adi, dolgu=None, vurgu_satiri=None):
    """Bir dokum tablosu yazar; son satir yil toplamidir.

    `alan_adi` donem kaydindaki hangi senaryonun yazilacagini soyler:
    "beyan" (mukellefce beyan edilen) ya da "elestirili" (olmasi gereken).

    `vurgu_satiri` verilirse toplamin altina (etiket, tutar, sutun_kodu)
    biciminde vurgulu bir satir eklenir; tablonun icinde yer alir, ayri bir
    blok degildir.
    """
    _yaz(ws, satir, 1, baslik, FONT_BASLIK, SOL, bicim=None)
    ws.merge_cells(start_row=satir, start_column=1, end_row=satir,
                   end_column=GENISLIK)
    satir += 1

    _yaz(ws, satir, 1, "Dönem", FONT_BOLD, ORTA, DOLGU_BASLIK, bicim=None)
    _olc(ws, 1, "Dönem", KALIN_PAYI)
    for i, (_kod, etiket) in enumerate(SUTUNLAR):
        _yaz(ws, satir, 2 + i, etiket, FONT_BOLD, ORTA, DOLGU_BASLIK, bicim=None)
        # Baslik birkac satira sarabilir; olcuye yalnizca EN UZUN SOZCUGU girer.
        # Boylece sutun baslik yuzunden gereksiz genislemez ama sarma sozcuk
        # sinirindan olur, sozcugun ortasindan degil.
        _olc(ws, 2 + i, max(etiket.split(), key=len), KALIN_PAYI)
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
    satir += 1

    if vurgu_satiri:
        etiket, tutar, kod = vurgu_satiri
        satir = _vurgulu_satir(ws, satir, etiket, tutar, _sutun_no(kod))
    return satir


def _vurgulu_satir(ws, satir, etiket, deger, sutun):
    """Tablonun sonuna eklenen, dolgulu ve kalin tek tutarli satir.

    Tutar, ustteki tablonun HANGI sutununa ait ise oraya yazilir; boylece
    satir tablonun kolonlariyla hizali okunur. Etiket, tutarin sutununa kadar
    olan alana yayilir - tutar hucresi birlesime GIRMEZ, yoksa sayi gorunmez.
    """
    tutar = round(float(deger or 0.0), 2)
    # Fark varsa kirmizi kalin, yoksa duz kalin; dolgu her iki durumda da var,
    # cunku satirin kendisi fisin gerekcesi ve goze carpmasi gerekiyor.
    font = FONT_FARK if abs(tutar) > 0.005 else FONT_BOLD
    _yaz(ws, satir, 1, etiket, font, SOL, DOLGU_FARK, bicim=None)
    if sutun > 2:
        ws.merge_cells(start_row=satir, start_column=1, end_row=satir,
                       end_column=sutun - 1)
        # Birlestirme kapsanan hucreleri yeniden olusturuyor; cerceve sonradan
        # cekilmezse etiket kutusunun ust/alt cizgisi B'den itibaren kopuyor.
        _alani_cercevele(ws, satir, 1, sutun - 1, DOLGU_FARK)
    _yaz(ws, satir, sutun, tutar, font, SAG, DOLGU_FARK)
    _olc(ws, sutun, tutar)
    # Tutarin sagindaki sutunlar bos kalmasin; tablo cercevesi surer.
    for bos in range(sutun + 1, GENISLIK + 1):
        _yaz(ws, satir, bos, None, font, SAG, DOLGU_FARK, bicim=None)
    return satir + 1


def _bloklar(kac):
    """2..GENISLIK sutunlarini `kac` esit bloga boler: [(bas, son), ...].

    Tarhiyat tablosunun uc tutar sutunu var, sayfa ise dokuz sutun genisliginde.
    Bloklara bolunmezse tablo A-D arasinda sikisip sayfanin geri kalanini bos
    birakiyor; birlestirilerek yayilinca ustteki tablolarla ayni eni tutuyor.
    """
    toplam = GENISLIK - 1
    taban, artan = divmod(toplam, kac)
    bloklar, bas = [], 2
    for i in range(kac):
        boy = taban + (1 if i < artan else 0)
        bloklar.append((bas, bas + boy - 1))
        bas += boy
    return bloklar


def _tarhiyat_tablosu(ws, satir, baslik, donemler):
    """Tarhi gereken vergiyi ayri tablo olarak yazar.

    Beyan edilen / olmasi gereken / tarhi gereken odenecek KDV yan yana durur.
    Tarhi gereken tutar iki sutunun farkindan TUREMEZ; tarhiyat ozetindeki
    degerin aynisi okunur, yoksa iki ekran farkli sayi gosterebilir.
    """
    bloklar = _bloklar(len(TARHIYAT_SUTUNLARI))

    _yaz(ws, satir, 1, baslik, FONT_BASLIK, SOL, bicim=None)
    ws.merge_cells(start_row=satir, start_column=1, end_row=satir,
                   end_column=GENISLIK)
    satir += 1

    _yaz(ws, satir, 1, "Dönem", FONT_BOLD, ORTA, DOLGU_BASLIK, bicim=None)
    _olc(ws, 1, "Dönem", KALIN_PAYI)
    for (bas, son), (_yol, etiket) in zip(bloklar, TARHIYAT_SUTUNLARI):
        _yaz(ws, satir, bas, etiket, FONT_BOLD, ORTA, DOLGU_BASLIK, bicim=None)
        _blogu_birlestir(ws, satir, bas, son, DOLGU_BASLIK)
    satir += 1

    toplamlar = [0.0] * len(TARHIYAT_SUTUNLARI)
    for d in donemler:
        _yaz(ws, satir, 1, d["ay_adi"], FONT, SOL, bicim=None)
        _olc(ws, 1, d["ay_adi"])
        for i, ((bas, son), (yol, _etiket)) in enumerate(zip(bloklar,
                                                             TARHIYAT_SUTUNLARI)):
            bolum, alan = yol
            deger = float((d.get(bolum) or {}).get(alan) or 0.0)
            toplamlar[i] += deger
            _yaz(ws, satir, bas, deger, FONT, SAG)
            _blogu_birlestir(ws, satir, bas, son)
        satir += 1

    _yaz(ws, satir, 1, "Toplam", FONT_BOLD, SOL, DOLGU_TOPLAM, bicim=None)
    _olc(ws, 1, "Toplam")
    for (bas, son), toplam in zip(bloklar, toplamlar):
        _yaz(ws, satir, bas, round(toplam, 2), FONT_BOLD, SAG, DOLGU_TOPLAM)
        _blogu_birlestir(ws, satir, bas, son, DOLGU_TOPLAM)
    return satir + 1


def _blogu_birlestir(ws, satir, bas, son, dolgu=None):
    """Bir tutar/baslik blogunu birlestirir ve cercevesini sonradan ceker."""
    if son > bas:
        ws.merge_cells(start_row=satir, start_column=bas, end_row=satir,
                       end_column=son)
    _alani_cercevele(ws, satir, bas, son, dolgu)


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

    # Fazla ve yersiz devredilen KDV: yilin SON doneminde beyandaki devir ile
    # olmasi gereken devir arasindaki fark. Toplam alinmaz - devir bir stok
    # kalemidir, aylik farklarin toplami bir yil devri anlamina gelmez.
    son = donemler[-1]
    uyumsuzluk = round(float(son["beyan"].get("sonraki_devir") or 0.0)
                       - float(son["elestirili"].get("sonraki_devir") or 0.0), 2)
    satir = _tablo(ws, satir, "MÜKELLEF ADINA OLMASI GEREKEN", donemler,
                   "elestirili",
                   vurgu_satiri=("Devreden KDV Uyumsuzluk Tutarı", uyumsuzluk,
                                 "sonraki_devir"))
    satir += 1

    satir = _tarhiyat_tablosu(ws, satir, "TARHI GEREKEN VERGİ", donemler)
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
