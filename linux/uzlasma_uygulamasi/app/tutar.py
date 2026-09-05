"""Uzlasilan tutarin hesabi ve yuvarlama kurali.

Tutanaga yazilan uzlasilan tutar yuvarlak olur: kurus hanesi 00'a iner ve
tutar 10 TL'nin katina cikarilir. Kural tek yerde tanimlidir; hem tutanak
olusturulurken (web_server) hem de tutanagin sonucu sonradan degistirilirken
(db) buradan cagrilir, ekrandaki onizleme de ayni sonucu gosterir.
"""
from decimal import Decimal, ROUND_CEILING, ROUND_HALF_UP

# Uzlasilan tutarin katina yuvarlanacagi adim (TL).
YUVARLAMA_ADIMI = 10


def uzlasilan_yuvarla(tutar):
    """Tutari 10 TL'nin bir ust katina yuvarlar; kurus 00 olur.

    Daima yukari yuvarlanir (1.234,56 -> 1.240,00); asagi yuvarlamak tahsil
    edilecek tutari eksiltirdi. Zaten tam kat olan tutar degismez
    (1.230,00 -> 1.230,00).

    Once kurusa yuvarlanir: `miktar * (1 - oran / 100)` carpimi ikilik kayan
    noktada 1230.0000000000002 gibi bir artik birakabiliyor ve bu artik, tam
    kat olan bir tutari gereksiz yere bir ust kata tasirdi.
    """
    if not tutar or tutar <= 0:
        return 0.0
    kurusa = Decimal(str(tutar)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    adim = Decimal(YUVARLAMA_ADIMI)
    return float((kurusa / adim).to_integral_value(rounding=ROUND_CEILING) * adim)


def uzlasilan_tutar(miktar, indirim_orani):
    """Indirim oranindan sonra kalan (uzlasilan) tutar, yuvarlanmis halde."""
    return uzlasilan_yuvarla((miktar or 0) * (1 - (indirim_orani or 0) / 100))
