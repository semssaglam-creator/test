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
    """Kalin, numarali tutanak maddesi."""
    b.paragraf("%d- %s" % (sayac(), metin), kalin=True, aralik_once=140,
               aralik_sonra=80)


def _giris_paragraflari(b, inceleme, kunye, donemler, satici_satirlari):
    M = ik.mukellef_sozu
    tanitim = (
        "%s %s vergi kimlik numaralı mükellefi %s, “%s” adresinde “%s” "
        "faaliyeti ile iştigal etmektedir."
        % (inceleme.get("vergi_dairesi") or "[Vergi dairesi]",
           inceleme.get("vkn_tckn") or "[VKN]",
           inceleme.get("ad_unvan") or "[Mükellef unvanı]",
           inceleme.get("adres") or "[Adres]",
           ik.deger(kunye, "faaliyet_konusu")))
    if ik.secim_mi(kunye, "e_defter", "Kapsamda"):
        tanitim += (" %s e-Defter ve e-Fatura uygulamaları kapsamındadır."
                    % M(kunye, buyuk=True))
    tanitim += (" %s Vergi Usul Kanununun 107/A maddesi kapsamında "
                "e-tebligata tabidir." % M(kunye, buyuk=True))
    b.paragraf(tanitim, girinti=1)

    if satici_satirlari:
        adlar = ["%s %s vergi kimlik numaralı mükellefi %s’den"
                 % (s["vergi_dairesi"] or "[Satıcının vergi dairesi]",
                    s["vkn"] or "[VKN]", s["unvan"] or "[unvan girilmedi]")
                 for s in satici_satirlari]
        alis = (" %s %s %s olan alışlarının sahte belge kullanma kapsamında "
                "sınırlı olarak incelenmesi neticesinde aşağıdaki hususlar "
                "mükellef ile birlikte tespit edilmiştir."
                % (M(kunye, buyuk=True, ek="in"),
                   _donem_ifadesi(kunye, donemler, "bulunma"),
                   turkce.liste(adlar)))
    else:
        alis = (" İnceleme neticesinde aşağıdaki hususlar mükellef ile birlikte "
                "tespit edilmiştir.")

    b.paragraf(
        "T.C. Hazine ve Maliye Bakanlığı Vergi Denetim Kurulu %s %s tarih ve "
        "%s sayılı görevlendirme yazısı ile %s işlemlerinin “Sahte Belge "
        "Kullanma” gerekçesiyle sınırlı olarak incelenmesi istenmiştir.%s "
        "(Ek-1: Kimlik kartı fotokopisi)"
        % (ik.deger(kunye, "grup_baskanligi", "Denetim Daire Başkanlığının"),
           ik.deger(kunye, "gorevlendirme_tarihi", "tarih"),
           ik.deger(kunye, "gorevlendirme_no", "sayı"),
           _donem_ifadesi(kunye, donemler), alis),
        girinti=1)


def _donem_ifadesi(kunye, donemler, hal="yalin"):
    """"2023 hesap dönemi" / "2022 ve 2023 takvim yılları" gibi ifadeler."""
    yillar = sorted({d["yil"] for d in donemler})
    if not yillar:
        return "[yıl] %s" % ik.donem_adi(kunye, False, hal)
    return "%s %s" % (turkce.liste(yillar),
                      ik.donem_adi(kunye, len(yillar) > 1, hal))


def _defter_maddesi(b, kunye, sayac):
    satirlar = ik.cizgili_satirlar(kunye, "defter_bilgileri", 4)
    if not satirlar:
        return
    _madde(b, sayac, "Mükellef tarafından incelemeye ibraz edilen yasal "
                     "defterlere ilişkin bilgiler aşağıdaki tabloda "
                     "gösterildiği gibidir.")
    b.tablo(["Yılı", "Defterin Türü", "Tasdik Tarihi ve Numarası", "Tasdik Makamı"],
            satirlar, hizalar=["orta", "sol", "orta", "sol"],
            oranlar=[0.6, 1.4, 1.4, 1.6], buyukluk=TABLO_PUNTOSU)


def _vergi_beyani_maddesi(b, kunye, sayac, donemler):
    satirlar = ik.cizgili_satirlar(kunye, "vergi_beyan_ozeti", 2)
    if not satirlar:
        return
    ad = "Kurumlar Vergisi" if ik.kurum_mu(kunye) else "Gelir Vergisi"
    _madde(b, sayac, "%s %s ait %s Beyannamesi özetine aşağıda yer verilmiştir."
           % (ik.mukellef_sozu(kunye, buyuk=True, ek="in"),
              _donem_ifadesi(kunye, donemler, "yonelme"), ad))
    b.tablo(["Açıklama", "Tutar"], satirlar, hizalar=["sol", "sag"],
            oranlar=[3, 1], buyukluk=TABLO_PUNTOSU)


def _kdv_beyani_maddesi(b, kunye, sayac, donemler):
    if not donemler:
        return
    _madde(b, sayac, "%s %s ait Katma Değer Vergisi Beyannameleri özet "
                     "bilgilerine aşağıda yer verilmiştir. (GİB YBS kayıtları)"
           % (ik.mukellef_sozu(kunye, buyuk=True, ek="in"),
              _donem_ifadesi(kunye, donemler, "yonelme")))
    beyan_dokum_tablosu(b, donemler)


def _fatura_maddesi(b, kunye, sayac, satici_satirlari, liste):
    """Ba-Bs tespiti ve satici basina fatura dokumu."""
    from . import faturalar as F

    if not satici_satirlari:
        return
    M = ik.mukellef_sozu
    for s in satici_satirlari:
        kendi = [f for f in liste
                 if f.get("dahil") and (f.get("satici_vkn") or "") == s["vkn"]]
        if not kendi:
            continue
        _madde(b, sayac,
               "%s Ba-Bs analizi sorgulamasında %s %s vergi kimlik numaralı "
               "mükellefi %s’den %d belge ile KDV hariç %s TL tutarında alış "
               "bildiriminde bulunduğu tespit edilmiştir. Mükellef tarafından "
               "müfettişliğimize ibraz edilen faturalara ait ayrıntılı bilgiler "
               "ile defter kayıtları aşağıdaki gibidir. (Ek-2: %d adet fatura "
               "fotokopisi)"
               % (M(kunye, buyuk=True, ek="in"),
                  s["vergi_dairesi"] or "[Satıcının vergi dairesi]",
                  s["vkn"] or "[VKN]", s["unvan"] or "[unvan girilmedi]",
                  len(kendi), _tl(s["matrah"]), len(kendi)))
        tablo = []
        for f in kendi:
            yev_tarih, yev_no = F.yevmiye_hucreleri(f)
            tablo.append([f.get("tarih") or "", f.get("fatura_no") or "",
                          f.get("mal_cinsi") or "", _tl(f.get("matrah")),
                          _tl(f.get("kdv")), _tl(f.get("toplam")),
                          yev_tarih, yev_no])
        tablo.append(["TOPLAM", "", "", _tl(s["matrah"]), _tl(s["kdv"]),
                      _tl(s["toplam"]), "", ""])
        b.tablo(["Fatura Tarih", "Fatura No", "Malın Cinsi", "Tutar", "KDV",
                 "Toplam Tutar", "Yevmiye Tarih", "Yevmiye No"], tablo,
                hizalar=["orta", "sol", "sol", "sag", "sag", "sag", "orta", "orta"],
                oranlar=[1, 1.4, 1.3, 1.1, 1, 1.1, 1, 0.7],
                buyukluk=TABLO_PUNTOSU, toplam_satiri=True)

    for satir in ik.satirlar(kunye, "muhasebe_kaydi"):
        b.paragraf(satir, girinti=1)


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
    if sorular:
        giris = ("Mükellefe, yukarıda bilgileri yer alan faturaların sahte "
                 "faturalar olduğunun tespit edildiği hususu izah edilmiş ve "
                 "%s sorulmuş olup, mükellef cevaben; “%s” şeklinde ifade ve "
                 "beyanda bulunmuştur."
                 % (turkce.liste([s.rstrip("?") for s in sorular]) + " hususları",
                    beyan or "[mükellefin beyanı]"))
    else:
        giris = ("Mükellefe tespit edilen hususlar izah edilmiş olup, mükellef "
                 "cevaben; “%s” şeklinde ifade ve beyanda bulunmuştur." % beyan)
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
               "Mükellef %s için tarhiyat öncesi uzlaşma kapsamına giren, adına "
               "tarh edilebilecek vergiler ve kesilebilecek cezalar için "
               "tarhiyat öncesi uzlaşma talep etmiştir."
               % _donem_ifadesi(kunye, donemler))
    else:
        _madde(b, sayac,
               "Mükellef %s için tarhiyat öncesi uzlaşma talebinde "
               "bulunmamıştır." % _donem_ifadesi(kunye, donemler))
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
         ik.deger(kunye, "eleman_ad", "ad soyad")),
        ("Mükellef", ik.deger(kunye, "nezdinde_ad", "ad soyad")),
    ])


# ---------------------------------------------------------------------- giris
def tutanak_uret(inceleme, kunye, yillar, sonuc, bulgular=None, duzeltme=None,
                 calisma=None):
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
    _giris_paragraflari(b, inceleme, kunye, donemler, satici_satirlari)

    sayac = _Sayac()
    _madde(b, sayac,
           "Bu tutanakta yer alan hususların vergi kanunları karşısında "
           "yapılması muhtemel işlemler bakımından ispatlama vasıtası olduğu ve "
           "yapılması muhtemel işlemlerin neler olduğu, tutanağın "
           "düzenlenmesinden önce mükellefe açıklanmıştır.")
    # Calisma adresi girilmediyse inceleme yeri secimi ("Dairede" vb.) yazilir;
    # cumle o zaman "... Dairede çalışma adresinde" olmasin diye ayrilir.
    adres = str(kunye.get("calisma_adresi") or "").strip()
    if adres:
        _madde(b, sayac, "İnceleme, Müfettişliğimizin “%s” çalışma adresinde "
                         "yapılmıştır." % adres)
    else:
        _madde(b, sayac, "İnceleme %s yapılmıştır."
               % ik.deger(kunye, "inceleme_yeri").lower())
    _defter_maddesi(b, kunye, sayac)
    _vergi_beyani_maddesi(b, kunye, sayac, donemler)
    _kdv_beyani_maddesi(b, kunye, sayac, donemler)
    if duzeltme:
        _madde(b, sayac, "Mükellef tarafından verilen düzeltme beyannameleri "
                         "aşağıdaki gibidir.")
        _duzeltme_tablosu(b, duzeltme)
    _fatura_maddesi(b, kunye, sayac, satici_satirlari, liste)
    if not satici_satirlari:
        _tespit_maddesi(b, kunye, sayac, yillar, donemler)
    _sorular_maddesi(b, kunye, sayac, satici_satirlari)
    _standart_maddeler(b, kunye, sayac, donemler)

    uyumsuz = belgeye_giren_bulgular(bulgular, donemler)
    if uyumsuz:
        _madde(b, sayac, "Beyan edilen tutarlar üzerinde yapılan aritmetik "
                         "denetimde aşağıdaki hususlar tespit edilmiştir:")
        b.madde_listesi([x["mesaj"] for x in uyumsuz], numarali=False)

    _kapanis(b, kunye)
    b.bos_satir()
    b.paragraf("Bu belge %s tarihinde KDV İnceleme Çalışması uygulamasıyla "
               "taslak olarak üretilmiştir; imzaya hazır nihai belge değildir."
               % _bugun(), italik=True, hiza="orta", buyukluk=9)
    return b


def _duzeltme_tablosu(b, duzeltme):
    for yil_blogu in duzeltme:
        tablo = []
        for s in yil_blogu["satirlar"]:
            tablo.append([s.get("donem") or "", s.get("tarih") or "",
                          _tl(s.get("matrah_toplami")), _tl(s.get("hesaplanan_kdv")),
                          _tl(s.get("onceki_donem_devreden")),
                          _tl(s.get("bu_donem_indirilecek")),
                          _tl(s.get("indirimler_toplami")),
                          _tl(s.get("odenmesi_gereken_kdv")),
                          _tl(s.get("sonraki_donem_devreden")),
                          s.get("gerekce") or ""])
        b.tablo(["Dönemi\n%s" % yil_blogu["yil"], "Düzeltme\nTarihi", "KDV\nMatrahı",
                 "Hspl.\nKDV", "Önc. Dön.\nDev. KDV", "Bu Dön.\nİndl. KDV",
                 "İndirimler\nToplamı", "Öden.\nKDV", "Son. Dön.\nDev. KDV",
                 "Düzeltme Gerekçesi"], tablo,
                hizalar=["sol", "sol"] + ["sag"] * 7 + ["sol"],
                oranlar=[0.8, 0.9, 1.1, 0.9, 1, 1, 1.1, 0.9, 1, 1.8],
                buyukluk=TABLO_PUNTOSU)


def dosya_adi(inceleme):
    ad = "".join(c for c in (inceleme.get("ad_unvan") or "tutanak")
                 if c.isalnum() or c in " -_").strip() or "tutanak"
    return ("Tutanak_taslagi_%s.docx" % ad).replace(" ", "_")
