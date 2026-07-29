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
        "indirimler": _yuvarla(indirimler),
        "odenecek": _yuvarla(odenecek),
        "sonraki_devir": _yuvarla(sonraki_devir),
        "iade": _yuvarla(iade_edilecek),
        "tecil_edilecek": _yuvarla(tecil_edilecek),
        "iade_teslim": _yuvarla(iade_teslim),
        "iade_yuklenilen": _yuvarla(iade_yuklenilen),
        "ihrac_teslim": _yuvarla(ihrac_teslim),
        "tecil_edilebilir": _yuvarla(tecil_edilebilir),
        "ihracat_iade_tecil_edilemeyen": _yuvarla(ihracat_iade_tecil_edilemeyen),
    }


def _beyan_ozeti(beyan, yil, ay):
    """Beyan edilen degerlerin ozet tablosu (Excel 100-113 blogu)."""
    return {
        "yil": yil,
        "ay": ay + 1,
        "ay_adi": AYLAR[ay],
        "matrah": _yuvarla(_d(beyan, "matrah_toplami", ay)),
        "hesaplanan": _yuvarla(_d(beyan, "toplam_kdv", ay)),
        "onceki_devir": _yuvarla(_d(beyan, "onceki_donem_devreden", ay)),
        "bu_donem_indirim": _yuvarla(_d(beyan, "bu_donem_indirilecek", ay)
                                     + _d(beyan, "diger_indirimler_toplami", ay)),
        "indirimler": _yuvarla(_d(beyan, "indirimler_toplami", ay)),
        "odenecek": _yuvarla(_d(beyan, "odenmesi_gereken_kdv", ay)),
        "sonraki_devir": _yuvarla(_d(beyan, "sonraki_donem_devreden", ay)),
        "iade": _yuvarla(_d(beyan, "iade_edilmesi_gereken_kdv", ay)),
        "tecil_edilecek": _yuvarla(_d(beyan, "tecil_edilecek_kdv", ay)),
    }


OZET_ALANLARI = ["matrah", "hesaplanan", "onceki_devir", "bu_donem_indirim",
                 "indirimler", "odenecek", "sonraki_devir", "iade"]


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
    for yil_kaydi in sorted(yillar, key=lambda y: y["yil"]):
        yil = int(yil_kaydi["yil"])
        beyan = yil_kaydi.get("beyan") or bos_beyan()
        elestiri = yil_kaydi.get("elestiri") or bos_elestiri()
        ay_sayisi = int(yil_kaydi.get("ay_sayisi") or 12)
        for ay in range(min(max(ay_sayisi, 1), 12)):
            elestirili = _donem_hesapla(beyan, elestiri, yil, ay, devreden)
            beyan_ozet = _beyan_ozeti(beyan, yil, ay)
            fark = {alan: _yuvarla(elestirili[alan] - beyan_ozet[alan]) for alan in OZET_ALANLARI}
            donemler.append({
                "yil": yil,
                "ay": ay + 1,
                "ay_adi": AYLAR[ay],
                "beyan": beyan_ozet,
                "elestirili": elestirili,
                "fark": fark,
                "elestiri_var": _elestiri_var(elestiri, ay),
            })
            devreden = elestirili["sonraki_devir"]

    return {
        "donemler": donemler,
        "yil_toplamlari": _yil_toplamlari(donemler),
        "genel_toplam": _toplam(donemler),
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
    onceki = None  # (yil, ay_adi, beyan edilen sonraki devir)
    for yil_kaydi in sorted(yillar, key=lambda y: y["yil"]):
        yil = int(yil_kaydi["yil"])
        beyan = yil_kaydi.get("beyan") or bos_beyan()
        ay_sayisi = min(max(int(yil_kaydi.get("ay_sayisi") or 12), 1), 12)
        for ay in range(ay_sayisi):
            donem = f"{yil}/{AYLAR[ay]}"
            onceki_devir = _d(beyan, "onceki_donem_devreden", ay)
            sonraki_devir = _d(beyan, "sonraki_donem_devreden", ay)

            if onceki is not None and abs(onceki[2] - onceki_devir) > 0.01:
                bulgular.append({
                    "donem": donem,
                    "tur": "devir_zinciri",
                    "mesaj": (f"{onceki[0]}/{onceki[1]} dönemi sonraki döneme devreden KDV "
                              f"{onceki[2]:,.2f} TL iken, {donem} dönemi önceki dönemden "
                              f"devreden KDV {onceki_devir:,.2f} TL beyan edilmiş. "
                              f"Fark: {onceki_devir - onceki[2]:,.2f} TL."),
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

            onceki = (yil, AYLAR[ay], sonraki_devir)
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
    akim = ["matrah", "hesaplanan", "bu_donem_indirim", "indirimler", "odenecek", "iade"]
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
