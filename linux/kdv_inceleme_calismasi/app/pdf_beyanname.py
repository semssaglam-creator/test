"""KDV beyannamesi PDF'ini okur ve beyan satirlarina cevirir.

Girdi, GIB'in "KATMA DEGER VERGISI BEYANNAMESI (Gercek Usulde Vergilendirilen
Mukellefler Icin)" ciktisidir (1015 A). Hem kanuni suresinde verilen beyanname
hem de duzeltme beyannamesi ayni duzeni tasir; ikisi "Duzeltme Nedeni"
satirinin varligindan ve "Onay Zamani" damgasindan ayirt edilir.

Iki cikti bicimi
----------------
Ayni beyannamenin iki farkli basimi dolasimdadir; okuyucu ikisini de kabul
eder ve hangisi oldugunu kendi anlar (`_yeni_bicim_mi`).

  ESKI bicim                          YENI bicim
  ----------------------------------  ----------------------------------
  "Yıl"  "2025"   (iki ayri parca)    "Yıl: 2026"   (tek parca)
  "28.01.2025 - 22:07:21"             "06/05/2026 06:01:51"
  "Vergi Kimlik Numarası"             "Vergi Kimlik No"
  "Soyadı (Unvanı)" + devami          "Adı Soyadı/Ünvanı"
  "... Katma Değer Vergisi"           "... KDV"  (sonuc hesaplarinda)
  vergi dairesi, adinin altindaki      vergi dairesi etiketsiz; donem
  "Vergi Dairesi Müdürlüğü" ile        serisinin ("Şube No / Yıl / Ay")
  isaretlenir                          en solunda durur
  indirimler yalnizca toplam olarak    ayrica "INDIRIMLER DETAYI"nde
  ilgili satirlarda                    kalem kalem ("108 - ...")
  butun bolumler basilir, bos          tutari tumden sifir olan BOLUM hic
  satirlar 0,00 gorunur                basilmaz

Son fark onemlidir: yeni bicimde eksik bolum "okunamadi" degil "sifir"
demektir. Bu yuzden yeni bicimde okunamayan cekirdek satirlar sifir kabul
edilir (`YENI_BICIM_SIFIRLAR`); okuma yanlissa `_denetle`nin aritmetigi
zaten tutmaz ve kullanici uyarilir.

Neden konum bazli okuma
-----------------------
PDF'te metin, gorsel duzenden bagimsiz bir sirada saklanir; duz metin
cikarildiginda etiketler ve tutarlar birbirine karisir (ornegin
"20 36.090.556,00180.452.780,00"). Bu yuzden her metin parcasinin sayfa
uzerindeki (x, y) konumu alinir:

  - Solda duran metinler etikettir; alt alta gelenler tek bir cok satirli
    etiket blogunda birlestirilir (form alanlari iki satira tasabiliyor).
  - Sagda duran sayilar tutardir; her tutar, dikey olarak denk geldigi
    etiket bloguna baglanir.

Boylece etiketin kac satira yayildigi ya da tutarin etiketin ustunde mi
altinda mi durdugu onemini yitirir.
"""
import os
import re
import sys
import unicodedata
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LIB_DIR = os.path.join(BASE_DIR, "lib")
if LIB_DIR not in sys.path:
    sys.path.insert(0, LIB_DIR)
# pypdf, Python 3.11'den eskisinde typing_extensions'a ihtiyac duyar.
# Sona eklenir; gerekcesi main.py'de aciklanmistir (kurulu surumu golgelememek).
EK_LIB_DIR = os.path.join(BASE_DIR, "lib_ek")
if EK_LIB_DIR not in sys.path:
    sys.path.append(EK_LIB_DIR)

AYLAR_PDF = {
    "OCAK": 1, "SUBAT": 2, "MART": 3, "NISAN": 4, "MAYIS": 5, "HAZIRAN": 6,
    "TEMMUZ": 7, "AGUSTOS": 8, "EYLUL": 9, "EKIM": 10, "KASIM": 11, "ARALIK": 12,
}

# Beyannamedeki alan adlarinin uygulama satir kodlarina karsiligi.
# Anahtarlar normalize edilmis (buyuk harf, Turkce harfler sadelestirilmis,
# noktalama ve bosluk atilmis) bicimdedir.
ETIKET_ESLEMESI = {
    "MATRAHTOPLAMI": "matrah_toplami",
    # Yeni bicimde ad ters cevrilmis: "Matrah Toplamı" -> "Toplam Matrah".
    # Eksikligi sessiz kaliyordu: okunamayan cekirdek satirlar yeni bicimde
    # sifir sayildigi icin (bkz. YENI_BICIM_SIFIRLAR) matrah 0,00 gorunuyordu.
    "TOPLAMMATRAH": "matrah_toplami",
    "HESAPLANANKATMADEGERVERGISI": "hesaplanan_kdv",
    "DAHAONCEINDIRIMKONUSUYAPILANKDVNINILAVESI": "ilave_edilecek_kdv",
    "ILAVEEDILECEKKDV": "ilave_edilecek_kdv",
    "TOPLAMKATMADEGERVERGISI": "toplam_kdv",

    # --- Indirimler
    "ONCEKIDONEMDENDEVREDENINDIRILECEKKDV": "onceki_donem_devreden",
    "SATISTANIADEEDILENISLEMIGERCEKLESMEYENVEYAISLEMINDENVAZGECILENMALVEHIZMETLERNEDENIYLEINDIRILMESIGEREKENKDV":
        "satistan_iade_kdv",
    "TURKIYEDEIKAMETETMEYENLEREBUDONEMDEIADEEDILENKDV": "ikamet_etmeyenlere_iade",
    "YURTICIALIMLARAILISKINKDV": "yurtici_alim_kdv",
    "SORUMLUSIFATIYLABEYANEDILEREKODENENKDV": "sorumlu_sifatiyla_kdv",
    "ITHALDEODENENKDV": "ithalde_odenen_kdv",
    "DEGERSIZHALEGELENALACAKLARAILISKININDIRILECEKKDV": "degersiz_alacak_kdv",
    "INDIRIMLERTOPLAMI": "indirimler_toplami",

    # --- Ihrac kaydiyla teslimler
    "IHRACKAYDIYLATESLIMBEDELITOPLAMI": "ihrac_teslim_bedeli",
    "YUKLENILENKDV": "ihrac_yuklenilen_kdv",
    "TECILEDILEBILIRKDV": "tecil_edilebilir_kdv",
    "IHRACATINGERCEKLESTIGIDONEMDEIADEEDILECEKTECILEDILEMEYENKDV":
        "ihracat_tecil_edilemeyen",
    "INDIRIMLIORANATABIMALLARINIHRACKAYDIYLATESLIMINDEIADEEDILECEKYUKLENILENVERGIFARKI":
        "indirimli_oran_yuklenim_farki",

    # --- Istisnalar / diger iade hakki doguran islemler
    "ISTISNAKAPSAMINAGIRENISLEMLEREAITTOPLAMTESLIMVEHIZMETTUTARI":
        "istisna_toplam_teslim",
    "YURTICIVEYURTDISIKDVODENMEKSIZINTEMINEDILENMALBEDELI": "kdv_odenmeksizin_temin",
    "IHRACATINGERCEKLESTIGIDONEMDEIADEEDILECEKKDV": "ihracat_doneminde_iade",
    "IADEEDILEBILIRKDV": "iade_edilebilir_kdv",

    # --- Sonuc hesaplari
    "TECILEDILECEKKATMADEGERVERGISI": "tecil_edilecek_kdv",
    "ODENMESIGEREKENKATMADEGERVERGISI": "odenmesi_gereken_kdv",
    "IADEEDILMESIGEREKENKATMADEGERVERGISI": "iade_edilmesi_gereken_kdv",
    "SONRAKIDONEMEDEVREDENKATMADEGERVERGISI": "sonraki_donem_devreden",

    # --- Diger bilgiler
    "OZELMATRAHSEKLINETABIISLEMLERDEMATRAHADAHILOLMAYANBEDEL": "ozel_matrah_bedel",
    "TESLIMVEHIZMETLERINKARSILIGINITESKILEDENBEDELAYLIK": "teslim_bedel_aylik",
    "TESLIMVEHIZMETLERINKARSILIGINITESKILEDENBEDELKUMULATIF": "teslim_bedel_kumulatif",
    "KREDIKARTIILETAHSILEDILENTESLIMVEHIZMETLERINKDVDAHILKARSILIGINITESKILEDENBEDEL":
        "kredi_karti_tahsilat",

    # --- Yeni bicimin kisaltilmis alan adlari
    # Ayni satirlar, "Katma Değer Vergisi" yerine "KDV" yazilarak basiliyor.
    # Eski adlar yukarida duruyor; ikisi bir arada calisir.
    "HESAPLANANKDV": "hesaplanan_kdv",
    "TOPLAMKDV": "toplam_kdv",
    "TECILEDILECEKKDV": "tecil_edilecek_kdv",
    "ODENMESIGEREKENKDV": "odenmesi_gereken_kdv",
    "IADEEDILMESIGEREKENKDV": "iade_edilmesi_gereken_kdv",
    "SONRAKIDONEMEDEVREDENKDV": "sonraki_donem_devreden",
    # "İNDİRİMLER DETAYI" tablosunun devir satiri. Ayni metin bolumun
    # basligi olarak da gecer; baslikta tutar bulunmadigi icin deger
    # buradan, tablo satirindan gelir.
    "ONCEKIDONEMDENDEVREDENKDV": "onceki_donem_devreden",
}

# Beyannamede yer alan ama uygulama satirlarina girmeyen, yine de bilgi olarak
# tasinan alanlar
EK_ETIKETLER = {
    "BUDONEMDEODENMESIGEREKENKATMADEGERVERGISI": "bu_donemde_odenmesi_gereken",
    "7440SAYILIKANUNUN62AMADDESIKAPSAMINDAKIISLEMLERNEDENIYLEHESAPLANANKATMADEGERVERGISI":
        "kanun_7440_hesaplanan",
}

# Bolum basliklari: ayni etiket farkli bolumlerde farkli anlam tasiyabildigi
# icin (ornegin yalin "Toplam") gecerli bolum izlenir.
BOLUM_BASLIKLARI = {
    "BUDONEMEAITINDIRILECEKKDVTUTARININORANLARAGOREDAGILIMI": "oran_dagilimi",
    "MATRAHVEVERGIBILDIRIMI": "matrah",
    "INDIRIMLER": "indirimler",
    "INDIRIMNEDENLERI": "indirim_nedenleri",
    "DIGERBILGILER": "diger",
    "IHRACKAYDIYLATESLIMLER": "ihrac",
    "SONUCHESAPLARI": "sonuc",

    # --- Yeni bicimin bolumleri
    # Bunlar deger tasimaz; bolum olarak taninmalari, altlarindaki yalin
    # "Toplam" satirlarinin baska bir bolumun toplami sanilmasini onler.
    "INDIRIMLERDETAYI": "indirimler_detayi",
    "DIGERINDIRIMLER": "diger_indirimler",
    "MATRAH": "matrah",
    "MATRAHDETAYI": "matrah_detayi",
    "TEVKIFATUYGULANMAYANISLEMLER": "tevkifatsiz",
    "ISTISNALARDIGERIADEHAKKIDOGURANISLEMLER": "istisnalar",
    "ISTISNALARDIGERIADEHAKKIDOGURANISLEMLERDETAYI": "istisnalar_detayi",
    "TAMISTISNAKAPSAMINAGIRENISLEMLER": "tam_istisna",
    "IHRACKAYDIYLATESLIMLEREAITBILDIRIM": "ihrac_bildirim",
    "MUKELLEFBILGILERI": "kunye",
    "BEYANNAMEYIDUZENLEYENBILGILERI": "kunye",
    "BEYANNAMEYIONAYLAYANBILGILERI": "kunye",
}

# Yalnizca belirli bir bolumde anlamli olan etiketler
BOLUME_BAGLI = {
    ("oran_dagilimi", "TOPLAM"): "bu_donem_indirilecek",
}

SAYI = re.compile(r"^-?\d{1,3}(?:\.\d{3})*,\d{2}$|^-?\d+,\d{2}$")
# Onay damgasi iki bicimde gelir: eskisinde "28.01.2025 - 22:07:21",
# yenisinde "06/05/2026 06:01:51" (nokta yerine egik cizgi, tire yok).
TARIH_SAATI = re.compile(
    r"(\d{2})[./](\d{2})[./](\d{4})\s*-?\s*(\d{2}):(\d{2}):(\d{2})")
# Yeni bicimde kunye alanlari "Etiket: Deger" olarak tek parcada basilir
# ("Yıl: 2026", "Dönem Tipi: AYLIK", "Onay Zamanı: ...").
SATIR_ICI_ALAN = re.compile(r"^\s*([^:]{2,40}?)\s*:\s*(.*)$")
# Yeni bicimde indirim kalemleri resmi satir koduyla basilir:
# "108 - Yurtiçi Alımlara İlişkin KDV". Kod, alan adinin parcasi degildir.
BAS_KODU = re.compile(r"^\d{2,3}(?=[A-Z])")


class PdfHata(Exception):
    """Kullaniciya gosterilecek okuma hatasi."""


def normalize(metin):
    """Etiket karsilastirmasi icin sadelestirir.

    Buyuk harfe cevirir, Turkce harfleri ASCII karsiligina indirir, harf ve
    rakam disindaki her seyi atar. Boylece kesme isareti, parantez, iki nokta
    ve satir sonu farklari eslesmeyi bozmaz.
    """
    if not metin:
        return ""
    d = {"İ": "I", "ı": "i", "Ş": "S", "ş": "s", "Ğ": "G", "ğ": "g",
         "Ü": "U", "ü": "u", "Ö": "O", "ö": "o", "Ç": "C", "ç": "c"}
    metin = "".join(d.get(k, k) for k in metin)
    metin = unicodedata.normalize("NFKD", metin)
    metin = "".join(k for k in metin if not unicodedata.combining(k))
    return "".join(k for k in metin.upper() if k.isalnum())


def tutar_coz(metin):
    """'1.234.567,89' -> 1234567.89"""
    if metin is None:
        return None
    m = metin.strip().replace(" ", "")
    if not SAYI.match(m):
        return None
    return float(m.replace(".", "").replace(",", "."))


def _kripto_saglayicisini_ele(_yapildi=[]):
    """pypdf'in istege bagli sifreleme saglayicilarini gerekiyorsa devre disi birakir.

    pypdf, sifreli PDF'ler icin once `cryptography` sonra `PyCryptodome`
    paketlerini dener ve bulamazsa saf Python cozumune duser. Ancak bu paketler
    KURULU AMA BOZUK ise (ornegin derlenmis eklentisi eksikse) import
    ImportError yerine baska bir hata firlatir; pypdf bunu yakalamaz ve
    uygulama hic acilmaz.

    Okudugumuz beyanname PDF'leri sifreli olmadigi icin bu saglayicilara
    ihtiyac yoktur. Bozuk olanlari sys.modules'te None isaretleyerek pypdf'in
    temiz bir ImportError gorup saf Python yoluna dusmesini saglariz.
    """
    if _yapildi:
        return
    _yapildi.append(True)
    denemeler = (
        ("cryptography", "from cryptography.hazmat.primitives.ciphers.algorithms "
                         "import AES"),
        ("Crypto", "from Crypto.Cipher import AES"),
    )
    for ad, ifade in denemeler:
        if sys.modules.get(ad) is None and ad in sys.modules:
            continue
        try:
            exec(compile(ifade, "<kripto denetimi>", "exec"), {})
        except BaseException:       # ImportError da, bozuk kurulumun paniki de
            sys.modules[ad] = None


def _parcalar(yol):
    """PDF'teki her metin parcasini (sayfa, x, y, metin) olarak dondurur."""
    _kripto_saglayicisini_ele()
    try:
        import pypdf
    except ImportError as exc:                                # pragma: no cover
        raise PdfHata("PDF okuyucu (pypdf) bulunamadı: %s" % exc)

    try:
        okuyucu = pypdf.PdfReader(yol)
    except Exception as exc:
        raise PdfHata("PDF açılamadı: %s" % exc)

    tumu = []
    for sayfa_no, sayfa in enumerate(okuyucu.pages):
        gecici = []

        def gorucu(metin, cm, tm, yazitipi, boyut, _liste=gecici):
            if metin and metin.strip():
                _liste.append((round(tm[4], 1), round(tm[5], 1), metin.strip()))

        try:
            sayfa.extract_text(visitor_text=gorucu)
        except Exception as exc:
            raise PdfHata("PDF metni okunamadı (sayfa %d): %s" % (sayfa_no + 1, exc))
        for x, y, metin in gecici:
            tumu.append((sayfa_no, x, y, metin))
    if not tumu:
        raise PdfHata("PDF'te metin bulunamadı. Taranmış (resim) bir belge olabilir; "
                      "metin katmanı olan bir çıktı gerekir.")
    return tumu


def _etiket_satirlari(parcalar, sayfa_no):
    """Sayfadaki etiket metinlerini yukaridan asagiya sirali dondurur."""
    satirlar = [(x, y, m) for s, x, y, m in parcalar
                if s == sayfa_no and tutar_coz(m) is None]
    satirlar.sort(key=lambda p: (-p[1], p[0]))
    return satirlar


def _tutarlar(parcalar, sayfa_no):
    return [(x, y, tutar_coz(m)) for s, x, y, m in parcalar
            if s == sayfa_no and tutar_coz(m) is not None]


# Formda bir alan adi en fazla kac satira tasiyor. Yeni bicimde sutunlar
# daha dar oldugu icin dorde cikti (ornegin "Kredi Kartı İle Tahsil Edilen /
# Teslim ve Hizmetlerin KDV / Dahil Karşılığını Teşkil Eden / Bedel").
# Yukseltmek yanlis birlestirme riski tasimaz: birlesik metin ancak BILINEN
# bir alan adina birebir esitse kabul edilir.
EN_COK_SATIR = 4
# Alt alta gelen iki satirin ayni alana ait sayilabilmesi icin en buyuk dikey
# aralik ve sola hizalanma toleransi
SATIR_ARALIGI = 14
HIZA_TOLERANSI = 3


def _kod_ara(anahtar, bolum):
    kod = (ETIKET_ESLEMESI.get(anahtar)
           or EK_ETIKETLER.get(anahtar)
           or BOLUME_BAGLI.get((bolum, anahtar)))
    if kod:
        return kod
    # Yeni bicim alan adinin onune resmi satir kodunu koyuyor
    # ("108 - Yurtiçi Alımlara İlişkin KDV"). Kod atilarak yeniden bakilir;
    # boylece iki bicim icin tek bir alan adi tablosu yeter.
    kodsuz = BAS_KODU.sub("", anahtar)
    if kodsuz != anahtar:
        return (ETIKET_ESLEMESI.get(kodsuz)
                or EK_ETIKETLER.get(kodsuz)
                or BOLUME_BAGLI.get((bolum, kodsuz)))
    return None


def _bloklari_esle(satirlar):
    """Etiket satirlarini bilinen alan adlariyla eslestirir.

    Bir alan adi forma iki-uc satira tasabildigi icin, her satirdan baslayarak
    once tek satir, sonra iki, sonra uc satir birlestirilerek tabloda aranir;
    ilk tutan alinir. Piksel araligina gore tahmin yurutmek yerine bilinen
    resmi alan adlarina dayanmak, satir araliklarinin birbirine yakin oldugu
    yerlerde (ornegin ayri bir alan ile devam satirinin 13 ve 11 punto
    olmasi) yanlis birlesmeyi onler.

    Doner: [{"kod", "metin", "ust", "alt", "x"}], eslesmeyen metinler
    """
    bolum = None
    bloklar = []
    tanimsiz = []
    i = 0
    while i < len(satirlar):
        x, y, metin = satirlar[i]
        anahtar = normalize(metin)
        if anahtar in BOLUM_BASLIKLARI:
            bolum = BOLUM_BASLIKLARI[anahtar]
            i += 1
            continue

        bulunan = None
        birlesik = metin
        for uzunluk in range(1, EN_COK_SATIR + 1):
            if uzunluk > 1:
                j = i + uzunluk - 1
                if j >= len(satirlar):
                    break
                x2, y2, m2 = satirlar[j]
                onceki_y = satirlar[j - 1][1]
                if abs(x2 - x) > HIZA_TOLERANSI or not 0 < onceki_y - y2 <= SATIR_ARALIGI:
                    break
                if normalize(m2) in BOLUM_BASLIKLARI:
                    break
                birlesik += " " + m2
            kod = _kod_ara(normalize(birlesik), bolum)
            if kod:
                bulunan = (kod, uzunluk, birlesik)
                break

        if not bulunan:
            tanimsiz.append(metin)
            i += 1
            continue

        kod, uzunluk, tam_metin = bulunan
        bloklar.append({
            "kod": kod, "metin": tam_metin, "x": x,
            "ust": y, "alt": satirlar[i + uzunluk - 1][1],
        })
        i += uzunluk
    return bloklar, tanimsiz


def _alanlari_topla(parcalar):
    """Etiket bloklarini tutarlarla eslestirir. Doner: ({kod: deger}, tanimsiz)"""
    degerler = {}
    tanimsiz = []
    for sayfa_no in sorted({s for s, _x, _y, _m in parcalar}):
        bloklar, sayfa_tanimsiz = _bloklari_esle(_etiket_satirlari(parcalar, sayfa_no))
        tanimsiz.extend(sayfa_tanimsiz)
        tutarlar = _tutarlar(parcalar, sayfa_no)
        kullanilan = set()

        for blok in bloklar:
            if blok["kod"] in degerler:
                continue                      # ilk gorulen gecerli

            # Blogun dikey araligina denk gelen, sagdaki tutar
            aday = None
            for i, (x, y, deger) in enumerate(tutarlar):
                if i in kullanilan or x < blok["x"]:
                    continue
                if blok["alt"] - 4 <= y <= blok["ust"] + 4:
                    uzaklik = 0
                else:
                    uzaklik = min(abs(y - blok["alt"]), abs(y - blok["ust"]))
                if uzaklik <= 4 and (aday is None or (uzaklik, -x) < (aday[0], -aday[2])):
                    aday = (uzaklik, i, x, deger)
            if aday:
                kullanilan.add(aday[1])
                degerler[blok["kod"]] = aday[3]
    return degerler, tanimsiz


def _etiket_mi(metin):
    """Parca, beyannamenin taninan bir alan / bolum basligi mi."""
    n = normalize(metin)
    if not n:
        return False
    if n in ETIKET_ESLEMESI or n in EK_ETIKETLER or n in BOLUM_BASLIKLARI:
        return True
    # "Vergi Kimlik Numarası", "E-Posta Adresi" gibi kunye etiketleri de burada
    # durdurucu sayilir; hepsini listelemek yerine bilinen birkac tanesi yeter.
    # Sondaki dordu yeni bicimin kunye alanlaridir.
    return n.startswith(("VERGIKIMLIKNUMARASI", "EPOSTAADRESI", "TICARETSICILNO",
                         "IRTIBATTELNO", "SOYADI", "ADI", "UNVANI",
                         "VERGIDAIRESIMUDURLUGU", "ONAYZAMANI",
                         "VERGIKIMLIKNO", "TCKIMLIKNO", "TELEFONNO", "SUBENO"))


# Duzeltme beyannamesini isaretleyen alanin adi bicime gore degisir.
DUZELTME_ETIKETLERI = ("DUZELTMENEDENI", "DUZELTMEACIKLAMASI")


def _duzeltme_nedeni(ilk_sayfa, indeks):
    """Duzeltme nedeni aciklamasinin tamamini toplar.

    Aciklama tek parcada bitmeyebilir: uzun metinler PDF'te ayni satirda birkac
    parcaya bolunur ya da alt satira taser. Onceden yalnizca ilk parca
    alindigindan gerekce yarim kaliyordu. Burada once etiketin kendi satirinin
    devami, sonra hemen altindaki satirlar - taninan bir alan basligina ya da
    satir araligindan buyuk bir bosluga rastlanana kadar - eklenir.
    """
    x0, y0, m0 = ilk_sayfa[indeks]
    parcalar = []
    kalan = m0.split(":", 1)[1].strip() if ":" in m0 else ""
    if kalan:
        parcalar.append(kalan)

    onceki_y = y0
    for x, y, m in ilk_sayfa[indeks + 1:]:
        ayni_satir = abs(y - onceki_y) <= HIZA_TOLERANSI
        alt_satir = 0 < onceki_y - y <= SATIR_ARALIGI + HIZA_TOLERANSI
        if not (ayni_satir or alt_satir):
            break
        if _etiket_mi(m) or tutar_coz(m) is not None:
            break
        # Alt satira gecildiyse aciklamanin devami sola yaslidir; sagdaki ayri
        # bir sutun (ornegin "Onay Zamanı" degeri) gerekceye karismasin.
        if alt_satir and x > x0 + 200:
            break
        metin = m.strip()
        if metin:
            parcalar.append(metin)
        onceki_y = y
    return " ".join(parcalar).strip()


def _satir_ici_alanlar(ilk_sayfa):
    """Yeni bicimdeki "Etiket: Deger" parcalarini sozluge cevirir.

    Ayni etiket birden cok gecerse ilki gecerlidir; kunye alanlari sayfanin
    ustunde durur, asagidaki tekrarlar (tablo sutunlari) sonra gelir.
    """
    alanlar = {}
    for _x, _y, m in ilk_sayfa:
        e = SATIR_ICI_ALAN.match(m)
        if not e:
            continue
        anahtar = normalize(e.group(1))
        if anahtar and anahtar not in alanlar:
            alanlar[anahtar] = e.group(2).strip()
    return alanlar


def _yeni_bicim_mi(parcalar, alanlar):
    """Cikti, yeni beyanname duzeninde mi.

    En kesin isaret, donem bilgisinin "Yıl: 2026" gibi TEK parcada
    basilmasidir; eski bicimde etiket ve deger ayri parcalardir. Yedek
    isaret, yalnizca yeni bicimde bulunan "INDIRIMLER DETAYI" bolumudur.
    """
    if "DONEMTIPI" in alanlar or ("YIL" in alanlar and "AY" in alanlar):
        return True
    return any(normalize(m) == "INDIRIMLERDETAYI" for _s, _x, _y, m in parcalar)


def _sagdaki_deger(ilk_sayfa, etiketler, dogrula=None, devam=False):
    """Etiketin sagindaki degeri dondurur.

    `etiketler` normalize edilmis alan adlaridir; ilk gecerli degeri veren
    gecerlidir (ayni ad formda birden cok blokta gecebiliyor: "Vergi Kimlik
    No" hem mukellefin hem beyannameyi onaylayanin bolumunde var).

    `devam` verilirse deger, alt satira tasan parcalariyla birlestirilir;
    yalnizca yeni bicimde gerekir (unvan iki satira tasiyor).
    """
    for x, y, m in ilk_sayfa:
        if normalize(m) not in etiketler:
            continue
        aday = None
        for x2, y2, m2 in ilk_sayfa:
            if abs(y2 - y) > 3 or x2 <= x + 10:
                continue
            if dogrula and not dogrula(m2.strip()):
                continue
            if aday is None or x2 < aday[0]:
                aday = (x2, m2.strip())
        if aday is None:
            continue                       # bu blokta yok; sonrakine bak
        ax, deger = aday
        if not devam:
            return deger
        parcalari, onceki = [deger], y
        for x2, y2, m2 in ilk_sayfa:
            if (abs(x2 - ax) <= 6 and 0 < onceki - y2 <= SATIR_ARALIGI
                    and tutar_coz(m2) is None and not _etiket_mi(m2)):
                parcalari.append(m2.strip())
                onceki = y2
        return " ".join(p for p in parcalari if p).strip()
    return ""


def _yeni_vergi_dairesi(ilk_sayfa):
    """Yeni bicimde vergi dairesi adini konumundan bulur.

    Bu bicimde alanin etiketi yoktur: ad, donem serisinin ("Şube No: - /
    Yıl: 2026 / Ay: Nisan / Dönem Tipi: AYLIK") en solunda tek basina
    durur ve alt satira tasabilir. Bu yuzden "Yıl:" parcasi capa alinip
    ayni bandin solundaki metin okunur.
    """
    capa = next(((x, y) for x, y, m in ilk_sayfa
                 if ":" in m and normalize(m).startswith("YIL")), None)
    if capa is None:
        return ""
    cx, cy = capa
    aday = None
    for x, y, m in ilk_sayfa:
        if abs(y - cy) > 4 or x >= cx or ":" in m or tutar_coz(m) is not None:
            continue
        if aday is None or x < aday[0]:
            aday = (x, m.strip())
    if aday is None:
        return ""
    ax, ad = aday
    parcalari, onceki = [ad], cy
    for x, y, m in ilk_sayfa:
        if (abs(x - ax) <= HIZA_TOLERANSI and 0 < onceki - y <= SATIR_ARALIGI
                and ":" not in m and tutar_coz(m) is None and not _etiket_mi(m)):
            parcalari.append(m.strip())
            onceki = y
    return " ".join(p for p in parcalari if p).strip()


def _kunye(parcalar):
    """Mukellef, donem ve onay bilgilerini cikarir.

    Iki cikti bicimini birden karsilar; farklari modulun basinda anlatildi.
    """
    kunye = {"vkn": "", "unvan": "", "vergi_dairesi": "", "yil": None, "ay": None,
             "onay_zamani": "", "duzeltme_nedeni": "", "donem_tipi": "",
             "yeni_bicim": False}

    ilk_sayfa = [(x, y, m) for s, x, y, m in parcalar if s == 0]
    ilk_sayfa.sort(key=lambda p: (-p[1], p[0]))
    metinler = [m for _x, _y, m in ilk_sayfa]
    tam = " ".join(metinler)
    alanlar = _satir_ici_alanlar(ilk_sayfa)
    kunye["yeni_bicim"] = _yeni_bicim_mi(parcalar, alanlar)
    kunye["donem_tipi"] = alanlar.get("DONEMTIPI", "")

    # Onay zamani ve duzeltme nedeni
    eslesme = TARIH_SAATI.search(tam)
    if eslesme:
        kunye["onay_zamani"] = eslesme.group(0)
    # Etiket bicime gore degisiyor: eski ciktida "Düzeltme Nedeni", 2026
    # Nisan sonrasi ciktida "Düzeltme Açıklaması". Etiket taninmazsa
    # beyanname duzeltme olarak isaretlenmiyor ve donem icin tek beyan
    # varmis gibi gorunuyordu.
    for i, (_x, _y, m) in enumerate(ilk_sayfa):
        if normalize(m).startswith(DUZELTME_ETIKETLERI):
            kunye["duzeltme_nedeni"] = (_duzeltme_nedeni(ilk_sayfa, i)
                                        or "(belirtilmemiş)")
    # Yeni bicimde beyanname turu ayri bir alanda yazili olabiliyor. Buradaki
    # olcut alanin ADI ve DEGERI birlikte oldugu icin dardir; "Değişiklik
    # Nedeni" (indirimler detayi tablosunun sutunu) buna takilmaz.
    if not kunye["duzeltme_nedeni"]:
        tur = alanlar.get("BEYANNAMETURU", "")
        if normalize(tur).startswith("DUZELTME"):
            kunye["duzeltme_nedeni"] = alanlar.get("DUZELTMENEDENI") or tur.strip()

    # Vergi dairesi: "VERGI DAIRESI MUDURLUGU" yazisinin hemen ustundeki ad
    for idx, (x, y, m) in enumerate(ilk_sayfa):
        if normalize(m) == "VERGIDAIRESIMUDURLUGU":
            for x2, y2, m2 in ilk_sayfa:
                if abs(x2 - x) < 6 and 0 < y2 - y <= 20 and tutar_coz(m2) is None:
                    kunye["vergi_dairesi"] = m2.strip()
                    break
            break
    if not kunye["vergi_dairesi"] and kunye["yeni_bicim"]:
        kunye["vergi_dairesi"] = _yeni_vergi_dairesi(ilk_sayfa)

    # Yil / Ay: yeni bicimde ayni parcada ("Yıl: 2026"), eskisinde etiketin
    # sagindaki ayri parcada.
    for etiket, alan in (("YIL", "yil"), ("AY", "ay")):
        if alanlar.get(etiket):
            kunye[alan] = alanlar[etiket]
            continue
        for x, y, m in ilk_sayfa:
            if normalize(m) != etiket:
                continue
            for x2, y2, m2 in ilk_sayfa:
                if abs(y2 - y) <= 3 and x2 > x + 10:
                    kunye[alan] = m2.strip()
                    break
            break

    if kunye["yil"]:
        try:
            kunye["yil"] = int(re.sub(r"\D", "", str(kunye["yil"]))[:4])
        except ValueError:
            kunye["yil"] = None
    if kunye["ay"]:
        kunye["ay"] = AYLAR_PDF.get(normalize(kunye["ay"]))

    # VKN: "Vergi Kimlik Numarası" (eski) / "Vergi Kimlik No" (yeni). Ad
    # formda birden cok gecer (mukellef, beyannameyi duzenleyen, onaylayan);
    # rakam denetimi sayesinde bos bloklar atlanir ve mukellefinki bulunur.
    kunye["vkn"] = _sagdaki_deger(
        ilk_sayfa, {"VERGIKIMLIKNUMARASI", "VERGIKIMLIKNO"},
        dogrula=lambda v: re.fullmatch(r"\d{10,11}", v) is not None)

    # Unvan: eski bicimde iki ayri alan ("Soyadı (Unvanı)" ve
    # "Adı (Unvanının Devamı)"), yeni bicimde tek alan ve degeri alt satira
    # tasabiliyor.
    parcalari = [_sagdaki_deger(ilk_sayfa, {etiket})
                 for etiket in ("SOYADIUNVANI", "ADIUNVANINDEVAMI")]
    kunye["unvan"] = " ".join(p for p in parcalari if p).strip()
    if not kunye["unvan"]:
        kunye["unvan"] = _sagdaki_deger(ilk_sayfa, {"ADISOYADIUNVANI"}, devam=True)
    return kunye


def _onay_ts(metin):
    """'28.01.2025 - 22:07:21' -> siralanabilir ISO damgasi."""
    e = TARIH_SAATI.search(metin or "")
    if not e:
        return ""
    g, a, y, s, d, sn = e.groups()
    try:
        return datetime(int(y), int(a), int(g), int(s), int(d), int(sn)).isoformat()
    except ValueError:
        return ""


def _turet(degerler):
    """Beyannamede dogrudan yer almayan uygulama satirlarini turetir."""
    ind = degerler.get("indirimler_toplami")
    onc = degerler.get("onceki_donem_devreden", 0.0)

    # Bu doneme ait indirilecek KDV = 108+109+110. Oran dagilimi tablosunun
    # toplami buna esit degildir: "Satıştan iade edilen ... nedeniyle
    # indirilmesi gereken KDV" (103) gibi kalemler de o tabloda oranlara
    # dagitilir. Toplami oldugu gibi almak, bu doneme ait indirimi sisirip
    # 103+104+105 toplamini ayni tutarda eksiltiyordu. Bu yuzden kalemler
    # okunabildiginde onlar esas alinir; oran dagilimi toplami yalnizca
    # kalemler yoksa (2019/Ocak ve oncesi bicimi) kullanilir.
    parcalar = [degerler.get(k) for k in
                ("yurtici_alim_kdv", "sorumlu_sifatiyla_kdv", "ithalde_odenen_kdv")]
    if any(p is not None for p in parcalar):
        kalem_toplami = round(sum(p or 0.0 for p in parcalar), 2)
        if "bu_donem_indirilecek" in degerler:
            degerler["oran_dagilimi_toplami"] = degerler["bu_donem_indirilecek"]
        degerler["bu_donem_indirilecek"] = kalem_toplami

    bu = degerler.get("bu_donem_indirilecek")
    # 103+104+105 toplami: indirimler toplamindan devir ve bu donem indirimi dusulur
    if ind is not None and bu is not None and "diger_indirimler_toplami" not in degerler:
        degerler["diger_indirimler_toplami"] = round(ind - (onc or 0.0) - bu, 2)

    hes = degerler.get("hesaplanan_kdv")
    top = degerler.get("toplam_kdv")
    if hes is not None and top is not None and "ilave_edilecek_kdv" not in degerler:
        degerler["ilave_edilecek_kdv"] = round(top - hes, 2)
    return degerler


# Yeni bicimde tutari tumden sifir olan BOLUM basligiyla birlikte hic
# basilmiyor (ornek beyannamede satis olmadigi icin "Matrah ve Vergi
# Bildirimi" bolumu yok). Eski bicimde her satir 0,00 olarak basildigindan
# bu ayrim yoktu. Bu yuzden yeni bicimde okunamayan cekirdek satirlar sifir
# sayilir. Yanlis okumayi ortmez: sifir kabulu hatali olsaydi _denetle'deki
# "toplam KDV - indirimler = odenecek / devreden" esitligi tutmazdi.
YENI_BICIM_SIFIRLAR = (
    "matrah_toplami", "hesaplanan_kdv", "ilave_edilecek_kdv", "toplam_kdv",
    "onceki_donem_devreden", "bu_donem_indirilecek", "diger_indirimler_toplami",
    "indirimler_toplami", "tecil_edilecek_kdv", "odenmesi_gereken_kdv",
    "iade_edilmesi_gereken_kdv", "sonraki_donem_devreden",
)


def _denetle(degerler):
    """Beyannamenin kendi icindeki aritmetigi denetler; uyari listesi dondurur."""
    uyarilar = []

    def d(kod):
        return degerler.get(kod) or 0.0

    if "hesaplanan_kdv" in degerler and "toplam_kdv" in degerler:
        beklenen = d("hesaplanan_kdv") + d("ilave_edilecek_kdv")
        if abs(beklenen - d("toplam_kdv")) > 0.01:
            uyarilar.append(
                "Toplam KDV %.2f okundu; hesaplanan (%.2f) ve ilave edilecek (%.2f) "
                "toplamı %.2f." % (d("toplam_kdv"), d("hesaplanan_kdv"),
                                   d("ilave_edilecek_kdv"), beklenen))

    if "oran_dagilimi_toplami" in degerler:
        fark = d("oran_dagilimi_toplami") - d("bu_donem_indirilecek")
        if abs(fark) > 0.01:
            iade = d("satistan_iade_kdv")
            uyarilar.append(
                "Oranlara göre dağılım tablosunun toplamı %.2f; yurtiçi alımlar, "
                "sorumlu sıfatıyla ödenen ve ithalde ödenen KDV toplamı ise %.2f. "
                "Aradaki %.2f fark, oranlara dağıtılan diğer indirim kalemlerinden "
                "gelir%s. Bu döneme ait indirilecek KDV olarak kalemlerin toplamı "
                "alındı; fark 103+104+105 toplamında yer alıyor."
                % (d("oran_dagilimi_toplami"), d("bu_donem_indirilecek"), fark,
                   " (satıştan iade edilen mal ve hizmetler nedeniyle indirilmesi "
                   "gereken KDV)" if abs(iade - fark) < 0.01 else ""))

    if "indirimler_toplami" in degerler and "bu_donem_indirilecek" in degerler:
        beklenen = (d("onceki_donem_devreden") + d("bu_donem_indirilecek")
                    + d("diger_indirimler_toplami"))
        if abs(beklenen - d("indirimler_toplami")) > 0.01:
            uyarilar.append(
                "İndirimler toplamı %.2f okundu; alt kalemlerin toplamı %.2f."
                % (d("indirimler_toplami"), beklenen))

    if "toplam_kdv" in degerler and "indirimler_toplami" in degerler:
        fark = d("toplam_kdv") - d("indirimler_toplami")
        bek_od = max(fark - d("tecil_edilecek_kdv"), 0.0) if fark > 0 else 0.0
        bek_dev = max(-fark - d("iade_edilmesi_gereken_kdv"), 0.0) if fark < 0 else 0.0
        if abs(bek_od - d("odenmesi_gereken_kdv")) > 0.01:
            uyarilar.append("Ödenmesi gereken KDV %.2f okundu; beyandaki rakamlara göre "
                            "%.2f olmalıydı." % (d("odenmesi_gereken_kdv"), bek_od))
        if abs(bek_dev - d("sonraki_donem_devreden")) > 0.01:
            uyarilar.append("Sonraki döneme devreden KDV %.2f okundu; beyandaki "
                            "rakamlara göre %.2f olmalıydı."
                            % (d("sonraki_donem_devreden"), bek_dev))
    return uyarilar



# --------------------------------------------------------------------------
# Devir degisikliginin gerekcesi
#
# Mukellef, gec gelen bir faturayi ilgili donemin beyannamesini duzeltmeden
# devreden KDV uzerinden yansittiginda, aradaki farkin gerekcesini
# beyannameye yazar. Uygulama devreden KDV zincirinde bir sicrama gordugunde
# bu satirlari kullaniciya gosterir; bu yuzden metin ve tutar birlikte
# saklanir.
#
# Gerekce iki ayri yerde durabiliyor:
#
#   Eski bicim  : "INDIRIM NEDENLERI" bolumu, uc sutun
#                 Degisiklik Nedeni | Aciklama | Miktar
#
#   2026 Nisan+ : "INDIRIMLER DETAYI" icindeki "Onceki Donemden Devreden
#                 Indirilecek KDV" tablosu, dort sutun
#                 Degisiklik Nedeni | Devrolunan (Eski Mukellef) Sirket VKN |
#                 Aciklama | KDV Tutari
#
# Sutun basliklarinin x konumu, veri satirlarini sutunlara dagitmakta
# kullanilir.
INDIRIM_TABLOLARI = (
    {
        "baslik": "INDIRIMNEDENLERI",
        "sutunlar": (("DEGISIKLIKNEDENI", "neden"),
                     ("ACIKLAMA", "aciklama"),
                     ("MIKTAR", "miktar")),
        # Eski bicimde bolumun bittigi yer, taninan bir alan basligidir.
        "etikette_dur": True,
    },
    {
        "baslik": "ONCEKIDONEMDENDEVREDENINDIRILECEKKDV",
        "sutunlar": (("DEGISIKLIKNEDENI", "neden"),
                     ("DEVROLUNANESKIMUKELLEFSIRKETVKN", "vkn"),
                     ("ACIKLAMA", "aciklama"),
                     ("KDVTUTARI", "miktar")),
        # Yeni tabloda veri satiri taninan bir alan adiyla basliyor
        # ("Onceki donemden devreden KDV"); etikette durulursa tablo bos kalir.
        "etikette_dur": False,
    },
)

# Yeni tabloda, devir tutari degismemis donemde de bir satir bulunur ve
# "Degisiklik Nedeni" sutununa alanin kendi adi yazilir. Bu satir bir gerekce
# degil, "gerekce yok" demektir; aksi halde her beyanname gerekceli gorunur ve
# devir sicramasi uyarisi anlamini yitirir.
VARSAYILAN_DEVIR_SATIRI = "ONCEKIDONEMDENDEVREDENKDV"


def _satirlara_bol(parcalar_xy):
    """(x, y, metin) parcalarini ayni satirda olanlari birlestirerek gruplar.

    Doner: [(y, [(x, metin), ...])] - yukaridan asagiya sirali, her satirin
    icinde soldan saga.
    """
    sirali = sorted(parcalar_xy, key=lambda p: (-p[1], p[0]))
    satirlar = []
    for x, y, metin in sirali:
        if satirlar and abs(satirlar[-1][0] - y) <= HIZA_TOLERANSI:
            satirlar[-1][1].append((x, metin))
        else:
            satirlar.append((y, [(x, metin)]))
    for _y, hucreler in satirlar:
        hucreler.sort(key=lambda h: h[0])
    return satirlar


def _bos_hucre(metin, varsayilan=None):
    """Hucre bos mu sayilir.

    Beyanname bos hucreye tire koyuyor. Ayrica bir hucre alanin kendi adini
    tasiyorsa (varsayilan) yine bilgi tasimiyor demektir.
    """
    sade = (metin or "").strip(" -\u2013\u2014\t")
    if not sade:
        return True
    return varsayilan is not None and normalize(sade) == varsayilan


def _indirim_nedenleri(parcalar):
    """Devir degisikliginin gerekcesini tasiyan tabloyu okur.

    Beyannamenin bicimine gore iki tablodan biri bulunur; ilk dolu olan
    dondurulur (bkz. INDIRIM_TABLOLARI).
    """
    for tablo in INDIRIM_TABLOLARI:
        kayitlar = _indirim_tablosunu_oku(parcalar, tablo)
        if kayitlar:
            return kayitlar
    return []


def _indirim_tablosunu_oku(parcalar, tablo):
    """Bir gerekce tablosunun satirlarini okur.

    Sutun basliklari bulunursa satirlar basliklarin x konumuna gore
    dagitilir. Baslik satiri okunamazsa daha kaba bir yol izlenir: satirdaki
    son sayi miktar, ilk metin neden, arasi aciklama sayilir. Boylece bicim
    beklenenden saparsa bolum tumuyle kaybolmaz.
    """
    for sayfa_no in sorted({s for s, _x, _y, _m in parcalar}):
        sayfa = [(x, y, m) for s, x, y, m in parcalar if s == sayfa_no]
        baslik = next((p for p in sayfa
                       if normalize(p[2]) == tablo["baslik"]), None)
        if baslik is None:
            continue
        altindakiler = [p for p in sayfa if p[1] < baslik[1] - HIZA_TOLERANSI]
        satirlar = _satirlara_bol(altindakiler)

        sutun_x = {}
        veri_satirlari = []
        for _y, hucreler in satirlar:
            anahtarlar = [normalize(m) for _x, m in hucreler]
            if any(a in BOLUM_BASLIKLARI for a in anahtarlar):
                break                                   # sonraki bolum basladi
            if not sutun_x:
                for anahtar, ad in tablo["sutunlar"]:
                    for x, m in hucreler:
                        if normalize(m) == anahtar:
                            sutun_x[ad] = x
                            break
                if len(sutun_x) >= 2:
                    continue                            # baslik satiri veri degil
                sutun_x = {}
            if anahtarlar and anahtarlar[0] == "TOPLAM":
                break                                   # tablonun toplam satiri
            if tablo["etikette_dur"] and any(_etiket_mi(m) for _x, m in hucreler):
                break                                   # taninan bir alan basligi
            veri_satirlari.append(hucreler)

        return _indirim_satirlarini_coz(veri_satirlari, sutun_x)
    return []


def _indirim_satirlarini_coz(veri_satirlari, sutun_x):
    """Veri satirlarini {neden, aciklama, miktar} kayitlarina cevirir."""
    def sutuna_ata(x):
        if not sutun_x:
            return None
        return min(sutun_x, key=lambda ad: abs(sutun_x[ad] - x))

    kayitlar = []
    for hucreler in veri_satirlari:
        alanlar = {"neden": [], "aciklama": [], "vkn": [], "miktar": None}
        artakalan = []
        for x, metin in hucreler:
            tutar = tutar_coz(metin)
            if tutar is not None:
                alanlar["miktar"] = tutar
                continue
            ad = sutuna_ata(x)
            if ad in ("neden", "aciklama", "vkn"):
                alanlar[ad].append(metin)
            else:
                artakalan.append(metin)
        if artakalan and not sutun_x:
            # Baslik okunamadi: ilk parca neden, kalani aciklama
            alanlar["neden"] = artakalan[:1]
            alanlar["aciklama"] = artakalan[1:]
        elif artakalan:
            alanlar["aciklama"].extend(artakalan)

        neden = " ".join(alanlar["neden"]).strip()
        aciklama = " ".join(alanlar["aciklama"]).strip()
        vkn = " ".join(alanlar["vkn"]).strip()
        if not neden and not aciklama and alanlar["miktar"] is None:
            continue
        if (_bos_hucre(neden, VARSAYILAN_DEVIR_SATIRI) and _bos_hucre(aciklama)
                and _bos_hucre(vkn)):
            continue
        # Yalnizca aciklama tasiyan satir, ustteki kaydin devamidir
        if kayitlar and not neden and alanlar["miktar"] is None and aciklama:
            kayitlar[-1]["aciklama"] = (
                kayitlar[-1]["aciklama"] + " " + aciklama).strip()
            continue
        kayit = {"neden": neden, "aciklama": aciklama, "miktar": alanlar["miktar"]}
        if not _bos_hucre(vkn):
            kayit["vkn"] = vkn
        kayitlar.append(kayit)
    return kayitlar

def beyanname_oku(yol, dosya_adi=None):
    """Bir beyanname PDF'ini okur.

    Doner:
        {
          "yil", "ay", "vkn", "unvan", "vergi_dairesi",
          "tur": "kanuni" | "duzeltme",
          "onay_zamani", "onay_ts", "duzeltme_nedeni",
          "kaynak", "degerler": {satir_kodu: tutar}, "ek": {...},
          "uyarilar": [...], "tanimsiz": [...]
        }
    """
    parcalar = _parcalar(yol)
    kunye = _kunye(parcalar)
    degerler, tanimsiz = _alanlari_topla(parcalar)
    indirim_nedenleri = _indirim_nedenleri(parcalar)

    ek = {kod: degerler.pop(kod) for kod in list(EK_ETIKETLER.values())
          if kod in degerler}
    degerler = _turet(degerler)

    if not degerler:
        raise PdfHata("Beyanname alanları okunamadı. Dosya bir KDV beyannamesi "
                      "çıktısı (1015 A) olmayabilir.")
    if kunye["yil"] is None or kunye["ay"] is None:
        raise PdfHata("Beyannamenin dönemi (yıl/ay) okunamadı.")

    # Turetmeden SONRA: turetme (ornegin 103+104+105 toplami) var olan
    # degerlere dayanir, sifirla doldurulmus olanlara degil.
    if kunye["yeni_bicim"]:
        for kod in YENI_BICIM_SIFIRLAR:
            degerler.setdefault(kod, 0.0)

    uyarilar = _denetle(degerler)
    if kunye["donem_tipi"] and normalize(kunye["donem_tipi"]) != "AYLIK":
        # Calisma aylik KDV duzenine gore kuruldugu icin ucer aylik bir
        # beyanname sessizce tek aya yazilir; kullanici bunu gormeli.
        uyarilar.append(
            "Beyannamenin dönem tipi \"%s\" okundu. Çalışma aylık KDV düzenine "
            "göre kuruludur; bu beyanname yalnızca %d. aya yazılır."
            % (kunye["donem_tipi"], kunye["ay"]))
    # Oran dagilimi toplami bir uygulama satiri degildir; denetimden sonra
    # bilgi alanina alinir.
    if "oran_dagilimi_toplami" in degerler:
        ek["oran_dagilimi_toplami"] = degerler.pop("oran_dagilimi_toplami")

    return {
        "yil": kunye["yil"],
        "ay": kunye["ay"],
        "vkn": kunye["vkn"],
        "unvan": kunye["unvan"],
        "vergi_dairesi": kunye["vergi_dairesi"],
        "tur": "duzeltme" if kunye["duzeltme_nedeni"] else "kanuni",
        "bicim": "yeni" if kunye["yeni_bicim"] else "eski",
        "donem_tipi": kunye["donem_tipi"],
        "onay_zamani": kunye["onay_zamani"],
        "onay_ts": _onay_ts(kunye["onay_zamani"]),
        "duzeltme_nedeni": kunye["duzeltme_nedeni"],
        "indirim_nedenleri": indirim_nedenleri,
        # yol bir akis (BytesIO) da olabilir; bkz. fatura_oku.dosya_oku
        "kaynak": dosya_adi or (os.path.basename(yol)
                                if isinstance(yol, str) else ""),
        "degerler": degerler,
        "ek": ek,
        "uyarilar": uyarilar,
        "tanimsiz": tanimsiz,
    }
