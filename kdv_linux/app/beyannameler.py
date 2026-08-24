"""Beyanname surumleri: kanuni suresinde verilen beyan ve duzeltmeleri.

Bir donem icin birden cok beyanname verilebilir: kanuni suresinde verilen ilk
beyanname ve ardindan bir ya da daha cok duzeltme beyannamesi. Duzeltme
beyannamesi onceki beyani tamamen yeniler (degisen satirlari degil, beyanin
butununu yeniden beyan eder); bu yuzden her surum kendi basina eksiksiz bir
beyandir.

Bu modul:
  - beyannameleri doneme gore gruplar ve onay zamanina gore siralar,
  - her donem icin ilk beyani, duzeltmeleri ve son hali ayirir,
  - ilk beyan ile son hal arasindaki satir bazinda farki cikarir,
  - secilen kombinasyonu (hepsi ilk beyan / hepsi son hal / donem donem secim)
    incelemede kullanilacak beyan verisine cevirir.
"""
from .satirlar import (AYLAR, BEYAN_SATIRLARI, ETIKETLER, OZET_HEDEF_SECENEKLERI,
                       OZET_KOLONLARI, VERI_KODLARI)

# Genel Bakis tablosu, Sonuc ve Fark sekmesindeki ozet tabloyla ayni kolonlari
# kullanir; iki ekran yan yana okunabilsin diye. Asagidaki esleme, ozet
# kolonunun beyannamedeki hangi satirdan geldigini soyler.
OZET_ESLEMESI = {
    "matrah": "matrah_toplami",
    "toplam_kdv": "toplam_kdv",
    "onceki_devir": "onceki_donem_devreden",
    "bu_donem_indirim_toplam": "bu_donem_indirilecek",
    "indirimler": "indirimler_toplami",
    "odenecek": "odenmesi_gereken_kdv",
    "sonraki_devir": "sonraki_donem_devreden",
    "iade": "iade_edilmesi_gereken_kdv",
}

# Karsilastirma tablosunda one cikarilan satirlar (sonuc hesaplari ve ana
# buyuklukler); digerleri "tum satirlar" secildiginde gorunur.
ONEMLI_KODLAR = [
    "matrah_toplami", "hesaplanan_kdv", "ilave_edilecek_kdv", "toplam_kdv",
    "onceki_donem_devreden", "bu_donem_indirilecek", "diger_indirimler_toplami",
    "indirimler_toplami", "odenmesi_gereken_kdv", "sonraki_donem_devreden",
    "iade_edilmesi_gereken_kdv", "tecil_edilecek_kdv",
]


def donem_anahtari(yil, ay):
    return "%04d-%02d" % (int(yil), int(ay))


def _surum_etiketi(tur, sira):
    if sira == 0:
        return "Kanuni süresinde" if tur == "kanuni" else "İlk beyan"
    return "%d. düzeltme" % sira


def _ayni_mi(a, b):
    """Iki kaydin ayni beyanname olup olmadigi (mukerrer yukleme denetimi).

    Olcut, ayni BEYANNAMENIN iki kez yuklenmis olmasidir; rakamlarin ayni
    olmasi degil. Bir duzeltme beyannamesi onceki beyanla birebir ayni
    tutarlari tasiyor olabilir (ornegin yalnizca bir bilgi alani duzeltilmis
    olabilir); bu yine de ayri bir beyannamedir ve listede ayri satir olarak
    gorunmelidir. Once rakamlara bakan eski olcut boyle beyannameleri
    sessizce eliyordu.
    """
    if a.get("onay_ts") and a.get("onay_ts") == b.get("onay_ts"):
        return True
    if a.get("kaynak") and a.get("kaynak") == b.get("kaynak"):
        return True
    # Ikisinde de onay damgasi ve kaynak adi yoksa elde ayirt edici bir sey
    # kalmaz; o zaman rakamlara bakilir.
    if not (a.get("onay_ts") or b.get("onay_ts")
            or a.get("kaynak") or b.get("kaynak")):
        return a.get("degerler") == b.get("degerler")
    return False


def duzenle(beyannameler):
    """Beyannameleri donemlere ayirir, siralar ve karsilastirir.

    Doner:
      {
        "donemler": [ {yil, ay, ay_adi, etiket, surumler[], ilk, son,
                       degisen[], surum_sayisi} ],
        "uyarilar": [...],
        "mukellefler": [ {vkn, unvan} ],   # birden cok cikarsa uyari verilir
      }
    """
    gruplar = {}
    uyarilar = []
    for b in beyannameler or []:
        try:
            yil, ay = int(b["yil"]), int(b["ay"])
        except (KeyError, TypeError, ValueError):
            uyarilar.append("Dönemi okunamayan bir beyanname atlandı: %s"
                            % (b.get("kaynak") or "?"))
            continue
        if not 1 <= ay <= 12:
            uyarilar.append("%s: ay değeri geçersiz (%s)." % (b.get("kaynak"), ay))
            continue
        gruplar.setdefault(donem_anahtari(yil, ay), []).append(b)

    donemler = []
    for anahtar in sorted(gruplar):
        liste = gruplar[anahtar]
        # Onay zamanina gore sirala; damgasi olmayanlar sona
        liste = sorted(liste, key=lambda b: (b.get("onay_ts") or "9999", b.get("kaynak") or ""))

        benzersiz = []
        for b in liste:
            ikiz = next((v for v in benzersiz if _ayni_mi(v, b)), None)
            if ikiz:
                uyarilar.append(
                    "%s ile %s aynı beyanname (aynı onay zamanı/dosya); ikincisi "
                    "kullanılmadı." % (ikiz.get("kaynak") or "?",
                                       b.get("kaynak") or "?"))
                continue
            benzersiz.append(b)

        yil, ay = int(benzersiz[0]["yil"]), int(benzersiz[0]["ay"])
        surumler = []
        for sira, b in enumerate(benzersiz):
            tur = b.get("tur") or ("kanuni" if sira == 0 else "duzeltme")
            surumler.append({
                "sira": sira,
                "tur": tur,
                "etiket": _surum_etiketi(tur, sira),
                "onay_zamani": b.get("onay_zamani") or "",
                "onay_ts": b.get("onay_ts") or "",
                "duzeltme_nedeni": b.get("duzeltme_nedeni") or "",
                "kaynak": b.get("kaynak") or "",
                "vkn": b.get("vkn") or "",
                "unvan": b.get("unvan") or "",
                "vergi_dairesi": b.get("vergi_dairesi") or "",
                "uyarilar": b.get("uyarilar") or [],
                "degerler": b.get("degerler") or {},
            })

        if surumler[0]["tur"] != "kanuni":
            uyarilar.append(
                "%s dönemi için kanuni süresinde verilen beyanname yüklenmemiş; "
                "en erken tarihli beyanname (%s) ilk beyan sayıldı."
                % (_donem_etiketi(yil, ay), surumler[0]["kaynak"]))
        for s in surumler[1:]:
            if s["tur"] == "kanuni":
                uyarilar.append(
                    "%s dönemi için birden çok kanuni süre beyannamesi var; %s "
                    "düzeltme gibi sıralandı."
                    % (_donem_etiketi(yil, ay), s["kaynak"]))

        donemler.append({
            "yil": yil,
            "ay": ay,
            "ay_adi": AYLAR[ay - 1],
            "etiket": _donem_etiketi(yil, ay),
            "anahtar": anahtar,
            "surumler": surumler,
            "surum_sayisi": len(surumler),
            "ilk": surumler[0],
            "son": surumler[-1],
            "degisen": _degisenler(surumler[0], surumler[-1]),
            "adim_adim": _adim_adim(surumler),
        })

    mukellefler = []
    for d in donemler:
        for s in d["surumler"]:
            kimlik = (s["vkn"], s["unvan"])
            if s["vkn"] and kimlik not in mukellefler:
                mukellefler.append(kimlik)
    vknler = {v for v, _u in mukellefler}
    if len(vknler) > 1:
        uyarilar.append("Yüklenen beyannameler farklı vergi kimlik numaralarına ait: %s"
                        % ", ".join(sorted(vknler)))

    return {
        "donemler": donemler,
        "uyarilar": uyarilar,
        "mukellefler": [{"vkn": v, "unvan": u} for v, u in mukellefler],
    }


def _donem_etiketi(yil, ay):
    return "%d/%s" % (yil, AYLAR[ay - 1])


def _degisenler(ilk, son):
    """Iki surum arasinda degisen satirlar."""
    if ilk is son:
        return []
    satirlar = []
    for kod in VERI_KODLARI:
        a = ilk["degerler"].get(kod)
        b = son["degerler"].get(kod)
        if a is None and b is None:
            continue
        a = a or 0.0
        b = b or 0.0
        if abs(b - a) > 0.005:
            satirlar.append({
                "kod": kod,
                "etiket": ETIKETLER.get(kod, kod),
                "ilk": round(a, 2),
                "son": round(b, 2),
                "fark": round(b - a, 2),
            })
    return satirlar


def _adim_adim(surumler):
    """Her duzeltmenin bir oncekine gore neyi degistirdigi."""
    adimlar = []
    for onceki, simdiki in zip(surumler, surumler[1:]):
        adimlar.append({
            "sira": simdiki["sira"],
            "etiket": simdiki["etiket"],
            "onay_zamani": simdiki["onay_zamani"],
            "duzeltme_nedeni": simdiki["duzeltme_nedeni"],
            "degisen": _degisenler(onceki, simdiki),
        })
    return adimlar


def karsilastirma_tablosu(donem, yalniz_degisen=True):
    """Bir donemin tum surumlerini satir bazinda yan yana verir.

    Sutunlar: ilk beyan, duzeltmeler (sirayla), son hal, fark (son - ilk).
    """
    surumler = donem["surumler"]
    kodlar = [kod for kod, _e, baslik in BEYAN_SATIRLARI if not baslik]
    satirlar = []
    for kod in kodlar:
        degerler = [s["degerler"].get(kod) for s in surumler]
        if all(d is None for d in degerler):
            continue
        sayilar = [d or 0.0 for d in degerler]
        fark = round(sayilar[-1] - sayilar[0], 2)
        degisti = abs(fark) > 0.005 or any(
            abs(b - a) > 0.005 for a, b in zip(sayilar, sayilar[1:]))
        if yalniz_degisen and not degisti:
            continue
        satirlar.append({
            "kod": kod,
            "etiket": ETIKETLER.get(kod, kod),
            "degerler": [round(s, 2) for s in sayilar],
            "fark": fark,
            "degisti": degisti,
            "onemli": kod in ONEMLI_KODLAR,
        })
    return satirlar


def secimi_coz(duzen, secim):
    """Secime gore her donemde hangi surumun kullanilacagini belirler.

    secim: {"mod": "ilk" | "son" | "elle", "secimler": {"2024-12": 1}}
    Doner: {donem_anahtari: surum}
    """
    secim = secim or {}
    mod = secim.get("mod") or "son"
    elle = secim.get("secimler") or {}
    sonuc = {}
    for d in duzen["donemler"]:
        if mod == "elle" and d["anahtar"] in elle:
            try:
                sira = int(elle[d["anahtar"]])
            except (TypeError, ValueError):
                sira = d["surum_sayisi"] - 1
            sira = max(0, min(sira, d["surum_sayisi"] - 1))
            sonuc[d["anahtar"]] = d["surumler"][sira]
        elif mod == "ilk":
            sonuc[d["anahtar"]] = d["ilk"]
        else:
            sonuc[d["anahtar"]] = d["son"]
    return sonuc


def beyana_cevir(duzen, secim):
    """Secilen surumleri inceleme calismasinin beyan verisine cevirir.

    Doner: {"yillar": [{"yil", "ay_sayisi", "beyan": {kod: [12 deger]},
                        "dolu_aylar": [...]}], "kullanilan": [...]}
    """
    secilen = secimi_coz(duzen, secim)
    yillar = {}
    kullanilan = []
    for d in duzen["donemler"]:
        surum = secilen.get(d["anahtar"])
        if not surum:
            continue
        kayit = yillar.setdefault(d["yil"], {
            "yil": d["yil"],
            "beyan": {kod: [0.0] * 12 for kod in VERI_KODLARI},
            "dolu_aylar": [],
        })
        for kod in VERI_KODLARI:
            deger = surum["degerler"].get(kod)
            if deger is not None:
                kayit["beyan"][kod][d["ay"] - 1] = round(float(deger), 2)
        if d["ay"] not in kayit["dolu_aylar"]:
            kayit["dolu_aylar"].append(d["ay"])
        kullanilan.append({
            "donem": d["etiket"],
            "anahtar": d["anahtar"],
            "surum": surum["etiket"],
            "sira": surum["sira"],
            "onay_zamani": surum["onay_zamani"],
            "kaynak": surum["kaynak"],
        })

    liste = []
    for yil in sorted(yillar):
        kayit = yillar[yil]
        kayit["dolu_aylar"].sort()
        kayit["ay_sayisi"] = max(kayit["dolu_aylar"]) if kayit["dolu_aylar"] else 12
        liste.append(kayit)
    return {"yillar": liste, "kullanilan": kullanilan,
            "mukellef": mukellef_bilgisi(duzen),
            "uyarilar": [u for u in duzen["uyarilar"] if "vergi kimlik" in u]}


def mukellef_bilgisi(duzen):
    """Beyannamelerden okunan mukellef kimligi.

    Beyanname PDF'i mukellefin VKN'sini, unvanini ve vergi dairesini de
    tasiyor; bunlar calismaya yazilirsa kullanicinin elle girmesi gerekmez.
    Birden cok VKN varsa kimlik verilmez: karisik bir yigini tek mukellefe
    mal etmek, yanlis kimlikle rapor uretmek demektir. `duzenle` bu durumu
    zaten uyari olarak bildirir.
    """
    kimlikler = duzen.get("mukellefler") or []
    vknler = {k["vkn"] for k in kimlikler if k["vkn"]}
    if len(vknler) != 1:
        return None
    vkn = sorted(vknler)[0]
    unvan = next((k["unvan"] for k in kimlikler if k["vkn"] == vkn and k["unvan"]), "")
    daire = ""
    for d in duzen["donemler"]:
        for s in d["surumler"]:
            if s["vkn"] == vkn and s["vergi_dairesi"]:
                daire = s["vergi_dairesi"]
                break
        if daire:
            break
    return {"vkn_tckn": vkn, "ad_unvan": unvan, "vergi_dairesi": daire}


# Rapora yapistirilan "duzeltme beyannameleri" tablosunun kolon duzeni.
# Elde kullanilan tablonun birebir karsiligidir.
DUZELTME_KOLONLARI = [
    ("donem", "Dönemi"),
    ("tarih", "Düzeltme Tarihi"),
    ("matrah_toplami", "KDV Matrahı"),
    ("hesaplanan_kdv", "Hspl. KDV"),
    ("onceki_donem_devreden", "Önc. Dön. Dev. KDV"),
    ("bu_donem_indirilecek", "Bu Dön. İndl. KDV"),
    ("indirimler_toplami", "İndirimler Toplamı"),
    ("odenmesi_gereken_kdv", "Öden. KDV"),
    ("sonraki_donem_devreden", "Son. Dön. Dev. KDV"),
    ("gerekce", "Düzeltme Gerekçesi"),
]

# Tutar tasiyan kolonlar (metin kolonlarindan ayirmak icin)
DUZELTME_TUTAR_KODLARI = [kod for kod, _e in DUZELTME_KOLONLARI
                          if kod not in ("donem", "tarih", "gerekce")]


def _tarih(onay_zamani):
    """'27.04.2025 - 17:03:28' -> '27.04.2025'"""
    return (onay_zamani or "").split("-")[0].strip()


def duzeltme_tablosu(duzen):
    """Rapora yapistirilan duzeltme beyannameleri tablosu.

    Yalnizca duzeltme beyannameleri yer alir; kanuni suresinde verilen ilk
    beyanname bu tabloya girmez. Bir donemde birden cok duzeltme varsa her
    biri ayri satirdir. Tutarlar o duzeltme beyannamesinin kendi rakamlaridir.

    Siralama once DONEME, sonra donem icinde ONAY ZAMANINA goredir: aylar
    takvim sirasinda akar, bir donemin duzeltmeleri de kendi icinde verilis
    sirasiyla dizilir. Onay damgasi okunamayanlar donemin sonuna alinir.

    Doner: [{"yil", "satirlar": [{kod: deger}]}] — yil yil ayrilmis, cunku
    tablonun basligi "Dönemi <yil>" bicimindedir.
    """
    yillar = {}
    for d in duzen["donemler"]:
        for surum in d["surumler"]:
            if surum["tur"] != "duzeltme":
                continue
            satir = {
                "donem": d["ay_adi"],
                "tarih": _tarih(surum["onay_zamani"]),
                "gerekce": surum["duzeltme_nedeni"] or "",
                "sira": surum["sira"],
                "kaynak": surum["kaynak"],
                # Siralama icin; arayuze gosterilmez
                "onay_ts": surum["onay_ts"] or "",
                "ay": d["ay"],
            }
            for kod in DUZELTME_TUTAR_KODLARI:
                satir[kod] = round(surum["degerler"].get(kod) or 0.0, 2)
            yillar.setdefault(d["yil"], []).append(satir)

    for satirlar in yillar.values():
        # Once donem, sonra donem icinde onay zamani; damgasi olmayanlar sona
        satirlar.sort(key=lambda s: (s["ay"], s["onay_ts"] or "9999", s["sira"]))

    return [{"yil": yil, "satirlar": yillar[yil]} for yil in sorted(yillar)]


# Ayrintili duzeltme tablosunda yer alacak satirlar ve sirasi. Beyannamenin
# butun satirlari yazilmaz: turetilmis / tekrarli kalemler (toplam KDV, "bu
# doneme ait indirilecek KDV", teslim bedelleri) ayni degisikligi ikinci kez
# gostererek tabloyu okunmaz hale getiriyor.
# Ayrintili duzeltme tablosunun sutunlari. Hem rapor/tutanak (Word) hem de
# Excel ciktisi bunu kullanir; iki tablo birebir ayni olsun diye tek yerde
# tutulur.
AYRINTI_TABLO_KOLONLARI = [
    ("onceki_donem_devreden", "Önceki Dönemden\nDevreden KDV"),
    ("yurtici_alim_kdv", "Yurtiçi Alımlara\nİlişkin KDV"),
    ("indirimler_toplami", "İndirimler\nToplamı"),
    ("odenmesi_gereken_kdv", "Ödenmesi Gereken\nKDV"),
    ("sonraki_donem_devreden", "Son. Dön.\nDev. KDV"),
    ("iade_edilmesi_gereken_kdv", "İade Edil.\nKDV"),
]

AYRINTI_TABLO_SATIRLARI = ["Düzeltme Öncesi Beyanname", "Düzeltme Beyannamesi",
                           "Fark"]


AYRINTI_KODLARI = [
    "matrah_toplami",
    "hesaplanan_kdv",
    "ilave_edilecek_kdv",
    "onceki_donem_devreden",
    "yurtici_alim_kdv",
    "diger_indirimler_toplami",
    "indirimler_toplami",
    "odenmesi_gereken_kdv",
    "iade_edilmesi_gereken_kdv",
    "sonraki_donem_devreden",
]


def surum_dokumu(duzen, hangi="ilk"):
    """Her donem icin ilk ya da son beyannamenin ozet satiri.

    Rapordaki III. bolum uc tablo tasir: mukellefin ilk (kanuni suresinde
    verilen) beyannameleri, verdigi duzeltme beyannameleri ve beyanin son
    hali. Ilk ve son tablolar bu dokumden uretilir; kolonlar Sonuc ve Fark
    ekranindaki ozet kolonlariyla ayni olsun diye `OZET_ESLEMESI` kullanilir.

    Doner: [{"yil", "ay", "ay_adi", "ozet": {ozet_kodu: tutar}}]
    """
    # Rapordaki dokum tablosu "Hspl. KDV" sutununu `hesaplanan` adiyla okur;
    # ozet eslemesinde bu ad bulunmadigindan ayrica eklenir.
    esleme = dict(OZET_ESLEMESI, hesaplanan="hesaplanan_kdv")
    satirlar = []
    for d in duzen["donemler"]:
        surum = d["ilk"] if hangi == "ilk" else d["son"]
        ozet = {kod: round(surum["degerler"].get(kaynak) or 0.0, 2)
                for kod, kaynak in esleme.items()}
        satirlar.append({"yil": d["yil"], "ay": d["ay"], "ay_adi": d["ay_adi"],
                         "ozet": ozet})
    return satirlar


def _fark(karsilastirma, kod):
    """Bir donemde bir beyanname satirinin duzeltmeyle degisimi (sonrasi - oncesi)."""
    for s in karsilastirma["satirlar"]:
        if s["kod"] == kod:
            return s["fark"]
    return 0.0


def duzeltme_takibi(karsilastirmalar, baslangic_aylari, hedef_kdv=None,
                    unvan=None):
    """Duzeltmeyle cikarilan KDV'nin akibetini donem donem izler.

    Bir donemde indirimlerden cikarilan KDV her zaman o ay odenecek vergiye
    donusmez: o ayda devir varsa tutar once devri azaltir, izleyen aylarin
    "onceki donemden devreden KDV" satirindan dusulerek tasinir ve ancak
    odenecek verginin dogdugu ayda kapanir. Bu yuzden "fatura KDV'si gercekten
    cikarilmis mi" sorusu tek aya bakarak yanitlanamaz.

    Izleme su bicimde yurur:
      - baslangic, saticinin faturalarinin kaydedildigi (ya da gerekcesinde
        saticinin anildigi) donemdir,
      - o donemde YURTICI ALIMLAR satirindan dusulen tutar "cikarilan"dir,
      - her donemde odenecek verginin artisi (ve iadenin azalisi) kadari
        kapanir; kapanmayan kisim "devirde kalan" olarak sonraki aya gecer,
      - zincir, devreden KDV'de degisiklik olan aylar boyunca surer; kalan
        sifirlaninca ya da zincir kirilinca durur.

    Doner:
      {"donemler": [{"karsilastirma", "cikarilan", "devirden_dusen",
                     "odenecege_donusen", "kalan"}],
       "cikarilan_toplam", "odenecege_donusen_toplam", "devirde_kalan",
       "hedef", "tamamlandi", "eksik"}
    """
    sirali = sorted(karsilastirmalar or [], key=lambda k: (k["yil"], k["ay"]))
    ad = (unvan or "").lower().replace(".", "").strip()
    aylar = set(baslangic_aylari or [])

    izleme, kalan, cikarilan_toplam, kapanan_toplam = [], 0.0, 0.0, 0.0
    basladi = False
    for k in sirali:
        gerekce = (k.get("gerekce") or "").lower().replace(".", "")
        kendi_ayi = (k["yil"], k["ay"]) in aylar or (
            len(ad) > 4 and ad in gerekce)
        devirden_dusen = max(0.0, -_fark(k, "onceki_donem_devreden"))
        if not basladi and not kendi_ayi:
            continue
        if basladi and not kendi_ayi and devirden_dusen <= 0.005:
            break                                   # zincir kirildi
        basladi = True

        cikarilan = max(0.0, -_fark(k, "yurtici_alim_kdv"))
        kapanabilir = (max(0.0, _fark(k, "odenmesi_gereken_kdv"))
                       + max(0.0, -_fark(k, "iade_edilmesi_gereken_kdv")))
        kalan += cikarilan
        kapanan = min(kalan, kapanabilir)
        kalan = round(kalan - kapanan, 2)
        cikarilan_toplam = round(cikarilan_toplam + cikarilan, 2)
        kapanan_toplam = round(kapanan_toplam + kapanan, 2)
        izleme.append({
            "karsilastirma": k,
            "cikarilan": round(cikarilan, 2),
            "devirden_dusen": round(devirden_dusen, 2),
            "odenecege_donusen": round(kapanan, 2),
            "kalan": kalan,
        })
        if kalan <= 0.005 and cikarilan_toplam > 0.005:
            if hedef_kdv is None or cikarilan_toplam + 0.005 >= float(hedef_kdv):
                break

    eksik = None
    if hedef_kdv is not None:
        eksik = round(float(hedef_kdv) - cikarilan_toplam, 2)
        if eksik <= 0.005:
            eksik = 0.0
    return {
        "donemler": izleme,
        "cikarilan_toplam": cikarilan_toplam,
        "odenecege_donusen_toplam": kapanan_toplam,
        "devirde_kalan": kalan,
        "hedef": None if hedef_kdv is None else round(float(hedef_kdv), 2),
        "tamamlandi": bool(izleme) and (eksik in (None, 0.0)),
        "eksik": eksik,
    }


def duzeltme_karsilastirmalari(duzen):
    """Duzeltme verilen her donem icin satir bazinda oncesi / sonrasi tablosu.

    Rapordaki "duzeltme beyannamesinde yapilan duzeltmelere iliskin ayrintili
    tablo" bundan uretilir: hangi beyanname satirinin duzeltme oncesinde ve
    sonrasinda ne oldugu ve aradaki fark.

    Butun ayrinti kalemleri yazilir (farki sifir olanlar da): rapordaki tablo
    sabit sutunlu oldugundan eksik kalem tabloyu bozar. Hangi satirin degistigi
    "degisti" bayragindan okunur.

    Doner: [{"yil", "ay", "ay_adi", "etiket", "tarih", "gerekce",
             "gerekceler", "satirlar": [{"kod", "etiket", "oncesi", "sonrasi",
                                         "fark", "degisti"}]}]

    "gerekce" son duzeltmenin nedeni, "gerekceler" ise butun duzeltme
    surumlerinin nedenleridir (sirali, yinelenmeden).
    """
    adlar = dict(OZET_HEDEF_SECENEKLERI)
    adlar["yurtici_alim_kdv"] = "Yurtiçi Alımlara İlişkin KDV"
    sonuc = []
    for d in duzen["donemler"]:
        if d["surum_sayisi"] < 2:
            continue
        ilk, son = d["ilk"], d["son"]
        satirlar = []
        for kod in AYRINTI_KODLARI:
            oncesi = ilk["degerler"].get(kod) or 0.0
            sonrasi = son["degerler"].get(kod) or 0.0
            fark = round(sonrasi - oncesi, 2)
            satirlar.append({
                "kod": kod,
                "etiket": adlar.get(kod) or ETIKETLER.get(kod, kod),
                "oncesi": round(oncesi, 2),
                "sonrasi": round(sonrasi, 2),
                "fark": fark,
                "degisti": abs(fark) > 0.005,
            })
        if not any(s["degisti"] for s in satirlar):
            continue
        # Gerekce yalnizca son duzeltmeden okunamaz: bir donem icin birden cok
        # duzeltme verilmisse aranan aciklama (ornegin cikarilan faturanin
        # kimligi) cogu zaman ARADAKI duzeltmededir; sonuncusu "devir KDV
        # beyaninin duzeltilmesi" gibi teknik bir not tasir. Bu yuzden butun
        # duzeltme surumlerinin gerekceleri sirasiyla toplanir.
        gerekceler = []
        for s in d["surumler"][1:]:
            g = (s["duzeltme_nedeni"] or "").strip()
            if g and g not in gerekceler:
                gerekceler.append(g)
        sonuc.append({
            "yil": d["yil"], "ay": d["ay"], "ay_adi": d["ay_adi"],
            "etiket": d["etiket"], "tarih": _tarih(son["onay_zamani"]),
            "gerekce": son["duzeltme_nedeni"] or "",
            "gerekceler": gerekceler,
            "satirlar": satirlar,
            # Ayrintili tablo bunu kullanir: bir doneme birden cok duzeltme
            # verilmisse her biri bir onceki surumle karsilastirilmis olarak
            # burada durur. Tarhiyat hesabi yine yukaridaki toplam farktan
            # beslenir.
            "adimlar": _donem_adimlari(d),
        })
    return sonuc


def duzeltme_adimlari(duzen):
    """Her duzeltme beyannamesini BIR ONCEKI surumle karsilastirir.

    `duzeltme_karsilastirmalari` bir donem icin TEK karsilastirma verir:
    kanuni beyan ile SON duzeltme. Bir doneme birden cok duzeltme verilmisse
    aradaki adimlar o tabloda kaybolur ve "Duzeltme Oncesi / Duzeltme
    Beyannamesi" basligi hangi iki beyanname arasindaki farki gosterdigini
    soylemez. Burasi zinciri adim adim verir: 1. duzeltme kanuni beyanla,
    2. duzeltme 1. duzeltmeyle karsilastirilir.

    Tarhiyat ve devir takibi bundan DEGIL, toplam farki veren
    `duzeltme_karsilastirmalari`'ndan beslenir; burasi yalnizca gosterim
    icindir, yoksa ayni donem birden cok kez sayilirdi.

    Doner: [{"yil", "ay", "ay_adi", "etiket", "sira", "adim_sayisi",
             "oncesi_etiketi", "sonrasi_etiketi", "tarih", "gerekce",
             "satirlar": [{"kod", "etiket", "oncesi", "sonrasi", "fark",
                           "degisti"}]}]
    """
    sonuc = []
    for d in duzen["donemler"]:
        sonuc.extend(_donem_adimlari(d))
    return sonuc


def _donem_adimlari(d):
    """Bir donemin duzeltme zincirini adim adim karsilastirir."""
    adlar = dict(OZET_HEDEF_SECENEKLERI)
    adlar["yurtici_alim_kdv"] = "Yurtiçi Alımlara İlişkin KDV"
    sonuc = []
    surumler = d["surumler"]
    if len(surumler) < 2:
        return sonuc
    adim_sayisi = len(surumler) - 1
    for sira, (onceki, simdiki) in enumerate(zip(surumler, surumler[1:]), 1):
        satirlar = []
        for kod in AYRINTI_KODLARI:
            oncesi = onceki["degerler"].get(kod) or 0.0
            sonrasi = simdiki["degerler"].get(kod) or 0.0
            fark = round(sonrasi - oncesi, 2)
            satirlar.append({
                "kod": kod,
                "etiket": adlar.get(kod) or ETIKETLER.get(kod, kod),
                "oncesi": round(oncesi, 2),
                "sonrasi": round(sonrasi, 2),
                "fark": fark,
                "degisti": abs(fark) > 0.005,
            })
        if not any(x["degisti"] for x in satirlar):
            # Hicbir kalemi degistirmeyen duzeltme (orn. yalnizca kunye
            # duzeltmesi) tabloya bos bir blok olarak girmesin.
            continue
        # Tek duzeltme varsa basliklar eskisi gibi kalir; boylece dosyalarin
        # ezici cogunlugunda belge ciktisi degismez. Birden cok duzeltme
        # varsa hangi ikisinin karsilastirildigi basliktan okunur.
        if adim_sayisi == 1:
            oncesi_etiketi, sonrasi_etiketi = ("Düzeltme Öncesi Beyanname",
                                               "Düzeltme Beyannamesi")
        else:
            oncesi_etiketi = ("Düzeltme Öncesi Beyanname" if sira == 1
                              else "%d. Düzeltme Beyannamesi" % (sira - 1))
            sonrasi_etiketi = "%d. Düzeltme Beyannamesi" % sira
        sonuc.append({
            "yil": d["yil"], "ay": d["ay"], "ay_adi": d["ay_adi"],
            "etiket": d["etiket"], "sira": sira, "adim_sayisi": adim_sayisi,
            "oncesi_etiketi": oncesi_etiketi,
            "sonrasi_etiketi": sonrasi_etiketi,
            "tarih": _tarih(simdiki["onay_zamani"]),
            "gerekce": simdiki["duzeltme_nedeni"] or "",
            "satirlar": satirlar,
        })
    return sonuc


def genel_bakis(duzen):
    """Her beyanname surumu icin bir satir.

    Donem basina tek satir verilmez: bir donemde kac beyanname varsa o kadar
    satir olur (kanuni beyan ve ardindan her duzeltme ayri ayri). Boylece
    araya giren duzeltmeler gorunur kalir; yalnizca ilk ve son hal
    karsilastirilinca ortadaki adimlar kayboluyordu.

    Bir duzeltme hicbir rakami degistirmemis olsa da satiri yine yazilir;
    farklar sifir gorunur. "Degisiklik yok" bilgisinin kendisi de bir
    bulgudur ve beyannamenin verilmis olmasi gizlenmemelidir.

    Tutar kolonlari Sonuc ve Fark sekmesindeki ozet tabloyla aynidir
    (`OZET_KOLONLARI`); hangi beyanname satirindan geldikleri
    `OZET_ESLEMESI` ile belirlenir. Boylece iki ekran yan yana okunabilir.

    "ozet_degisen", bu beyannamede BIR ONCEKI beyannameye gore degismis olan
    kolonlarin listesidir; arayuz o hucreleri vurgular.
    """
    def al(kaynak, kod):
        return round(kaynak.get(kod) or 0.0, 2)

    satirlar = []
    for d in duzen["donemler"]:
        onceki_surum = None
        for s in d["surumler"]:
            simdiki = s["degerler"]
            ilk_mi = onceki_surum is None
            onceki = {} if ilk_mi else onceki_surum["degerler"]
            ozet, degisen = {}, []
            for ozet_kod, _etiket in OZET_KOLONLARI:
                beyan_kod = OZET_ESLEMESI.get(ozet_kod)
                deger = al(simdiki, beyan_kod) if beyan_kod else 0.0
                ozet[ozet_kod] = deger
                if not ilk_mi and beyan_kod \
                        and abs(deger - al(onceki, beyan_kod)) > 0.005:
                    degisen.append(ozet_kod)
            satirlar.append({
                "anahtar": d["anahtar"],
                "yil": d["yil"],
                "ay_adi": d["ay_adi"],
                "etiket": d["etiket"],
                "sira": s["sira"],
                "tur": s["tur"],
                "surum_etiketi": s["etiket"],
                "tarih": _tarih(s["onay_zamani"]),
                "ilk_mi": ilk_mi,
                "gerekce": s["duzeltme_nedeni"] or "",
                # Bu surumde bir onceki surume gore degisen satir sayisi
                "degisen_satir": 0 if ilk_mi else len(_degisenler(onceki_surum, s)),
                "ozet": ozet,
                "ozet_degisen": degisen,
            })
            onceki_surum = s
    return satirlar
