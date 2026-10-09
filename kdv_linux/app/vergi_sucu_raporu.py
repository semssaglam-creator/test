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
FIIL_IBRAZ_ETMEME = "ibraz_etmeme"    # 359/a - defter ve belgeleri gizleme

_FIIL_ADI = {
    FIIL_SAHTE_BELGE: "sahte belge kullanma",
    FIIL_IBRAZ_ETMEME: "defter ve belgeleri gizleme",
}
_FIIL_BENDI = {FIIL_SAHTE_BELGE: "b", FIIL_IBRAZ_ETMEME: "a"}


def _donem_ifadesi(kunye, donemler, hal="yalin"):
    yillar = sorted({d["yil"] for d in donemler})
    if not yillar:
        return "[dönem]"
    return "%s %s" % (turkce.liste([str(y) for y in yillar]),
                      ik.donem_adi(kunye, len(yillar) > 1, hal))


def _vir_ifadesi(kunye):
    """"20.10.2025 tarih ve 2025-[2013]/72 sayılı Vergi İnceleme Raporu"

    Tarhiyat oneren rapor bu raporun her bolumunde aniliyor; tarihi ve sayisi
    girilmemisse kirmizi yer tutucu kalir ki doldurulmasi gerektigi belgede
    gorunsun.
    """
    return ("%s tarih ve %s sayılı Vergi İnceleme Raporu"
            % (ik.deger(kunye, "vir_tarihi", "rapor tarihi"),
               ik.deger(kunye, "vir_sayisi", "rapor sayısı")))


def _vir_de(kunye):
    """"...sayılı Vergi İnceleme Raporunda" - bulunma hali.

    "Raporu" diye biten ifadeye ek getirilirken araya kaynastirma "n"si
    girer; eki elle eklemek "Raporu'da" gibi bozuk bicimler uretiyordu.
    """
    return _vir_ifadesi(kunye) + "nda"


# ------------------------------------------------------------------ 1) giris
def _giris(b, inceleme, kunye, donemler, fiil):
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
            "%s yasal defter ve belgeleri üzerinden yapılan inceleme "
            "neticesinde Müfettişliğimizce %s tanzim edilmiştir. Söz konusu "
            "raporda, %s işbu raporun II nci bölümünde unvanları belirtilen "
            "mükellefler tarafından sahte veya muhteviyatı itibarıyla "
            "yanıltıcı belge olarak düzenlenen faturaları kasıtlı olarak, "
            "yani bilerek ve isteyerek kullandığı kanaatine varılmıştır."
            % (_donem_ifadesi(kunye, donemler), _vir_ifadesi(kunye),
               M(kunye, ek="in")), girinti=1)
    else:
        b.paragraf(
            "%s yasal defter ve belgelerinin incelemeye ibraz edilmesi "
            "istenilmiş, ancak %s söz konusu defter ve belgeleri incelemeye "
            "ibraz etmediği tespit edilmiş ve Müfettişliğimizce %s tanzim "
            "edilmiştir."
            % (_donem_ifadesi(kunye, donemler), M(kunye, ek="in"),
               _vir_ifadesi(kunye)), girinti=1)


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
    else:
        b.paragraf(
            "%s yasal defter ve belgelerinin ibrazı, usulüne uygun olarak "
            "tebliğ edilen yazımızla istenilmiştir. Verilen süre içinde defter "
            "ve belgeler ibraz edilmemiş; ibraz etmemeye ilişkin olarak mücbir "
            "sebep hâli de bildirilmemiştir."
            % _donem_ifadesi(kunye, donemler, "ilgi"), girinti=1)
        b.paragraf(
            "Defterlerin varlığı, %s tasdik kayıtlarıyla sabittir."
            % ik.deger(kunye, "defter_tasdik_makami", "tasdik makamı"),
            girinti=1)

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
def _unsurlar(b, kunye, donemler, oran, fiil):
    M = ik.mukellef_sozu
    b.baslik("III- SUÇUN UNSURLARI", duzey=1)

    # --- 3.1 kanuni unsur
    b.baslik("3.1. Suçun Kanuni Unsuru", duzey=2)
    b.paragraf(
        "Kanunsuz suç ve ceza olmaz. Bir fiilin suç olarak nitelendirilebilmesi "
        "için kanunda açık bir şekilde suç olduğunun belirtilmesi ve yine suç "
        "olarak belirtilen fiil için kanunda bir cezanın öngörülmesi "
        "gerekmektedir. %s fiili 213 sayılı Vergi Usul Kanununun 359 uncu "
        "maddesinde vergi kaçakçılığı suçu olarak tanımlanmıştır. Bu nedenle "
        "söz konusu incelemede, %s fiili mevcut olduğundan 213 sayılı Vergi "
        "Usul Kanununun 359 uncu maddesinde yer alan düzenleme nedeniyle suçun "
        "kanuni unsuru bulunmaktadır."
        % (_FIIL_ADI[fiil].capitalize(), _FIIL_ADI[fiil]), girinti=1)
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
    b.baslik("3.2. Suçun Maddi Unsurları", duzey=2)
    b.paragraf(
        "Bilindiği gibi suçun maddi unsuru, kanunda suç olarak belirtilen "
        "fiilin fail veya failleri tarafından gerçekleştirilmesidir.",
        girinti=1)
    if fiil == FIIL_SAHTE_BELGE:
        # "hakkinda" yalin ad ister: "mukellef kurum hakkinda". Buraya
        # ilgi ekli bicim ("mukellef kurumun hakkinda") yazilmaz.
        if oran and oran.get("oran") is not None:
            # "gibi yuksek bir orana" ibaresi yalnizca gercekten yuksek bir
            # oranda yazilir; %1'lik bir payi "yuksek" diye nitelemek raporu
            # itiraz edilebilir hale getirir. Esik yalnizca CUMLENIN
            # kuruluşunu belirler, bilerek kullanma kanaatini belirlemez -
            # kanaat satici bazinda muffettis tarafindan verilmistir.
            pay = ("Müfettişliğimizce %s hakkında düzenlenen %s ayrıntılı "
                   "açıklandığı üzere, %s kullandığı sahte faturaların toplam "
                   "indirimleri içindeki payının %%%s %s"
                   % (M(kunye), _vir_de(kunye), M(kunye, ek="in"),
                      _tl(oran["oran"]),
                      "gibi yüksek bir orana tekabül ettiği görülmektedir. "
                      if oran["oran"] >= 25.0
                      else "olarak hesaplandığı görülmektedir. "))
        else:
            pay = ("Müfettişliğimizce %s hakkında düzenlenen %s ayrıntılı "
                   "açıklandığı üzere, %s kullandığı sahte faturaların toplam "
                   "indirimleri içindeki payı [oran] olarak hesaplanmıştır. "
                   % (M(kunye), _vir_de(kunye),
                      M(kunye, ek="in")))
        b.paragraf(
            pay + "Söz konusu raporda sahte belge niteliğinde olduğu tespit "
            "edilen faturalardaki mal ve hizmeti gerçekten aldığı, ancak "
            "alınan mal ve hizmetin belgelendirilmesinin sahte belgelerle "
            "temin edildiği kanaati hasıl olduğundan, vergi ziyaına sebebiyet "
            "vermek amacıyla söz konusu sahte faturaları bilerek kullandığı "
            "kanaati oluşmuştur. Bu durum ilgili dönemlerde vergi ziyaına "
            "sebebiyet vermiş ve suçun maddi unsuru oluşmuştur.", girinti=1)
    else:
        b.paragraf(
            "Müfettişliğimizce %s hakkında düzenlenen %s ayrıntılı "
            "açıklandığı üzere; usulüne uygun olarak tebliğ edilen yazımıza "
            "rağmen defter ve belgeler incelemeye ibraz edilmemiştir. "
            "Varlığı tasdik kayıtlarıyla sabit olan defter ve belgelerin "
            "ibraz edilmemesi gizleme fiilini oluşturmuş, bu durum ilgili "
            "dönemlerde vergi ziyaına sebebiyet vermiş ve suçun maddi unsuru "
            "oluşmuştur." % (M(kunye), _vir_de(kunye)),
            girinti=1)

    # --- 3.3 manevi unsur
    b.baslik("3.3. Suçun Manevi Unsurları", duzey=2)
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
        % (_vir_de(kunye),
           "mükellefin bilerek sahte belge kullandığı"
           if fiil == FIIL_SAHTE_BELGE
           else "mükellefin defter ve belgeleri gizlediği",
           _FIIL_ADI[fiil]), girinti=1)


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
        # 359/a metni henuz dogrulanmadi; uydurulmaz, kirmizi birakilir.
        # Kullanicidan madde metni geldiginde buraya yazilacak.
        b.paragraf(
            "[213 sayılı Vergi Usul Kanununun 359 uncu maddesinin (a) bendinin "
            "defter ve belgeleri gizlemeye ilişkin hükmü buraya yazılacaktır.]",
            girinti=1, renk=KIRMIZI)


# ------------------------------------------------------------- 4) sucun faili
def _fail(b, kunye, inceleme, fiil):
    M = ik.mukellef_sozu
    kurum = ik.kurum_mu(kunye)
    b.baslik("IV- SUÇUN FAİLİ", duzey=1)
    b.paragraf(
        "%s, %s %s fiilini bilerek ve isteyerek işlediği ayrıntılı şekilde "
        "açıklanmıştır." % (_vir_de(kunye), M(kunye, ek="in"),
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


def _tarhiyat_tablosu(b, inceleme, kunye, donemler, ceza_toplami, kabul=None):
    """Etkin pismanlik icin gereken bilgiler: tarhiyat oneren raporun kunyesi.

    Bu rapor tarhiyat ONERMEZ; tablo, tarhiyati oneren AYRI raporu ve onun
    tutarlarini anar. Tutarlar hesaplanan tarhiyattan gelir.

    `kabul` verilmisse rapor bir DUZELTME KABUL raporuna eklenmistir: tutarlar
    tarhiyattan degil duzeltmeden gelir. Tarh edilen vergi yoktur (tutar
    beyandan cikarilmistir); ceza ise duzeltme uzerine kesilen yarim katin
    uc kata tamamlanmis halidir.
    """
    from .tutanak import tarhiyat_toplami

    if kabul is not None:
        ziya = kabul.get("ziya")
        vergi = 0.0
        ceza = round(ziya * 3, 2) if ziya else (0.0 if ziya == 0 else None)
        _tablo_satiri(b, inceleme, kunye, donemler, vergi, ceza)
        return

    # tarhiyat_toplami, farki olan DONEMLERIN listesini bekler; genel toplam
    # (sonuc["tarhiyat_toplami"]) farki sifir olanlari da icerdiginden burada
    # kullanilmaz.
    tarhiyatli = [d for d in donemler
                  if abs(float((d.get("tarhiyat") or {}).get("toplam_fark")
                               or 0.0)) > 0.005]
    toplam = tarhiyat_toplami(tarhiyatli) if tarhiyatli else {}
    # Onerilen vergi: re'sen tarhi gereken + haksiz iade nedeniyle aranmasi
    # gereken. Sahte belge raporunun sonuc bolumu de bu ikisini topluyor.
    vergi = (toplam.get("resen_tarhi_gereken", 0.0)
             + toplam.get("aranmasi_gereken", 0.0)) if toplam else None
    ceza = (ceza_toplami or {}).get("ceza_toplam")
    _tablo_satiri(b, inceleme, kunye, donemler, vergi, ceza)


def _tablo_satiri(b, inceleme, kunye, donemler, vergi, ceza):
    yillar = sorted({d["yil"] for d in donemler}) or [None]
    b.tablo(
        ["Raporun Tarihi", "Raporun Sayısı", "Dönemi", "Vergi Türü",
         "Vergi Tutarı", "Ceza Tutarı", "Vergi Dairesi"],
        [[ik.deger(kunye, "vir_tarihi", "rapor tarihi"),
          ik.deger(kunye, "vir_sayisi", "rapor sayısı"),
          str(yillar[0]) if yillar[0] else "[yıl]",
          "KDV",
          _tl(vergi) if vergi is not None else "[vergi tutarı]",
          _tl(ceza) if ceza is not None else "[ceza tutarı]",
          ik.vergi_dairesi(inceleme.get("vergi_dairesi"))]],
        hizalar=["orta", "orta", "orta", "orta", "sag", "sag", "sol"],
        oranlar=[1, 1.2, 0.7, 0.8, 1.1, 1.1, 1.6],
        buyukluk=TABLO_PUNTOSU)


# ------------------------------------------------------------------- uretim
def rapor_uret(inceleme, kunye, yillar, sonuc, calisma,
               fiil=FIIL_SAHTE_BELGE, yil=None, kabul=None):
    """Vergi suclari raporu taslagini uretir ve `Belge` dondurur.

    `kabul`: rapor bir DUZELTME KABUL raporuna eklenecekse {"ziya": tutar}
    seklinde verilir. O halde tarhiyat yoktur ve V. bolumdeki tablo
    duzeltme uzerine kesilen cezanin uc kata tamamlanmis halini yazar.
    """
    kunye = ik.normalize(kunye)
    calisma = calisma or {}
    mukellef_vkn = (calisma.get("mukellef") or {}).get("vkn_tckn")
    liste = F.normalize(calisma.get("faturalar"), mukellef_vkn)
    saticilar = calisma.get("saticilar") or {}

    # Rapor bir yila aitse oran ve ceza hesabi da yalnizca o yilin
    # verisinden uretilmeli; aksi halde 2022 raporunun V. bolumundeki
    # tabloda 2023 cezasi da toplanmis halde gorunur.
    if yil:
        from .sahte_belge_raporu import _fatura_yili
        sonuc = dict(sonuc)
        sonuc["donemler"] = [d for d in (sonuc.get("donemler") or [])
                             if d["yil"] == yil]
        liste = [f for f in liste if _fatura_yili(f) == yil]
    donemler = dolu_donemler(sonuc)
    # Yalnizca BILEREK kullanilan saticilar bu rapora girer: suc duyurusu
    # onlara iliskin fiilden dogar. Bilmeden kullanilan belgeler 306 Sira
    # No'lu Tebligt geregi 359 kapsaminda degerlendirilmez.
    # `liste` yukarida yila daraltildigi icin satici ozeti de kendiliginden
    # o yilin saticilarini verir; ayrica yil_dokumu suzgeci gerekmez.
    satici_satirlari = F.bilerek_kullananlar(F.satici_ozeti(liste, saticilar))
    # Duzeltme kabul halinde faturalar tarhiyat disi birakildigi icin
    # `sahte_belge_orani` sifir doner; oran, ebeveyn raporla ayni olcutten
    # (`duzeltme_kabul_orani`) alinmali ki iki belgedeki yuzde birbirini tutsun.
    oran = (F.duzeltme_kabul_orani(liste, sonuc, saticilar) if kabul is not None
            else F.sahte_belge_orani(liste, sonuc, saticilar))
    # Ceza tutari, sahte belge raporuyla AYNI ureteceten gelsin ki
    # iki belgedeki rakam birbirini tutsun.
    ceza_toplami = (F.ceza_dagilimi(liste, saticilar, sonuc)
                    or {}).get("toplam") or {}

    b = Belge()
    b.paragraf("VERGİ SUÇLARI RAPORU", kalin=True, hiza="orta")
    b.bos_satir()
    _giris(b, inceleme, kunye, donemler, fiil)
    _tespitler(b, kunye, donemler, satici_satirlari, fiil, kabul)
    _unsurlar(b, kunye, donemler, oran, fiil)
    _fail(b, kunye, inceleme, fiil)
    _sonuc(b, inceleme, kunye, donemler, fiil)
    _tarhiyat_tablosu(b, inceleme, kunye, donemler, ceza_toplami, kabul)
    return b


def gerekli_mi(calisma, fiil=FIIL_SAHTE_BELGE, yil=None):
    """Bu dosyada vergi suclari raporu duzenlenmesi gerekiyor mu.

    Sahte belgede olcut, saticilardan en az birinin "Bilerek kullanma" olarak
    isaretlenmesidir. Ibraz etmemede olcut kunyedeki defter ibraz durumudur.

    `yil` verilirse olcut o yila daraltilir: 2022'de bilerek kullanma varken
    2023'te yoksa 2023 icin suc duyurusu gerekmez ve o yil icin VSR
    uretilmemelidir.
    """
    calisma = calisma or {}
    if fiil == FIIL_IBRAZ_ETMEME:
        return str((calisma.get("kunye") or {}).get("defter_ibraz") or "") \
            == "İbraz edilmedi"
    mukellef_vkn = (calisma.get("mukellef") or {}).get("vkn_tckn")
    liste = F.normalize(calisma.get("faturalar"), mukellef_vkn)
    if yil:
        from .sahte_belge_raporu import _fatura_yili
        liste = [f for f in liste if _fatura_yili(f) == yil]
    satirlar = F.satici_ozeti(liste, calisma.get("saticilar") or {})
    return bool(F.bilerek_kullananlar(satirlar))


def dosya_adi(inceleme, yil=None):
    ad = "".join(c for c in (inceleme.get("ad_unvan") or "rapor")
                 if c.isalnum() or c in " -_").strip() or "rapor"
    if yil:
        ad = "%s_%s" % (yil, ad)
    return ("Vergi_suclari_raporu_taslagi_%s.docx" % ad).replace(" ", "_")
