"""Hazir bir Word (.docx) formunun tablosunu doldurur.

`belge_docx` SIFIRDAN belge yazar; burasi tersini yapar: kullanicinin
verdigi bir dosyayi ACAR, icindeki tabloyu bulur, satirlarini cogaltip
doldurur ve dosyayi geri verir. Formun kendi duzeni - antet, aciklama
metinleri, sutun genislikleri, yazi tipi, kenarliklar - oldugu gibi kalir;
yalnizca hucrelerin ICINE yazilir. Vergi dairesine giden form, dairenin
kendi bicimiyle gitmelidir; onu yeniden cizmek o bicimi kaybetmek olurdu.

Yine yalnizca standart kutuphane: `.docx` bir zip arsividir, icindeki
`word/document.xml` ayristirilir ve arsiv birebir yeniden yazilir - yalnizca
o parca degisir, kalan her parca (stiller, antet, gomulu resimler)
dokunulmadan kopyalanir.

Kullanim:

    form = Form(ham_baytlar)
    tablo = form.tablolar()[0]
    tablo.doldur([["1", "Örnek Ltd", "1234567890"], ...])
    yeni = form.bayt()

Tuzaklar:

- **Onek adlari korunur.** ElementTree bilmedigi ad alani oneklerini
  "ns0" diye yeniden adlandirir; `mc:Ignorable="w14 wp14"` gibi degerler
  ONEK adi tasidigindan bu, Word'un dosyayi bozuk saymasina yol acar. Bu
  yuzden belgedeki butun xmlns bildirimleri okunup once kaydedilir.
- **Hucreye yazarken ilk kosunun (run) bicimi korunur.** Metni silip
  yenisini yazmak yazi tipini de silerdi; bunun yerine ilk kosunun metni
  degistirilip oteki kosular atilir.
"""
import copy
import io
import re
import zipfile
import xml.etree.ElementTree as ET

BELGE_PARCASI = "word/document.xml"
W = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
XML_NS = "http://www.w3.org/XML/1998/namespace"

_XMLNS = re.compile(br'xmlns:([A-Za-z0-9_.-]+)\s*=\s*"([^"]+)"')
_XMLNS_BILDIRIMI = re.compile(br'xmlns(?::[A-Za-z0-9_.-]+)?\s*=\s*"[^"]*"')
# Belgenin kok acilis etiketi: "<?xml ...?>" ve "<!-- -->" ile baslamadigi
# icin ilk eslesme her zaman kok ogedir.
_KOK_ETIKETI = re.compile(br"<([A-Za-z_][^\s/>]*)([^>]*)>")


class FormHata(Exception):
    """Dosya .docx degil ya da icinde beklenen parca yok."""


def _ad(etiket):
    return "{%s}%s" % (W, etiket)


def _onekleri_kaydet(ham_xml):
    """Belgedeki butun ad alani oneklerini ElementTree'ye bildirir.

    Bildirilmezse cikti "ns0:" gibi uydurma oneklerle yazilir; `mc:Ignorable`
    bu onek adlarini metin olarak tasidigi icin dosya Word'de acilmaz.
    """
    for onek, uri in _XMLNS.findall(ham_xml):
        try:
            ET.register_namespace(onek.decode("ascii"), uri.decode("utf-8"))
        except (UnicodeDecodeError, ValueError):
            continue


def karsilastir(metin):
    """Sutun adi karsilastirmasi icin sadelestirir.

    Formdaki adlar yildiz, iki nokta, satir sonu ve degisken buyuk/kucuk
    harf tasiyor ("SAHTE BELGE KULLANIM BİLGİLERİ **"); Turkce I/i cifti de
    `lower()` ile bozuldugundan elle esleniyor.
    """
    metin = str(metin or "")
    for a, b in (("İ", "i"), ("I", "ı"), ("Ü", "ü"), ("Ö", "ö"),
                 ("Ş", "ş"), ("Ç", "ç"), ("Ğ", "ğ")):
        metin = metin.replace(a, b)
    metin = metin.lower()
    return " ".join(ch for ch in metin.split() if ch).strip(" *:.\n\t")


def hucre_metni(hucre):
    """Bir tablo hucresindeki butun metin, satir sonlari korunarak."""
    parcalar = []
    for p in hucre.iter(_ad("p")):
        satir = "".join(t.text or "" for t in p.iter(_ad("t")))
        parcalar.append(satir)
    return "\n".join(parcalar).strip()


def _hucreye_yaz(hucre, metin):
    """Hucrenin metnini degistirir; ilk kosunun bicimi korunur.

    Hucrede hic kosu yoksa (bos form hucreleri cogu zaman boyledir) yeni bir
    paragraf ve kosu acilir; bicim o zaman hucrenin kendi varsayilanidir.
    """
    metin = "" if metin is None else str(metin)
    paragraflar = list(hucre.iter(_ad("p")))
    if not paragraflar:
        p = ET.SubElement(hucre, _ad("p"))
        paragraflar = [p]
    ilk = paragraflar[0]
    # Fazla paragraflar atilir: hucre tek satir yazacak.
    for p in paragraflar[1:]:
        for ana in hucre.iter():
            if p in list(ana):
                ana.remove(p)
                break

    kosular = ilk.findall(_ad("r"))
    if kosular:
        tutulan, atilacak = kosular[0], kosular[1:]
        for r in atilacak:
            ilk.remove(r)
        for t in tutulan.findall(_ad("t")):
            tutulan.remove(t)
    else:
        tutulan = ET.SubElement(ilk, _ad("r"))

    satirlar = metin.split("\n")
    for i, satir in enumerate(satirlar):
        if i:
            ET.SubElement(tutulan, _ad("br"))
        t = ET.SubElement(tutulan, _ad("t"))
        t.set("{%s}space" % XML_NS, "preserve")
        t.text = satir
    return hucre


def _bicimi_sadelestir(satir):
    """Baslik satirindan klonlanan satirin baslik bicimini siler.

    Formda baslik disinda hic satir yoksa sablon olarak baslik satiri
    kullanilir; gri zemin ve kalin yazi oldugu gibi kalirsa butun veri
    satirlari baslik gibi gorunurdu.
    """
    for hucre in satir.findall(_ad("tc")):
        for ozellik in hucre.findall(_ad("tcPr")):
            for shd in ozellik.findall(_ad("shd")):
                ozellik.remove(shd)
        for p in hucre.iter(_ad("p")):
            for r in p.findall(_ad("r")):
                for rPr in r.findall(_ad("rPr")):
                    for etiket in ("b", "bCs"):
                        for e in rPr.findall(_ad(etiket)):
                            rPr.remove(e)
    return satir


class Tablo:
    """Belgedeki bir tablo. Satirlar `w:tr`, hucreler `w:tc`."""

    def __init__(self, oge):
        self.oge = oge

    def satirlar(self):
        # Yalnizca DOGRUDAN alt satirlar: ic ice tablolarin satirlari
        # bu tablonun satiri degildir.
        return self.oge.findall(_ad("tr"))

    def hucreler(self, satir):
        return satir.findall(_ad("tc"))

    def basliklar(self, indeks=0):
        """Verilen satirin hucre metinleri (varsayilan: ilk satir)."""
        satirlar = self.satirlar()
        if indeks >= len(satirlar):
            return []
        return [hucre_metni(h) for h in self.hucreler(satirlar[indeks])]

    def baslik_indeksi(self, anahtarlar):
        """Sutun adlarini tasiyan satirin sirasi; bulunamazsa None.

        Formlarda tablonun ILK satiri cogu zaman tek hucreli bir BASLIK
        satiridir ("SAHTE BELGE KULLANIM BILGILERI") ve sutun adlari bir alt
        satirdadir. Bu yuzden sutun satiri sirayla degil, aranan adlarin
        hepsini tasiyan satir olarak bulunur.
        """
        anahtarlar = [karsilastir(a) for a in anahtarlar]
        for i, satir in enumerate(self.metinler()):
            hucreler = [karsilastir(h) for h in satir]
            if all(any(a and a in h for h in hucreler) for a in anahtarlar):
                return i
        return None

    def metinler(self):
        """Butun satirlarin hucre metinleri (tani ve denetim icin)."""
        return [[hucre_metni(h) for h in self.hucreler(s)]
                for s in self.satirlar()]

    def doldur(self, satirlar, baslik_satiri=1, toplam=None):
        """Baslik satirindan SONRAKI satirlari verilen degerlerle degistirir.

        `baslik_satiri`: kac satirin baslik sayilacagi. Formlarda tablonun
        ilk satiri cogu zaman tek hucreli bir baslik, sutun adlari bir alt
        satirdadir; o tabloda bu deger 2'dir (bkz. `baslik_indeksi`).

        `toplam`: {sutun_sirasi: metin}. Verilirse tablonun SON satiri bir
        TOPLAM satiri sayilir, veri satirlarindan sonra korunur ve yalnizca
        buradaki hucreleri yazilir - "TOPLAM" yazan hucre oldugu gibi kalir.

        Sablon olarak baslikten sonraki ILK veri satiri kullanilir ve mevcut
        veri satirlarinin tamami atilir; boylece formdaki bos ornek satirlar
        birikmez. Veri satiri yoksa baslik satiri klonlanip bicimi
        sadelestirilir.

        Doner: (yazilan satir sayisi, sutun sayisi).
        """
        tum = self.satirlar()
        basliklar = tum[:baslik_satiri]
        if not basliklar:
            raise FormHata("Tabloda başlık satırı yok.")
        veriler = tum[baslik_satiri:]
        toplam_satiri = None
        if toplam is not None and veriler:
            toplam_satiri = veriler.pop()
        sablon = (copy.deepcopy(veriler[0]) if veriler
                  else _bicimi_sadelestir(copy.deepcopy(basliklar[-1])))
        sutun_sayisi = len(self.hucreler(sablon))
        for s in veriler:
            self.oge.remove(s)
        if toplam_satiri is not None:
            self.oge.remove(toplam_satiri)

        for degerler in satirlar:
            yeni = copy.deepcopy(sablon)
            for i, hucre in enumerate(self.hucreler(yeni)):
                _hucreye_yaz(hucre, degerler[i] if i < len(degerler) else "")
            self.oge.append(yeni)

        if toplam_satiri is not None:
            hucreler = self.hucreler(toplam_satiri)
            for i, metin in (toplam or {}).items():
                if 0 <= i < len(hucreler):
                    _hucreye_yaz(hucreler[i], metin)
            self.oge.append(toplam_satiri)
        return len(satirlar), sutun_sayisi

    def hucreye_yaz(self, satir_sirasi, sutun_sirasi, metin):
        """Tek bir hucreye yazar (etiket/deger bicimindeki kucuk tablolar)."""
        satirlar = self.satirlar()
        if satir_sirasi >= len(satirlar):
            return False
        hucreler = self.hucreler(satirlar[satir_sirasi])
        if sutun_sirasi >= len(hucreler):
            return False
        _hucreye_yaz(hucreler[sutun_sirasi], metin)
        return True


class Form:
    """Acilmis bir .docx. `bayt()` ile geri yazilir."""

    def __init__(self, ham):
        try:
            with zipfile.ZipFile(io.BytesIO(ham)) as z:
                self._adlar = z.namelist()
                self._parcalar = {ad: z.read(ad) for ad in self._adlar}
                self._bilgiler = {i.filename: i for i in z.infolist()}
        except zipfile.BadZipFile:
            raise FormHata(
                "Dosya bir .docx değil. Word'de “Farklı Kaydet > Word "
                "Belgesi (.docx)” ile kaydedip yeniden deneyin; eski .doc "
                "biçimi okunamıyor.")
        if BELGE_PARCASI not in self._parcalar:
            raise FormHata("Dosyanın içinde word/document.xml yok; "
                           "bu bir Word belgesi değil.")
        self._ham_xml = self._parcalar[BELGE_PARCASI]
        _onekleri_kaydet(self._ham_xml)
        try:
            self.kok = ET.fromstring(self._ham_xml)
        except ET.ParseError as exc:
            raise FormHata("Word belgesi okunamadı: %s" % exc)

    def tablolar(self):
        return [Tablo(t) for t in self.kok.iter(_ad("tbl"))]

    def paragraf_metinleri(self):
        """Belgedeki paragraf metinleri (tablo disinda kalanlar dahil)."""
        return [("".join(t.text or "" for t in p.iter(_ad("t")))).strip()
                for p in self.kok.iter(_ad("p"))]

    def _govde(self):
        """document.xml'i yeniden yazar, kok etiketini ORIJINALIYLE degistirir.

        ElementTree kok etikete yalnizca KENDI kullandigi ad alanlarini
        bildirir. Word belgesinin kokunde ise kullanilmayan bir yigin
        bildirim daha vardir ve `mc:Ignorable="w14 w15 w16se wp14"` bunlarin
        ONEK adlarini metin olarak sayar. Bildirim dusunce o onekler bosa
        duser ve Word dosyayi "okunamayan icerik" diye reddeder - dosya
        acilmaz, uyari da vermez. Bu yuzden orijinal acilis etiketi oldugu
        gibi korunur; ElementTree'nin ekledigi ama orijinalde bulunmayan bir
        bildirim varsa (ic ogelerden hoist edilmis olabilir) sonuna eklenir.
        """
        govde = ET.tostring(self.kok, encoding="UTF-8", xml_declaration=True)
        eski = _KOK_ETIKETI.search(self._ham_xml)
        yeni = _KOK_ETIKETI.search(govde)
        if not (eski and yeni):
            return govde
        eski_etiket = eski.group(0)
        bildirimler = {b.split(b"=", 1)[0].strip(): b
                       for b in _XMLNS_BILDIRIMI.findall(eski_etiket)}
        eksikler = [b for b in _XMLNS_BILDIRIMI.findall(yeni.group(0))
                    if b.split(b"=", 1)[0].strip() not in bildirimler]
        if eksikler:
            eski_etiket = (eski_etiket[:-1].rstrip() + b" "
                           + b" ".join(eksikler) + b">")
        return govde[:yeni.start()] + eski_etiket + govde[yeni.end():]

    def bayt(self):
        """Arsivi yeniden yazar; yalnizca document.xml degismistir."""
        govde = self._govde()
        tampon = io.BytesIO()
        with zipfile.ZipFile(tampon, "w", zipfile.ZIP_DEFLATED) as z:
            for ad in self._adlar:
                veri = govde if ad == BELGE_PARCASI else self._parcalar[ad]
                bilgi = zipfile.ZipInfo(ad, date_time=(1980, 1, 1, 0, 0, 0))
                bilgi.compress_type = zipfile.ZIP_DEFLATED
                # Dis dosya ozniteliklerini koru: bazi uretici programlar
                # arsivde dizin girdisi de tasiyor.
                eski = self._bilgiler.get(ad)
                if eski is not None:
                    bilgi.external_attr = eski.external_attr
                    bilgi.date_time = eski.date_time
                z.writestr(bilgi, veri)
        return tampon.getvalue()
