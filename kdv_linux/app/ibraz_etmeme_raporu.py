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
# Ibraz etmemenin yaninda, duzenlenen belgelerin beyan edilmemis olmasi da
# ayri bir re'sen takdir sebebidir: VUK 30/6 "defterlerin veya verilen
# beyannamelerin gercek durumu yansitmadigina dair delil bulunursa".
# Mufettisin karari (2026-10-20): ikisi de yazilsin. Dayanak DELILE bagli
# oldugundan 30/6, yalnizca matrah ilavesi yapilan dosyalarda aniliyor -
# delil yokken o bende dayanmak raporu itiraz edilebilir kilar.
RESEN_MADDE_DELIL = "30/6"
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
    _olmasi_gereken(b, kunye, inceleme, yil, donemler, liste)


def _resen_dayanagi(donemler):
    """Re'sen takdir dayanaginin cumle icindeki ifadesi.

    Ibraz etmeme 30/3'tur. Duzenledigi belgeleri beyan disi birakmis
    olmasi ise beyannamelerin gercek durumu yansitmadigina DELIL
    oldugundan ayrica 30/6'dir; bu yuzden matrah ilavesi yapilan
    dosyalarda iki bende birlikte dayaniliyor (mufettisin karari,
    2026-10-20).
    """
    if _matrah_ilavesi_var(donemler):
        return ("30 uncu maddesinin (3) ve (6) numaralı bentleri")
    return "30 uncu maddesinin (3) numaralı bendi"


def _resen_takdir_nedeni(b, kunye, yil, donemler):
    M = ik.mukellef_sozu
    b.baslik("4.1- Re’sen Takdir Nedeni", duzey=2)
    maddeler = ["vuk_253", "vuk_256", "vuk_139", "vuk_30_3"]
    delil = _matrah_ilavesi_var(donemler)
    if delil:
        maddeler.append("vuk_30_6")
    for baslik, metin in mevzuat.maddeler(maddeler):
        b.paragraf(baslik, kalin=True, hiza="sol", aralik_once=120,
                   aralik_sonra=40)
        b.paragraf("“%s”" % metin, girinti=1, italik=True)
    b.paragraf(
        "%s %s ilişkin yasal defter ve belgelerinin incelemeye ibraz "
        "edilmemesi nedeniyle, 213 sayılı Vergi Usul Kanunu’nun %s uyarınca "
        "ilgili dönemlerin katma değer vergisi beyanlarının re’sen "
        "tarhiyata esas olacak şekilde düzeltilmesi ve %s %s dönemleri katma "
        "değer vergisi beyannamelerinde indirim konusu yapılmış olan katma "
        "değer vergilerinin reddedilmesi gerekmektedir."
        % (M(kunye, buyuk=True, ek="in"),
           "%s %s" % (yil, ik.donem_adi(kunye, False, "yonelme")),
           _resen_dayanagi(donemler), M(kunye, ek="in"),
           _donem_araligi(yil, donemler)), girinti=1)
    if delil:
        # Iki bendin HANGI tespite dayandigi yazilmali; aksi halde okuyan
        # "30/6'nin delili ne?" diye sorar.
        b.paragraf(
            "Ayrıca %s düzenlediği belgelerin bir kısmını katma değer "
            "vergisi beyannamelerine yansıtmadığı, raporumuzun izleyen "
            "bölümlerinde ayrıntılı olarak açıklandığı üzere GİB "
            "kayıtlarından tespit edilmiştir. Bu tespit, verilen "
            "beyannamelerin gerçek durumu yansıtmadığına dair delil "
            "niteliğinde olduğundan, mezkûr Kanun’un 30 uncu maddesinin (6) "
            "numaralı bendi de re’sen takdir nedeni olarak birlikte "
            "uygulanmıştır." % M(kunye, ek="in"), girinti=1)


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
    # Iki dokumun rapordaki islevi AYRIDIR ve bu, okuyana soylenmeli:
    # duzenlenen belgeler matrahin, adina duzenlenenler indirim tarafinin
    # dayanagidir. Mufettisin istegi (2026-10-19).
    b.paragraf(
        "Söz konusu belgeler raporumuzda iki ayrı yönden değerlendirilmiştir: "
        "%s düzenlediği belgeler katma değer vergisi matrahının, %s adına "
        "düzenlenen belgeler ise indirim konusu yapılan katma değer "
        "vergisinin dayanağıdır. Bu nedenle iki döküm ayrı tablolar hâlinde "
        "gösterilmiştir."
        % (ik.mukellef_sozu(kunye, ek="in"), ik.mukellef_sozu(kunye)),
        girinti=1)

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


def _ceza_ayrimi_var(tarhiyatli):
    """Tarhiyatin bir kismi matrah farkindan mi geliyor.

    Geliyorsa ceza iki katli olur ve tablo kaynak sutunlarini tasir;
    gelmiyorsa tek kat yeter ve bos sutun yazmanin anlami yok.
    """
    return any(float((d.get("tarhiyat") or {}).get("ceza_matrah_payi")
                     or 0.0) > 0.005 for d in tarhiyatli)


def _ceza_bolumu(b, kunye, tarhiyatli):
    """Vergi ziyai cezasi: KAYNAGA gore iki kat.

    Mufettisin karari (2026-10-19): matrah farkindan - yani beyan disi
    birakilan belgelerden - dogan tutar VUK 359 kapsaminda bir fiile
    dayanmadigi icin BIR kat; defter ve belge ibraz etmemekten, yani
    indirimlerin reddinden dogan tutar 359/a-2 kapsaminda oldugundan UC
    kat tasir.

    Paylar motorda hesaplanmistir (`hesap._tarhiyat_satiri`); burada
    yalnizca yazilir, ikinci bir hesap yapilmaz - iki yerde hesaplanan
    rakam birbirini tutmaz.
    """
    if not tarhiyatli:
        return
    ayrim = _ceza_ayrimi_var(tarhiyatli)
    if not ayrim:
        # Tarhiyatin tamami indirimlerin reddinden: tek kat, tek cumle.
        b.paragraf(
            "Re’sen tarh edilecek katma değer vergisi tutarlarının tamamı "
            "defter ve belgelerin ibraz edilmemesi nedeniyle indirimlerin "
            "reddinden kaynaklandığından, bu tutarlar üzerinden 213 sayılı "
            "Vergi Usul Kanunu’nun 344 üncü maddesinin ikinci fıkrası "
            "gereğince üç kat vergi ziyaı cezası kesilmesi gerekmektedir.",
            girinti=1)
    else:
        b.paragraf(
            "Re’sen tarh edilecek katma değer vergisi, iki ayrı tespitten "
            "kaynaklanmaktadır ve vergi ziyaı cezasının katı bu iki "
            "tespitte AYNI DEĞİLDİR:", girinti=1)
        b.paragraf(
            "1- Beyan dışı bırakılan belgelerden (matrah farkından) doğan "
            "tutar: bu tespit 213 sayılı Vergi Usul Kanunu’nun 359 uncu "
            "maddesinde yazılı fiillere dayanmadığından, aynı Kanun’un 344 "
            "üncü maddesinin birinci fıkrası gereğince BİR KAT vergi ziyaı "
            "cezası kesilmesi gerekmektedir.", girinti=1)
        b.paragraf(
            "2- Defter ve belgelerin ibraz edilmemesi nedeniyle "
            "indirimlerin reddinden doğan tutar: bu fiil mezkûr Kanun’un "
            "359 uncu maddesinin (a) fıkrasında kaçakçılık suçu olarak "
            "sayıldığından, 344 üncü maddenin ikinci fıkrası gereğince ÜÇ "
            "KAT vergi ziyaı cezası kesilmesi gerekmektedir.", girinti=1)
        b.paragraf(
            "Dönem dönem hangi tutarın hangi tespitten doğduğu ve buna göre "
            "kesilmesi gereken vergi ziyaı cezası aşağıdaki tabloda "
            "gösterilmiştir.", girinti=1)
    _ceza_tablosu(b, tarhiyatli)


def _ceza_tablosu(b, tarhiyatli):
    """Donem donem kaynak paylari ve her birine dusen ceza.

    Matrah farkindan dogan pay hic yoksa kaynak sutunlari yazilmaz: bos
    sutunlar tabloyu gereksiz genisletiyor ve rakamlari alt satira
    dusuruyor.
    """
    ayrim = _ceza_ayrimi_var(tarhiyatli)
    if ayrim:
        basliklar = ["Dönemi", "Re’sen Tarhı\nGereken KDV",
                     "Beyan Dışı Bırakılan\nBelgelerden",
                     "İbraz Etmemeden\n(İndirim Reddi)",
                     "Vergi Ziyaı\nCezası (1 kat)",
                     "Vergi Ziyaı\nCezası (3 kat)",
                     "Vergi Ziyaı Cezası\nToplamı"]
        kodlar = ["resen_tarhi_gereken", "ceza_matrah_payi",
                  "ceza_indirim_payi", "ceza_matrah", "ceza_indirim",
                  "vergi_ziyai_cezasi"]
        oranlar = [0.9, 1.0, 1.1, 1.0, 1.0, 1.0, 1.1]
    else:
        basliklar = ["Dönemi", "Re’sen Tarhı\nGereken KDV",
                     "Vergi Ziyaı Cezası\n(3 kat)"]
        kodlar = ["resen_tarhi_gereken", "vergi_ziyai_cezasi"]
        oranlar = [1.0, 1.4, 1.4]

    satirlar = [[_donem_adi(d)]
                + [_tl(float((d.get("tarhiyat") or {}).get(k) or 0.0))
                   for k in kodlar] for d in tarhiyatli]
    toplam = ["Toplam:"] + [
        _tl(sum(float((d.get("tarhiyat") or {}).get(k) or 0.0)
                for d in tarhiyatli)) for k in kodlar]
    satirlar.append(toplam)
    b.tablo(basliklar, satirlar,
            hizalar=["orta"] + ["sag"] * len(kodlar), oranlar=oranlar,
            buyukluk=TABLO_PUNTOSU, toplam_satiri=True)


def _matrah_ilavesi_var(donemler):
    """Herhangi bir donemde matrah ilavesi yapilmis mi."""
    return any(float(d["elestirili"].get("matrah") or 0.0)
               - float(d["beyan"].get("matrah") or 0.0) > 0.005
               for d in donemler)


def _yasal_duzenlemeler(b, kunye, yil, donemler):
    b.baslik("4.2.3- Konuya İlişkin Yasal Düzenlemeler", duzey=2)
    maddeler = ["vuk_3b", "vuk_134", "vuk_227", "vuk_229", "kdv_29", "kdv_34"]
    # Matrah ilavesi varsa onun dayanagi olan KDVK hukumleri de buraya
    # girer: ilave, VUK'a degil KDV Kanununun kendi hukumlerine dayaniyor
    # (mufettisin karari, 2026-10-19). Ilave yoksa bu maddeler yazilmaz;
    # rapora ilgisiz hukum doldurmak okuyani yoruyor.
    if _matrah_ilavesi_var(donemler):
        maddeler += ["kdv_1", "kdv_2", "kdv_3", "kdv_10", "kdv_8_2",
                     "kdv_20", "kdv_40"]
    maddeler += ["vuk_341", "vuk_344"]
    for baslik, metin in mevzuat.maddeler(maddeler):
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


def _olmasi_gereken(b, kunye, inceleme, yil, donemler, liste=None):
    M = ik.mukellef_sozu
    b.baslik("4.2.4- Olması Gereken Katma Değer Vergisi Beyan Tablosu",
             duzey=2)

    _matrah_paragrafi(b, kunye, yil, donemler, liste)
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
    _tarhiyat_tablosu(b, tarhiyatli)
    b.paragraf(
        "Yukarıdaki tabloda hesaplanmış olan fark katma değer vergisi "
        "tutarlarının ilgili dönemlere ait fark katma değer vergisi olarak "
        "213 sayılı Vergi Usul Kanunu’nun %s gereğince re’sen tarh "
        "edilmesi gerekmektedir." % _resen_dayanagi(donemler), girinti=1)
    _ceza_bolumu(b, kunye, tarhiyatli)
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


def _matrah_paragrafi(b, kunye, yil, donemler, liste=None):
    """Beyan edilmeyen belgelerin matraha ilavesinin DEGERLENDIRMESI.

    Mufettisin istegi (2026-10-19): bu bolumde bir paragraf aciklama
    bulunmali - tek cumle, tarhiyatin en tartismali kalemini tasiyamiyordu.
    Anlatilan zincir:

      tespit  : duzenlenen belgeler GIB kayitlarindan donem donem bulundu
      olcut   : defter ibraz edilmedigi icin beyanin dogrulugu
                denetlenemez; VUK 3/B geregi gercek mahiyet esastir ve
                mukellefin KENDI duzenledigi belge matrahin en guvenilir
                dayanagidir
      yontem  : karsilastirma donem donem yapilir ve yalnizca mukellef
                ALEYHINE olan yonde ilave dogurur; belgeler beyandan azsa
                beyan esas alinir
      hesap   : hesaplanan KDV faturalarin KENDI KDV'sinden alinir, orana
                bolunmez (dokumde sifir KDV'li satir bulunabiliyor)
      tablo   : donem donem belge adedi / fatura matrahi / beyan / ilave

    Yalnizca gercekten ilave yapildiysa yazilir: ilave yoksa anlatilacak
    bir sey de yoktur.
    """
    satirlar = []
    ilave_toplam = beyan_toplam = fatura_toplam = 0.0
    kdv_fatura_toplam = kdv_beyan_toplam = kdv_ilave_toplam = 0.0
    for d in donemler:
        beyan = float(d["beyan"].get("matrah") or 0.0)
        olmasi = float(d["elestirili"].get("matrah") or 0.0)
        ilave = round(olmasi - beyan, 2)
        beyan_toplam += beyan
        # KDV tarafinin olcutu, beyan edilen TOPLAM hesaplanan vergidir:
        # hesaplanan + ILAVE EDILECEK. Mukellef matrahi beyan etmeden
        # faturanin vergisini ilave edilecek satirinda beyan etmis olabilir
        # (sahada boyle cikti, 2026-10-20); bu halde matrah ilavesi
        # buyukken KDV ilavesi sifir cikar ve SEBEBI tabloda gorunmelidir.
        kdv_beyan = max(float(d["beyan"].get("toplam_kdv") or 0.0),
                        float(d["beyan"].get("hesaplanan") or 0.0)
                        + float(d["beyan"].get("ilave_edilecek") or 0.0))
        kdv_fatura = _satis_kdvsi(liste, d["yil"], d["ay"])
        kdv_ilave = round(max(kdv_fatura - kdv_beyan, 0.0), 2)
        if ilave <= 0.005:
            # Belgeler beyandan az: beyan esas alinir, satir da yazilmaz.
            fatura_toplam += beyan
            kdv_fatura_toplam += kdv_beyan
            kdv_beyan_toplam += kdv_beyan
            continue
        fatura_toplam += olmasi
        ilave_toplam += ilave
        kdv_fatura_toplam += kdv_fatura
        kdv_beyan_toplam += kdv_beyan
        kdv_ilave_toplam += kdv_ilave
        adet = _satis_adedi(liste, d["yil"], d["ay"])
        satirlar.append([_donem_adi(d), str(adet) if adet else "—",
                         _tl(olmasi), _tl(beyan), _tl(ilave),
                         _tl(kdv_fatura), _tl(kdv_beyan),
                         _tl(kdv_ilave) if kdv_ilave > 0.005 else "—"])
    if ilave_toplam <= 0.005:
        return

    M = ik.mukellef_sozu
    b.paragraf(
        "Müfettişliğimizce GİB kayıtlarından yapılan sorgulamada, %s %s "
        "düzenlediği belgelerin toplamı ile beyan ettiği %s TL katma değer "
        "vergisi matrahının uyuşmadığı, düzenlenen belgelerin bir kısmının "
        "beyan dışı bırakıldığı tespit edilmiştir."
        % (M(kunye, ek="in"),
           "%s %s" % (yil, ik.donem_adi(kunye, False, "bulunma")),
           _tl(beyan_toplam)), girinti=1)
    # Dayanak VUK DEGIL, KDV Kanununun kendi hukumleridir (mufettisin
    # karari, 2026-10-19): fatura duzenlenmisse vergiyi doguran olay
    # gerceklesmis, faturada KDV gosterilmisse o vergi odenmesi gereken
    # vergi haline gelmistir. Zincir mevzuat.kdv_1/2/3/10/8_2/20/40.
    b.paragraf(
        "Katma değer vergisinde matrahın ve beyanın dayanağı, 3065 sayılı "
        "Katma Değer Vergisi Kanunu’nun kendi hükümleridir. Mezkûr "
        "Kanun’un 1 inci maddesinin birinci fıkrası uyarınca ticarî, sınaî, "
        "ziraî faaliyet ve serbest meslek faaliyeti çerçevesinde yapılan "
        "teslim ve hizmetler katma değer vergisine tabi olup, teslim 2 nci "
        "maddede tanımlanmış, teslim sayılan haller ise 3 üncü maddede "
        "sayılmıştır. Aynı Kanun’un 20 nci maddesine göre teslim ve hizmet "
        "işlemlerinde matrah, bu işlemlerin karşılığını teşkil eden "
        "bedeldir.", girinti=1)
    b.paragraf(
        "Söz konusu Kanun’un vergiyi doğuran olayı düzenleyen 10 uncu "
        "maddesinin (a) bendinde mal teslimi ve hizmet ifası hallerinde "
        "malın teslimi veya hizmetin yapılması, (b) bendinde ise malın "
        "tesliminden veya hizmetin yapılmasından önce fatura veya benzeri "
        "belgeler verilmesi hallerinde, bu belgelerde gösterilen miktarla "
        "sınırlı olmak üzere fatura veya benzeri belgelerin düzenlenmesi "
        "anında vergiyi doğuran olayın meydana geleceği hükme "
        "bağlanmıştır. Buna göre fatura düzenlenmiş olması, belgede "
        "gösterilen tutar bakımından vergiyi doğuran olayın gerçekleştiğini "
        "göstermektedir. Kanun’un 8 inci maddesinin ikinci fıkrası ise, "
        "vergiye tabi bir işlem söz konusu olmasa dahi düzenledikleri "
        "vesikalarda katma değer vergisi gösterenlerin bu vergiyi ödemekle "
        "mükellef olduklarını hükme bağlamıştır; dolayısıyla bir faturada "
        "katma değer vergisi hesaplanmışsa o vergi, her hâlükârda beyan "
        "edilip ödenmesi gereken bir vergi hâline gelmiştir.", girinti=1)
    b.paragraf(
        "Kanun’un 40 ıncı maddesi uyarınca katma değer vergisi, aksine "
        "hüküm bulunmadıkça mükelleflerin yazılı beyanları üzerine tarh "
        "olunur ve vergiye tabi işlemi bulunmayan mükellefler dahi "
        "beyanname vermek mecburiyetindedir. %s düzenlediği, ancak ilgili "
        "dönem katma değer vergisi beyannamesine yansıtmadığı belgeler, "
        "vergiyi doğuran olayı gerçekleşmiş ve üzerinde hesaplanan katma "
        "değer vergisi de beyan edilmesi gereken hâle gelmiş olan "
        "teslimlere ilişkindir. Bu nedenle söz konusu belgelerin matrahı ve "
        "bunlar üzerinde gösterilen katma değer vergisi, ait oldukları "
        "dönem beyanlarına ilave edilmiştir."
        % M(kunye, buyuk=True, ek="in"), girinti=1)
    b.paragraf(
        "Karşılaştırma dönem dönem yapılmış ve yalnızca %s aleyhine olan "
        "yönde ilave yapılmıştır: düzenlenen belgelerin toplamı beyan "
        "edilen matrahtan fazla olan dönemlerde aradaki tutar matraha ilave "
        "edilmiş, az olan dönemlerde ise beyan esas alınarak matrah "
        "indirilmemiştir. Bu dönemlerde belge dökümünün beyandan az "
        "kalması, mükellefin daha az teslimde bulunduğunu değil, dökümün "
        "teslimlerin tamamını kapsamadığını gösterebileceğinden beyandan "
        "aşağı inilmemiştir. İlave edilen matrahlara ilişkin hesaplanan "
        "katma değer vergisi de belgelerin kendi üzerinde gösterilen katma "
        "değer vergisi tutarlarından alınmış, matraha oran uygulanmak "
        "suretiyle bulunmamıştır; zira 3065 sayılı Katma Değer Vergisi "
        "Kanunu’nun 8 inci maddesinin ikinci fıkrası uyarınca belgede "
        "gösterilen katma değer vergisi, kanunen hesaplanması gerekenden "
        "fazla dahi olsa, beyan edilip ödenmesi gereken vergidir."
        % M(kunye, ek="in"), girinti=1)
    b.paragraf(
        "Vergi yönünden karşılaştırmada ölçü, beyannamenin TOPLAM KATMA "
        "DEĞER VERGİSİ satırıdır; bu satır hesaplanan katma değer vergisi "
        "ile ilave edilecek katma değer vergisini birlikte içerir. Bir "
        "dönemde matrah beyan edilmemiş olsa dahi belgenin vergisi "
        "beyannamenin ilave edilecek katma değer vergisi satırında beyan "
        "edilmiş olabileceğinden, matraha ilave yapılan bir dönemde "
        "vergiye ilave yapılması gerekmeyebilir; bu durumda vergi zaten "
        "beyan edilmiştir.", girinti=1)
    b.paragraf("Beyan Edilmeyen Belgelere İlişkin Matrah ve Katma Değer "
               "Vergisi İlavesi",
               kalin=True, hiza="sol", aralik_once=120, aralik_sonra=40)
    satirlar.append(["TOPLAM", "", _tl(fatura_toplam), _tl(beyan_toplam),
                     _tl(ilave_toplam), _tl(kdv_fatura_toplam),
                     _tl(kdv_beyan_toplam), _tl(kdv_ilave_toplam)])
    b.tablo(["Dönemi", "Belge\nAdedi", "Düzenlenen\nBelgelerin Matrahı",
             "Beyan Edilen\nMatrah", "Matraha\nİlave",
             "Düzenlenen\nBelgelerin KDV’si",
             "Beyan Edilen\nToplam KDV",
             "Toplam KDV’ye\nİlave"], satirlar,
            hizalar=["orta", "orta", "sag", "sag", "sag", "sag", "sag",
                     "sag"],
            oranlar=[0.85, 0.6, 1.2, 1.0, 1.0, 1.2, 1.1, 1.05],
            buyukluk=TABLO_PUNTOSU, toplam_satiri=True)
    _kdvsiz_belge_paragrafi(b, kunye, donemler, liste)
    b.paragraf(
        "Buna göre %s katma değer vergisi matrahlarına toplam %s TL ilave "
        "edilmiş ve beyanlar aşağıdaki bölümde dönemler itibarıyla yeniden "
        "düzenlenmiştir."
        # "doneminin ... matrahlarina" degil "donemi ... matrahlarina":
        # resmi dilde yalin ad tercih ediliyor ve ust uste ilgi ekinden de
        # kaciniliyor (bkz. testler/ibraz_etmeme_testi.py).
        % ("%s %s" % (yil, ik.donem_adi(kunye, False)),
           _tl(ilave_toplam)), girinti=1)


def _kdvsiz_belge_paragrafi(b, kunye, donemler, liste):
    """KDV'si SIFIR belgeler: beyan disi mi, istisna / ozel matrah mi.

    Mufettisin tespiti (2026-10-20): beyan disi sanilan faturalarin
    KDV'si sifirdi ve ozel matrah sekline tabi islem olarak beyan
    edilmislerdi. Istisna kapsamindaki teslimler ile ozel matrah sekline
    tabi islemler beyannamenin "MATRAH TOPLAMI" satirinda YER ALMAZ, ayri
    bolumlerde beyan edilir; bu yuzden karsilastirmada "beyan edilmemis"
    gorunurler.

    Rapor bunu susarak gecemez: tutarlar ve beyannamedeki karsiliklari
    yazilir, uzerlerinden VERGI HESAPLANMADIGI da belirtilir. Nitelendirme
    mufettisindir; uygulama rakamlari koyar.
    """
    kdvsiz = 0.0
    istisna = ozel = 0.0
    for d in donemler:
        beyan = float(d["beyan"].get("matrah") or 0.0)
        olmasi = float(d["elestirili"].get("matrah") or 0.0)
        if olmasi - beyan <= 0.005:          # o donemde ilave yok
            continue
        kdvsiz += _satis_kdvsiz_matrahi(liste, d["yil"], d["ay"])
        istisna += float(d["beyan"].get("istisna_teslim") or 0.0)
        ozel += float(d["beyan"].get("ozel_matrah") or 0.0)
    if kdvsiz <= 0.005:
        return
    ortulen = istisna + ozel
    acik = round(kdvsiz - ortulen, 2)

    if ortulen > 0.005:
        bulgu = ("toplam %s TL beyan bulunduğu görülmüştür.%s" % (
            _tl(ortulen),
            # Acikta kalan tutar varsa SUSULMAZ: raporu okuyanin ilk
            # soracagi sey odur.
            "" if acik <= 0.005 else
            (" Bu tutarın %s TL’lik kısmı ise anılan bölümlerde de beyan "
             "edilmemiştir." % _tl(acik))))
    else:
        bulgu = "herhangi bir beyan bulunmadığı görülmüştür."
    b.paragraf(
        "Matraha ilave edilen belgelerin %s TL tutarındaki kısmı, üzerinde "
        "katma değer vergisi hesaplanmamış belgelerden oluşmaktadır. %s "
        "ilgili dönem katma değer vergisi beyannamelerinin istisna "
        "kapsamına giren işlemler ile özel matrah şekline tabi işlemlere "
        "ilişkin bölümlerinde %s Bu belgeler üzerinde katma değer vergisi "
        "hesaplanmadığından, anılan tutarlar bakımından hesaplanan katma "
        "değer vergisine ilave yapılmamıştır."
        % (_tl(kdvsiz), ik.mukellef_sozu(kunye, buyuk=True, ek="in"), bulgu),
        girinti=1)


def _satis_kdvsiz_matrahi(liste, yil, ay):
    """O donemde duzenlenen ve KDV'si SIFIR olan belgelerin matrahi."""
    return round(sum(float(f.get("matrah") or 0.0) for f in (liste or [])
                     if f.get("yon") == F.YON_SATIS and not f.get("iptal")
                     and f.get("kayit_yil") == yil and f.get("kayit_ay") == ay
                     and abs(float(f.get("kdv") or 0.0)) < 0.005), 2)


def _satis_kdvsi(liste, yil, ay):
    """O donemde mukellefin duzenledigi belgelerin KDV toplami."""
    return round(sum(float(f.get("kdv") or 0.0) for f in (liste or [])
                     if f.get("yon") == F.YON_SATIS and not f.get("iptal")
                     and f.get("kayit_yil") == yil
                     and f.get("kayit_ay") == ay), 2)


def _satis_adedi(liste, yil, ay):
    """O donemde mukellefin duzenledigi belge adedi."""
    return sum(1 for f in (liste or [])
               if f.get("yon") == F.YON_SATIS and not f.get("iptal")
               and f.get("kayit_yil") == yil and f.get("kayit_ay") == ay)


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
        "Vergi Usul Kanunu’nun %s gereğince re’sen tarh edilmesi, "
        "re’sen tarh edilecek fark katma değer vergisi tutarları üzerinden "
        "%s"
        % (M(kunye), _resen_dayanagi(donemler),
           # Ceza kati KAYNAGA gore degisiyorsa sonuc maddesi de ikisini
           # ayri ayri istemeli; tek cumleyle "uc kat" demek tabloyla
           # celisirdi (mufettisin karari, 2026-10-19).
           "aşağıdaki tabloda gösterildiği üzere, beyan dışı bırakılan "
           "belgelerden doğan tutar üzerinden aynı Kanun’un 344 üncü "
           "maddesinin birinci fıkrası gereğince bir kat, defter ve "
           "belgelerin ibraz edilmemesi nedeniyle indirimlerin reddinden "
           "doğan tutar üzerinden ise aynı maddenin ikinci fıkrası "
           "gereğince üç kat vergi ziyaı cezası kesilmesi,"
           if _ceza_ayrimi_var(tarhiyatli) else
           "aynı Kanun’un 344 üncü maddesinin ikinci fıkrası gereğince üç "
           "kat vergi ziyaı cezası kesilmesi,"),
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
            _ceza_tablosu(b, tarhiyatli)

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
