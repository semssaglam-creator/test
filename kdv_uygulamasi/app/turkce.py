"""Belge metinlerinde ek uyumu ve tutar bicimi.

Uretilen tutanak ve raporlarda kurum adlari degiskendir; "Mersin Vergi Dairesi
Müdürlüğü'nün" ile "Vergi Dairesi Başkanlığı'nın" ayni cumlede farkli ek alir.
Eki sabit yazmak metni bozdugundan son unluye gore secilir.
"""

KALIN_UNLULER = "aıou"
INCE_UNLULER = "eiöü"
UNLULER = KALIN_UNLULER + INCE_UNLULER

# Son unluye gore ilgi hali (tamlayan) eki
_ILGI = {"a": "ın", "ı": "ın", "e": "in", "i": "in",
         "o": "un", "u": "un", "ö": "ün", "ü": "ün"}

# Bulunma hali (-da/-de) bilerek yok. Iyelik ekiyle biten kurum adlarinda
# arada kaynastirma "n" gerekir ("Müdürlüğü'nde"), sade bir adda gerekmez
# ("Bursa'da"); ikisini kelimeye bakarak ayirt etmek guvenilir degil. Belge
# metinleri bu ekten kacinacak bicimde kuruldu.


def _son_unlu(kelime):
    for ch in reversed(kelime.lower()):
        if ch in UNLULER:
            return ch
    return "e"          # unlu yoksa (kisaltma vb.) ince kabul edilir


def _son_harf(kelime):
    for ch in reversed(kelime):
        if not ch.isspace():
            return ch
    return ""


def ilgi(ozel_ad):
    """Ozel ada kesme isaretiyle ilgi hali eki ekler.

    "Mersin Vergi Dairesi Müdürlüğü" -> "Mersin Vergi Dairesi Müdürlüğü'nün"
    "Vergi Dairesi Başkanlığı"       -> "Vergi Dairesi Başkanlığı'nın"
    """
    ad = (ozel_ad or "").strip()
    if not ad:
        return ad
    ek = _ILGI[_son_unlu(ad)]
    if _son_harf(ad).lower() in UNLULER:
        ek = "n" + ek        # unluyle bitiyorsa kaynastirma harfi
    return "%s'%s" % (ad, ek)


def ilgi_kurum(kurum_adi):
    """Kurum adina kesme isareti kullanmadan ilgi hali eki ekler.

    Yazim kurallarina gore kurum ve kurulus adlarina gelen ekler kesme
    isaretiyle ayrilmaz: "Liman Vergi Dairesi Müdürlüğü" -> "Liman Vergi
    Dairesi Müdürlüğünün".
    """
    ad = (kurum_adi or "").strip()
    if not ad or ad.startswith("["):     # yer tutucu ek almaz
        return ad
    ek = _ILGI[_son_unlu(ad)]
    if _son_harf(ad).lower() in UNLULER:
        ek = "n" + ek        # unluyle bitiyorsa kaynastirma harfi
    return ad + ek


def tl(deger):
    """Tutari Turkce bicimde yazar: binlik nokta, ondalik virgul."""
    try:
        deger = float(deger or 0.0)
    except (TypeError, ValueError):
        deger = 0.0
    return "{:,.2f}".format(deger).replace(",", "#").replace(".", ",").replace("#", ".")


def liste(ogeler, baglac="ve"):
    """['A', 'B', 'C'] -> 'A, B ve C'"""
    ogeler = [str(o) for o in ogeler if str(o or "").strip()]
    if not ogeler:
        return ""
    if len(ogeler) == 1:
        return ogeler[0]
    return "%s %s %s" % (", ".join(ogeler[:-1]), baglac, ogeler[-1])


# ------------------------------------------------------------- ad / unvan
# Turkce'de i/I cifti asimetriktir: "i" -> "İ", "I" -> "ı". Python'un
# upper/lower'i bunu bilmez ve "İstanbul" -> "ISTANBUL" yerine "iSTANBUL"
# gibi hatalar cikar. Bu yuzden cevrim once bu harfler icin yapilir.
_BUYUK = {"i": "İ", "ı": "I"}
_KUCUK = {"I": "ı", "İ": "i"}

# Unvanlarda kucuk kalan baglaclar ve buyuk kalan kisaltmalar. Kisaltmalar
# noktali yazildigindan cogu kendiliginden taninir; noktasiz yazilanlar icin
# liste tutulur.
_UNVAN_KUCUK = {"ve", "ile"}
_UNVAN_BUYUK = {"AŞ", "A.Ş.", "LTD", "ŞTİ", "TİC", "SAN", "VD", "TAŞ", "KOM",
                "İTH", "İHR", "PAZ", "İNŞ", "NAK", "OTO", "TR"}


def buyuk(metin):
    """Turkce kurallariyla buyuk harfe cevirir."""
    return "".join(_BUYUK.get(ch, ch).upper() for ch in str(metin or ""))


def kucuk(metin):
    """Turkce kurallariyla kucuk harfe cevirir."""
    return "".join(_KUCUK.get(ch, ch).lower() for ch in str(metin or ""))


def _bas_harf(kelime):
    """"AHMET" -> "Ahmet"; noktali kisaltmalar oldugu gibi kalir."""
    if not kelime:
        return kelime
    return buyuk(kelime[0]) + kucuk(kelime[1:])


def unvan(metin):
    """Sirket unvanini yazim kurallarina getirir: her kelimenin ilk harfi buyuk.

    Kisaltmalar buyuk kalir ("LTD. ŞTİ.", "A.Ş."), baglaclar kucuk yazilir
    ("ve"). Bos deger oldugu gibi doner; yer tutucularin ("[unvan girilmedi]")
    bozulmamasi icin koseli parantezli metne dokunulmaz.
    """
    ham = str(metin or "").strip()
    if not ham or ham.startswith("["):
        return ham
    kelimeler = []
    for kelime in ham.split():
        cikarilmis = kelime.replace(".", "")
        if kucuk(kelime) in _UNVAN_KUCUK:
            kelimeler.append(kucuk(kelime))
        elif "." in kelime or buyuk(cikarilmis) in _UNVAN_BUYUK:
            kelimeler.append(buyuk(kelime))
        else:
            kelimeler.append(_bas_harf(kelime))
    return " ".join(kelimeler)


def kisi_adi(metin):
    """Kisi adini yazim kurallarina getirir: ad(lar) ilk harf buyuk, soyad BUYUK.

    Son kelime soyad sayilir; ondan oncekiler addir. Iki soyadli yazimlar
    (ornegin evlilik soyadi) tek kelime gibi ele alinir - hangi kelimenin
    soyad oldugunu metinden kestirmek guvenilir degil, yanlis tahmin de resmi
    belgeye yanlis yazim koyar. Yer tutucular ("[ad soyad]") korunur.
    """
    ham = str(metin or "").strip()
    if not ham or ham.startswith("["):
        return ham
    kelimeler = ham.split()
    if len(kelimeler) == 1:
        return _bas_harf(kelimeler[0])
    return "%s %s" % (" ".join(_bas_harf(k) for k in kelimeler[:-1]),
                      buyuk(kelimeler[-1]))


def _adres_parcasi(parca):
    """Adresteki tek bir sozcugu bicimler.

    Kisa ve bastan sona buyuk yazilmis parcalar kisaltma sayilip oldugu gibi
    kalir ("VD", "OSB", "B"); otekilerin ilk harfi buyuk yazilir.
    """
    if not parca:
        return parca
    harfler = "".join(ch for ch in parca if ch.isalpha())
    if (harfler == parca and len(parca) <= 3
            and parca == buyuk(parca)) or buyuk(parca) in _UNVAN_BUYUK:
        return parca
    return _bas_harf(parca)


def adres(metin):
    """Adresi yazim kurallarina getirir: her kelimenin ilk harfi buyuk.

    Sistem dokumlerinden gelen adresler bastan sona buyuk harf oluyor. Kelime
    ayraci olarak bosluk yaninda "/" ve "-" de sayilir ("SEYHAN/ADANA" ->
    "Seyhan/Adana"). Rakam tasiyan parcalar bozulmaz ("NO:5" -> "No:5").
    Koseli parantezli yer tutuculara dokunulmaz.
    """
    ham = str(metin or "").strip()
    if not ham or ham.startswith("["):
        return ham
    kelimeler = []
    for kelime in ham.split():
        parcalar, tampon, ayraclar = [], "", "/-"
        for ch in kelime:
            if ch in ayraclar:
                parcalar.append(_adres_parcasi(tampon))
                parcalar.append(ch)
                tampon = ""
            else:
                tampon += ch
        parcalar.append(_adres_parcasi(tampon))
        kelimeler.append("".join(parcalar))
    return " ".join(kelimeler)
