"""Sahte belge kullanma raporu taslagi (5 bolumlu vergi inceleme raporu duzeni).

Bolumler:
    1. Giris
    2. Usul Incelemeleri
    3. Hesap Incelemeleri
    4. Tespit ve Tenkit Edilen Hususlar (re'sen takdir nedeni, veriler,
       yasal mevzuat, degerlendirme)
    5. Sonuc

Uretilen belge bir TASLAKTIR. Ozellikle 4d ve 5. bolumdeki nitelendirme,
inceleme elemanina aittir; buradaki metin girilen veriden turetilmis bir ilk
yazimdir. Satici bazinda "bilerek / bilmeden kullanma" secilmemisse rapor yine
uretilir, ama o satici icin ceza katsayisi bir kat varsayilir ve belgede bu
durum acikca yazilir.
"""
from datetime import datetime

from . import faturalar as F
from . import inceleme_kunyesi as ik
from . import mevzuat, turkce
from .belge_docx import Belge
from .belge_docx import TABLO_PUNTOSU
from .tutanak import (_kapsam, _yillar_metni, belgeye_giren_bulgular,
                      beyan_dokum_tablosu, dolu_donemler, tarhiyat_toplami)

_tl = turkce.tl


def _var(deger, esik=0.005):
    return abs(float(deger or 0.0)) > esik


def _donem_adi(d):
    return "%s/%s" % (d["yil"], d["ay_adi"])


def _kapsam_cumlesi(secim):
    """"Kapsamda" / "Kapsamda değil" secimini cumleye cevirir."""
    if secim == "Kapsamda":
        return "kapsamındadır"
    if secim == "Kapsamda değil":
        return "kapsamında değildir"
    return "[kapsamı belirtilmedi]"


# ------------------------------------------------------------------ 1. giris
def _giris(b, inceleme, kunye, donemler):
    b.baslik("1. GİRİŞ", 1)

    b.paragraf(
        "%s %s vergi kimlik numaralı mükellefi %s; %s adresinde \"%s\" "
        "faaliyeti ile iştigal etmektedir. Mükellef e-Tebligat uygulaması "
        "%s. Mükellef e-Defter ve e-Fatura uygulamaları %s."
        % (turkce.ilgi(inceleme.get("vergi_dairesi") or "[Vergi dairesi]"),
           inceleme.get("vkn_tckn") or "[VKN]",
           inceleme.get("ad_unvan") or "[Mükellef unvanı]",
           inceleme.get("adres") or "[Adres]",
           ik.deger(kunye, "faaliyet_konusu"),
           _kapsam_cumlesi(kunye.get("e_tebligat")),
           _kapsam_cumlesi(kunye.get("e_defter"))),
        girinti=1)

    gerekce = kunye.get("inceleme_gerekce") or ""
    if gerekce == "İhbar":
        dayanak = ("Söz konusu mükellef hakkında yapılan ihbar üzerine, 213 "
                   "sayılı Vergi Usul Kanunu'nun 134 ve müteakip maddeleri "
                   "uyarınca vergi incelemesi yapılması uygun görülmüş")
    elif gerekce == "Karşıt inceleme":
        dayanak = ("Yürütülmekte olan karşıt inceleme kapsamında, 213 sayılı "
                   "Vergi Usul Kanunu'nun 134 ve müteakip maddeleri uyarınca "
                   "mükellef hakkında vergi incelemesi yapılmasına karar verilmiş")
    elif gerekce == "Risk analizi":
        dayanak = ("Risk analizi çalışmaları sonucunda mükellefin vergi "
                   "beyannameleri incelemeye alınmış; 213 sayılı Vergi Usul "
                   "Kanunu'nun 134 ve müteakip maddeleri uyarınca inceleme "
                   "yapılması uygun görülmüş")
    else:
        dayanak = ("213 sayılı Vergi Usul Kanunu'nun 134 ve müteakip maddeleri "
                   "uyarınca mükellef hakkında vergi incelemesi yapılması uygun "
                   "görülmüş")
    b.paragraf(
        "%s; %s tarih ve %s sayılı görevlendirme yazısı ile incelemeye "
        "başlanılmıştır."
        % (dayanak, ik.deger(kunye, "gorevlendirme_tarihi", "tarih"),
           ik.deger(kunye, "gorevlendirme_no", "sayı")),
        girinti=1)

    b.paragraf(
        "Mükellefin %s ilişkin katma değer vergisi hesap ve işlemleri, ibraz "
        "edilen yasal defter ve belgeler ile vergi dairesinden temin edilen "
        "kayıtlara dayanılarak %s dönemi itibarıyla incelenmiş; inceleme "
        "neticesinde tespit ve tenkit edilen hususlara raporun ilerleyen "
        "bölümlerinde yer verilmiştir."
        % (_yillar_metni(donemler), _kapsam(donemler)),
        girinti=1)


# ------------------------------------------------------------------- 2. usul
def _usul(b, kunye, bulgular, donemler):
    b.baslik("2. USUL İNCELEMELERİ", 1)

    b.baslik("2.1. Defter Tasdik ve İbraz Durumu", 2)
    tasdik = kunye.get("defter_tasdik") or ""
    if tasdik == "Usulüne uygun":
        b.paragraf("Mükellefin incelenen döneme ait yasal defterlerinin usulüne "
                   "uygun şekilde tasdik ettirildiği ve incelemeye ibraz edildiği "
                   "tespit edilmiştir.", girinti=1)
    else:
        b.paragraf("213 sayılı Vergi Usul Kanunu'nun 221. maddesi uyarınca tasdik "
                   "ettirilmesi gereken defterler yönünden \"%s\" durumu tespit "
                   "edilmiştir." % (tasdik or "[belirtilmedi]"), girinti=1)
    ibraz = kunye.get("defter_ibraz") or ""
    if ibraz and ibraz != "İbraz edildi":
        b.paragraf("Defter ve belgelerin ibrazı yönünden \"%s\" durumu söz "
                   "konusudur." % ibraz, girinti=1)

    b.baslik("2.2. Beyanname Durumu", 2)
    beyan_durumu = kunye.get("beyanname_durumu") or ""
    if beyan_durumu == "Süresinde verilmiş":
        b.paragraf("Mükellefin incelenen döneme ait katma değer vergisi "
                   "beyannamelerini yasal süreler içinde vergi dairesine ibraz "
                   "ettiği görülmüştür.", girinti=1)
    else:
        b.paragraf("Mükellefin incelenen döneme ait katma değer vergisi "
                   "beyannamelerinin verilmesi yönünden \"%s\" durumu tespit "
                   "edilmiştir." % (beyan_durumu or "[belirtilmedi]"), girinti=1)

    b.baslik("2.3. e-Defter / e-Fatura Yükümlülüğü", 2)
    if (kunye.get("e_defter") or "") == "Kapsamda":
        b.paragraf("Mükellef, 213 sayılı Vergi Usul Kanunu kapsamında yayımlanan "
                   "tebliğler çerçevesinde e-Defter ve e-Fatura uygulamalarına "
                   "dahildir.", girinti=1)
    else:
        b.paragraf("Mükellef, ilgili dönem itibarıyla e-Defter ve e-Fatura "
                   "uygulamalarına dahil olma şartlarını taşımamaktadır.", girinti=1)

    usulsuzluk = kunye.get("usulsuzluk") or "Yok"
    if usulsuzluk != "Yok":
        b.baslik("2.4. Usulsüzlük", 2)
        madde = ("353. maddesi" if "Özel" in usulsuzluk
                 else "351 ve 352. maddeleri")
        b.paragraf("Yapılan usul incelemesinde tespit edilen hususlar nedeniyle, "
                   "213 sayılı Vergi Usul Kanunu'nun %s uyarınca mükellef adına "
                   "\"%s\" uygulanması gerekmektedir."
                   % (madde, usulsuzluk), girinti=1)

    for satir in ik.satirlar(kunye, "usul_notu"):
        b.paragraf(satir, girinti=1)

    uyumsuz = belgeye_giren_bulgular(bulgular, donemler)
    if uyumsuz:
        b.paragraf("Beyan edilen tutarlar üzerinde yapılan aritmetik denetimde "
                   "aşağıdaki hususlar tespit edilmiştir:", girinti=1)
        b.madde_listesi([x["mesaj"] for x in uyumsuz])


# ------------------------------------------------------------------ 3. hesap
def _hesap(b, donemler):
    b.baslik("3. HESAP İNCELEMELERİ", 1)
    b.paragraf("Mükellefin incelenen döneme ilişkin katma değer vergisi "
               "beyannameleri ve eki tablolar incelenmiş olup beyannameye "
               "ilişkin döküm aşağıda yer almaktadır.", girinti=1)
    beyan_dokum_tablosu(b, donemler)


# ------------------------------------------------------------------ 4. tespit
def _tespit(b, kunye, liste, satici_satirlari, donemler):
    b.baslik("4. TESPİT VE TENKİT EDİLEN HUSUSLAR", 1)

    # ---- 4.1 re'sen takdir nedeni
    b.baslik("4.1. Re'sen Takdir Nedeni", 2)
    kod = ik.resen_madde_kodu(kunye)
    if kod == "30/4":
        b.paragraf("Mükellef tarafından yasal defter ve belgelerinin incelemeye "
                   "ibraz edilmemesi/ihticaca salih bulunmaması nedeniyle 213 "
                   "sayılı Vergi Usul Kanunu'nun 30/4. maddesi hükmü gereğince "
                   "re'sen vergi tarhiyatı yoluna gidilmesi gerekmektedir.",
                   girinti=1)
    elif kod == "30/7":
        b.paragraf("Yapılan inceleme kapsamında mükellefin kayıt ve beyanlarında "
                   "saptanan aykırılıklar nedeniyle 213 sayılı Vergi Usul "
                   "Kanunu'nun 30/7. maddesi uyarınca re'sen tarhiyat yapılması "
                   "gerekmektedir.", girinti=1)
    else:
        b.paragraf("Yapılan inceleme neticesinde tespit edilen hususlar "
                   "doğrultusunda, mükellefin incelenen döneme ait katma değer "
                   "vergisi beyannamelerinin gerçek durumu yansıtmadığı "
                   "anlaşılmıştır. Bu itibarla 213 sayılı Vergi Usul Kanunu'nun "
                   "30/6. maddesi hükmü gereğince re'sen tarhiyat yapılması "
                   "gerekmektedir.", girinti=1)

    # ---- 4.2 re'sen takdir verileri
    b.baslik("4.2. Re'sen Takdire Esas Alınan Veriler", 2)
    if not satici_satirlari:
        b.paragraf("[Sahte belge düzenlediği tespit edilen mükelleflere ait "
                   "fatura listesi girilmediği için bu bölüm boş bırakılmıştır.]",
                   girinti=1, italik=True)
        return

    toplam_kdv = sum(s["kdv"] for s in satici_satirlari)
    toplam_matrah = sum(s["matrah"] for s in satici_satirlari)
    b.paragraf(
        "İnceleme kapsamında, mükellef tarafından aşağıda unvan ve vergi kimlik "
        "numaraları belirtilen mükelleflerden temin edilerek yasal defterlere "
        "kaydedilen ve katma değer vergisi indirimine konu edilen toplam %s TL "
        "tutarlı faturaların, gerçek bir mal teslimi veya hizmet ifasına "
        "dayanmadığı tespit edilmiştir. Söz konusu belgelere ait toplam %s TL "
        "katma değer vergisi haksız olarak indirim konusu yapılmıştır."
        % (_tl(toplam_matrah), _tl(toplam_kdv)), girinti=1)

    b.baslik("4.2.1. Sahte Belge Düzenleyicileri", 2)
    satici_tablo = []
    for s in satici_satirlari:
        satici_tablo.append([
            s["unvan"] or "[unvan girilmedi]",
            s["vkn"] or "—",
            s["vtr_no"] or "—",
            str(s["adet"]),
            _tl(s["matrah"]),
            _tl(s["kdv"]),
            s["kullanma"],
        ])
    satici_tablo.append(["TOPLAM", "", "", str(sum(s["adet"] for s in satici_satirlari)),
                         _tl(toplam_matrah), _tl(toplam_kdv), ""])
    b.tablo(["Düzenleyici Unvanı", "VKN", "VTR No", "Fatura", "Matrah", "KDV",
             "Kullanma Durumu"], satici_tablo,
            hizalar=["sol", "sol", "sol", "sag", "sag", "sag", "sol"],
            oranlar=[2, 1.2, 1, 0.7, 1.2, 1.2, 1.3],
            buyukluk=TABLO_PUNTOSU, toplam_satiri=True)

    for s in satici_satirlari:
        parcalar = []
        if s["vtr_no"] or s["vtr_tarihi"]:
            parcalar.append("hakkında %s tarih ve %s sayılı vergi tekniği raporu "
                            "düzenlenmiş" % (s["vtr_tarihi"] or "[tarih]",
                                             s["vtr_no"] or "[sayı]"))
        if s["ozel_esaslar"]:
            parcalar.append("%s tarihi itibarıyla özel esaslar kapsamına alınmış"
                            % s["ozel_esaslar"])
        if parcalar or s["not"]:
            cumle = "%s (VKN: %s)" % (s["unvan"] or "[unvan girilmedi]", s["vkn"] or "—")
            if parcalar:
                cumle += " " + turkce.liste(parcalar) + "tır."
            b.paragraf(cumle, girinti=1)
            for satir in str(s["not"] or "").split("\n"):
                if satir.strip():
                    b.paragraf(satir.strip(), girinti=1)

    b.baslik("4.2.2. Faturalara İlişkin Döküm", 2)
    fatura_tablo = []
    for f in liste:
        if not f.get("dahil"):
            continue
        fatura_tablo.append([
            f.get("satici_vkn") or "—",
            f.get("fatura_no") or "—",
            f.get("tarih") or "—",
            ("%s/%02d" % (f.get("kayit_yil"), f.get("kayit_ay"))
             if f.get("kayit_yil") and f.get("kayit_ay") else "—"),
            _tl(f.get("matrah")), _tl(f.get("kdv")), _tl(f.get("toplam")),
        ])
    fatura_tablo.append(["TOPLAM", "", "", "", _tl(toplam_matrah), _tl(toplam_kdv),
                         _tl(sum(f.get("toplam") or 0.0 for f in liste if f.get("dahil")))])
    b.tablo(["Satıcı VKN", "Fatura No", "Fatura Tarihi", "Kayıt Dönemi",
             "Matrah", "KDV", "Genel Toplam"], fatura_tablo,
            hizalar=["sol", "sol", "sol", "sol", "sag", "sag", "sag"],
            oranlar=[1.2, 1.5, 1.1, 1, 1.2, 1.1, 1.2],
            buyukluk=TABLO_PUNTOSU, toplam_satiri=True)


def _mevzuat_bolumu(b, kunye):
    b.baslik("4.3. Yasal Mevzuat", 2)
    anahtarlar = list(mevzuat.SAHTE_BELGE_MADDELERI)
    resen = mevzuat.RESEN_MADDELERI.get(ik.resen_madde_kodu(kunye))
    if resen:
        anahtarlar.insert(2, resen)
    anahtarlar.append("vuk_359")
    for baslik, metin in mevzuat.maddeler(anahtarlar):
        b.paragraf(baslik, kalin=True, hiza="sol", aralik_once=120, aralik_sonra=40)
        b.paragraf("“%s”" % metin, girinti=1, italik=True)


def _degerlendirme(b, satici_satirlari, ceza):
    b.baslik("4.4. Değerlendirme", 2)
    if not satici_satirlari:
        b.paragraf("[Değerlendirme, fatura listesi girildikten sonra "
                   "üretilecektir.]", girinti=1, italik=True)
        return

    b.paragraf(
        "Yapılan inceleme ve araştırmalar neticesinde, yukarıda belirtilen "
        "mükellefler tarafından düzenlenen faturaların gerçek bir ticari "
        "faaliyete dayanmadığı ve bu belgelerin sahte belge niteliği taşıdığı "
        "kanaatine varılmıştır. 3065 sayılı Katma Değer Vergisi Kanunu'nun 29 "
        "ve 34. maddeleri ile Katma Değer Vergisi Genel Uygulama Tebliği'nin "
        "ilgili bölümü uyarınca, gerçek bir teslim veya hizmet ifasına "
        "dayanmayan faturalarda gösterilen katma değer vergisinin indirim "
        "konusu yapılması mümkün bulunmadığından, söz konusu indirimler "
        "reddedilmiştir.", girinti=1)

    bilerek = [s for s in satici_satirlari if s["kullanma"] == "Bilerek kullanma"]
    bilmeden = [s for s in satici_satirlari if s["kullanma"] == "Bilmeden kullanma"]
    belirsiz = [s for s in satici_satirlari if s["kullanma"] == "Belirlenmedi"]

    if bilerek:
        b.paragraf(
            "%s tarafından düzenlenen belgeler yönünden; mükellefin söz konusu "
            "belgelerin sahte olduğunu bilerek kullandığı sonucuna varılmıştır. "
            "Bu fiil 213 sayılı Vergi Usul Kanunu'nun 359. maddesi kapsamında "
            "olduğundan, aynı Kanun'un 344. maddesi uyarınca vergi ziyaı "
            "cezasının üç kat olarak uygulanması ve mükellef hakkında Cumhuriyet "
            "Başsavcılığı'na suç duyurusunda bulunulması gerekmektedir."
            % turkce.liste(["%s (VKN: %s)" % (s["unvan"] or "[unvan girilmedi]",
                                              s["vkn"]) for s in bilerek]),
            girinti=1)
    if bilmeden:
        b.paragraf(
            "%s tarafından düzenlenen belgeler yönünden; mükellefin belgelerin "
            "sahte olduğunu bilmeden kullandığı değerlendirilmiştir. Bu belgelere "
            "ait katma değer vergisi indirimi reddedilmekle birlikte, vergi ziyaı "
            "cezasının 213 sayılı Vergi Usul Kanunu'nun 344. maddesi uyarınca bir "
            "kat olarak uygulanması gerekmektedir."
            % turkce.liste(["%s (VKN: %s)" % (s["unvan"] or "[unvan girilmedi]",
                                              s["vkn"]) for s in bilmeden]),
            girinti=1)
    if belirsiz:
        b.paragraf(
            "[%s tarafından düzenlenen belgeler yönünden bilerek/bilmeden "
            "kullanma değerlendirmesi yapılmamıştır. Aşağıdaki ceza hesabında bu "
            "belgeler için ceza bir kat olarak alınmıştır; nitelendirme "
            "yapıldıktan sonra bu bölümün ve ceza tablosunun gözden geçirilmesi "
            "gerekir.]"
            % turkce.liste(["%s (VKN: %s)" % (s["unvan"] or "[unvan girilmedi]",
                                              s["vkn"]) for s in belirsiz]),
            girinti=1, italik=True)

    if _var(ceza["toplam"].get("tarh_diger")):
        b.paragraf(
            "Tarh edilmesi gereken verginin %s TL tutarındaki kısmı, sahte belge "
            "kullanımı dışındaki tespitlerden kaynaklanmaktadır; bu kısma ilişkin "
            "değerlendirme bu raporun konusu değildir."
            % _tl(ceza["toplam"]["tarh_diger"]), girinti=1)


# ------------------------------------------------------------------ 5. sonuc
def _sonuc(b, kunye, sonuc, donemler, ceza):
    b.baslik("5. SONUÇ", 1)
    tarhiyatli = [d for d in donemler if _var(d["tarhiyat"]["toplam_fark"])]
    toplam = tarhiyat_toplami(tarhiyatli)

    if not tarhiyatli:
        b.paragraf("Yapılan inceleme sonucunda re'sen tarhı gereken bir vergi "
                   "farkı hesaplanmamıştır.", girinti=1)
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
    b.baslik("5.1. Tarhiyat Özeti", 2)
    b.tablo(["Dönem", "Ödenecek KDV (Beyan)", "Ödenecek KDV (Olması Gereken)",
             "Re'sen Tarhı Gereken", "Aranması Gereken", "Toplam Fark"], tablo,
            hizalar=["sol"] + ["sag"] * 5, oranlar=[1.1, 1, 1.1, 1, 1, 1],
            buyukluk=TABLO_PUNTOSU, toplam_satiri=True)

    if ceza["satirlar"]:
        b.baslik("5.2. Vergi Ziyaı Cezası", 2)
        b.paragraf(
            "Tarh edilmesi gereken vergi, dönem dönem, ilgili faturaları "
            "düzenleyen mükellefler bakımından yapılan bilerek/bilmeden kullanma "
            "nitelendirmesine göre paylaştırılmıştır. Bir dönemde reddedilen "
            "katma değer vergisi ile tarh edilmesi gereken vergi eşit "
            "olmayabilir; devir zinciri reddin bir kısmını soğurabildiğinden, "
            "paylaştırma tarh edilen tutar üzerinden yapılmıştır.", girinti=1)
        ceza_tablo = []
        for s in ceza["satirlar"]:
            ceza_tablo.append([
                "%s/%s" % (s["yil"], s["ay_adi"]),
                _tl(s["tarh"]), _tl(s["pay_bilerek"]), _tl(s["ceza_bilerek"]),
                _tl(s["pay_bilmeden"] + s["pay_belirsiz"]),
                _tl(s["ceza_bilmeden"] + s["ceza_belirsiz"]),
                _tl(s["ceza_toplam"])])
        t = ceza["toplam"]
        ceza_tablo.append(["TOPLAM", _tl(t["tarh"]), _tl(t["pay_bilerek"]),
                           _tl(t["ceza_bilerek"]),
                           _tl(t["pay_bilmeden"] + t["pay_belirsiz"]),
                           _tl(t["ceza_bilmeden"] + t["ceza_belirsiz"]),
                           _tl(t["ceza_toplam"])])
        b.tablo(["Dönem", "Tarh Edilecek KDV", "Bilerek Pay", "Ceza (3 kat)",
                 "Bilmeden Pay", "Ceza (1 kat)", "Ceza Toplamı"], ceza_tablo,
                hizalar=["sol"] + ["sag"] * 6,
                oranlar=[1, 1.2, 1.1, 1.1, 1.1, 1.1, 1.2],
                buyukluk=TABLO_PUNTOSU, toplam_satiri=True)

    b.baslik("5.3. Sonuç ve Öneri", 2)
    b.paragraf(
        "Yukarıda açıklanan nedenlerle, mükellefin incelenen dönemlere ait katma "
        "değer vergisi beyanlarında toplam %s TL vergi farkı saptanmış olup bu "
        "tutarın 213 sayılı Vergi Usul Kanunu'nun %s. maddesi uyarınca re'sen "
        "tarh edilmesi, tarh edilecek vergi üzerinden aynı Kanun'un 344. maddesi "
        "uyarınca %s tutarında vergi ziyaı cezası kesilmesi ve 112. madde "
        "uyarınca gecikme faizi hesaplanması gerekmektedir."
        % (_tl(toplam.get("toplam_fark")), ik.resen_madde_kodu(kunye),
           "%s TL" % _tl(ceza["toplam"].get("ceza_toplam"))
           if ceza["satirlar"] else "[hesaplanacak]"),
        girinti=1)

    if any(s["kullanma"] == "Bilerek kullanma" for s in
           (ceza.get("_saticilar") or [])):
        b.paragraf("Ayrıca 213 sayılı Vergi Usul Kanunu'nun 359. maddesi "
                   "kapsamındaki fiil nedeniyle mükellef hakkında Cumhuriyet "
                   "Başsavcılığı'na suç duyurusunda bulunulması gerekmektedir.",
                   girinti=1)

    usulsuzluk = kunye.get("usulsuzluk") or "Yok"
    if usulsuzluk != "Yok":
        b.paragraf("Usul incelemeleri bölümünde tespit edilen hususlar nedeniyle "
                   "mükellef adına \"%s\" uygulanması gerekmektedir." % usulsuzluk,
                   girinti=1)

    if ik.secim_mi(kunye, "uzlasma_notu", "Evet"):
        b.paragraf("Mükellefin yasal süreler içinde tarhiyat sonrası uzlaşma "
                   "talep etme hakkı saklıdır.", girinti=1)
    if ik.secim_mi(kunye, "duzeltme_notu", "Evet"):
        b.paragraf("Yukarıda belirtilen farklar doğrultusunda ilgili dönem katma "
                   "değer vergisi beyannamelerinin 213 sayılı Vergi Usul "
                   "Kanunu'nun 116 ve müteakip maddeleri çerçevesinde "
                   "düzeltilmesi gerekmektedir.", girinti=1)

    b.bos_satir()
    b.imza_bloklari([(ik.deger(kunye, "eleman_unvan", "unvan"),
                      ik.deger(kunye, "eleman_ad", "ad soyad"))])


# ---------------------------------------------------------------------- giris
def rapor_uret(inceleme, kunye, yillar, sonuc, calisma, bulgular=None):
    """Sahte belge kullanma raporu taslagini uretir."""
    kunye = ik.normalize(kunye)
    donemler = dolu_donemler(sonuc)
    mukellef_vkn = (calisma.get("mukellef") or {}).get("vkn_tckn")
    liste = F.normalize(calisma.get("faturalar"), mukellef_vkn)
    saticilar = calisma.get("saticilar") or {}
    satici_satirlari = F.satici_ozeti(liste, saticilar)
    ceza = F.ceza_dagilimi(liste, saticilar, sonuc)
    ceza["_saticilar"] = satici_satirlari

    b = Belge()
    b.baslik("VERGİ İNCELEME RAPORU", 1)
    b.paragraf("(Sahte Belge Kullanma — Taslak)", hiza="orta", italik=True,
               aralik_sonra=60)
    b.paragraf("Rapor No: %s          Tarih: %s"
               % (ik.deger(kunye, "rapor_no", "rapor no"), _bugun()),
               hiza="orta", aralik_sonra=240)

    _giris(b, inceleme, kunye, donemler)
    _usul(b, kunye, bulgular, donemler)
    _hesap(b, donemler)
    _tespit(b, kunye, liste, satici_satirlari, donemler)
    _mevzuat_bolumu(b, kunye)
    _degerlendirme(b, satici_satirlari, ceza)
    _sonuc(b, kunye, sonuc, donemler, ceza)

    b.bos_satir()
    b.paragraf("Bu belge %s tarihinde KDV İnceleme Çalışması uygulamasıyla taslak "
               "olarak üretilmiştir; imzaya hazır nihai belge değildir."
               % _bugun(), italik=True, hiza="orta", buyukluk=9)
    return b


def _bugun():
    return datetime.now().strftime("%d.%m.%Y")


def dosya_adi(inceleme):
    ad = "".join(c for c in (inceleme.get("ad_unvan") or "rapor")
                 if c.isalnum() or c in " -_").strip() or "rapor"
    return ("Sahte_belge_raporu_taslagi_%s.docx" % ad).replace(" ", "_")
