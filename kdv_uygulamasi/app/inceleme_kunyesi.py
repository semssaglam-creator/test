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


def secim_mi(kunye, kod, beklenen):
    """Secim alaninin belirli bir degerde olup olmadigini soyler."""
    return str((kunye or {}).get(kod) or "").strip() == beklenen


def resen_madde_kodu(kunye):
    """Secilen re'sen takdir nedeninden madde numarasini ayiklar (orn '30/6')."""
    secim = str((kunye or {}).get("resen_madde") or "")
    for kod in ("30/4", "30/6", "30/7"):
        if kod in secim:
            return kod
    return "30/6"
