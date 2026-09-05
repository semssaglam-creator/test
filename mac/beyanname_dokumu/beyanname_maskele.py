#!/usr/bin/env python3
"""Beyanname PDF'inin metin katmanini, mukellef bilgileri maskelenmis olarak dokun.

Neden: Ayristiriciyi yeni bir beyanname bicimine uyarlamak icin PDF'in metin
katmani ve her parcanin sayfadaki konumu gerekir. Belgenin kendisini
paylasmaya gerek yok; bu betik dokumu uretirken kimlik bilgilerini maskeler.

DIKKAT: PDF'te yaziyi ustunden boyamak (highlight) metni SILMEZ. Boyanan
metin katmanda oldugu gibi durur ve okunur. Guvenli yol, metnin kendisini
degistirmektir - bu betigin yaptigi budur.

Mac'te: yanindaki "Beyanname Dokumu Al.command" dosyasina cift tiklamak
yeter; bu betigi elle calistirmaniza gerek yok.

Terminalden:
    python3 beyanname_maskele.py beyanname.pdf
    python3 beyanname_maskele.py beyanname.pdf --ek-gizle "ACME LTD" --ek-gizle "Ahmet"
    python3 beyanname_maskele.py beyanname.pdf --tutarsiz     # tutarlari da gizle

Cikti ekrana yazilir; dosyaya almak icin:
    python3 beyanname_maskele.py beyanname.pdf > dokum.txt

Ciktiyi GONDERMEDEN ONCE GOZDEN GECIRIN. Betik kimlik alanlarini bicimlerinden
ve sayfadaki yerlerinden taniyor; tanimadigi bir alan kalirsa --ek-gizle ile
elle ekleyebilirsiniz.
"""
import argparse
import os
import re
import sys
import unicodedata

def _lib_yollarini_ekle():
    """Uygulamanin gomulu `lib/` klasorunu arayip sys.path'e ekler.

    Dagitilan pakette lib/ betigin yanindadir; depodan calistirilinca ise
    uygulamanin lib/ klasoru (linux/kdv_uygulamasi/lib) kullanilir. Dosya
    tek basina indirilip baska bir yere de konabiliyor; o yuzden birkac makul
    yer sirayla denenir. Hicbiri yoksa sistemde kurulu pypdf de is gorur.
    """
    burasi = os.path.dirname(os.path.abspath(__file__))
    depo = os.path.join(burasi, os.pardir, os.pardir)   # mac/beyanname_dokumu -> depo koku
    adaylar = [
        os.path.join(burasi, "lib"),                    # dagitilan paketin icinde
        os.path.join(os.path.dirname(burasi), "lib"),
        os.path.join(depo, "linux", "kdv_uygulamasi", "lib"),   # depodan calisirken
        os.path.join(os.getcwd(), "lib"),               # bulundugu klasorden
        os.path.join(os.getcwd(), "kdv_uygulamasi", "lib"),
        os.path.join(os.path.dirname(os.getcwd()), "lib"),
    ]
    for aday in adaylar:
        if os.path.isdir(os.path.join(aday, "pypdf")) and aday not in sys.path:
            sys.path.insert(0, aday)
            return aday
    return None


ARANAN_LIB = _lib_yollarini_ekle()

MASKE = "[MASKELI]"

# Kimlik bilgilerinin bulundugu bloklarin basliklari. Bu basliklardan sonra
# gelen ve asagidaki "veri bolumu" basliklarindan once biten alanda, etiket
# olmayan her parca maskelenir.
KIMLIK_BOLUMLERI = (
    "MUKELLEFBILGILERI",
    "BEYANNAMENINHANGISIFATLAVERILDIGIBILGILERIMUKELLEF",
    "BEYANNAMENINHANGISIFATLAVERILDIGIBILGILERI",
    "BEYANNAMEYIDUZENLEYENBILGILERI",
    "BEYANNAMEYIONAYLAYANBILGILERI",
)

# Kimlik bloklarinin bittigi yer: buradan sonrasi tutar/veri bolumleridir.
VERI_BOLUMLERI = (
    "MATRAH", "MATRAHVEVERGIBILDIRIMI", "MATRAHDETAYI", "INDIRIMLER",
    "INDIRIMLERDETAYI", "SONUCHESAPLARI", "DIGERBILGILER", "TEVKIFAT",
    "IHRACKAYDIYLATESLIMLER", "INDIRIMNEDENLERI",
)

# Kimlik bloklarindaki ETIKETLER korunur; yalnizca degerleri maskelenir.
KIMLIK_ETIKETLERI = (
    "TCKIMLIKNO", "VERGIKIMLIKNO", "ADISOYADIUNVANI", "EPOSTAADRESI",
    "TELEFONNO", "SUBENO", "VERGIDAIRESI", "VERGIDAIRESIMUDURLUGU",
    "YIL", "AY", "DONEMTIPI", "ONAYZAMANI", "SOYADI", "ADI", "UNVANI",
    "TICARETSICILNO", "IRTIBATTELNO",
)

# Bicimlerinden taninan kisisel veriler; belgenin her yerinde maskelenir.
DESENLER = (
    re.compile(r"\b\d{10,11}\b"),                          # VKN / TCKN
    re.compile(r"[\w.+-]+@[\w-]+\.[\w.]+"),                # e-posta
    re.compile(r"(?:\+90|0)[\s()-]*\d{3}[\s()-]*\d{3}"     # telefon
               r"[\s()-]*\d{2}[\s()-]*\d{2}"),
    re.compile(r"\bTR\d{2}[\dA-Z ]{16,30}\b"),             # IBAN
)

TUTAR = re.compile(r"^-?\d{1,3}(?:\.\d{3})*,\d{2}$|^-?\d+,\d{2}$")

# Kimlik bandinda gecse de kisisel olmayan, ayristiricinin donemi tanimasi icin
# GEREKEN degerler. Bunlar maskelenmez.
AY_ADLARI = ("OCAK", "SUBAT", "MART", "NISAN", "MAYIS", "HAZIRAN", "TEMMUZ",
             "AGUSTOS", "EYLUL", "EKIM", "KASIM", "ARALIK")
DONEM_TIPLERI = ("AYLIK", "UCAYLIK", "YILLIK")
YIL_DESENI = re.compile(r"^(?:19|20)\d{2}$")


def guvenli_deger(metin):
    """Kimlik bandinda olsa bile maskelenmemesi gereken deger mi.

    Donem (yil / ay / donem tipi) ve vergi dairesi kisiye ozel bilgi degil;
    ayristirici beyannamenin hangi doneme ait oldugunu bunlardan anliyor.
    Maskelenirse dokum ise yaramaz hale gelir.
    """
    a = normalize(metin)
    if not a:
        return True
    if a in AY_ADLARI or a in DONEM_TIPLERI:
        return True
    if YIL_DESENI.match(metin.strip()):
        return True
    if "VERGIDAIRESI" in a:
        return True
    return False


def normalize(metin):
    """pdf_beyanname.normalize ile ayni sadelestirme (etiket karsilastirmasi)."""
    d = {"İ": "I", "ı": "i", "Ş": "S", "ş": "s", "Ğ": "G", "ğ": "g",
         "Ü": "U", "ü": "u", "Ö": "O", "ö": "o", "Ç": "C", "ç": "c"}
    metin = "".join(d.get(k, k) for k in (metin or ""))
    metin = unicodedata.normalize("NFKD", metin)
    metin = "".join(k for k in metin if not unicodedata.combining(k))
    return "".join(k for k in metin.upper() if k.isalnum())


def _kripto_saglayicisini_ele():
    """pypdf'in istege bagli sifreleme saglayicilarini kapatir.

    pypdf, sifreli PDF'ler icin once `cryptography` sonra `PyCryptodome`
    dener. Bu paketler KURULU AMA BOZUKSA (ornegin derlenmis eklentisi
    eksikse) yoklamanin kendisi ImportError yerine Rust katmanindan bir panik
    uretiyor. Panik metnini Python yakalayamaz; dogrudan terminale basilir ve
    betik calistigi halde cokmus gibi gorunur:

        ModuleNotFoundError: No module named '_cffi_backend'
        thread '<unnamed>' panicked at ... Python API call failed

    Bu yuzden paketleri yoklamak yerine, denemeden None isaretliyoruz. pypdf
    temiz bir ImportError gorup saf Python yoluna dusuyor. Beyanname PDF'leri
    sifreli olmadigi icin kaybimiz yok.
    """
    for ad in ("cryptography", "Crypto"):
        if ad not in sys.modules:
            sys.modules[ad] = None


def parcalari_al(yol):
    """PDF'teki her metin parcasini (sayfa, x, y, metin) olarak dondurur."""
    _kripto_saglayicisini_ele()
    try:
        import pypdf
    except ImportError:
        sys.exit(
            "pypdf bulunamadi.\n\n"
            "Bu betik PDF okumak icin pypdf kullanir; normalde yanindaki\n"
            "lib/ klasorunden gelir. Demek ki lib/ klasoru eksik.\n\n"
            "Cozum: paketi (zip'i) oldugu gibi acin - beyanname_maskele.py,\n"
            "'Beyanname Dokumu Al.command' ve lib/ ayni klasorde durmali.\n"
            "Ya da pypdf'i kurun: pip3 install --user pypdf")
    if isinstance(yol, str) and not os.path.isfile(yol):
        sys.exit("Dosya bulunamadi: %s\n"
                 "Yolu kontrol edin; bosluk iceriyorsa tirnak icine alin." % yol)
    try:
        okuyucu = pypdf.PdfReader(yol)
    except Exception as exc:
        sys.exit("PDF acilamadi: %s" % exc)

    tumu = []
    for sayfa_no, sayfa in enumerate(okuyucu.pages):
        gecici = []

        def gorucu(metin, cm, tm, yazitipi, boyut, _l=gecici):
            if metin and metin.strip():
                _l.append((round(tm[4], 1), round(tm[5], 1), metin.strip()))

        try:
            sayfa.extract_text(visitor_text=gorucu)
        except Exception as exc:
            sys.exit("Sayfa %d okunamadi: %s" % (sayfa_no + 1, exc))
        for x, y, metin in gecici:
            tumu.append((sayfa_no, x, y, metin))
    if not tumu:
        sys.exit("PDF'te metin katmani yok. Taranmis (resim) bir belge olabilir; "
                 "bu durumda dokum uretilemez.")
    return tumu


# Kurum/kisi adi belirtileri. Bolge tespiti (kimlik bandi) PDF'in koordinat
# bilgisine dayaniyor; koordinatlar bozuk gelirse o katman calismaz. Bu liste
# koordinattan bagimsiz calisir ve unvani yine de yakalar.
UNVAN_BELIRTILERI = (
    "AS", "ANONIMSIRKETI", "LTD", "LIMITED", "STI", "SIRKETI", "SANAYI",
    "TICARET", "TIC", "SAN", "KOLLEKTIF", "KOMANDIT", "HOLDING", "ISLETMESI",
)


def unvana_benziyor(metin):
    """Parca bir kurum unvani ya da kisi adi gibi mi duruyor.

    Kesin bir olcut degil; amac koordinat katmani calismadiginda unvanin
    maskelenmeden gecmesini onlemek. Fazladan maskelemek, eksik maskelemekten
    iyidir - eksik maskelenen bilgi geri alinamaz.
    """
    a = normalize(metin)
    if not a or TUTAR.match(metin):
        return False
    parcalar = [normalize(p) for p in metin.replace(".", " ").split()]
    return any(p in UNVAN_BELIRTILERI for p in parcalar if p)


def gozden_gecirilecekler(maskeli):
    """Maskelenmemis serbest metinlerin listesi (kullanici gozden gecirsin).

    Bolge ve desen katmanlarindan gecen her sey guvenli demek degil; tanimadigi
    bir alan kalmis olabilir. Kullanicinin butun dokumu okumasi yerine, tutar
    ve sayi olmayan benzersiz metinleri kisa bir liste halinde onune koyariz.
    """
    gorulen = []
    for _sayfa, _x, _y, metin in maskeli:
        m = metin.strip()
        if not m or m == MASKE or m == "[TUTAR]":
            continue
        if TUTAR.match(m) or m.replace(",", "").replace(".", "").isdigit():
            continue
        if m not in gorulen:
            gorulen.append(m)
    return gorulen


def desenle_maskele(metin):
    """Bicimlerinden taninan kisisel verileri metnin icinde maskeler."""
    for desen in DESENLER:
        metin = desen.sub(MASKE, metin)
    return metin


def kimlik_bandi_mi(parcalar):
    """Her parca icin, kimlik blogunun icinde olup olmadigini isaretler.

    Kimlik bilgileri sayfanin ust bandinda, bilinen bir baslikla basliyor ve
    ilk veri bolumu basliginda bitiyor. Sayfa sirasi ve y konumuna gore
    ilerleyip bu bandi bulur.
    """
    icinde = [False] * len(parcalar)
    # Okuma sirasi: sayfa, sonra yukaridan asagi (y azalan), sonra soldan saga
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
    gizlenecek = {normalize(e) for e in ek_gizle if e.strip()}
    # Bir kez maskelenen deger belgenin baska yerinde de gecebilir
    maskelenmis_degerler = set()

    # Once kimlik bandi: etiket olmayan her parca maskelenir
    ara_sonuc = []
    for i, (sayfa, x, y, metin) in enumerate(parcalar):
        anahtar = normalize(metin)
        etiket = any(anahtar.startswith(e) for e in KIMLIK_ETIKETLERI)
        if (bandda[i] or unvana_benziyor(metin)) and not etiket \
                and not TUTAR.match(metin) and not guvenli_deger(metin):
            maskelenmis_degerler.add(anahtar)
            ara_sonuc.append((sayfa, x, y, MASKE))
        else:
            ara_sonuc.append((sayfa, x, y, metin))

    sonuc = []
    sayac = 0
    for sayfa, x, y, metin in ara_sonuc:
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
        if tutarsiz and TUTAR.match(yeni):
            yeni = "[TUTAR]"
        if yeni != metin:
            sayac += 1
        sonuc.append((sayfa, x, y, yeni))
    return sonuc, sayac


def main():
    ayristirici = argparse.ArgumentParser(
        description="Beyanname PDF'inin metin katmanini maskeleyerek doker.")
    ayristirici.add_argument("pdf", help="Beyanname PDF dosyasi")
    ayristirici.add_argument("--ek-gizle", action="append", default=[], metavar="METIN",
                             help="Ek olarak maskelenecek metin (birden cok kez verilebilir)")
    ayristirici.add_argument("--tutarsiz", action="store_true",
                             help="Tutarlari da gizle (aritmetik dogrulamasi yapilamaz)")
    a = ayristirici.parse_args()

    parcalar = parcalari_al(a.pdf)
    maskeli, sayac = maskele(parcalar, a.ek_gizle, a.tutarsiz)

    print("# Beyanname metin katmani dokumu (maskelenmis)")
    print("# Bicim: sayfa <sekme> x <sekme> y <sekme> metin")
    print("# Toplam %d parca, %d tanesi maskelendi." % (len(maskeli), sayac))
    print("# GONDERMEDEN ONCE GOZDEN GECIRIN: maskelenmemis kisisel bilgi kaldiysa")
    print("# --ek-gizle \"...\" ile yeniden calistirin.")
    print("#")

    kalanlar = gozden_gecirilecekler(maskeli)
    print("# ---- GOZDEN GECIRIN: maskelenmemis %d metin ----" % len(kalanlar))
    print("# Aralarinda kisisel bilgi varsa betigi soyle yeniden calistirin:")
    print("#   python3 beyanname_maskele.py DOSYA --ek-gizle \"o metin\"")
    for m in kalanlar:
        print("#   %s" % m)
    print("# ---- liste sonu ----")
    print("#")

    for sayfa, x, y, metin in maskeli:
        print("%d\t%s\t%s\t%s" % (sayfa, x, y, metin))


if __name__ == "__main__":
    main()
