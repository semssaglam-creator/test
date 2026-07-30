"""KDV yeniden hesaplama motoru.

Excel calismasindaki 2-21 satirlarinin karsiligidir. Beyan edilen degerler ve
inceleme elestirileri girdi alinir; elestirili (duzeltilmis) beyan, donem donem
yeniden hesaplanir.

Kritik davranis - devir zinciri:
    Bir donemde yapilan elestiri, o donemin "sonraki doneme devreden KDV"
    tutarini degistirir. Bu tutar, izleyen donemin "onceki donemden devreden
    KDV" girdisi olur. Zincir, yil sinirinda kesilmez: Aralik ayinin duzeltilmis
    devri, izleyen yilin Ocak ayina tasinir. Boylece tek bir donemde yapilan
    tespit, sonraki tum donemlere kendiliginden yansir.
"""
from .satirlar import AYLAR, VERI_KODLARI, varsayilan_kdv_orani


def _d(degerler, kod, ay):
    """Beyan sozlugunden guvenli deger okur."""
    dizi = degerler.get(kod) or []
    if ay < len(dizi) and dizi[ay] is not None:
        try:
            return float(dizi[ay])
        except (TypeError, ValueError):
            return 0.0
    return 0.0


def _yuvarla(deger):
    return round(deger + 0.0, 2)


def bos_beyan():
    return {kod: [0.0] * 12 for kod in VERI_KODLARI}


def _devir_pini(yil_kaydi):
    """Yila ozel baslangic devri (yoksa None).

    Bu deger verildiginde o yilin Ocak ayina onceki yildan gelen devir yerine
    bu tutar tasinir. Boylece incelemenin bir yildan baslatilmasi ya da bir
    yilin acilis devrinin ayrica belirlenmesi mumkun olur.
    """
    ham = yil_kaydi.get("devir_baslangic")
    if ham in (None, ""):
        return None
    try:
        return float(ham)
    except (TypeError, ValueError):
        return None


def bos_elestiri():
    return {
        "matrah_ilave": [0.0] * 12,
        "hesaplanan_kdv_ilave": [0.0] * 12,
        "devir_cikar": [0.0] * 12,
        "indirim_cikar": [0.0] * 12,
        "yuklenilen_cikar": [0.0] * 12,
        "kdv_orani": [None] * 12,
        "hesaplanan_otomatik": [True] * 12,
    }


def hesaplanan_kdv_ilavesi(elestiri, yil, ay):
    """Matrah ilavesine karsilik gelen hesaplanan KDV ilavesini dondurur.

    'hesaplanan_otomatik' isaretli donemlerde ilave matrah x donem orani ile
    bulunur; isaret kaldirilmissa kullanicinin girdigi tutar aynen kullanilir.
    Farkli oranli teslimlerde (%1, %10) oran alani elle degistirilebilir.
    """
    otomatik = (elestiri.get("hesaplanan_otomatik") or [True] * 12)
    elle = _d(elestiri, "hesaplanan_kdv_ilave", ay)
    if ay < len(otomatik) and not otomatik[ay]:
        return elle
    oranlar = elestiri.get("kdv_orani") or [None] * 12
    oran = oranlar[ay] if ay < len(oranlar) and oranlar[ay] is not None else None
    if oran is None:
        oran = varsayilan_kdv_orani(yil, ay + 1)
    return _yuvarla(_d(elestiri, "matrah_ilave", ay) * float(oran) / 100.0)


def _donem_hesapla(beyan, elestiri, yil, ay, devreden_giris):
    """Tek bir donemin elestirili sonuclarini hesaplar.

    devreden_giris: onceki donemin duzeltilmis "sonraki doneme devreden KDV"
    tutari. None ise (serinin ilk donemi) beyandaki devirden elestiri dusulur.
    """
    # --- Hesaplanan taraf (Excel 2-5) ---
    matrah = _d(beyan, "matrah_toplami", ay) + _d(elestiri, "matrah_ilave", ay)
    hesaplanan = _d(beyan, "hesaplanan_kdv", ay) + hesaplanan_kdv_ilavesi(elestiri, yil, ay)
    ilave_edilecek = _d(beyan, "ilave_edilecek_kdv", ay)
    toplam_kdv = hesaplanan + ilave_edilecek

    # --- Indirim tarafi (Excel 6-9) ---
    if devreden_giris is None:
        onceki_devir = _d(beyan, "onceki_donem_devreden", ay) - _d(elestiri, "devir_cikar", ay)
    else:
        # Zincirin ici: onceki donemin duzeltilmis devri esas alinir; bu donemde
        # ayrica bir devir elestirisi varsa o da dusulur.
        onceki_devir = devreden_giris - _d(elestiri, "devir_cikar", ay)
    bu_donem_indirim = _d(beyan, "bu_donem_indirilecek", ay) - _d(elestiri, "indirim_cikar", ay)
    diger_indirim = _d(beyan, "diger_indirimler_toplami", ay)
    indirimler = onceki_devir + bu_donem_indirim + diger_indirim

    # --- Iade hakki doguran islemler (Excel 14-15) ---
    iade_teslim = _d(beyan, "istisna_toplam_teslim", ay) + _d(beyan, "diger_iade_teslim", ay)
    iade_yuklenilen = (_d(beyan, "tam_istisna_yuklenilen", ay)
                       + _d(beyan, "diger_iade_kdv", ay)
                       - _d(elestiri, "yuklenilen_cikar", ay))

    # --- Ihrac kayitli teslimler (Excel 17-20) ---
    ihrac_teslim = _d(beyan, "ihrac_teslim_bedeli", ay)
    tecil_edilebilir = _d(beyan, "tecil_edilebilir_kdv", ay)

    # --- Sonuc hesaplari (Excel 10-13, 16, 19-20) ---
    fark = toplam_kdv - indirimler
    if fark > 0:
        # Odenecek durumu: once tecil, kalan odenir
        tecil_edilecek = min(fark, tecil_edilebilir)
        odenecek = fark - tecil_edilecek
        iade_edilecek = 0.0
        sonraki_devir = 0.0
    else:
        devir_fazlasi = -fark
        tecil_edilecek = 0.0
        odenecek = 0.0
        iade_edilecek = min(devir_fazlasi, max(iade_yuklenilen, 0.0))
        sonraki_devir = devir_fazlasi - iade_edilecek
    ihracat_iade_tecil_edilemeyen = tecil_edilebilir - tecil_edilecek

    return {
        "yil": yil,
        "ay": ay + 1,
        "ay_adi": AYLAR[ay],
        "matrah": _yuvarla(matrah),
        "hesaplanan": _yuvarla(hesaplanan),
        "ilave_edilecek": _yuvarla(ilave_edilecek),
        "toplam_kdv": _yuvarla(toplam_kdv),
        "onceki_devir": _yuvarla(onceki_devir),
        "bu_donem_indirim": _yuvarla(bu_donem_indirim),
        "diger_indirim": _yuvarla(diger_indirim),
        # Ozet tablosunda beyan tarafiyla ayni tanim kullanilir: bu doneme ait
        # indirilecek KDV ile 103+104+105 toplaminin birlesimi
        "bu_donem_indirim_toplam": _yuvarla(bu_donem_indirim + diger_indirim),
        "indirimler": _yuvarla(indirimler),
        "odenecek": _yuvarla(odenecek),
        "sonraki_devir": _yuvarla(sonraki_devir),
        "iade": _yuvarla(iade_edilecek),
        "tecil_edilecek": _yuvarla(tecil_edilecek),
        "iade_teslim": _yuvarla(iade_teslim),
        "iade_yuklenilen": _yuvarla(iade_yuklenilen),
        "ihrac_teslim": _yuvarla(ihrac_teslim),
        "tecil_edilebilir": _yuvarla(tecil_edilebilir),
        "ihracat_iade": _yuvarla(ihracat_iade_tecil_edilemeyen),
    }


def _beyan_ozeti(beyan, yil, ay):
    """Beyan edilen degerlerin ozet tablosu (Excel 100-113 blogu)."""
    return {
        "yil": yil,
        "ay": ay + 1,
        "ay_adi": AYLAR[ay],
        "matrah": _yuvarla(_d(beyan, "matrah_toplami", ay)),
        # Ozet kolonlari her iki tarafta ayni tanimi tasimali: "hesaplanan"
        # yalnizca hesaplanan KDV, "toplam_kdv" ilave edilecek KDV ile birlikte
        "hesaplanan": _yuvarla(_d(beyan, "hesaplanan_kdv", ay)),
        "ilave_edilecek": _yuvarla(_d(beyan, "ilave_edilecek_kdv", ay)),
        "toplam_kdv": _yuvarla(_d(beyan, "toplam_kdv", ay)),
        "onceki_devir": _yuvarla(_d(beyan, "onceki_donem_devreden", ay)),
        "bu_donem_indirim": _yuvarla(_d(beyan, "bu_donem_indirilecek", ay)),
        "diger_indirim": _yuvarla(_d(beyan, "diger_indirimler_toplami", ay)),
        "bu_donem_indirim_toplam": _yuvarla(_d(beyan, "bu_donem_indirilecek", ay)
                                            + _d(beyan, "diger_indirimler_toplami", ay)),
        "indirimler": _yuvarla(_d(beyan, "indirimler_toplami", ay)),
        "odenecek": _yuvarla(_d(beyan, "odenmesi_gereken_kdv", ay)),
        "sonraki_devir": _yuvarla(_d(beyan, "sonraki_donem_devreden", ay)),
        "iade": _yuvarla(_d(beyan, "iade_edilmesi_gereken_kdv", ay)),
        "tecil_edilecek": _yuvarla(_d(beyan, "tecil_edilecek_kdv", ay)),
        "ihracat_iade": _yuvarla(_d(beyan, "ihracat_tecil_edilemeyen", ay)),
    }


OZET_ALANLARI = ["matrah", "toplam_kdv", "onceki_devir", "bu_donem_indirim_toplam",
                 "indirimler", "odenecek", "sonraki_devir", "iade"]

# Fark ayristirmasinda karsilastirilan tum alanlar
AYRISTIRMA_ALANLARI = OZET_ALANLARI + ["tecil_edilecek", "ihracat_iade"]


def seri_hesapla(yillar, devreden_baslangic=None):
    """Cok yilli seriyi kronolojik sirada hesaplar.

    yillar: [{"yil": 2022, "ay_sayisi": 12, "beyan": {...}, "elestiri": {...}}, ...]
    devreden_baslangic: serinin ilk donemine tasinacak duzeltilmis devir
        (None ise ilk donemde beyandaki devir esas alinir).

    Doner: {"donemler": [...], "yil_toplamlari": [...], "genel_toplam": {...}}
    Her donem kaydi beyan / elestirili / fark uclusunu birlikte tasir.
    """
    donemler = []
    devreden = devreden_baslangic
    bos = bos_elestiri()
    for yil_kaydi in sorted(yillar, key=lambda y: y["yil"]):
        yil = int(yil_kaydi["yil"])
        beyan = yil_kaydi.get("beyan") or bos_beyan()
        elestiri = yil_kaydi.get("elestiri") or bos_elestiri()
        ay_sayisi = int(yil_kaydi.get("ay_sayisi") or 12)
        # Yila ozel baslangic devri verilmisse zincir bu yilin basinda o degerle
        # yeniden kurulur; onceki yildan gelen devir yerine bu tutar kullanilir.
        pin = _devir_pini(yil_kaydi)
        if pin is not None:
            devreden = pin
        for ay in range(min(max(ay_sayisi, 1), 12)):
            beyan_ozet = _beyan_ozeti(beyan, yil, ay)
            elestirili = _donem_hesapla(beyan, elestiri, yil, ay, devreden)

            # Farki bilesenlerine ayirmak icin iki ara senaryo:
            # beyan_hesap : beyandaki girdilerden, elestirisiz  -> beyanin
            #               kendi aritmetigi dogru olsaydi cikacak sonuc
            # tespit_tek  : beyandaki onceki devirle, YALNIZ bu donemin
            #               tespiti uygulanmis -> tespitin kendi etkisi
            beyan_devir = _d(beyan, "onceki_donem_devreden", ay)
            beyan_hesap = _donem_hesapla(beyan, bos, yil, ay, beyan_devir)
            tespit_tek = _donem_hesapla(beyan, elestiri, yil, ay, beyan_devir)

            fark = {a: _yuvarla(elestirili[a] - beyan_ozet[a]) for a in AYRISTIRMA_ALANLARI}
            fark_beyan_hatasi = {a: _yuvarla(beyan_hesap[a] - beyan_ozet[a])
                                 for a in AYRISTIRMA_ALANLARI}
            fark_tespit = {a: _yuvarla(tespit_tek[a] - beyan_hesap[a])
                           for a in AYRISTIRMA_ALANLARI}
            fark_devir = {a: _yuvarla(elestirili[a] - tespit_tek[a])
                          for a in AYRISTIRMA_ALANLARI}

            donemler.append({
                "yil": yil,
                "ay": ay + 1,
                "ay_adi": AYLAR[ay],
                "beyan": beyan_ozet,
                "beyan_hesap": beyan_hesap,
                "elestirili": elestirili,
                "fark": fark,
                "fark_beyan_hatasi": fark_beyan_hatasi,
                "fark_tespit": fark_tespit,
                "fark_devir": fark_devir,
                "elestiri_var": _elestiri_var(elestiri, ay),
                "tarhiyat": _tarhiyat_satiri(beyan_ozet, elestirili),
            })
            devreden = elestirili["sonraki_devir"]

    return {
        "donemler": donemler,
        "yil_toplamlari": _yil_toplamlari(donemler),
        "genel_toplam": _toplam(donemler),
        "tarhiyat_toplami": _tarhiyat_toplami(donemler),
        "yil_uyumu": _yil_uyumu(donemler),
    }


def _tarhiyat_satiri(beyan_ozet, elestirili):
    """Bir donemin tarhiyat ozeti satirini uretir.

    Sutunlar, elde kullanilan tarhiyat tablosunun karsiligidir:
      1) Re'sen tarhi gereken KDV  = olmasi gereken odenecek - beyan edilen
      2) Aranmasi gereken KDV      = beyan edilen iade - olmasi gereken iade
      3) Haksiz olarak iade edilen = beyan edilen ihracat iadesi - olmasi gereken
    Her uc sutun da yalnizca mukellef aleyhine olan yonu tasir; ters yondeki
    tutar (fazla beyan) ayri alanlarda bildirilir, tarhiyata eklenmez.
    """
    odenecek_fark = elestirili["odenecek"] - beyan_ozet["odenecek"]
    iade_fark = beyan_ozet["iade"] - elestirili["iade"]
    ihracat_fark = beyan_ozet["ihracat_iade"] - elestirili["ihracat_iade"]

    resen = max(odenecek_fark, 0.0)
    aranmasi = max(iade_fark, 0.0)
    haksiz = max(ihracat_fark, 0.0)
    return {
        "odenecek_olmasi_gereken": _yuvarla(elestirili["odenecek"]),
        "odenecek_beyan": _yuvarla(beyan_ozet["odenecek"]),
        "resen_tarhi_gereken": _yuvarla(resen),
        "iade_olmasi_gereken": _yuvarla(elestirili["iade"]),
        "iade_beyan": _yuvarla(beyan_ozet["iade"]),
        "aranmasi_gereken": _yuvarla(aranmasi),
        "resen_toplam": _yuvarla(resen + aranmasi),
        "ihracat_iade_olmasi_gereken": _yuvarla(elestirili["ihracat_iade"]),
        "ihracat_iade_beyan": _yuvarla(beyan_ozet["ihracat_iade"]),
        "haksiz_iade": _yuvarla(haksiz),
        "toplam_fark": _yuvarla(resen + aranmasi + haksiz),
        # Mukellef lehine olan sapmalar: tarhiyata girmez, bilgi amaclidir
        "fazla_beyan_odenecek": _yuvarla(max(-odenecek_fark, 0.0)),
        "eksik_talep_iade": _yuvarla(max(-iade_fark, 0.0)),
    }


TARHIYAT_ALANLARI = ["odenecek_olmasi_gereken", "odenecek_beyan", "resen_tarhi_gereken",
                     "iade_olmasi_gereken", "iade_beyan", "aranmasi_gereken", "resen_toplam",
                     "ihracat_iade_olmasi_gereken", "ihracat_iade_beyan", "haksiz_iade",
                     "toplam_fark", "fazla_beyan_odenecek", "eksik_talep_iade"]


def _tarhiyat_toplami(donemler):
    return {a: _yuvarla(sum(d["tarhiyat"][a] for d in donemler)) for a in TARHIYAT_ALANLARI}


def _yil_uyumu(donemler):
    """Yil bazinda beyan uyumu ozeti (cok yilli incelemelerde genel gorunum)."""
    satirlar = []
    for yil in sorted({d["yil"] for d in donemler}):
        alt = [d for d in donemler if d["yil"] == yil]
        satirlar.append({
            "yil": yil,
            "donem_sayisi": len(alt),
            "tespit_donem_sayisi": sum(1 for d in alt if d["elestiri_var"]),
            "matrah_beyan": _yuvarla(sum(d["beyan"]["matrah"] for d in alt)),
            "matrah_olmasi_gereken": _yuvarla(sum(d["elestirili"]["matrah"] for d in alt)),
            "matrah_farki": _yuvarla(sum(d["fark"]["matrah"] for d in alt)),
            "odenecek_beyan": _yuvarla(sum(d["beyan"]["odenecek"] for d in alt)),
            "odenecek_olmasi_gereken": _yuvarla(sum(d["elestirili"]["odenecek"] for d in alt)),
            "resen_tarhi_gereken": _yuvarla(sum(d["tarhiyat"]["resen_tarhi_gereken"] for d in alt)),
            "toplam_fark": _yuvarla(sum(d["tarhiyat"]["toplam_fark"] for d in alt)),
            "tespit_etkisi": _yuvarla(sum(d["fark_tespit"]["odenecek"] for d in alt)),
            "devir_etkisi": _yuvarla(sum(d["fark_devir"]["odenecek"] for d in alt)),
            "beyan_hatasi_etkisi": _yuvarla(sum(d["fark_beyan_hatasi"]["odenecek"] for d in alt)),
            "devir_giris": _yuvarla(alt[0]["elestirili"]["onceki_devir"]),
            "devir_cikis": _yuvarla(alt[-1]["elestirili"]["sonraki_devir"]),
            "devir_cikis_beyan": _yuvarla(alt[-1]["beyan"]["sonraki_devir"]),
        })
    return satirlar


def kaynak_anahtari(yil, ay):
    """Bir tespit kaynagini benzersiz tanimlar (ay: 0-11)."""
    return f"{yil}-{ay + 1:02d}"


def _zincir(yillar, devreden_baslangic, aktif=None):
    """Seriyi hesaplar; `aktif` verilirse yalnizca o donemlerin tespiti uygulanir.

    aktif=None  -> tum tespitler acik (tam senaryo)
    aktif=set() -> hicbir tespit yok (baz senaryo)
    aktif={"2023-01"} -> yalnizca Ocak 2023 tespiti acik
    """
    bos = bos_elestiri()
    sonuc = {}
    devreden = devreden_baslangic
    for yil_kaydi in sorted(yillar, key=lambda y: y["yil"]):
        yil = int(yil_kaydi["yil"])
        beyan = yil_kaydi.get("beyan") or bos_beyan()
        elestiri = yil_kaydi.get("elestiri") or bos_elestiri()
        ay_sayisi = min(max(int(yil_kaydi.get("ay_sayisi") or 12), 1), 12)
        pin = _devir_pini(yil_kaydi)
        if pin is not None:
            devreden = pin
        for ay in range(ay_sayisi):
            anahtar = kaynak_anahtari(yil, ay)
            kullanilan = elestiri if (aktif is None or anahtar in aktif) else bos
            kayit = _donem_hesapla(beyan, kullanilan, yil, ay, devreden)
            sonuc[anahtar] = kayit
            devreden = kayit["sonraki_devir"]
    return sonuc


KAYNAK_ETKI_ALANLARI = ["odenecek", "sonraki_devir", "iade", "indirimler", "matrah"]


def kaynak_analizi(yillar, devreden_baslangic=None):
    """Her tespitin, sonraki tum donemlere yaptigi etkiyi ayri ayri hesaplar.

    Bir tespit yalnizca girildigi donemi degil, devir zinciri yoluyla izleyen
    tum donemleri etkiler. Ornegin 2023/Ocak'ta matraha yapilan ilave ile
    2024/Subat'ta yapilan indirim reddinin 2026/Nisan'daki sonuca katkilari
    burada ayri ayri gorulur.

    Yontem: her tespit tek basina acilarak seri bastan hesaplanir ve baz
    senaryodan (hicbir tespit yok) farki o tespitin katkisi sayilir.

    Onemli: hesap dogrusal degildir (odenecek/devir esiginde min-max vardir).
    Bu nedenle tekil katkilarin toplami, tum tespitler birlikte uygulandigindaki
    farki tam vermeyebilir. Aradaki bakiye "etkilesim" olarak ayri bildirilir;
    gizlenmez ve kaynaklara dagitilmaz.
    """
    kaynaklar = []
    for yil_kaydi in sorted(yillar, key=lambda y: y["yil"]):
        yil = int(yil_kaydi["yil"])
        elestiri = yil_kaydi.get("elestiri") or bos_elestiri()
        ay_sayisi = min(max(int(yil_kaydi.get("ay_sayisi") or 12), 1), 12)
        for ay in range(ay_sayisi):
            if not _elestiri_var(elestiri, ay):
                continue
            kaynaklar.append({
                "anahtar": kaynak_anahtari(yil, ay),
                "yil": yil,
                "ay": ay + 1,
                "ay_adi": AYLAR[ay],
                "etiket": f"{yil}/{AYLAR[ay]}",
                "matrah_ilave": _yuvarla(_d(elestiri, "matrah_ilave", ay)),
                "hesaplanan_kdv_ilave": _yuvarla(hesaplanan_kdv_ilavesi(elestiri, yil, ay)),
                "devir_cikar": _yuvarla(_d(elestiri, "devir_cikar", ay)),
                "indirim_cikar": _yuvarla(_d(elestiri, "indirim_cikar", ay)),
                "yuklenilen_cikar": _yuvarla(_d(elestiri, "yuklenilen_cikar", ay)),
            })

    baz = _zincir(yillar, devreden_baslangic, aktif=set())
    tam = _zincir(yillar, devreden_baslangic, aktif=None)
    sirali = list(baz.keys())

    katkilar = {}
    for kaynak in kaynaklar:
        tek = _zincir(yillar, devreden_baslangic, aktif={kaynak["anahtar"]})
        katkilar[kaynak["anahtar"]] = {
            anahtar: {alan: _yuvarla(tek[anahtar][alan] - baz[anahtar][alan])
                      for alan in KAYNAK_ETKI_ALANLARI}
            for anahtar in sirali
        }

    # Donem donem dagilim: her kaynagin katkisi + etkilesim bakiyesi
    donemler = []
    for anahtar in sirali:
        toplam = {alan: _yuvarla(tam[anahtar][alan] - baz[anahtar][alan])
                  for alan in KAYNAK_ETKI_ALANLARI}
        paylar = {k["anahtar"]: katkilar[k["anahtar"]][anahtar] for k in kaynaklar}
        etkilesim = {
            alan: _yuvarla(toplam[alan] - sum(p[alan] for p in paylar.values()))
            for alan in KAYNAK_ETKI_ALANLARI
        }
        if (any(abs(v) > 0.005 for v in toplam.values())
                or any(abs(v) > 0.005 for p in paylar.values() for v in p.values())):
            yil, ay = anahtar.split("-")
            donemler.append({
                "anahtar": anahtar,
                "yil": int(yil),
                "ay": int(ay),
                "ay_adi": AYLAR[int(ay) - 1],
                "etiket": f"{yil}/{AYLAR[int(ay) - 1]}",
                "paylar": paylar,
                "etkilesim": etkilesim,
                "toplam": toplam,
            })

    # Her kaynagin seri genelindeki toplam etkisi
    for kaynak in kaynaklar:
        pay = katkilar[kaynak["anahtar"]]
        kaynak["toplam_odenecek_etkisi"] = _yuvarla(
            sum(pay[a]["odenecek"] for a in sirali))
        kaynak["son_donem_devir_etkisi"] = _yuvarla(
            pay[sirali[-1]]["sonraki_devir"]) if sirali else 0.0
        etkilenen = [a for a in sirali if any(abs(pay[a][alan]) > 0.005
                                              for alan in KAYNAK_ETKI_ALANLARI)]
        kaynak["etkilenen_donem_sayisi"] = len(etkilenen)
        kaynak["ilk_etki"] = etkilenen[0] if etkilenen else None
        kaynak["son_etki"] = etkilenen[-1] if etkilenen else None

    etkilesim_var = any(abs(v) > 0.005 for d in donemler for v in d["etkilesim"].values())
    return {
        "kaynaklar": kaynaklar,
        "donemler": donemler,
        "etkilesim_var": etkilesim_var,
    }


def beyan_tutarlilik_kontrol(yillar):
    """Beyan edilen degerleri kendi icinde denetler ve bulgu listesi dondurur.

    Uc denetim yapilir:
    1) Devir zinciri: bir donemin beyan edilen "onceki donem devreden KDV"
       tutari, bir onceki donemin beyan edilen "sonraki doneme devreden KDV"
       tutarina esit olmalidir. (Yil sinirinda da surer.)
    2) Indirimler toplami: onceki devir + bu donem indirimi + diger indirimler
       toplamina esit olmalidir.
    3) Sonuc hesaplari: beyan edilen odenecek/devreden tutarlari, beyandaki
       hesaplanan ve indirim rakamlariyla uyumlu olmalidir.

    Excel calismasinda bulunmayan bu denetim, beyanname hatalarini elestiri
    girilmeden once ortaya cikarir.
    """
    bulgular = []
    onceki = None  # (yil, ay, ay_adi, beyan edilen sonraki devir)
    for yil_kaydi in sorted(yillar, key=lambda y: y["yil"]):
        yil = int(yil_kaydi["yil"])
        beyan = yil_kaydi.get("beyan") or bos_beyan()
        ay_sayisi = min(max(int(yil_kaydi.get("ay_sayisi") or 12), 1), 12)
        for ay in range(ay_sayisi):
            donem = f"{yil}/{AYLAR[ay]}"
            onceki_devir = _d(beyan, "onceki_donem_devreden", ay)
            sonraki_devir = _d(beyan, "sonraki_donem_devreden", ay)

            # Zincir denetimi yalnizca birbirini izleyen donemler icin gecerlidir.
            # Arada eksik donem varsa (ornegin bir yil yuklenmemisse) devirin
            # tutmamasi beklenir; bu bir tutarsizlik degil, veri bosluguduur.
            if onceki is not None:
                ardisik = ((onceki[0] == yil and onceki[1] == ay - 1)
                           or (onceki[0] == yil - 1 and onceki[1] == 11 and ay == 0))
                if not ardisik:
                    bulgular.append({
                        "donem": donem,
                        "tur": "donem_boslugu",
                        "mesaj": (f"{onceki[0]}/{onceki[2]} ile {donem} arasında yüklenmemiş "
                                  f"dönem var. Devir zinciri bu boşlukta kesildiği için "
                                  f"aradaki devir farkı denetlenemedi."),
                    })
                    onceki = None

            if onceki is not None and abs(onceki[3] - onceki_devir) > 0.01:
                bulgular.append({
                    "donem": donem,
                    "tur": "devir_zinciri",
                    "mesaj": (f"{onceki[0]}/{onceki[2]} dönemi sonraki döneme devreden KDV "
                              f"{onceki[3]:,.2f} TL iken, {donem} dönemi önceki dönemden "
                              f"devreden KDV {onceki_devir:,.2f} TL beyan edilmiş. "
                              f"Fark: {onceki_devir - onceki[3]:,.2f} TL."),
                })

            beklenen_indirim = (onceki_devir + _d(beyan, "bu_donem_indirilecek", ay)
                                + _d(beyan, "diger_indirimler_toplami", ay))
            beyan_indirim = _d(beyan, "indirimler_toplami", ay)
            if abs(beklenen_indirim - beyan_indirim) > 0.01:
                bulgular.append({
                    "donem": donem,
                    "tur": "indirim_toplami",
                    "mesaj": (f"{donem} indirimler toplamı {beyan_indirim:,.2f} TL beyan edilmiş; "
                              f"alt kalemlerin toplamı {beklenen_indirim:,.2f} TL. "
                              f"Fark: {beyan_indirim - beklenen_indirim:,.2f} TL."),
                })

            fark = _d(beyan, "toplam_kdv", ay) - beyan_indirim
            tecil = _d(beyan, "tecil_edilecek_kdv", ay)
            beklenen_odenecek = max(fark - tecil, 0.0) if fark > 0 else 0.0
            beklenen_devir = max(-fark - _d(beyan, "iade_edilmesi_gereken_kdv", ay), 0.0) \
                if fark < 0 else 0.0
            if abs(beklenen_odenecek - _d(beyan, "odenmesi_gereken_kdv", ay)) > 0.01:
                bulgular.append({
                    "donem": donem,
                    "tur": "sonuc_odenecek",
                    "mesaj": (f"{donem} ödenmesi gereken KDV "
                              f"{_d(beyan, 'odenmesi_gereken_kdv', ay):,.2f} TL beyan edilmiş; "
                              f"beyandaki rakamlara göre {beklenen_odenecek:,.2f} TL olmalıydı."),
                })
            if abs(beklenen_devir - sonraki_devir) > 0.01:
                bulgular.append({
                    "donem": donem,
                    "tur": "sonuc_devir",
                    "mesaj": (f"{donem} sonraki döneme devreden KDV {sonraki_devir:,.2f} TL "
                              f"beyan edilmiş; beyandaki rakamlara göre "
                              f"{beklenen_devir:,.2f} TL olmalıydı."),
                })

            onceki = (yil, ay, AYLAR[ay], sonraki_devir)
    return bulgular


def _elestiri_var(elestiri, ay):
    return any(abs(_d(elestiri, alan, ay)) > 0 for alan in
               ("matrah_ilave", "hesaplanan_kdv_ilave", "devir_cikar",
                "indirim_cikar", "yuklenilen_cikar"))


def _toplam(donemler):
    """Toplam satiri.

    Devir sutunlari stok niteliginde oldugu icin toplanmaz; donem sonu
    (serinin son donemi) degeri gosterilir. Akim sutunlari toplanir.
    """
    akim = ["matrah", "toplam_kdv", "bu_donem_indirim_toplam", "indirimler",
            "odenecek", "iade"]
    sonuc = {"beyan": {}, "elestirili": {}, "fark": {}}
    for blok in ("beyan", "elestirili", "fark"):
        for alan in akim:
            sonuc[blok][alan] = _yuvarla(sum(d[blok].get(alan, 0.0) for d in donemler))
        son = donemler[-1][blok] if donemler else {}
        ilk = donemler[0][blok] if donemler else {}
        sonuc[blok]["sonraki_devir"] = _yuvarla(son.get("sonraki_devir", 0.0))
        sonuc[blok]["onceki_devir"] = _yuvarla(ilk.get("onceki_devir", 0.0))
    return sonuc


def _yil_toplamlari(donemler):
    yillar = []
    for yil in sorted({d["yil"] for d in donemler}):
        alt = [d for d in donemler if d["yil"] == yil]
        toplam = _toplam(alt)
        toplam["yil"] = yil
        yillar.append(toplam)
    return yillar
