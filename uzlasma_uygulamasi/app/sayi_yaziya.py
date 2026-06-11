"""TL tutarlarini Turkce yaziya ceviren yardimci modul."""

BIRLER = ["", "Bir", "Iki", "Uc", "Dort", "Bes", "Alti", "Yedi", "Sekiz", "Dokuz"]
ONLAR = ["", "On", "Yirmi", "Otuz", "Kirk", "Elli", "Altmis", "Yetmis", "Seksen", "Doksan"]
BASAMAKLAR = ["", "Bin", "Milyon", "Milyar", "Trilyon"]

# Turkce karakterli versiyonlar (gorunum icin)
BIRLER_TR = ["", "Bir", "İki", "Üç", "Dört", "Beş", "Altı", "Yedi", "Sekiz", "Dokuz"]
ONLAR_TR = ["", "On", "Yirmi", "Otuz", "Kırk", "Elli", "Altmış", "Yetmiş", "Seksen", "Doksan"]


def _uc_basamak_yaziya(sayi, birler, onlar):
    yuzler = sayi // 100
    kalan = sayi % 100
    onlar_basamagi = kalan // 10
    birler_basamagi = kalan % 10

    parca = ""
    if yuzler > 0:
        if yuzler > 1:
            parca += birler[yuzler]
        parca += "Yüz"
    parca += onlar[onlar_basamagi]
    parca += birler[birler_basamagi]
    return parca


def sayi_yaziya(sayi, birler=None, onlar=None):
    """Tam sayiyi (0 dahil) Turkce yaziya cevirir, kelimeler birlesik dondurulur."""
    birler = birler or BIRLER_TR
    onlar = onlar or ONLAR_TR

    sayi = int(sayi)
    if sayi == 0:
        return "Sıfır"

    gruplar = []
    n = sayi
    while n > 0:
        gruplar.append(n % 1000)
        n //= 1000

    parcalar = []
    for i in range(len(gruplar) - 1, -1, -1):
        grup = gruplar[i]
        if grup == 0:
            continue
        grup_yazi = _uc_basamak_yaziya(grup, birler, onlar)
        if i == 1 and grup == 1:
            # "BirBin" yerine "Bin"
            grup_yazi = ""
        parcalar.append(grup_yazi + BASAMAKLAR[i])

    return "".join(parcalar)


def tutar_yaziya(tutar):
    """Ondalikli TL tutarini 'Lira [+ Kuruş]' seklinde Turkce yaziya cevirir."""
    tutar = round(float(tutar) + 1e-9, 2)
    lira = int(tutar)
    kurus = int(round((tutar - lira) * 100))
    if kurus == 100:
        lira += 1
        kurus = 0

    metin = sayi_yaziya(lira)
    if kurus > 0:
        metin += " " + sayi_yaziya(kurus) + " Kuruş"
    return metin


def tl_formatla(tutar):
    """1234.5 -> '1.234,50' biciminde gosterim."""
    return f"{float(tutar):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
