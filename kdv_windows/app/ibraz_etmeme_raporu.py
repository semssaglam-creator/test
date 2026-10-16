"""Defter ve belge ibraz etmeme raporu (VUK 30/3).

Mukellef yasal defter ve belgelerini incelemeye ibraz etmediginde beyan
edilen indirilecek KDV'nin KDVK 29 ve 34 geregince indirilebilirligi
denetlenemez; bu yuzden indirimlerin TAMAMI reddedilir ve fark KDV, VUK
30/3 uyarinca re'sen tarh edilir. Fiil ayni zamanda VUK 359/a-2'de
"defter, kayit ve belgeleri gizlemek" olarak kacakcilik sucudur: ceza UC
KAT uygulanir ve ayrica vergi suclari raporu duzenlenir.

Mufettisin verdigi ornek rapordan cikarilan yapi:

  1. GIRIS                    (mukellef, gorevlendirme, isteme yazisi ve
                               ibraz edilmedigi, ortaklik tablosu)
  2. USUL INCELEMELERI        (usul tenkitleri ayri raporda)
  3. HESAP INCELEMELERI       (beyan tablosu)
  4. TESPIT VE TENKIT EDILEN HUSUSLAR
       4.1 Re'sen takdir nedeni        (VUK 253, 256, 139, 30/3)
       4.2 Re'sen takdir verileri
             4.2.1 Ibraz edilmemesi + tasdikli defterler
             4.2.2 Duzenlenen ve adina duzenlenen belgeler
             4.2.3 Konuya iliskin yasal duzenlemeler
             4.2.4 Olmasi gereken beyan tablosu + tarhiyat
  5. SONUC                    (re'sen tarh + uc kat ceza + VSR)

Matrah kurali: beyan edilen matrah ile mukellefin DUZENLEDIGI faturalarin
toplami uyusmadiginda VUK 3/B geregi gercek durum esas alinir - ama
yalnizca mukellef aleyhine olan yonde. Duzenlenen faturalar beyandan azsa
beyan esas alinir. Hesabi `hesap.ibraz_etmeme_elestirisi` kuruyor; bu modul
yalnizca yazar, boylece tutanak, Excel ve sonuc bolumu ayni rakamlari
gorur.
"""
from . import faturalar as F
from . import inceleme_kunyesi as ik
from . import mevzuat, turkce
from .belge_docx import TABLO_PUNTOSU, YER_TUTUCU_RENGI as KIRMIZI, Belge
from .sahte_belge_raporu import _donem_adi, _tarhiyat_tablosu, _var
from .tutanak import beyan_dokum_tablosu, dolu_donemler, tarhiyat_toplami

_tl = turkce.tl

# Ibraz etmeme hem re'sen takdir nedeni hem kacakcilik sucudur.
RESEN_MADDE = "30/3"
SUC_MADDESI = "359/a-2"

DEFTER_TUTUCULARI = ("yıl", "defterin türü", "tasdik tarihi ve numarası",
                     "tasdik makamı")


def gerekli_mi(calisma):
    """Bu dosyada ibraz etmeme raporu duzenlenmesi gerekiyor mu."""
    return str((calisma or {}).get("kunye", {}).get("defter_ibraz") or "") \
        == "İbraz edilmedi"


def rapor_yillari(sonuc):
    """Rapor duzenlenecek yillar; sahte belge raporuyla ayni olcut."""
    return sorted({d["yil"] for d in dolu_donemler(sonuc)})


# ------------------------------------------------------------------ 1) giris
def _giris(b, inceleme, kunye, yil, donemler):
    M = ik.mukellef_sozu
    b.baslik("1- GİRİŞ", duzey=1)

    # Mukellefin ise baslama / terk gecmisi serbest metin olarak girilir;
    # tek bir kalipla anlatilamayacak kadar degisken (adres degisikligi,
    # re'sen terk, nevi degisikligi). Girilmemisse olagan cumle yazilir.
    gecmis = ik.satirlar(kunye, "mukellef_gecmisi")
    if gecmis:
        b.paragraf(
            "%s %s mükellefi %s, %s"
            % (ik.vergi_dairesi(inceleme.get("vergi_dairesi"), ek="in"),
               ik.mukellef_kimligi(inceleme, kunye),
               ik.mukellef_adi(inceleme, kunye), gecmis[0]), girinti=1)
        for satir in gecmis[1:]:
            b.paragraf(satir, girinti=1)
    else:
        konular = ik.satirlar(kunye, "faaliyet_konulari")
        b.paragraf(
            "%s %s mükellefi %s, %s adresinde %s faaliyetleri ile iştigal "
            "etmektedir."
            % (ik.vergi_dairesi(inceleme.get("vergi_dairesi"), ek="in"),
               ik.mukellef_kimligi(inceleme, kunye),
               ik.mukellef_adi(inceleme, kunye),
               ik.adres(kunye.get("faaliyet_adresi") or inceleme.get("adres")),
               turkce.liste(konular) if konular else "[faaliyet konusu]"),
            girinti=1)

    emirler = ik.is_emirleri(kunye)
    b.paragraf(
        "T.C. Hazine ve Maliye Bakanlığı Vergi Denetim Kurulu %s %s ile %s "
        "%s katma değer vergisi hesap ve işlemlerinin incelenmesi "
        "istenmiştir."
        % (ik.deger(kunye, "grup_baskanligi", "Denetim Daire Başkanlığının"),
           ik.gorevlendirme_ifadesi(emirler), M(kunye, ek="in"),
           # Donem YALIN kalir: "kurumun ... donemi ... islemlerinin".
           # Ilgi eki eklemek ust uste ucuncu ilgi ekini uretiyordu.
           "%s %s" % (yil, ik.donem_adi(kunye, False))), girinti=1)

    _isteme_yazisi(b, kunye, yil)

    b.paragraf(
        "%s %s ilişkin yasal defter ve belgeleri incelemeye ibraz "
        "edilmediğinden, %s %s faaliyeti GİB Yönetim Bilgi Sistemleri (YBS) "
        "kayıtları ve harici karineler dikkate alınarak incelenmiş ve katma "
        "değer vergisi yönünden tespit ve tenkit edilen hususlar raporun "
        "izleyen bölümlerinde açıklanmıştır."
        % (M(kunye, buyuk=True, ek="in"),
           "%s %s" % (yil, ik.donem_adi(kunye, False, "yonelme")),
           M(kunye, ek="in"),
           "%s %s" % (yil, ik.donem_adi(kunye, False))), girinti=1)

    _ortaklik_tablosu(b, kunye)


def _isteme_yazisi(b, kunye, yil):
    """Defter-belge isteme yazisinin teblig edildigi ve surenin gectigi.

    Raporun en kritik paragrafi: re'sen takdir nedeni buna dayaniyor.
    Tarih ve sayi girilmemisse uydurulmaz, kirmizi yer tutucu kalir.
    """
    eksik = not (str(kunye.get("ibraz_yazi_tarihi") or "").strip()
                 and str(kunye.get("ibraz_teblig_tarihi") or "").strip())
    b.paragraf(
        "Müfettişliğimizce düzenlenen %s tarih ve %s sayılı Defter ve Belge "
        "İsteme yazısının tebligat alındısı %s %s tarihinde teslim "
        "edilmiştir. Defter ve belge isteme yazısında tayin olunan yasal süre "
        "(tebliğ tarihinden itibaren 15 gün) geçmiş olmasına rağmen, %s %s "
        "yasal defter ve belgeleri rapor tarihi itibarıyla Müfettişliğimize "
        "ibraz edilmemiştir."
        % (ik.deger(kunye, "ibraz_yazi_tarihi", "yazı tarihi"),
           ik.deger(kunye, "ibraz_yazi_sayisi", "yazı sayısı"),
           ik.deger(kunye, "ibraz_teblig_alan", "tebligatı teslim alan"),
           ik.deger(kunye, "ibraz_teblig_tarihi", "tebliğ tarihi"),
           ik.mukellef_sozu(kunye, ek="in"),
           "%s %s" % (yil, ik.donem_adi(kunye, False))),
        girinti=1, renk=KIRMIZI if eksik else None)


def _ortaklik_tablosu(b, kunye):
    satirlar = ik.cizgili_satirlar(kunye, "ortaklik_bilgileri", 5)
    if not satirlar:
        return
    b.paragraf("%s ortaklık ve yöneticilik bilgileri aşağıdaki gibidir."
               % ik.mukellef_sozu(kunye, buyuk=True, ek="in"), girinti=1)
    b.tablo([k["etiket"] for k in ik.ORTAKLIK_KOLONLARI], satirlar,
            hizalar=["orta", "orta", "sol", "orta", "sol"],
            oranlar=[1, 1.1, 1.6, 0.7, 1.4], buyukluk=TABLO_PUNTOSU)


# -------------------------------------------------------------- 2) usul
def _usul(b, kunye):
    b.baslik("2- USUL İNCELEMELERİ", duzey=1)
    kayitlar = ik.vir_kayitlari(kunye)
    if kayitlar:
        k = kayitlar[0]
        b.paragraf(
            "Usul yönünden eleştirilen hususlara %s tarih ve %s sayılı vergi "
            "inceleme raporunda yer verildiğinden burada ayrıca "
            "bahsedilmeyecektir."
            % (k.get("tarih") or "[rapor tarihi]",
               k.get("sayi") or "[rapor sayısı]"), girinti=1)
        return
    for satir in ik.satirlar(kunye, "usul_notu"):
        b.paragraf(satir, girinti=1)
    if not ik.satirlar(kunye, "usul_notu"):
        b.paragraf("Usul yönünden tenkidi gerektiren bir husus tespit "
                   "edilmemiştir.", girinti=1)


# -------------------------------------------------------------- 3) hesap
def _hesap(b, kunye, yil, donemler):
    b.baslik("3- HESAP İNCELEMELERİ", duzey=1)
    b.paragraf(
        "Müfettişliğimizce GİB Intranet sistemi kayıtlarından yapılan "
        "sorgulamalarda %s %s dönemine ilişkin olarak verdiği katma değer "
        "vergisi beyannamelerinin özetinin aşağıdaki gibi olduğu tespit "
        "edilmiştir."
        % (ik.mukellef_sozu(kunye, buyuk=True, ek="in"),
           _donem_araligi(yil, donemler)), girinti=1)
    beyan_dokum_tablosu(b, donemler, "beyan")


def _donem_araligi(yil, donemler):
    """"Ocak-Temmuz/2021" gibi; girilen ay sayisina gore daralir."""
    if not donemler:
        return "%s/Ocak-Aralık" % yil
    adlar = sorted(donemler, key=lambda d: d["ay"])
    if adlar[0]["ay"] == adlar[-1]["ay"]:
        return "%s/%s" % (yil, adlar[0]["ay_adi"])
    return "%s/%s-%s" % (yil, adlar[0]["ay_adi"], adlar[-1]["ay_adi"])


# ----------------------------------------------------------- 4) tenkit
def _tenkit(b, kunye, inceleme, yil, donemler, liste, saticilar):
    M = ik.mukellef_sozu
    b.baslik("4- TESPİT VE TENKİT EDİLEN HUSUSLAR", duzey=1)

    _resen_takdir_nedeni(b, kunye, yil, donemler)
    b.baslik("4.2- Re’sen Takdir Verileri", duzey=2)
    _ibraz_edilmemesi(b, kunye, yil, donemler)
    _belge_dokumleri(b, kunye, yil, liste)
    _yasal_duzenlemeler(b, kunye, yil, donemler)
    _olmasi_gereken(b, kunye, inceleme, yil, donemler)


def _resen_takdir_nedeni(b, kunye, yil, donemler):
    M = ik.mukellef_sozu
    b.baslik("4.1- Re’sen Takdir Nedeni", duzey=2)
    for baslik, metin in mevzuat.maddeler(["vuk_253", "vuk_256", "vuk_139",
                                           "vuk_30_3"]):
        b.paragraf(baslik, kalin=True, hiza="sol", aralik_once=120,
                   aralik_sonra=40)
        b.paragraf("“%s”" % metin, girinti=1, italik=True)
    b.paragraf(
        "%s %s ilişkin yasal defter ve belgelerinin incelemeye ibraz "
        "edilmemesi nedeniyle, 213 sayılı Vergi Usul Kanunu’nun %s. maddesi "
        "uyarınca ilgili dönemlerin katma değer vergisi beyanlarının re’sen "
        "tarhiyata esas olacak şekilde düzeltilmesi ve %s %s dönemleri katma "
        "değer vergisi beyannamelerinde indirim konusu yapılmış olan katma "
        "değer vergilerinin reddedilmesi gerekmektedir."
        % (M(kunye, buyuk=True, ek="in"),
           "%s %s" % (yil, ik.donem_adi(kunye, False, "yonelme")),
           RESEN_MADDE, M(kunye, ek="in"),
           _donem_araligi(yil, donemler)), girinti=1)


def _ibraz_edilmemesi(b, kunye, yil, donemler):
    b.baslik("4.2.1- Yasal Defter ve Belgelerin İncelemeye İbraz Edilmemesi",
             duzey=2)
    b.paragraf(
        "213 sayılı Vergi Usul Kanunu’nun 256 ve 257 nci maddeleri "
        "doğrultusunda yürütülecek vergi incelemesine esas olmak üzere yasal "
        "defter ve belgelerin ibrazı istenmiş, yasal süre (tebliğ tarihinden "
        "itibaren 15 gün) geçmesine rağmen söz konusu defter ve belgeler %s "
        "tarafından raporun yazıldığı tarih dahil olmak üzere ibraz "
        "edilmemiştir." % ik.mukellef_sozu(kunye), girinti=1)

    # Tasdikli defter bilgileri: defterlerin VARLIGINI ortaya koyar ve
    # gizleme fiilinin maddi unsuru buna dayanir.
    satirlar = ik.cizgili_satirlar(kunye, "defter_bilgileri", 4,
                                   DEFTER_TUTUCULARI)
    if not satirlar:
        satirlar = [[str(yil)] + ["[%s]" % ad for ad in DEFTER_TUTUCULARI[1:]]]
    b.paragraf("%s tasdik edilmiş defter bilgileri aşağıdaki gibidir."
               % ik.mukellef_sozu(kunye, buyuk=True, ek="in"), girinti=1)
    b.tablo(["Yılı", "Defterin Türü", "Tasdik Tarihi ve Numarası",
             "Tasdik Makamı"], satirlar,
            hizalar=["orta", "sol", "orta", "sol"],
            oranlar=[0.6, 1.4, 1.4, 1.6], buyukluk=TABLO_PUNTOSU)
    belge_basim_tablosu(b, kunye)


def belge_basim_tablosu(b, kunye, cumle=True):
    """Anlasmali matbaaya bastirilan belgelerin dokumu.

    YALNIZCA kunyeye satir girilmisse yazilir. Bos birakildiginda ne tablo
    ne de ona gonderme yapan cumle kurulur; mukellef e-belgeye gecmisse bu
    kayit hic bulunmaz, kirmizi yer tutucu birakmak yanlis olurdu.

    Ibraz etmeme raporu ile onun vergi suclari raporu ayni tabloyu yazdigi
    icin ortak: VSR bu ismi dogrudan cagirir. VSR'de tabloya gonderme yapan
    cumle defter tasdik cumlesiyle birlesik kuruldugundan oradan
    `cumle=False` gelir.
    """
    satirlar = ik.belge_basim_satirlari(kunye)
    if not satirlar:
        return
    if cumle:
        b.paragraf(
            "Müfettişliğimizce GİB Intranet sisteminden yapılan sorgulama "
            "neticesinde %s anlaşmalı matbaalara bastırdığı belgelere "
            "ilişkin basım bilgilerinin aşağıdaki gibi olduğu tespit "
            "edilmiştir." % ik.mukellef_sozu(kunye, ek="in"), girinti=1)
    b.paragraf("İbraz Edilmeyen Belgelerin Basım Bilgileri", kalin=True,
               hiza="sol", aralik_once=120, aralik_sonra=40)
    b.tablo(ik.belge_basim_basliklari(), satirlar,
            hizalar=["sol", "orta", "sol", "orta", "orta", "orta", "orta"],
            oranlar=[1.6, 1.0, 1.2, 0.7, 1.0, 1.0, 0.7],
            buyukluk=TABLO_PUNTOSU)


def _belge_dokumleri(b, kunye, yil, liste):
    """Mukellefin duzenledigi ve adina duzenlenen belgeler.

    Ikisi AYRI tablodur ve ikisi de rapora girer: duzenlenen belgeler
    matrahin, adina duzenlenenler indirim tarafinin dayanagidir. Defter
    ibraz edilmedigi icin ikisi de GIB kayitlarindan alinmistir.
    """
    b.baslik("4.2.2- Mükellef Tarafından Düzenlenen ve Mükellef Adına "
             "Düzenlenen Belgeler", duzey=2)

    satislar = [f for f in liste
                if f.get("yon") == F.YON_SATIS and not f.get("iptal")
                and f.get("kayit_yil") == yil]
    alislar = [f for f in liste
               if f.get("yon") == F.YON_ALIS and not f.get("iptal")
               and f.get("kayit_yil") == yil]

    b.paragraf(
        "Müfettişliğimizce %s hakkında GİB Intranet sisteminden yapılan "
        "sorgulama neticesinde %s yılında düzenlediği ve adına düzenlenen "
        "belgelerin aşağıdaki gibi olduğu tespit edilmiştir."
        % (ik.mukellef_sozu(kunye), yil), girinti=1)

    _belge_tablosu(b, "Mükellef Tarafından Düzenlenen Belgeler", satislar,
                   "düzenlediği")
    _belge_tablosu(b, "Mükellef Adına Düzenlenen Belgeler", alislar,
                   "adına düzenlenen")


def _belge_tablosu(b, baslik, faturalar, soz):
    b.paragraf(baslik, kalin=True, hiza="sol", aralik_once=120,
               aralik_sonra=40)
    if not faturalar:
        b.paragraf("[%s belge dökümü Faturalar sekmesine girilmemiştir.]"
                   % baslik, girinti=1, renk=KIRMIZI)
        return
    satirlar = []
    matrah = kdv = toplam = 0.0
    for i, f in enumerate(sorted(faturalar,
                                 key=lambda x: (x.get("tarih") or "",
                                                x.get("fatura_no") or "")), 1):
        m = float(f.get("matrah") or 0.0)
        k = float(f.get("kdv") or 0.0)
        t = float(f.get("toplam") or 0.0) or (m + k)
        matrah += m
        kdv += k
        toplam += t
        satirlar.append([str(i), f.get("fatura_no") or "",
                         _gun(f.get("tarih")),
                         f.get("satici_vkn") or f.get("alici_vkn") or "",
                         _tl(m), _tl(k), _tl(t)])
    satirlar.append(["", "TOPLAM", "", "", _tl(matrah), _tl(kdv), _tl(toplam)])
    b.tablo(["Sıra", "Belge Numarası", "Belge Tarihi", "VKN / TCKN",
             "Vergi Hariç\nTutar", "Vergi\nTutarı", "Toplam\nTutar"],
            satirlar, hizalar=["orta", "sol", "orta", "orta", "sag", "sag",
                               "sag"],
            oranlar=[0.5, 1.6, 0.9, 1.1, 1.1, 1.0, 1.1],
            buyukluk=TABLO_PUNTOSU, toplam_satiri=True)


def _gun(iso):
    """ISO tarihi belgede gun.ay.yil olarak yazar."""
    parcalar = str(iso or "").split("-")
    if len(parcalar) == 3 and all(p.isdigit() for p in parcalar):
        return "%s.%s.%s" % (parcalar[2], parcalar[1], parcalar[0])
    return iso or ""


def _yasal_duzenlemeler(b, kunye, yil, donemler):
    b.baslik("4.2.3- Konuya İlişkin Yasal Düzenlemeler", duzey=2)
    for baslik, metin in mevzuat.maddeler(["vuk_3b", "vuk_134", "vuk_227",
                                           "vuk_229", "kdv_29", "kdv_34",
                                           "vuk_341", "vuk_344"]):
        b.paragraf(baslik, kalin=True, hiza="sol", aralik_once=120,
                   aralik_sonra=40)
        b.paragraf("“%s”" % metin, girinti=1, italik=True)
    b.paragraf(
        "Yukarıda belirtilen açıklamalar ile 213 sayılı Vergi Usul Kanunu ve "
        "3065 sayılı Katma Değer Vergisi Kanununda yer alan kanuni "
        "düzenlemelere göre, mükellefin alışlarına ilişkin katma değer "
        "vergilerini indirim konusu yapabilmesi için bunların fatura veya "
        "vesikalarda ayrıca gösterilmesi ve kanuni defterlere kaydedilmesi "
        "gerekmektedir.", girinti=1)
    b.paragraf(
        "%s defter ve belge ibraz etme ödevine uymayarak %s ait defter ve "
        "belgelerini incelemeye ibraz etmemiştir. Yukarıda belirtilen yasal "
        "dayanaklar ve açıklamalar ışığında, %s katma değer vergisi "
        "beyannameleri ile beyan edilen indirilecek katma değer vergisinin "
        "Katma Değer Vergisi Kanunu’nun 29 ve 34 üncü maddeleri hükmünce "
        "indirimi mümkün değildir. Bu nedenle %s %s dönemleri katma değer "
        "vergisi beyannamelerinde belirttiği indirilecek katma değer "
        "vergilerinin reddedilmesi gerekmektedir."
        % (ik.mukellef_sozu(kunye, buyuk=True),
           "%s %s" % (yil, ik.donem_adi(kunye, False, "yonelme")),
           ik.mukellef_sozu(kunye, ek="in"), ik.mukellef_sozu(kunye, ek="in"),
           _donem_araligi(yil, donemler)), girinti=1)


def _olmasi_gereken(b, kunye, inceleme, yil, donemler):
    M = ik.mukellef_sozu
    b.baslik("4.2.4- Olması Gereken Katma Değer Vergisi Beyan Tablosu",
             duzey=2)

    _matrah_paragrafi(b, kunye, yil, donemler)
    b.paragraf(
        "Raporumuzun 1. bölümünde açıklandığı üzere Müfettişliğimizce %s %s "
        "ilişkin yasal defter ve belgelerinin incelemeye ibraz edilmesi "
        "istenmiştir. Ancak yasal defter ve belgelerin ibraz edilmemesi "
        "nedeniyle indirim konusu yapılan alışlara ait katma değer "
        "vergilerinin defter ve belgelere uygunluğu tespit edilememiştir. Bu "
        "nedenle %s indirim konusu yaptığı katma değer vergisi tutarları "
        "Müfettişliğimizce yukarıda açıklanan kanun hükümleri gereğince "
        "reddedilmiş ve %s dönemlerine ait katma değer vergisi beyanları "
        "dönemler itibarıyla aşağıdaki gibi yeniden düzenlenmiştir."
        % (M(kunye, ek="in"),
           "%s %s" % (yil, ik.donem_adi(kunye, False, "yonelme")),
           M(kunye, ek="in"), _donem_araligi(yil, donemler)), girinti=1)
    beyan_dokum_tablosu(b, donemler, "elestirili")

    tarhiyatli = [d for d in donemler
                  if abs(float((d.get("tarhiyat") or {}).get("toplam_fark")
                               or 0.0)) > 0.005]
    b.paragraf(
        "Tarafımızca düzenlenen katma değer vergisi beyan tablosunda tespit "
        "edilen ödenecek katma değer vergisi tutarlarından %s verdiği katma "
        "değer vergisi beyannamelerinde beyan edilen ödenecek katma değer "
        "vergisi tutarları mahsup edildiğinde, aşağıdaki tabloda yer alan "
        "fark katma değer vergisi tutarlarının re’sen tarh edilmesi "
        "gerekmektedir." % M(kunye, ek="in"), girinti=1)
    _tarhiyat_tablosu(b, tarhiyatli, {})
    b.paragraf(
        "Yukarıdaki tabloda hesaplanmış olan fark katma değer vergisi "
        "tutarlarının ilgili dönemlere ait fark katma değer vergisi olarak "
        "213 sayılı Vergi Usul Kanunu’nun %s. maddesi gereğince re’sen tarh "
        "edilmesi, re’sen tarh edilecek katma değer vergisi tutarları "
        "üzerinden aynı Kanun’un 344 üncü maddesinin ikinci fıkrası gereğince "
        "üç kat vergi ziyaı cezası kesilmesi gerekmektedir."
        % RESEN_MADDE, girinti=1)
    b.paragraf(
        "Raporumuzun önceki bölümlerinde açıklandığı üzere %s %s ilişkin "
        "yasal defter ve belgeleri incelemeye ibraz edilmemiştir. Bu nedenle "
        "%s %s kazançlarının tespitine yönelik başka bir veri ve bilgiye "
        "ulaşılamadığından, %s ve %s yönünden %s hakkında yapılacak bir işlem "
        "bulunmamaktadır."
        % (M(kunye, ek="in"),
           "%s %s" % (yil, ik.donem_adi(kunye, False, "yonelme")),
           M(kunye, ek="in"), "%s %s" % (yil, ik.donem_adi(kunye, False)),
           ik.gelir_vergisi_adi(kunye).title(),
           ik.gecici_vergi_adi(kunye).title(), M(kunye)), girinti=1)


def _matrah_paragrafi(b, kunye, yil, donemler):
    """Matrahin duzenlenen faturalara gore kuruldugu hal.

    Yalnizca gercekten ilave yapildiysa yazilir: beyan edilen matrah
    duzenlenen faturalarin toplamindan BUYUKSE beyan esas alinir ve
    anlatilacak bir sey yoktur.
    """
    ilave = sum(float(d["elestirili"].get("matrah") or 0.0)
                - float(d["beyan"].get("matrah") or 0.0) for d in donemler)
    if ilave <= 0.005:
        return
    beyan_toplam = sum(float(d["beyan"].get("matrah") or 0.0)
                       for d in donemler)
    b.paragraf(
        "Müfettişliğimizce GİB kayıtlarından yapılan sorgulamada, %s %s "
        "beyan ettiği %s TL katma değer vergisi matrahı ile düzenlediği "
        "belgelerin toplamı uyuşmamaktadır. 213 sayılı Vergi Usul "
        "Kanunu’nun 3 üncü maddesinin (B) fıkrası uyarınca vergilendirmede "
        "vergiyi doğuran olayın gerçek mahiyeti esas olduğundan, katma değer "
        "vergisi matrahları %s düzenlediği belgelere göre %s TL ilavesiyle "
        "yeniden düzenlenmiştir."
        % (ik.mukellef_sozu(kunye, ek="in"),
           "%s %s" % (yil, ik.donem_adi(kunye, False, "bulunma")),
           _tl(beyan_toplam), ik.mukellef_sozu(kunye, ek="in"), _tl(ilave)),
        girinti=1)


# ------------------------------------------------------------------ 5) sonuc
def _sonuc(b, inceleme, kunye, yil, donemler):
    M = ik.mukellef_sozu
    b.baslik("5- SONUÇ", duzey=1)
    b.paragraf(
        "%s %s mükellefi %s’nin %s ilişkin olarak yapılan inceleme "
        "neticesinde;"
        % (ik.vergi_dairesi(inceleme.get("vergi_dairesi"), ek="in"),
           ik.mukellef_kimligi(inceleme, kunye),
           ik.mukellef_adi(inceleme, kunye),
           "%s %s" % (yil, ik.donem_adi(kunye, False, "yonelme"))), girinti=1)

    tarhiyatli = [d for d in donemler
                  if abs(float((d.get("tarhiyat") or {}).get("toplam_fark")
                               or 0.0)) > 0.005]
    toplam = tarhiyat_toplami(tarhiyatli)

    maddeler = [
        "5.1- Raporun 4.2.4 bölümünde ayrıntılı olarak açıklandığı üzere, "
        "aşağıda dönemi ve tutarı yazılı katma değer vergilerinin ilgili "
        "dönemlere ait fark katma değer vergisi olarak %s adına 213 sayılı "
        "Vergi Usul Kanunu’nun %s. maddesi gereğince re’sen tarh edilmesi, "
        "re’sen tarh edilecek fark katma değer vergisi tutarları üzerinden "
        "aynı Kanun’un 344 üncü maddesinin ikinci fıkrası gereğince üç kat "
        "vergi ziyaı cezası kesilmesi,"
        % (M(kunye), RESEN_MADDE),
        # Ibraz etmeme ayni zamanda kacakcilik sucudur; VSR bu maddeyle
        # istenir ve uygulama raporla birlikte uretir.
        "5.2- 213 sayılı Vergi Usul Kanunu’nun %s maddesine göre “defter, "
        "kayıt ve belgeleri gizlemek” suretiyle vergi ziyaına sebebiyet veren "
        "%s hakkında aynı Kanun’un 367 nci maddesi gereğince %s suç "
        "duyurusunda bulunulması gerektiğinden Müfettişliğimizce Vergi "
        "Suçları Raporu düzenlenmesi,"
        % (SUC_MADDESI, ik.suc_duyurusu_hedefi(kunye, inceleme),
           _savcilik(kunye)),
    ]
    if ik.secim_mi(kunye, "tou_talebi", "Talep edildi"):
        maddeler.append("5.3- %s tarhiyat öncesi uzlaşma talebinin dikkate "
                        "alınması," % M(kunye, ek="in"))

    for sira, metin in enumerate(maddeler):
        b.paragraf(metin, kalin=True, girinti=1, aralik_sonra=100)
        if tarhiyatli and sira == 0:
            _tarhiyat_tablosu(b, tarhiyatli, {})

    b.paragraf("Gerektiği kanaat ve sonucuna varılmıştır.", girinti=1,
               aralik_once=120)
    b.bos_satir()
    b.imza_bloklari([(ik.deger(kunye, "eleman_unvan", "unvan"),
                      ik.ad(kunye, "eleman_ad"))])


def _savcilik(kunye):
    """"Adana Cumhuriyet Başsavcılığına" - VSR ile ayni kaynaktan."""
    from .vergi_sucu_raporu import _savcilik as vsr_savcilik
    return vsr_savcilik(kunye, "yonelme")


# ------------------------------------------------------------------- uretim
def rapor_uret(inceleme, kunye, sonuc, calisma, yil):
    """Bir yilin ibraz etmeme raporunu uretir ve `Belge` dondurur."""
    kunye = ik.normalize(kunye)
    yil = int(yil)
    calisma = calisma or {}
    donemler = [d for d in dolu_donemler(sonuc) if d["yil"] == yil]
    mukellef_vkn = (calisma.get("mukellef") or {}).get("vkn_tckn")
    liste = F.normalize(calisma.get("faturalar"), mukellef_vkn)
    saticilar = calisma.get("saticilar") or {}

    b = Belge()
    _giris(b, inceleme, kunye, yil, donemler)
    _usul(b, kunye)
    _hesap(b, kunye, yil, donemler)
    _tenkit(b, kunye, inceleme, yil, donemler, liste, saticilar)
    _sonuc(b, inceleme, kunye, yil, donemler)
    return b


def dosya_adi(inceleme, yil):
    ad = "".join(c for c in (inceleme.get("ad_unvan") or "rapor")
                 if c.isalnum() or c in " -_").strip() or "rapor"
    return ("Ibraz_etmeme_raporu_taslagi_%s_%s.docx"
            % (yil, ad)).replace(" ", "_")


def paket_adi(inceleme):
    ad = "".join(c for c in (inceleme.get("ad_unvan") or "rapor")
                 if c.isalnum() or c in " -_").strip() or "rapor"
    return ("Ibraz_etmeme_raporlari_%s.zip" % ad).replace(" ", "_")
