"""Sahte belge kullanma vergi inceleme raporu taslagi.

Duzen, kullanicinin gonderdigi iki ornek rapordan cikarilmistir (biri
bilmeden, biri bilerek kullanma):

    I-   GİRİŞ
    II-  USUL İNCELEMELERİ          A- Genel Usulsüzlük
                                    B- Özel Usulsüzlük Cezası (VUK mük. 355)
    III- HESAP İNCELEMELERİ         kanuni beyan / düzeltme / son hal tabloları
    IV-  ELEŞTİRİLEN HUSUSLAR       A- Re'sen Takdir Nedeni
                                    B- Re'sen Takdir Verileri (satıcı başına B.1, B.2…)
                                    C- İlgili Mevzuat
                                    D- Tespit Edilen Hususların Değerlendirilmesi
                                    Ç- Tarhiyat Öncesi Uzlaşma
    V-   SONUÇ                      numaralı maddeler + tarhiyat tablosu

Bilerek / bilmeden ayrimi metnin bircok yerini birden degistirir: vergi ziyai
cezasinin kati, vergi sucu raporu ve suc duyurusu, tarhiyat oncesi uzlasma
kapsami. Bu yuzden ayrim tek bir yerde cozulur ve butun bolumler ondan okur.

Uretilen belge TASLAKTIR; nitelendirme inceleme elemanina aittir.
"""
from . import faturalar as F
from . import inceleme_kunyesi as ik
from . import mevzuat, turkce
from .belge_docx import TABLO_PUNTOSU, Belge
from .tutanak import (BEYAN_DOKUM_KOLONLARI, belgeye_giren_bulgular,
                      beyan_dokum_tablosu, dolu_donemler,
                      satici_veri_maddeleri, tarhiyat_toplami)

_tl = turkce.tl


def _var(deger, esik=0.005):
    return abs(float(deger or 0.0)) > esik


def _donem_adi(d):
    return "%s/%s" % (d["yil"], d["ay_adi"])


def _donem_ifadesi(kunye, donemler, hal="yalin"):
    """"2023 hesap dönemi" / "2022 ve 2023 takvim yılları" gibi ifadeler.

    Sirketlerde donem "hesap donemi", gercek kisilerde "takvim yili" diye
    anilir; ikisi ayni eki de almaz. Bu yuzden ifade tek yerden uretilir.
    """
    yillar = sorted({d["yil"] for d in donemler})
    if not yillar:
        return "[yıl] %s" % ik.donem_adi(kunye, False, hal)
    return "%s %s" % (turkce.liste(yillar),
                      ik.donem_adi(kunye, len(yillar) > 1, hal))


def _madde_numaralari_metni(numaralar):
    """[6, 8, 10] -> "6., 8. ve 10." ; bos liste kirmizi tutucu birakir."""
    if not numaralar:
        return "[ilgili]"
    if len(numaralar) == 1:
        return "%d." % numaralar[0]
    return "%s ve %d." % (", ".join("%d." % n for n in numaralar[:-1]),
                          numaralar[-1])


def _bilerek_mi(satici_satirlari):
    """Satıcılardan herhangi biri bilerek kullanma sayilmis mi."""
    return any(s["kullanma"] == "Bilerek kullanma" for s in satici_satirlari)


# --------------------------------------------------------------------- I. giris
def _yilin_is_emirleri(kunye, yil):
    """Is emri listesini rapora konu yila daraltir.

    Birden cok yil incelenirken her yilin raporunda yalnizca o yila ait
    gorevlendirme yazilari yer almalidir. Donem sutununda yil yaziliysa
    secim ona gore yapilir; hicbir satir eslesmezse liste oldugu gibi
    kalir - eksik bilgi yuzunden tablo bosalmasin.
    """
    emirler = ik.is_emirleri(kunye)
    if yil is None:
        return emirler
    eslesen = [e for e in emirler if str(yil) in (e.get("donem") or "")]
    return eslesen or emirler


def _giris(b, inceleme, kunye, donemler, satici_satirlari, yil=None):
    b.baslik("I- GİRİŞ", 1)
    M = ik.mukellef_sozu

    tanitim = (
        "%s %s vergi kimlik numaralı mükellefi %s (Raporun ilerleyen "
        "bölümlerinde %s olarak anılacaktır), “%s” adresinde “%s” faaliyeti "
        "ile iştigal etmektedir. %s Vergi Usul Kanununun 107/A maddesi "
        "kapsamında e-tebligata tabidir."
        % (inceleme.get("vergi_dairesi") or "[Vergi dairesi]",
           inceleme.get("vkn_tckn") or "[VKN]",
           ik.mukellef_adi(inceleme, kunye),
           M(kunye), inceleme.get("adres") or "[Adres]",
           ik.deger(kunye, "faaliyet_konusu"), M(kunye, buyuk=True)))
    if ik.secim_mi(kunye, "e_defter", "Kapsamda"):
        tanitim += " %s e-Defter ve e-Fatura uygulamaları kapsamındadır." % M(kunye, buyuk=True)
    b.paragraf(tanitim, girinti=1)

    emirler = _yilin_is_emirleri(kunye, yil)
    if emirler:
        b.paragraf(
            "T.C. Hazine ve Maliye Bakanlığı Vergi Denetim Kurulu %s iş "
            "emirleri ile %s incelenmesi istenen yıllar ve inceleme konusu "
            "aşağıdaki gibidir."
            % (ik.deger(kunye, "grup_baskanligi", "Denetim Daire Başkanlığının"),
               M(kunye, ek="in")),
            girinti=1)
        b.tablo(["Sıra No", "İş Emri Tarihi", "İş Emri Sayısı", "Dönemi", "Konusu"],
                [[str(i),
                  e["tarih"] or "[iş emri tarihi]",
                  e["sayi"] or "[iş emri sayısı]",
                  e["donem"] or "[dönemi]", e["konu"]]
                 for i, e in enumerate(emirler, 1)],
                hizalar=["orta", "orta", "sol", "orta", "sol"],
                oranlar=[0.5, 1, 2.2, 0.8, 1.5], buyukluk=TABLO_PUNTOSU)
    else:
        b.paragraf(
            "T.C. Hazine ve Maliye Bakanlığı Vergi Denetim Kurulu %s %s ile %s "
            "%s işlemlerinin “Sahte Belge Kullanma” gerekçesiyle sınırlı olarak "
            "incelenmesi istenmiştir."
            % (ik.deger(kunye, "grup_baskanligi", "Denetim Daire Başkanlığının"),
               ik.gorevlendirme_ifadesi(emirler),
               M(kunye, ek="in"), _donem_ifadesi(kunye, donemler)),
            girinti=1)

    if satici_satirlari:
        adlar = ["%s %s vergi kimlik numaralı mükellefi %s’den"
                 % (s["vergi_dairesi"] or "[Satıcının vergi dairesi]",
                    s["vkn"] or "[VKN]", ik.satici_unvani(s))
                 for s in satici_satirlari]
        b.paragraf(
            "İş emri gerekçelerinde; %s %s %s olan alışlarının sahte belge "
            "kullanma kapsamında sınırlı olarak incelenmesi gerektiği yer "
            "almaktadır."
            % (M(kunye, ek="in"), _donem_ifadesi(kunye, donemler, "bulunma"),
               turkce.liste(adlar)),
            girinti=1)

    for satir in ik.satirlar(kunye, "imzaya_davet"):
        b.paragraf(satir, girinti=1)

    b.paragraf(
        "%s %s ilişkin hesap ve işlemlerinin sınırlı olarak incelenmesi "
        "neticesinde Katma Değer Vergisi yönünden tespit ve tenkit edilen "
        "hususlar raporun izleyen bölümlerinde açıklanmıştır."
        % (M(kunye, buyuk=True, ek="in"),
           _donem_ifadesi(kunye, donemler, "yonelme")),
        girinti=1)


# ---------------------------------------------------------------- II. usul
def _usul(b, kunye, donemler, ouc):
    """II- USUL İNCELEMELERİ.

    Genel usulsuzluk basligi bilerek yok: defter tasdiki ve ibrazi tutanakta
    zaten tespit ediliyor, raporda ayri bir bolum acmak tekrar oluyordu.
    Bolum, varsa usul notu ve ozel usulsuzluk cezasindan olusur.
    """
    b.baslik("II- USUL İNCELEMELERİ", 1)

    for satir in ik.satirlar(kunye, "usul_notu"):
        b.paragraf(satir, girinti=1)

    if ouc and ouc["satirlar"]:
        _ozel_usulsuzluk(b, kunye, ouc)
    elif not ik.satirlar(kunye, "usul_notu"):
        b.paragraf("Usul yönünden tenkidi gerektiren bir husus tespit "
                   "edilmemiştir.", girinti=1)


def _ozel_usulsuzluk(b, kunye, ouc):
    """VUK muk. 355 — odemeleri tevsik etmeme fiili."""
    M = ik.mukellef_sozu
    b.baslik("A- Özel Usulsüzlük Cezası", 2)
    b.baslik("1- 213 Sayılı Vergi Usul Kanunu’nun Mükerrer 355. Maddesine Göre "
             "Ödemelerini Tevsik Etmeme Fiili", 2)

    b.paragraf(
        "%s, rapora ekli tutanakta ayrıntılı olarak tespitine yer verilen "
        "toplam %s TL tutarındaki fatura bedellerine ilişkin olarak tevsik "
        "haddini aşan ödemelerin banka, benzeri finans kurumları veya posta "
        "idarelerince düzenlenen belgelerle yapıldığını tevsik etmemiştir."
        % (M(kunye, buyuk=True), _tl(ouc["islem_tutari"])), girinti=1)

    for baslik, metin in mevzuat.maddeler(["vuk_mk257", "vuk_mk355"]):
        b.paragraf(baslik, kalin=True, hiza="sol", aralik_once=120, aralik_sonra=40)
        b.paragraf("“%s”" % metin, girinti=1, italik=True)

    b.paragraf(
        "Maliye Bakanlığı, 213 sayılı Vergi Usul Kanunu’nun mükerrer 257. "
        "maddesinden aldığı yetkiyle çıkardığı 320, 323, 324, 332, 459, 479 ve "
        "480 sıra numaralı Genel Tebliğler ile tahsilat ve ödemelerin banka "
        "veya benzeri finans kurumlarınca düzenlenen belgelerle tevsik "
        "edilmesi zorunluluğunu getirmiştir. 459 sıra numaralı Genel Tebliğ ile "
        "tevsik haddi 01.01.2016 tarihinden itibaren 7.000,00 TL olarak "
        "belirlenmiştir.", girinti=1)

    satirlar = []
    for i, s in enumerate(ouc["satirlar"], 1):
        satirlar.append([str(i), s["tarih"], s["fatura_no"], _tl(s["matrah"]),
                         _tl(s["kdv"]), _tl(s["toplam"]), _tl(s["yuzde_bes"]),
                         _tl(s["alt_had"]), _tl(s["ceza"])])
    satirlar.append(["", "", "TOPLAM", "", "", _tl(ouc["islem_tutari"]), "", "",
                     _tl(ouc["ham_toplam"])])
    b.tablo(["Sıra\nNo", "Fatura Tarihi", "Fatura No", "Tutar", "KDV",
             "Ödeme veya Tahsilatın\nToplam Tutarı", "Ödeme veya\nTahsilatın %5’i",
             "En Az Ceza\nHaddi", "Kesilecek Ceza\nTutarı"], satirlar,
            hizalar=["orta", "orta", "sol"] + ["sag"] * 6,
            oranlar=[0.45, 0.9, 1.1, 1, 0.9, 1.2, 1.1, 1, 1.1],
            buyukluk=TABLO_PUNTOSU, toplam_satiri=True)

    yillar = sorted({str(x["kayit_yil"]) for x in ouc["satirlar"] if x["kayit_yil"]})
    sonuc = ("%s %s yukarıdaki tabloda gösterilen ve tevsik zorunluluğuna "
             "uyulmayan %d işlem nedeniyle, 213 sayılı Vergi Usul Kanunu’nun "
             "mükerrer 355. maddesi uyarınca toplam %s TL özel usulsüzlük "
             "cezası kesilmesi gerekmektedir."
             % (turkce.liste(yillar) or "[yıl]",
                ik.donem_adi(kunye, len(yillar) > 1, "bulunma"),
                ouc["islem_sayisi"], _tl(ouc["ham_toplam"])))
    if ouc["ust_sinir_uygulandi"]:
        sonuc += (" Ancak bir takvim yılı içinde kesilebilecek toplam ceza %s TL "
                  "ile sınırlı olduğundan, kesilecek ceza %s TL’dir."
                  % (_tl(ouc["ust_sinir"]), _tl(ouc["kesilecek"])))
    b.paragraf(sonuc, girinti=1)


# --------------------------------------------------------------- III. hesap
DAR_TABLO_PUNTOSU = 8


def _surum_tablosu(b, satirlar):
    """Beyanname dokumunu (ilk beyan / son hal) yil yil tabloya doker."""
    for yil in sorted({s["yil"] for s in satirlar}):
        alt = [s for s in satirlar if s["yil"] == yil]
        govde = [[s["ay_adi"]] + [_tl(s["ozet"].get(kod))
                                  for kod, _e in BEYAN_DOKUM_KOLONLARI]
                 for s in alt]
        govde.append(["Toplam:"] + [
            _tl(sum(s["ozet"].get(kod, 0.0) for s in alt))
            for kod, _e in BEYAN_DOKUM_KOLONLARI])
        b.tablo(["Dönemi\n%s" % yil] + [e for _k, e in BEYAN_DOKUM_KOLONLARI],
                govde, hizalar=["sol"] + ["sag"] * len(BEYAN_DOKUM_KOLONLARI),
                oranlar=[1.0] + [1.15] * len(BEYAN_DOKUM_KOLONLARI),
                buyukluk=TABLO_PUNTOSU, toplam_satiri=True, dar=True)


def _duzeltme_tablosu(b, duzeltme):
    """Verilen duzeltme beyannameleri.

    Duzeltme gerekcesi tabloya sigmiyordu: dokuz tutar sutununun yaninda genis
    bir metin sutunu, rakamlarin alt satira kaymasina yol aciyordu. Gerekce
    artik tablonun altinda cumle olarak yazilir, tablo da dar hucre
    bosluklariyla ve kucuk puntoyla kurulur.
    """
    for yil_blogu in duzeltme:
        tablo = []
        gerekceler = []
        for s in yil_blogu["satirlar"]:
            tablo.append([s.get("donem") or "", s.get("tarih") or "",
                          _tl(s.get("matrah_toplami")), _tl(s.get("hesaplanan_kdv")),
                          _tl(s.get("onceki_donem_devreden")),
                          _tl(s.get("bu_donem_indirilecek")),
                          _tl(s.get("indirimler_toplami")),
                          _tl(s.get("odenmesi_gereken_kdv")),
                          _tl(s.get("sonraki_donem_devreden"))])
            if s.get("gerekce"):
                gerekceler.append((s.get("donem") or "", s["gerekce"]))
        b.tablo(["Dönemi\n%s" % yil_blogu["yil"], "Düzeltme\nTarihi",
                 "KDV\nMatrahı", "Hspl.\nKDV", "Önc. Dön.\nDev. KDV",
                 "Bu Dön.\nİndl. KDV", "İndirimler\nToplamı", "Öden.\nKDV",
                 "Son. Dön.\nDev. KDV"], tablo,
                hizalar=["sol", "orta"] + ["sag"] * 7,
                oranlar=[0.7, 1.0, 1.3, 1.2, 1.1, 1.2, 1.3, 1.0, 1.1],
                buyukluk=DAR_TABLO_PUNTOSU, dar=True)
        for donem, gerekce in gerekceler:
            b.paragraf("%s dönemine ilişkin düzeltme gerekçesi: “%s”"
                       % (donem, gerekce.strip().rstrip(".")),
                       girinti=1, buyukluk=DAR_TABLO_PUNTOSU + 1)


def _hesap(b, kunye, donemler, duzeltme, bulgular, dokumler=None):
    """III- HESAP İNCELEMELERİ.

    Uc tablo sirayla: mukellefin ilk (kanuni suresinde verilen) beyannameleri,
    verdigi duzeltme beyannameleri ve beyanin son hali. Beyanname PDF'leri
    yuklenmemisse ilk ve son hal ayrimi bilinmediginden calismadaki tek beyan
    dokumu yazilir.
    """
    b.baslik("III- HESAP İNCELEMELERİ", 1)
    M = ik.mukellef_sozu
    dokumler = dokumler or {}

    if dokumler.get("ilk"):
        b.paragraf("%s %s ilişkin kanuni süresinde verdiği katma değer vergisi "
                   "beyannamelerinin özet bilgileri aşağıdaki gibidir."
                   % (M(kunye, buyuk=True, ek="in"),
                      _donem_ifadesi(kunye, donemler, "yonelme")), girinti=1)
        _surum_tablosu(b, dokumler["ilk"])
    else:
        b.paragraf("%s %s ilişkin katma değer vergisi beyanlarının özet "
                   "bilgileri aşağıdaki gibidir."
                   % (M(kunye, buyuk=True, ek="in"),
                      _donem_ifadesi(kunye, donemler, "yonelme")), girinti=1)
        beyan_dokum_tablosu(b, donemler)

    if duzeltme:
        b.paragraf("%s tarafından verilen düzeltme beyannameleri aşağıdaki "
                   "gibidir." % M(kunye, buyuk=True), girinti=1)
        _duzeltme_tablosu(b, duzeltme)

    if dokumler.get("son"):
        b.paragraf("Yapılan düzeltmeler sonrasında beyanların son hali "
                   "aşağıdaki gibidir.", girinti=1)
        _surum_tablosu(b, dokumler["son"])

    if bulgular:
        b.paragraf("%s katma değer vergisi beyannamelerinin tetkikinde;"
                   % M(kunye, buyuk=True, ek="in"), girinti=1)
        for x in bulgular:
            b.paragraf("- " + x["mesaj"], girinti=1, aralik_sonra=60)
        b.paragraf("tespit edilmiştir.", girinti=1)


# ------------------------------------------------------------- IV. elestiri
def _elestiri(b, kunye, liste, satici_satirlari, donemler, sonuc, ceza, oran,
              saticilar=None, inceleme=None, karsilastirmalar=None):
    b.baslik("IV- ELEŞTİRİLEN HUSUSLAR", 1)
    M = ik.mukellef_sozu
    kod = ik.resen_madde_kodu(kunye)

    # ---- A: re'sen takdir nedeni
    b.baslik("A- Re’sen Takdir Nedeni", 2)
    veri_maddeleri = satici_veri_maddeleri(kunye, donemler,
                                           len(satici_satirlari))
    b.paragraf(
        "Raporun IV. bölümünde ayrıntılı olarak açıklandığı üzere, rapora ekli "
        "tutanağın %s %s belirtilen sahte faturaların yasal defterlere "
        "kaydedildiği, söz konusu faturalarda gösterilen Katma Değer Vergisi "
        "tutarlarının ise İndirilecek Katma Değer Vergisi hesabına "
        "kaydedilerek beyannamelerde indirim konusu yapıldığı tespit "
        "edilmiştir."
        % (_madde_numaralari_metni(veri_maddeleri),
           "maddesinde" if len(veri_maddeleri) == 1 else "maddelerinde"),
        girinti=1)
    b.paragraf(
        "Bu tespit, tutulması zorunlu olan defterlerin ve verilen "
        "beyannamelerin gerçek durumu yansıtmadığına dair delil niteliğinde "
        "olup, söz konusu husus 213 sayılı Vergi Usul Kanunu’nun %s. "
        "maddesinde re’sen takdir nedeni olarak sayılmıştır. Bu nedenle %s "
        "adına re’sen tarhiyat yapılması gerekmektedir."
        % (kod, M(kunye)), girinti=1)

    # ---- B: satici basina veriler
    b.baslik("B- Re’sen Takdir Verileri", 2)
    if not satici_satirlari:
        b.paragraf("[Sahte belge düzenlediği tespit edilen mükelleflere ait "
                   "fatura listesi girilmediği için bu bölüm boş bırakılmıştır.]",
                   girinti=1, italik=True)
    for i, s in enumerate(satici_satirlari, 1):
        _satici_bolumu(b, kunye, s, liste, i,
                       _donem_ifadesi(kunye, donemler), karsilastirmalar)

    # ---- C: mevzuat
    b.baslik("C- İlgili Mevzuat", 2)
    for baslik, metin in mevzuat.maddeler(
            ["kdv_indirim_sartlari", "kdv_29", "kdv_34", "vuk_3b", "vuk_227",
             "vuk_359", "danistay_indirim"]):
        b.paragraf(baslik, kalin=True, hiza="sol", aralik_once=120, aralik_sonra=40)
        b.paragraf("“%s”" % metin, girinti=1, italik=True)

    if satici_satirlari:
        b.paragraf(
            "Yukarıda açıklandığı üzere, sahte belgelere dayanılarak indirim "
            "konusu yapılan katma değer vergilerinin, indirim konusu "
            "yapıldıkları dönemlere ait indirimlerden tenzili gerekmektedir. "
            "Bu doğrultuda ilgili dönem beyanlarından çıkarılacak tutarlar "
            "aşağıdaki tabloda gösterilmiştir.", girinti=1)
        _cikarilacak_tablosu(b, liste, saticilar)

    # ---- D: degerlendirme
    b.baslik("D- Tespit Edilen Hususların İlgili Mevzuat Çerçevesinde "
             "Değerlendirilmesi", 2)
    _kdv_degerlendirmesi(b, kunye, satici_satirlari, donemler, sonuc, ceza)
    _ceza_degerlendirmesi(b, kunye, satici_satirlari, ceza)
    _kasit_degerlendirmesi(b, kunye, satici_satirlari, oran, inceleme)

    # ---- Ç: tarhiyat oncesi uzlasma
    _uzlasma(b, kunye, satici_satirlari)


def _cikarilacak_tablosu(b, liste, saticilar=None):
    """"İndirilecek KDV Hesabından Çıkarılacak Tutar" tablosu.

    Dahil edilen faturalarin KDV'si kayit donemine gore toplanir. Bu tablo,
    tespitlerdeki "İndirilecek KDV'den çıkarılacak" satiriyla ayni veriden
    gelir; ikisi zorunlu olarak birbirini tutar.
    """
    from .satirlar import AYLAR
    ozet = F.donem_ozeti(liste, saticilar)
    for yil in sorted(ozet):
        aylar = ozet[yil]
        satirlar = [[AYLAR[ay - 1], str(aylar[ay]["adet"]), _tl(aylar[ay]["matrah"]),
                     _tl(aylar[ay]["kdv"])] for ay in sorted(aylar)]
        satirlar.append(["TOPLAM",
                         str(sum(h["adet"] for h in aylar.values())),
                         _tl(sum(h["matrah"] for h in aylar.values())),
                         _tl(sum(h["kdv"] for h in aylar.values()))])
        b.tablo(["Dönemi\n%s" % yil, "Fatura\nAdedi", "Matrah",
                 "İndirilecek KDV Hesabından\nÇıkarılacak Tutar"], satirlar,
                hizalar=["sol", "orta", "sag", "sag"],
                oranlar=[1, 0.8, 1.3, 2],
                buyukluk=TABLO_PUNTOSU, toplam_satiri=True)


DUZELTME_AYRINTI_SATIRLARI = [
    "Önceki Dönemden Devreden KDV",
    "Yurtiçi Alımlara İlişkin KDV",
    "İndirimler Toplamı",
    "Ödenmesi Gereken KDV",
    "Sonraki Döneme Devreden KDV",
]


def _donem_listesi(kunye):
    """Kunyeye elle yazilan duzeltme donemlerini ayristirir.

    Beyanname PDF'leri yuklenmediginde donemler veriden bulunamaz; kullanici
    "2023/Şubat, 2023/Mart" gibi yazar. Ayrac olarak virgul de noktali virgul
    de kabul edilir.
    """
    ham = str((kunye or {}).get("duzeltme_donemleri") or "")
    for ayrac in (";", "\n"):
        ham = ham.replace(ayrac, ",")
    return [p.strip() for p in ham.split(",") if p.strip()]


def _duzeltme_ayrinti_tablolari(b, kunye, karsilastirmalar):
    """Duzeltme beyannamesinde satir bazinda ne degistigini gosteren tablolar.

    Veri varsa (beyannameler yuklenmisse) donem donem gercek rakamlarla,
    yoksa kunyeye yazilan donemler icin kirmizi yer tutucularla acilir.
    Boylece beyanname yuklenmemis dosyalarda da tablo belgede hazir durur.
    """
    M = ik.mukellef_sozu
    donemler = _donem_listesi(kunye)
    if not karsilastirmalar and not donemler:
        return

    b.paragraf(
        "%s tarafından verilen düzeltme beyannamelerinde yapılan düzeltmelere "
        "ilişkin ayrıntılı tablo aşağıda sunulmuştur."
        % M(kunye, buyuk=True), girinti=1)

    if karsilastirmalar:
        bloklar = [(k["yil"], k["ay_adi"],
                    [[s["etiket"], _tl(s["oncesi"]), _tl(s["sonrasi"]),
                      _tl(s["fark"])] for s in k["satirlar"]])
                   for k in karsilastirmalar]
    else:
        bloklar = []
        for metin in donemler:
            yil, _, ay_adi = str(metin).partition("/")
            bloklar.append((yil.strip() or "[yıl]", ay_adi.strip() or "[dönem]",
                            [[ad, "[tutar]", "[tutar]", "[tutar]"]
                             for ad in DUZELTME_AYRINTI_SATIRLARI]))

    for yil, ay_adi, satirlar in bloklar:
        # Ay adi yalnizca ilk satirda yazilir; ornekteki birlestirilmis hucrenin
        # karsiligi budur.
        tablo = [[ay_adi if i == 0 else ""] + satir
                 for i, satir in enumerate(satirlar)]
        b.tablo(["Dönemi\n%s" % yil, "Beyanname Satırı",
                 "Düzeltme Öncesi\nBeyanname", "Düzeltme\nBeyannamesi", "Fark"],
                tablo, hizalar=["orta", "sol", "sag", "sag", "sag"],
                oranlar=[0.8, 2.0, 1.3, 1.3, 1.1], buyukluk=TABLO_PUNTOSU)


def _satici_bolumu(b, kunye, s, liste, sira, donem_metni="",
                   karsilastirmalar=None):
    M = ik.mukellef_sozu
    daire = s["vergi_dairesi"] or "[Satıcının vergi dairesi]"
    unvan = ik.satici_unvani(s)
    b.baslik("B.%d- %s %s Vergi Kimlik Numaralı Mükellefi %s’den Olan Alışları"
             % (sira, daire, s["vkn"] or "[VKN]", unvan), 2)

    b.paragraf(
        "%s %s yasal defter ve belgelerinin tetkik edilmesi sonucunda %s %s "
        "vergi kimlik numaralı mükellefi %s’den mal ve/veya hizmet alışlarının "
        "olduğu tespit edilmiştir."
        % (M(kunye, buyuk=True, ek="in"), donem_metni, daire,
           s["vkn"] or "[VKN]", unvan),
        girinti=1)

    # Vergi Tekniği Raporu cumlesi girilmemis olsa da yazilir: eksik tarih ve
    # sayi kirmizi yer tutucu olarak kalir ve doldurulmasi gerektigi gorunur.
    # Vergi Teknigi Raporunun sonuc bolumundeki tespit, ayni cumlenin devami
    # olarak yazilir: "... tanzim edilmis olup, raporun sonuc bolumunde <tespit>
    # tespitine yer verilmistir."
    tespit = " ".join(satir.strip() for satir in str(s["not"] or "").split("\n")
                      if satir.strip())
    b.paragraf(
        "Anılan mükellef hakkında %s tarih ve %s sayılı Vergi Tekniği Raporu "
        "tanzim edilmiş olup, anılan raporun sonuç bölümünde %s tespitine yer "
        "verilmiştir."
        % (s["vtr_tarihi"] or "[VTR tarihi]", s["vtr_no"] or "[VTR no]",
           tespit.rstrip(".") or "[satıcı hakkındaki tespit]"),
        girinti=1)
    if s["ozel_esaslar"]:
        b.paragraf("Söz konusu mükellef %s tarihi itibarıyla özel esaslar "
                   "kapsamına alınmıştır." % s["ozel_esaslar"], girinti=1)

    kendi = [f for f in liste
             if f.get("dahil") and (f.get("satici_vkn") or "") == s["vkn"]]
    if kendi:
        tablo = []
        for f in kendi:
            yev_tarih, yev_no = F.yevmiye_hucreleri(f)
            tablo.append([F.tarih_goster(f.get("tarih")), f.get("fatura_no") or "",
                          F.mal_cinsi_hucresi(f), _tl(f.get("matrah")),
                          _tl(f.get("kdv")), _tl(f.get("toplam")),
                          yev_tarih, yev_no])
        tablo.append(["TOPLAM", "", "", _tl(s["matrah"]), _tl(s["kdv"]),
                      _tl(s["toplam"]), "", ""])
        b.tablo(["Fatura Tarih", "Fatura No", "Malın Cinsi", "Tutar", "KDV",
                 "Toplam Tutar", "Yevmiye Tarih", "Yevmiye No"], tablo,
                hizalar=["orta", "sol", "sol", "sag", "sag", "sag", "orta", "orta"],
                oranlar=[1, 1.4, 1.3, 1.1, 1, 1.1, 1, 0.7],
                buyukluk=TABLO_PUNTOSU, toplam_satiri=True)

    if s.get("duzeltme_ile_cikarildi") == "Evet":
        # Mukerrer tarhiyati onlemek icin bu satici tarhiyata girmez; gerekcesi
        # burada ve degerlendirme bolumunde acikca yazilir.
        for satir in str(s.get("duzeltme_aciklama") or "").split("\n"):
            if satir.strip():
                b.paragraf(satir.strip(), girinti=1)
        b.paragraf(
            "Yukarıda dökümü verilen faturalara ait %s TL tutarındaki katma "
            "değer vergisi, %s tarafından verilen düzeltme beyannameleri ile "
            "ilgili dönem indirimlerinden çıkarılmıştır. Söz konusu tutar "
            "hâlihazırda beyanlardan tenzil edilmiş olduğundan, mükerrer "
            "tarhiyata yol açmamak bakımından bu raporda hesaplanan tarhiyata "
            "dahil edilmemiştir."
            % (_tl(s["kdv"]), M(kunye)), girinti=1)
        _duzeltme_ayrinti_tablolari(b, kunye, karsilastirmalar)
        return

    b.paragraf(
        "Yukarıdaki açıklamalar ve tespit edilen hususlar ile ilgili mevzuat "
        "hükümlerinden hareketle; %s tarafından kullanılan söz konusu "
        "faturalara isabet eden ve ilgili dönem katma değer vergisi "
        "beyannamelerinde indirim konusu yapılmış olan %s TL tutarındaki "
        "katma değer vergisinin indiriminin reddedilmesi ve buna göre ilgili "
        "dönem beyanlarının düzeltilmesi gerekmektedir."
        % (M(kunye), _tl(s["kdv"])), girinti=1)


def _kdv_degerlendirmesi(b, kunye, satici_satirlari, donemler, sonuc, ceza):
    M = ik.mukellef_sozu
    b.baslik("1- Sahte Belge Kullanımının Katma Değer Vergisi Yönünden "
             "Değerlendirilmesi", 2)
    if not satici_satirlari:
        b.paragraf("[Fatura listesi girildikten sonra üretilecektir.]",
                   girinti=1, italik=True)
        return

    haric = [s for s in satici_satirlari
             if s.get("duzeltme_ile_cikarildi") == "Evet"]
    sayilan = [s for s in satici_satirlari if s not in haric]
    toplam_kdv = sum(s["kdv"] for s in sayilan)

    if not sayilan:
        b.paragraf("Düzeltme beyannameleriyle çıkarılan faturalar dışında "
                   "tarhiyata konu edilecek bir tutar kalmamıştır.", girinti=1)
        return

    b.paragraf(
        "Yasanın açık hükümlerinden anlaşılacağı üzere, katma değer vergisinin "
        "indirim konusu yapılabilmesi için gerçek bir teslim veya hizmet "
        "ifasının bulunması gerekmektedir. Raporun yukarıdaki bölümlerinde "
        "yapılan araştırma ve incelemeler ile ortaya konan deliller "
        "çerçevesinde, %s %s yasal defterlerine kaydettiği ve "
        "indirim konusu yaptığı toplam %s TL tutarındaki katma değer "
        "vergisinin sahte belgelere dayandığı ve indiriminin kabul "
        "edilemeyeceği sonucuna ulaşılmıştır."
        % (M(kunye, ek="in"), _donem_ifadesi(kunye, donemler, "bulunma"),
           _tl(toplam_kdv)), girinti=1)

    if haric:
        # Mukerrer tarhiyat riski: bu tutar mukellefin kendi duzeltmesiyle
        # zaten indirimlerden cikmis durumda. Aciklama, duzeltilmis beyan
        # tablosunun hemen oncesinde yer alir; tablodaki tutarlarin neden bu
        # faturalari icermedigi orada sorulur.
        b.paragraf(
            "Diğer taraftan; %s tarafından düzenlenen ve toplam %s TL katma "
            "değer vergisi içeren faturalar, %s tarafından verilen düzeltme "
            "beyannameleri ile ilgili dönem indirimlerinden çıkarılmıştır. Söz "
            "konusu tutar beyanlardan hâlihazırda tenzil edilmiş olduğundan, "
            "aynı tutarın bir de bu raporla tarh edilmesi mükerrer tarhiyat "
            "sonucunu doğuracaktır. Bu nedenle anılan faturalar aşağıdaki "
            "hesaplamaya ve tarhiyata dahil edilmemiştir."
            % (turkce.liste(["%s (VKN: %s)" % (ik.satici_unvani(s),
                                               s["vkn"] or "—") for s in haric]),
               _tl(sum(s["kdv"] for s in haric)), M(kunye)),
            girinti=1)

    b.paragraf("Yapılan düzeltmeler sonucunda beyanların aşağıdaki gibi olması "
               "gerekmektedir.", girinti=1)
    beyan_dokum_tablosu(b, donemler, blok="elestirili")

    tarhiyatli = [d for d in donemler if _var(d["tarhiyat"]["toplam_fark"])]
    if not tarhiyatli:
        b.paragraf("Yapılan düzeltmeler sonucunda re’sen tarhı gereken bir "
                   "vergi farkı hesaplanmamıştır.", girinti=1)
        return

    son = donemler[-1]
    if not _var(son["elestirili"]["sonraki_devir"]) and _var(son["beyan"]["sonraki_devir"]):
        b.paragraf(
            "Yapılan düzeltmeler sonucunda %s dönemine ait sonraki döneme "
            "devreden katma değer vergisi tutarı %s TL olmayıp 0,00 TL "
            "olduğundan, izleyen dönem beyannamelerinin bu tutar dikkate "
            "alınarak düzeltilmesi gerekmektedir."
            % (_donem_adi(son), _tl(son["beyan"]["sonraki_devir"])), girinti=1)

    b.paragraf(
        "Yapılan düzeltmeler sonucunda ortaya çıkan, ödenmesi gereken katma "
        "değer vergisinden beyan edilen tutarın tenzili ile bulunan re’sen "
        "tarhı gereken vergi ile iade edilebilir katma değer vergisinin "
        "indirilecek katma değer vergisinden mahsubu suretiyle bulunan "
        "aranması gereken vergi tutarları aşağıdaki tabloda gösterilmiştir.",
        girinti=1)
    _tarhiyat_tablosu(b, tarhiyatli)


def _tarhiyat_tablosu(b, tarhiyatli):
    """Iki satirli baslik tasiyan tarhiyat tablosu (ornek raporun duzeni)."""
    toplam = tarhiyat_toplami(tarhiyatli)
    satirlar = []
    for d in tarhiyatli:
        t = d["tarhiyat"]
        satirlar.append([_donem_adi(d), _tl(t["odenecek_olmasi_gereken"]),
                         _tl(t["odenecek_beyan"]), _tl(t["resen_tarhi_gereken"]),
                         _tl(t["iade_olmasi_gereken"]), _tl(t["iade_beyan"]),
                         _tl(t["aranmasi_gereken"]), _tl(t["resen_toplam"])])
    satirlar.append(["Toplam:", _tl(toplam["odenecek_olmasi_gereken"]),
                     _tl(toplam["odenecek_beyan"]), _tl(toplam["resen_tarhi_gereken"]),
                     _tl(toplam["iade_olmasi_gereken"]), _tl(toplam["iade_beyan"]),
                     _tl(toplam["aranmasi_gereken"]),
                     _tl(toplam["resen_tarhi_gereken"] + toplam["aranmasi_gereken"])])
    b.tablo(["Dönemi", "Ödenecek KDV\nOlması Gereken", "Ödenecek KDV\nBeyan Edilen",
             "Re’sen Tarhı\nGereken KDV", "İade Edil. KDV\nOlması Gereken",
             "İade Edil. KDV\nBeyan Edilen", "Aranması Ger.\nKDV",
             "Re’sen Tarhı\nGer. Toplam"], satirlar,
            hizalar=["sol"] + ["sag"] * 7,
            oranlar=[0.9, 1.1, 1.1, 1.1, 1.1, 1.1, 1, 1.1],
            buyukluk=TABLO_PUNTOSU, toplam_satiri=True)


def _ceza_degerlendirmesi(b, kunye, satici_satirlari, ceza):
    if not satici_satirlari:
        return
    b.baslik("2- Tarhı Gereken KDV Tutarları Üzerinden Kesilecek Vergi Ziyaı "
             "Cezası", 2)
    for baslik, metin in mevzuat.maddeler(["vuk_341", "vuk_344"]):
        b.paragraf(baslik, kalin=True, hiza="sol", aralik_once=120, aralik_sonra=40)
        b.paragraf("“%s”" % metin, girinti=1, italik=True)

    bilerek = _bilerek_mi(satici_satirlari)
    M = ik.mukellef_sozu
    if bilerek:
        b.paragraf(
            "%s, söz konusu vergilendirme dönemlerinde sahte belgelere "
            "dayanarak haksız yere indirim konusu yaptığı katma değer vergisi "
            "nedeniyle vergi ziyaına sebebiyet vermiş olup, vergi ziyaına 213 "
            "sayılı Vergi Usul Kanunu’nun 359. maddesinde yazılı fiillerle "
            "sebebiyet verildiğinden, aynı Kanun’un 344. maddesi uyarınca "
            "vergi ziyaı cezasının üç kat olarak uygulanması gerekmektedir."
            % M(kunye, buyuk=True), girinti=1)
    else:
        b.paragraf(
            "%s, söz konusu vergilendirme dönemlerinde sahte belgelere "
            "dayanarak haksız yere indirim konusu yaptığı katma değer vergisi "
            "nedeniyle vergi ziyaına sebebiyet vermiştir. Belgelerin bilerek "
            "kullanıldığı kesin verilerle ortaya konulamadığından, 213 sayılı "
            "Vergi Usul Kanunu’nun 344. maddesi uyarınca vergi ziyaı cezasının "
            "bir kat olarak uygulanması gerekmektedir."
            % M(kunye, buyuk=True), girinti=1)

    if ceza["satirlar"]:
        karisik = any(s["ceza_belirsiz"] for s in ceza["satirlar"])
        b.paragraf(
            "Tarh edilmesi gereken vergi, dönem dönem, ilgili faturaları "
            "düzenleyen mükellefler bakımından yapılan bilerek/bilmeden "
            "kullanma nitelendirmesine göre paylaştırılmıştır. Bir dönemde "
            "reddedilen katma değer vergisi ile tarh edilmesi gereken vergi "
            "eşit olmayabilir; devir zinciri reddin bir kısmını "
            "soğurabildiğinden, paylaştırma tarh edilen tutar üzerinden "
            "yapılmıştır.", girinti=1)
        tablo = []
        for s in ceza["satirlar"]:
            tablo.append(["%s/%s" % (s["yil"], s["ay_adi"]), _tl(s["tarh"]),
                          _tl(s["pay_bilerek"]), _tl(s["ceza_bilerek"]),
                          _tl(s["pay_bilmeden"] + s["pay_belirsiz"]),
                          _tl(s["ceza_bilmeden"] + s["ceza_belirsiz"]),
                          _tl(s["ceza_toplam"])])
        t = ceza["toplam"]
        tablo.append(["Toplam:", _tl(t["tarh"]), _tl(t["pay_bilerek"]),
                      _tl(t["ceza_bilerek"]),
                      _tl(t["pay_bilmeden"] + t["pay_belirsiz"]),
                      _tl(t["ceza_bilmeden"] + t["ceza_belirsiz"]),
                      _tl(t["ceza_toplam"])])
        b.tablo(["Dönemi", "Tarh Edilecek\nKDV", "Bilerek\nPay", "Ceza\n(3 kat)",
                 "Bilmeden\nPay", "Ceza\n(1 kat)", "Ceza\nToplamı"], tablo,
                hizalar=["sol"] + ["sag"] * 6,
                oranlar=[0.9, 1.2, 1.1, 1.1, 1.1, 1.1, 1.2],
                buyukluk=TABLO_PUNTOSU, toplam_satiri=True)
        if karisik:
            b.paragraf(
                "[Bilerek/bilmeden kullanma nitelendirmesi yapılmamış satıcılar "
                "için ceza yukarıdaki tabloda bir kat olarak alınmıştır; "
                "nitelendirme yapıldıktan sonra bu tablonun gözden geçirilmesi "
                "gerekir.]", girinti=1, italik=True)


def _kasit_degerlendirmesi(b, kunye, satici_satirlari, oran, inceleme):
    if not satici_satirlari:
        return
    M = ik.mukellef_sozu
    bilerek = _bilerek_mi(satici_satirlari)
    b.baslik("3- Sahte Belge Kullanımının %s, %s ve Kaçakçılık Suçu Yönünden "
             "Değerlendirilmesi"
             % (ik.gelir_vergisi_adi(kunye).title(),
                ik.gecici_vergi_adi(kunye).title()), 2)

    for baslik, metin in mevzuat.maddeler(["vuk_teblig_306", "tck_21"]):
        b.paragraf(baslik, kalin=True, hiza="sol", aralik_once=120, aralik_sonra=40)
        b.paragraf("“%s”" % metin, girinti=1, italik=True)
    b.paragraf(
        "Buna göre failin, fiilin oluşturduğu suçtan sorumlu tutulabilmesi için "
        "kastın mevcudiyeti gerekmekte; kasten hareket edilmiş sayılabilmesi "
        "için de suçu oluşturan fiilin bilerek ve isteyerek işlenmiş olması "
        "gerekmektedir.", girinti=1)

    # Oran, bilerek kullanma kanaatinin en cok dayandirildigi olcuttur.
    if oran and oran["oran"] is not None:
        b.paragraf(
            "Yapılan tespitler doğrultusunda; %s kullandığı sahte faturalara "
            "ait katma değer vergisinin (%s TL), aynı dönemde indirim konusu "
            "yaptığı toplam katma değer vergisi (%s TL) içindeki payının "
            "%%%s olduğu görülmektedir."
            % (M(kunye, ek="in"), _tl(oran["sahte_kdv"]),
               _tl(oran["toplam_indirim_kdv"]),
               turkce.tl(oran["oran"]).rstrip("0").rstrip(",")), girinti=1)
    else:
        b.paragraf("[Sahte belgelerin toplam indirimler içindeki payı, beyan "
                   "verisi girilmediği için hesaplanamamıştır.]",
                   girinti=1, italik=True)

    for satir in ik.satirlar(kunye, "bilerek_gerekce"):
        b.paragraf(satir, girinti=1)

    if bilerek:
        b.paragraf(
            "Yukarıda yapılan açıklamalar 213 sayılı Vergi Usul Kanunu ve 306 "
            "Sıra No’lu Genel Tebliği kapsamında değerlendirildiğinde, %s "
            "kullanmış olduğu sahte faturaları bilerek kullandığı ve vergi "
            "ziyaına sebebiyet vermede kastının bulunduğu sonucuna varılmıştır. "
            "Bu nedenle %s hakkında 213 sayılı Vergi Usul Kanunu’nun 359. "
            "maddesi uyarınca vergi suçu raporu düzenlenmesi ve %s hakkında "
            "Cumhuriyet Başsavcılığına suç duyurusunda bulunulması "
            "gerekmektedir."
            % (M(kunye, ek="in"), M(kunye),
               ik.suc_duyurusu_hedefi(kunye, inceleme)), girinti=1)
    else:
        b.paragraf(
            "Sahte faturalarda yer alan alımların yapıldığının kabul edilmesi, "
            "faturaların bilerek kullanıldığının kesin verilerle ortaya "
            "konulamaması ve yukarıda belirtilen oran birlikte "
            "değerlendirildiğinde, %s söz konusu faturaları bilmeden kullandığı "
            "kanaatine varılmış olup, 213 sayılı Vergi Usul Kanunu’nun 359. "
            "maddesi gereği vergi suçu raporu düzenlenmesine ve suç duyurusunda "
            "bulunulmasına gerek görülmemiştir." % M(kunye, ek="in"), girinti=1)
        for baslik, metin in mevzuat.maddeler(ik.kazanc_maddeleri(kunye)):
            b.paragraf(baslik, kalin=True, hiza="sol", aralik_once=120,
                       aralik_sonra=40)
            b.paragraf("“%s”" % metin, girinti=1, italik=True)
        b.paragraf(
            "Söz konusu faturalarla belgelendirilen alımların %s faaliyet "
            "konusuyla ilgili olduğu ve gerçekten yapıldığı kanaati "
            "oluştuğundan, faturaların katma değer vergisi hariç tutarının "
            "yukarıdaki hükümler çerçevesinde maliyet unsuru olarak kabul "
            "edilmesi ve %s ile %s yönünden eleştiriyi gerektirir bir husus "
            "bulunmadığı sonucuna varılmıştır."
            % (M(kunye, ek="in"), ik.gelir_vergisi_adi(kunye),
               ik.gecici_vergi_adi(kunye)), girinti=1)


def _uzlasma(b, kunye, satici_satirlari):
    bilerek = _bilerek_mi(satici_satirlari)
    M = ik.mukellef_sozu
    b.baslik("Ç- Tarhiyat Öncesi Uzlaşma Talebi Yönünden Değerlendirme", 2)
    if ik.secim_mi(kunye, "tou_talebi", "Talep edildi"):
        b.paragraf("%s, salınacak vergiler ve kesilecek cezalar için 213 sayılı "
                   "Vergi Usul Kanunu’nun Ek 11. maddesinde düzenlenen tarhiyat "
                   "öncesi uzlaşma hakkını kullanmıştır."
                   % M(kunye, buyuk=True), girinti=1)
    else:
        b.paragraf("%s, salınacak vergiler ve kesilecek cezalar için 213 sayılı "
                   "Vergi Usul Kanunu’nun Ek 11. maddesinde düzenlenen tarhiyat "
                   "öncesi uzlaşma talep hakkını kullanmamıştır."
                   % M(kunye, buyuk=True), girinti=1)

    if bilerek:
        baslik, metin = mevzuat.madde("vuk_ek11")
        b.paragraf(baslik, kalin=True, hiza="sol", aralik_once=120, aralik_sonra=40)
        b.paragraf("“%s”" % metin, girinti=1, italik=True)
        b.paragraf(
            "Dolayısıyla %s vergi ziyaına 213 sayılı Vergi Usul Kanunu’nun "
            "359/b maddesinde sayılan “sahte belge kullanma” fiili ile "
            "sebebiyet vermesi nedeniyle, tarh edilecek vergi ve kesilecek "
            "cezalar tarhiyat öncesi uzlaşma kapsamı dışındadır."
            % M(kunye, ek="in"), girinti=1)


# ------------------------------------------------------------------- V. sonuc
def _sonuc(b, inceleme, kunye, satici_satirlari, donemler, ceza, ouc):
    b.baslik("V- SONUÇ", 1)
    M = ik.mukellef_sozu
    tarhiyatli = [d for d in donemler if _var(d["tarhiyat"]["toplam_fark"])]
    toplam = tarhiyat_toplami(tarhiyatli)
    bilerek = _bilerek_mi(satici_satirlari)

    b.paragraf(
        "%s %s vergi kimlik numaralı mükellefi %s’in %s defter ve belgelerinin "
        "sahte belge kullanımı ile sınırlı olarak incelenmesi neticesinde;"
        % (inceleme.get("vergi_dairesi") or "[Vergi dairesi]",
           inceleme.get("vkn_tckn") or "[VKN]",
           ik.mukellef_adi(inceleme, kunye),
           _donem_ifadesi(kunye, donemler)),
        girinti=1)

    maddeler, sira = [], 1
    if tarhiyatli:
        kat = "üç kat" if bilerek else "bir kat"
        maddeler.append(
            "%d- Raporun IV/B ve IV/D bölümlerinde belirtildiği üzere, aşağıda "
            "belirtilen dönemler itibarıyla ortaya çıkan toplam %s TL "
            "tutarındaki katma değer vergisinin 213 sayılı Vergi Usul "
            "Kanunu’nun %s. maddesi uyarınca %s adına re’sen tarh edilmesi; "
            "re’sen tarh edilecek vergi üzerinden aynı Kanun’un 341. ve 344. "
            "maddeleri uyarınca %s vergi ziyaı cezası kesilmesi gerektiği,"
            % (sira, _tl(toplam["resen_tarhi_gereken"] + toplam["aranmasi_gereken"]),
               ik.resen_madde_kodu(kunye), M(kunye), kat))
        sira += 1

    if ouc and ouc["satirlar"]:
        maddeler.append(
            "%d- Raporun II/A.1 bölümünde ayrıntılı olarak açıklandığı üzere; "
            "213 sayılı Vergi Usul Kanunu’nun mükerrer 355. maddesi hükmü "
            "gereğince toplam %s TL özel usulsüzlük cezası kesilmesi gerektiği,"
            % (sira, _tl(ouc["kesilecek"])))
        sira += 1

    if bilerek:
        maddeler.append(
            "%d- Raporun IV/D.3 bölümünde açıklandığı üzere, %s sahte olduğu "
            "Vergi Tekniği Raporlarıyla tespit edilen faturaları bilerek "
            "kullandığı, bu fiil nedeniyle 213 sayılı Vergi Usul Kanunu’nun "
            "359. maddesi uyarınca vergi suçu raporu düzenlenmesi ve %s "
            "hakkında Cumhuriyet Başsavcılığına suç duyurusunda bulunulması "
            "gerektiği,"
            % (sira, M(kunye, ek="in"),
               ik.suc_duyurusu_hedefi(kunye, inceleme)))
        sira += 1
        maddeler.append(
            "%d- Raporun IV/Ç bölümünde açıklandığı üzere, tarh edilecek vergi "
            "ve kesilecek cezaların 213 sayılı Vergi Usul Kanunu’nun Ek 11. "
            "maddesi uyarınca tarhiyat öncesi uzlaşma kapsamı dışında olduğu,"
            % sira)
        sira += 1

    son = donemler[-1] if donemler else None
    if son and not _var(son["elestirili"]["sonraki_devir"]) \
            and _var(son["beyan"]["sonraki_devir"]):
        maddeler.append(
            "%d- Raporun IV/D.1 bölümünde açıklandığı üzere, %s dönemine "
            "ilişkin sonraki döneme devreden katma değer vergisi tutarının "
            "0,00 TL olarak hesaplandığı, müteakip dönem beyannamelerinin bu "
            "tutar dikkate alınarak düzeltilmesi gerektiği,"
            % (sira, _donem_adi(son)))
        sira += 1

    if not maddeler:
        maddeler.append("1- Tenkidi gerektirir bir husus tespit edilmediği,")

    for madde in maddeler:
        b.paragraf(madde, kalin=True, girinti=1, aralik_sonra=100)

    if tarhiyatli:
        _tarhiyat_tablosu(b, tarhiyatli)

    # Inceleme elemaninin kendi tespit notu. Girilmediginde kirmizi yer tutucu
    # kalir; belgeyi okuyan burasinin doldurulacagini gorur.
    notlar = ik.satirlar(kunye, "sonuc_notu")
    if notlar:
        for satir in notlar:
            b.paragraf(satir, girinti=1)
    else:
        b.paragraf("[Sonuç bölümüne eklenecek tespit notu]", girinti=1)

    b.paragraf("Sonucuna varılmıştır.", girinti=1, aralik_once=120)
    b.bos_satir()
    b.imza_bloklari([(ik.deger(kunye, "eleman_unvan", "unvan"),
                      ik.ad(kunye, "eleman_ad"))])


def rapor_yillari(sonuc):
    """Rapor duzenlenecek yillar.

    Tutanak butun inceleme donemi icin tek duzenlenir; rapor ise her yil icin
    ayri duzenlenir. Bu yuzden veri bulunan yillar burada tek yerden secilir ve
    hem uretim hem indirme akisi ayni listeyi kullanir.
    """
    return sorted({d["yil"] for d in dolu_donemler(sonuc)})


def _yila_indirge(sonuc, liste, bulgular, duzeltme, yil):
    """Butun girdileri tek bir yila daraltir.

    Rapor bir yila ait oldugundan hesap tablolari, fatura dokumu, ceza
    dagilimi ve oran hesabi da yalnizca o yilin verisinden uretilmelidir;
    aksi halde 2022 raporunda 2023 donemleri gorunur.
    """
    sonuc = dict(sonuc)
    sonuc["donemler"] = [d for d in (sonuc.get("donemler") or [])
                         if d["yil"] == yil]
    liste = [f for f in liste if _fatura_yili(f) == yil]
    duzeltme = [g for g in (duzeltme or [])
                if str(g.get("yil")) == str(yil)] or None
    bulgular = [x for x in (bulgular or []) if _bulgu_yili(x) in (None, yil)]
    return sonuc, liste, bulgular, duzeltme


def _fatura_yili(f):
    """Faturanin kayit yili; cozulemezse None."""
    try:
        return int(f.get("kayit_yil"))
    except (TypeError, ValueError):
        return None


def _bulgu_yili(bulgu):
    """Tutarlilik bulgusunun ait oldugu yil; donemi okunamazsa None."""
    parcalar = str(bulgu.get("donem") or "").split("/")
    try:
        return int(parcalar[0].strip())
    except (ValueError, IndexError):
        return None


# ---------------------------------------------------------------------- giris
def rapor_uret(inceleme, kunye, yillar, sonuc, calisma, bulgular=None,
               duzeltme=None, yil=None, karsilastirmalar=None, dokumler=None):
    """Sahte belge kullanma raporu taslagini uretir.

    `yil` verilirse rapor yalnizca o yila iliskin duzenlenir; birden cok yilin
    incelendigi dosyalarda her yil icin ayri rapor yazilir.

    `karsilastirmalar`, duzeltme verilen donemlerde satir bazinda oncesi /
    sonrasi dokumudur (beyannameler.duzeltme_karsilastirmalari); duzeltmeyle
    cikarilmis saticinin bolumunde ayrintili tablo olarak yazilir.
    """
    kunye = ik.normalize(kunye)
    mukellef_vkn = (calisma.get("mukellef") or {}).get("vkn_tckn")
    liste = F.normalize(calisma.get("faturalar"), mukellef_vkn)
    if yil is not None:
        sonuc, liste, bulgular, duzeltme = _yila_indirge(
            sonuc, liste, bulgular, duzeltme, int(yil))
        karsilastirmalar = [k for k in (karsilastirmalar or [])
                            if k["yil"] == int(yil)]
        dokumler = {ad: [s for s in satirlar if s["yil"] == int(yil)]
                    for ad, satirlar in (dokumler or {}).items()}
    donemler = dolu_donemler(sonuc)
    saticilar = calisma.get("saticilar") or {}
    satici_satirlari = F.satici_ozeti(liste, saticilar)
    ceza = F.ceza_dagilimi(liste, saticilar, sonuc)
    oran = F.sahte_belge_orani(liste, sonuc, saticilar)
    ouc = None
    if ik.secim_mi(kunye, "ouc_uygula", "Evet"):
        ouc = F.ozel_usulsuzluk(liste, kunye.get("ouc_alt_had"),
                                kunye.get("ouc_ust_sinir"), saticilar)

    # Belge dogrudan "I- GİRİŞ" ile baslar. Baslik/rapor no/tarih blogu
    # bilerek yok: dairenin kullandigi raporlarda bu bilgiler rapor kapak
    # sayfasinda yer aliyor, metnin basinda tekrarlanmiyor.
    b = Belge()
    _giris(b, inceleme, kunye, donemler, satici_satirlari, yil)
    _usul(b, kunye, donemler, ouc)
    _hesap(b, kunye, donemler, duzeltme,
           belgeye_giren_bulgular(bulgular, donemler), dokumler)
    _elestiri(b, kunye, liste, satici_satirlari, donemler, sonuc, ceza, oran,
              saticilar, inceleme, karsilastirmalar)
    _sonuc(b, inceleme, kunye, satici_satirlari, donemler, ceza, ouc)
    return b


def dosya_adi(inceleme, yil=None):
    ad = "".join(c for c in (inceleme.get("ad_unvan") or "rapor")
                 if c.isalnum() or c in " -_").strip() or "rapor"
    if yil:
        ad = "%s_%s" % (yil, ad)
    return ("Sahte_belge_raporu_taslagi_%s.docx" % ad).replace(" ", "_")


def paket_adi(inceleme):
    """Birden cok yilin raporu tek dosyada gonderilirken kullanilan ad."""
    ad = "".join(c for c in (inceleme.get("ad_unvan") or "rapor")
                 if c.isalnum() or c in " -_").strip() or "rapor"
    return ("Sahte_belge_raporlari_%s.zip" % ad).replace(" ", "_")
