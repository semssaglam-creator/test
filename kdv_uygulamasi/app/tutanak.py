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

Duzeltme beyannamelerinin genel dokumu tutanaga girmez; raporun III.
bolumunde yer alir. Ancak faturalari duzeltmeyle indirimlerden cikarilmis bir
satici varsa, bu tespit ve o saticiya iliskin duzeltme dokumu tutanakta da
yazilir: tutanak, incelemede tespit edilen hususlarin mukellefle birlikte
tutulan kaydidir ve faturalari tutanakta dokumu verilen bir saticinin neden
tarhiyata girmedigi tutanaktan anlasilmalidir.
"""
from . import inceleme_kunyesi as ik
from . import turkce
from .belge_docx import TABLO_PUNTOSU, YER_TUTUCU_RENGI as KIRMIZI, Belge
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
        if bulgu.get("tur") in ("donem_boslugu", "indirim_asimi"):
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


def tarhiyat_toplami(tarhiyatli):
    """Gosterilen satirlarin toplami.

    Bilerek `sonuc["tarhiyat_toplami"]` kullanilmaz: o, farkin sifir oldugu
    donemleri de icerir. Tabloya yalnizca farki olan donemler alindigindan
    genel toplam kullanilirsa TOPLAM satiri, ustundeki sutunun toplami
    olmaz ve tablo kendi icinde tutmaz.
    """
    alanlar = ("odenecek_beyan", "odenecek_olmasi_gereken", "resen_tarhi_gereken",
               "iade_beyan", "iade_olmasi_gereken", "aranmasi_gereken",
               "resen_toplam", "haksiz_iade", "toplam_fark")
    return {a: round(sum(d["tarhiyat"].get(a, 0.0) for d in tarhiyatli), 2)
            for a in alanlar}



# Alintilanan metnin kenarindan temizlenecek tirnak isaretleri
_TIRNAKLAR = "“”\"'‘’«»"

DIKKAT_NOTU = ("DİKKAT: LİSTEDE BULUNAN İNDİRİLECEK KDV TUTARINDAN DAHA AZ "
               "İNDİRİLECEK KDV BEYAN EDİLMİŞTİR.")


def indirim_yetersiz_donemler(liste, saticilar, donemler):
    """Fatura KDV'sinin, indirimden cikarilabilecek tutari astigi donemler.

    Sahte belgelerin KDV'si "yurtici alimlara iliskin KDV" icinden cikarilir.
    Bir donemde beyan edilen bu tutar, o donemde kaydedilen sahte faturalarin
    KDV'sinden az ise faturalarin tamami o donemde indirim konusu yapilmamis
    demektir. Belgede ilgili maddenin basina kirmizi bir not dusulur.

    Olcut, sahte belge duzenledigi belirlenen saticilarin LISTEDEKI BUTUN
    faturalaridir; hangilerinin tarhiyata dahil edildigine bakilmaz. Cunku
    not, tarhiyatin kurulusuna degil, listedeki belgelerle beyan arasindaki
    celiskiye isaret eder. Aday fatura birlesimi secilip fazla faturalar
    tarhiyat disina alindiginda tarhiyat beyana oturur ama celiski ortadan
    kalkmaz - mukellef o alislari beyanina dahil etmemis demektir ve
    tutanakta bunun gorunmesi gerekir. Sahteci olarak belirlenmemis
    saticilarin faturalari (mukellefin olagan alislari) sayilmaz; iptal/itiraz
    kaydi bulunanlar da sayilmaz, onlarin indirim konusu yapilmadigi zaten
    ayrica belirtiliyor.

    Doner: {(yil, ay), ...}
    """
    from . import faturalar as F

    sinirlar = {(d["yil"], d["ay"]): d["elestirili"].get("indirim_siniri",
                                                         d["beyan"]["bu_donem_indirim"])
                for d in donemler or []}
    secilenler = F.sahteci_vknler(liste, saticilar)
    toplamlar = {}
    for f in liste or []:
        if f.get("yon") == F.YON_SATIS or f.get("iptal"):
            continue
        if (f.get("satici_vkn") or "") not in secilenler:
            continue
        yil, ay = f.get("kayit_yil"), f.get("kayit_ay")
        if not yil or not ay:
            continue
        anahtar = (int(yil), int(ay))
        toplamlar[anahtar] = toplamlar.get(anahtar, 0.0) + float(f.get("kdv") or 0.0)
    return {d for d, kdv in toplamlar.items()
            if d in sinirlar and kdv - sinirlar[d] > 0.005}


def _alinti_govdesi(metin):
    """Alinti icine girecek metni hazirlar.

    Kullanicidan gelen metin tirnaklariyla birlikte yapistirilmis olabilir;
    belgede tirnak iki kez gorunmesin diye bastaki ve sondaki tirnaklar
    temizlenir. Sondaki nokta da atilir: cumle "... tespitine yer verilmiştir."
    diye surdugunden alintinin icinde nokta kalmaz.
    """
    govde = str(metin or "").strip()
    while govde and govde[0] in _TIRNAKLAR:
        govde = govde[1:].lstrip()
    while govde and govde[-1] in _TIRNAKLAR:
        govde = govde[:-1].rstrip()
    return govde.rstrip(".").strip()


def satici_tespit_paragraflari(s):
    """Satici hakkindaki tespit: Vergi Teknigi Raporu ve ozel esaslar.

    Hem tutanakta hem raporda ayni cumlelerle gecer. Tutanakta da yer almasi
    gerekir: satici hakkindaki tespit, incelemede varilan ve mukellefe izah
    edilen bir husustur; tutanak bunun mukellefle birlikte tutulan kaydidir.
    Eksik tarih ve sayi kirmizi yer tutucu olarak kalir ve doldurulmasi
    gerektigi belgede gorunur. Vergi Teknigi Raporunun sonuc bolumundeki
    tespit ayni cumlenin devami olarak, tirnak icinde aktarilir.
    """
    tespit = _alinti_govdesi(" ".join(
        satir.strip() for satir in str(s.get("not") or "").split("\n")
        if satir.strip()))
    paragraflar = [
        "Anılan mükellef hakkında %s tarih ve %s sayılı Vergi Tekniği Raporu "
        "tanzim edilmiş olup, anılan raporun sonuç bölümünde %s tespitine yer "
        "verilmiştir."
        % (s.get("vtr_tarihi") or "[VTR tarihi]", s.get("vtr_no") or "[VTR no]",
           ("“%s”" % tespit) if tespit else "[satıcı hakkındaki tespit]")]
    if s.get("ozel_esaslar"):
        paragraflar.append("Söz konusu mükellef %s tarihi itibarıyla özel "
                           "esaslar kapsamına alınmıştır." % s["ozel_esaslar"])
    return paragraflar


def iptal_notlari(faturalar):
    """Iptal/itiraz kaydi bulunan faturalar icin aciklama paragraflari.

    Tarhiyata dahil edilmeyen faturalar tabloda gorunmez; kaydin varligi yine
    de belgeye gecer ki o faturanin listede neden yer almadigi anlasilsin.
    """
    from . import faturalar as F

    def ad(f):
        return ("%s tarihinde düzenlenen %s numaralı fatura"
                % (F.tarih_goster(f.get("tarih")) or "[tarih]",
                   f.get("fatura_no") or "[fatura no]"))

    iptalliler = [f for f in faturalar or [] if f.get("iptal")]
    paragraflar = []
    dahil = [ad(f) for f in iptalliler if f.get("dahil")]
    haric = [ad(f) for f in iptalliler if not f.get("dahil")]
    if dahil:
        paragraflar.append("%s ile ilgili iptal/itiraz kaydı bulunduğu tespit "
                           "edilmiştir." % turkce.liste(dahil))
    if haric:
        paragraflar.append("%s ile ilgili iptal/itiraz kaydı bulunduğu tespit "
                           "edilmiş olup, söz konusu %s tarhiyata dahil "
                           "edilmemiştir."
                           % (turkce.liste(haric),
                              "faturalar" if len(haric) > 1 else "fatura"))
    return paragraflar


def yetersiz_donemleri(faturalar, yetersiz):
    """Verilen faturalarin dustugu yetersiz donemler, sirali."""
    return sorted({(f.get("kayit_yil"), f.get("kayit_ay")) for f in faturalar}
                  & (yetersiz or set()))


def _donem_adlari(donemler):
    return ", ".join("%d/%s" % (yil, turkce.buyuk(AYLAR[ay - 1]))
                     for yil, ay in donemler)


def dikkat_notu(faturalar, yetersiz):
    """Verilen faturalar yetersiz donemlere dusuyorsa kirmizi not metni."""
    donemler = yetersiz_donemleri(faturalar, yetersiz)
    return "%s (%s)" % (DIKKAT_NOTU, _donem_adlari(donemler)) if donemler else ""


def kalan_iptal_notlari(b, liste, yazilan_vknler, saticilar=None):
    """Hicbir satici maddesine girmemis iptal/itiraz kayitlarini yazar.

    Bir saticinin butun faturalari tarhiyat disinda kalirsa (hepsi iptal
    edilmisse ya da aday birlesim disinda kaldiysa) o satici icin madde
    acilmaz. Kaydin varligi yine de belgeye gecmelidir: fatura listede
    gorunurken tarhiyatta yer almiyorsa okuyan kisi bunun nedenini
    belgeden anlayabilmelidir.
    """
    from . import faturalar as F

    secilenler = F.sahteci_vknler(liste, saticilar)
    kalan = [f for f in liste or []
             if f.get("iptal")
             and (f.get("satici_vkn") or "") in secilenler
             and (f.get("satici_vkn") or "") not in (yazilan_vknler or set())]
    for satir in iptal_notlari(kalan):
        b.paragraf(satir, girinti=1)


def kalan_dikkat_notu(b, yetersiz, kapsanan):
    """Hicbir satici maddesine dusmemis yetersiz donemler icin ayri not.

    Aday fatura birlesimi secilip bir saticinin butun faturalari tarhiyat
    disina alindiginda o saticinin maddesi acilmaz. Not onunla birlikte
    kaybolmasin diye kalan donemler burada ayrica yazilir: listedeki
    belgelerle beyan arasindaki celiski, tarhiyat beyana oturtulmus olsa da
    belgede gorunmelidir.
    """
    kalan = sorted((yetersiz or set()) - set(kapsanan or set()))
    if not kalan:
        return
    b.paragraf("%s (%s)" % (DIKKAT_NOTU, _donem_adlari(kalan)), kalin=True,
               girinti=1, renk=KIRMIZI, aralik_once=140, aralik_sonra=0)


def satici_veri_maddeleri(kunye, donemler, satici_sayisi):
    """Satici verilerinin dustugu tutanak madde numaralari: [6, 8, 10, ...].

    Rapor, re'sen takdir nedenini yazarken tutanagin hangi maddelerine atif
    yapacagini bilmek zorunda. Numaralar tutanak uretilirken sayacla veriliyor;
    ayni sirayi rapor tarafinda tekrar tahmin etmemek icin burada tek yerden
    hesaplanir. Satici basina iki madde (veri + soru) surdugunden numaralar
    ikiser ikiser artar.
    """
    # 1: ispat vasitasi, 2: inceleme yeri, 3: defter, 4: gelir/kurumlar beyani
    onceki = 4
    if donemler:                                  # 5: KDV beyan dokumu
        onceki += 1
    return [onceki + 1 + 2 * i for i in range(max(int(satici_sayisi or 0), 0))]


# ---------------------------------------------------------------- maddeler
class _Sayac:
    """Tutanak maddelerini sirali numaralandirir.

    Bazi maddeler kosullu (defter tablosu, fatura dokumu, vergi beyani);
    atlandiginda numaralarda bosluk kalmasin diye numara burada uretilir.
    """

    def __init__(self):
        self.sira = 0

    def __call__(self):
        self.sira += 1
        return self.sira


def _madde(b, sayac, metin):
    """Numarali tutanak maddesi. Kullanilan numarayi dondurur.

    Madde metni duz yazilir; dairenin tutanaklarinda da madde govdesi kalin
    degildir. Yalnizca madde numarasi kalin yazilir ki maddeler goz gezdirirken
    ayirt edilebilsin. Numara ile metin ayni paragrafta kalir ve paragraf,
    tutanagin oteki paragraflari gibi satir basi girintisiyle baslar.
    """
    no = sayac()
    b.paragraf("%d- %s" % (no, metin), girinti=1,
               aralik_once=140, aralik_sonra=80, kalin_onek="%d-" % no)
    return no


def _satici_adi(s):
    """Giris cumlesinde saticinin anilisi: vergi dairesi, VKN ve unvan."""
    return ("%s %s vergi kimlik numaralı mükellefi %s"
            % (ik.vergi_dairesi(s["vergi_dairesi"], "[Satıcının vergi dairesi]", "in"),
               s["vkn"] or "[VKN]", ik.satici_unvani(s)))


def _yil_bazli_alis_metni(kunye, satici_satirlari, liste, donemler):
    """Alislari yil yil gruplayan ifade.

    Bir tutanak birden cok yili kapsadiginda hangi yil kimden alis yapildigi
    tek bir yiginda kayboluyordu. Ifade artik yil yil kuruluyor:
    "2021 takvim yılında A’dan alışları, 2022 takvim yılında B ve C’den"
    Son grup, cumlenin devamindaki "olan alışlarının" ekiyle birleseceginden
    "alışları" sozcugunu almaz.
    """
    gruplar = {}
    for s in satici_satirlari:
        yillar = {f.get("kayit_yil") for f in liste
                  if f.get("dahil") and (f.get("satici_vkn") or "") == s["vkn"]
                  and f.get("kayit_yil")}
        if not yillar:                       # kayit donemi cozulememis satici
            yillar = {None}
        for yil in yillar:
            gruplar.setdefault(yil, []).append(s)

    bilinen = sorted(y for y in gruplar if y)
    if not bilinen:
        # Yil bilgisi hic yoksa eski davranis: donem ifadesi + butun saticilar
        return "%s %s" % (_donem_ifadesi(kunye, donemler, "bulunma"),
                          turkce.liste(["%s’den" % _satici_adi(s)
                                        for s in satici_satirlari]))

    parcalar = []
    for yil in bilinen + ([None] if None in gruplar else []):
        adlar = turkce.liste(["%s’den" % _satici_adi(s) for s in gruplar[yil]])
        parcalar.append("%s %s %s"
                        % (yil if yil else "[yıl]",
                           ik.donem_adi(kunye, False, "bulunma"), adlar))
    if len(parcalar) == 1:
        return parcalar[0]
    return "%s alışları, %s" % (" alışları, ".join(parcalar[:-1]), parcalar[-1])


def _giris_paragraflari(b, inceleme, kunye, donemler, satici_satirlari,
                        liste=None):
    M = ik.mukellef_sozu
    tanitim = (
        "%s %s mükellefi %s, “%s” adresinde %s ile iştigal etmektedir."
        % (ik.vergi_dairesi(inceleme.get("vergi_dairesi"), ek="in"),
           ik.mukellef_kimligi(inceleme, kunye),
           ik.mukellef_adi(inceleme, kunye),
           ik.faaliyet_adresi(kunye, inceleme),
           ik.faaliyet_ifadesi(kunye)))
    if ik.secim_mi(kunye, "e_defter", "Kapsamda"):
        tanitim += (" %s e-Defter ve e-Fatura uygulamaları kapsamındadır."
                    % M(kunye, buyuk=True))
    tanitim += (" %s Vergi Usul Kanununun 107/A maddesi kapsamında "
                "e-tebligata tabidir." % M(kunye, buyuk=True))
    b.paragraf(tanitim, girinti=1)

    if satici_satirlari:
        alis = (" %s %s olan alışlarının sahte belge kullanma kapsamında "
                "sınırlı olarak incelenmesi neticesinde aşağıdaki hususlar "
                "mükellef ile birlikte tespit edilmiştir."
                % (M(kunye, buyuk=True, ek="in"),
                   _yil_bazli_alis_metni(kunye, satici_satirlari, liste or [],
                                         donemler)))
    else:
        alis = (" İnceleme neticesinde aşağıdaki hususlar mükellef ile birlikte "
                "tespit edilmiştir.")

    emirler = ik.is_emirleri(kunye)
    if emirler:
        # Birden cok gorevlendirme yazisi cumle icinde sayilinca paragraf
        # okunmaz hale geliyor; raporda oldugu gibi tablo yazilir.
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
        b.paragraf(
            "Bu kapsamda %s işlemleri “Sahte Belge Kullanma” gerekçesiyle "
            "sınırlı olarak incelenmiştir.%s (Ek-1: Kimlik kartı fotokopisi)"
            % (_donem_ifadesi(kunye, donemler), alis), girinti=1)
    else:
        b.paragraf(
            "T.C. Hazine ve Maliye Bakanlığı Vergi Denetim Kurulu %s %s ile %s "
            "işlemlerinin “Sahte Belge Kullanma” gerekçesiyle sınırlı olarak "
            "incelenmesi istenmiştir.%s (Ek-1: Kimlik kartı fotokopisi)"
            % (ik.deger(kunye, "grup_baskanligi", "Denetim Daire Başkanlığının"),
               ik.gorevlendirme_ifadesi(emirler),
               _donem_ifadesi(kunye, donemler), alis),
            girinti=1)


def _donem_ifadesi(kunye, donemler, hal="yalin"):
    """"2023 hesap dönemi" / "2022 ve 2023 takvim yılları" gibi ifadeler."""
    yillar = sorted({d["yil"] for d in donemler})
    if not yillar:
        return "[yıl] %s" % ik.donem_adi(kunye, False, hal)
    return "%s %s" % (turkce.liste(yillar),
                      ik.donem_adi(kunye, len(yillar) > 1, hal))


DEFTER_TUTUCULARI = ["yıl", "defterin türü", "tasdik tarihi ve numarası",
                     "tasdik makamı"]


def _defter_maddesi(b, kunye, sayac, donemler):
    """Ibraz edilen defterlerin tablosu.

    Kunyede hic satir yoksa madde atlanmaz: incelenen her yil icin bir satir
    acilir ve hucreler kirmizi tutucularla birakilir. Defter bilgisi tasdik
    serhinden okunup taslak uzerinde doldurulacagindan, tablonun belgede hazir
    durmasi elle satir eklemekten kolaydir.
    """
    satirlar = ik.cizgili_satirlar(kunye, "defter_bilgileri", 4,
                                   DEFTER_TUTUCULARI)
    if not satirlar:
        yillar = sorted({d["yil"] for d in donemler}) or [None]
        satirlar = [[str(y) if y else "[yıl]"]
                    + ["[%s]" % ad for ad in DEFTER_TUTUCULARI[1:]]
                    for y in yillar]
    _madde(b, sayac, "Mükellef tarafından incelemeye ibraz edilen yasal "
                     "defterlere ilişkin bilgiler aşağıdaki tabloda "
                     "gösterildiği gibidir.")
    b.tablo(["Yılı", "Defterin Türü", "Tasdik Tarihi ve Numarası", "Tasdik Makamı"],
            satirlar, hizalar=["orta", "sol", "orta", "sol"],
            oranlar=[0.6, 1.4, 1.4, 1.6], buyukluk=TABLO_PUNTOSU)


GELIR_VERGISI_KALEMLERI = [
    "Ticari Kazançlar",
    "Vergiye Tabi Gelir (Matrah)",
    "Hesaplanan Gelir Vergisi",
    "Mahsup Edilecek Vergiler Toplamı",
    "Ödenmesi Gereken Gelir Vergisi",
    "İadesi Gereken Gelir Vergisi",
]

KURUMLAR_VERGISI_KALEMLERI = [
    "Ticari Bilanço Karı",
    "Kanunen Kabul Edilmeyen Giderler",
    "Zarar Olsa Dahi İndirilecek İstisna ve İndirimler",
    "Kurumlar Vergisi Matrahı",
    "Hesaplanan Kurumlar Vergisi",
    "Mahsup Edilecek Vergiler Toplamı",
    "Ödenmesi Gereken Kurumlar Vergisi",
    "İadesi Gereken Kurumlar Vergisi",
]


def _inceleme_yeri_cumlesi(inceleme, kunye):
    """İncelemenin nerede yapildigini adresiyle birlikte yazar.

    Yalnizca "dairede" demek yetmiyor; tutanakta incelemenin yapildigi adres
    de yer almali. Adres girilmemisse kirmizi yer tutucu birakilir ki taslak
    uzerinde doldurulsun.
    """
    yer = str(kunye.get("inceleme_yeri") or "").strip()
    calisma_adresi = ik.calisma_adresi(kunye)
    if yer == "Mükellefin iş yerinde":
        return ("İnceleme, %s “%s” adresindeki iş yerinde yapılmıştır."
                % (ik.mukellef_sozu(kunye, ek="in"),
                   ik.faaliyet_adresi(kunye, inceleme)))
    if yer == "Uzaktan":
        return ("İnceleme, Müfettişliğimizin “%s” çalışma adresinden uzaktan "
                "erişim yoluyla yapılmıştır." % calisma_adresi)
    return ("İnceleme, Müfettişliğimizin “%s” çalışma adresinde yapılmıştır."
            % calisma_adresi)


def _vergi_beyani_yillari(kunye, donemler):
    """Yil -> [(aciklama, tutar)] biciminde beyanname ozetleri.

    Kunyedeki satirlar "yil | aciklama | tutar" duzenindedir. Eski
    calismalarda yil sutunu yoktur; o satirlar incelemenin ilk yilina
    yazilir - veri kaybolmasin, ama yil bilgisi de uydurulmasin diye yil
    okunamayan satirlar kirmizi "[yıl]" basligi altinda toplanir.
    """
    incelenen = sorted({d["yil"] for d in donemler})
    varsayilan = str(incelenen[0]) if incelenen else "[yıl]"
    gruplar = {}
    sira = []
    for ham in ik.satirlar(kunye, "vergi_beyan_ozeti"):
        parcalar = [p.strip() for p in ham.replace("\t", "|").split("|")]
        if len(parcalar) >= 3:
            yil, aciklama, tutar = parcalar[0], parcalar[1], parcalar[2]
        else:
            parcalar += [""] * (2 - len(parcalar))
            yil, aciklama, tutar = varsayilan, parcalar[0], parcalar[1]
        yil = yil or varsayilan
        if not (aciklama or tutar):
            continue
        if yil not in gruplar:
            gruplar[yil] = []
            sira.append(yil)
        gruplar[yil].append([aciklama or "[açıklama]", tutar or "[tutar]"])

    if not sira:
        # Hic ozet girilmemis: incelenen her yil icin olagan kalemler yazilir,
        # tutarlar kirmizi birakilir.
        kalemler = (KURUMLAR_VERGISI_KALEMLERI if ik.kurum_mu(kunye)
                    else GELIR_VERGISI_KALEMLERI)
        for yil in (incelenen or ["[yıl]"]):
            sira.append(str(yil))
            gruplar[str(yil)] = [[ad, "[tutar]"] for ad in kalemler]
    return [(yil, gruplar[yil]) for yil in sira]


def _vergi_beyani_maddesi(b, kunye, sayac, donemler):
    """Gelir / Kurumlar Vergisi beyannamesi dokumu maddesi.

    Inceleme birden cok yili kapsiyorsa her yilin ozeti ayri tablo olarak
    yazilir. Kunyeye ozet girilmemis olsa da madde atlanmaz: mukellef turune
    gore olagan kalemler yazilir, tutarlar kirmizi tutucu olarak birakilir.
    """
    bloklar = _vergi_beyani_yillari(kunye, donemler)
    ad = "Kurumlar Vergisi" if ik.kurum_mu(kunye) else "Gelir Vergisi"
    _madde(b, sayac, "%s %s ait %s Beyannamesi özetlerine aşağıda yer "
                     "verilmiştir."
           % (ik.mukellef_sozu(kunye, buyuk=True, ek="in"),
              _donem_ifadesi(kunye, donemler, "yonelme"), ad))
    # Baslikta buyuk harfe cevirirken Turkce i/I ciftine dikkat edilmeli;
    # str.title() "ilk" gibi sozcukleri bozar.
    donem_adi = turkce.unvan(ik.donem_adi(kunye, False))
    for yil, satirlar in bloklar:
        b.tablo(["%s %s\nAçıklama" % (yil, donem_adi), "Tutar"], satirlar,
                hizalar=["sol", "sag"], oranlar=[3, 1], buyukluk=TABLO_PUNTOSU)


def _kdv_beyani_maddesi(b, kunye, sayac, donemler, uyumsuz=None):
    """KDV beyan dokumu ve varsa uzerinde bulunan tutarsizliklar.

    Aritmetik denetim bulgulari, tutanagin sonunda ayri bir maddede degil
    dayandiklari tablonun hemen altinda yer alir; okuyan kisi hangi tabloya
    iliskin oldugunu aramak zorunda kalmasin.
    """
    if not donemler:
        return
    _madde(b, sayac, "%s %s ait Katma Değer Vergisi Beyannameleri özet "
                     "bilgilerine aşağıda yer verilmiştir. (GİB YBS kayıtları)"
           % (ik.mukellef_sozu(kunye, buyuk=True, ek="in"),
              _donem_ifadesi(kunye, donemler, "yonelme")))
    beyan_dokum_tablosu(b, donemler)
    if uyumsuz:
        b.paragraf("Beyan edilen tutarlar üzerinde yapılan aritmetik "
                   "denetimde aşağıdaki hususlar tespit edilmiştir:",
                   girinti=1, aralik_once=120)
        b.madde_listesi([x["mesaj"] for x in uyumsuz], numarali=False)


def _fatura_maddesi(b, kunye, sayac, satici_satirlari, liste, yetersiz=None,
                    karsilastirmalar=None):
    """Satici basina VERI maddesi ve hemen ardindan SORU maddesi.

    Duzen tutanagin kendi mantigina uyar: once o saticiya ait ba-bs tespiti ve
    fatura dokumu, hemen ardindan mukellefe o faturalara iliskin sorulan
    hususlar ve alinan cevap. Birden cok satici varsa cift cift surer:
    6 veri / 7 soru, 8 veri / 9 soru, 10 veri / 11 soru...

    Cevap satici bazinda girilebilir; girilmemisse kunyedeki genel beyan
    kullanilir.
    """
    from . import faturalar as F

    kapsanan, yazilan_vknler = set(), set()
    if not satici_satirlari:
        return kapsanan, yazilan_vknler
    M = ik.mukellef_sozu
    sorular = ik.satirlar(kunye, "sorular")
    genel_cevap = " ".join(ik.satirlar(kunye, "mukellef_beyani"))

    for s in satici_satirlari:
        # Saticinin LISTEDEKI butun faturalari yazilir; tarhiyata girmeyenler
        # de tabloda yer alir. Sahte belge duzenledigi tespit edilen mukellef
        # ve faturalari tutanakta gorunmelidir - hangilerinin indirim reddine
        # konu edildigi ayri bir sorudur ve raporun degerlendirme bolumunde
        # ayrica aciklanir.
        tum = [f for f in liste if (f.get("satici_vkn") or "") == s["vkn"]]
        if not tum:
            continue

        # --- VERI maddesi. Beyan edilen indirim faturalari karsilamiyorsa
        # maddenin basina kirmizi uyari dusulur.
        yazilan_vknler.add(s["vkn"])
        kapsanan.update(yetersiz_donemleri(tum, yetersiz))
        not_metni = dikkat_notu(tum, yetersiz)
        if not_metni:
            b.paragraf(not_metni, kalin=True, girinti=1, renk=KIRMIZI,
                       aralik_once=140, aralik_sonra=0)
        veri_no = _madde(
            b, sayac,
            "%s Ba-Bs analizi sorgulamasında %s %s vergi kimlik numaralı "
            "mükellefi %s’den %d belge ile KDV hariç %s TL tutarında alış "
            "bildiriminde bulunduğu tespit edilmiştir. Mükellef tarafından "
            "müfettişliğimize ibraz edilen faturalara ait ayrıntılı bilgiler "
            "ile defter kayıtları aşağıdaki gibidir. (Ek-2: %d adet fatura "
            "fotokopisi)"
            % (M(kunye, buyuk=True, ek="in"),
               ik.vergi_dairesi(s["vergi_dairesi"], "[Satıcının vergi dairesi]", "in"),
               s["vkn"] or "[VKN]", ik.satici_unvani(s),
               len(tum), _tl(s["liste_matrah"]), len(tum)))

        # Satici hakkindaki tespit (Vergi Teknigi Raporu, ozel esaslar) fatura
        # dokumunden once yazilir: once belgeleri kimin duzenledigi ve hakkinda
        # ne tespit edildigi, sonra o belgelerin dokumu.
        for satir in satici_tespit_paragraflari(s):
            b.paragraf(satir, girinti=1)

        tablo = []
        for f in tum:
            yev_tarih, yev_no = F.yevmiye_hucreleri(f)
            tablo.append([F.tarih_goster(f.get("tarih")), f.get("fatura_no") or "",
                          F.mal_cinsi_hucresi(f), _tl(f.get("matrah")),
                          _tl(f.get("kdv")), _tl(f.get("toplam")),
                          yev_tarih, yev_no])
        tablo.append(["TOPLAM", "", "", _tl(s["liste_matrah"]),
                      _tl(s["liste_kdv"]), _tl(s["liste_toplam"]), "", ""])
        b.tablo(["Fatura Tarih", "Fatura No", "Malın Cinsi", "Tutar", "KDV",
                 "Toplam Tutar", "Yevmiye Tarih", "Yevmiye No"], tablo,
                hizalar=["orta", "sol", "sol", "sag", "sag", "sag", "orta", "orta"],
                oranlar=[1, 1.4, 1.3, 1.1, 1, 1.1, 1, 0.7],
                buyukluk=TABLO_PUNTOSU, toplam_satiri=True)

        for satir in _muhasebe_paragraflari(kunye, tum):
            b.paragraf(satir, girinti=1)
        # Iptal/itiraz kaydi, dahil edilmeyen faturalar icin de yazilir
        for satir in iptal_notlari(tum):
            b.paragraf(satir, girinti=1)

        _duzeltme_tespiti(b, kunye, s, tum, karsilastirmalar, veri_no)

        # --- SORU maddesi (hemen ardindan, veri maddesine atifla)
        cevap = (s.get("cevap") or "").strip() or genel_cevap
        _madde(b, sayac, _soru_metni(kunye, veri_no, s, sorular, cevap))

    return kapsanan, yazilan_vknler


def _duzeltme_tespiti(b, kunye, s, faturalar, karsilastirmalar, veri_no):
    """Duzeltme beyannamesiyle cikarilmis satici icin tutanak bolumu.

    Bu saticinin faturalarinin duzeltmeyle indirimlerden cikarilmis olmasi,
    incelemede yapilmis bir TESPITTIR ve mukellefle birlikte tutulan tutanakta
    yer almalidir; yoksa faturalari tutanakta dokumu verilen bir saticinin
    neden tarhiyata girmedigi tutanaktan anlasilamaz. Hangi donemde hangi
    satirdan cikarildiginin dokumu rapordaki ile ayni uretecten yazilir, ki
    iki belge birbirini tutsun.

    Yalnizca DOKUM yazilir. "Mukerrer tarhiyata yol acmamak bakimindan bu
    faturalar tarhiyata dahil edilmemistir" gibi bir cumle burada yer almaz:
    tutanak tespit belgesidir, degerlendirme raporda yapilir. Satici kartina
    yazilan "duzeltme beyannamesi aciklamasi" da ayri bir paragraf olarak
    yazilmaz; beyanname gerekcesi dokumun giris cumlesinde tirnak icinde
    kendi baglaminda geciyor.
    """
    if str(s.get("duzeltme_ile_cikarildi") or "") != "Evet":
        return
    # Modul dongusune girmemek icin burada yuklenir: sahte_belge_raporu bu
    # modulu bastan ice aktariyor. Beyanname yuklenmemis olsa da cagrilir:
    # dokum yazilamasa bile duzeltme gerekcesi bir tespittir, tutanakta yazilir.
    from .sahte_belge_raporu import _duzeltme_bolumu
    _duzeltme_bolumu(b, kunye, s, faturalar, karsilastirmalar, veri_no)


def _muhasebe_paragraflari(kunye, faturalar):
    """Fatura tablosunun altina giren muhasebe kaydi paragrafi.

    Kunyeye metin yazilmissa oldugu gibi kullanilir. Yazilmamissa dairenin
    kullandigi kalip yazilir; yil, o saticinin faturalarinin kayit yilindan
    alinir.

    Hesap numaralarini iceren bolum kirmizi birakilir: kullanilan hesap
    mukellefin faaliyetine gore degisir (hizmet isletmesinde 740-Hizmet Uretim
    Maliyeti, ticaret isletmesinde 153-Ticari Mallar, sabit kiymette 25x) ve
    dogru hesabi ancak defter kaydini goren inceleme elemani secebilir.
    """
    girilen = ik.satirlar(kunye, "muhasebe_kaydi")
    if girilen:
        return girilen
    yillar = sorted({f.get("kayit_yil") for f in faturalar if f.get("kayit_yil")})
    yil_metni = (turkce.liste([str(y) for y in yillar]) if yillar else "[yıl]")
    return ["Yukarıda ayrıntılı dökümü yer alan faturaların %s yasal defterine "
            "kayıtlarının tetkikinde, %s söz konusu alışları "
            "[740-Hizmet Üretim Maliyeti ile 191-İndirilecek KDV hesaplarına "
            "borç ve 320-Satıcılar hesabına alacak] kaydı ile %s yılı yevmiye "
            "defterine kaydettiği; faturanın içerdiği KDV tutarlarını ilgili "
            "dönem KDV beyannamelerinde indirim konusu yaptığı tespit "
            "edilmiştir."
            % (ik.mukellef_sozu(kunye, ek="in"),
               ik.mukellef_sozu(kunye, buyuk=True, ek="in"), yil_metni)]


def _soru_metni(kunye, veri_no, s, sorular, cevap):
    """Bir saticinin faturalarina iliskin soru maddesinin metni.

    Sorular kurumda kurum yetkilisine, gercek kisi mukellefte mukellefin
    kendisine yoneltilir; madde de ona gore baslar.
    """
    if sorular:
        hususlar = turkce.liste([x.rstrip("?").strip() for x in sorular])
    else:
        hususlar = ("söz konusu sahte faturaları düzenleyen mükellefi tanıyıp "
                    "tanımadığı, bu mükelleften faturalar içeriğinde yer alan "
                    "emtiayı alıp almadığı, mal sevklerinin kim tarafından "
                    "yerine getirildiği ve fatura ödemelerinin ne şekilde "
                    "yapıldığı")
    return ("%s, tutanağın %d. maddesinde bilgileri yer alan ve %s tarafından "
            "düzenlenen faturaların sahte faturalar olduğunun tespit edildiği "
            "hususu izah edilmiş ve %s hususları sorulmuş olup, %s cevaben; "
            "“%s” şeklinde ifade ve beyanda bulunmuştur."
            % (ik.soru_muhatabi(kunye, ek="e"), veri_no, ik.satici_unvani(s),
               hususlar, ik.soru_muhatabi(kunye, buyuk=False),
               cevap or "[mükellefin beyanı]"))


def _tespit_maddesi(b, kunye, sayac, yillar, donemler):
    """Fatura listesi yoksa elle girilen elestiriler madde olarak yazilir."""
    elestiri_haritasi = {}
    for yil_kaydi in yillar or []:
        yil = int(yil_kaydi.get("yil"))
        elestiri = yil_kaydi.get("elestiri") or {}
        for ay in range(12):
            degerler = {kod: (elestiri.get(kod) or [0.0] * 12)[ay]
                        for kod, _e in ELESTIRI_ALANLARI}
            if any(_var(v) for v in degerler.values()):
                elestiri_haritasi[(yil, ay + 1)] = degerler
    if not elestiri_haritasi:
        return
    _madde(b, sayac, "İnceleme sonucunda beyan edilen tutarların "
                     "düzeltilmesini gerektiren tespitler aşağıdaki gibidir.")
    tablo = []
    for (yil, ay), degerler in sorted(elestiri_haritasi.items()):
        tablo.append(["%s/%s" % (yil, AYLAR[ay - 1])]
                     + [_tl(degerler[kod]) if _var(degerler[kod]) else "-"
                        for kod, _e in ELESTIRI_ALANLARI])
    b.tablo(["Dönem", "Matraha İlave", "Hesaplanan KDV İlave",
             "Devirden Çıkarılan", "İndirimden Çıkarılan",
             "Yüklenilenden Çıkarılan"], tablo,
            hizalar=["sol"] + ["sag"] * len(ELESTIRI_ALANLARI),
            oranlar=[1.1, 1, 1, 1, 1, 1], buyukluk=TABLO_PUNTOSU)


def _sorular_maddesi(b, kunye, sayac, satici_satirlari):
    sorular = ik.satirlar(kunye, "sorular")
    beyan = " ".join(ik.satirlar(kunye, "mukellef_beyani"))
    if not sorular and not beyan:
        return
    muhatap = ik.soru_muhatabi(kunye, ek="e")
    kucuk = ik.soru_muhatabi(kunye, buyuk=False)
    if sorular:
        giris = ("%s, yukarıda bilgileri yer alan faturaların sahte faturalar "
                 "olduğunun tespit edildiği hususu izah edilmiş ve %s sorulmuş "
                 "olup, %s cevaben; “%s” şeklinde ifade ve beyanda bulunmuştur."
                 % (muhatap,
                    turkce.liste([s.rstrip("?") for s in sorular]) + " hususları",
                    kucuk, beyan or "[mükellefin beyanı]"))
    else:
        giris = ("%s tespit edilen hususlar izah edilmiş olup, %s cevaben; "
                 "“%s” şeklinde ifade ve beyanda bulunmuştur."
                 % (muhatap, kucuk, beyan))
    _madde(b, sayac, giris)


def _standart_maddeler(b, kunye, sayac, donemler):
    """Her tutanakta yer alan usul maddeleri."""
    _madde(b, sayac,
           "Mükellefe Rapor Değerlendirme Komisyonlarında dinlenme talebinin "
           "olup olmadığı sorulmuş olup, mükellef cevaben; “%s” şeklinde ifade "
           "ve beyanda bulunmuştur." % ik.deger(kunye, "rdk_dinlenme"))
    _madde(b, sayac,
           "Mükellefe; inceleme tutanağının bir taslağının, varsa itiraz ve "
           "mülahazaların geçirilebilmesini sağlamak amacıyla tutanağın "
           "imzalanmasından iki gün öncesinde bilgilerine sunulabileceği hususu "
           "hatırlatılmış olup, mükellef cevaben; “%s” şeklinde ifade ve "
           "beyanda bulunmuştur." % ik.deger(kunye, "taslak_tutanak"))
    if ik.secim_mi(kunye, "tou_talebi", "Talep edildi"):
        _madde(b, sayac,
               "Mükellef %s için tarhiyat öncesi uzlaşma kapsamına giren adına "
               "tarh edilebilecek vergiler ve kesilebilecek cezalar için "
               "tarhiyat öncesi uzlaşma talep etmiştir."
               % _donem_ifadesi(kunye, donemler))
    else:
        _madde(b, sayac,
               "Mükellef %s için tarhiyat öncesi uzlaşma kapsamına giren adına "
               "tarh edilebilecek vergiler ve kesilebilecek cezalar için "
               "tarhiyat öncesi uzlaşma talebinde bulunmamıştır."
               % _donem_ifadesi(kunye, donemler))
    _madde(b, sayac,
           "Mükellefe; mükellef hakkında verilmiş herhangi bir özelge olup "
           "olmadığı sorulmuş, mükellef cevaben; “%s” şeklinde ifade ve beyanda "
           "bulunmuştur." % ik.deger(kunye, "ozelge_cevabi"))
    _madde(b, sayac,
           "Mükellefe incelemeye veya bu tutanakta yer alan hususlara ilişkin "
           "başkaca itiraz ve mülahazaları olup olmadığı soruldu; mükellef "
           "cevaben; “%s” şeklinde ifade ve beyanda bulunmuştur."
           % ik.deger(kunye, "baskaca_itiraz"))


def _yaziyla(sayi):
    """Kucuk sayilari yaziyla verir; tutanak kapanisinda kullanilir."""
    adlar = {1: "bir", 2: "iki", 3: "üç", 4: "dört", 5: "beş", 6: "altı",
             7: "yedi", 8: "sekiz", 9: "dokuz", 10: "on"}
    try:
        return adlar.get(int(sayi), str(sayi))
    except (TypeError, ValueError):
        return str(sayi)


def _kapanis(b, kunye):
    sayfa = kunye.get("tutanak_sayfa") or 3
    nusha = kunye.get("tutanak_nusha") or 2
    b.paragraf(
        "Durumu tespit eden bu tutanak %s (%s) sayfada %s (%s) örnek "
        "düzenlendi, mükellef ile birlikte okundu, içerdiği hususların "
        "doğruluğu, defter kayıtlarına, belgelere ve ifadelere uygunluğu "
        "anlaşıldıktan sonra birlikte imzalandı ve mühürlendi. Tutanağın "
        "imzalı ve mühürlü bir örneği mükellefe verildi. %s, %s"
        % (sayfa, _yaziyla(sayfa), nusha, _yaziyla(nusha),
           ik.deger(kunye, "tutanak_yeri", "yer"),
           ik.deger(kunye, "tutanak_tarihi", "tarih")),
        girinti=1, aralik_once=180)

    hazir = ik.satirlar(kunye, "hazir_bulunanlar")
    if hazir:
        b.paragraf("Hazır bulunanlar:", kalin=True, aralik_once=120)
        b.madde_listesi(hazir, numarali=False)

    b.imza_bloklari([
        (ik.deger(kunye, "eleman_unvan", "unvan"),
         ik.ad(kunye, "eleman_ad")),
        ("Mükellef", ik.ad(kunye, "nezdinde_ad")),
    ])


# ---------------------------------------------------------------------- giris
def tutanak_uret(inceleme, kunye, yillar, sonuc, bulgular=None, calisma=None,
                 karsilastirmalar=None):
    """Tutanak taslagini uretir ve `Belge` nesnesi dondurur."""
    from . import faturalar as F

    kunye = ik.normalize(kunye)
    donemler = dolu_donemler(sonuc)
    calisma = calisma or {}
    mukellef_vkn = (calisma.get("mukellef") or {}).get("vkn_tckn")
    liste = F.normalize(calisma.get("faturalar"), mukellef_vkn)
    saticilar = calisma.get("saticilar") or {}
    satici_satirlari = F.satici_ozeti(liste, saticilar)

    b = Belge()
    b.baslik("VERGİ İNCELEME TUTANAĞI", 1, hiza="orta")
    _giris_paragraflari(b, inceleme, kunye, donemler, satici_satirlari,
                        liste)

    sayac = _Sayac()
    _madde(b, sayac,
           "Bu tutanakta yer alan hususların vergi kanunları karşısında "
           "yapılması muhtemel işlemler bakımından ispatlama vasıtası olduğu ve "
           "yapılması muhtemel işlemlerin neler olduğu, tutanağın "
           "düzenlenmesinden önce mükellefe açıklanmıştır.")
    # Calisma adresi girilmediyse inceleme yeri secimi ("Dairede" vb.) yazilir;
    # cumle o zaman "... Dairede çalışma adresinde" olmasin diye ayrilir.
    _madde(b, sayac, _inceleme_yeri_cumlesi(inceleme, kunye))
    _defter_maddesi(b, kunye, sayac, donemler)
    _vergi_beyani_maddesi(b, kunye, sayac, donemler)
    _kdv_beyani_maddesi(b, kunye, sayac, donemler,
                        belgeye_giren_bulgular(bulgular, donemler))
    # Satici varsa veri/soru ciftleri _fatura_maddesi icinde uretilir; ayrica
    # genel bir soru maddesi acilmaz.
    yetersiz = indirim_yetersiz_donemler(liste, saticilar, donemler)
    kapsanan, yazilan = _fatura_maddesi(b, kunye, sayac, satici_satirlari,
                                        liste, yetersiz, karsilastirmalar)
    kalan_iptal_notlari(b, liste, yazilan, saticilar)
    kalan_dikkat_notu(b, yetersiz, kapsanan)
    if not satici_satirlari:
        _tespit_maddesi(b, kunye, sayac, yillar, donemler)
        _sorular_maddesi(b, kunye, sayac, satici_satirlari)
    _standart_maddeler(b, kunye, sayac, donemler)

    _kapanis(b, kunye)
    return b


def dosya_adi(inceleme):
    ad = "".join(c for c in (inceleme.get("ad_unvan") or "tutanak")
                 if c.isalnum() or c in " -_").strip() or "tutanak"
    return ("Tutanak_taslagi_%s.docx" % ad).replace(" ", "_")
