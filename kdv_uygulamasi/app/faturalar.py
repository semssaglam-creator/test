"""Sahte belge kullanmaya konu fatura listesi ve satici dokumu.

Portal dokumlerinden okunan ham satirlar burada incelemeye baglanir:

- **Yon**: her satirin VKN'leri mukellefin VKN'siyle karsilastirilir. Alici
  mukellefse fatura bir ALIStir (sahte belge kullanmaya konu olan budur);
  duzenleyen mukellefse SATIStir. VKN tasimayan elle hazirlanmis dokumlerde
  yon belirsiz kalir ve kullanici belirler.
- **Kayit donemi**: KDV indirimi belgenin deftere kaydedildigi donemde
  yapilir; tarhiyat da o doneme yazilir. Yevmiye tarihi varsa donem oradan,
  yoksa fatura tarihinden alinir. Kullanici satir bazinda degistirebilir.
- **Satici**: portal dokumu saticinin yalnizca VKN'sini tasir (dokum onun
  kendi portalindan alinmistir, unvan alani ALICInin unvanidir). Satici
  unvani ve hakkindaki tespit (VTR, ozel esaslar) kullanici tarafindan
  girilir.

Fatura KDV'lerinin donem donem toplami, eleştirideki "İndirilecek KDV'den
çıkarılacak" satirina yazilir. Boylece rapordaki fatura tablosu ile tarhiyat
ozeti ayni veriden gelir ve birbirini tutmak zorunda kalir.
"""
from datetime import date

from .satirlar import AYLAR

# Turkiye'de uygulanan KDV oranlari; disina cikan satir kullaniciya bildirilir
BILINEN_ORANLAR = (0.0, 1.0, 8.0, 10.0, 18.0, 20.0)
ORAN_TOLERANSI = 0.3          # yuzde puan

YON_ALIS = "alis"
YON_SATIS = "satis"
YON_BELIRSIZ = "belirsiz"

YON_ETIKETLERI = {
    YON_ALIS: "Alış (mükellef alıcı)",
    YON_SATIS: "Satış (mükellef düzenleyen)",
    YON_BELIRSIZ: "Belirsiz",
}

# Satici bazinda bilerek/bilmeden ayrimi. Sonucu bastan sona degistirdigi
# icin varsayilani yoktur; kullanici acikca secmelidir.
KULLANMA_SECENEKLERI = ["Belirlenmedi", "Bilmeden kullanma", "Bilerek kullanma"]

SATICI_ALANLARI = [
    {"kod": "unvan", "etiket": "Satıcı unvanı", "tur": "metin"},
    {"kod": "vergi_dairesi", "etiket": "Satıcının vergi dairesi", "tur": "metin",
     "ipucu": "Belgede “... Vergi Dairesi Müdürlüğünün VKN vergi kimlik "
              "numaralı mükellefi ...” biçiminde geçer."},
    {"kod": "kullanma", "etiket": "Kullanma durumu", "tur": "secim",
     "secenekler": KULLANMA_SECENEKLERI, "varsayilan": "Belirlenmedi"},
    {"kod": "vtr_no", "etiket": "VTR no", "tur": "metin"},
    {"kod": "vtr_tarihi", "etiket": "VTR tarihi", "tur": "tarih"},
    {"kod": "ozel_esaslar", "etiket": "Özel esaslara alınma tarihi", "tur": "tarih"},
    {"kod": "duzeltme_ile_cikarildi",
     "etiket": "Faturaları düzeltme beyannamesiyle çıkarılmış", "tur": "secim",
     "secenekler": ["Hayır", "Evet"], "varsayilan": "Hayır",
     "ipucu": "Mükellef bu satıcının faturalarını kendi düzeltme beyannamesiyle "
              "kayıtlarından çıkardıysa “Evet” seçin. O faturalar tarhiyata "
              "girmez; belgede neden dahil edilmediği açıklanır."},
    {"kod": "duzeltme_aciklama", "etiket": "Düzeltme beyannamesi açıklaması",
     "tur": "uzun",
     "ipucu": "Düzeltmenin tarihi ve hangi dönemleri kapsadığı. Belgeye olduğu "
              "gibi girer."},
    {"kod": "cevap", "etiket": "Mükellefin bu satıcıya ilişkin beyanı", "tur": "uzun",
     "ipucu": "Tutanakta bu satıcının fatura dökümünden hemen sonra gelen soru "
              "maddesinde tırnak içinde yazılır. Boş bırakılırsa künyedeki genel "
              "beyan kullanılır."},
    {"kod": "not", "etiket": "Satıcı hakkındaki tespit", "tur": "uzun"},
]


def tarih_goster(deger):
    """Tarihi GG.AA.YYYY bicimine getirir.

    Portal dokumleri tarihi "2023-01-03" olarak veriyor ve calismada da bu
    bicimde saklaniyor: siralamada ve karsilastirmada dogru olan budur. Ekranda
    ve belgede ise resmi yazim GG.AA.YYYY oldugundan cevrim yalnizca gosterimde
    yapilir. Cozulemeyen deger oldugu gibi birakilir; kullanicinin elle yazdigi
    bir metni bozmak, bicimlemekten kotudur.
    """
    metin = str(deger or "").strip()
    parcalar = metin.split("-")
    if len(parcalar) == 3 and len(parcalar[0]) == 4:
        yil, ay, gun = parcalar
        if yil.isdigit() and ay.isdigit() and gun.isdigit():
            return "%02d.%02d.%s" % (int(gun), int(ay), yil)
    return metin


def yevmiye_hucreleri(f):
    """Fatura tablosunun son iki hucresi: yevmiye tarihi ve numarasi.

    Portal dokumleri (e-Arsiv / e-Fatura) yevmiye bilgisi tasimaz; bu alanlar
    defter kaydindan elle girilir. Bos birakmak yerine kose parantezli tutucu
    yazilir: belge yazicisi bunlari kirmizi gosterdiginden, doldurulacak yer
    belgede goze carpar.
    """
    return (tarih_goster(f.get("yevmiye_tarih")) or "[yevmiye tarihi]",
            f.get("yevmiye_no") or "[yevmiye no]")


def mal_cinsi_hucresi(f):
    """Fatura tablosunun "Malin Cinsi" hucresi.

    Portal dokumlerinde mal cinsi cogu zaman bos gelir; yevmiye hucrelerinde
    oldugu gibi kose parantezli tutucu yazilir ki belgede kirmizi gorunsun ve
    taslak uzerinde doldurulacagi anlasilsin.
    """
    return (f.get("mal_cinsi") or "").strip() or "[malın cinsi]"


def duzeltilmis_mi(satici_vkn, saticilar):
    """Bu saticinin faturalari duzeltme beyannamesiyle cikarilmis mi."""
    bilgi = (saticilar or {}).get(satici_vkn or "") or {}
    return str(bilgi.get("duzeltme_ile_cikarildi") or "") == "Evet"


def sayilir(f, saticilar=None):
    """Fatura tarhiyata giriyor mu.

    Iki kosul birlikte aranir: kullanici satiri "dahil" birakmis olmali ve
    faturayi duzenleyen satici, faturalari duzeltme beyannamesiyle
    kayitlardan cikarilmis olarak isaretlenmemis olmali. Ikincisi onemlidir:
    mukellef o KDV'yi kendi duzeltmesiyle zaten indirimlerinden cikardiysa
    ayni tutari bir de rapor uzerinden tarh etmek mukerrer tarhiyat olur.
    """
    if not f.get("dahil"):
        return False
    return not duzeltilmis_mi(f.get("satici_vkn"), saticilar)


def _tarihi_coz(metin):
    """ISO tarihten (yil, ay) uretir; cozulemezse None."""
    parcalar = str(metin or "").split("-")
    if len(parcalar) < 2:
        return None
    try:
        return int(parcalar[0]), int(parcalar[1])
    except ValueError:
        return None


def _vkn(deger):
    return "".join(ch for ch in str(deger or "") if ch.isdigit())


def yonu_belirle(fatura, mukellef_vkn):
    """Faturanin alis mi satis mi oldugunu VKN karsilastirmasiyla bulur."""
    mukellef = _vkn(mukellef_vkn)
    if not mukellef:
        return YON_BELIRSIZ
    if _vkn(fatura.get("alici_vkn")) == mukellef:
        return YON_ALIS
    if _vkn(fatura.get("duzenleyen_vkn")) == mukellef:
        return YON_SATIS
    return YON_BELIRSIZ


def _ortak_vkn(ham_faturalar):
    """Butun satirlarda tekrar eden VKN'yi bulur.

    Portal dokumlerinde bir taraf hep aynidir: incelenen mukellef. Calismada
    mukellefin VKN'si girilmemisse yon tayini bundan yararlanir; boylece
    kullanici VKN yazmadan da alis/satis ayrimi dogru kurulur.
    """
    kumeler = []
    for f in ham_faturalar or []:
        kume = {v for v in (_vkn(f.get("alici_vkn")),
                            _vkn(f.get("duzenleyen_vkn"))) if v}
        if kume:
            kumeler.append(kume)
    if not kumeler:
        return ""
    ortak = set.intersection(*kumeler)
    return sorted(ortak)[0] if len(ortak) == 1 else ""


def _taraf_sutunu_var(ham_faturalar):
    """Dokumde hem alici hem duzenleyen VKN sutunu tasiniyor mu."""
    return (any(_vkn(f.get("alici_vkn")) for f in ham_faturalar or [])
            and any(_vkn(f.get("duzenleyen_vkn")) for f in ham_faturalar or []))


def normalize(ham_faturalar, mukellef_vkn=None):
    """Ham fatura satirlarini calismada saklanacak bicime getirir.

    Kullanicinin elle degistirdigi alanlar (yon, kayit donemi, dahil) varsa
    korunur; yalnizca bos olanlar veriden turetilir.

    Yon tayini: dokumde alici ve duzenleyen sutunlari varsa mukellefin VKN'si
    ile karsilastirilir. Mukellef VKN'si girilmemisse butun satirlarda tekrar
    eden VKN mukellef sayilir. Dokum taraf sutunu tasimiyorsa - tek tarafli
    alis listelerinde oldugu gibi - mukellef alici kabul edilir; aksi halde
    butun satirlar "belirsiz" kalip tarhiyat disinda kaliyordu.
    """
    ham_faturalar = list(ham_faturalar or [])
    mukellef_vkn = _vkn(mukellef_vkn) or _ortak_vkn(ham_faturalar)
    taraf_var = _taraf_sutunu_var(ham_faturalar)
    sonuc = []
    for ham in ham_faturalar:
        f = dict(ham)
        f.setdefault("iptal", False)

        if not f.get("yon"):
            f["yon"] = (yonu_belirle(f, mukellef_vkn) if taraf_var
                        else YON_ALIS)

        if not f.get("kayit_yil") or not f.get("kayit_ay"):
            # Once yevmiye tarihi: KDV indirimi kayit doneminde yapilir
            donem = _tarihi_coz(f.get("yevmiye_tarih")) or _tarihi_coz(f.get("tarih"))
            if donem:
                f["kayit_yil"], f["kayit_ay"] = donem
            else:
                f["kayit_yil"], f["kayit_ay"] = None, None

        f["tevsik_yok"] = bool(f.get("tevsik_yok"))

        if "dahil" not in f:
            # Iptal edilmis ve alis olmayan belgeler bastan disarida kalir;
            # kullanici isterse geri alir.
            f["dahil"] = bool(f["yon"] == YON_ALIS and not f["iptal"])

        f["satici_vkn"] = (_vkn(f.get("duzenleyen_vkn")) if f["yon"] != YON_SATIS
                           else _vkn(f.get("alici_vkn")))
        sonuc.append(f)
    return sonuc


def kdv_orani(fatura):
    """Faturanin ima ettigi KDV oranini yuzde olarak verir; matrah yoksa None."""
    matrah = float(fatura.get("matrah") or 0.0)
    if abs(matrah) < 0.005:
        return None
    return round(float(fatura.get("kdv") or 0.0) / matrah * 100.0, 2)


def satici_ozeti(faturalar, saticilar=None):
    """Satici bazinda fatura adedi ve tutar toplamlari.

    Listedeki BUTUN alis faturalari sayilir ve her satici - tek bir faturasi
    bile tarhiyata girmese de - ozette yer alir. Sahte belge duzenledigi
    tespit edilen mukellef ve faturalari tutanakta ve raporda gorunmelidir;
    hangilerinin tarhiyata girdigi ayri bir sorudur. Bu yuzden iki takim
    rakam tutulur:

      adet / matrah / kdv / toplam   -> "dahil" isaretli faturalar
      liste_*                        -> listedeki faturalarin tamami

    Tarhiyat, ceza ve oran hesaplari birincisinden; fatura tablolari ve
    Ba-Bs bildirim cumlesi ikincisinden beslenir.
    """
    saticilar = saticilar or {}
    gruplar = {}
    for f in faturalar or []:
        if f.get("yon") == YON_SATIS:
            continue
        vkn = f.get("satici_vkn") or ""
        grup = gruplar.setdefault(vkn, {
            "vkn": vkn, "adet": 0, "matrah": 0.0, "kdv": 0.0, "toplam": 0.0,
            "liste_adet": 0, "liste_matrah": 0.0, "liste_kdv": 0.0,
            "liste_toplam": 0.0, "donemler": set(),
        })
        grup["liste_adet"] += 1
        grup["liste_matrah"] += float(f.get("matrah") or 0.0)
        grup["liste_kdv"] += float(f.get("kdv") or 0.0)
        grup["liste_toplam"] += float(f.get("toplam") or 0.0)
        if f.get("kayit_yil") and f.get("kayit_ay"):
            grup["donemler"].add((f["kayit_yil"], f["kayit_ay"]))
        # Duzeltme ile cikarilmis saticinin faturalari da bu takima girer:
        # belgede tutari "duzeltme ile cikarildi" gerekcesiyle anilir.
        if not f.get("dahil"):
            continue
        grup["adet"] += 1
        grup["matrah"] += float(f.get("matrah") or 0.0)
        grup["kdv"] += float(f.get("kdv") or 0.0)
        grup["toplam"] += float(f.get("toplam") or 0.0)

    satirlar = []
    for vkn, grup in gruplar.items():
        bilgi = saticilar.get(vkn) or {}
        donemler = sorted(grup.pop("donemler"))
        grup.update({
            "unvan": bilgi.get("unvan") or "",
            "vergi_dairesi": bilgi.get("vergi_dairesi") or "",
            "kullanma": bilgi.get("kullanma") or "Belirlenmedi",
            "vtr_no": bilgi.get("vtr_no") or "",
            "vtr_tarihi": bilgi.get("vtr_tarihi") or "",
            "ozel_esaslar": bilgi.get("ozel_esaslar") or "",
            "not": bilgi.get("not") or "",
            "cevap": bilgi.get("cevap") or "",
            "duzeltme_ile_cikarildi": bilgi.get("duzeltme_ile_cikarildi") or "Hayır",
            "duzeltme_aciklama": bilgi.get("duzeltme_aciklama") or "",
            "matrah": round(grup["matrah"], 2),
            "kdv": round(grup["kdv"], 2),
            "toplam": round(grup["toplam"], 2),
            "liste_matrah": round(grup["liste_matrah"], 2),
            "liste_kdv": round(grup["liste_kdv"], 2),
            "liste_toplam": round(grup["liste_toplam"], 2),
            "tarhiyat_disi": grup["liste_adet"] - grup["adet"],
            "donem_sayisi": len(donemler),
            "ilk_donem": "%d/%s" % (donemler[0][0], AYLAR[donemler[0][1] - 1])
                         if donemler else "",
            "son_donem": "%d/%s" % (donemler[-1][0], AYLAR[donemler[-1][1] - 1])
                         if donemler else "",
        })
        satirlar.append(grup)
    satirlar.sort(key=lambda s: (-s["liste_kdv"], s["vkn"]))
    return satirlar


def donem_ozeti(faturalar, saticilar=None):
    """Tarhiyata giren alis faturalarinin donem donem toplami.

    Doner: {yil: {ay(1-12): {"adet", "matrah", "kdv"}}}
    """
    ozet = {}
    for f in faturalar or []:
        if not sayilir(f, saticilar):
            continue
        yil, ay = f.get("kayit_yil"), f.get("kayit_ay")
        if not yil or not ay or not (1 <= int(ay) <= 12):
            continue
        hucre = ozet.setdefault(int(yil), {}).setdefault(int(ay), {
            "adet": 0, "matrah": 0.0, "kdv": 0.0})
        hucre["adet"] += 1
        hucre["matrah"] += float(f.get("matrah") or 0.0)
        hucre["kdv"] += float(f.get("kdv") or 0.0)
    for aylar in ozet.values():
        for hucre in aylar.values():
            hucre["matrah"] = round(hucre["matrah"], 2)
            hucre["kdv"] = round(hucre["kdv"], 2)
    return ozet


def indirim_dizileri(faturalar, saticilar=None):
    """Her yil icin 12 elemanli "indirilecek KDV'den cikarilacak" dizisi."""
    ozet = donem_ozeti(faturalar, saticilar)
    diziler = {}
    for yil, aylar in ozet.items():
        dizi = [0.0] * 12
        for ay, hucre in aylar.items():
            dizi[ay - 1] = hucre["kdv"]
        diziler[yil] = dizi
    return diziler


def uygulama_farki(faturalar, yillar, saticilar=None):
    """Fatura toplami ile calismadaki elestiri girdisini karsilastirir.

    Fatura listesi tarhiyata otomatik yazilabildigi icin, elle girilmis bir
    tutarin sessizce ezilmesi ya da iki kaynagin birbirinden ayrilmasi
    tehlikelidir. Bu yuzden fark satir satir bildirilir.
    """
    diziler = indirim_dizileri(faturalar, saticilar)
    mevcut = {}
    for yil_kaydi in yillar or []:
        try:
            yil = int(yil_kaydi.get("yil"))
        except (TypeError, ValueError):
            continue
        elestiri = yil_kaydi.get("elestiri") or {}
        dizi = list(elestiri.get("indirim_cikar") or [])
        mevcut[yil] = [float(d or 0.0) for d in (dizi + [0.0] * 12)[:12]]

    farklar = []
    for yil in sorted(set(diziler) | set(mevcut)):
        fatura_dizi = diziler.get(yil) or [0.0] * 12
        mevcut_dizi = mevcut.get(yil) or [0.0] * 12
        for ay in range(12):
            fark = round(fatura_dizi[ay] - mevcut_dizi[ay], 2)
            if abs(fark) > 0.005:
                farklar.append({
                    "yil": yil, "ay": ay + 1, "ay_adi": AYLAR[ay],
                    "fatura": round(fatura_dizi[ay], 2),
                    "mevcut": round(mevcut_dizi[ay], 2),
                    "fark": fark,
                    "yil_var": yil in mevcut,
                })
    return farklar


def bulgular(faturalar, yillar=None, saticilar=None):
    """Fatura listesindeki dikkat gerektiren noktalari bildirir.

    Bunlar birer hata degil, kullaniciya "buraya bak" demektir; hicbiri
    kendiliginden veriyi degistirmez.
    """
    saticilar = saticilar or {}
    bilinen_yillar = {int(y.get("yil")) for y in (yillar or [])
                      if str(y.get("yil") or "").isdigit()}
    sonuc = []
    gorulen_no = {}

    for f in faturalar or []:
        etiket = f.get("fatura_no") or f.get("uuid") or "(numarasız)"

        if f.get("iptal") and f.get("dahil"):
            sonuc.append({"tur": "iptal", "fatura": etiket,
                          "mesaj": "%s iptal/itiraz listesinde görünüyor ama "
                                   "tarhiyata dahil edilmiş." % etiket})

        yevmiye = _tarihi_coz(f.get("yevmiye_tarih"))
        fatura_tarihi = f.get("tarih")
        if yevmiye and fatura_tarihi and f.get("yevmiye_tarih") < fatura_tarihi:
            sonuc.append({"tur": "yevmiye_tarihi", "fatura": etiket,
                          "mesaj": "%s: yevmiye tarihi (%s) fatura tarihinden "
                                   "(%s) önce." % (etiket, f["yevmiye_tarih"],
                                                   fatura_tarihi)})

        oran = kdv_orani(f)
        if oran is not None and sayilir(f, saticilar):
            if not any(abs(oran - o) <= ORAN_TOLERANSI for o in BILINEN_ORANLAR):
                sonuc.append({"tur": "kdv_orani", "fatura": etiket,
                              "mesaj": "%s: KDV oranı %%%s çıkıyor; bilinen "
                                       "oranlardan biri değil." % (etiket, oran)})

        if sayilir(f, saticilar) and not (f.get("kayit_yil") and f.get("kayit_ay")):
            sonuc.append({"tur": "donem_yok", "fatura": etiket,
                          "mesaj": "%s: kayıt dönemi belirlenemedi; tarhiyata "
                                   "yazılamaz." % etiket})
        elif sayilir(f, saticilar) and bilinen_yillar and f.get("kayit_yil") not in bilinen_yillar:
            sonuc.append({"tur": "yil_disi", "fatura": etiket,
                          "mesaj": "%s: kayıt dönemi %s, ancak bu yıl için beyan "
                                   "verisi yüklenmemiş." % (etiket, f["kayit_yil"])})

        if f.get("fatura_no"):
            anahtar = (f["fatura_no"].upper(), f.get("satici_vkn") or "")
            gorulen_no[anahtar] = gorulen_no.get(anahtar, 0) + 1

    for (no, _vkn_), adet in gorulen_no.items():
        if adet > 1:
            sonuc.append({"tur": "yinelenen", "fatura": no,
                          "mesaj": "%s numaralı fatura listede %d kez var." % (no, adet)})

    for satici in satici_ozeti(faturalar, saticilar):
        if satici["kullanma"] == "Belirlenmedi":
            sonuc.append({
                "tur": "kullanma_secilmedi", "fatura": satici["vkn"],
                "mesaj": "%s VKN'li satıcı için bilerek/bilmeden kullanma "
                         "belirlenmemiş. Bu seçim vergi ziyaı cezasının 1 kat mı "
                         "3 kat mı uygulanacağını belirler."
                         % (satici["vkn"] or "(VKN yok)")})
        if not satici["unvan"]:
            sonuc.append({"tur": "unvan_yok", "fatura": satici["vkn"],
                          "mesaj": "%s VKN'li satıcının unvanı girilmemiş; "
                                   "belgelerde boş kalır." % (satici["vkn"] or "(VKN yok)")})
    return sonuc


def _kategori(satici_vkn, saticilar):
    secim = (saticilar.get(satici_vkn) or {}).get("kullanma") or "Belirlenmedi"
    if secim == "Bilerek kullanma":
        return "bilerek"
    if secim == "Bilmeden kullanma":
        return "bilmeden"
    return "belirsiz"


# Vergi ziyai cezasi katsayilari (VUK 344): 359'daki fiillerle ziyaa sebebiyet
# verilirse uc kat, diger hallerde bir kat.
CEZA_KATI = {"bilerek": 3, "bilmeden": 1, "belirsiz": 1}


def ceza_dagilimi(faturalar, saticilar, sonuc):
    """Donem donem tarh edilen vergiyi satici kategorilerine paylastirir.

    Neden paylastirma gerekiyor: bir donemde birden cok saticinin faturasi
    olabilir ve bunlarin bir kismi bilerek, bir kismi bilmeden kullanma
    sayilabilir; ceza kati ikisinde farklidir. Ayrica reddedilen KDV ile
    tarh edilen vergi her zaman esit degildir - devir zinciri reddin bir
    kismini sogurabilir, ya da tarhiyatin bir kismi matrah ilavesi gibi baska
    tespitlerden gelebilir.

    Bu yuzden once tarh edilen tutarin sahte belgeye atfedilebilecek kismi
    ayrilir (reddedilen KDV'yi asamaz), sonra bu kisim kategorilerin reddedilen
    KDV'leri oraninda bolunur. Kalan tutar "diger tespitler" olarak ayri
    gosterilir; cezasi bu raporun konusu degildir.
    """
    saticilar = saticilar or {}
    # Donem -> kategori -> reddedilen KDV
    red = {}
    for f in faturalar or []:
        if not sayilir(f, saticilar):
            continue
        yil, ay = f.get("kayit_yil"), f.get("kayit_ay")
        if not yil or not ay:
            continue
        hucre = red.setdefault((int(yil), int(ay)),
                               {"bilerek": 0.0, "bilmeden": 0.0, "belirsiz": 0.0})
        hucre[_kategori(f.get("satici_vkn") or "", saticilar)] += float(f.get("kdv") or 0.0)

    satirlar = []
    for d in (sonuc.get("donemler") or []):
        anahtar = (d["yil"], d["ay"])
        tarh = float(d["tarhiyat"].get("resen_toplam") or 0.0)
        kategoriler = red.get(anahtar) or {}
        red_toplam = sum(kategoriler.values())
        if tarh <= 0.005 and red_toplam <= 0.005:
            continue

        sahte_pay = min(tarh, red_toplam)
        paylar, ceza = {}, {}
        for kategori in ("bilerek", "bilmeden", "belirsiz"):
            tutar = kategoriler.get(kategori, 0.0)
            pay = (sahte_pay * tutar / red_toplam) if red_toplam > 0.005 else 0.0
            paylar[kategori] = round(pay, 2)
            ceza[kategori] = round(pay * CEZA_KATI[kategori], 2)

        satirlar.append({
            "yil": d["yil"], "ay": d["ay"], "ay_adi": d["ay_adi"],
            "red_bilerek": round(kategoriler.get("bilerek", 0.0), 2),
            "red_bilmeden": round(kategoriler.get("bilmeden", 0.0), 2),
            "red_belirsiz": round(kategoriler.get("belirsiz", 0.0), 2),
            "red_toplam": round(red_toplam, 2),
            "tarh": round(tarh, 2),
            "tarh_sahte": round(sahte_pay, 2),
            "tarh_diger": round(tarh - sahte_pay, 2),
            "pay_bilerek": paylar["bilerek"],
            "pay_bilmeden": paylar["bilmeden"],
            "pay_belirsiz": paylar["belirsiz"],
            "ceza_bilerek": ceza["bilerek"],
            "ceza_bilmeden": ceza["bilmeden"],
            "ceza_belirsiz": ceza["belirsiz"],
            "ceza_toplam": round(sum(ceza.values()), 2),
        })

    alanlar = [k for k in (satirlar[0] if satirlar else {})
               if k not in ("yil", "ay", "ay_adi")]
    toplam = {a: round(sum(s[a] for s in satirlar), 2) for a in alanlar}
    return {"satirlar": satirlar, "toplam": toplam}


# --------------------------------------------------------- oran ve ozel usulsuzluk
def sahte_belge_orani(faturalar, sonuc, saticilar=None):
    """Sahte belgelerin mukellefin toplam alislari icindeki payini hesaplar.

    Bu oran, "bilerek kullanma" kanaatinin en cok dayandirildigi olcuttur:
    alislarinin buyuk bolumunu sahte belgeyle belgelendiren bir mukellefin
    durumu bilmediginin kabulu guclesir. Rapor bu orani yazar; kanaati yine
    inceleme elemani kurar.

    Olcut KDV uzerinden alinir: reddedilen KDV / beyan edilen bu donem
    indirilecek KDV toplami. Matrah yerine KDV secilmesinin nedeni, fatura
    dokumunde her zaman KDV bulunmasi ama alis matrahinin beyannamede ayrica
    yer almamasidir.
    """
    dahil = [f for f in (faturalar or []) if sayilir(f, saticilar)]
    sahte_kdv = sum(float(f.get("kdv") or 0.0) for f in dahil)
    yillar = {f.get("kayit_yil") for f in dahil if f.get("kayit_yil")}
    toplam_indirim = sum(
        d["beyan"].get("bu_donem_indirim_toplam", 0.0)
        for d in (sonuc.get("donemler") or []) if d["yil"] in yillar)
    oran = (sahte_kdv / toplam_indirim * 100.0) if toplam_indirim > 0.005 else None
    return {
        "sahte_kdv": round(sahte_kdv, 2),
        "toplam_indirim_kdv": round(toplam_indirim, 2),
        "oran": round(oran, 2) if oran is not None else None,
        "yillar": sorted(y for y in yillar if y),
    }


# VUK muk. 355 / 459 sira no'lu Genel Teblig: tevsik zorunlulugu haddi.
# 2016 sonuna kadar 8.000 TL, 2017'den itibaren 7.000 TL.
def tevsik_haddi(yil):
    try:
        yil = int(yil)
    except (TypeError, ValueError):
        return 7000.0
    return 8000.0 if yil <= 2016 else 7000.0


def ozel_usulsuzluk(faturalar, alt_had, ust_sinir, saticilar=None):
    """Odemeleri tevsik etmeme fiilinden dogan ozel usulsuzluk cezasi.

    Yalnizca kullanicinin "tevsik edilmemis" diye isaretledigi faturalar
    hesaba girer; uygulama bunu kendiliginden varsaymaz. Ceza, islem
    tutarinin (KDV dahil) yuzde besidir ve yila ait alt haddin altina
    inemez. Bir hesap doneminde kesilebilecek toplam ceza da ust sinirla
    kisitlidir (VUK muk. 355).

    alt_had / ust_sinir yil yil degistigi icin kunyeden alinir; uygulama
    bunlari tahmin etmez.
    """
    try:
        alt_had = float(alt_had or 0.0)
    except (TypeError, ValueError):
        alt_had = 0.0
    try:
        ust_sinir = float(ust_sinir or 0.0)
    except (TypeError, ValueError):
        ust_sinir = 0.0

    satirlar = []
    for f in faturalar or []:
        if not f.get("tevsik_yok") or not sayilir(f, saticilar):
            continue
        matrah = float(f.get("matrah") or 0.0)
        kdv = float(f.get("kdv") or 0.0)
        toplam = float(f.get("toplam") or 0.0) or (matrah + kdv)
        if toplam < tevsik_haddi(f.get("kayit_yil")):
            continue                      # had altinda kalan islem ceza dogurmaz
        yuzde_bes = round(toplam * 0.05, 2)
        satirlar.append({
            "fatura_no": f.get("fatura_no") or "",
            "tarih": f.get("tarih") or "",
            "satici_vkn": f.get("satici_vkn") or "",
            "kayit_yil": f.get("kayit_yil"),
            "matrah": round(matrah, 2),
            "kdv": round(kdv, 2),
            "toplam": round(toplam, 2),
            "yuzde_bes": yuzde_bes,
            "alt_had": round(alt_had, 2),
            "ceza": round(max(yuzde_bes, alt_had), 2),
        })
    satirlar.sort(key=lambda s: (s["kayit_yil"] or 0, s["tarih"], s["fatura_no"]))

    ham_toplam = round(sum(s["ceza"] for s in satirlar), 2)
    kesilecek = min(ham_toplam, ust_sinir) if ust_sinir > 0 else ham_toplam
    return {
        "satirlar": satirlar,
        "islem_sayisi": len(satirlar),
        "islem_tutari": round(sum(s["toplam"] for s in satirlar), 2),
        "ham_toplam": ham_toplam,
        "ust_sinir": round(ust_sinir, 2),
        "ust_sinir_uygulandi": ust_sinir > 0 and ham_toplam > ust_sinir,
        "kesilecek": round(kesilecek, 2),
    }


def toplamlar(faturalar, saticilar=None):
    """Tarhiyata giren alis faturalarinin genel toplami."""
    dahil = [f for f in (faturalar or []) if sayilir(f, saticilar)]
    return {
        "adet": len(dahil),
        "matrah": round(sum(float(f.get("matrah") or 0.0) for f in dahil), 2),
        "kdv": round(sum(float(f.get("kdv") or 0.0) for f in dahil), 2),
        "toplam": round(sum(float(f.get("toplam") or 0.0) for f in dahil), 2),
        "toplam_satir": len(faturalar or []),
    }


# --------------------------------------------------- beyana oturtma (altkume)
# Bir donemde listedeki faturalarin toplami, beyan edilen yurtici alimlari
# asabiliyor: mukellef bazi alislarini beyana hic dahil etmemis olabilir.
# O zaman "hangi faturalar indirim konusu yapilmis" sorusu, toplama oturan
# fatura birlesimini aramaya donusuyor. Kalem sayisi bu sinirin altindaysa
# butun birlesimler taranir; ustundeyse buyukten kucuge yerlestirme yapilir.
KESIN_COZUM_SINIRI = 18
ALTERNATIF_SAYIM_TAVANI = 99


def altkume_secimi(tutarlar, sinir):
    """Toplami siniri asmayan en yuksek tutarli fatura birlesimini secer.

    Doner: {"toplam", "secim" (indis listesi), "alternatif", "yaklasik"}
    `alternatif`, ayni toplama ulasan baska birlesim sayisidir; birden
    buyukse hangi faturalarin beyana girdigi tek basina aritmetikle
    belirlenemiyor demektir.
    """
    kurus = [int(round(float(t or 0.0) * 100)) for t in tutarlar]
    hedef = int(round(float(sinir or 0.0) * 100))
    if hedef <= 0 or not kurus:
        return {"toplam": 0.0, "secim": [], "alternatif": 0, "yaklasik": False}

    if len(kurus) > KESIN_COZUM_SINIRI:
        sirali = sorted(range(len(kurus)), key=lambda i: -kurus[i])
        secim, toplam = [], 0
        for i in sirali:
            if toplam + kurus[i] <= hedef:
                secim.append(i)
                toplam += kurus[i]
        return {"toplam": toplam / 100.0, "secim": sorted(secim),
                "alternatif": 0, "yaklasik": True}

    ornek = {0: ()}                 # toplam -> ornek indis demeti
    sayac = {0: 1}                  # toplam -> kac farkli birlesim
    for i, tutar in enumerate(kurus):
        for toplam in sorted(ornek, reverse=True):
            yeni = toplam + tutar
            if yeni > hedef:
                continue
            if yeni not in ornek:
                ornek[yeni] = ornek[toplam] + (i,)
            sayac[yeni] = min(sayac.get(yeni, 0) + sayac[toplam],
                              ALTERNATIF_SAYIM_TAVANI)
    en_iyi = max(ornek)
    return {"toplam": en_iyi / 100.0, "secim": list(ornek[en_iyi]),
            "alternatif": max(sayac[en_iyi] - 1, 0), "yaklasik": False}


def _satici_gruplari(dahil):
    """Donemdeki faturalari satici satici gruplar.

    Mukellef bir alisi beyana dahil etmediginde bunu genellikle tek tek
    faturalarla degil, o saticiyla olan alislarinin tamamiyla yapar. Bu yuzden
    aday birlesim once satici butunlugu korunarak aranir.
    """
    gruplar = {}
    for sira, f in dahil:
        vkn = f.get("satici_vkn") or ""
        grup = gruplar.setdefault(vkn, {"vkn": vkn, "siralar": [], "kdv": 0.0})
        grup["siralar"].append(sira)
        grup["kdv"] = round(grup["kdv"] + float(f.get("kdv") or 0.0), 2)
    return [gruplar[v] for v in sorted(gruplar)]


def dikkat_dokumu(faturalar, sinirlar, saticilar=None):
    """Beyan edilen indirim ile fatura listesini donem donem karsilastirir.

    sinirlar: {(yil, ay): indirimden cikarilabilecek en yuksek tutar}
        (beyandaki yurtici alimlara iliskin KDV; yoksa bu doneme ait
        indirilecek KDV)

    Yalnizca listedeki faturalarin KDV'si bu tutari asan donemler doner.
    Boyle bir donemde faturalarin tamami indirim konusu yapilmis olamaz;
    hangilerinin yapildigi ancak defter kaydindan kesin olarak belirlenir.
    Uygulama iki aday uretir: satici butunlugu korunarak en yuksek birlesim
    (varsayilan; mukellefin bir saticiyla olan alislarinin tamamini beyan disi
    birakmasi tipik durumdur) ve fatura bazinda en yuksek birlesim. Ikisi
    farkliysa ikisi de gosterilir - secim aritmetikle degil, defterle yapilir.
    """
    # Satirlar, calismadaki sirasiyla birlikte tutulur: ekran bu sira numarasi
    # uzerinden faturayi bulup "dahil" isaretini kaldirabiliyor.
    donemler = {}
    for sira, f in enumerate(faturalar or []):
        yil, ay = f.get("kayit_yil"), f.get("kayit_ay")
        if not yil or not ay:
            continue
        anahtar = (int(yil), int(ay))
        hucre = donemler.setdefault(anahtar, {"tumu": [], "dahil": []})
        hucre["tumu"].append(f)
        if sayilir(f, saticilar):
            hucre["dahil"].append((sira, f))

    dokum = []
    for (yil, ay) in sorted(donemler):
        hucre = donemler[(yil, ay)]
        sinir = float(sinirlar.get((yil, ay)) or 0.0)
        dahil_kdv = round(sum(float(f.get("kdv") or 0.0)
                              for _s, f in hucre["dahil"]), 2)
        if dahil_kdv - sinir <= 0.005:
            continue

        gruplar = _satici_gruplari(hucre["dahil"])
        grup_secim = altkume_secimi([g["kdv"] for g in gruplar], sinir)
        secili_siralar = set()
        secili_saticilar = []
        for i in grup_secim["secim"]:
            secili_siralar.update(gruplar[i]["siralar"])
            secili_saticilar.append(gruplar[i]["vkn"])
        fatura_secim = altkume_secimi([f.get("kdv") for _s, f in hucre["dahil"]],
                                      sinir)

        dokum.append({
            "yil": yil,
            "ay": ay,
            "ay_adi": AYLAR[ay - 1],
            "donem": "%d/%s" % (yil, AYLAR[ay - 1]),
            "sinir": round(sinir, 2),
            "liste_kdv": round(sum(float(f.get("kdv") or 0.0)
                                   for f in hucre["tumu"]), 2),
            "dahil_kdv": dahil_kdv,
            "asim": round(dahil_kdv - sinir, 2),
            "satici_sayisi": len(gruplar),
            # Uygulanan aday: satici butunlugu korunmus birlesim
            "secim_toplami": grup_secim["toplam"],
            "alternatif": grup_secim["alternatif"],
            "yaklasik": grup_secim["yaklasik"],
            "secili_saticilar": secili_saticilar,
            # Bilgi olarak: fatura bazinda daha yuksek bir toplam mumkun mu
            "fatura_secim_toplami": fatura_secim["toplam"],
            "fatura_alternatif": fatura_secim["alternatif"],
            "faturalar": [{
                "sira": sira,
                "fatura_no": f.get("fatura_no") or "",
                "tarih": tarih_goster(f.get("tarih")),
                "satici_vkn": f.get("satici_vkn") or "",
                "kdv": round(float(f.get("kdv") or 0.0), 2),
                "secili": sira in secili_siralar,
            } for sira, f in hucre["dahil"]],
        })
    return dokum
