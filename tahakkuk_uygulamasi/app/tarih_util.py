"""Tarih ve vergi donemi bicim donusumleri.

Veritabaninda yukleme zamani ISO 'YYYY-AA-GG SS:DD' formatinda saklanir;
arayuzde Turkce 'GG.AA.YYYY SS:DD' gosterilir.

Vergi donemi alani Excel'de 12 haneli 'AAYYYYAAYYYY' bicimindedir; ilk alti
hane baslangic (ay+yil), son alti hane bitis (ay+yil) donemini verir.
Ornek: '052026052026' -> Mayis 2026 (tek ay),
       '012026122026' -> 2026 (Yillik, Ocak-Aralik).
"""
from datetime import datetime

AYLAR = [
    "", "Ocak", "Şubat", "Mart", "Nisan", "Mayıs", "Haziran",
    "Temmuz", "Ağustos", "Eylül", "Ekim", "Kasım", "Aralık",
]


def simdi_tr():
    return datetime.now().strftime("%d.%m.%Y %H:%M")


def simdi_iso():
    return datetime.now().strftime("%Y-%m-%d %H:%M")


def iso_to_tr(iso_str):
    iso_str = (iso_str or "").strip()
    if not iso_str:
        return ""
    try:
        return datetime.strptime(iso_str, "%Y-%m-%d %H:%M").strftime("%d.%m.%Y %H:%M")
    except ValueError:
        return iso_str


def _ay_yil_coz(parca):
    """6 haneli 'AAYYYY' -> (ay, yil) veya None."""
    if not parca or len(parca) != 6 or not parca.isdigit():
        return None
    ay = int(parca[:2])
    yil = int(parca[2:])
    if not (1 <= ay <= 12):
        return None
    return ay, yil


def donem_metni(donem):
    """'AAYYYYAAYYYY' -> okunabilir Turkce metin.

    Cozulemezse ham deger oldugu gibi dondurulur.
    """
    s = str(donem or "").strip()
    if len(s) != 12 or not s.isdigit():
        return s
    bas = _ay_yil_coz(s[:6])
    bit = _ay_yil_coz(s[6:])
    if not bas or not bit:
        return s
    bas_ay, bas_yil = bas
    bit_ay, bit_yil = bit
    # Tek ay donemi (baslangic = bitis)
    if bas_ay == bit_ay and bas_yil == bit_yil:
        return f"{AYLAR[bas_ay]} {bas_yil}"
    # Tam yil donemi (Ocak-Aralik, ayni yil)
    if bas_ay == 1 and bit_ay == 12 and bas_yil == bit_yil:
        return f"{bas_yil} (Yıllık)"
    # Diger araliklar
    if bas_yil == bit_yil:
        return f"{AYLAR[bas_ay]}-{AYLAR[bit_ay]} {bas_yil}"
    return f"{AYLAR[bas_ay]} {bas_yil} - {AYLAR[bit_ay]} {bit_yil}"
