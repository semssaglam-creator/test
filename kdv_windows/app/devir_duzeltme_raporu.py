"""Devir duzeltme raporu — incelenen yillardan SONRAKI yillar icin.

Sahte belge kullanma raporu bir yilin indirimlerini reddettiginde, o yilin
Aralik ayindan devreden KDV kucululur. Devir zinciri ileriye aktigi icin
INCELENMEYEN sonraki yillarin beyanlari da gercek durumu yansitmaz hale
gelir; kucuk devirle yeniden kurulan zincirde bir donemde odenecek vergi
dogarsa o yil icin AYRI bir rapor duzenlenir. Bu modul o raporu uretir.

Mufettisin verdigi ornek rapordan cikarilan yapi:

  I.   GIRIS                        (mukellef, gorevlendirme, hangi VIR'den
                                     dogdugu)
  II.  USUL INCELEMELERI            (usul tenkitleri asil rapordadir)
  III. HESAP INCELEMELERI           (III.1 mukellefin beyan tablosu)
  IV.  TESPIT VE TENKIT EDILEN HUSUSLAR
         IV.A Re'sen takdir nedeni  (onceki yilin devri degisti)
         IV.B Re'sen takdir verileri
         IV.C Beyanlarin duzeltilmesi (duzeltilmis tablo + tarhiyat)
  V.   SONUC                        (numarali maddeler)

Bu rapor TARHIYAT ONERIR: kendi yilinda dogan fark vergiyi ve bir kat vergi
ziyai cezasini ister. Sahte belge kullanma raporundan ayri durur; o rapor
incelenen yila, bu rapor sonraki yila aittir.

Raporun en onemli cumlesi V. bolumun 3. maddesidir: bu yilin Aralik devri de
degistiginden, SONRAKI yilin Ocak devrinin vergi dairesince duzeltilmesi
istenir. Zincir boylece elle devam ettirilir.
"""
from . import faturalar as F
from . import inceleme_kunyesi as ik
from . import turkce
from .belge_docx import TABLO_PUNTOSU, YER_TUTUCU_RENGI as KIRMIZI, Belge
from .sahte_belge_raporu import _donem_adi, _fatura_yili, _tarhiyat_tablosu
from .tutanak import beyan_dokum_tablosu, dolu_donemler, tarhiyat_toplami

_tl = turkce.tl

# Beyanin gercek durumu yansitmadigina dair delil bulunmasi VUK 30'un 4 ve 6
# numarali bentlerinde re'sen takdir nedeni sayilir; ornek rapor ikisini
# birlikte aniyor ve bu raporun dayanagi tam olarak budur.
RESEN_BENTLER = "4 ve 6 numaralı bendi"


def rapor_yillari(sonuc, liste, saticilar):
    """Devir duzeltme raporu duzenlenecek yillar.

    Olcut UC kosulun birlikte saglanmasi:

      1. O yilda sahte belge YOK. Hakkinda VTR bulunan bir saticidan alinmis
         fatura tasiyan yil INCELENEN yildir; onun belgesi sahte belge
         kullanma raporudur, bu rapor degil. ("dahil" isaretine bakilmaz:
         yil incelenmis mi diye soruluyor, tarhiyata giriyor mu diye degil.)
      2. Onunden gelen devir GERCEKTEN degismis: onceki yilin Aralik ayinda
         beyan edilen devir ile olmasi gereken devir ayrisiyor. Bu raporun
         butun gerekcesi bu ayrisma oldugu icin aranmasi sart. Tek basina
         "fark var" demek yetmez - fark, mufettisin o yila girdigi bir
         matrah ilavesinden ya da beyan verisindeki bir tutarsizliktan da
         dogabilir; o zaman yazilacak belge bu rapor DEGILDIR.
         Onceki yil calismada yoksa devrin degistigi de bilinemez, yil
         secilmez.
      3. O yilda re'sen tarhi gereken bir fark VAR. Devir kuculmesi sonraki
         yillarda her zaman vergi dogurmaz - zincir farki sogurup
         tuketebilir. Fark yoksa tarhiyat da yoktur ve rapor gerekmez;
         devrin sonraki yila tasinmasi zaten onceki raporun sonuc maddesiyle
         isteniyordur.

    "Incelenen yillardan sonraki" kosulu ayrica aranmaz: 2. kosul bunu
    zaten sagliyor, cunku devir ileriye akar.
    """
    sahte_yillar = {_fatura_yili(f) for f in (liste or [])
                    if (saticilar or {}).get(f.get("satici_vkn") or "")}
    sahte_yillar.discard(None)

    donemler = dolu_donemler(sonuc)
    yillar = []
    for yil in sorted({d["yil"] for d in donemler}):
        if yil in sahte_yillar:
            continue
        beyan_devir, olmasi_devir = _onceki_yil_devri(sonuc, yil)
        if beyan_devir is None or olmasi_devir is None:
            continue
        if abs(beyan_devir - olmasi_devir) <= 0.005:
            continue
        fark = sum(float((d.get("tarhiyat") or {}).get("toplam_fark") or 0.0)
                   for d in donemler if d["yil"] == yil)
        if abs(fark) > 0.005:
            yillar.append(yil)
    return yillar


def _onceki_yil_devri(sonuc, yil):
    """Bu yilin onundeki yilin Aralik devri: (beyan edilen, olmasi gereken).

    Raporun butun gerekcesi bu iki sayinin farkidir. Onceki yil calismada
    yoksa (yalnizca sonraki yil girilmisse) None doner ve belge kirmizi yer
    tutucu yazar - uydurulmaz.
    """
    oncekiler = [d for d in dolu_donemler(sonuc) if d["yil"] == yil - 1]
    if not oncekiler:
        return None, None
    son = max(oncekiler, key=lambda d: d["ay"])
    return (son["beyan"].get("sonraki_devir"),
            son["elestirili"].get("sonraki_devir"))


def _aralik_devri(donemler):
    """Bu yilin son doneminin devri: (beyan edilen, olmasi gereken)."""
    if not donemler:
        return None, None
    son = max(donemler, key=lambda d: d["ay"])
    return (son["beyan"].get("sonraki_devir"),
            son["elestirili"].get("sonraki_devir"))


def _vir_ifadesi(kunye, yil):
    """Bu yilin devrini degistiren raporun kunyesi.

    Devir, hemen ONCEKI yilin raporundan gelir; o yilin tarih/sayisi
    kunyedeki "Tarhiyat oneren rapor(lar)" tablosundan okunur. Bulunamazsa
    kirmizi yer tutucu kalir.
    """
    for kayit in ik.vir_kayitlari(kunye):
        if str(kayit.get("yil")) == str(yil - 1):
            return ("%s tarih ve %s sayılı Vergi İnceleme Raporu"
                    % (kayit.get("tarih") or "[rapor tarihi]",
                       kayit.get("sayi") or "[rapor sayısı]"))
    return "[rapor tarihi] tarih ve [rapor sayısı] sayılı Vergi İnceleme Raporu"


def _vir_de(kunye, yil):
    """"...sayılı Vergi İnceleme Raporunda" - bulunma hali.

    "Raporu" tamlama ekiyle bittiginden araya kaynastirma "n"si girer. Eki
    elle eklemek "Raporu'da" gibi bozuk bicimler uretiyor; VSR'de ayni
    kusur bir kez yasandi.
    """
    return _vir_ifadesi(kunye, yil) + "nda"


# ------------------------------------------------------------------ 1) giris
def _giris(b, inceleme, kunye, yil, donemler):
    M = ik.mukellef_sozu
    b.baslik("I- GİRİŞ", duzey=1)

    konular = ik.satirlar(kunye, "faaliyet_konulari")
    b.paragraf(
        "%s %s mükellefi %s (Raporun ilerleyen bölümlerinde %s olarak "
        "bahsedilecektir), %s adresinde %s ile iştigal etmektedir.%s"
        % (ik.vergi_dairesi(inceleme.get("vergi_dairesi"), ek="in"),
           ik.mukellef_kimligi(inceleme, kunye),
           ik.mukellef_adi(inceleme, kunye),
           M(kunye),
           ik.adres(kunye.get("faaliyet_adresi") or inceleme.get("adres")),
           turkce.liste(konular) if konular else "[faaliyet konusu]",
           " Mükellef Vergi Usul Kanununun 107/A maddesi kapsamında "
           "e-tebligata tabidir."
           if ik.secim_mi(kunye, "e_tebligat", "Kapsamda") else ""),
        girinti=1)

    emirler = ik.is_emirleri(kunye)
    b.paragraf(
        "T.C. Hazine ve Maliye Bakanlığı Vergi Denetim Kurulu %s %s ile %s "
        "%s işlemlerinin “Sahte Belge Kullanma” gerekçesiyle sınırlı olarak "
        "incelenmesi istenmiştir."
        % (ik.deger(kunye, "grup_baskanligi", "Denetim Daire Başkanlığının"),
           ik.gorevlendirme_ifadesi(emirler), M(kunye, ek="in"),
           _incelenen_donem_ifadesi(kunye, emirler, yil)), girinti=1)

    b.paragraf(
        "%s %s ait hesap ve işlemlerinin sahte belge ile belgelendirilen "
        "ticari mal alışlarına ilişkin olarak vergi kanunları yönünden "
        "sınırlı olarak incelenmesi sonucunda, %s tanzim edilmiştir. Söz "
        "konusu raporda tespit edilen hususlar nedeniyle %s yılı katma değer "
        "vergisi beyanlarının yeniden düzenlenmesi gereği hasıl olduğundan, "
        "ayrıca bu rapor tanzim edilmiştir."
        % (M(kunye, buyuk=True, ek="in"),
           _incelenen_donem_ifadesi(kunye, emirler, yil, "yonelme"),
           _vir_ifadesi(kunye, yil), yil), girinti=1)


def _incelenen_donem_ifadesi(kunye, emirler, yil, hal="yalin"):
    """Bu raporun DAYANDIGI incelenen donem; bu raporun yili DEGIL.

    Devir hemen onceki yildan geldigi icin olcut odur. Is emirlerinde donem
    yaziliysa oradan da dogrulanabilir ama tek dogru kaynak zincirdir.
    """
    return "%s %s" % (yil - 1, ik.donem_adi(kunye, False, hal))


# -------------------------------------------------------------- 2) usul
def _usul(b, kunye, yil):
    b.baslik("II- USUL İNCELEMELERİ", duzey=1)
    b.paragraf(
        "Usul yönünden eleştirilen hususlara %s yer verildiğinden burada "
        "ayrıca bahsedilmeyecektir." % _vir_de(kunye, yil), girinti=1)


# -------------------------------------------------------------- 3) hesap
def _hesap(b, kunye, yil, donemler):
    M = ik.mukellef_sozu
    b.baslik("III- HESAP İNCELEMELERİ", duzey=1)
    b.baslik("III.1- Mükellefin Katma Değer Vergisi Beyanı", duzey=2)
    b.paragraf(
        "%s GİB Yönetim Bilgi Sistemleri (YBS) kayıtlarından tespit edildiği "
        "üzere %s yılı vergilendirme dönemleri itibarıyla katma değer vergisi "
        "beyanları aşağıdaki tabloda olduğu gibidir."
        % (M(kunye, buyuk=True, ek="in"), yil), girinti=1)
    beyan_dokum_tablosu(b, donemler, "beyan")


# ----------------------------------------------------------- 4) tenkit
def _tenkit(b, kunye, inceleme, yil, donemler, sonuc):
    M = ik.mukellef_sozu
    b.baslik("IV- TESPİT VE TENKİT EDİLEN HUSUSLAR", duzey=1)

    beyan_devir, olmasi_devir = _onceki_yil_devri(sonuc, yil)
    devir_metni = (_tl(olmasi_devir) + "-TL" if olmasi_devir is not None
                   else "[önceki yılın devri]")

    # ---- IV.A re'sen takdir nedeni
    b.baslik("IV.A- Re’sen Takdir Nedeni", duzey=2)
    b.paragraf(
        "%s %s hesap ve işlemlerinin sınırlı incelenmesi neticesinde tanzim "
        "edilen vergi inceleme raporunda %s Aralık dönemi sonraki döneme "
        "devreden katma değer vergisi tutarı %s olarak değişmiş olduğundan "
        "%s yılı katma değer vergisi beyanlarının da düzeltilmesi "
        "gerekmektedir. Bu durumda %s yılında verilen katma değer vergisi "
        "beyannameleri gerçek durumu yansıtmamaktadır."
        # "Kurumun ... doneminin hesap ve islemlerinin" ust uste iki ilgi eki
        # oluyordu; donem yalin kalmali ("2022 hesap donemi hesap ve
        # islemlerinin"), ornek rapor da boyle yaziyor.
        % (M(kunye, buyuk=True, ek="in"),
           "%s %s" % (yil - 1, ik.donem_adi(kunye, False)),
           yil - 1, devir_metni, yil, yil),
        girinti=1, renk=KIRMIZI if olmasi_devir is None else None)
    b.paragraf(
        "Öte yandan verilen beyannamelerin gerçek durumu yansıtmadığına dair "
        "delil bulunması 213 sayılı Vergi Usul Kanunu’nun 30. maddesinin %s "
        "gereğince re’sen takdir nedeni sayıldığından, ilgili madde kapsamında "
        "%s %s yılı katma değer vergisi matrahlarının re’sen takdir edilmesi "
        "ve bulunacak vergi farklarının da re’sen tarh edilmesi gerekmektedir."
        % (RESEN_BENTLER, M(kunye, ek="in"), yil), girinti=1)

    # ---- IV.B re'sen takdir verileri
    b.baslik("IV.B- Re’sen Takdir Verileri", duzey=2)
    b.paragraf(
        "%s %s ilişkin hesap ve işlemlerinin sınırlı incelenmesi neticesinde "
        "Müfettişliğimiz tarafından tanzim edilen %s, %s tarafından sahte "
        "belge kullanılması nedeniyle %s yılında yersiz olarak indirim konusu "
        "yapıldığı tespit edilen katma değer vergisi tutarları ilgili dönem "
        "indirilecek katma değer vergisi hesaplarından çıkarılmış ve reddi "
        "gereken katma değer vergisi indirimleri dikkate alınarak %s "
        "dönemlerine ilişkin katma değer vergisi beyanları yeniden "
        "düzenlenmiştir."
        % (M(kunye, buyuk=True, ek="in"),
           "%s %s" % (yil - 1, ik.donem_adi(kunye, False, "yonelme")),
           _vir_de(kunye, yil), M(kunye), yil - 1,
           _donem_araligi(yil, donemler)), girinti=1)
    b.paragraf(
        "%s söz konusu dönemlerine ilişkin katma değer vergisi beyanlarının "
        "yeniden düzenlenmesi neticesinde %s Aralık döneminde sonraki döneme "
        "devreden katma değer vergisi tutarı %s olarak belirlenmiştir."
        % (M(kunye, buyuk=True, ek="in"), yil - 1, devir_metni),
        girinti=1, renk=KIRMIZI if olmasi_devir is None else None)

    # ---- IV.C duzeltme ve yapilacak islemler
    b.baslik("IV.C- Mükellefin Katma Değer Vergisi Beyanlarının Düzeltilmesi "
             "ve Yapılacak İşlemler", duzey=2)
    b.paragraf(
        "%s %s ilişkin Müfettişliğimizce düzenlenen %s, Aralık/%s döneminden "
        "Ocak/%s dönemine önceki dönemden devreden katma değer vergisi "
        "tutarının mükellefin beyanında yer aldığı üzere %s olmayıp %s "
        "olduğundan, %s yılı katma değer vergisi beyanları Müfettişliğimizce "
        "düzeltilecektir."
        % (M(kunye, buyuk=True, ek="in"),
           "%s %s" % (yil - 1, ik.donem_adi(kunye, False, "yonelme")),
           _vir_de(kunye, yil), yil - 1, yil,
           (_tl(beyan_devir) + "-TL" if beyan_devir is not None
            else "[beyan edilen devir]"),
           devir_metni, yil),
        girinti=1,
        renk=KIRMIZI if None in (beyan_devir, olmasi_devir) else None)
    b.paragraf(
        "Buna göre, %s %s yılı vergilendirme dönemi katma değer vergisi "
        "beyanları Müfettişliğimizce aşağıdaki şekilde yeniden "
        "düzenlenmiştir." % (M(kunye, ek="in"), yil), girinti=1)
    beyan_dokum_tablosu(b, donemler, "elestirili")

    # Bu yilin Aralik devri de degisti; zincirin sonraki yila tasinmasi
    # istenmeli, yoksa duzeltme bu yilda kesilir.
    _devir_devam_paragrafi(b, kunye, yil, donemler)

    tarhiyatli = _tarhiyatli_donemler(donemler)
    b.paragraf(
        "Yukarıdaki tablonun tetkik edilmesinden görüleceği üzere, yapılan "
        "düzeltmeler sonucunda; aşağıda belirtilen dönem itibarıyla ortaya "
        "çıkan, ödenmesi gereken katma değer vergisinden, %s söz konusu "
        "dönemde beyan ettiği ödenmesi gereken katma değer vergisinin tenzili "
        "suretiyle bulunan katma değer vergisi tutarı aşağıdaki tablodaki "
        "gibidir." % M(kunye, ek="in"), girinti=1)
    _tarhiyat_tablosu(b, tarhiyatli)
    b.paragraf(
        "Ayrıca %s adına re’sen tarh edilecek katma değer vergisi üzerinden "
        "213 sayılı Vergi Usul Kanunu’nun 341. ve 344. maddeleri gereği vergi "
        "ziyaına sebebiyet verildiğinden 1 (bir) kat vergi ziyaı cezası "
        "kesilmesi gerekmektedir." % M(kunye), girinti=1)


def _devir_devam_paragrafi(b, kunye, yil, donemler):
    """"...2024/Ocak donemi onceki donemden devreden KDV ... dikkate alinmali"

    Bu rapor zincirin bir halkasidir: kendi yilini duzeltirken bir sonraki
    yilin baslangic devrini de degistirir. Cumle yazilmazsa duzeltme bu
    yilda kesilir ve sonraki yil yine yanlis devirle kalir.
    """
    beyan_devir, olmasi_devir = _aralik_devri(donemler)
    if beyan_devir is None or olmasi_devir is None:
        return
    b.paragraf(
        "Yukarıdaki tablonun tetkik edilmesinden görüleceği üzere, yapılan "
        "düzeltmeler sonucunda; %s %s/Aralık döneminde sonraki döneme "
        "devreden katma değer vergisi tutarı %s-TL olmayıp %s-TL olduğundan, "
        "%s/Ocak dönemi önceki dönemden devreden katma değer vergisi tutarı "
        "%s-TL olarak dikkate alınmalı ve %s yılı katma değer vergisi "
        "beyanları buna göre düzeltilmelidir."
        % (ik.mukellef_sozu(kunye, ek="in"), yil, _tl(beyan_devir),
           _tl(olmasi_devir), yil + 1, _tl(olmasi_devir), yil + 1),
        girinti=1)


def _donem_araligi(yil, donemler):
    """"2023/1-12" gibi; girilen ay sayisina gore daralir."""
    aylar = sorted(d["ay"] for d in donemler)
    if not aylar:
        return "%s/1-12" % yil
    if aylar[0] == aylar[-1]:
        return "%s/%d" % (yil, aylar[0])
    return "%s/%d-%d" % (yil, aylar[0], aylar[-1])


def _tarhiyatli_donemler(donemler):
    """Farki olan donemler. Tablo yalnizca bunlari tasir."""
    return [d for d in donemler
            if abs(float((d.get("tarhiyat") or {}).get("toplam_fark") or 0.0))
            > 0.005]


# ------------------------------------------------------------------ 5) sonuc
def _sonuc(b, inceleme, kunye, yil, donemler):
    M = ik.mukellef_sozu
    b.baslik("V- SONUÇ", duzey=1)
    b.paragraf(
        "%s %s mükellefi %s’nin %s yılı vergilendirme dönemleri katma değer "
        "vergisi beyanlarının 213 sayılı Vergi Usul Kanunu’nun 116. ve "
        "müteakip maddeleri gereğince düzeltilmesi neticesinde,"
        % (ik.vergi_dairesi(inceleme.get("vergi_dairesi"), ek="in"),
           ik.mukellef_kimligi(inceleme, kunye),
           ik.mukellef_adi(inceleme, kunye), yil), girinti=1)

    tarhiyatli = _tarhiyatli_donemler(donemler)
    toplam = tarhiyat_toplami(tarhiyatli)

    # Maddeler, agacin diger raporlarinda oldugu gibi "N- " oneki metnin
    # kendisinde tasinarak kuruluyor; `madde_listesi` bir tabloyu maddelerin
    # ARASINA koyamadigi icin paragraflar elle yaziliyor.
    maddeler = [
        "1- Raporun (IV.C) bölümünde açıklandığı üzere, 213 sayılı Vergi Usul "
        "Kanunu’nun 30. maddesinin %s gereğince aşağıdaki tabloda %s için "
        "hesap edilen fark katma değer vergisinin %s adına re’sen tarh "
        "edilmesi gerektiği,"
        % (RESEN_BENTLER, _donem_listesi(tarhiyatli), M(kunye)),
        "2- Raporun (IV.C) bölümünde açıklandığı üzere, tarhı gereken %s TL "
        "katma değer vergisi için 213 sayılı Vergi Usul Kanunu’nun 341. ve "
        "344. maddeleri gereği 1 (bir) kat vergi ziyaı cezası kesilmesi "
        "gerektiği," % _tl(toplam.get("resen_tarhi_gereken")),
    ]
    madde = _devir_devam_maddesi(kunye, yil, donemler)
    if madde:
        maddeler.append("%d- %s" % (len(maddeler) + 1, madde))
    if ik.secim_mi(kunye, "tou_talebi", "Talep edildi"):
        maddeler.append("%d- Mükellefin tarhiyat öncesi uzlaşma talebinin "
                        "dikkate alınması gerektiği," % (len(maddeler) + 1))

    # Tarhiyat tablosu, maddelerin sonunda degil kendisini oneren maddenin
    # hemen altinda durur (agacin diger raporlarinda da boyle).
    for sira, metin in enumerate(maddeler):
        b.paragraf(metin, kalin=True, girinti=1, aralik_sonra=100)
        if tarhiyatli and sira == 0:
            _tarhiyat_tablosu(b, tarhiyatli)

    b.paragraf("Kanaat ve sonucuna varılmıştır.", girinti=1, aralik_once=120)
    b.bos_satir()
    b.imza_bloklari([(ik.deger(kunye, "eleman_unvan", "unvan"),
                      ik.ad(kunye, "eleman_ad"))])


def _devir_devam_maddesi(kunye, yil, donemler):
    """Sonuc bolumunun "sonraki yilin Ocak devri duzeltilsin" maddesi.

    Bu raporun en islevsel maddesi: tarhiyat vergi dairesine bildirilirken
    devrin de duzeltilmesi istenir, yoksa zincir orada kopar.
    """
    beyan_devir, olmasi_devir = _aralik_devri(donemler)
    if beyan_devir is None or olmasi_devir is None:
        return None
    return ("Raporun (IV.C) bölümünde belirtildiği üzere, %s %s/Aralık "
            "döneminde sonraki döneme devreden katma değer vergisi tutarı "
            "%s-TL olmayıp %s-TL olduğundan, %s/Ocak dönemi önceki dönemden "
            "devreden katma değer vergisi tutarının %s-TL olarak dikkate "
            "alınması ve %s/Ocak dönemi katma değer vergisi beyannamesinin "
            "buna göre vergi dairesince düzeltilmesi gerektiği,"
            % (ik.mukellef_sozu(kunye, ek="in"), yil, _tl(beyan_devir),
               _tl(olmasi_devir), yil + 1, _tl(olmasi_devir), yil + 1))


def _donem_listesi(tarhiyatli):
    """"2023/Temmuz donemi" / "belirtilen donemler".

    Donem sayisi azsa adlari yazilir. Devir eridikce yilin yarisinda vergi
    dogabiliyor; sekiz donemi cumle icinde saymak, hemen altindaki tablonun
    zaten gosterdigi seyi tekrar ediyordu.
    """
    if not tarhiyatli:
        return "[dönem]"
    adlar = [_donem_adi(d) for d in tarhiyatli]
    if len(adlar) > 3:
        return "belirtilen dönemler"
    return "%s dönem%s" % (turkce.liste(adlar),
                           "i" if len(adlar) == 1 else "leri")


# ------------------------------------------------------------------- uretim
def rapor_uret(inceleme, kunye, sonuc, calisma, yil):
    """Bir yilin devir duzeltme raporunu uretir ve `Belge` dondurur."""
    kunye = ik.normalize(kunye)
    yil = int(yil)
    donemler = [d for d in dolu_donemler(sonuc) if d["yil"] == yil]

    b = Belge()
    _giris(b, inceleme, kunye, yil, donemler)
    _usul(b, kunye, yil)
    _hesap(b, kunye, yil, donemler)
    _tenkit(b, kunye, inceleme, yil, donemler, sonuc)
    _sonuc(b, inceleme, kunye, yil, donemler)
    return b


def dosya_adi(inceleme, yil):
    ad = "".join(c for c in (inceleme.get("ad_unvan") or "rapor")
                 if c.isalnum() or c in " -_").strip() or "rapor"
    return ("Devir_duzeltme_raporu_taslagi_%s_%s.docx"
            % (yil, ad)).replace(" ", "_")
