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
from .satirlar import (AYLAR, BEYAN_SATIRLARI, ETIKETLER, OZET_KOLONLARI,
                       VERI_KODLARI)

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
    return {"yillar": liste, "kullanilan": kullanilan}


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
