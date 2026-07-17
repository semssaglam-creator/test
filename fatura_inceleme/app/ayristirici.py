"""Fatura metnini alanlara ayristirir.

GIB e-Fatura / e-Arsiv PDF'lerinin metin duzenine gore hazirlanmistir;
OCR ciktilarinda da ayni etiketler arandigindan taranmis faturalarda da
calisir (dogruluk OCR kalitesine baglidir). Ayristirilamayan ya da
tutarlari tutmayan faturalar 'kontrol' durumuyla isaretlenir ve arayuzden
elle duzeltilebilir.
"""
import re

# ---------------------------------------------------------------- sayi/tarih
_TR_AYLAR = {
    "ocak": 1, "şubat": 2, "subat": 2, "mart": 3, "nisan": 4, "mayıs": 5,
    "mayis": 5, "haziran": 6, "temmuz": 7, "ağustos": 8, "agustos": 8,
    "eylül": 9, "eylul": 9, "ekim": 10, "kasım": 11, "kasim": 11, "aralık": 12,
    "aralik": 12,
}

SAYI_DESENI = r"\d{1,3}(?:[.,]\d{3})*(?:[.,]\d+)?|\d+(?:[.,]\d+)?"


def sayi_coz(metin):
    """'1.234,56' / '1,234.56' / '1234.56' -> float; cozulmezse None."""
    s = str(metin or "").strip().replace(" ", "")
    s = re.sub(r"(?i)(TL|TRY|₺)$", "", s).strip()
    if not s or not re.search(r"\d", s):
        return None
    nokta, virgul = s.rfind("."), s.rfind(",")
    if nokta >= 0 and virgul >= 0:
        # Son gorunen ayirici ondaliktir
        if virgul > nokta:
            s = s.replace(".", "").replace(",", ".")
        else:
            s = s.replace(",", "")
    elif virgul >= 0:
        # Tek virgul: '1,234' gibi binlik olabilir ama TR faturada ondaliktir
        s = s.replace(",", ".")
    elif nokta >= 0:
        # '1.234' binlik mi ondalik mi? Tam 3 hane ve birden fazla nokta -> binlik
        parcalar = s.split(".")
        if len(parcalar) > 2 or (len(parcalar) == 2 and len(parcalar[1]) == 3
                                 and len(parcalar[0]) <= 3):
            s = s.replace(".", "")
    try:
        return float(s)
    except ValueError:
        return None


def tarih_iso(metin):
    """'01-02-2024', '01.02.2024', '2024-02-01', '1 Şubat 2024' -> '2024-02-01'."""
    s = str(metin or "").strip()
    m = re.search(r"\b(\d{4})-(\d{2})-(\d{2})\b", s)
    if m:
        return m.group(0)
    m = re.search(r"\b(\d{1,2})[./-](\d{1,2})[./-](\d{4})\b", s)
    if m:
        g, a, y = int(m.group(1)), int(m.group(2)), int(m.group(3))
        if 1 <= a <= 12 and 1 <= g <= 31:
            return f"{y:04d}-{a:02d}-{g:02d}"
    m = re.search(r"\b(\d{1,2})\s+([A-Za-zÇĞİÖŞÜçğıöşü]+)\s+(\d{4})\b", s)
    if m and m.group(2).lower() in _TR_AYLAR:
        return f"{int(m.group(3)):04d}-{_TR_AYLAR[m.group(2).lower()]:02d}-{int(m.group(1)):02d}"
    return ""


def iso_to_tr(iso):
    if re.match(r"^\d{4}-\d{2}-\d{2}$", iso or ""):
        y, a, g = iso.split("-")
        return f"{g}.{a}.{y}"
    return iso or ""


# ---------------------------------------------------------------- etiketler
def _etiket_ara(metin, etiketler, deger_deseni=r"[^\n]+"):
    """'Etiket ...: deger' satirini bulur, deger kismini dondurur."""
    for etiket in etiketler:
        m = re.search(
            etiket + r"\s*:?\s*(" + deger_deseni + ")", metin,
            re.IGNORECASE)
        if m:
            deger = m.group(1).strip()
            if deger:
                return deger
    return ""


def _kdv_toplami(metin):
    """Farkli oranlardaki 'Hesaplanan KDV(%x)' satirlarini toplar."""
    toplam, bulundu = 0.0, False
    for m in re.finditer(
            r"Hesaplanan\s*KDV\s*\(?%?\s*[\d.,]*\)?[^\n%\d]*(" + SAYI_DESENI + r")",
            metin, re.IGNORECASE):
        deger = sayi_coz(m.group(1))
        if deger is not None:
            toplam += deger
            bulundu = True
    if bulundu:
        return round(toplam, 2)
    return _tutar_ara(metin, [r"KDV\s*Toplam[ıi]?", r"Toplam\s*KDV"])


def _tutar_ara(metin, etiketler):
    for etiket in etiketler:
        m = re.search(
            etiket + r"[^\n%\d]*(" + SAYI_DESENI + r")\s*(?:TL|TRY|₺)?",
            metin, re.IGNORECASE)
        if m:
            deger = sayi_coz(m.group(1))
            if deger is not None:
                return deger
    return None


_VKN_DESEN = re.compile(
    r"(?:VKN|TCKN|V\.K\.N|T\.C\.K\.N|Vergi\s*(?:Kimlik)?\s*No(?:su)?|"
    r"Vergi\s*Numarası|TC\s*Kimlik\s*No)\s*:?\s*(\d{10,11})", re.IGNORECASE)

_ETTN_DESEN = re.compile(
    r"[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}")

# GIB belge no: 3 harf/rakam on ek + yil + 9 haneli sira (orn. GIB2024000000001)
_FATURA_NO_DESEN = re.compile(r"\b[A-Z0-9]{3}(?:20\d{2})\d{9}\b")

_ALICI_AYIRICI = re.compile(r"\bSAYIN\b|\bALICI\b", re.IGNORECASE)


def _unvan_tahmini(blok):
    """Bir metin blogundaki ilk anlamli satiri unvan olarak dondurur."""
    atla = re.compile(
        r"^(e-?\s*(arşiv|arsiv|fatura)|fatura|irsaliye|sayın|sayin|alıcı|alici|"
        r"vergi dairesi|vkn|tckn|mersis|ticaret sicil|tel|fax|faks|e-?posta|"
        r"web|adres|mah\.|cad\.|sok\.|no:|kat:|daire)", re.IGNORECASE)
    for satir in blok.splitlines():
        s = satir.strip(" \t:-")
        if len(s) < 3 or atla.match(s):
            continue
        if re.fullmatch(r"[\d\s./:-]+", s):  # yalniz sayi/tarih satiri
            continue
        return s[:150]
    return ""


# ---------------------------------------------------------------- kalemler
_KALEM_BASLIK = re.compile(
    r"S[ıi]ra\s*No.{0,120}?(?:Mal|Hizmet|Açıklama|Aciklama|Cinsi)", re.IGNORECASE | re.DOTALL)
_KALEM_SON = re.compile(
    r"Mal\s*/?\s*Hizmet\s*Toplam|Toplam\s*İskonto|Toplam\s*Iskonto|"
    r"Hesaplanan\s*KDV|Vergiler\s*Dahil|Ödenecek|Odenecek", re.IGNORECASE)
_SAYI_TOKEN = re.compile(r"^(" + SAYI_DESENI + r")(?:TL|TRY|₺)?$", re.IGNORECASE)
_KDV_TOKEN = re.compile(r"^%\s*(\d{1,2}(?:[.,]\d+)?)$|^(\d{1,2})\s*%$")

_BIRIMLER = {
    "adet", "ad", "kg", "kilogram", "gram", "gr", "ton", "lt", "litre", "l",
    "mt", "metre", "m", "m2", "m3", "cm", "paket", "pk", "koli", "kutu",
    "çuval", "cuval", "torba", "saat", "gün", "gun", "ay", "yıl", "yil",
    "c62", "kgm", "ltr", "mtr", "mtk", "mtq", "niu", "pr", "set", "takım", "takim",
}


def _kalem_satiri_coz(satir):
    """Tek metin satirindan kalem alanlarini tahmin eder; olmazsa None."""
    tokenlar = satir.split()
    if len(tokenlar) < 3:
        return None

    sira = None
    if re.fullmatch(r"\d{1,4}", tokenlar[0]):
        sira = int(tokenlar[0])
        tokenlar = tokenlar[1:]

    # Tokenlari sinifla: sayi, kdv orani, birim, metin
    sayilar, kdv_orani, birim = [], None, ""
    ilk_sayi_indeksi = None
    for i, t in enumerate(tokenlar):
        m = _KDV_TOKEN.match(t)
        if m:
            kdv_orani = sayi_coz(m.group(1) or m.group(2))
            continue
        m = _SAYI_TOKEN.match(t)
        if m:
            deger = sayi_coz(m.group(1))
            if deger is not None:
                sayilar.append(deger)
                if ilk_sayi_indeksi is None:
                    ilk_sayi_indeksi = i
                continue
        if t.upper() in ("TL", "TRY", "₺"):
            continue
        if sayilar and not birim and t.lower().strip(".") in _BIRIMLER:
            birim = t
            continue

    if len(sayilar) < 2 or ilk_sayi_indeksi is None or ilk_sayi_indeksi == 0:
        return None  # aciklama + en az miktar/tutar olmali

    aciklama = " ".join(tokenlar[:ilk_sayi_indeksi]).strip(" -:")
    if len(aciklama) < 2:
        return None

    kalem = {
        "sira": sira, "mal_hizmet": aciklama[:300], "miktar": sayilar[0],
        "birim": birim, "birim_fiyat": None, "kdv_orani": kdv_orani,
        "kdv_tutari": None, "tutar": sayilar[-1],
    }
    if len(sayilar) >= 3:
        # Sutun sirasi sablondan sablona degisir; tutar ve KDV tutarini
        # aritmetik tutarlilikla sec (tutar ~= miktar x birim fiyat,
        # KDV ~= tutar x oran). Tutarli aday yoksa son sayi tutar sayilir.
        kalem["birim_fiyat"] = sayilar[1]
        kalanlar = sayilar[2:]
        beklenen = sayilar[0] * sayilar[1]
        en_yakin = min(kalanlar, key=lambda v: abs(v - beklenen))
        if abs(en_yakin - beklenen) <= max(0.05, beklenen * 0.02):
            kalem["tutar"] = en_yakin
        kdv_adaylari = list(kalanlar)
        if kalem["tutar"] in kdv_adaylari:
            kdv_adaylari.remove(kalem["tutar"])
        if kdv_orani and kdv_adaylari:
            beklenen_kdv = kalem["tutar"] * kdv_orani / 100
            en_yakin = min(kdv_adaylari, key=lambda v: abs(v - beklenen_kdv))
            if abs(en_yakin - beklenen_kdv) <= max(0.05, beklenen_kdv * 0.05):
                kalem["kdv_tutari"] = en_yakin
        elif not kdv_orani and len(sayilar) >= 4:
            # miktar, birim fiyat, (iskonto,) kdv tutari, tutar dizilimi yaygindir
            kalem["kdv_tutari"] = sayilar[-2]
    return kalem


def _kalem_akisi_coz(bolge):
    """Satir bazli ayristirma bulamayinca: tum bolgeyi tek akis olarak ele
    alip 1, 2, 3... sira numaralarindan kalemlere boler.

    PDF metin cikarimi tablo hucrelerini ayri satirlara dagitabildiginden
    (ornek: '2.232,14' ile 'TL' farkli satirlara duser) satir bazli yontem
    bu sablonlarda calismaz; akis modu bu durumu kurtarir.
    """
    tokenlar = bolge.split()
    segmentler, aktif = [], None
    beklenen = 1
    for i, t in enumerate(tokenlar):
        sonraki = tokenlar[i + 1] if i + 1 < len(tokenlar) else ""
        sira_gibi = (
            t == str(beklenen) and sonraki
            and not _SAYI_TOKEN.match(sonraki) and not _KDV_TOKEN.match(sonraki)
            and sonraki.upper() not in ("TL", "TRY", "₺")
            and sonraki.lower().strip(".") not in _BIRIMLER)
        if sira_gibi:
            if aktif is not None:
                segmentler.append(aktif)
            aktif = [t]
            beklenen += 1
        elif aktif is not None:
            aktif.append(t)
    if aktif is not None:
        segmentler.append(aktif)

    kalemler = []
    for seg in segmentler:
        kalem = _kalem_satiri_coz(" ".join(seg))
        if kalem:
            kalemler.append(kalem)
    return kalemler


def _kalemleri_ayristir(metin):
    baslik = _KALEM_BASLIK.search(metin)
    baslangic = baslik.end() if baslik else 0
    son = _KALEM_SON.search(metin, baslangic)
    bolge = metin[baslangic:son.start()] if son else metin[baslangic:]

    kalemler = []
    for satir in bolge.splitlines():
        satir = satir.strip()
        if not satir or _KALEM_SON.search(satir):
            continue
        kalem = _kalem_satiri_coz(satir)
        if kalem:
            kalemler.append(kalem)
    if not kalemler:
        # Hucreler ayri satirlara dagilmis olabilir; akis modunu dene
        kalemler = _kalem_akisi_coz(bolge)
    # Sira numarasi hic yoksa otomatik numarala
    if kalemler and all(k["sira"] is None for k in kalemler):
        for i, k in enumerate(kalemler, 1):
            k["sira"] = i
    return kalemler


# ---------------------------------------------------------------- coklu fatura
def _fatura_kimligi(sayfa_metni):
    """Sayfadaki fatura kimligini (ETTN, yoksa fatura no) dondurur."""
    m = _ETTN_DESEN.search(sayfa_metni)
    if m:
        return m.group(0).lower()
    no = _etiket_ara(sayfa_metni, [r"Fatura\s*No(?:su)?", r"Belge\s*No"],
                     r"[A-Z0-9]{9,20}")
    if no:
        return no
    m = _FATURA_NO_DESEN.search(sayfa_metni)
    return m.group(0) if m else ""


def faturalari_bol(sayfalar):
    """Sayfa metinlerini fatura bolumlerine ayirir.

    Bir PDF birden fazla fatura icerebilir (birlestirilmis e-Arsiv ciktisi,
    seri taranmis fatura destesi). Her sayfanin fatura kimligine (ETTN /
    fatura no) bakilir; kimlik degistiginde yeni bolum baslar. Kimliksiz
    sayfalar (kalem devami vb.) aktif bolume eklenir. Ayni sayfada iki
    fatura varsa ayrilamaz; tek bolum olarak doner ve ayristirici uyari
    uretir.
    """
    bolumler = []
    aktif, aktif_kimlik = [], ""
    for sayfa in sayfalar:
        kimlik = _fatura_kimligi(sayfa)
        if aktif and kimlik and aktif_kimlik and kimlik != aktif_kimlik:
            bolumler.append("\n".join(aktif))
            aktif, aktif_kimlik = [sayfa], kimlik
        else:
            aktif.append(sayfa)
            aktif_kimlik = aktif_kimlik or kimlik
    if aktif:
        bolumler.append("\n".join(aktif))
    return bolumler or [""]


# ---------------------------------------------------------------- ana giris
def fatura_ayristir(metin):
    """Fatura metnini (baslik, kalemler, uyarilar) uclusune ayristirir."""
    metin = (metin or "").replace("\r", "")
    uyarilar = []

    fatura_no = _etiket_ara(metin, [r"Fatura\s*No(?:su)?", r"Belge\s*No"],
                            r"[A-Z0-9]{9,20}")
    if not fatura_no:
        m = _FATURA_NO_DESEN.search(metin)
        fatura_no = m.group(0) if m else ""

    tarih = tarih_iso(_etiket_ara(
        metin, [r"Fatura\s*Tarihi", r"Düzenle(?:n)?me\s*Tarihi", r"Belge\s*Tarihi"]))
    if not tarih:
        # Bazi sablonlarda etiket yalnizca 'Tarih:' seklindedir. Satir basi
        # araniyor ki 'Son Ödeme Tarihi' gibi alanlarla karismasin.
        m = re.search(r"^[ \t]*Tarih[ \t]*:?[ \t]*([^\n]+)", metin, re.MULTILINE)
        if m:
            tarih = tarih_iso(m.group(1))
    if not tarih:
        tarih = tarih_iso(metin)  # metindeki ilk tarih
        if tarih:
            uyarilar.append("Fatura tarihi etiketi bulunamadi; metindeki ilk tarih alindi.")

    m = _ETTN_DESEN.search(metin)
    ettn = m.group(0).lower() if m else ""

    fatura_tipi = _etiket_ara(metin, [r"Fatura\s*Tipi"], r"[A-ZÇĞİÖŞÜa-zçğıöşü]+")

    # Satici / alici bloklari: 'SAYIN' oncesi satici, sonrasi alicidir
    ayirici = _ALICI_AYIRICI.search(metin)
    if ayirici:
        satici_blok = metin[:ayirici.start()]
        alici_son = re.search(r"Fatura\s*No|ETTN|Özelleştirme|Ozellestirme|Senaryo",
                              metin[ayirici.end():], re.IGNORECASE)
        alici_blok = metin[ayirici.end():ayirici.end() + alici_son.start()] \
            if alici_son else metin[ayirici.end():ayirici.end() + 600]
    else:
        satici_blok, alici_blok = metin[:600], ""
        uyarilar.append("Alici bolumu (SAYIN) bulunamadi; taraf bilgilerini kontrol edin.")

    satici_vknler = _VKN_DESEN.findall(satici_blok)
    alici_vknler = _VKN_DESEN.findall(alici_blok)
    satici_vkn = satici_vknler[0] if satici_vknler else ""
    alici_vkn = alici_vknler[0] if alici_vknler else ""
    if not satici_vkn and not alici_vkn:
        tum = _VKN_DESEN.findall(metin)
        if len(tum) >= 2:
            satici_vkn, alici_vkn = tum[0], tum[1]
        elif len(tum) == 1:
            satici_vkn = tum[0]

    satici_unvan = _unvan_tahmini(satici_blok)
    alici_unvan = _unvan_tahmini(alici_blok)

    baslik = {
        "fatura_no": fatura_no, "fatura_tarihi": tarih, "ettn": ettn,
        "fatura_tipi": fatura_tipi.upper() if fatura_tipi else "",
        "satici_unvan": satici_unvan, "satici_vkn": satici_vkn,
        "alici_unvan": alici_unvan, "alici_vkn": alici_vkn,
        "para_birimi": "TL",
        "mal_hizmet_toplam": _tutar_ara(metin, [
            r"Mal\s*/?\s*Hizmet\s*Toplam\s*Tutar[ıi]", r"Mal\s*Hizmet\s*Toplam"]),
        "toplam_iskonto": _tutar_ara(metin, [
            r"Toplam\s*[İIi]skonto"]),
        "kdv_toplam": _kdv_toplami(metin),
        "vergiler_dahil_toplam": _tutar_ara(metin, [
            r"Vergiler\s*Dahil\s*Toplam\s*Tutar", r"Vergiler\s*Dahil\s*Toplam"]),
        "odenecek_tutar": _tutar_ara(metin, [
            r"Ödenecek\s*Tutar", r"Odenecek\s*Tutar"]),
    }

    kalemler = _kalemleri_ayristir(metin)

    # ---------------- dogrulama / uyari uretimi
    if not fatura_no:
        uyarilar.append("Fatura numarasi bulunamadi.")
    if not tarih:
        uyarilar.append("Fatura tarihi bulunamadi.")
    if not satici_vkn and not satici_unvan:
        uyarilar.append("Satici bilgisi bulunamadi.")
    if baslik["odenecek_tutar"] is None and baslik["vergiler_dahil_toplam"] is None:
        uyarilar.append("Fatura toplam tutari bulunamadi.")
    if not kalemler:
        uyarilar.append("Mal/hizmet kalemleri ayristirilamadi.")
    elif baslik["mal_hizmet_toplam"] is not None:
        kalem_toplami = sum(k["tutar"] or 0 for k in kalemler)
        if abs(kalem_toplami - baslik["mal_hizmet_toplam"]) > 0.05:
            uyarilar.append(
                f"Kalem toplami ({kalem_toplami:.2f}) ile Mal/Hizmet toplami "
                f"({baslik['mal_hizmet_toplam']:.2f}) uyusmuyor; kalemleri kontrol edin.")

    return baslik, kalemler, uyarilar
