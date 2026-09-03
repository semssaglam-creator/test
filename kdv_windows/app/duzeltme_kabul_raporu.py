"""Duzeltme kabul raporu (Vergi Teknigi Raporu).

Sahte belge kullanma incelemesinde, sahteci mukelleften alinan faturalarin
TAMAMI ya duzeltme beyannamesiyle indirimlerden cikarilmis ya da hic kayitlara
alinmamissa tarhiyat yapilacak bir sey kalmaz: reddedilecek indirim zaten
beyanda degildir. Bu durumda tarhiyatli rapor degil, tespiti ve "yapilacak bir
islem bulunmadigi" sonucunu yazan bir rapor duzenlenir.

Yapisi ornek rapordan cikarilmistir:

  1- GIRIS
  2- YAPILAN INCELEME VE TESPITLER   (KDV beyan ozeti, satici bazinda tespit,
                                      duzeltme dokumu)
  3- ILGILI MEVZUAT                  (KDV indirimi, yargi kararlari, sahte
                                      belge kullanimi)
  4- DEGERLENDIRMELER                (KDV, bilerek/bilmeden, kazanc vergileri)
  5- SONUC

Tarhiyat, ceza ve uzlasma bolumleri BILEREK yoktur; bu raporun tamami
"islem yapilmasina gerek bulunmadigi" kanaatini kurar. Sahte belge kullanma
raporu (sahte_belge_raporu.py) ise tarhiyatli dosyalar icindir; ikisi ayni
dosyada birlikte kullanilmaz.
"""
from . import faturalar as F
from . import inceleme_kunyesi as ik
from . import mevzuat, turkce
from .belge_docx import TABLO_PUNTOSU, YER_TUTUCU_RENGI as KIRMIZI, Belge
from .tutanak import (beyan_dokum_tablosu, dolu_donemler,
                      satici_tespit_paragraflari)

_tl = turkce.tl


def _donem_ifadesi(kunye, donemler, hal="yalin"):
    """"2021 takvim yili" / "2021 ve 2022 hesap donemleri" gibi ifadeler."""
    yillar = sorted({d["yil"] for d in donemler})
    if not yillar:
        return "[dönem]"
    return "%s %s" % (turkce.liste([str(y) for y in yillar]),
                      ik.donem_adi(kunye, len(yillar) > 1, hal))


# --------------------------------------------------------------------- 1) giris
def _giris(b, inceleme, kunye, donemler, satici_satirlari):
    M = ik.mukellef_sozu
    b.baslik("1- GİRİŞ", duzey=1)

    b.paragraf(
        "%s %s mükellefi %s (bundan sonra %s olarak anılacaktır) “%s” "
        "adresinde %s."
        % (ik.vergi_dairesi(inceleme.get("vergi_dairesi"), ek="in"),
           ik.mukellef_kimligi(inceleme, kunye),
           ik.mukellef_adi(inceleme, kunye),
           M(kunye),
           ik.faaliyet_adresi(kunye, inceleme),
           ik.faaliyet_ifadesi(kunye)), girinti=1)

    emirler = ik.is_emirleri(kunye)
    b.paragraf(
        "T.C. Hazine ve Maliye Bakanlığı Vergi Denetim Kurulu Başkanlığı %s "
        "%s ile %s işlemlerinin “Sahte Belge Kullanma” gerekçesiyle sınırlı "
        "olarak incelenmesi istenmiştir."
        % (ik.deger(kunye, "grup_baskanligi", "Denetim Daire Başkanlığının"),
           ik.gorevlendirme_ifadesi(emirler),
           _donem_ifadesi(kunye, donemler)), girinti=1)

    is_emrili, sonradan = F.is_emrine_gore_ayir(satici_satirlari)
    if is_emrili:
        adlar = ["%s %s vergi kimlik numaralı mükellefi %s’den"
                 % (ik.vergi_dairesi(s["vergi_dairesi"],
                                     "[Satıcının vergi dairesi]", "in"),
                    s["vkn"] or "[VKN]", ik.satici_unvani(s))
                 for s in is_emrili]
        b.paragraf(
            "İş emri gerekçesinde; %s %s %s olan alışlarının sahte belge "
            "kullanma kapsamında sınırlı olarak incelenmesi gerektiği yer "
            "almaktadır."
            % (M(kunye, ek="in"), _donem_ifadesi(kunye, donemler, "bulunma"),
               turkce.liste(adlar)), girinti=1)

    if sonradan:
        b.paragraf(
            "Müfettişliğimizce yapılan inceleme esnasında, %s alış yaptığı "
            "aşağıda listelenen mükellefler hakkında da sahte belge "
            "düzenlediği yönünde vergi tekniği raporu bulunduğu tespit "
            "edildiğinden, söz konusu mükellefler de incelememiz kapsamına "
            "alınmıştır." % M(kunye, ek="in"), girinti=1)
        b.tablo(["Sıra No", "Yılı", "Vergi Dairesi", "Vergi Kimlik No",
                 "Unvanı", "Vergi Tekniği Raporu\nTarih ve Sayısı"],
                [[str(i), _yillar(x),
                  ik.vergi_dairesi(x["vergi_dairesi"],
                                   "[Satıcının vergi dairesi]"),
                  x["vkn"] or "[VKN]", ik.satici_unvani(x),
                  "%s tarih ve %s" % (x.get("vtr_tarihi") or "[VTR tarihi]",
                                      x.get("vtr_no") or "[VTR no]")]
                 for i, x in enumerate(sonradan, 1)],
                hizalar=["orta", "orta", "sol", "orta", "sol", "orta"],
                oranlar=[0.45, 0.6, 1.5, 1, 1.9, 1.5],
                buyukluk=TABLO_PUNTOSU)

    b.paragraf(
        "%s %s iş ve işlemlerinin söz konusu görevlendirme yazısına istinaden "
        "sınırlı olarak incelenmesi neticesinde Katma Değer Vergisi ve sahte "
        "belge kullanma fiilinin 213 sayılı Vergi Usul Kanunu’nun 359. "
        "maddesine sirayet edip etmediği hususu yönünden tespit ve "
        "değerlendirmeler raporun izleyen bölümlerinde açıklanmıştır."
        % (M(kunye, buyuk=True, ek="in"), _donem_ifadesi(kunye, donemler)),
        girinti=1)


def _yillar(s):
    """Saticinin belgelerinin ait oldugu yil(lar)."""
    yillar = [str(d["yil"]) for d in (s.get("yil_dokumu") or []) if d.get("yil")]
    return ", ".join(yillar) if yillar else "[yıl]"


# ------------------------------------------------------- 2) inceleme ve tespit
def _tespitler(b, kunye, donemler, satici_satirlari, liste, karsilastirmalar):
    M = ik.mukellef_sozu
    b.baslik("2- YAPILAN İNCELEME VE TESPİTLER", duzey=1)

    b.baslik("2.1- %s KDV Beyanname Özetleri"
             % _donem_ifadesi(kunye, donemler), duzey=2)
    b.paragraf("%s %s ait KDV beyannamelerinin özeti aşağıdaki gibidir."
               % (M(kunye, buyuk=True, ek="in"),
                  _donem_ifadesi(kunye, donemler, "yonelme")), girinti=1)
    beyan_dokum_tablosu(b, donemler)

    b.baslik("2.2- Mükellef Hakkında Yapılan Tespitler", duzey=2)
    for sira, s in enumerate(satici_satirlari, 1):
        _satici_tespiti(b, kunye, s, liste, karsilastirmalar, sira)


def _satici_tespiti(b, kunye, s, liste, karsilastirmalar, sira):
    """Bir saticiya iliskin tespit: fatura dokumu, VTR, duzeltme akibeti."""
    M = ik.mukellef_sozu
    kendi = [f for f in liste if (f.get("satici_vkn") or "") == s["vkn"]]

    b.baslik("2.2.%d- %s" % (sira, ik.satici_unvani(s)), duzey=3)

    kayda_alinmadi = str(s.get("kayda_alinmadi") or "") == "Evet"
    if kendi:
        b.paragraf(
            "Aşağıda dökümü yapılan %d adet faturanın, %s %s vergi kimlik "
            "numaralı mükellefi %s’den %s alındığı tespit edilmiştir.%s"
            % (len(kendi),
               ik.vergi_dairesi(s["vergi_dairesi"], "[Satıcının vergi dairesi]",
                                "in"),
               s["vkn"] or "[VKN]", ik.satici_unvani(s), _yillar(s),
               (" Söz konusu faturaların %s yasal defter kayıtlarına hiç "
                "alınmadığı görülmüştür." % M(kunye, ek="in"))
               if kayda_alinmadi else ""), girinti=1)
        b.tablo(["Fatura Tarih", "Fatura No", "Malın Cinsi", "Tutar", "KDV",
                 "Toplam Tutar"],
                [[F.tarih_goster(f.get("tarih")), f.get("fatura_no") or "",
                  F.mal_cinsi_hucresi(f), _tl(f.get("matrah")),
                  _tl(f.get("kdv")), _tl(f.get("toplam"))] for f in kendi]
                + [["TOPLAM", "", "", _tl(s["liste_matrah"]),
                    _tl(s["liste_kdv"]), _tl(s["liste_toplam"])]],
                hizalar=["orta", "sol", "sol", "sag", "sag", "sag"],
                oranlar=[1, 1.3, 1.4, 1.2, 1.1, 1.2],
                buyukluk=TABLO_PUNTOSU, toplam_satiri=True)
    else:
        b.paragraf(
            "%s %s vergi kimlik numaralı mükellefi %s’den %s %s TL tutarında "
            "alış bildiriminde bulunulduğu tespit edilmiştir."
            % (ik.vergi_dairesi(s["vergi_dairesi"], "[Satıcının vergi dairesi]",
                                "in"),
               s["vkn"] or "[VKN]", ik.satici_unvani(s), _yillar(s),
               _tl(s.get("liste_matrah"))), girinti=1)

    for satir in satici_tespit_paragraflari(s):
        b.paragraf(satir, girinti=1)
    b.paragraf("(Yetkili makamlarca talep edilmesi hâlinde, söz konusu rapor "
               "ilgili vergi dairesinden temin edilebilecektir.)", girinti=1)

    _akibet(b, kunye, s, kendi, karsilastirmalar)


def _akibet(b, kunye, s, kendi, karsilastirmalar):
    """Faturalarin akibeti: duzeltmeyle cikarilma ya da hic kayda girmeme."""
    M = ik.mukellef_sozu
    if str(s.get("kayda_alinmadi") or "") == "Evet":
        b.paragraf(
            "Söz konusu faturalar %s yasal defterlerine hiç kaydedilmediğinden "
            "ve bu faturalarda yer alan katma değer vergisi indirim "
            "hesaplarına hiç alınmadığından, reddi gereken bir indirim "
            "bulunmamaktadır." % M(kunye, ek="in"), girinti=1)
        return

    if str(s.get("duzeltme_ile_cikarildi") or "") != "Evet":
        return

    # Duzeltme dokumu: hangi donemde hangi satirdan cikarildigi. Rapor ile
    # tutanak ayni ureteceten beslensin diye sahte_belge_raporu'ndaki bolum
    # kullanilir; modul dongusune girmemek icin burada yuklenir.
    from .sahte_belge_raporu import _duzeltme_bolumu
    _duzeltme_bolumu(b, kunye, s, kendi, karsilastirmalar, None)

    b.paragraf(
        "Yukarıda yer verilen tespitlerden görüleceği üzere, %s tarafından "
        "%s TL tutarındaki katma değer vergisi düzeltme beyannamesi verilmek "
        "suretiyle indirim hesaplarından çıkarılmıştır. Dolayısıyla anılan "
        "mükellefe ait faturalar beyanlardan çıkarılmış olduğundan, ilgili "
        "faturalara ilişkin eleştiriyi gerektirecek bir hususa "
        "rastlanılmamıştır."
        % (M(kunye, ek="in"), _tl(s.get("liste_kdv"))), girinti=1)


# ------------------------------------------------------------- 3) mevzuat
def _ilgili_mevzuat(b):
    b.baslik("3- İLGİLİ MEVZUAT", duzey=1)

    b.baslik("3.1- Katma Değer Vergisi ile İlgili Yasal Düzenlemeler", duzey=2)
    for baslik, metin in mevzuat.maddeler(["kdv_29", "kdv_34",
                                           "kdv_indirim_sartlari"]):
        b.paragraf(baslik, kalin=True, girinti=1)
        b.paragraf(metin, girinti=1)

    b.baslik("3.2- Yargı Kararları", duzey=2)
    baslik, metin = mevzuat.madde("danistay_indirim")
    b.paragraf(metin, girinti=1)

    b.baslik("3.3- Sahte Belge Kullanımı ile İlgili Yasal Düzenlemeler",
             duzey=2)
    for baslik, metin in mevzuat.maddeler(["vuk_3b", "vuk_359",
                                           "vuk_teblig_306"]):
        b.paragraf(baslik, kalin=True, girinti=1)
        b.paragraf(metin, girinti=1)


# -------------------------------------------------------- 4) degerlendirmeler
def _degerlendirmeler(b, kunye, satici_satirlari, oran, inceleme):
    M = ik.mukellef_sozu
    b.baslik("4- DEĞERLENDİRMELER", duzey=1)

    b.baslik("4.1- Katma Değer Vergisi Yönünden Yapılan Değerlendirme",
             duzey=2)
    adlar = turkce.liste([ik.satici_unvani(s) for s in satici_satirlari])
    b.paragraf(
        "Raporumuzun 2.2. bölümünde yer alan tespitlerden görüleceği üzere; "
        "%s adına düzenlenmiş olan %s faturalarında yer alan katma değer "
        "vergisi tutarları indirim hesaplarına hiç alınmamış ya da düzeltme "
        "beyannamesi verilmek suretiyle indirim hesaplarından çıkarılmıştır. "
        "Bu sebeple müfettişliğimizce söz konusu alışlarla ilgili katma değer "
        "vergisi yönünden yapılacak bir işlem bulunmamaktadır."
        % (M(kunye, ek="in"), adlar), girinti=1)

    b.paragraf(
        "Bu tutarlar beyandan çıkarılmış olduğundan, söz konusu faturalar "
        "nedeniyle re’sen ya da ikmalen tarh edilecek bir katma değer vergisi "
        "bulunmamaktadır.", girinti=1)

    b.baslik("4.2- Sahte Faturaların Bilerek Kullanılıp Kullanılmadığına "
             "Yönelik Değerlendirme", duzey=2)
    if oran and oran.get("oran") is not None:
        b.paragraf(
            "%s söz konusu belgelerde yer alan indirilecek katma değer vergisi "
            "tutarının (%s TL), bu döneme ait indirilecek katma değer vergisi "
            "toplamı (%s TL) içindeki payı %%%s’e tekabül etmektedir."
            % (M(kunye, buyuk=True, ek="in"), _tl(oran["sahte_kdv"]),
               _tl(oran["toplam_indirim_kdv"]), _tl(oran["oran"])), girinti=1)
    else:
        b.paragraf(
            "Söz konusu belgelerde yer alan indirilecek katma değer vergisinin "
            "toplam indirimler içindeki payı [oran] olarak hesaplanmıştır.",
            girinti=1, renk=KIRMIZI)

    bilerek = F.bilerek_kullananlar(satici_satirlari)
    if bilerek:
        b.paragraf(
            "%s söz konusu belgeleri bilerek kullandığı kanaatine varılmıştır. "
            "Bu kanaate; %s hakkında düzenlenen vergi tekniği raporlarındaki "
            "tespitler, belgelerin %s ve inceleme sırasında elde edilen diğer "
            "bulgular birlikte değerlendirilerek ulaşılmıştır."
            % (M(kunye, buyuk=True, ek="in"),
               turkce.liste([ik.satici_unvani(x) for x in bilerek]),
               "toplam indirimler içindeki payı"
               if (oran or {}).get("oran") is not None else "niteliği"),
            girinti=1)
        b.paragraf(
            "306 Sıra No’lu Vergi Usul Kanunu Genel Tebliğinde belirtildiği "
            "üzere, sahte belgenin bilerek kullanılması hâlinde kasıt unsuru "
            "oluştuğundan fiil Vergi Usul Kanunu’nun 359. maddesi kapsamında "
            "değerlendirilmekte; bu belgeleri bilerek kullandığı sonucuna "
            "varılan mükellefler için vergi suçu raporu düzenlenmesi, "
            "haklarında Cumhuriyet Savcılığına suç duyurusunda bulunulması ve "
            "vergi ziyaına sebebiyet verilmiş olması hâlinde 344. madde "
            "uyarınca üç kat vergi ziyaı cezası kesilmesi gerekmektedir.",
            girinti=1)
    else:
        b.paragraf(
            "%s tarafından düzeltme beyannamesi verilerek faturalarda yer alan "
            "katma değer vergisi tutarlarının indirimlerden çıkarılmış olması, "
            "maliyet yönüyle eleştirilecek bir hususun bulunmadığı kanaatimizi "
            "güçlendirmiştir." % M(kunye, buyuk=True), girinti=1)
        b.paragraf(
            "Ticari hayatın olağan akışı içinde mal ve hizmet satışı yapan "
            "kişiler kendilerine ait olmayan belgeleri düzenleyerek karşı "
            "tarafa verebilmekte, mükelleflerin her zaman kendilerine verilen "
            "faturaları denetleme imkânı bulunmamaktadır. İnceleme sırasında "
            "söz konusu faturaların %s tarafından bilerek kullanıldığına dair "
            "herhangi bir delile rastlanılmamıştır." % M(kunye), girinti=1)
        b.paragraf(
            "306 Sıra No’lu Vergi Usul Kanunu Genel Tebliğinde yapılan "
            "açıklamalar dikkate alındığında, kasıt unsuru oluşmadığından "
            "fiilin Vergi Usul Kanunu’nun 359. maddesi kapsamında "
            "değerlendirilmesine ve bu konuda %s hakkında suç duyurusunda "
            "bulunulmasına gerek bulunmamaktadır." % M(kunye), girinti=1)

    b.baslik("4.3- %s ve %s Yönünden Yapılan Değerlendirme"
             % (ik.gelir_vergisi_adi(kunye).title(),
                ik.gecici_vergi_adi(kunye).title()), duzey=2)
    b.paragraf(
        "%s söz konusu faturalarda gösterilen mal ve hizmetleri gerçekten "
        "aldığı, faturaları bilmeden kullandığı kabul edildiğinden, %s "
        "matrahları aynen kabul edilmiş olup 306 Sıra No’lu Vergi Usul Kanunu "
        "Genel Tebliği gereği kaçakçılık suçu yönünden işlem "
        "yapılmayacaktır."
        % (M(kunye, buyuk=True, ek="in"),
           ik.gelir_vergisi_adi(kunye)), girinti=1)


# ------------------------------------------------------------------ 5) sonuc
def _sonuc(b, inceleme, kunye, donemler, bilerek, ziya_matrahi):
    M = ik.mukellef_sozu
    b.baslik("5- SONUÇ", duzey=1)
    b.paragraf(
        "%s %s mükellefi %s’nin %s ilişkin hesaplarının, sahte belge "
        "düzenlediğine "
        "ilişkin tespit bulunan mükelleflerden ticari mal alışlarına ilişkin "
        "olarak (sahte belge kullanımı nedeniyle) vergi kanunları yönünden "
        "sınırlı olarak incelenmesi sonucunda;"
        % (ik.vergi_dairesi(inceleme.get("vergi_dairesi"), ek="in"),
           ik.mukellef_kimligi(inceleme, kunye),
           ik.mukellef_adi(inceleme, kunye),
           _donem_ifadesi(kunye, donemler, "yonelme")), girinti=1)
    if bilerek:
        maddeler = [
            "Raporun 4.1. bölümünde belirtildiği üzere, söz konusu faturalara "
            "ait katma değer vergisi tutarları beyanlardan çıkarılmış "
            "olduğundan tarh edilecek bir katma değer vergisi bulunmadığı,",
            "Raporun 4.2. bölümünde belirtildiği üzere, söz konusu belgelerin "
            "bilerek kullanıldığı ve kasıt unsurunun oluştuğu; bu nedenle "
            "213 sayılı Vergi Usul Kanunu’nun 344. maddesi uyarınca %s TL "
            "vergi ziyaına konu tutar üzerinden ÜÇ KAT vergi ziyaı cezası "
            "kesilmesi gerektiği," % _tl(ziya_matrahi),
            "Aynı Kanun’un 359. maddesi kapsamında %s hakkında vergi suçu "
            "raporu düzenlenerek Cumhuriyet Savcılığına suç duyurusunda "
            "bulunulması gerektiği," % ik.mukellef_sozu(kunye),
            "Raporun 4.3. bölümünde belirtildiği üzere, %s ve %s yönünden "
            "yapılacak bir işlem bulunmadığı,"
            % (ik.gelir_vergisi_adi(kunye).title(),
               ik.gecici_vergi_adi(kunye).title()),
        ]
    else:
        maddeler = [
            "Raporun 4.1. bölümünde belirtildiği üzere, Katma Değer Vergisi ve "
            "Vergi Usul Kanunu’nun 359. maddesi yönünden yapılacak bir işlem "
            "bulunmadığı,",
            "Raporun 4.3. bölümünde belirtildiği üzere, %s ve %s yönünden "
            "yapılacak bir işlem bulunmadığı,"
            % (ik.gelir_vergisi_adi(kunye).title(),
               ik.gecici_vergi_adi(kunye).title()),
        ]
    b.madde_listesi(maddeler, numarali=True)
    b.paragraf("kanaat ve sonuçlarına varılmıştır.", girinti=1)


# ------------------------------------------------------------------- uretim
def rapor_uret(inceleme, kunye, yillar, sonuc, calisma, bulgular=None,
               karsilastirmalar=None, yil=None):
    """Duzeltme kabul raporu taslagini uretir ve `Belge` dondurur."""
    kunye = ik.normalize(kunye)
    calisma = calisma or {}
    donemler = dolu_donemler(sonuc)
    if yil:
        donemler = [d for d in donemler if d["yil"] == yil]
    mukellef_vkn = (calisma.get("mukellef") or {}).get("vkn_tckn")
    liste = F.normalize(calisma.get("faturalar"), mukellef_vkn)
    saticilar = calisma.get("saticilar") or {}
    satici_satirlari = F.satici_ozeti(liste, saticilar)
    if yil:
        satici_satirlari = [s for s in satici_satirlari
                            if any(d.get("yil") == yil
                                   for d in (s.get("yil_dokumu") or []))]
    oran = F.duzeltme_kabul_orani(liste, sonuc, saticilar)

    b = Belge()
    b.paragraf("VERGİ TEKNİĞİ RAPORU", kalin=True, hiza="orta")
    b.bos_satir()
    _giris(b, inceleme, kunye, donemler, satici_satirlari)
    _tespitler(b, kunye, donemler, satici_satirlari, liste, karsilastirmalar)
    _ilgili_mevzuat(b)
    _degerlendirmeler(b, kunye, satici_satirlari, oran, inceleme)
    _sonuc(b, inceleme, kunye, donemler,
           F.bilerek_kullananlar(satici_satirlari),
           sum(x.get("liste_kdv") or 0.0 for x in satici_satirlari))
    return b


def rapor_yillari(sonuc):
    """Rapor duzenlenecek yillar (sahte belge raporuyla ayni olcut)."""
    from .sahte_belge_raporu import rapor_yillari as _y
    return _y(sonuc)


def dosya_adi(inceleme, yil=None):
    ad = "".join(c for c in (inceleme.get("ad_unvan") or "rapor")
                 if c.isalnum() or c in " -_").strip() or "rapor"
    if yil:
        ad = "%s_%s" % (yil, ad)
    return ("Duzeltme_kabul_raporu_taslagi_%s.docx" % ad).replace(" ", "_")


def paket_adi(inceleme):
    ad = "".join(c for c in (inceleme.get("ad_unvan") or "rapor")
                 if c.isalnum() or c in " -_").strip() or "rapor"
    return ("Duzeltme_kabul_raporlari_%s.zip" % ad).replace(" ", "_")
