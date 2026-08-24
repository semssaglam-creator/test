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

from . import turkce

# Alan turleri:
#   metin   : tek satir
#   uzun    : cok satirli serbest metin
#   tarih   : gg.aa.yyyy beklenir, dogrulanmaz (taslak icin serbest birakildi)
#   secim   : seceneklerden biri
#   sayi    : tam sayi
#   satirlar: sutunlari "kolonlar" ile bildirilen kucuk tablo. Arayuzde her
#             satir bir kutucuk dizisidir, (+) dugmesiyle satir eklenir.
#             Calismada yine tek metin olarak saklanir: her satir bir satir,
#             hucreler dikey cizgiyle ayrilir. Boylece eski calismalar da
#             oldugu gibi okunur.

IS_EMRI_KOLONLARI = [
    {"kod": "tarih", "etiket": "İş Emri Tarihi", "tur": "tarih"},
    {"kod": "sayi", "etiket": "İş Emri Sayısı", "tur": "metin"},
    {"kod": "donem", "etiket": "Dönemi", "tur": "metin"},
    {"kod": "konu", "etiket": "Konusu", "tur": "metin",
     "varsayilan": "Sahte Belge Kullanma"},
]

# Faaliyet konusu tek sutunlu bir satir alanidir: mukellefin birden cok
# faaliyet konusu varsa her biri ayri satira yazilir.
FAALIYET_KOLONLARI = [
    {"kod": "konu", "etiket": "Faaliyet konusu", "tur": "metin"},
]

BOLUMLER = [
    {
        "kod": "gorevlendirme",
        "baslik": "Görevlendirme ve İnceleme",
        "alanlar": [
            {"kod": "is_emirleri", "etiket": "Görevlendirme yazıları",
             "tur": "satirlar", "kolonlar": IS_EMRI_KOLONLARI,
             "ekle_etiketi": "+ Görevlendirme yazısı ekle",
             "ipucu": "Her görevlendirme yazısı için (+) düğmesiyle yeni satır "
                      "açın. Sıra numarası kendiliğinden verilir. Bir yazı "
                      "birden çok yılı kapsıyorsa dönemi “2022,2023” biçiminde "
                      "yazın; rapor yıl yıl düzenlendiğinden her yılın raporuna "
                      "yalnızca kendi görevlendirme yazıları girer."},
            {"kod": "inceleme_yeri", "etiket": "İncelemenin yapıldığı yer", "tur": "secim",
             "secenekler": ["Mükellefin iş yerinde", "Dairede", "Uzaktan"],
             "varsayilan": "Dairede"},
            {"kod": "inceleme_konusu", "etiket": "İnceleme konusu", "tur": "metin",
             "varsayilan": "Katma Değer Vergisi yönünden",
             "ipucu": "Belgede \"... yönünden inceleme\" biçiminde geçer."},
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
            {"kod": "mukellef_vkn", "etiket": "Vergi kimlik numarası", "tur": "metin",
             "ipucu": "Belgede “... vergi kimlik numaralı mükellefi” biçiminde "
                      "geçer. Boş bırakılırsa Çalışma Bilgilerine girilen numara "
                      "kullanılır."},
            {"kod": "mukellef_tckn", "etiket": "T.C. kimlik numarası", "tur": "metin",
             "ipucu": "Gerçek kişi mükelleflerde doldurun. İkisi de girilirse "
                      "belgede her ikisi de yazılır."},
            {"kod": "faaliyet_adresi", "etiket": "Faaliyet adresi", "tur": "uzun",
             "ipucu": "Belgede “... adresinde” biçiminde geçer. Boş bırakılırsa "
                      "Çalışma Bilgilerine girilen adres kullanılır."},
            {"kod": "faaliyet_konulari", "etiket": "Faaliyet konuları",
             "tur": "satirlar", "kolonlar": FAALIYET_KOLONLARI,
             "ekle_etiketi": "+ Faaliyet konusu ekle",
             "ipucu": "Örn: yapı malzemesi alım satımı. Mükellefin birden çok "
                      "faaliyet konusu varsa (+) düğmesiyle her birini ayrı "
                      "satıra yazın; belgede “... ve ... faaliyetleri ile "
                      "iştigal etmektedir” biçiminde sıralanır."},
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
            {"kod": "duzeltme_donemleri",
             "etiket": "Düzeltme beyannamesi verilen dönemler", "tur": "metin",
             "ipucu": "Yalnızca beyannameler yüklenmediğinde gerekir; yüklüyse "
                      "dönemler kendiliğinden bulunur. Biçim: 2023/Şubat, "
                      "2023/Mart. Raporda bu dönemler için ayrıntılı düzeltme "
                      "tablosu açılır, tutarlar kırmızı bırakılır."},
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
             "ipucu": "Adres olarak yazınız. Belgede iki yerde kullanılır: "
                      "“... adresinde düzenlenmiş” cümlesinde ve incelemenin "
                      "dairede/uzaktan yapıldığı hâlde “Müfettişliğimizin ... "
                      "çalışma adresinde” cümlesinde."},
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
            {"kod": "defter_bilgileri", "etiket": "İbraz edilen defterler", "tur": "uzun",
             "ipucu": "Her satıra bir defter; alanları dikey çizgiyle ayırın: "
                      "yıl | defterin türü | tasdik tarihi ve numarası | tasdik makamı. "
                      "Örn: 2023 | Yevmiye Defteri | 25.12.2022 - 55555 | Mersin 17. Noterliği"},
            {"kod": "vergi_beyan_ozeti",
             "etiket": "Gelir / Kurumlar Vergisi beyanname özeti", "tur": "uzun",
             "ipucu": "Her satıra bir kalem: yıl | açıklama | tutar. Örn: "
                      "2023 | Ticari Kazançlar | 13.019,63. İncelenen her yıl "
                      "için ayrı satırlar yazın; tutanakta yıl yıl ayrı tablo "
                      "olarak yer alır. Beyanname PDF'i yüklendiğinde yıl "
                      "kendiliğinden eklenir."},
            {"kod": "muhasebe_kaydi", "etiket": "Faturaların muhasebe kaydı", "tur": "uzun",
             "ipucu": "Boş bırakılırsa fatura tablosunun altına standart "
                      "paragraf yazılır (hesap numaraları kırmızı bırakılır; "
                      "hizmet işletmesinde 740, ticaret işletmesinde 153). "
                      "Buraya yazarsanız yazdığınız metin olduğu gibi girer."},
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
    "is_emirleri", "nezdinde_ad", "eleman_ad", "tutanak_tarihi", "tutanak_yeri",
    "faaliyet_konulari",
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
    ham = dict(ham or {})
    # "faaliyet_konusu" tek satirlik bir metindi; artik satir alani. Eski
    # calismalar acilirken o deger ilk satira tasinir ki belge bos kalmasin.
    # Mufettisligin calisma adresi ayri bir alandi; artik tutanagin
    # duzenlendigi yerden okunuyor. Eski kayitlarda o alan doluysa aktarilir.
    if not str(ham.get("tutanak_yeri") or "").strip():
        eski = str(ham.get("calisma_adresi") or "").strip()
        if eski:
            ham["tutanak_yeri"] = eski
    if not str(ham.get("faaliyet_konulari") or "").strip():
        eski = str(ham.get("faaliyet_konusu") or "").strip()
        if eski:
            ham["faaliyet_konulari"] = eski
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


def gorevlendirme_ifadesi(emirler):
    """Gorevlendirme yazilarini cumle icine girecek bicime getirir.

    Tek yazi varsa "28.05.2024 tarih ve X sayılı görevlendirme yazısı",
    birden coksa hepsi sayilir ve "yazıları" denir. Girilmemis hucreler ve
    hic satir olmamasi durumu kirmizi yer tutucu birakir: belgeyi okuyan
    kisi neyi elle dolduracagini gorsun.
    """
    if not emirler:
        return ("[görevlendirme yazısı tarihi] tarih ve "
                "[görevlendirme yazısı sayısı] sayılı görevlendirme yazısı")
    parcalar = ["%s tarih ve %s sayılı"
                % (e.get("tarih") or "[görevlendirme yazısı tarihi]",
                   e.get("sayi") or "[görevlendirme yazısı sayısı]")
                for e in emirler]
    # `turkce.liste` burada kullanilmaz: modul dongusu olusur ve bu liste
    # "ile" baglaciyla degil, viryulle siralanir.
    return "%s görevlendirme yazı%s" % (", ".join(parcalar),
                                        "sı" if len(parcalar) == 1 else "ları")


def faaliyet_konulari(kunye):
    """Mukellefin faaliyet konularini liste olarak verir."""
    return [s.split("|")[0].strip() for s in satirlar_al(kunye, "faaliyet_konulari")
            if s.split("|")[0].strip()]


def faaliyet_ifadesi(kunye):
    """Cumleye girecek faaliyet ifadesi.

    Tek konu varsa "“yapı malzemesi alım satımı” faaliyeti", birden coksa
    hepsi sayilir ve "faaliyetleri" denir. Hic girilmemisse kirmizi yer
    tutucu birakilir.
    """
    konular = faaliyet_konulari(kunye)
    if not konular:
        return "“[faaliyet konusu]” faaliyeti"
    return "%s faaliyet%s" % (turkce.liste(["“%s”" % k for k in konular]),
                              "i" if len(konular) == 1 else "leri")


def mukellef_kimligi(inceleme, kunye):
    """Belgede mukellefin anilisindaki kimlik numarasi ifadesi.

    Kunyedeki numaralar esastir; girilmemisse Calisma Bilgilerine yazilan
    numaraya dusulur. Gercek kisi mukellefte T.C. kimlik numarasi da
    girilmisse ikisi birlikte yazilir.
    """
    kunye = kunye or {}
    vkn = str(kunye.get("mukellef_vkn") or "").strip()
    tckn = str(kunye.get("mukellef_tckn") or "").strip()
    if not vkn and not tckn:
        vkn = str((inceleme or {}).get("vkn_tckn") or "").strip()
    parcalar = []
    if vkn:
        parcalar.append("%s vergi kimlik numaralı" % vkn)
    if tckn:
        parcalar.append("%s T.C. kimlik numaralı" % tckn)
    if not parcalar:
        return "[VKN] vergi kimlik numaralı"
    return " ve ".join(parcalar)


def calisma_adresi(kunye):
    """Mufettisligin calisma adresi.

    Ayri bir alan tutulmuyor: tutanagin duzenlendigi yer zaten bu adrestir
    (inceleme dairede ya da uzaktan yapildiginda tutanak da orada duzenlenir),
    ayni adresi iki kez yazdirmak gereksiz.
    """
    return adres((kunye or {}).get("tutanak_yeri"),
                 "[Müfettişliğin çalışma adresi]")


def faaliyet_adresi(kunye, inceleme=None):
    """Belgeye gececek faaliyet adresi; kunye bos ise calismadaki adres."""
    ham = str((kunye or {}).get("faaliyet_adresi") or "").strip()
    return adres(ham or (inceleme or {}).get("adres"))


def cizgili_satirlar(kunye, kod, alan_sayisi, tutucular=None):
    """Dikey cizgiyle ayrilmis cok satirli alani tabloya cevirir.

    Eksik alanlar bos birakilir; fazlasi son alana eklenmez, atilir. Sekme
    karakteri de ayirac sayilir (Excel'den yapistirma kolaylasir).

    `tutucular` verilirse bos kalan hucrelere o sutunun adi koseli parantez
    icinde yazilir; belge yazicisi bunlari kirmizi gosterdiginden taslakta
    doldurulacak yer goze carpar.
    """
    tablo = []
    for ham in satirlar_al(kunye, kod):
        parcalar = [p.strip() for p in ham.replace("\t", "|").split("|")]
        parcalar += [""] * (alan_sayisi - len(parcalar))
        parcalar = parcalar[:alan_sayisi]
        for i, ad in enumerate(tutucular or []):
            if i < len(parcalar) and not parcalar[i]:
                parcalar[i] = "[%s]" % ad
        tablo.append(parcalar)
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


def gecici_vergi_adi(kunye):
    """Kurumda "kurum geçici vergisi", gercek kiside "geçici vergi"."""
    return "kurum geçici vergisi" if kurum_mu(kunye) else "geçici vergi"


def kazanc_maddeleri(kunye):
    """Kazanc tespitine iliskin mevzuat anahtarlari.

    Kurumda 5520 sayili Kanun, gercek kiside 193 sayili Kanun esas alinir;
    sahte belgeyle belgelenen alimin maliyet/gider kabulu bu maddelere
    dayandirilir.
    """
    if kurum_mu(kunye):
        return ["kvk_6", "kvk_11"]
    return ["gvk_37", "gvk_40", "gvk_mk120"]


def soru_muhatabi(kunye, buyuk=True, ek=""):
    """Tutanakta alislara iliskin sorularin yoneltildigi kisi.

    Kurumda sorular tuzel kisiye degil, onun adina hareket eden yetkiliye
    yoneltilir ve tutanakta "Mükellef Kurum Yetkilisi" diye anilir; gercek
    kisi mukellefte muhatap mukellefin kendisidir. Iyelik ekiyle biten
    "Yetkilisi" sozcugu yonelme ekinden once kaynastirma "n"si aldigindan
    ekler burada verilir.
    """
    if kurum_mu(kunye):
        govde = "Mükellef Kurum Yetkilisi" if buyuk else "mükellef kurum yetkilisi"
        return govde + {"": "", "e": "ne", "in": "nin"}.get(ek, ek)
    govde = "Mükellef" if buyuk else "mükellef"
    return govde + {"": "", "e": "e", "in": "in"}.get(ek, ek)


def mukellef_adi(inceleme, kunye, yer_tutucu="[Mükellef unvanı]"):
    """Incelenen mukellefin adini yazim kurallariyla verir.

    Kurumda unvan kurali (her kelimenin ilk harfi buyuk), gercek kiside ad
    soyad kurali (ad ilk harf buyuk, soyad tumu buyuk) uygulanir. Belgeye
    girecek metin buradan gecer; kullanicinin nasil yazdigina bakilmaz, cunku
    sistem dokumlerinden gelen adlar cogunlukla bastan sona buyuk harftir.
    """
    ham = str((inceleme or {}).get("ad_unvan") or "").strip()
    if not ham:
        return yer_tutucu
    return turkce.unvan(ham) if kurum_mu(kunye) else turkce.kisi_adi(ham)


# Vergi dairesi adinin sonunda gecen kisaltmalar; "vdb" baskanligi gosterir.
_DAIRE_KISALTMALARI = {"vd": False, "vdm": False, "vdb": True}


def daire_adi(deger, yer_tutucu="[Vergi dairesi]"):
    """Vergi dairesi adini tam ve yazim kurallarina uygun bicimde verir.

    Belgelerde daire adi tam yazilir; kullanici ise ekrana kisa yazar.
    "liman" da "LIMAN VD" de "Liman Vergi Dairesi Müdürlüğü" olur. Tam yazilmis
    adlar ("Büyük Mükellefler Vergi Dairesi Başkanlığı") oldugu gibi korunur.
    """
    ham = str(deger or "").strip()
    if not ham:
        return yer_tutucu
    if ham.startswith("["):                    # yer tutucu
        return ham

    kelimeler = ham.split()
    baskanlik = False
    son = turkce.kucuk(kelimeler[-1]).replace(".", "")
    if son in _DAIRE_KISALTMALARI:
        baskanlik = _DAIRE_KISALTMALARI[son]
        kelimeler = kelimeler[:-1]

    govde = turkce.unvan(" ".join(kelimeler))
    if not govde:
        return yer_tutucu
    kucugu = turkce.kucuk(govde)
    if kucugu.endswith("müdürlüğü") or kucugu.endswith("başkanlığı"):
        return govde
    kuyruk = " Başkanlığı" if baskanlik else " Müdürlüğü"
    if kucugu.endswith("vergi dairesi"):
        return govde + kuyruk
    return govde + " Vergi Dairesi" + kuyruk


def vergi_dairesi(deger, yer_tutucu="[Vergi dairesi]", ek=""):
    """Belgeye gececek vergi dairesi adi; ek="in" ilgi hali eki ekler.

    Daire adi metinlerde hep "...nün ... mükellefi" kalibinda geciyor; eki
    burada vermek, cagiran her yerde ayri ayri kurulmasini onluyor.
    """
    ad = daire_adi(deger, yer_tutucu)
    return turkce.ilgi_kurum(ad) if ek == "in" else ad


def adres(deger, yer_tutucu="[Adres]"):
    """Adresi yazim kurallariyla verir; sistem dokumlerinden buyuk harf gelir."""
    return turkce.adres(str(deger or "").strip()) or yer_tutucu


def satici_unvani(satici, yer_tutucu="[unvan girilmedi]"):
    """Satici unvanini yazim kurallariyla verir."""
    return turkce.unvan(str((satici or {}).get("unvan") or "").strip()) or yer_tutucu


def ad(kunye, kod, yer_tutucu="ad soyad"):
    """Kunyedeki bir kisi adini yazim kurallariyla verir."""
    return turkce.kisi_adi(deger(kunye, kod, yer_tutucu))


def suc_duyurusu_hedefi(kunye, inceleme=None):
    """Suc duyurusunun kim hakkinda yapilacagini yazar.

    Kurumda fiil kanuni temsilciye isnat edilir ve onun T.C. kimlik numarasi
    yazilir. Gercek kisi mukellefte ayri bir temsilci yoktur; duyuru
    mukellefin kendisi hakkindadir ve kimlik numarasi kunyeden degil
    mukellef bilgisinden gelir.
    """
    inceleme = inceleme or {}
    if kurum_mu(kunye):
        return "%s T.C. kimlik numaralı kanuni temsilci %s" % (
            deger(kunye, "temsilci_tckn", "T.C. kimlik no"),
            ad(kunye, "kanuni_temsilci", "kanuni temsilci"))
    kimlik = (str(kunye.get("nezdinde_tckn") or "").strip()
              or str(inceleme.get("vkn_tckn") or "").strip()
              or "[T.C. kimlik no]")
    return "%s T.C. kimlik numaralı %s" % (
        kimlik, mukellef_adi(inceleme, kunye, "[Mükellef adı]"))


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
