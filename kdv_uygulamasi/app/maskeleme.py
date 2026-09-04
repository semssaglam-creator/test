"""Beyanname PDF'inin metin katmanini, kimlik bilgileri maskelenmis olarak doker.

Yeni bir beyanname bicimi cikinca ayristiriciyi uyarlamak icin PDF'in metin
katmani ve parcalarin sayfadaki konumu gerekir; belgenin kendisi gerekmez.
Bu modul dokumu uretirken mukellef bilgilerini maskeler, boylece bicim
uzerinde calisirken belgenin paylasilmasi gerekmez.

Not: PDF'te yaziyi ustunden boyamak (highlight) metni SILMEZ; boyanan metin
katmanda durur ve okunur. Maskeleme metnin kendisi uzerinde yapilir.

Uc katman birbirinin acigini kapatir:
  1. Desen      - VKN/TCKN, e-posta, telefon, IBAN her yerde maskelenir.
  2. Kimlik bandi - "Mukellef Bilgileri" gibi bir baslikla baslayip ilk veri
     bolumunde biten alanda, etiket olmayan her deger maskelenir.
  3. Unvan sezgisi - A.S./LTD/STI/SANAYI gibi belirtiler tasiyan parcalar
     bandin disinda da maskelenir. Bant katmani koordinata dayanir; koordinat
     bozuk gelirse bu katman yine de unvani yakalar.

Son emniyet kullanicidir: `gozden_gecirilecekler` maskelenmemis serbest
metinleri kisa bir liste halinde verir, kullanici kalan bir adi gorup
`ek_gizle` ile ekleyebilir.
"""
import re

from .pdf_beyanname import normalize, tutar_coz, _parcalar

MASKE = "[MASKELI]"

# Kimlik bilgilerinin bulundugu bloklarin basliklari
KIMLIK_BOLUMLERI = (
    "MUKELLEFBILGILERI",
    "BEYANNAMENINHANGISIFATLAVERILDIGIBILGILERIMUKELLEF",
    "BEYANNAMENINHANGISIFATLAVERILDIGIBILGILERI",
    "BEYANNAMEYIDUZENLEYENBILGILERI",
    "BEYANNAMEYIONAYLAYANBILGILERI",
)

# Kimlik bloklarinin bittigi yer: buradan sonrasi tutar/veri bolumleridir
VERI_BOLUMLERI = (
    "MATRAH", "MATRAHVEVERGIBILDIRIMI", "MATRAHDETAYI", "INDIRIMLER",
    "INDIRIMLERDETAYI", "SONUCHESAPLARI", "DIGERBILGILER", "TEVKIFAT",
    "IHRACKAYDIYLATESLIMLER", "INDIRIMNEDENLERI",
)

# Kimlik bloklarindaki ETIKETLER korunur; yalnizca degerleri maskelenir
KIMLIK_ETIKETLERI = (
    "TCKIMLIKNO", "VERGIKIMLIKNO", "ADISOYADIUNVANI", "EPOSTAADRESI",
    "TELEFONNO", "SUBENO", "VERGIDAIRESI", "VERGIDAIRESIMUDURLUGU",
    "YIL", "AY", "DONEMTIPI", "ONAYZAMANI", "SOYADI", "ADI", "UNVANI",
    "TICARETSICILNO", "IRTIBATTELNO",
)

# Bicimlerinden taninan kisisel veriler; belgenin her yerinde maskelenir
DESENLER = (
    re.compile(r"\b\d{10,11}\b"),                          # VKN / TCKN
    re.compile(r"[\w.+-]+@[\w-]+\.[\w.]+"),                # e-posta
    re.compile(r"(?:\+90|0)[\s()-]*\d{3}[\s()-]*\d{3}"     # telefon
               r"[\s()-]*\d{2}[\s()-]*\d{2}"),
    re.compile(r"\bTR\d{2}[\dA-Z ]{16,30}\b"),             # IBAN
)

# Kimlik bandinda gecse de kisisel olmayan, ayristiricinin donemi tanimasi
# icin GEREKEN degerler. Maskelenirse dokum ise yaramaz hale gelir.
AY_ADLARI = ("OCAK", "SUBAT", "MART", "NISAN", "MAYIS", "HAZIRAN", "TEMMUZ",
             "AGUSTOS", "EYLUL", "EKIM", "KASIM", "ARALIK")
DONEM_TIPLERI = ("AYLIK", "UCAYLIK", "YILLIK")
YIL_DESENI = re.compile(r"^(?:19|20)\d{2}$")

# Kurum/kisi adi belirtileri (koordinattan bagimsiz katman)
UNVAN_BELIRTILERI = (
    "AS", "ANONIMSIRKETI", "LTD", "LIMITED", "STI", "SIRKETI", "SANAYI",
    "TICARET", "TIC", "SAN", "KOLLEKTIF", "KOMANDIT", "HOLDING", "ISLETMESI",
)


def _tutar_mi(metin):
    return tutar_coz(metin) is not None


def guvenli_deger(metin):
    """Kimlik bandinda olsa bile maskelenmemesi gereken deger mi.

    Donem (yil / ay / donem tipi) ve vergi dairesi kisiye ozel bilgi degil;
    ayristirici beyannamenin hangi doneme ait oldugunu bunlardan anlar.
    """
    a = normalize(metin)
    if not a:
        return True
    if a in AY_ADLARI or a in DONEM_TIPLERI:
        return True
    if YIL_DESENI.match((metin or "").strip()):
        return True
    return "VERGIDAIRESI" in a


def unvana_benziyor(metin):
    """Parca bir kurum unvani gibi mi duruyor.

    Kesin bir olcut degil; amac koordinat katmani calismadiginda unvanin
    maskelenmeden gecmesini onlemek. Fazladan maskelemek, eksik maskelemekten
    iyidir - eksik maskelenen bilgi geri alinamaz.
    """
    if not normalize(metin) or _tutar_mi(metin):
        return False
    parcalar = [normalize(p) for p in (metin or "").replace(".", " ").split()]
    return any(p in UNVAN_BELIRTILERI for p in parcalar if p)


def desenle_maskele(metin):
    """Bicimlerinden taninan kisisel verileri metnin icinde maskeler."""
    for desen in DESENLER:
        metin = desen.sub(MASKE, metin)
    return metin


def kimlik_bandi_mi(parcalar):
    """Her parca icin, kimlik blogunun icinde olup olmadigini isaretler."""
    icinde = [False] * len(parcalar)
    # Okuma sirasi: sayfa, yukaridan asagi (y azalan), soldan saga
    sirali = sorted(range(len(parcalar)),
                    key=lambda i: (parcalar[i][0], -parcalar[i][2], parcalar[i][1]))
    bandda = False
    for i in sirali:
        anahtar = normalize(parcalar[i][3])
        if anahtar in KIMLIK_BOLUMLERI:
            bandda = True
            continue
        if anahtar in VERI_BOLUMLERI:
            bandda = False
        icinde[i] = bandda
    return icinde


def maskele(parcalar, ek_gizle=(), tutarsiz=False):
    """Parcalari maskeler. Doner: (yeni_parcalar, maskelenen_sayisi)"""
    bandda = kimlik_bandi_mi(parcalar)
    gizlenecek = {normalize(e) for e in ek_gizle if (e or "").strip()}
    maskelenmis_degerler = set()

    ara = []
    for i, (sayfa, x, y, metin) in enumerate(parcalar):
        anahtar = normalize(metin)
        etiket = any(anahtar.startswith(e) for e in KIMLIK_ETIKETLERI)
        if ((bandda[i] or unvana_benziyor(metin)) and not etiket
                and not _tutar_mi(metin) and not guvenli_deger(metin)):
            maskelenmis_degerler.add(anahtar)
            ara.append((sayfa, x, y, MASKE))
        else:
            ara.append((sayfa, x, y, metin))

    sonuc, sayac = [], 0
    for sayfa, x, y, metin in ara:
        if metin == MASKE:
            sayac += 1
            sonuc.append((sayfa, x, y, metin))
            continue
        anahtar = normalize(metin)
        # Bandda maskelenen bir deger belgenin baska yerinde de geciyorsa
        if anahtar and (anahtar in maskelenmis_degerler or anahtar in gizlenecek):
            sayac += 1
            sonuc.append((sayfa, x, y, MASKE))
            continue
        yeni = desenle_maskele(metin)
        if tutarsiz and _tutar_mi(yeni):
            yeni = "[TUTAR]"
        if yeni != metin:
            sayac += 1
        sonuc.append((sayfa, x, y, yeni))
    return sonuc, sayac


def gozden_gecirilecekler(maskeli):
    """Maskelenmemis serbest metinlerin benzersiz listesi.

    Kullanicinin butun dokumu okumasi yerine, tutar ve sayi olmayan metinleri
    kisa bir liste halinde onune koyariz; kalan bir ad varsa fark eder.
    """
    gorulen = []
    for _s, _x, _y, metin in maskeli:
        m = (metin or "").strip()
        if not m or m in (MASKE, "[TUTAR]") or _tutar_mi(m):
            continue
        if m.replace(",", "").replace(".", "").isdigit():
            continue
        if m not in gorulen:
            gorulen.append(m)
    return gorulen


def dokum_metni(maskeli, sayac, kalanlar):
    """Yapistirmaya hazir dokum metni."""
    satirlar = [
        "# Beyanname metin katmani dokumu (maskelenmis)",
        "# Bicim: sayfa <sekme> x <sekme> y <sekme> metin",
        "# Toplam %d parca, %d tanesi maskelendi." % (len(maskeli), sayac),
        "#",
        "# ---- GOZDEN GECIRIN: maskelenmemis %d metin ----" % len(kalanlar),
        "# Aralarinda kisisel bilgi varsa 'Ek gizlenecek' kutusuna yazip",
        "# dokumu yeniden uretin.",
    ]
    satirlar += ["#   %s" % m for m in kalanlar]
    satirlar += ["# ---- liste sonu ----", "#"]
    satirlar += ["%d\t%s\t%s\t%s" % (s, x, y, m) for s, x, y, m in maskeli]
    return "\n".join(satirlar)


def dokum_uret(yol_veya_akis, ek_gizle=(), tutarsiz=False):
    """Bir PDF'ten maskelenmis dokumu uretir.

    Doner: {"metin", "parca_sayisi", "maskelenen", "gozden_gecir"}
    """
    parcalar = _parcalar(yol_veya_akis)
    maskeli, sayac = maskele(parcalar, ek_gizle, tutarsiz)
    kalanlar = gozden_gecirilecekler(maskeli)
    return {
        "metin": dokum_metni(maskeli, sayac, kalanlar),
        "parca_sayisi": len(maskeli),
        "maskelenen": sayac,
        "gozden_gecir": kalanlar,
    }
