"""Inceleme kunyesi: tutanak ve rapor taslaklarinin gerektirdigi kimlik bilgisi.

Beyan verisi ve tespitler uygulamada zaten var; eksik olan, belgelerin hukuki
iskeletini kuran bilgilerdi: gorevlendirme yazisi, inceleme turu ve gerekcesi,
nezdinde inceleme yapilan kisi, usul bulgulari, tutanaga ozgu alanlar.

Alanlar burada tek bir yerde bildirilir. Arayuz formu bu bildirimden uretilir;
belge uretenler ayni bildirimden okur. Boylece yeni bir alan eklemek icin tek
dosya degistirmek yeter.

Kunye, calisma JSON'unun icinde "kunye" anahtariyla saklanir; veritabani
semasi degismez.
"""

# Alan turleri:
#   metin  : tek satir
#   uzun   : cok satirli serbest metin
#   tarih  : gg.aa.yyyy beklenir, dogrulanmaz (taslak icin serbest birakildi)
#   secim  : seceneklerden biri
#   sayi   : tam sayi
BOLUMLER = [
    {
        "kod": "gorevlendirme",
        "baslik": "Görevlendirme ve İnceleme",
        "alanlar": [
            {"kod": "gorevlendirme_no", "etiket": "Görevlendirme yazısı no", "tur": "metin"},
            {"kod": "gorevlendirme_tarihi", "etiket": "Görevlendirme yazısı tarihi",
             "tur": "tarih"},
            {"kod": "inceleme_dosya_no", "etiket": "İnceleme dosya no", "tur": "metin"},
            {"kod": "rapor_no", "etiket": "Rapor no", "tur": "metin"},
            {"kod": "baslama_tarihi", "etiket": "İncelemeye başlama tarihi", "tur": "tarih"},
            {"kod": "inceleme_turu", "etiket": "İnceleme türü", "tur": "secim",
             "secenekler": ["Tam inceleme", "Sınırlı inceleme"],
             "varsayilan": "Sınırlı inceleme"},
            {"kod": "inceleme_gerekce", "etiket": "İnceleme gerekçesi", "tur": "secim",
             "secenekler": ["İhbar", "Karşıt inceleme", "Risk analizi",
                            "İade talebi", "Diğer"],
             "varsayilan": "Karşıt inceleme"},
            {"kod": "inceleme_yeri", "etiket": "İncelemenin yapıldığı yer", "tur": "secim",
             "secenekler": ["Mükellefin iş yerinde", "Dairede", "Uzaktan"],
             "varsayilan": "Dairede"},
            {"kod": "inceleme_konusu", "etiket": "İnceleme konusu", "tur": "metin",
             "varsayilan": "Katma Değer Vergisi yönünden",
             "ipucu": "Belgede \"... yönünden inceleme\" biçiminde geçer."},
            {"kod": "is_emirleri", "etiket": "İş emirleri (birden çoksa)", "tur": "uzun",
             "ipucu": "Her satıra bir iş emri; alanları dikey çizgiyle ayırın: "
                      "tarih | sayı | dönem | konu. Örn: "
                      "28.05.2024 | 23929873-663.05[31848]-22046 | 2023 | Sahte Belge Kullanma. "
                      "Doldurulursa belgeye tablo olarak girer."},
            {"kod": "mukellef_turu", "etiket": "Mükellef türü", "tur": "secim",
             "secenekler": ["Kurum (sermaye şirketi)", "Gerçek kişi"],
             "varsayilan": "Kurum (sermaye şirketi)",
             "ipucu": "Belgede \"mükellef kurum\" mu \"mükellef\" mi denileceğini ve "
                      "kurumlar vergisi mi gelir vergisi mi yazılacağını belirler."},
        ],
    },
    {
        "kod": "mukellef_ek",
        "baslik": "Mükellefe İlişkin Ek Bilgiler",
        "alanlar": [
            {"kod": "faaliyet_konusu", "etiket": "Faaliyet konusu", "tur": "metin",
             "ipucu": "Örn: yapı malzemesi alım satımı"},
            {"kod": "nace_kodu", "etiket": "NACE kodu", "tur": "metin"},
            {"kod": "ise_baslama_tarihi", "etiket": "İşe başlama tarihi", "tur": "tarih"},
            {"kod": "kanuni_temsilci", "etiket": "Kanuni temsilci / ortaklar", "tur": "uzun"},
            {"kod": "e_tebligat", "etiket": "e-Tebligat", "tur": "secim",
             "secenekler": ["Kapsamda", "Kapsamda değil"], "varsayilan": "Kapsamda"},
            {"kod": "e_defter", "etiket": "e-Defter / e-Fatura", "tur": "secim",
             "secenekler": ["Kapsamda", "Kapsamda değil"], "varsayilan": "Kapsamda"},
        ],
    },
    {
        "kod": "taraflar",
        "baslik": "Nezdinde İnceleme Yapılan ve İnceleme Elemanı",
        "alanlar": [
            {"kod": "nezdinde_ad", "etiket": "Nezdinde inceleme yapılan (ad soyad)",
             "tur": "metin"},
            {"kod": "nezdinde_sifat", "etiket": "Sıfatı", "tur": "secim",
             "secenekler": ["Kanuni temsilci", "Şirket müdürü", "Ortak",
                            "Serbest muhasebeci mali müşavir", "Vekil", "Mükellefin kendisi"],
             "varsayilan": "Kanuni temsilci"},
            {"kod": "nezdinde_tckn", "etiket": "T.C. kimlik no", "tur": "metin"},
            {"kod": "eleman_ad", "etiket": "İncelemeyi yapan (ad soyad)", "tur": "metin"},
            {"kod": "eleman_unvan", "etiket": "Unvanı", "tur": "secim",
             "secenekler": ["Vergi Müfettişi", "Vergi Müfettiş Yardımcısı",
                            "Vergi Denetim Kurulu Başkanlığı Vergi Müfettişi"],
             "varsayilan": "Vergi Müfettişi"},
            {"kod": "eleman_sicil", "etiket": "Sicil no", "tur": "metin"},
            {"kod": "grup_baskanligi", "etiket": "Grup başkanlığı", "tur": "metin"},
        ],
    },
    {
        "kod": "usul",
        "baslik": "Usul Bulguları",
        "alanlar": [
            {"kod": "defter_tasdik", "etiket": "Defter tasdik durumu", "tur": "secim",
             "secenekler": ["Usulüne uygun", "Eksik / usulsüz", "Tasdik ettirilmemiş",
                            "Tespit edilemedi"],
             "varsayilan": "Usulüne uygun"},
            {"kod": "defter_ibraz", "etiket": "Defter ve belge ibrazı", "tur": "secim",
             "secenekler": ["İbraz edildi", "Kısmen ibraz edildi", "İbraz edilmedi"],
             "varsayilan": "İbraz edildi"},
            {"kod": "beyanname_durumu", "etiket": "Beyannamelerin verilmesi", "tur": "secim",
             "secenekler": ["Süresinde verilmiş", "Bir kısmı geç verilmiş",
                            "Verilmemiş"],
             "varsayilan": "Süresinde verilmiş"},
            {"kod": "usulsuzluk", "etiket": "Usulsüzlük tespiti", "tur": "secim",
             "secenekler": ["Yok", "Birinci derece usulsüzlük", "İkinci derece usulsüzlük",
                            "Özel usulsüzlük (VUK 353)"],
             "varsayilan": "Yok"},
            {"kod": "usul_notu", "etiket": "Usul incelemesine ilişkin not", "tur": "uzun",
             "ipucu": "Belgeye olduğu gibi aktarılır."},
            {"kod": "ouc_uygula", "etiket": "Özel usulsüzlük (tevsik) hesaplansın",
             "tur": "secim", "secenekler": ["Hayır", "Evet"], "varsayilan": "Hayır",
             "ipucu": "Faturalar sekmesinde \"tevsik edilmemiş\" işaretlenen "
                      "faturalardan VUK mükerrer 355 cezası hesaplanır."},
            {"kod": "ouc_alt_had", "etiket": "Özel usulsüzlük alt haddi (TL)",
             "tur": "metin",
             "ipucu": "İlgili yıl için VUK mükerrer 355 alt haddi. 2023 için "
                      "7.500 (544 Sıra No'lu Tebliğ). Uygulama yıl yıl tahmin etmez."},
            {"kod": "ouc_ust_sinir", "etiket": "Bir hesap dönemi üst sınırı (TL)",
             "tur": "metin",
             "ipucu": "2023 için 5.500.000. Boş bırakılırsa sınır uygulanmaz."},
        ],
    },
    {
        "kod": "tutanak",
        "baslik": "Tutanağa Özgü Bilgiler",
        "alanlar": [
            {"kod": "tutanak_tarihi", "etiket": "Tutanak tarihi", "tur": "tarih"},
            {"kod": "tutanak_yeri", "etiket": "Tutanağın düzenlendiği yer", "tur": "metin",
             "ipucu": "Belgede \"... adresinde düzenlenmiş\" biçiminde geçer; "
                      "adres olarak yazınız."},
            {"kod": "tutanak_nusha", "etiket": "Nüsha sayısı", "tur": "sayi",
             "varsayilan": 2},
            {"kod": "hazir_bulunanlar", "etiket": "Hazır bulunanlar", "tur": "uzun",
             "ipucu": "Her satıra bir kişi: ad soyad, sıfat."},
            {"kod": "sorular", "etiket": "Sorulan hususlar ve alınan cevaplar",
             "tur": "uzun",
             "ipucu": "Her satır belgede ayrı bir madde olarak numaralanır."},
            {"kod": "mukellef_beyani", "etiket": "Mükellefin beyanı / itirazı", "tur": "uzun"},
            {"kod": "tutanak_sayfa", "etiket": "Tutanak sayfa sayısı", "tur": "sayi",
             "varsayilan": 3},
            {"kod": "calisma_adresi", "etiket": "Müfettişliğin çalışma adresi",
             "tur": "metin",
             "ipucu": "Tutanakta “İnceleme, Müfettişliğimizin ... çalışma "
                      "adresinde yapılmıştır.” cümlesinde geçer."},
            {"kod": "defter_bilgileri", "etiket": "İbraz edilen defterler", "tur": "uzun",
             "ipucu": "Her satıra bir defter; alanları dikey çizgiyle ayırın: "
                      "yıl | defterin türü | tasdik tarihi ve numarası | tasdik makamı. "
                      "Örn: 2023 | Yevmiye Defteri | 25.12.2022 - 55555 | Mersin 17. Noterliği"},
            {"kod": "vergi_beyan_ozeti",
             "etiket": "Gelir / Kurumlar Vergisi beyanname özeti", "tur": "uzun",
             "ipucu": "Her satıra bir kalem: açıklama | tutar. Örn: "
                      "Ticari Kazançlar | 13.019,63"},
            {"kod": "muhasebe_kaydi", "etiket": "Faturaların muhasebe kaydı", "tur": "uzun",
             "ipucu": "Fatura tablosunun altına girer. Örn: alışların 153-Ticari "
                      "Mallar ile 191-İndirilecek KDV hesaplarına borç, 320-Satıcılar "
                      "hesabına alacak kaydedildiği."},
            {"kod": "rdk_dinlenme", "etiket": "Rapor Değerlendirme Komisyonunda dinlenme",
             "tur": "secim",
             "secenekler": ["Dinlenme talebi yoktur.", "Dinlenme talebi vardır."],
             "varsayilan": "Dinlenme talebi yoktur."},
            {"kod": "taslak_tutanak", "etiket": "Taslak tutanak talebi", "tur": "secim",
             "secenekler": ["Taslak tutanak talebim bulunmamaktadır.",
                            "Taslak tutanak talep ediyorum."],
             "varsayilan": "Taslak tutanak talebim bulunmamaktadır."},
            {"kod": "ozelge_cevabi", "etiket": "Özelge bulunup bulunmadığı", "tur": "secim",
             "secenekler": ["Yoktur.", "Vardır."], "varsayilan": "Yoktur."},
            {"kod": "baskaca_itiraz", "etiket": "Başkaca itiraz ve mülahaza",
             "tur": "secim", "secenekler": ["Yoktur.", "Vardır."],
             "varsayilan": "Yoktur."},
        ],
    },
    {
        "kod": "rapor",
        "baslik": "Rapora İlişkin Tercihler",
        "alanlar": [
            {"kod": "resen_madde", "etiket": "Re'sen takdir nedeni", "tur": "secim",
             "secenekler": ["VUK 30/6 - beyanname gerçek durumu yansıtmıyor",
                            "VUK 30/4 - defter ve belgeler ihticaca salih değil",
                            "VUK 30/7 - diğer hâller"],
             "varsayilan": "VUK 30/6 - beyanname gerçek durumu yansıtmıyor"},
            {"kod": "uzlasma_notu", "etiket": "Uzlaşma notu eklensin", "tur": "secim",
             "secenekler": ["Evet", "Hayır"], "varsayilan": "Evet"},
            {"kod": "duzeltme_notu", "etiket": "Beyanname düzeltme notu eklensin",
             "tur": "secim", "secenekler": ["Evet", "Hayır"], "varsayilan": "Hayır"},
            {"kod": "tou_talebi", "etiket": "Tarhiyat öncesi uzlaşma talebi",
             "tur": "secim",
             "secenekler": ["Talep edilmedi", "Talep edildi"],
             "varsayilan": "Talep edilmedi",
             "ipucu": "Bilerek kullanmada VUK Ek 11 uyarınca uzlaşma kapsamı "
                      "dışında kalındığı ayrıca yazılır."},
            {"kod": "imzaya_davet", "etiket": "İmzaya davet / gıyabi tutanak notu",
             "tur": "uzun",
             "ipucu": "Mükellef imzaya gelmediyse davet yazısının tarih-sayısı ve "
                      "tutanağın gıyapta düzenlendiği buraya yazılır; giriş "
                      "bölümüne olduğu gibi girer."},
            {"kod": "temsilci_tckn", "etiket": "Kanuni temsilci T.C. kimlik no",
             "tur": "metin",
             "ipucu": "Bilerek kullanmada suç duyurusu paragrafında geçer."},
            {"kod": "sonuc_notu", "etiket": "Sonuç bölümü tespit notu", "tur": "uzun",
             "ipucu": "V- SONUÇ bölümünün sonuna, numaralı maddelerden sonra "
                      "girer. Boş bırakılırsa belgede kırmızı yer tutucu kalır."},
            {"kod": "bilerek_gerekce", "etiket": "Bilerek kullanma değerlendirmesi",
             "tur": "uzun",
             "ipucu": "Orana ek olarak yazılacak gerekçe. Oran uygulamaca "
                      "hesaplanıp cümleye kendiliğinden eklenir."},
        ],
    },
]

# Taslagin anlamli olmasi icin gercekten gereken alanlar. Eksikse belge yine
# uretilir; kullanici uyarilir ve belgede koseli parantezli bir yer tutucu kalir.
ONEMLI_ALANLAR = [
    "gorevlendirme_no", "gorevlendirme_tarihi", "inceleme_turu", "inceleme_gerekce",
    "nezdinde_ad", "eleman_ad", "tutanak_tarihi", "tutanak_yeri", "faaliyet_konusu",
]

_ALANLAR = {a["kod"]: a for b in BOLUMLER for a in b["alanlar"]}


def alan(kod):
    return _ALANLAR.get(kod)


def bos_kunye():
    """Varsayilanlariyla dolu bos bir kunye uretir."""
    return {kod: a.get("varsayilan", "") for kod, a in _ALANLAR.items()}


def normalize(ham):
    """Istemciden gelen kunyeyi tanimli alanlara indirger ve turlerini duzeltir.

    Tanimsiz anahtarlar atilir: belge uretimi yalnizca bildigi alanlara
    dayansin, arayuzden gelen artik veri belgeye sizmasin.
    """
    ham = ham or {}
    kunye = {}
    for kod, tanim in _ALANLAR.items():
        deger = ham.get(kod, tanim.get("varsayilan", ""))
        if tanim["tur"] == "sayi":
            try:
                kunye[kod] = int(deger)
            except (TypeError, ValueError):
                kunye[kod] = tanim.get("varsayilan") or 0
        else:
            kunye[kod] = ("" if deger is None else str(deger)).strip()
    return kunye


def eksik_alanlar(kunye):
    """Doldurulmasi onerilen ama bos birakilmis alanlarin etiketlerini verir."""
    kunye = kunye or {}
    return [_ALANLAR[k]["etiket"] for k in ONEMLI_ALANLAR
            if not str(kunye.get(k) or "").strip()]


def deger(kunye, kod, yer_tutucu=None):
    """Bir alanin degerini verir; bos ise koseli parantezli yer tutucu dondurur.

    Yer tutucu bilerek gozle gorulur birakilir: taslagi okuyan kisi neyi
    doldurmasi gerektigini belgenin uzerinde gorsun, sessizce bos kalmasin.
    """
    d = str((kunye or {}).get(kod) or "").strip()
    if d:
        return d
    tanim = _ALANLAR.get(kod)
    return "[%s]" % (yer_tutucu or (tanim["etiket"] if tanim else kod))


def satirlar(kunye, kod):
    """Cok satirli bir alani bos satirlardan arindirilmis listeye cevirir."""
    ham = str((kunye or {}).get(kod) or "")
    return [s.strip() for s in ham.replace("\r\n", "\n").split("\n") if s.strip()]


# `satirlar` adi asagida yerel degiskenlerle cakistigi icin ikinci bir ad
satirlar_al = satirlar


def secim_mi(kunye, kod, beklenen):
    """Secim alaninin belirli bir degerde olup olmadigini soyler."""
    return str((kunye or {}).get(kod) or "").strip() == beklenen


def is_emirleri(kunye):
    """Serbest metne yazilan is emirlerini tabloya cevirir.

    Her satir "tarih | sayi | donem | konu" bicimindedir; eksik alanlar bos
    birakilir. Tek bir is emri varsa kullanici bu alani doldurmaz, belge
    gorevlendirme yazisini cumle icinde yazar.
    """
    satirlar = []
    for ham in satirlar_al(kunye, "is_emirleri"):
        parcalar = [p.strip() for p in ham.replace("\t", "|").split("|")]
        parcalar += [""] * (4 - len(parcalar))
        satirlar.append({"tarih": parcalar[0], "sayi": parcalar[1],
                         "donem": parcalar[2], "konu": parcalar[3] or "Sahte Belge Kullanma"})
    return satirlar


def cizgili_satirlar(kunye, kod, alan_sayisi):
    """Dikey cizgiyle ayrilmis cok satirli alani tabloya cevirir.

    Eksik alanlar bos birakilir; fazlasi son alana eklenmez, atilir. Sekme
    karakteri de ayirac sayilir (Excel'den yapistirma kolaylasir).
    """
    tablo = []
    for ham in satirlar_al(kunye, kod):
        parcalar = [p.strip() for p in ham.replace("\t", "|").split("|")]
        parcalar += [""] * (alan_sayisi - len(parcalar))
        tablo.append(parcalar[:alan_sayisi])
    return tablo


def kurum_mu(kunye):
    """Belgede "mükellef kurum" mu yoksa "mükellef" mi denecegini soyler."""
    return not secim_mi(kunye, "mukellef_turu", "Gerçek kişi")


def mukellef_sozu(kunye, buyuk=False, ek=""):
    """Metinde mukelleften soz eden kaliplari uretir.

    Kurum ise "Mükellef Kurum" / "Mükellef Kurumun", gercek kisi ise
    "mükellef" / "mükellefin" yazilir. Gercek kisiyi "mükellef kurum" diye
    anmak, kurumlar vergisi bolumlerinin de yanlis kurulmasina yol acar.
    """
    if kurum_mu(kunye):
        govde = "Mükellef Kurum" if buyuk else "mükellef kurum"
        return govde + {"": "", "in": "un", "a": "a", "u": "u"}.get(ek, ek)
    govde = "Mükellef" if buyuk else "mükellef"
    return govde + {"": "", "in": "in", "a": "e", "u": "i"}.get(ek, ek)


def gelir_vergisi_adi(kunye):
    """Kurumda "kurumlar vergisi", gercek kiside "gelir vergisi"."""
    return "kurumlar vergisi" if kurum_mu(kunye) else "gelir vergisi"


# Sirketlerde donem "hesap donemi", gercek kisilerde "takvim yili" diye anilir.
# Ikisi ayni eki almadigi icin (donemine / yilina) cekimli halleri hazir tutulur.
_DONEM_ADLARI = {
    # (kurum_mu, cogul_mu): {hal: sozcuk}
    (True, False): {"yalin": "hesap dönemi", "yonelme": "hesap dönemine",
                    "bulunma": "hesap döneminde", "ilgi": "hesap döneminin"},
    (True, True): {"yalin": "hesap dönemleri", "yonelme": "hesap dönemlerine",
                   "bulunma": "hesap dönemlerinde", "ilgi": "hesap dönemlerinin"},
    (False, False): {"yalin": "takvim yılı", "yonelme": "takvim yılına",
                     "bulunma": "takvim yılında", "ilgi": "takvim yılının"},
    (False, True): {"yalin": "takvim yılları", "yonelme": "takvim yıllarına",
                    "bulunma": "takvim yıllarında", "ilgi": "takvim yıllarının"},
}


def donem_adi(kunye, cogul=False, hal="yalin"):
    """"hesap dönemi" / "takvim yılı" ve cekimli halleri."""
    return _DONEM_ADLARI[(kurum_mu(kunye), bool(cogul))].get(
        hal, _DONEM_ADLARI[(kurum_mu(kunye), bool(cogul))]["yalin"])


def resen_madde_kodu(kunye):
    """Secilen re'sen takdir nedeninden madde numarasini ayiklar (orn '30/6')."""
    secim = str((kunye or {}).get("resen_madde") or "")
    for kod in ("30/4", "30/6", "30/7"):
        if kod in secim:
            return kod
    return "30/6"
