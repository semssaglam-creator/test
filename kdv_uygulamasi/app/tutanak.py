"""Vergi inceleme tutanagi taslagi uretir (VUK 141).

Uretilen belge bir TASLAKTIR. Hukuki nitelendirme, ceza uygulamasi ve
degerlendirme inceleme elemanina aittir; buradaki metin yalnizca uygulamada
bulunan veriyi tutanak duzenine oturtur. Doldurulmamis kunye alanlari belgede
koseli parantez icinde birakilir ki eksik oldugu gozden kacmasin.

Girdi:
    inceleme  : mukellef kimligi (bkz. web_server._inceleme_bilgisi)
    kunye     : inceleme_kunyesi.normalize cikti
    yillar    : hesap motoruna verilen cozulmus yil kayitlari (elestiri girdisi
                buradan okunur)
    sonuc     : hesap.seri_hesapla ciktisi
    bulgular  : hesap.beyan_tutarlilik_kontrol ciktisi (istege bagli)
    duzeltme  : beyannameler.duzeltme_tablosu ciktisi (istege bagli)
"""
from datetime import datetime

from . import inceleme_kunyesi as ik
from . import turkce
from .belge_docx import TABLO_PUNTOSU, Belge
from .satirlar import AYLAR, ELESTIRI_ALANLARI

_tl = turkce.tl


def _var(deger, esik=0.005):
    return abs(float(deger or 0.0)) > esik


def _donem_adi(d):
    return "%s/%s" % (d["yil"], d["ay_adi"])


def dolu_donemler(sonuc):
    """Icinde veri bulunan donemleri secer.

    Hesap motoru bir yilin 12 ayini da uretir; hic beyan girilmemis aylar
    tutanaga girmemeli, yoksa tablo sifirlarla dolar.
    """
    dolular = []
    for d in sonuc.get("donemler") or []:
        beyan, elestirili = d["beyan"], d["elestirili"]
        anlamli = any(_var(beyan.get(a)) for a in
                      ("matrah", "toplam_kdv", "onceki_devir",
                       "bu_donem_indirim_toplam", "odenecek", "sonraki_devir"))
        if anlamli or d.get("elestiri_var") or _var(elestirili.get("odenecek")):
            dolular.append(d)
    return dolular


def _kapsam(donemler):
    """Inceleme donemini "2023/Ocak - 2023/Aralik" bicimine getirir."""
    if not donemler:
        return "[İnceleme dönemi]"
    ilk, son = donemler[0], donemler[-1]
    if ilk is son:
        return _donem_adi(ilk)
    return "%s - %s" % (_donem_adi(ilk), _donem_adi(son))


def _yillar_metni(donemler):
    """Incelenen yillari "2023 yılına" / "2022 ve 2023 yıllarına" bicimine getirir."""
    yillar = sorted({d["yil"] for d in donemler})
    if not yillar:
        return "[yıl] yılına"
    if len(yillar) == 1:
        return "%d yılına" % yillar[0]
    return "%s yıllarına" % turkce.liste(yillar)


def _bugun():
    return datetime.now().strftime("%d.%m.%Y")


# ------------------------------------------------------------------- bolumler
def _mukellef_tablosu(b, inceleme, kunye):
    b.baslik("1. Mükellefe İlişkin Bilgiler", 2)
    satirlar = [
        ["Adı / Unvanı", inceleme.get("ad_unvan") or "[Mükellef unvanı]"],
        ["Vergi Kimlik No", inceleme.get("vkn_tckn") or "[VKN]"],
        ["Vergi Dairesi", inceleme.get("vergi_dairesi") or "[Vergi dairesi]"],
        ["Adresi", inceleme.get("adres") or "[Adres]"],
        ["Faaliyet Konusu", ik.deger(kunye, "faaliyet_konusu")],
        ["NACE Kodu", ik.deger(kunye, "nace_kodu")],
        ["İşe Başlama Tarihi", ik.deger(kunye, "ise_baslama_tarihi")],
        ["Kanuni Temsilci / Ortaklar", ik.deger(kunye, "kanuni_temsilci")],
        ["e-Tebligat", ik.deger(kunye, "e_tebligat")],
        ["e-Defter / e-Fatura", ik.deger(kunye, "e_defter")],
    ]
    b.tablo(["Bilgi", "Açıklama"], satirlar, hizalar=["sol", "sol"], oranlar=[1, 2])


def _inceleme_tablosu(b, kunye, donemler):
    b.baslik("2. İncelemeye İlişkin Bilgiler", 2)
    satirlar = [
        ["Görevlendirme Yazısı", "%s tarih ve %s sayılı"
         % (ik.deger(kunye, "gorevlendirme_tarihi", "tarih"),
            ik.deger(kunye, "gorevlendirme_no", "sayı"))],
        ["İnceleme Dosya No", ik.deger(kunye, "inceleme_dosya_no")],
        ["İncelemeye Başlama Tarihi", ik.deger(kunye, "baslama_tarihi")],
        ["İnceleme Türü", ik.deger(kunye, "inceleme_turu")],
        ["İnceleme Gerekçesi", ik.deger(kunye, "inceleme_gerekce")],
        ["İnceleme Konusu", ik.deger(kunye, "inceleme_konusu")],
        ["İncelenen Dönem", _kapsam(donemler)],
        ["İncelemenin Yapıldığı Yer", ik.deger(kunye, "inceleme_yeri")],
        ["İncelemeyi Yapan", "%s, %s (Sicil: %s)"
         % (ik.deger(kunye, "eleman_ad", "ad soyad"),
            ik.deger(kunye, "eleman_unvan", "unvan"),
            ik.deger(kunye, "eleman_sicil", "sicil"))],
        ["Grup Başkanlığı", ik.deger(kunye, "grup_baskanligi")],
    ]
    b.tablo(["Bilgi", "Açıklama"], satirlar, hizalar=["sol", "sol"], oranlar=[1, 2])


def _donem_coz(metin):
    """"2024/Aralık" -> (2024, 12); cozulemezse None."""
    parcalar = str(metin or "").split("/")
    if len(parcalar) != 2:
        return None
    try:
        yil = int(parcalar[0].strip())
        return yil, AYLAR.index(parcalar[1].strip()) + 1
    except (ValueError, IndexError):
        return None


def belgeye_giren_bulgular(bulgular, donemler):
    """Tutanaga yazilabilecek tutarlilik bulgularini secer.

    Uygulamadaki denetimlerin bir kismi, incelemeye iliskin bir tespit degil,
    veri eksikliginin sonucudur: yalnizca Aralik yuklenmisse Kasim'dan gelen
    devir tutmaz ve zincir denetimi bunu bildirir. Ekranda dogru bir uyaridir,
    ama tutanakta "aritmetik denetimde su husus tespit edilmistir" diye yer
    alirsa mukellefe yoneltilmis bir elestiri gibi okunur. Bu yuzden:
      - donem boslugu bildirimleri hic alinmaz,
      - devir zinciri bulgusu, bir onceki donem de yuklenmisse alinir.
    """
    dolu = {(d["yil"], d["ay"]) for d in donemler}
    secilenler = []
    for bulgu in bulgular or []:
        if not bulgu.get("mesaj"):
            continue
        if bulgu.get("tur") == "donem_boslugu":
            continue
        if bulgu.get("tur") == "devir_zinciri":
            donem = _donem_coz(bulgu.get("donem"))
            if donem is None:
                continue
            yil, ay = donem
            onceki = (yil, ay - 1) if ay > 1 else (yil - 1, 12)
            if onceki not in dolu:
                continue
        secilenler.append(bulgu)
    return secilenler


def _usul_bolumu(b, kunye, bulgular, donemler):
    b.baslik("3. Usul Yönünden Tespitler", 2)

    tasdik = kunye.get("defter_tasdik") or ""
    if tasdik == "Usulüne uygun":
        b.paragraf("Mükellefin incelenen döneme ait yasal defterlerinin usulüne uygun "
                   "şekilde tasdik ettirildiği tespit edilmiştir.", girinti=1)
    elif tasdik:
        b.paragraf("Mükellefin incelenen döneme ait yasal defterlerinin tasdiki "
                   "yönünden \"%s\" durumu tespit edilmiştir. 213 sayılı Vergi Usul "
                   "Kanunu'nun 221. maddesi uyarınca değerlendirilmesi gerekmektedir."
                   % tasdik, girinti=1)

    ibraz = kunye.get("defter_ibraz") or ""
    if ibraz == "İbraz edildi":
        b.paragraf("Defter ve belgeler incelemeye ibraz edilmiştir.", girinti=1)
    elif ibraz:
        b.paragraf("Defter ve belgelerin ibrazı yönünden \"%s\" durumu söz konusudur."
                   % ibraz, girinti=1)

    beyan_durumu = kunye.get("beyanname_durumu") or ""
    if beyan_durumu == "Süresinde verilmiş":
        b.paragraf("İncelenen döneme ait katma değer vergisi beyannamelerinin yasal "
                   "süresi içinde verildiği görülmüştür.", girinti=1)
    elif beyan_durumu:
        b.paragraf("İncelenen döneme ait katma değer vergisi beyannamelerinin "
                   "verilmesi yönünden \"%s\" durumu tespit edilmiştir."
                   % beyan_durumu, girinti=1)

    usulsuzluk = kunye.get("usulsuzluk") or ""
    if usulsuzluk and usulsuzluk != "Yok":
        b.paragraf("Yapılan usul incelemesinde \"%s\" kapsamında değerlendirilmesi "
                   "gereken bir durum tespit edilmiştir." % usulsuzluk, girinti=1)

    for satir in ik.satirlar(kunye, "usul_notu"):
        b.paragraf(satir, girinti=1)

    # Uygulamanin kendi tutarlilik denetimleri: beyannamenin kendi rakamlari
    # icinde tutmayan noktalar. Tespitten bagimsizdir, usul basligina girer.
    uyumsuz = belgeye_giren_bulgular(bulgular, donemler)
    if uyumsuz:
        b.paragraf("Beyan edilen tutarlar üzerinde yapılan aritmetik denetimde "
                   "aşağıdaki hususlar tespit edilmiştir:", girinti=1)
        b.madde_listesi([x["mesaj"] for x in uyumsuz])


# Beyan dokum tablosunun sutunlari. Uygulamadaki duzeltme beyannameleri
# tablosuyla ayni sutunlar ve ayni kisaltmalar kullanilir; ikisi yan yana
# okundugunda karsilastirilabilsin diye.
BEYAN_DOKUM_KOLONLARI = [
    ("matrah", "KDV Matrahı"),
    ("hesaplanan", "Hspl. KDV"),
    ("onceki_devir", "Önc. Dön. Dev. KDV"),
    ("bu_donem_indirim_toplam", "Bu Dön. İndl. KDV"),
    ("indirimler", "İndirimler Toplamı"),
    ("odenecek", "Ödenecek KDV"),
    ("sonraki_devir", "Son. Dön. Dev. KDV"),
]


def beyan_dokum_tablosu(b, donemler, blok="beyan"):
    """Beyannameye iliskin dokumu yil yil tabloya doker.

    Basligin ilk hucresi "Dönemi <yil>" oldugundan her yil ayri bir tablodur;
    satirlarda yalnizca ay adi yazar. Punto kucultulur: yedi tutar sutunu 12
    puntoda sigmaz, basliklar satir ortasindan bolunur ve rakamlar alt satira
    taser.
    """
    for yil in sorted({d["yil"] for d in donemler}):
        alt = [d for d in donemler if d["yil"] == yil]
        satirlar = []
        for d in alt:
            satirlar.append([d["ay_adi"]]
                            + [_tl(d[blok].get(kod)) for kod, _e in BEYAN_DOKUM_KOLONLARI])
        satirlar.append(["Toplam:"] + [
            _tl(sum(d[blok].get(kod, 0.0) for d in alt))
            for kod, _e in BEYAN_DOKUM_KOLONLARI])
        b.tablo(["Dönemi\n%s" % yil] + [e for _k, e in BEYAN_DOKUM_KOLONLARI],
                satirlar,
                hizalar=["sol"] + ["sag"] * len(BEYAN_DOKUM_KOLONLARI),
                oranlar=[1.0] + [1.15] * len(BEYAN_DOKUM_KOLONLARI),
                buyukluk=TABLO_PUNTOSU, toplam_satiri=True)


def _beyan_dokumu(b, donemler):
    b.baslik("4. Beyan Edilen Tutarlar", 2)
    b.paragraf("İncelenen döneme ait katma değer vergisi beyannamelerinde yer alan "
               "tutarlar aşağıda gösterilmiştir.", girinti=1)
    beyan_dokum_tablosu(b, donemler)


def _duzeltme_bolumu(b, duzeltme, sira):
    """Beyanname surumleri yuklendiyse duzeltme dokumunu yazar.

    `duzeltme`, beyannameler.duzeltme_tablosu ciktisidir: yil yil ayrilmis
    ve her yilin icinde donem + onay zamani sirasina dizilmis satirlar.
    """
    if not duzeltme:
        return sira
    b.baslik("%d. Düzeltme Beyannameleri" % sira, 2)
    b.paragraf("Mükellef tarafından verilen düzeltme beyannamelerine ilişkin döküm "
               "aşağıdadır. Bir döneme ait birden çok düzeltme bulunması hâlinde "
               "her düzeltme ayrı satırda, veriliş sırasıyla gösterilmiştir.",
               girinti=1)
    for yil_blogu in duzeltme:
        tablo = []
        for s in yil_blogu["satirlar"]:
            tablo.append([
                s.get("donem") or "",
                s.get("tarih") or "",
                _tl(s.get("matrah_toplami")),
                _tl(s.get("hesaplanan_kdv")),
                _tl(s.get("odenmesi_gereken_kdv")),
                _tl(s.get("sonraki_donem_devreden")),
                s.get("gerekce") or "",
            ])
        b.paragraf("Dönemi: %s" % yil_blogu["yil"], kalin=True, hiza="sol",
                   aralik_once=120, aralik_sonra=60)
        b.tablo(["Dönemi\n%s" % yil_blogu["yil"], "Düzeltme Tarihi",
                 "KDV Matrahı", "Hspl. KDV", "Öden. KDV", "Son. Dön. Dev. KDV",
                 "Düzeltme Gerekçesi"], tablo,
                hizalar=["sol", "sol", "sag", "sag", "sag", "sag", "sol"],
                oranlar=[1, 1.1, 1.2, 1, 1, 1.2, 1.6],
                buyukluk=TABLO_PUNTOSU)
    return sira + 1


def _tespit_bolumu(b, yillar, donemler, sira):
    """Girilen elestirileri ve bunlarin tarhiyata etkisini yazar."""
    b.baslik("%d. Tespit ve Tenkit Edilen Hususlar" % sira, 2)

    tespitli = [d for d in donemler if d.get("elestiri_var")]
    if not tespitli:
        b.paragraf("İnceleme sonucunda, beyan edilen tutarların değiştirilmesini "
                   "gerektiren bir tespitte bulunulmamıştır.", girinti=1)
        return

    b.paragraf("Yapılan inceleme sonucunda aşağıdaki dönemlere ilişkin tespitlerde "
               "bulunulmuş; bu tespitler doğrultusunda beyan edilen tutarlar "
               "düzeltilmiştir.", girinti=1)

    # Elestiri girdisi ham yil kayitlarinda tutulur; dönem dönem tabloya dokulur
    elestiri_haritasi = {}
    for yil_kaydi in yillar or []:
        yil = int(yil_kaydi.get("yil"))
        elestiri = yil_kaydi.get("elestiri") or {}
        for ay in range(12):
            degerler = {kod: (elestiri.get(kod) or [0.0] * 12)[ay]
                        for kod, _e in ELESTIRI_ALANLARI}
            if any(_var(v) for v in degerler.values()):
                elestiri_haritasi[(yil, ay + 1)] = degerler

    tablo = []
    for (yil, ay), degerler in sorted(elestiri_haritasi.items()):
        tablo.append(["%s/%s" % (yil, AYLAR[ay - 1])]
                     + [_tl(degerler[kod]) if _var(degerler[kod]) else "-"
                        for kod, _e in ELESTIRI_ALANLARI])
    if tablo:
        b.tablo(["Dönem", "Matraha İlave", "Hesaplanan KDV İlave",
                 "Devirden Çıkarılan", "İndirimden Çıkarılan",
                 "Yüklenilenden Çıkarılan"], tablo,
                hizalar=["sol"] + ["sag"] * len(ELESTIRI_ALANLARI),
                oranlar=[1.1, 1, 1, 1, 1, 1], buyukluk=TABLO_PUNTOSU)


def tarhiyat_toplami(tarhiyatli):
    """Gosterilen satirlarin toplami.

    Bilerek `sonuc["tarhiyat_toplami"]` kullanilmaz: o, farkin sifir oldugu
    donemleri de icerir. Tabloya yalnizca farki olan donemler alindigindan
    genel toplam kullanilirsa TOPLAM satiri, ustundeki sutunun toplami
    olmaz ve tablo kendi icinde tutmaz.
    """
    alanlar = ("odenecek_beyan", "odenecek_olmasi_gereken", "resen_tarhi_gereken",
               "aranmasi_gereken", "haksiz_iade", "toplam_fark")
    return {a: round(sum(d["tarhiyat"].get(a, 0.0) for d in tarhiyatli), 2)
            for a in alanlar}


def _tarhiyat_bolumu(b, sonuc, donemler, kunye, sira):
    b.baslik("%d. Tarhiyat Özeti" % sira, 2)
    tarhiyatli = [d for d in donemler if _var(d["tarhiyat"]["toplam_fark"])]
    toplam = tarhiyat_toplami(tarhiyatli)

    if not tarhiyatli:
        b.paragraf("Yapılan inceleme sonucunda re'sen tarhı gereken bir vergi farkı "
                   "hesaplanmamıştır.", girinti=1)
        return

    tablo = []
    for d in tarhiyatli:
        t = d["tarhiyat"]
        tablo.append([_donem_adi(d), _tl(t["odenecek_beyan"]),
                      _tl(t["odenecek_olmasi_gereken"]), _tl(t["resen_tarhi_gereken"]),
                      _tl(t["aranmasi_gereken"]), _tl(t["toplam_fark"])])
    tablo.append(["TOPLAM", _tl(toplam.get("odenecek_beyan")),
                  _tl(toplam.get("odenecek_olmasi_gereken")),
                  _tl(toplam.get("resen_tarhi_gereken")),
                  _tl(toplam.get("aranmasi_gereken")),
                  _tl(toplam.get("toplam_fark"))])
    b.tablo(["Dönem", "Ödenecek KDV (Beyan)", "Ödenecek KDV (Olması Gereken)",
             "Re'sen Tarhı Gereken", "Aranması Gereken", "Toplam Fark"], tablo,
            hizalar=["sol"] + ["sag"] * 5, oranlar=[1.1, 1, 1.1, 1, 1, 1],
            buyukluk=TABLO_PUNTOSU, toplam_satiri=True)

    b.paragraf("Yukarıda gösterildiği üzere, incelenen dönemler itibarıyla toplam "
               "%s TL katma değer vergisinin re'sen tarh edilmesi gerektiği "
               "sonucuna varılmıştır. Bu tutar, 213 sayılı Vergi Usul Kanunu'nun "
               "%s. maddesi kapsamında değerlendirilmiştir."
               % (_tl(toplam.get("toplam_fark")), ik.resen_madde_kodu(kunye)),
               girinti=1)
    if _var(toplam.get("haksiz_iade")):
        b.paragraf("Ayrıca %s TL tutarında haksız olarak iade edilen katma değer "
                   "vergisi tespit edilmiştir."
                   % _tl(toplam.get("haksiz_iade")), girinti=1)


def _sorular_bolumu(b, kunye, sira):
    sorular = ik.satirlar(kunye, "sorular")
    if not sorular:
        return sira
    b.baslik("%d. Sorulan Hususlar ve Alınan Cevaplar" % sira, 2)
    b.madde_listesi(sorular)
    return sira + 1


def _beyan_bolumu(b, kunye, sira):
    beyan = ik.satirlar(kunye, "mukellef_beyani")
    b.baslik("%d. Nezdinde İnceleme Yapılanın Beyanı" % sira, 2)
    if beyan:
        for satir in beyan:
            b.paragraf(satir, girinti=1)
    else:
        b.paragraf("[Nezdinde inceleme yapılanın beyanı bu bölüme yazılacaktır.]",
                   girinti=1, italik=True)
    return sira + 1


def _kapanis(b, inceleme, kunye, sira):
    b.baslik("%d. Sonuç" % sira, 2)
    nusha = kunye.get("tutanak_nusha") or 2
    b.paragraf(
        "İşbu tutanak, yukarıda yer alan hususların tespiti amacıyla %s tarihinde "
        "%s adresinde %d nüsha olarak düzenlenmiş; okunmak üzere nezdinde inceleme "
        "yapılana verilmiş, tutanakta yer alan hususların okunduğu ve anlaşıldığı "
        "belirtilerek 213 sayılı Vergi Usul Kanunu'nun 141. maddesi uyarınca "
        "birlikte imza altına alınmıştır."
        % (ik.deger(kunye, "tutanak_tarihi", "tutanak tarihi"),
           ik.deger(kunye, "tutanak_yeri", "tutanak yeri"), int(nusha)),
        girinti=1)
    b.paragraf("Tutanağın bir nüshası nezdinde inceleme yapılana teslim edilmiştir.",
               girinti=1)

    hazir = ik.satirlar(kunye, "hazir_bulunanlar")
    if hazir:
        b.paragraf("Hazır bulunanlar:", kalin=True, aralik_once=120)
        b.madde_listesi(hazir, numarali=False)

    b.imza_bloklari([
        (ik.deger(kunye, "eleman_unvan", "unvan"),
         ik.deger(kunye, "eleman_ad", "ad soyad")),
        ("Nezdinde İnceleme Yapılan\n(%s)" % ik.deger(kunye, "nezdinde_sifat", "sıfat"),
         ik.deger(kunye, "nezdinde_ad", "ad soyad")),
    ])


# ---------------------------------------------------------------------- giris
def tutanak_uret(inceleme, kunye, yillar, sonuc, bulgular=None, duzeltme=None):
    """Tutanak taslagini uretir ve `Belge` nesnesi dondurur."""
    kunye = ik.normalize(kunye)
    donemler = dolu_donemler(sonuc)

    b = Belge()
    b.baslik("VERGİ İNCELEME TUTANAĞI", 1)
    b.paragraf("(Taslak — 213 sayılı VUK md. 141)", hiza="orta", italik=True,
               aralik_sonra=240)

    b.paragraf(
        "%s tarih ve %s sayılı görevlendirme yazısına istinaden, %s %s vergi "
        "kimlik numaralı mükellefi %s nezdinde, %s ait %s %s yapılmış olup, "
        "%s dönemine ilişkin olarak aşağıdaki hususlar tespit edilmiştir."
        % (ik.deger(kunye, "gorevlendirme_tarihi", "tarih"),
           ik.deger(kunye, "gorevlendirme_no", "sayı"),
           turkce.ilgi(inceleme.get("vergi_dairesi") or "[Vergi dairesi]"),
           inceleme.get("vkn_tckn") or "[VKN]",
           inceleme.get("ad_unvan") or "[Mükellef unvanı]",
           _yillar_metni(donemler),
           ik.deger(kunye, "inceleme_konusu"),
           (kunye.get("inceleme_turu") or "inceleme").lower(),
           _kapsam(donemler)),
        girinti=1)

    _mukellef_tablosu(b, inceleme, kunye)
    _inceleme_tablosu(b, kunye, donemler)
    _usul_bolumu(b, kunye, bulgular, donemler)

    if donemler:
        _beyan_dokumu(b, donemler)
        sira = 5
    else:
        b.baslik("4. Beyan Edilen Tutarlar", 2)
        b.paragraf("[Beyan verisi girilmediği için bu bölüm boş bırakılmıştır.]",
                   girinti=1, italik=True)
        sira = 5

    sira = _duzeltme_bolumu(b, duzeltme, sira)

    _tespit_bolumu(b, yillar, donemler, sira)
    sira += 1
    _tarhiyat_bolumu(b, sonuc, donemler, kunye, sira)
    sira += 1
    sira = _sorular_bolumu(b, kunye, sira)
    sira = _beyan_bolumu(b, kunye, sira)
    _kapanis(b, inceleme, kunye, sira)

    b.bos_satir()
    b.paragraf("Bu belge %s tarihinde KDV İnceleme Çalışması uygulamasıyla taslak "
               "olarak üretilmiştir; imzaya hazır nihai belge değildir."
               % _bugun(), italik=True, hiza="orta", buyukluk=9)
    return b


def dosya_adi(inceleme):
    ad = "".join(c for c in (inceleme.get("ad_unvan") or "tutanak")
                 if c.isalnum() or c in " -_").strip() or "tutanak"
    return ("Tutanak_taslagi_%s.docx" % ad).replace(" ", "_")
