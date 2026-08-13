"""Word (.docx) belgesi ureten kucuk bir yazici. Yalnizca standart kutuphane.

Neden kendi yazicimiz:
    `python-docx` lxml'e bagimlidir; lxml derlenmis bir eklentidir ve
    kullanicinin Python 3.8 kurulumunda ek paket kurmayi gerektirir. Daha once
    tam da boyle bir ek paket (Pillow + typing_extensions) uygulamanin hic
    acilmamasina yol acti. Bu yuzden yeni bagimlilik almiyoruz.

`.docx` aslinda icinde XML dosyalari bulunan bir zip arsividir. Bir taslak
belge icin gereken parca sayisi azdir: icerik turleri, iki iliski dosyasi,
stiller ve belgenin kendisi. Hepsi asagida uretilir.

Kullanim:

    b = Belge()
    b.baslik("VERGI INCELEME TUTANAGI", duzey=1)
    b.paragraf("...")
    b.tablo(["Donem", "Tutar"], [["2023/Ocak", "1.000,00"]], hizalar=["sol", "sag"])
    veri = b.bayt()

Uretilen belge A4, Times New Roman 12 punto, 1,5 satir araliklidir.
"""
import io
import re
import zipfile

# Word olcu birimleri
# dxa  : 1/20 punto (1 cm = 567 dxa) -- sayfa ve tablo olculeri
# yarim punto : yazi buyuklugu (12 punto = 24)
A4_GENISLIK = 11906
A4_YUKSEKLIK = 16838
KENAR_BOSLUGU = 1134                       # 2 cm
YAZI_ALANI = A4_GENISLIK - 2 * KENAR_BOSLUGU

BASLIK_DOLGUSU = "D9D9D9"                  # tablo baslik satirinin gri zemini
TOPLAM_DOLGUSU = "EDEDED"                  # toplam satirinin daha acik zemini

# Cok sutunlu tutar tablolarinda kullanilan punto. Govde 12 punto; sekiz
# sutunlu bir tabloda 12 punto sigmaz, basliklar bolunur ve rakamlar taser.
TABLO_PUNTOSU = 9

_XML_BASI = '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'

# Doldurulmamis alanlarin yer tutuculari kirmizi yazilir; belgeyi okuyan
# nereleri elle dolduracagini bir bakista gorsun.
YER_TUTUCU_RENGI = "C00000"
_YER_TUTUCU = re.compile(r"(\[[^\[\]]*\])")

_HIZA_KODLARI = {"sol": "left", "orta": "center", "sag": "right", "iki": "both"}


def _kacir(metin):
    """Metni XML govdesine guvenle konulabilir hale getirir.

    Kullanicinin forma yazdigi her sey buradan gecer; XML'de yasak olan
    denetim karakterleri de atilir, yoksa Word dosyayi bozuk sayar.
    """
    if metin is None:
        return ""
    metin = str(metin)
    temiz = []
    for ch in metin:
        kod = ord(ch)
        if kod in (0x09, 0x0A, 0x0D) or kod >= 0x20:
            temiz.append(ch)
    metin = "".join(temiz)
    return (metin.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
                 .replace('"', "&quot;"))


# Tablo sigdirmada kullanilan olculer
GOVDE_PUNTOSU = 12          # belge govde puntosu (stiller.xml ile ayni)
EN_KUCUK_PUNTO = 7          # bundan kucugu okunmuyor; asagi inilmez
GENIS_HUCRE_BOSLUGU = 216   # Word varsayilani (sutun basina, iki yan toplam)
DAR_HUCRE_BOSLUGU = 86


def _en_uzun_hucreler(basliklar, satirlar, kolon_sayisi):
    """Her kolon icin en uzun satirin karakter sayisi.

    Hucre icindeki alt satirlar (\\n) ayri ayri olculur: baslikta "Dönemi\\n2023"
    yazdiginda kolonun genisligini "Dönemi" belirler, ikisinin toplami degil.
    """
    uzunluklar = [0] * kolon_sayisi
    for satir in [basliklar] + list(satirlar or []):
        for i, hucre in enumerate(list(satir)[:kolon_sayisi]):
            for parca in str(hucre or "").split("\n"):
                uzunluklar[i] = max(uzunluklar[i], len(parca))
    return uzunluklar


def _icerik_agirliklari(basliklar, satirlar, kolon_sayisi):
    """Kolon genislik agirliklarini icerikten cikarir.

    Oran verilmediginde kolonlari esit bolmek, kisa kolonlara gereksiz yer
    ayirip uzun kolonlari alt satira dusuruyordu. En kisa kolon da okunabilsin
    diye alt sinir konur.
    """
    uzunluklar = _en_uzun_hucreler(basliklar, satirlar, kolon_sayisi)
    return [max(u, 4) for u in uzunluklar]


def _sigacak_punto(basliklar, satirlar, kolon_sayisi, buyukluk, dar):
    """Tablonun sayfaya sigmasi icin punto ve hucre boslugu secer.

    Times New Roman'da rakam ve ortalama harf genisligi yaklasik yarim em'dir;
    gereken genislik buradan kestirilir. Once dar hucre boslugu denenir,
    yetmezse punto oranli olarak kucultulur.
    """
    punto = float(buyukluk or GOVDE_PUNTOSU)
    uzunluklar = _en_uzun_hucreler(basliklar, satirlar, kolon_sayisi)
    karakter = float(sum(uzunluklar))
    if karakter <= 0:
        return buyukluk, dar

    def gereken(p, bosluk):
        return karakter * p * 10.0 + bosluk * kolon_sayisi

    if gereken(punto, DAR_HUCRE_BOSLUGU if dar else GENIS_HUCRE_BOSLUGU) <= YAZI_ALANI:
        return buyukluk, dar

    dar = True
    kalan = YAZI_ALANI - DAR_HUCRE_BOSLUGU * kolon_sayisi
    if kalan <= 0:
        return EN_KUCUK_PUNTO, dar
    yeni = min(punto, kalan / (karakter * 10.0))
    yeni = max(EN_KUCUK_PUNTO, round(yeni * 2) / 2.0)   # yarim puntoya yuvarla
    return yeni, dar


def _rpr(kalin, italik, buyukluk, renk=None):
    """Kosu bicim blogu. Ogelerin sirasi Word semasinin bekledigi siradir."""
    ozellikler = []
    if kalin:
        ozellikler.append("<w:b/>")
    if italik:
        ozellikler.append("<w:i/>")
    if renk:
        ozellikler.append('<w:color w:val="%s"/>' % renk)
    if buyukluk:
        # Word yazi buyuklugunu yarim punto biriminde tutar; kesirli punto
        # (orn. 8,5) bu sayede yazilabiliyor.
        yarim = max(1, int(round(float(buyukluk) * 2)))
        ozellikler.append('<w:sz w:val="%d"/><w:szCs w:val="%d"/>'
                          % (yarim, yarim))
    return "<w:rPr>%s</w:rPr>" % "".join(ozellikler) if ozellikler else ""


def _kosular(metin, kalin=False, italik=False, buyukluk=None, renk=None):
    """Bir paragrafin ic parcalarini (w:r) uretir; satir sonlarini korur.

    Kose parantezli parcalar kirmizi yazilir. Bu parcalar, kunyede
    doldurulmamis alanlarin yerine konan tutuculardir; belgeyi okuyanin
    "burayi elle dolduracagim" diyebilmesi icin goze carpmalari gerekir.

    `renk` verildiginde paragrafin tamami o renkte yazilir; koseli parantez
    kullanmadan dikkat cekmesi gereken notlar icindir.
    """
    duz = _rpr(kalin, italik, buyukluk, renk)
    kirmizi = _rpr(kalin, italik, buyukluk, YER_TUTUCU_RENGI)
    parcalar = []
    satirlar = str(metin or "").split("\n")
    for i, satir in enumerate(satirlar):
        if i:
            parcalar.append("<w:r>%s<w:br/></w:r>" % duz)
        for parca in _YER_TUTUCU.split(satir):
            if not parca:
                continue
            rpr = kirmizi if _YER_TUTUCU.match(parca) else duz
            parcalar.append('<w:r>%s<w:t xml:space="preserve">%s</w:t></w:r>'
                            % (rpr, _kacir(parca)))
    if not parcalar:
        parcalar.append("<w:r>%s</w:r>" % duz)
    return "".join(parcalar)


class Belge:
    """Sirayla paragraf ve tablo eklenen bir taslak belge."""

    def __init__(self):
        self._govde = []          # document.xml icine girecek XML parcalari
        self._duz = []            # ayni icerigin duz metin karsiligi

    # ------------------------------------------------------------- paragraflar
    def paragraf(self, metin="", kalin=False, italik=False, hiza="iki",
                 buyukluk=None, girinti=0, aralik_once=0, aralik_sonra=120,
                 renk=None):
        """Duz paragraf ekler. `girinti` cm cinsindendir."""
        ozellikler = ['<w:spacing w:before="%d" w:after="%d" w:line="360" '
                      'w:lineRule="auto"/>' % (aralik_once, aralik_sonra)]
        if girinti:
            ozellikler.append('<w:ind w:firstLine="%d"/>' % int(girinti * 567))
        ozellikler.append('<w:jc w:val="%s"/>' % _HIZA_KODLARI.get(hiza, "both"))
        self._govde.append("<w:p><w:pPr>%s</w:pPr>%s</w:p>"
                           % ("".join(ozellikler),
                              _kosular(metin, kalin, italik, buyukluk, renk)))
        self._duz.append(str(metin or ""))
        return self

    def baslik(self, metin, duzey=1, hiza="sol"):
        """Bolum basligi.

        Ikisi de sola dayalidir; belge basligi gibi ortalanmasi gereken tek
        tuk yerde `hiza="orta"` verilir. 1. duzey daha buyuk punto ve daha
        genis ust bosluk alir.
        """
        if duzey == 1:
            self.paragraf(metin, kalin=True, hiza=hiza, buyukluk=14,
                          aralik_once=240, aralik_sonra=180)
            self._duz[-1] = "\n" + metin.upper()
        else:
            self.paragraf(metin, kalin=True, hiza=hiza,
                          aralik_once=180, aralik_sonra=120)
            self._duz[-1] = "\n" + metin
        return self

    def bos_satir(self):
        return self.paragraf("", aralik_sonra=0)

    def sayfa_sonu(self):
        self._govde.append('<w:p><w:r><w:br w:type="page"/></w:r></w:p>')
        self._duz.append("\f")
        return self

    def madde_listesi(self, maddeler, numarali=True):
        """Sorular/cevaplar gibi sirali metinleri madde madde yazar."""
        for i, madde in enumerate(maddeler, 1):
            on = "%d. " % i if numarali else "- "
            self.paragraf(on + str(madde or ""), hiza="iki", aralik_sonra=80)
        return self

    # ------------------------------------------------------------------ tablo
    def tablo(self, basliklar, satirlar, hizalar=None, oranlar=None,
              baslik_tekrari=True, buyukluk=None, toplam_satiri=False,
              dar=False):
        """Tam sayfa genisliginde, cerceveli bir tablo ekler.

        basliklar    : baslik hucrelerinin metinleri
        satirlar     : her biri baslik sayisi kadar hucre tasiyan diziler
        hizalar      : kolon basina "sol" / "orta" / "sag" (tutarlar icin "sag")
        oranlar      : kolon genislik agirliklari; verilmezse esit bolusulur
        buyukluk     : hucre yazi buyuklugu (punto). Cok sutunlu tutar
                       tablolari 12 puntoda sigmaz; basliklar satir ortasindan
                       bolunur ve rakamlar alt satira taser.
        toplam_satiri: son satir kalin yazilir ve zemini griler
        dar          : hucre ic bosluklarini daraltir. Word'un varsayilan
                       bosluklari sutun basina 216 twip yer yer; dokuz on
                       sutunlu tutar tablolarinda bu, rakamlarin alt satira
                       kaymasina yol aciyor.

        Genislik ve punto icerige gore ayarlanir: en uzun hucrelerin sayfaya
        sigmadigi tablolarda once hucre bosluklari daraltilir, yetmezse punto
        oranli olarak kucultulur (en az `EN_KUCUK_PUNTO`). Boylece satirlar
        alt satira kaymaz.
        """
        kolon_sayisi = len(basliklar)
        if not kolon_sayisi:
            return self
        hizalar = list(hizalar or ["sol"] * kolon_sayisi)
        hizalar += ["sol"] * (kolon_sayisi - len(hizalar))
        agirliklar = list(oranlar or _icerik_agirliklari(basliklar, satirlar,
                                                         kolon_sayisi))
        agirliklar += [1] * (kolon_sayisi - len(agirliklar))
        buyukluk, dar = _sigacak_punto(basliklar, satirlar, kolon_sayisi,
                                       buyukluk, dar)
        toplam = float(sum(agirliklar)) or 1.0
        genislikler = [int(YAZI_ALANI * a / toplam) for a in agirliklar]
        # Yuvarlama artigini son kolona ver ki tablo tam genislikte kalsin
        genislikler[-1] += YAZI_ALANI - sum(genislikler)

        cerceve = "".join(
            '<w:%s w:val="single" w:sz="4" w:space="0" w:color="808080"/>' % kenar
            for kenar in ("top", "left", "bottom", "right", "insideH", "insideV"))
        kenar_boslugu = ""
        if dar:
            kenar_boslugu = (
                '<w:tblCellMar>'
                '<w:left w:w="43" w:type="dxa"/><w:right w:w="43" w:type="dxa"/>'
                '</w:tblCellMar>')
        parcalar = [
            # Sira onemli: OOXML semasinda tblCellMar, tblLayout'tan sonra
            # gelir; ters yazildiginda Word belgeyi bozuk sayar.
            '<w:tbl><w:tblPr><w:tblW w:w="%d" w:type="dxa"/>'
            '<w:tblBorders>%s</w:tblBorders>'
            '<w:tblLayout w:type="fixed"/>%s</w:tblPr><w:tblGrid>%s</w:tblGrid>'
            % (YAZI_ALANI, cerceve, kenar_boslugu,
               "".join('<w:gridCol w:w="%d"/>' % g for g in genislikler))]

        parcalar.append(self._satir_xml(basliklar, genislikler, hizalar,
                                        kalin=True, dolgu=BASLIK_DOLGUSU,
                                        baslik_satiri=baslik_tekrari,
                                        buyukluk=buyukluk))
        son = len(satirlar) - 1
        for i, satir in enumerate(satirlar):
            hucreler = list(satir) + [""] * (kolon_sayisi - len(satir))
            vurgulu = toplam_satiri and i == son
            parcalar.append(self._satir_xml(
                hucreler[:kolon_sayisi], genislikler, hizalar,
                kalin=vurgulu, dolgu=TOPLAM_DOLGUSU if vurgulu else None,
                buyukluk=buyukluk))
        parcalar.append("</w:tbl>")
        self._govde.append("".join(parcalar))
        # Word, tablodan hemen sonra bir paragraf bekler; tablolar art arda
        # gelirse ikisini tek tablo sayar.
        self._govde.append('<w:p><w:pPr><w:spacing w:after="120"/></w:pPr></w:p>')

        self._duz.append(_duz_tablo(basliklar, satirlar))
        return self

    def _satir_xml(self, hucreler, genislikler, hizalar, kalin=False,
                   dolgu=None, baslik_satiri=False, buyukluk=None):
        parcalar = ["<w:tr>"]
        if baslik_satiri:
            parcalar.append("<w:trPr><w:tblHeader/></w:trPr>")
        for i, hucre in enumerate(hucreler):
            ozellikler = ['<w:tcW w:w="%d" w:type="dxa"/>' % genislikler[i]]
            if dolgu:
                ozellikler.append('<w:shd w:val="clear" w:color="auto" w:fill="%s"/>'
                                  % dolgu)
            ozellikler.append('<w:vAlign w:val="center"/>')
            parcalar.append(
                "<w:tc><w:tcPr>%s</w:tcPr>"
                '<w:p><w:pPr><w:spacing w:before="40" w:after="40" w:line="240" '
                'w:lineRule="auto"/><w:jc w:val="%s"/></w:pPr>%s</w:p></w:tc>'
                % ("".join(ozellikler), _HIZA_KODLARI.get(hizalar[i], "left"),
                   _kosular(hucre, kalin=kalin, buyukluk=buyukluk)))
        parcalar.append("</w:tr>")
        return "".join(parcalar)

    # ------------------------------------------------------------------ imza
    def imza_bloklari(self, imzalar):
        """Yan yana imza sutunlari; her oge (sifat, ad soyad) ciftidir.

        Basligin altinda bilerek bos bir satir birakilir: islak imza oraya
        atilir, ad soyad en altta yazili kalir.
        """
        if not imzalar:
            return self
        self.bos_satir()
        self.tablo([sifat for sifat, _ad in imzalar],
                   [["\n\n"] * len(imzalar),          # imza icin bosluk
                    [ad for _sifat, ad in imzalar]],
                   hizalar=["orta"] * len(imzalar))
        return self

    # ------------------------------------------------------------------ cikti
    def duz_metin(self):
        """Ayni icerigin panoya yapistirilabilir duz metin karsiligi."""
        return "\n".join(self._duz).replace("\f", "\n" + "-" * 60 + "\n")

    def bayt(self):
        """Belgeyi .docx bayt dizisi olarak dondurur."""
        tampon = io.BytesIO()
        # Sabit tarih: ayni veriden ayni dosya uretilsin
        tarih = (2020, 1, 1, 0, 0, 0)
        with zipfile.ZipFile(tampon, "w", zipfile.ZIP_DEFLATED) as z:
            for ad, icerik in self._parcalar().items():
                bilgi = zipfile.ZipInfo(ad, tarih)
                bilgi.compress_type = zipfile.ZIP_DEFLATED
                z.writestr(bilgi, icerik.encode("utf-8"))
        return tampon.getvalue()

    def kaydet(self, yol):
        with open(yol, "wb") as f:
            f.write(self.bayt())
        return yol

    def _parcalar(self):
        return {
            "[Content_Types].xml": _ICERIK_TURLERI,
            "_rels/.rels": _KOK_ILISKILER,
            "word/_rels/document.xml.rels": _BELGE_ILISKILERI,
            "word/styles.xml": _STILLER,
            "word/document.xml": _XML_BASI + (
                '<w:document xmlns:w="%s"><w:body>%s%s</w:body></w:document>'
                % (_W, "".join(self._govde), _SAYFA_DUZENI)),
        }


def _duz_tablo(basliklar, satirlar):
    """Duz metin ciktisinda tabloyu okunabilir tutmak icin sekmeyle ayirir."""
    hepsi = [list(basliklar)] + [list(s) for s in satirlar]
    return "\n".join("\t".join(str(h or "") for h in satir) for satir in hepsi)


_W = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"

_ICERIK_TURLERI = _XML_BASI + (
    '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
    '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.'
    'relationships+xml"/>'
    '<Default Extension="xml" ContentType="application/xml"/>'
    '<Override PartName="/word/document.xml" ContentType="application/vnd.'
    'openxmlformats-officedocument.wordprocessingml.document.main+xml"/>'
    '<Override PartName="/word/styles.xml" ContentType="application/vnd.'
    'openxmlformats-officedocument.wordprocessingml.styles+xml"/>'
    "</Types>")

_KOK_ILISKILER = _XML_BASI + (
    '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/'
    'relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/'
    'officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/>'
    "</Relationships>")

_BELGE_ILISKILERI = _XML_BASI + (
    '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/'
    'relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/'
    'officeDocument/2006/relationships/styles" Target="styles.xml"/>'
    "</Relationships>")

# Belgenin tamaminda gecerli yazi tipi ve satir araligi burada tanimlanir;
# paragraflar ayrica kendi araliklarini verir.
_STILLER = _XML_BASI + (
    '<w:styles xmlns:w="%s"><w:docDefaults><w:rPrDefault><w:rPr>'
    '<w:rFonts w:ascii="Times New Roman" w:hAnsi="Times New Roman" '
    'w:eastAsia="Times New Roman" w:cs="Times New Roman"/>'
    '<w:sz w:val="24"/><w:szCs w:val="24"/><w:lang w:val="tr-TR"/>'
    "</w:rPr></w:rPrDefault><w:pPrDefault><w:pPr>"
    '<w:spacing w:after="120" w:line="360" w:lineRule="auto"/>'
    "</w:pPr></w:pPrDefault></w:docDefaults>"
    # Yazi tipi hem docDefaults'ta hem Normal stilinde verilir: bazi okuyucular
    # (ozellikle LibreOffice'in eski surumleri) yalnizca stile bakiyor.
    '<w:style w:type="paragraph" w:default="1" w:styleId="Normal">'
    '<w:name w:val="Normal"/><w:rPr>'
    '<w:rFonts w:ascii="Times New Roman" w:hAnsi="Times New Roman" '
    'w:eastAsia="Times New Roman" w:cs="Times New Roman"/>'
    '<w:sz w:val="24"/><w:szCs w:val="24"/></w:rPr></w:style></w:styles>' % _W)

_SAYFA_DUZENI = (
    '<w:sectPr><w:pgSz w:w="%d" w:h="%d"/>'
    '<w:pgMar w:top="%d" w:right="%d" w:bottom="%d" w:left="%d" '
    'w:header="708" w:footer="708" w:gutter="0"/></w:sectPr>'
    % (A4_GENISLIK, A4_YUKSEKLIK, KENAR_BOSLUGU, KENAR_BOSLUGU,
       KENAR_BOSLUGU, KENAR_BOSLUGU))
