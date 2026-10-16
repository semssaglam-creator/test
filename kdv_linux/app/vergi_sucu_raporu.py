"""Vergi Suclari Raporu (VSR).

Sahte belgeyi BILEREK kullanmak ve defter-belgeleri incelemeye IBRAZ ETMEMEK,
213 sayili VUK'un 359. maddesinde kacakcilik sucu olarak tanimlanmistir. Bu
fiiller tespit edildiginde, tarhiyat oneren vergi inceleme raporundan AYRI
olarak bir vergi suclari raporu duzenlenir ve VUK 367 geregince Rapor
Degerlendirme Komisyonunun mutalaasiyla keyfiyet Cumhuriyet Bassavciligina
bildirilir.

Yapisi ornek rapordan cikarilmistir:

  I-   GIRIS                 (mukellef, gorevlendirme, hangi VIR tanzim edildi)
  II-  YAPILAN TESPITLER     (satici bazinda VTR alintilari, defter/beyan hali)
  III- SUCUN UNSURLARI       (3.1 kanuni, 3.2 maddi, 3.3 manevi)
  IV-  SUCUN FAILI           (VIR'e atif + kimlik tablosu)
  V-   SONUC                 (numarali maddeler + tarhiyat onerisi tablosu)

Bu rapor TARHIYAT ONERMEZ; onerilen tarhiyat ayri bir raporda yer alir ve
burada yalnizca V. bolumdeki tabloda ANILIR. Rapor, etkin pismanlik (VUK
gecici 34) icin gereken bilgileri de o tabloyla verir.

FAIL kurumda kanuni temsilcidir, gercek kisi mukellefte mukellefin kendisi;
ayrimi `inceleme_kunyesi.suc_duyurusu_hedefi` yapar ve kimlik tablosu da ona
gore doldurulur.
"""
from . import faturalar as F
from . import inceleme_kunyesi as ik
from . import turkce
from .belge_docx import TABLO_PUNTOSU, YER_TUTUCU_RENGI as KIRMIZI, Belge
from .tutanak import _alinti_govdesi, dolu_donemler

_tl = turkce.tl

# Fiil turleri. Her biri 359'un farkli bir bendine dayanir ve raporun
# cumlelerini degistirir.
FIIL_SAHTE_BELGE = "sahte_belge"      # 359/b - sahte belgeyi bilerek kullanma
FIIL_IBRAZ_ETMEME = "ibraz_etmeme"    # 359/a-2 - defter, kayit ve belgeleri
                                      # gizlemek

_FIIL_ADI = {
    FIIL_SAHTE_BELGE: "sahte belge kullanma",
    # Mufettisin ornek ibraz etmeme raporundan (2026-10-16): fiil 359/a-2'de
    # "defter, kayit ve belgeleri gizlemek" olarak aniliyor.
    FIIL_IBRAZ_ETMEME: "defter, kayıt ve belgeleri gizlemek",
}
_FIIL_BENDI = {FIIL_SAHTE_BELGE: "b", FIIL_IBRAZ_ETMEME: "a-2"}


def _donem_ifadesi(kunye, donemler, hal="yalin"):
    yillar = sorted({d["yil"] for d in donemler})
    if not yillar:
        return "[dönem]"
    return "%s %s" % (turkce.liste([str(y) for y in yillar]),
                      ik.donem_adi(kunye, len(yillar) > 1, hal))


def _vir_kayitlari(kunye, donemler):
    """Atif yapilacak tarhiyat raporlari; incelenen her yil icin bir kayit."""
    return ik.vir_kayitlari(kunye, sorted({d["yil"] for d in donemler}) or None)


def _vir_ifadesi(kayitlar):
    """"20.10.2025 tarih ve 2025-[2013]/72 sayılı Vergi İnceleme Raporu"

    Tarhiyat raporu YIL YIL duzenlendigi icin birden cok yilda birden cok
    rapora atif yapilir ve ifade cogullasir: "... sayılı ve ... sayılı Vergi
    İnceleme Raporları". Tarih ya da sayi girilmemisse kirmizi yer tutucu
    kalir ki doldurulmasi gerektigi belgede gorunsun.
    """
    kayitlar = kayitlar or [{}]
    parcalar = ["%s tarih ve %s sayılı"
                % (k.get("tarih") or "[rapor tarihi]",
                   k.get("sayi") or "[rapor sayısı]")
                for k in kayitlar]
    # Parcalarin kendisi "ve" iceriyor ("tarih ve sayılı"); araya bir "ve"
    # daha koymak "...sayılı ve 25.10.2025 tarih ve..." gibi okunamaz bir
    # zincir uretiyordu. Resmi uslupta raporlar virgulle siralanir.
    return "%s Vergi İnceleme Rapor%s" % (", ".join(parcalar),
                                          "ları" if len(parcalar) > 1 else "u")


def _vir_de(kayitlar):
    """"...Vergi İnceleme Raporunda" / "...Raporlarında" - bulunma hali.

    Iki halde de ek "nda": "Raporu" ve "Raporları" tamlama eki (-u / -ı) ile
    bittiginden araya kaynastirma "n"si girer. Eki elle eklemek "Raporu'da"
    gibi bozuk bicimler uretiyordu.
    """
    return _vir_ifadesi(kayitlar) + "nda"


def _cogul_mu(kayitlar):
    """Atif yapilan rapor birden cok mu; cumlelerin sayi uyumu buna bagli."""
    return len(kayitlar or []) > 1


def _rapor_sozu(kayitlar, buyuk=False):
    """"söz konusu raporda" / "söz konusu raporlarda" - bulunma hali."""
    govde = "Söz konusu" if buyuk else "söz konusu"
    return "%s rapor%s" % (govde, "larda" if _cogul_mu(kayitlar) else "da")


# ------------------------------------------------------------------ 1) giris
def _giris(b, inceleme, kunye, donemler, fiil, virler):
    M = ik.mukellef_sozu
    b.baslik("I- GİRİŞ", duzey=1)

    konular = ik.satirlar(kunye, "faaliyet_konulari")
    b.paragraf(
        "%s %s mükellefi %s, %s adresinde %s faaliyetleri ile iştigal "
        "etmektedir.%s"
        % (ik.vergi_dairesi(inceleme.get("vergi_dairesi"), ek="in"),
           ik.mukellef_kimligi(inceleme, kunye),
           ik.mukellef_adi(inceleme, kunye),
           ik.adres(kunye.get("faaliyet_adresi") or inceleme.get("adres")),
           turkce.liste(konular) if konular else "[faaliyet konusu]",
           " Mükellef Vergi Usul Kanununun 107/A maddesi kapsamında "
           "e-tebligata tabidir."
           if ik.secim_mi(kunye, "e_tebligat", "Kapsamda") else ""),
        girinti=1)

    emirler = ik.is_emirleri(kunye)
    b.paragraf(
        "T.C. Hazine ve Maliye Bakanlığı Vergi Denetim Kurulu %s %s ile %s "
        "işlemlerinin “%s” gerekçesiyle sınırlı olarak incelenmesi "
        "istenmiştir."
        % (ik.deger(kunye, "grup_baskanligi", "Denetim Daire Başkanlığının"),
           ik.gorevlendirme_ifadesi(emirler),
           _donem_ifadesi(kunye, donemler),
           "Sahte Belge Kullanma" if fiil == FIIL_SAHTE_BELGE
           else "Defter ve Belge İbraz Etmeme"), girinti=1)

    if fiil == FIIL_SAHTE_BELGE:
        b.paragraf(
            # "kasitli olarak, yani bilerek ve isteyerek" uc kez ayni seyi
            # soyluyordu; mufettisin karari (2026-10-14): "bilerek" yeter.
            "%s yasal defter ve belgeleri üzerinden yapılan inceleme "
            "neticesinde Müfettişliğimizce %s tanzim edilmiştir. %s, %s işbu "
            "raporun II nci bölümünde unvanları belirtilen mükellefler "
            "tarafından sahte veya muhteviyatı itibarıyla yanıltıcı belge "
            "olarak düzenlenen faturaları bilerek kullandığı tespit "
            "edilmiştir."
            % (_donem_ifadesi(kunye, donemler), _vir_ifadesi(virler),
               _rapor_sozu(virler, buyuk=True), M(kunye, ek="in")), girinti=1)
    else:
        b.paragraf(
            "%s yasal defter ve belgelerinin incelemeye ibraz edilmesi "
            "istenilmiş, ancak %s söz konusu defter ve belgeleri incelemeye "
            "ibraz etmediği tespit edilmiş ve Müfettişliğimizce %s tanzim "
            "edilmiştir."
            % (_donem_ifadesi(kunye, donemler), M(kunye, ek="in"),
               _vir_ifadesi(virler)), girinti=1)


# -------------------------------------------------------------- 2) tespitler
def _tespitler(b, kunye, donemler, satici_satirlari, fiil, kabul=None):
    M = ik.mukellef_sozu
    b.baslik("II- YAPILAN TESPİTLER", duzey=1)

    if fiil == FIIL_SAHTE_BELGE:
        for s in satici_satirlari:
            ham = " ".join(x.strip() for x in str(s.get("not") or "").split("\n")
                           if x.strip())
            govde = _alinti_govdesi(ham)
            tespit = ("“%s”" % govde) if govde else "[satıcı hakkındaki tespit]"
            b.paragraf(
                "Yapılan tespitler doğrultusunda; %s kullanmış olduğu "
                "faturaları düzenleyen mükellef %s hakkında %s tarih ve %s "
                "sayılı Vergi Tekniği Raporu düzenlendiği, ayrıca ilgili "
                "raporun sonuç kısmında; %s hususu belirtilmiştir."
                % (M(kunye, ek="in"), ik.satici_unvani(s),
                   s.get("vtr_tarihi") or "[VTR tarihi]",
                   s.get("vtr_no") or "[VTR no]", tespit), girinti=1)

        b.paragraf(
            "Bununla birlikte, %s yevmiye defteri kayıtlarında söz konusu alış "
            "faturalarının gider hesaplarına kaydedildiği tespit edilmiştir."
            % M(kunye, ek="in"), girinti=1)
        b.paragraf(
            "Mükellef, ilgili sahte belgelerdeki tutarları %s beyannamesi ile "
            "%s beyannamelerinde gider olarak ve katma değer vergisi "
            "beyannamesinde indirimlerine dahil etmiştir.%s"
            % (ik.gelir_vergisi_adi(kunye), ik.gecici_vergi_adi(kunye),
               # Duzeltme kabul halinde tutarlar beyandan cikarilmistir;
               # bunu yazmazsak rapor hala tarhiyat varmis gibi okunur.
               " Ancak söz konusu tutarlar, inceleme sürecinde verilen "
               "düzeltme beyannameleri ile katma değer vergisi "
               "indirimlerinden çıkarılmış olduğundan tarh edilecek bir "
               "katma değer vergisi bulunmamaktadır; suçun oluşması "
               "bakımından bu durum, fiilin işlenmiş olması gerçeğini "
               "ortadan kaldırmamaktadır." if kabul is not None else ""),
            girinti=1)
    # Ibraz etmeme icin ayri bir dal YOK: o fiil `rapor_uret`te kendi
    # bolumlerine (bkz. `_ibraz_giris`, `_ibraz_maddi_unsur`) saptigi icin
    # bu islev yalnizca sahte belge yolunda cagriliyor.

    b.paragraf(
        "İşbu rapor, %s 213 sayılı Vergi Usul Kanunu’nun 359 uncu maddesinin "
        "%s bendinde kaçakçılık suçu olarak tanımlanan %s fiilinin faili olan "
        "%s hakkında, mezkûr Kanun’un 367 nci maddesi gereğince ilgili Rapor "
        "Değerlendirme Komisyonunun mütalaasıyla keyfiyetin %s bildirilmesi "
        "için düzenlenmiş olup, yapılması gerekenlere işbu raporun ilerleyen "
        "bölümlerinde ayrıntılı olarak yer verilmiştir."
        % (_donem_ifadesi(kunye, donemler, "bulunma"), _FIIL_BENDI[fiil],
           _FIIL_ADI[fiil], ik.suc_duyurusu_hedefi(kunye),
           _savcilik(kunye, "yonelme")), girinti=1)


def _savcilik(kunye, hal="yalin"):
    """"Adana Cumhuriyet Başsavcılığına" gibi."""
    ad = str(kunye.get("vsr_savcilik") or "").strip()
    if not ad:
        return "[yetkili Cumhuriyet Başsavcılığına]"
    if not turkce.kucuk(ad).endswith("başsavcılığı"):
        ad = "%s Cumhuriyet Başsavcılığı" % ad
    if hal == "ilgi":
        return turkce.ilgi_kurum(ad)
    if hal == "yonelme":
        # Kurum adina gelen ek kesme isaretiyle ayrilmaz; "...Başsavcılığına".
        return ad + ("na" if turkce.kucuk(ad).endswith(("ı", "i", "u", "ü",
                                                        "a", "e", "o", "ö"))
                     else "a")
    return ad


# ---------------------------------------------------------- 3) sucun unsurlari
# --------------------------------------------- ibraz etmeme VSR'sine ozgu
# Bu bolumler mufettisin verdigi ibraz etmeme VSR ornegine gore yazildi
# (2026-10-16). Yapi sahte belge VSR'sinden farklidir: tespitler bolumu ve
# tarhiyat onerisi tablosu yok, numaralar 1-2-3-4.
def _ibraz_giris(b, inceleme, kunye, donemler, virler):
    M = ik.mukellef_sozu
    b.baslik("1- GİRİŞ", duzey=1)

    gecmis = ik.satirlar(kunye, "mukellef_gecmisi")
    if gecmis:
        b.paragraf(
            "%s %s mükellefi %s (raporun ilerleyen kısımlarında %s olarak "
            "anılacaktır), %s"
            % (ik.vergi_dairesi(inceleme.get("vergi_dairesi"), ek="in"),
               ik.mukellef_kimligi(inceleme, kunye),
               ik.mukellef_adi(inceleme, kunye), M(kunye), gecmis[0]),
            girinti=1)
        for satir in gecmis[1:]:
            b.paragraf(satir, girinti=1)
    else:
        konular = ik.satirlar(kunye, "faaliyet_konulari")
        b.paragraf(
            "%s %s mükellefi %s (raporun ilerleyen kısımlarında %s olarak "
            "anılacaktır), %s adresinde %s faaliyeti ile iştigal etmektedir.%s"
            % (ik.vergi_dairesi(inceleme.get("vergi_dairesi"), ek="in"),
               ik.mukellef_kimligi(inceleme, kunye),
               ik.mukellef_adi(inceleme, kunye), M(kunye),
               ik.adres(kunye.get("faaliyet_adresi") or inceleme.get("adres")),
               turkce.liste(konular) if konular else "[faaliyet konusu]",
               " Mükellef Vergi Usul Kanununun 107/A maddesi kapsamında "
               "e-tebligata tabidir."
               if ik.secim_mi(kunye, "e_tebligat", "Kapsamda") else ""),
            girinti=1)

    emirler = ik.is_emirleri(kunye)
    b.paragraf(
        "T.C. Hazine ve Maliye Bakanlığı Vergi Denetim Kurulu %s %s ile %s "
        "%s hesap ve işlemlerinin incelenmesi istenmiştir."
        % (ik.deger(kunye, "grup_baskanligi", "Denetim Daire Başkanlığının"),
           ik.gorevlendirme_ifadesi(emirler), M(kunye, ek="in"),
           _donem_ifadesi(kunye, donemler)), girinti=1)

    _ibraz_yazisi_paragrafi(b, kunye, donemler)

    b.paragraf(
        "Raporun izleyen bölümlerinde açıklanacağı üzere, %s ilgili dönem "
        "defter ve belgelerini incelenmek üzere tarafımıza ibraz etmemiş ve "
        "tarafımızca %s hakkında %s ile ilgili olarak %s düzenlenmiştir."
        % (M(kunye), M(kunye), _donem_ifadesi(kunye, donemler),
           _vir_ifadesi(virler)), girinti=1)
    b.paragraf(
        "%s hakkında defter ve belge ibraz etmeme fiiline istinaden bu Vergi "
        "Suçları Raporu düzenlenmiş olup, konuyla ilgili eleştirilen "
        "hususlara raporun izleyen bölümlerinde yer verilmiştir."
        % M(kunye, buyuk=True), girinti=1)


def _ibraz_yazisi_paragrafi(b, kunye, donemler):
    """Defter-belge isteme yazisinin teblig edildigi ve surenin gectigi.

    Sucun hem maddi hem manevi unsuru buna dayaniyor: yazi teblig edilmis,
    sonuclari bildirilmis, sure gecmis ve defterler yine ibraz edilmemis.
    Tarih girilmemisse uydurulmaz, kirmizi yer tutucu kalir.
    """
    eksik = not (str(kunye.get("ibraz_yazi_tarihi") or "").strip()
                 and str(kunye.get("ibraz_teblig_tarihi") or "").strip())
    b.paragraf(
        "Müfettişliğimizce düzenlenen %s tarih ve %s sayılı Defter ve Belge "
        "İsteme yazısı %s tebliğ edilmiştir. Defter ve belge isteme yazısında "
        "tayin olunan yasal süre geçmiş olmasına rağmen, %s %s yasal defter "
        "ve belgeleri rapor tarihi itibarıyla Müfettişliğimize ibraz "
        "edilmemiştir."
        % (ik.deger(kunye, "ibraz_yazi_tarihi", "yazı tarihi"),
           ik.deger(kunye, "ibraz_yazi_sayisi", "yazı sayısı"),
           ik.deger(kunye, "ibraz_teblig_tarihi", "tebliğ tarihi") + " tarihinde",
           ik.mukellef_sozu(kunye, ek="in"),
           _donem_ifadesi(kunye, donemler)),
        girinti=1, renk=KIRMIZI if eksik else None)


def _ibraz_maddi_unsur(b, kunye, donemler, virler):
    """Gizleme fiilinin maddi unsuru.

    Dayanak zinciri: defterleri bes yil saklama ve istenince ibraz etme
    odevi -> varligi tasdik kayitlariyla SABIT olan defterlerin ibraz
    edilmemesi 359'un uygulanmasinda GIZLEME sayilir. Tasdik tablosu bu
    yuzden rapora giriyor; defterlerin varligini o tablo ortaya koyuyor.
    """
    M = ik.mukellef_sozu
    b.paragraf(
        "Bilindiği gibi vergi uygulamalarında mükelleflerin tuttukları "
        "defterleri, ilgili bulundukları yılı takip eden takvim yılından "
        "başlayarak beş yıl süreyle muhafaza etme ve bu süre içinde talep "
        "edilmesi hâlinde ilgili makam ve memurlara arz etme zorunlulukları "
        "bulunmaktadır. Bu çerçevede 213 sayılı Vergi Usul Kanunu’nun 359 "
        "uncu maddesine göre, varlığı noter tasdik kayıtları veya sair "
        "suretlerle sabit olduğu hâlde inceleme sırasında vergi incelemesine "
        "yetkili kimselere defter ve belgelerin ibraz edilmemesi, Kanun’un "
        "uygulanmasında gizleme olarak kabul edilir.", girinti=1)
    if ik.kurum_mu(kunye):
        # Kurumda odev kanuni temsilciye dusuyor; failin o olmasinin
        # dayanagi VUK 10.
        b.paragraf(
            "213 sayılı Vergi Usul Kanunu’nun 10 uncu maddesi kanuni "
            "temsilcilerin ödevini düzenlemektedir. Buna göre tüzel "
            "kişilerin mükellef veya vergi sorumlusu olmaları hâlinde "
            "bunlara düşen ödevler kanuni temsilcileri tarafından yerine "
            "getirilir.", girinti=1)

    _ibraz_yazisi_paragrafi(b, kunye, donemler)
    b.paragraf(
        "Defter ve belge ibraz etmemek suretiyle 213 sayılı Vergi Usul "
        "Kanunu’nun 359/a-2 maddesinde yer alan kaçakçılık fiili işlenmiş "
        "olmaktadır.", girinti=1)
    _defter_tasdik_tablosu(b, kunye, donemler)


def _defter_tasdik_tablosu(b, kunye, donemler):
    """Ibraz edilmeyen defterlerin tasdik bilgileri.

    Kunyedeki "İbraz edilen defterler" alani kullanilir; ibraz etmeme
    halinde o alana TASDIK kayitlarindan okunan defterler yazilir, cunku
    raporun dayanagi defterlerin VAR oldugu ama ibraz edilmedigidir.
    """
    tutucular = ("yıl", "defterin türü", "tasdik tarihi ve numarası",
                 "tasdik makamı")
    satirlar = ik.cizgili_satirlar(kunye, "defter_bilgileri", 4, tutucular)
    if not satirlar:
        yillar = sorted({d["yil"] for d in donemler}) or [None]
        satirlar = [[str(y) if y else "[yıl]"]
                    + ["[%s]" % ad for ad in tutucular[1:]] for y in yillar]
    b.paragraf(
        "GİB Yönetim Bilgi Sistemleri veri bankası üzerinden yapılan "
        "sorgulamalar sonucunda %s %s ilişkin notere tasdik ettirilmiş "
        "defter bilgilerinin aşağıdaki gibi olduğu tespit edilmiştir."
        % (ik.mukellef_sozu(kunye, ek="in"),
           _donem_ifadesi(kunye, donemler, "yonelme")), girinti=1)
    b.paragraf("İbraz Edilmeyen Defter Tasdik Bilgileri", kalin=True,
               hiza="sol", aralik_once=120, aralik_sonra=40)
    b.tablo(["Yılı", "Defterin Türü", "Tasdik Tarihi ve Numarası",
             "Tasdik Makamı"], satirlar,
            hizalar=["orta", "sol", "orta", "sol"],
            oranlar=[0.6, 1.4, 1.4, 1.6], buyukluk=TABLO_PUNTOSU)


def _ibraz_sonuc(b, inceleme, kunye, donemler):
    """4- SONUC. Tarhiyat onerisi YOK; o, ibraz etmeme raporunun isi.

    Bu rapor yalnizca suc duyurusunu ister.
    """
    b.baslik("4- SONUÇ", duzey=1)
    b.paragraf(
        "%s %s mükellefi %s, %s hesap ve işlemlerinin kaçakçılık cezasını "
        "gerektiren hususlar yönünden incelenmesi neticesinde;"
        % (ik.vergi_dairesi(inceleme.get("vergi_dairesi"), ek="in"),
           ik.mukellef_kimligi(inceleme, kunye),
           ik.mukellef_adi(inceleme, kunye),
           _donem_ifadesi(kunye, donemler)), girinti=1)
    b.paragraf(
        "4.1- Defter ve belge ibraz etmeme fiili nedeniyle kaçakçılık suçu "
        "işlediği tespit edilen %s hakkında 213 sayılı Vergi Usul Kanunu’nun "
        "359/a-2 maddesi hükmüne göre yargılanması için aynı Kanun’un 367 nci "
        "maddesi gereğince Rapor Değerlendirme Komisyonunun mütalaasıyla "
        "keyfiyetin %s bildirilmesi gerektiği,"
        % (ik.suc_duyurusu_hedefi(kunye, inceleme),
           _savcilik(kunye, "yonelme")),
        kalin=True, girinti=1, aralik_sonra=100)
    b.paragraf("Sonucuna varılmıştır.", girinti=1, aralik_once=120)
    b.bos_satir()
    b.imza_bloklari([(ik.deger(kunye, "eleman_unvan", "unvan"),
                      ik.ad(kunye, "eleman_ad"))])


def _alt_on(on):
    """Alt baslik oneki: "III" -> "3", "2" -> "2"."""
    return "3" if on == "III" else on


def _unsurlar(b, kunye, donemler, oran, fiil, virler, on=None):
    M = ik.mukellef_sozu
    # Bolum numarasi fiile gore degisir: sahte belgede III (once
    # tespitler bolumu var), ibraz etmemede 2.
    on = on or "III"
    b.baslik("%s- SUÇUN UNSURLARI" % on if on == "III"
             else "%s. SUÇUN UNSURLARI" % on, duzey=1)

    # --- 3.1 kanuni unsur
    b.baslik("%s.1. Suçun Kanuni Unsuru" % _alt_on(on), duzey=2)
    b.paragraf(
        "Kanunsuz suç ve ceza olmaz. Bir fiilin suç olarak nitelendirilebilmesi "
        "için kanunda açık bir şekilde suç olduğunun belirtilmesi ve yine suç "
        "olarak belirtilen fiil için kanunda bir cezanın öngörülmesi "
        "gerekmektedir. %s fiili 213 sayılı Vergi Usul Kanununun 359 uncu "
        "maddesinin (%s) bendinde vergi kaçakçılığı suçu olarak "
        "tanımlanmıştır. Bu nedenle "
        "söz konusu incelemede, %s fiili mevcut olduğundan 213 sayılı Vergi "
        "Usul Kanununun 359 uncu maddesinde yer alan düzenleme nedeniyle suçun "
        "kanuni unsuru bulunmaktadır."
        % (_FIIL_ADI[fiil].capitalize(), _FIIL_BENDI[fiil],
           _FIIL_ADI[fiil]), girinti=1)
    b.paragraf(
        "Bilindiği üzere, 213 sayılı Vergi Usul Kanununun “Kaçakçılık Suçları "
        "ve Cezaları” başlıklı 359 uncu maddesinde;", girinti=1)
    _madde_metni(b, fiil)
    b.paragraf("hükmü yer almaktadır.", girinti=1)
    b.paragraf(
        "Yine aynı Kanunun 367 nci maddesinde; “Yaptıkları inceleme sırasında "
        "359 uncu maddede yazılı suçların işlendiğini tespit eden Vergi "
        "Müfettişleri ve Vergi Müfettiş Yardımcıları tarafından ilgili rapor "
        "değerlendirme komisyonunun mütalaasıyla doğrudan doğruya ve vergi "
        "incelemesine yetkili olan diğer memurlar tarafından ilgili rapor "
        "değerlendirme komisyonunun mütalaasıyla vergi dairesi başkanlığı veya "
        "defterdarlık tarafından keyfiyetin Cumhuriyet başsavcılığına "
        "bildirilmesi mecburidir.” hükmü yer almaktadır.", girinti=1)

    # --- 3.2 maddi unsur
    b.baslik("%s.2. Suçun Maddi Unsurları" % _alt_on(on), duzey=2)
    b.paragraf(
        "Bilindiği gibi suçun maddi unsuru, kanunda suç olarak belirtilen "
        "fiilin fail veya failleri tarafından gerçekleştirilmesidir.",
        girinti=1)
    if fiil == FIIL_SAHTE_BELGE:
        # "hakkinda" yalin ad ister: "mukellef kurum hakkinda". Buraya
        # ilgi ekli bicim ("mukellef kurumun hakkinda") yazilmaz.
        # "payinin ... hesaplandigi" - yan cumle ilgi eki ister; "payi"
        # yazmak cumleyi bozuyordu.
        pay = ("Müfettişliğimizce %s hakkında düzenlenen %s ayrıntılı "
               "açıklandığı üzere, %s kullandığı sahte faturaların toplam "
               "indirimleri içindeki payının %s "
               % (M(kunye), _vir_de(virler), M(kunye, ek="in"),
                  _oran_ifadesi(kunye, oran)))
        b.paragraf(
            pay + "%s sahte belge niteliğinde olduğu tespit "
            "edilen faturalardaki mal ve hizmeti gerçekten aldığı, ancak "
            "alınan mal ve hizmetin belgelendirilmesinin sahte belgelerle "
            "temin edildiği kanaati hasıl olduğundan, vergi ziyaına sebebiyet "
            "vermek amacıyla söz konusu sahte faturaları bilerek kullandığı "
            "kanaati oluşmuştur. Bu durum ilgili dönemlerde vergi ziyaına "
            "sebebiyet vermiş ve suçun maddi unsuru oluşmuştur."
            % _rapor_sozu(virler, buyuk=True), girinti=1)
    else:
        _ibraz_maddi_unsur(b, kunye, donemler, virler)

    # --- 3.3 manevi unsur
    b.baslik("%s.3. Suçun Manevi Unsurları" % _alt_on(on), duzey=2)
    b.paragraf(
        "213 sayılı Vergi Usul Kanunu’nun cezaları düzenleyen 331 inci "
        "maddesinde; “Vergi kanunları hükümlerine aykırı hareket edenler, bu "
        "kitapta yazılı vergi cezaları (vergi ziyaı cezası ve usulsüzlük "
        "cezaları) ve diğer cezalar ile cezalandırılırlar.” hükmü yer "
        "almaktadır.", girinti=1)
    b.paragraf(
        "5237 sayılı Türk Ceza Kanunu’nun “Özel Kanunlarla İlişki” başlıklı "
        "5 inci maddesinde “Bu Kanunun genel hükümleri, özel ceza kanunları ve "
        "ceza içeren kanunlardaki suçlar hakkında da uygulanır.” hükmü yer "
        "almakta olup, mezkûr Kanun’un 21 inci maddesinin birinci fıkrası, "
        "“Suçun oluşması kastın varlığına bağlıdır. Kast, suçun kanuni "
        "tanımındaki unsurların bilerek ve istenerek gerçekleştirilmesidir.” "
        "hükmüne yer vermektedir.", girinti=1)
    b.paragraf(
        "Yukarıda da açıklandığı üzere, suçun oluşması için kastın varlığı "
        "gerekli olup, Müfettişliğimizce tanzim edilen %s %s ayrıntılı olarak "
        "açıklanmıştır. Dolayısıyla kastın varlığı açık olup, %s fiili suçun "
        "manevi unsurunu oluşturmuştur."
        % (_vir_de(virler),
           "%s bilerek sahte belge kullandığı" % M(kunye, ek="in")
           if fiil == FIIL_SAHTE_BELGE
           else "%s defter ve belgeleri gizlediği" % M(kunye, ek="in"),
           _FIIL_ADI[fiil]), girinti=1)


def _oran_ifadesi(kunye, oranlar):
    """3.2'deki oran ibaresi. Oran YIL YIL yazilir.

    Mufettisin karari (2026-10-14): tek bir birlesik yuzde, bir yilin agir
    digerinin hafif oldugu dosyalarda ikisini de yanlis temsil ediyordu.

    "gibi yuksek bir orana tekabul ettigi" ibaresi yalnizca BUTUN yillar
    esigin ustundeyse yazilir; %1'lik bir payi "yuksek" diye nitelemek
    raporu itiraz edilebilir hale getirir. Esik yalnizca CUMLENIN kurulusunu
    belirler, bilerek kullanma kanaatini belirlemez - kanaat satici bazinda
    mufettis tarafindan verilmistir.
    """
    # Butun bicimler "...hesaplandigi / tekabul ettigi gorulmektedir" diye
    # bitiyor; cumlenin basindaki "payinin" ilgi eki hepsinde tutuyor.
    olculenler = [o for o in (oranlar or []) if o.get("oran") is not None]
    if not olculenler:
        return "[oran] olarak hesaplandığı görülmektedir."

    yuksek = all(o["oran"] >= 25.0 for o in olculenler)
    if len(olculenler) == 1:
        govde = "%%%s" % _tl(olculenler[0]["oran"])
    else:
        # "2020 hesap doneminde %12,34" parcalari; sonuncusu "ve" ile baglanir.
        parcalar = ["%s %s %%%s"
                    % (o["yil"], ik.donem_adi(kunye, False, "bulunma"),
                       _tl(o["oran"]))
                    for o in olculenler]
        govde = turkce.liste(parcalar)
    return govde + (" gibi yüksek oranlara tekabül ettiği görülmektedir."
                    if yuksek and len(olculenler) > 1 else
                    " gibi yüksek bir orana tekabül ettiği görülmektedir."
                    if yuksek else " olarak hesaplandığı görülmektedir.")


def _madde_metni(b, fiil):
    """359'un ilgili bendinin metni, tirnak icinde."""
    if fiil == FIIL_SAHTE_BELGE:
        b.paragraf(
            "“b) Vergi kanunları uyarınca tutulan veya düzenlenen ve saklama "
            "ve ibraz mecburiyeti bulunan defter, kayıt ve belgeleri yok "
            "edenler veya defter sahifelerini yok ederek yerine başka "
            "yapraklar koyanlar veya hiç yaprak koymayanlar veya belgelerin "
            "asıl veya suretlerini tamamen veya kısmen sahte olarak "
            "düzenleyenler veya bu belgeleri kullananlar, üç yıldan beş yıla "
            "kadar hapis cezası ile cezalandırılır. Gerçek bir muamele veya "
            "durum olmadığı halde bunlar varmış gibi düzenlenen belge, sahte "
            "belgedir.", girinti=1)
        b.paragraf(
            "Kaçakçılık suçlarını işleyenler hakkında bu maddede yazılı "
            "cezaların uygulanması 344 üncü maddede yazılı vergi ziyaı "
            "cezasının ayrıca uygulanmasına engel teşkil etmez.”", girinti=1)
    else:
        # 359/a-2 metni, mufettisin verdigi ornek VSR'den BIREBIR alindi
        # (2026-10-16). Daha once kirmizi yer tutucuydu; uydurulmamisti.
        #
        # Dikkat: ornek 2022 tarihli bir rapor ve hapis suresini "on sekiz
        # aydan uc yila" diye aniyor (5904 sayili Kanunla gelen metin).
        # 7394 sayili Kanun bu sureyi degistirdi; mufettis, inceleme yilinda
        # yururlukte olan metni taslak uzerinde denetler.
        b.paragraf(
            "“a) Vergi kanunlarına göre tutulan veya düzenlenen ve saklanma "
            "ve ibraz mecburiyeti bulunan;", girinti=1)
        b.paragraf(
            "1) Defter ve kayıtlarda hesap ve muhasebe hileleri yapanlar, "
            "gerçek olmayan veya kayda konu işlemlerle ilgisi bulunmayan "
            "kişiler adına hesap açanlar veya defterlere kaydı gereken hesap "
            "ve işlemleri vergi matrahının azalması sonucunu doğuracak şekilde "
            "tamamen veya kısmen başka defter, belge veya diğer kayıt "
            "ortamlarına kaydedenler,", girinti=1)
        b.paragraf(
            "2) Defter, kayıt ve belgeleri tahrif edenler veya gizleyenler "
            "veya muhteviyatı itibariyle yanıltıcı belge düzenleyenler veya bu "
            "belgeleri kullananlar,", girinti=1)
        b.paragraf(
            "hakkında on sekiz aydan üç yıla kadar hapis cezasına hükmolunur. "
            "Varlığı noter tasdik kayıtları veya sair suretlerle sabit olduğu "
            "halde, inceleme sırasında vergi incelemesine yetkili kimselere "
            "defter ve belgelerin ibraz edilmemesi, bu fıkra hükmünün "
            "uygulanmasında gizleme olarak kabul edilir. Gerçek bir muamele "
            "veya duruma dayanmakla birlikte bu muamele veya durumu mahiyet "
            "veya miktar itibariyle gerçeğe aykırı şekilde yansıtan belge ise, "
            "muhteviyatı itibariyle yanıltıcı belgedir.”", girinti=1)


# ------------------------------------------------------------- 4) sucun faili
def _fail(b, kunye, inceleme, fiil, virler, on=None):
    M = ik.mukellef_sozu
    kurum = ik.kurum_mu(kunye)
    b.baslik("IV- SUÇUN FAİLİ" if not on else "%s. SUÇUN FAİLİ" % on,
             duzey=1)
    b.paragraf(
        "%s, %s %s fiilini bilerek ve isteyerek işlediği ayrıntılı şekilde "
        "açıklanmıştır." % (_vir_de(virler), M(kunye, ek="in"),
                            _FIIL_ADI[fiil]), girinti=1)
    b.paragraf(
        # Kurumda hapis cezasi tuzel kisiye degil kanuni temsilciye
        # uygulanir; "mukellef hakkinda" yazmak faili yanlis gosterir.
        "Dolayısıyla %s hakkında 213 sayılı Vergi Usul Kanunu’nun 359/%s "
        "maddesi kapsamındaki, %s fiilinin yaptırımı olan cezanın uygulanması "
        "gerekmektedir. Belirtilen cezanın uygulanması için mezkûr Kanunun 367 "
        "nci maddesi uyarınca yetkili %s suç duyurusunda bulunulması "
        "gerekmektedir."
        % ("kanuni temsilci" if kurum else "mükellef", _FIIL_BENDI[fiil],
           _FIIL_ADI[fiil], _savcilik(kunye, "yonelme")),
        girinti=1)

    b.paragraf(
        "%s açık kimlik bilgileri ve adres bilgileri aşağıdaki tabloda "
        "görüldüğü gibidir."
        % ("Kanuni temsilcinin" if kurum else "Mükellefin"), girinti=1)
    ad = (ik.ad(kunye, "kanuni_temsilci", "kanuni temsilci") if kurum
          else ik.mukellef_adi(inceleme, kunye))
    tckn = (ik.deger(kunye, "temsilci_tckn", "T.C. kimlik no") if kurum
            else (str(kunye.get("mukellef_tckn") or "").strip()
                  or str(inceleme.get("vkn_tckn") or "").strip()
                  or "[T.C. kimlik no]"))
    b.tablo(["Bilgi", "Değer"],
            [["Adı Soyadı", ad],
             ["T.C. Kimlik No", tckn],
             ["Baba - Anne Adı", ik.deger(kunye, "fail_baba_anne", "baba - anne adı")],
             ["Doğum Yeri", ik.deger(kunye, "fail_dogum_yeri", "doğum yeri")],
             ["Doğum Tarihi", ik.deger(kunye, "fail_dogum_tarihi", "doğum tarihi")],
             ["Adresi", ik.adres(kunye.get("fail_adresi")
                                 or kunye.get("faaliyet_adresi")
                                 or inceleme.get("adres"))]],
            hizalar=["sol", "sol"], oranlar=[1, 2.2],
            buyukluk=TABLO_PUNTOSU)


# ------------------------------------------------------------------ 5) sonuc
def _sonuc(b, inceleme, kunye, donemler, fiil):
    b.baslik("V- SONUÇ", duzey=1)
    b.paragraf(
        "%s %s mükellefi %s’nin %s defter ve belgelerinin %s yönünden sınırlı "
        "olarak incelenmesi neticesinde;"
        % (ik.vergi_dairesi(inceleme.get("vergi_dairesi"), ek="in"),
           ik.mukellef_kimligi(inceleme, kunye),
           ik.mukellef_adi(inceleme, kunye),
           _donem_ifadesi(kunye, donemler),
           _FIIL_ADI[fiil]), girinti=1)

    maddeler = [
        "Raporun III ve IV üncü bölümlerinde açıklandığı üzere %s %s %s "
        "suretiyle 213 sayılı Vergi Usul Kanununun 359 uncu maddesinin (%s) "
        "bendinde belirtilen kaçakçılık suçunu işlediği,"
        % (ik.suc_duyurusu_hedefi(kunye), _donem_ifadesi(kunye, donemler, "bulunma"),
           _FIIL_ADI[fiil], _FIIL_BENDI[fiil]),
        "Raporumuzun II nci bölümünde belirtildiği üzere mükellef hakkında, "
        "15.04.2022 tarih ve 31810 sayılı Resmî Gazete’de yayımlanan 7394 "
        "sayılı Kanunla 213 sayılı Vergi Usul Kanununun 359 uncu maddesi ile "
        "geçici 34 üncü maddesinde düzenlenen “etkin pişmanlık” hükümlerinden "
        "yararlanılması için ihtiyaç duyulacak bilgilere aşağıdaki tabloda yer "
        "verildiği, yapılan inceleme sonucunda vergi dairesince tarh edilmesi "
        "gereken diğer vergi ve cezalara ilişkin ayrıntılı bilgilerin ilgili "
        "vergi dairesinden istenmesi gerektiği,",
        "%s hakkında 213 sayılı Vergi Usul Kanununun 359/%s ve 367 nci "
        "maddeleri uyarınca Rapor Değerlendirme Komisyonunun mütalaasıyla "
        "yetkili %s suç duyurusunda bulunulması gerektiği,"
        % (ik.suc_duyurusu_hedefi(kunye), _FIIL_BENDI[fiil],
           _savcilik(kunye, "yonelme")),
    ]
    b.madde_listesi(maddeler, numarali=True)
    b.paragraf("kanaat ve sonucuna varılmıştır.", girinti=1)


def _tarhiyat_tablosu(b, inceleme, kunye, donemler, virler,
                      liste, saticilar, kabul=None):
    """Etkin pismanlik icin gereken bilgiler: tarhiyat oneren raporlarin kunyesi.

    Bu rapor tarhiyat ONERMEZ; tablo, tarhiyati oneren AYRI raporlari ve
    onlarin tutarlarini anar.

    Tarhiyat raporu YIL YIL duzenlendigi icin tablo da yil yil satir acar:
    her satirda o yilin raporunun tarih/sayisi ile o yilin vergi ve ceza
    tutari durur. Birden cok yil varsa sonuna TOPLAM satiri eklenir.

    `kabul` verilmisse rapor bir DUZELTME KABUL raporuna eklenmistir: tutarlar
    tarhiyattan degil duzeltmeden gelir. Tarh edilen vergi yoktur (tutar
    beyandan cikarilmistir); ceza ise duzeltme uzerine o yil kesilen yarim
    katin uc kata tamamlanmis halidir.
    """
    daire = ik.vergi_dairesi(inceleme.get("vergi_dairesi"))
    satirlar = []
    vergi_top = ceza_top = 0.0
    vergi_tam = ceza_tam = True
    for kayit in virler:
        yil = int(kayit["yil"]) if str(kayit["yil"]).isdigit() else None
        vergi, ceza = _yil_tutarlari(donemler, liste, saticilar, yil, kabul)
        if vergi is None:
            vergi_tam = False
        else:
            vergi_top += vergi
        if ceza is None:
            ceza_tam = False
        else:
            ceza_top += ceza
        satirlar.append([
            kayit["tarih"] or "[rapor tarihi]",
            kayit["sayi"] or "[rapor sayısı]",
            kayit["yil"] or "[yıl]",
            "KDV",
            _tl(vergi) if vergi is not None else "[vergi tutarı]",
            _tl(ceza) if ceza is not None else "[ceza tutarı]",
            daire])
    if not satirlar:
        satirlar = [["[rapor tarihi]", "[rapor sayısı]", "[yıl]", "KDV",
                     "[vergi tutarı]", "[ceza tutarı]", daire]]
    elif len(satirlar) > 1:
        satirlar.append(["", "", "TOPLAM", "",
                         _tl(vergi_top) if vergi_tam else "[vergi tutarı]",
                         _tl(ceza_top) if ceza_tam else "[ceza tutarı]", ""])
    b.tablo(
        ["Raporun Tarihi", "Raporun Sayısı", "Dönemi", "Vergi Türü",
         "Vergi Tutarı", "Ceza Tutarı", "Vergi Dairesi"],
        satirlar,
        hizalar=["orta", "orta", "orta", "orta", "sag", "sag", "sol"],
        oranlar=[1, 1.2, 0.7, 0.8, 1.1, 1.1, 1.6],
        buyukluk=TABLO_PUNTOSU)


def _yil_tutarlari(donemler, liste, saticilar, yil, kabul=None):
    """Bir yilin onerilen vergisi ve vergi ziyai cezasi.

    Doner: (vergi, ceza). Hesaplanamayan deger None doner ve tabloda kirmizi
    yer tutucu olur; sifir donmesi bundan farklidir ve "tutar yok" demektir.
    """
    from .sahte_belge_raporu import _fatura_yili
    from .tutanak import tarhiyat_toplami

    if kabul is not None:
        # Duzeltme kabul halinde tarh edilecek vergi yoktur; ceza, duzeltme
        # uzerine O YIL kesilen yarim katin uc kata tamamlanmis halidir.
        yil_ziyasi = kabul.get("yil_ziyasi")
        if yil_ziyasi is None:
            return 0.0, None            # beyannameler yuklenmemis
        ziya = yil_ziyasi.get(yil, 0.0)
        return 0.0, round(ziya * 3, 2)

    yil_donemleri = [d for d in donemler if yil is None or d["yil"] == yil]
    # tarhiyat_toplami, farki olan DONEMLERIN listesini bekler; genel toplam
    # farki sifir olanlari da icerdiginden burada kullanilmaz.
    tarhiyatli = [d for d in yil_donemleri
                  if abs(float((d.get("tarhiyat") or {}).get("toplam_fark")
                               or 0.0)) > 0.005]
    toplam = tarhiyat_toplami(tarhiyatli) if tarhiyatli else {}
    # Onerilen vergi: re'sen tarhi gereken + haksiz iade nedeniyle aranmasi
    # gereken. Sahte belge raporunun sonuc bolumu de bu ikisini topluyor.
    vergi = (toplam.get("resen_tarhi_gereken", 0.0)
             + toplam.get("aranmasi_gereken", 0.0)) if toplam else 0.0

    # Ceza, sahte belge raporuyla AYNI ureteceten gelsin ki iki belgedeki
    # rakam birbirini tutsun; girdiler o yila daraltilir.
    yil_listesi = [f for f in liste
                   if yil is None or _fatura_yili(f) == yil]
    yil_sonucu = {"donemler": yil_donemleri}
    dagilim = F.ceza_dagilimi(yil_listesi, saticilar, yil_sonucu) or {}
    ceza = (dagilim.get("toplam") or {}).get("ceza_toplam")
    return vergi, ceza


# ------------------------------------------------------------------- uretim
def rapor_uret(inceleme, kunye, yillar, sonuc, calisma,
               fiil=FIIL_SAHTE_BELGE, kabul=None):
    """Vergi suclari raporu taslagini uretir ve `Belge` dondurur.

    Rapor BUTUN inceleme donemi icin TEK duzenlenir - tarhiyat raporu gibi
    yil yil degil. Yillar raporun icinde yer alir: II. bolum butun yillarin
    saticilarini sayar, V. bolumdeki tablo ise her yil icin bir satir acar.
    Mufettisin karari (2026-10-09); daha once yil yil ayri rapor
    uretiliyordu, yanlisti.

    `kabul`: rapor bir DUZELTME KABUL raporuna eklenecekse
    {"yil_ziyasi": {yil: tutar}} seklinde verilir. O halde tarhiyat yoktur ve
    tablo, duzeltme uzerine kesilen cezanin uc kata tamamlanmis halini yazar.
    `yil_ziyasi` None ise (beyannameler yuklenmemis) ceza yer tutucu kalir.
    """
    kunye = ik.normalize(kunye)
    calisma = calisma or {}
    mukellef_vkn = (calisma.get("mukellef") or {}).get("vkn_tckn")
    liste = F.normalize(calisma.get("faturalar"), mukellef_vkn)
    saticilar = calisma.get("saticilar") or {}

    # Rapor YALNIZCA bilerek kullanma tespit edilen yillara iliskindir.
    # Dort yilin ucunde bilerek, birinde bilmeden kullanma varsa o dorduncu
    # yil bu raporda hic anilmamali: ne giris/sonuc cumlelerinde, ne V.
    # bolumdeki tabloda. Bilmeden kullanmada 306 Sira No'lu Teblig geregi
    # kasit, dolayisiyla suc yoktur. (Sahada boyle cikti, 2026-10-14.)
    bilerek_yillar = F.bilerek_yillari(liste, saticilar)
    donemler = [d for d in dolu_donemler(sonuc)
                if not bilerek_yillar or d["yil"] in bilerek_yillar]
    virler = _vir_kayitlari(kunye, donemler)

    # Yalnizca BILEREK kullanilan saticilar bu rapora girer: suc duyurusu
    # onlara iliskin fiilden dogar.
    satici_satirlari = F.bilerek_kullananlar(F.satici_ozeti(liste, saticilar))
    # Oran 3.2'de KASTIN delili olarak sunuldugu icin yalnizca bilerek
    # kullanilan belgelerden kurulmali; bilmeden kullanilan tutari paya
    # katmak, kasit kurulmayan bir rakamla kasit kanitlamak olur.
    bilerek_vknler = F.bilerek_vknler(saticilar)
    # Oran YIL YIL yaziliyor; duzeltme kabul halinde faturalar tarhiyat disi
    # birakildigi icin olcut `duzeltme_kabul_orani`ne geciyor, yoksa normal
    # olcut sifir donerdi.
    oran = F.sahte_belge_orani_yillara(liste, sonuc, saticilar,
                                       bilerek_vknler, kabul is not None)

    b = Belge()
    b.paragraf("VERGİ SUÇLARI RAPORU", kalin=True, hiza="orta")
    b.bos_satir()

    if fiil == FIIL_IBRAZ_ETMEME:
        # Ibraz etmeme VSR'sinin yapisi sahte belgeden FARKLIDIR (mufettisin
        # ornek raporu, 2026-10-16): dort bolum, "yapilan tespitler" bolumu
        # ve tarhiyat onerisi tablosu YOK. Tarhiyat ve etkin pismanlik
        # bilgileri ibraz etmeme raporunda yer aliyor; burada tekrarlanmaz.
        _ibraz_giris(b, inceleme, kunye, donemler, virler)
        _unsurlar(b, kunye, donemler, oran, fiil, virler, "2")
        _fail(b, kunye, inceleme, fiil, virler, "3")
        _ibraz_sonuc(b, inceleme, kunye, donemler)
        return b

    _giris(b, inceleme, kunye, donemler, fiil, virler)
    _tespitler(b, kunye, donemler, satici_satirlari, fiil, kabul)
    _unsurlar(b, kunye, donemler, oran, fiil, virler)
    _fail(b, kunye, inceleme, fiil, virler)
    _sonuc(b, inceleme, kunye, donemler, fiil)
    _tarhiyat_tablosu(b, inceleme, kunye, donemler, virler, liste, saticilar,
                      kabul)
    return b


def gerekli_mi(calisma, fiil=FIIL_SAHTE_BELGE):
    """Bu dosyada vergi suclari raporu duzenlenmesi gerekiyor mu.

    Sahte belgede olcut, saticilardan en az birinin "Bilerek kullanma" olarak
    isaretlenmesidir. Ibraz etmemede olcut kunyedeki defter ibraz durumudur.

    Olcut dosyanin TAMAMINA bakar, yil yil degil: rapor butun inceleme
    donemi icin tek duzenlendiginden, yillardan birinde bilerek kullanma
    varsa rapor gerekir ve o yil tablodaki satirina girer.
    """
    calisma = calisma or {}
    if fiil == FIIL_IBRAZ_ETMEME:
        return str((calisma.get("kunye") or {}).get("defter_ibraz") or "") \
            == "İbraz edilmedi"
    mukellef_vkn = (calisma.get("mukellef") or {}).get("vkn_tckn")
    liste = F.normalize(calisma.get("faturalar"), mukellef_vkn)
    satirlar = F.satici_ozeti(liste, calisma.get("saticilar") or {})
    return bool(F.bilerek_kullananlar(satirlar))


def dosya_adi(inceleme):
    """Dosya adinda yil YOKTUR: rapor butun donem icin tek duzenlenir."""
    ad = "".join(c for c in (inceleme.get("ad_unvan") or "rapor")
                 if c.isalnum() or c in " -_").strip() or "rapor"
    return ("Vergi_suclari_raporu_taslagi_%s.docx" % ad).replace(" ", "_")
