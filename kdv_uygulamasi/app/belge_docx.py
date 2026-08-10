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
import zipfile

# Word olcu birimleri
# dxa  : 1/20 punto (1 cm = 567 dxa) -- sayfa ve tablo olculeri
# yarim punto : yazi buyuklugu (12 punto = 24)
A4_GENISLIK = 11906
A4_YUKSEKLIK = 16838
KENAR_BOSLUGU = 1134                       # 2 cm
YAZI_ALANI = A4_GENISLIK - 2 * KENAR_BOSLUGU

BASLIK_DOLGUSU = "D9D9D9"                  # tablo baslik satirinin gri zemini

_XML_BASI = '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'

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


def _kosular(metin, kalin=False, italik=False, buyukluk=None):
    """Bir paragrafin ic parcalarini (w:r) uretir; satir sonlarini korur."""
    ozellikler = []
    if kalin:
        ozellikler.append("<w:b/>")
    if italik:
        ozellikler.append("<w:i/>")
    if buyukluk:
        ozellikler.append('<w:sz w:val="%d"/><w:szCs w:val="%d"/>'
                          % (buyukluk * 2, buyukluk * 2))
    rpr = "<w:rPr>%s</w:rPr>" % "".join(ozellikler) if ozellikler else ""
    parcalar = []
    satirlar = str(metin or "").split("\n")
    for i, satir in enumerate(satirlar):
        if i:
            parcalar.append("<w:r>%s<w:br/></w:r>" % rpr)
        if satir:
            parcalar.append('<w:r>%s<w:t xml:space="preserve">%s</w:t></w:r>'
                            % (rpr, _kacir(satir)))
    if not parcalar:
        parcalar.append("<w:r>%s</w:r>" % rpr)
    return "".join(parcalar)


class Belge:
    """Sirayla paragraf ve tablo eklenen bir taslak belge."""

    def __init__(self):
        self._govde = []          # document.xml icine girecek XML parcalari
        self._duz = []            # ayni icerigin duz metin karsiligi

    # ------------------------------------------------------------- paragraflar
    def paragraf(self, metin="", kalin=False, italik=False, hiza="iki",
                 buyukluk=None, girinti=0, aralik_once=0, aralik_sonra=120):
        """Duz paragraf ekler. `girinti` cm cinsindendir."""
        ozellikler = ['<w:spacing w:before="%d" w:after="%d" w:line="360" '
                      'w:lineRule="auto"/>' % (aralik_once, aralik_sonra)]
        if girinti:
            ozellikler.append('<w:ind w:firstLine="%d"/>' % int(girinti * 567))
        ozellikler.append('<w:jc w:val="%s"/>' % _HIZA_KODLARI.get(hiza, "both"))
        self._govde.append("<w:p><w:pPr>%s</w:pPr>%s</w:p>"
                           % ("".join(ozellikler),
                              _kosular(metin, kalin, italik, buyukluk)))
        self._duz.append(str(metin or ""))
        return self

    def baslik(self, metin, duzey=1):
        """Bolum basligi. 1. duzey ortali ve 14 punto, 2. duzey sola dayali."""
        if duzey == 1:
            self.paragraf(metin, kalin=True, hiza="orta", buyukluk=14,
                          aralik_once=240, aralik_sonra=180)
            self._duz[-1] = "\n" + metin.upper()
        else:
            self.paragraf(metin, kalin=True, hiza="sol",
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
              baslik_tekrari=True):
        """Tam sayfa genisliginde, cerceveli bir tablo ekler.

        basliklar : baslik hucrelerinin metinleri
        satirlar  : her biri baslik sayisi kadar hucre tasiyan diziler
        hizalar   : kolon basina "sol" / "orta" / "sag" (tutarlar icin "sag")
        oranlar   : kolon genislik agirliklari; verilmezse esit bolusulur
        """
        kolon_sayisi = len(basliklar)
        if not kolon_sayisi:
            return self
        hizalar = list(hizalar or ["sol"] * kolon_sayisi)
        hizalar += ["sol"] * (kolon_sayisi - len(hizalar))
        agirliklar = list(oranlar or [1] * kolon_sayisi)
        agirliklar += [1] * (kolon_sayisi - len(agirliklar))
        toplam = float(sum(agirliklar)) or 1.0
        genislikler = [int(YAZI_ALANI * a / toplam) for a in agirliklar]
        # Yuvarlama artigini son kolona ver ki tablo tam genislikte kalsin
        genislikler[-1] += YAZI_ALANI - sum(genislikler)

        cerceve = "".join(
            '<w:%s w:val="single" w:sz="4" w:space="0" w:color="808080"/>' % kenar
            for kenar in ("top", "left", "bottom", "right", "insideH", "insideV"))
        parcalar = [
            '<w:tbl><w:tblPr><w:tblW w:w="%d" w:type="dxa"/>'
            '<w:tblBorders>%s</w:tblBorders>'
            '<w:tblLayout w:type="fixed"/></w:tblPr><w:tblGrid>%s</w:tblGrid>'
            % (YAZI_ALANI, cerceve,
               "".join('<w:gridCol w:w="%d"/>' % g for g in genislikler))]

        parcalar.append(self._satir_xml(basliklar, genislikler, hizalar,
                                        kalin=True, dolgu=BASLIK_DOLGUSU,
                                        baslik_satiri=baslik_tekrari))
        for satir in satirlar:
            hucreler = list(satir) + [""] * (kolon_sayisi - len(satir))
            parcalar.append(self._satir_xml(hucreler[:kolon_sayisi], genislikler,
                                            hizalar))
        parcalar.append("</w:tbl>")
        self._govde.append("".join(parcalar))
        # Word, tablodan hemen sonra bir paragraf bekler; tablolar art arda
        # gelirse ikisini tek tablo sayar.
        self._govde.append('<w:p><w:pPr><w:spacing w:after="120"/></w:pPr></w:p>')

        self._duz.append(_duz_tablo(basliklar, satirlar))
        return self

    def _satir_xml(self, hucreler, genislikler, hizalar, kalin=False,
                   dolgu=None, baslik_satiri=False):
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
                   _kosular(hucre, kalin=kalin)))
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
