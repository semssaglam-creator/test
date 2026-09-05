"""KDV beyannamesi PDF'ini okur ve beyan satirlarina cevirir.

Girdi, GIB'in "KATMA DEGER VERGISI BEYANNAMESI (Gercek Usulde Vergilendirilen
Mukellefler Icin)" ciktisidir (1015 A). Hem kanuni suresinde verilen beyanname
hem de duzeltme beyannamesi ayni duzeni tasir; ikisi "Duzeltme Nedeni"
satirinin varligindan ve "Onay Zamani" damgasindan ayirt edilir.

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
# 2026 Nisan'da beyanname bicimi degisti: etiketler kisaldi ("Katma Deger
# Vergisi" -> "KDV"), bolumler bolundu ve kalemler kod onekli geldi. Yeni
# adlar ayni alanlara TAKMA AD olarak eklendi; boylece eski ve yeni bicim yan
# yana okunur. Tarihe gore bicim secmeye gerek yok - bir inceleme her iki
# bicimden beyanname icerebilir (Ocak-Mart eski, Nisan sonrasi yeni).
ETIKET_ESLEMESI = {
    "MATRAHTOPLAMI": "matrah_toplami",
    "TOPLAMMATRAH": "matrah_toplami",                    # yeni bicim
    "HESAPLANANKDV": "hesaplanan_kdv",                   # yeni bicim
    "TOPLAMKDV": "toplam_kdv",                           # yeni bicim
    "TECILEDILECEKKDV": "tecil_edilecek_kdv",            # yeni bicim
    "ODENMESIGEREKENKDV": "odenmesi_gereken_kdv",        # yeni bicim
    "IADEEDILMESIGEREKENKDV": "iade_edilmesi_gereken_kdv",   # yeni bicim
    "SONRAKIDONEMEDEVREDENKDV": "sonraki_donem_devreden",    # yeni bicim
    "ONCEKIDONEMDENDEVREDENKDV": "onceki_donem_devreden",    # yeni bicim
    "DAHAONCEINDIRIMKONUSUYAPILANKDVNINILAVESI2": "ilave_edilecek_kdv",
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
    # 2026 Nisan sonrasi bicimdeki bolum basliklari
    "MATRAH": "matrah",
    "MATRAHDETAYI": "matrah_detay",
    "INDIRIMLERDETAYI": "indirimler_detay",
    "ONCEKIDONEMDENDEVREDENINDIRILECEKKDV": "onceki_devir_detay",
    "DIGERINDIRIMLER": "diger_indirimler",
    "DIGERISLEMLER": "diger_islemler",
    "TEVKIFATUYGULANMAYANISLEMLER": "tevkifatsiz",
    "INDIRIMLER": "indirimler",
    "INDIRIMNEDENLERI": "indirim_nedenleri",
    "DIGERBILGILER": "diger",
    "IHRACKAYDIYLATESLIMLER": "ihrac",
    "SONUCHESAPLARI": "sonuc",
}

# Yalnizca belirli bir bolumde anlamli olan etiketler
BOLUME_BAGLI = {
    ("oran_dagilimi", "TOPLAM"): "bu_donem_indirilecek",
}

SAYI = re.compile(r"^-?\d{1,3}(?:\.\d{3})*,\d{2}$|^-?\d+,\d{2}$")
# Onay zamani iki bicimde gelebiliyor:
#   eski (2026 Nisan oncesi): 28.01.2025 - 22:07:21   (nokta, arada tire)
#   yeni:                     05/06/2026 12:52:04     (egik cizgi, tire yok)
# Ayirici ve tire istege bagli birakilarak ikisi de tek desenle okunur.
# Okunamazsa surumler onay zamanina gore siralanamaz ve butun duzeltme
# beyannameleri "kanuni suresinde" sayilir; bu yuzden desen genis tutuldu.
TARIH_SAATI = re.compile(
    r"(\d{2})[./](\d{2})[./](\d{4})\s*-?\s*(\d{2}):(\d{2}):(\d{2})")


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


# Formda bir alan adi en fazla kac satira tasiyor
EN_COK_SATIR = 3
# Alt alta gelen iki satirin ayni alana ait sayilabilmesi icin en buyuk dikey
# aralik ve sola hizalanma toleransi
SATIR_ARALIGI = 14
HIZA_TOLERANSI = 3


def _kod_ara(anahtar, bolum):
    return (ETIKET_ESLEMESI.get(anahtar)
            or EK_ETIKETLER.get(anahtar)
            or BOLUME_BAGLI.get((bolum, anahtar)))


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
    return n.startswith(("VERGIKIMLIKNUMARASI", "EPOSTAADRESI", "TICARETSICILNO",
                         "IRTIBATTELNO", "SOYADI", "ADI", "UNVANI",
                         "VERGIDAIRESIMUDURLUGU", "ONAYZAMANI"))


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


# "Indirim Nedenleri" bolumu uc sutunludur:
#   Degisiklik Nedeni | Aciklama | Miktar
# Sutun basliklarinin x konumu, veri satirlarini sutunlara dagitmakta kullanilir.
INDIRIM_NEDENI_SUTUNLARI = (
    ("DEGISIKLIKNEDENI", "neden"),
    ("ACIKLAMA", "aciklama"),
    ("MIKTAR", "miktar"),
)


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


def _indirim_nedenleri(parcalar):
    """İNDİRİM NEDENLERİ bolumundeki satirlari okur.

    Mukellef, gec gelen faturayi ilgili donemin beyannamesini duzeltmeden
    devreden KDV uzerinden yansittiginda, aradaki farkin gerekcesini bu
    bolume yazar. Uygulama devreden KDV zincirinde bir sicrama gordugunde
    bu satirlari kullaniciya gosterir; bu yuzden metin ve tutar birlikte
    saklanir.

    Sutun basliklari bulunursa satirlar basliklarin x konumuna gore
    dagitilir. Baslik satiri okunamazsa daha kaba bir yol izlenir: satirdaki
    son sayi miktar, ilk metin neden, arasi aciklama sayilir. Boylece biçim
    beklenenden saparsa bolum tumuyle kaybolmaz.

    Doner: [{"neden", "aciklama", "miktar"}]
    """
    for sayfa_no in sorted({s for s, _x, _y, _m in parcalar}):
        sayfa = [(x, y, m) for s, x, y, m in parcalar if s == sayfa_no]
        baslik = next((p for p in sayfa
                       if normalize(p[2]) == "INDIRIMNEDENLERI"), None)
        if baslik is None:
            continue
        # Bolum basligindan asagisi; sonraki bolum basligina kadar
        altindakiler = [p for p in sayfa if p[1] < baslik[1] - HIZA_TOLERANSI]
        satirlar = _satirlara_bol(altindakiler)

        sutun_x = {}
        veri_satirlari = []
        for _y, hucreler in satirlar:
            anahtarlar = [normalize(m) for _x, m in hucreler]
            if any(a in BOLUM_BASLIKLARI for a in anahtarlar):
                break                                   # sonraki bolum basladi
            if not sutun_x:
                # Sutun basligi satiri: uc basligi da tasiyorsa konumlari al
                for anahtar, ad in INDIRIM_NEDENI_SUTUNLARI:
                    for x, m in hucreler:
                        if normalize(m) == anahtar:
                            sutun_x[ad] = x
                            break
                if len(sutun_x) >= 2:
                    continue                            # baslik satiri veriye girmez
                sutun_x = {}
            if any(_etiket_mi(m) for _x, m in hucreler):
                break                                   # taninan bir alan basligi
            veri_satirlari.append(hucreler)

        return _indirim_satirlarini_coz(veri_satirlari, sutun_x)
    return []


def _indirim_satirlarini_coz(veri_satirlari, sutun_x):
    """Bolumun veri satirlarini {neden, aciklama, miktar} kayitlarina cevirir."""
    def sutuna_ata(x):
        if not sutun_x:
            return None
        return min(sutun_x, key=lambda ad: abs(sutun_x[ad] - x))

    kayitlar = []
    for hucreler in veri_satirlari:
        alanlar = {"neden": [], "aciklama": [], "miktar": None}
        artakalan = []
        for x, metin in hucreler:
            tutar = tutar_coz(metin)
            if tutar is not None:
                alanlar["miktar"] = tutar
                continue
            ad = sutuna_ata(x)
            if ad in ("neden", "aciklama"):
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
        if not neden and not aciklama and alanlar["miktar"] is None:
            continue
        # Yalnizca aciklama tasiyan satir, ustteki kaydin devamidir
        if kayitlar and not neden and alanlar["miktar"] is None and aciklama:
            kayitlar[-1]["aciklama"] = (kayitlar[-1]["aciklama"] + " " + aciklama).strip()
            continue
        kayitlar.append({"neden": neden, "aciklama": aciklama,
                         "miktar": alanlar["miktar"]})
    return kayitlar


def _kunye(parcalar):
    """Mukellef, donem ve onay bilgilerini cikarir."""
    kunye = {"vkn": "", "unvan": "", "vergi_dairesi": "", "yil": None, "ay": None,
             "onay_zamani": "", "duzeltme_nedeni": ""}

    ilk_sayfa = [(x, y, m) for s, x, y, m in parcalar if s == 0]
    ilk_sayfa.sort(key=lambda p: (-p[1], p[0]))
    metinler = [m for _x, _y, m in ilk_sayfa]
    tam = " ".join(metinler)

    # Onay zamani ve duzeltme nedeni
    eslesme = TARIH_SAATI.search(tam)
    if eslesme:
        kunye["onay_zamani"] = eslesme.group(0)
    for i, (_x, _y, m) in enumerate(ilk_sayfa):
        if normalize(m).startswith("DUZELTMENEDENI"):
            kunye["duzeltme_nedeni"] = (_duzeltme_nedeni(ilk_sayfa, i)
                                        or "(belirtilmemiş)")

    # Vergi dairesi: "VERGI DAIRESI MUDURLUGU" yazisinin hemen ustundeki ad
    for idx, (x, y, m) in enumerate(ilk_sayfa):
        if normalize(m) == "VERGIDAIRESIMUDURLUGU":
            for x2, y2, m2 in ilk_sayfa:
                if abs(x2 - x) < 6 and 0 < y2 - y <= 20 and tutar_coz(m2) is None:
                    kunye["vergi_dairesi"] = m2.strip()
                    break
            break

    # Yil / Ay: etiketin sagindaki deger
    for etiket, alan in (("YIL", "yil"), ("AY", "ay")):
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

    # VKN ve unvan
    for x, y, m in ilk_sayfa:
        if normalize(m) == "VERGIKIMLIKNUMARASI":
            for x2, y2, m2 in ilk_sayfa:
                if abs(y2 - y) <= 3 and x2 > x + 10 and re.fullmatch(r"\d{10,11}", m2.strip()):
                    kunye["vkn"] = m2.strip()
                    break
            break
    parcalari = []
    for etiket in ("SOYADIUNVANI", "ADIUNVANINDEVAMI"):
        for x, y, m in ilk_sayfa:
            if normalize(m) == etiket:
                for x2, y2, m2 in ilk_sayfa:
                    if abs(y2 - y) <= 3 and x2 > x + 10:
                        parcalari.append(m2.strip())
                        break
                break
    kunye["unvan"] = " ".join(p for p in parcalari if p).strip()
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


def beyanname_oku(yol, dosya_adi=None):
    """Bir beyanname PDF'ini okur.

    Doner:
        {
          "yil", "ay", "vkn", "unvan", "vergi_dairesi",
          "tur": "kanuni" | "duzeltme",
          "onay_zamani", "onay_ts", "duzeltme_nedeni",
          "indirim_nedenleri": [{"neden", "aciklama", "miktar"}],
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

    uyarilar = _denetle(degerler)
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
