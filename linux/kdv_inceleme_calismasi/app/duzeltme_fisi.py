"""Vergi dairesinin duzeltme fisi formunu Excel olarak uretir.

Inceleme sonucunda sonraki vergilendirme donemlerinin KDV beyanlari "fazla ve
yersiz devredilen KDV" yonunden re'sen duzeltildiginde, vergi dairesi bir
duzeltme fisi duzenler (VUK 116 ve muteakip maddeler). Fis uc bolumden olusur:

  1. mukellefce suresinde BEYAN EDILEN KDV dokumu (donemler satirlarda)
  2. mukellef adina OLMASI GEREKEN KDV dokumu (donemler satirlarda)
  3. TARHI GEREKEN VERGI (donemler SUTUNLARDA)

Ikinci tablonun son satiri, fazla ve yersiz devredilen KDV'yi gosteren
"devreden KDV uyumsuzluk tutari"dir: beyandaki yil sonu devri ile olmasi
gereken devir arasindaki fark. Satir vurgulu (dolgulu ve kalin), cunku fisin
duzenlenme nedeni odur.

Ucuncu tablo DEVRIKTIR: donemler sutunlara, kalemler satirlara gelir.

  Beyan Edilen Odenecek KDV   - mukellefin beyan ettigi
  Olmasi Gereken Odenecek KDV - inceleme sonucuna gore olmasi gereken
  Tarhi Gereken KDV           - tarhiyat ozetindeki "Re'sen Tarhi Gereken KDV"
                                sutununun aynisi

Devrik olmasinin nedeni sayfa: donem donem alt alta yazilinca fis bir A4'e
sigmiyordu. Devrik bicimde on iki donem uc satirda bitiyor. Bedeli genislik -
sayfa artik dokuz degil, donem sayisina gore genisliyor (bkz. _genislik).

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

# Devrik tarhiyat tablosunun SATIRLARI: (donem kaydindaki yol, etiket).
# Yol bir cifttir: once senaryo/bolum, sonra alan adi.
TARHIYAT_SATIRLARI = (
    (("beyan", "odenecek"), "Beyan Edilen Ödenecek KDV"),
    (("elestirili", "odenecek"), "Olması Gereken Ödenecek KDV"),
    (("tarhiyat", "resen_tarhi_gereken"), "Tarhı Gereken KDV"),
)

# Devrik tablonun etiket sutunu kac sutuna yayilir. Etiketler uzun ("Olması
# Gereken Ödenecek KDV"); tek sutuna sigdirmak icin A'yi genisletmek gerekirdi,
# oysa A ustteki tablolarin dar "Dönem" sutunu.
ETIKET_BLOK = 2

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

# A4 olculeri (inc) ve bir Excel "karakter" biriminin inc karsiligi. Yon secimi
# icerigin en/boy oranini sayfa oraniyla karsilastirir; bkz. _yonu_sec.
A4_EN, A4_BOY = 8.27, 11.69
KARAKTER_INC = 0.0729


def _genislik(donemler):
    """Sayfanin kac sutun genisliginde olacagini verir.

    Iki gereksinimin buyugu: dokum tablolari 1 + 8 sutun ister, devrik
    tarhiyat tablosu ise etiket blogu + her donem icin bir sutun + Toplam.
    On iki donemde 15 sutun olur; uc donemde dokuz yeter.
    """
    return max(1 + len(SUTUNLAR), ETIKET_BLOK + len(donemler) + 1)


def _gen(ws):
    """Sayfanin sutun genisligi (sayfa kurulurken saklanir)."""
    return getattr(ws, "_fis_genislik", 1 + len(SUTUNLAR))


def _bloklar(bas, son, kac):
    """bas..son sutunlarini `kac` esit bloga boler: [(bas, son), ...].

    Mantiksal sutun sayisi fiziksel sutun sayisindan az oldugunda tablo
    sayfanin solunda sikisip kalanini bos birakiyor; bloklara bolunup
    birlestirilince butun tablolar ayni eni tutuyor.
    """
    toplam = son - bas + 1
    taban, artan = divmod(toplam, kac)
    bloklar = []
    for i in range(kac):
        boy = taban + (1 if i < artan else 0)
        bloklar.append((bas, bas + boy - 1))
        bas += boy
    return bloklar


def _sayfa_kur(ws, donemler):
    """Sayfa duzeni: A4 DIKEY ve TEK sayfaya sigar.

    fitToWidth=1 ve fitToHeight=1: Excel hem eni hem boyu bir sayfaya
    sigacak olcegi kendisi secer. fitToHeight=0 birakilirsa yalnizca en
    sigar, uzun fis alta tasar - "tek sayfaya sigmadi" sikayeti buydu.
    Dikey A4'te sutunlar dar kaldigi icin basliklar sarar; sarilan satirlarin
    yuksekligi _yukseklikleri_uygula ile buyutulur.
    """
    ws._fis_genislik = _genislik(donemler)
    ws.sheet_view.showGridLines = False
    ws.page_setup.orientation = "portrait"
    ws.page_setup.paperSize = ws.PAPERSIZE_A4
    ws.sheet_properties.pageSetUpPr = PageSetupProperties(fitToPage=True)
    ws.page_setup.fitToWidth = 1
    ws.page_setup.fitToHeight = 1
    ws.page_margins.left = ws.page_margins.right = 0.4
    ws.page_margins.top = ws.page_margins.bottom = 0.5


def _olcum_kur(ws):
    """Sutun genisliklerini olcmek icin sayaci hazirlar."""
    ws._fis_olcum = {}
    return ws._fis_olcum


def _olc(ws, sutun, deger, kat=1.0, blok=1):
    """Hucre iceriginin goruntulenecek uzunlugunu sutun olcusune isler.

    `kat` kalin yazi payidir; kalin metin ayni karakter sayisinda daha genis
    yer kaplar. Payi vermezsek sutun tam bir sozcuk kadar dar kalir ve baslik
    sozcugun ortasindan bolunur - "Dönemden" iki satira dagilirdi.

    `blok` birlesik alanin kac sutuna yayildigidir; olcu o sutunlara bolunur,
    yoksa birlesik bir hucrenin metni tek sutunu gereksiz genisletir.
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
    uzunluk = max(len(parca) for parca in metin.split("\n")) * kat / blok
    if uzunluk > olcum.get(sutun, 0):
        olcum[sutun] = uzunluk


def _blok_olc(ws, bas, son, deger, kat=1.0):
    """Bir blogun gereken genisligini blogun sutunlarina esit paylastirir."""
    boy = son - bas + 1
    for sutun in range(bas, son + 1):
        _olc(ws, sutun, deger, kat, boy)


def _genislikleri_uygula(ws):
    """Olculen en uzun iceriklere gore sutun genisliklerini yazar."""
    olcum = getattr(ws, "_fis_olcum", {}) or {}
    for sutun in range(1, _gen(ws) + 1):
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


def _blogu_birlestir(ws, satir, bas, son, dolgu=None):
    """Bir blogu birlestirir ve cercevesini (dolgusunu) sonradan ceker."""
    if son > bas:
        ws.merge_cells(start_row=satir, start_column=bas, end_row=satir,
                       end_column=son)
    _alani_cercevele(ws, satir, bas, son, dolgu)


def _kunye_satiri(ws, satir, etiket, deger):
    """Kunye satiri: etiket ilk UC sutuna, deger kalanina yayilir.

    Etiket birlestirilmezse ("Vergilendirme Dönemi" gibi uzun olanlar) A
    sutununu genisletmek gerekirdi; oysa A sutunu tablolarin dar etiket
    sutunu. Alan uc sutun olunca en uzun etiket bile tek satira sigar.
    """
    genislik = _gen(ws)
    etiket_son = min(KUNYE_ETIKET_SON, genislik - 1)
    _yaz(ws, satir, 1, etiket, FONT_BOLD, SOL, DOLGU_BASLIK, bicim=None)
    _yaz(ws, satir, etiket_son + 1, deger or "", FONT, SOL, bicim=None)
    # Kenarlik ve dolgu BIRLESTIRMEDEN SONRA yazilir (bkz. _alani_cercevele).
    _blogu_birlestir(ws, satir, 1, etiket_son, DOLGU_BASLIK)
    _blogu_birlestir(ws, satir, etiket_son + 1, genislik)
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
    metnin ikinci satiri gorunmez olurdu. Genislikler yazildiktan SONRA
    cagrilir; kac satira sardigi genislige bagli.
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


def _deger(donem, yol):
    """Donem kaydindan (bolum, alan) yolundaki tutari okur."""
    bolum, alan = yol
    return float((donem.get(bolum) or {}).get(alan) or 0.0)


def _donem_bloklari(ws, donem_sayisi):
    """Etiket blogundan sonraki sutunlari donemler + Toplam olarak boler.

    Son blok Toplam sutunudur. Butun tablolar ayni bolumlemeyi kullanir;
    boylece uc tablonun sutunlari birbiriyle hizali okunur - devrik tabloyu
    tek basina degistirdigimizde sutunlar ustteki tablolara uymuyordu.
    """
    bloklar = _bloklar(ETIKET_BLOK + 1, _gen(ws), donem_sayisi + 1)
    return bloklar[:-1], bloklar[-1]


def _tablo(ws, satir, baslik, donemler, satirlar, vurgu_satiri=None):
    """Devrik dokum tablosu yazar: DONEMLER SUTUNLARDA, kalemler satirlarda.

    `satirlar` ((bolum, alan), etiket) ciftlerinden olusur. Son sutun yil
    toplamidir.

    Devrik olmasinin nedeni sayfa: on iki donem alt alta yazilinca fis bir
    A4'e sigmiyordu; devrik bicimde sekiz kalem sekiz satirda bitiyor.

    `vurgu_satiri` verilirse tablonun sonuna (etiket, aylik_tutarlar,
    yil_tutari) biciminde dolgulu ve kalin bir satir eklenir.
    """
    genislik = _gen(ws)
    donem_bloklari, toplam_blok = _donem_bloklari(ws, len(donemler))

    _yaz(ws, satir, 1, baslik, FONT_BASLIK, SOL, bicim=None)
    ws.merge_cells(start_row=satir, start_column=1, end_row=satir,
                   end_column=genislik)
    satir += 1

    # Baslik satiri: sol ust kose bos, sonra donem adlari, en sagda Toplam.
    _blogu_birlestir(ws, satir, 1, ETIKET_BLOK, DOLGU_BASLIK)
    for (bas, son), d in zip(donem_bloklari, donemler):
        _yaz(ws, satir, bas, d["ay_adi"], FONT_BOLD, ORTA, DOLGU_BASLIK,
             bicim=None)
        _blogu_birlestir(ws, satir, bas, son, DOLGU_BASLIK)
        _blok_olc(ws, bas, son, d["ay_adi"], KALIN_PAYI)
    _yaz(ws, satir, toplam_blok[0], "Toplam", FONT_BOLD, ORTA, DOLGU_BASLIK,
         bicim=None)
    _blogu_birlestir(ws, satir, toplam_blok[0], toplam_blok[1], DOLGU_BASLIK)
    _blok_olc(ws, toplam_blok[0], toplam_blok[1], "Toplam", KALIN_PAYI)
    satir += 1

    for yol, etiket in satirlar:
        _yaz(ws, satir, 1, etiket, FONT_BOLD, SOL, DOLGU_BASLIK, bicim=None)
        _blogu_birlestir(ws, satir, 1, ETIKET_BLOK, DOLGU_BASLIK)
        # Etiket olcuye TAMAMIYLA girer. Devrik tabloda etiket blogu tek metin
        # sutunu; tam sigmazsa sarar, satir yukselir ve sayfa boyuna uzayarak
        # olcegi dusurur. Bir kac karakter en, on iki punto boydan iyidir.
        _blok_olc(ws, 1, ETIKET_BLOK, etiket, KALIN_PAYI)
        toplam = 0.0
        for (bas, son), d in zip(donem_bloklari, donemler):
            tutar = _deger(d, yol)
            toplam += tutar
            _yaz(ws, satir, bas, tutar, FONT, SAG)
            _blogu_birlestir(ws, satir, bas, son)
            _blok_olc(ws, bas, son, tutar)
        toplam = round(toplam, 2)
        _yaz(ws, satir, toplam_blok[0], toplam, FONT_BOLD, SAG, DOLGU_TOPLAM)
        _blogu_birlestir(ws, satir, toplam_blok[0], toplam_blok[1], DOLGU_TOPLAM)
        _blok_olc(ws, toplam_blok[0], toplam_blok[1], toplam, KALIN_PAYI)
        satir += 1

    if vurgu_satiri:
        satir = _vurgulu_satir(ws, satir, vurgu_satiri, donem_bloklari,
                               toplam_blok)
    return satir


def _vurgulu_satir(ws, satir, vurgu_satiri, donem_bloklari, toplam_blok):
    """Tablonun sonuna eklenen, dolgulu ve kalin uyumsuzluk satiri.

    Tutar aylara bolunur: uyumsuzlugun hangi donemde dogdugu gorunsun diye.
    Uyumsuz olmayan ay bos birakilir (sifir yazilmaz) - dolgu ve cerceve yine
    cekilir, boylece satirin cizgisi kesintisiz surer.

    Toplam sutunundaki tutar aylik degerlerin TOPLAMI DEGILDIR: devir bir stok
    kalemi, aylik farklarin toplami bir yil devri anlamina gelmez. Orada yil
    sonu devrindeki fark durur.
    """
    etiket, aylik, yil_tutari = vurgu_satiri
    yil_tutari = round(float(yil_tutari or 0.0), 2)
    # Fark varsa kirmizi kalin, yoksa duz kalin; dolgu her iki durumda da var,
    # cunku satirin kendisi fisin gerekcesi ve goze carpmasi gerekiyor.
    font = FONT_FARK if abs(yil_tutari) > 0.005 else FONT_BOLD
    _yaz(ws, satir, 1, etiket, font, SOL, DOLGU_FARK, bicim=None)
    _blogu_birlestir(ws, satir, 1, ETIKET_BLOK, DOLGU_FARK)
    _blok_olc(ws, 1, ETIKET_BLOK, etiket, KALIN_PAYI)
    for (bas, son), tutar in zip(donem_bloklari, aylik):
        tutar = round(float(tutar or 0.0), 2)
        if abs(tutar) > 0.005:
            _yaz(ws, satir, bas, tutar, font, SAG, DOLGU_FARK)
            _blok_olc(ws, bas, son, tutar)
        _blogu_birlestir(ws, satir, bas, son, DOLGU_FARK)
    _yaz(ws, satir, toplam_blok[0], yil_tutari, font, SAG, DOLGU_FARK)
    _blogu_birlestir(ws, satir, toplam_blok[0], toplam_blok[1], DOLGU_FARK)
    _blok_olc(ws, toplam_blok[0], toplam_blok[1], yil_tutari, KALIN_PAYI)
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
    if not imzalar:
        return satir
    for (bas, son), imza in zip(_bloklar(1, _gen(ws), len(imzalar[:3])),
                                imzalar[:3]):
        for r, (metin, font) in enumerate((((imza.get("ad") or "").strip(),
                                            FONT_BOLD),
                                           ((imza.get("unvan") or "").strip(),
                                            FONT))):
            h = ws.cell(satir + r, bas, metin)
            h.font = font
            h.alignment = ORTA
            if son > bas:
                ws.merge_cells(start_row=satir + r, start_column=bas,
                               end_row=satir + r, end_column=son)
    return satir + 2


def _yonu_sec(ws, son_satir):
    """Icerigin en/boy oranina gore dikey mi yatay mi basilacagini secer.

    Devrik tablolarda sayfa enine buyur, boyuna kisalir. Dikey A4'e zorlanirsa
    Excel olcegi yuzde kirklara indirir ve 10 puntoluk yazi okunmaz olur.
    Iki yon icin de sigma olcegi hesaplanip buyugu secilir.
    """
    en = sum(_sutun_genisligi(ws, s) for s in range(1, _gen(ws) + 1)) * KARAKTER_INC
    boy = sum((ws.row_dimensions[r].height or VARSAYILAN_YUKSEKLIK)
              for r in range(1, son_satir + 1)) / 72.0
    kenar_en = ws.page_margins.left + ws.page_margins.right
    kenar_boy = ws.page_margins.top + ws.page_margins.bottom
    en = max(en, 0.01)
    boy = max(boy, 0.01)
    olcek = {}
    for yon, (sayfa_en, sayfa_boy) in (("portrait", (A4_EN, A4_BOY)),
                                       ("landscape", (A4_BOY, A4_EN))):
        olcek[yon] = min((sayfa_en - kenar_en) / en, (sayfa_boy - kenar_boy) / boy)
    secim = "landscape" if olcek["landscape"] > olcek["portrait"] else "portrait"
    ws.page_setup.orientation = secim
    return secim, olcek[secim]


def _yil_sayfasi(wb, yil, donemler, inceleme, fis):
    ws = wb.create_sheet(str(yil))
    _sayfa_kur(ws, donemler)
    _olcum_kur(ws)
    genislik = _gen(ws)
    satir = 1

    _yaz(ws, satir, 1, "DÜZELTME FİŞİ", FONT_BASLIK, ORTA, bicim=None)
    ws.merge_cells(start_row=satir, start_column=1, end_row=satir,
                   end_column=genislik)
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
                   tuple((("beyan", kod), etiket) for kod, etiket in SUTUNLAR))
    satir += 1

    # Fazla ve yersiz devredilen KDV. Aylik tutar ONCEKI DONEMDEN DEVIR
    # farkindan okunur: fazla devir bir ay beyan edilir, zarar ertesi ay o
    # tutar devralindiginda dogar. Uyumsuzlugun dogdugu ay bu yuzden devrin
    # ALINDIGI aydir, verildigi ay degil.
    aylik_uyumsuzluk = [_deger(d, ("beyan", "onceki_devir"))
                        - _deger(d, ("elestirili", "onceki_devir"))
                        for d in donemler]
    # Yil tutari: son donemde beyandaki devir ile olmasi gereken devir
    # arasindaki fark - ertesi yila fazla devredilen KDV. Aylik farklarin
    # toplami alinmaz; devir bir stok kalemidir.
    son = donemler[-1]
    uyumsuzluk = round(_deger(son, ("beyan", "sonraki_devir"))
                       - _deger(son, ("elestirili", "sonraki_devir")), 2)
    satir = _tablo(ws, satir, "MÜKELLEF ADINA OLMASI GEREKEN", donemler,
                   tuple((("elestirili", kod), etiket)
                         for kod, etiket in SUTUNLAR),
                   vurgu_satiri=("Devreden KDV Uyumsuzluk Tutarı",
                                 aylik_uyumsuzluk, uyumsuzluk))
    satir += 1

    satir = _tablo(ws, satir, "TARHI GEREKEN VERGİ", donemler,
                   TARHIYAT_SATIRLARI)
    satir += 1

    gerekce = (fis.get("gerekce") or "").strip()
    if gerekce:
        h = ws.cell(satir, 1, gerekce)
        h.font = FONT
        h.alignment = SOL
        ws.merge_cells(start_row=satir, start_column=1, end_row=satir + 2,
                       end_column=genislik)
        satir += 3

    satir = _imza_blogu(ws, satir, _imzalari_coz(fis))
    _genislikleri_uygula(ws)
    _yukseklikleri_uygula(ws)   # genislikler yazildiktan SONRA; sirasi onemli
    _yonu_sec(ws, satir)        # yon, olculer belli olduktan sonra secilir
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
