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
