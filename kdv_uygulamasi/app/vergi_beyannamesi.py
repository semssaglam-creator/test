"""Yillik Gelir / Kurumlar Vergisi beyannamesi PDF'inden ozet okur.

Tutanakta yer alan "Gelir Vergisi Beyannamesi Özeti" tablosunu elle girmek
yerine beyannameden almak icindir.

Neden KDV okuyucusundan farkli bir yontem:
    KDV beyannamesi okuyucusu (`pdf_beyanname`) satir kodlarina ve hucre
    koordinatlarina dayanir; o bicim iyi bilindigi icin guvenle yapilabiliyor.
    Gelir/Kurumlar beyannamesinin yerlesimi elimizde ornekle dogrulanmis
    degil. Bu yuzden burada daha dayanikli ama daha kaba bir yol izlenir:
    sayfadaki metin parcalari satirlara bolunur, taninan bir etiketin
    bulundugu satirdaki EN SAGDAKI tutar o etiketin degeri sayilir.

Bulunamayan kalem sessizce atlanir; okunanlar kullaniciya once gosterilir,
kullanici onaylayip kunyeye yazar. Uygulama beyannameyi kendiliginden
tutanaga islemez.
"""
import re

from .pdf_beyanname import PdfHata, _parcalar, normalize, tutar_coz

# Taninan ozet kalemleri. Anahtar normalize edilmis etiket, deger belgede
# yazilacak bicimdir. Uzun etiketler once denenir ki kisa olan onlari
# golgelemesin (orn. "MATRAH" ile "KURUMLARVERGISIMATRAHI").
KALEMLER = [
    # --- Kurumlar Vergisi ---
    ("TICARIBILANCOKARI", "Ticari Bilanço Karı"),
    ("TICARIBILANCOZARARI", "Ticari Bilanço Zararı"),
    ("KANUNENKABULEDILMEYENGIDERLER", "Kanunen Kabul Edilmeyen Giderler"),
    ("ZARAROLSADAHIINDIRILECEKISTISNAVEINDIRIMLER",
     "Zarar Olsa Dahi İndirilecek İstisna ve İndirimler"),
    ("KURUMLARVERGISIMATRAHI", "Kurumlar Vergisi Matrahı"),
    ("HESAPLANANKURUMLARVERGISI", "Hesaplanan Kurumlar Vergisi"),
    ("ODENMESIGEREKENKURUMLARVERGISI", "Ödenmesi Gereken Kurumlar Vergisi"),
    ("IADESIGEREKENKURUMLARVERGISI", "İadesi Gereken Kurumlar Vergisi"),
    # --- Gelir Vergisi ---
    ("TICARIKAZANCLAR", "Ticari Kazançlar"),
    ("ZIRAIKAZANCLAR", "Zirai Kazançlar"),
    ("SERBESTMESLEKKAZANCLARI", "Serbest Meslek Kazançları"),
    ("VERGIYETABIGELIRMATRAH", "Vergiye Tabi Gelir (Matrah)"),
    ("VERGIYETABIGELIR", "Vergiye Tabi Gelir (Matrah)"),
    ("HESAPLANANGELIRVERGISI", "Hesaplanan Gelir Vergisi"),
    ("ODENMESIGEREKENGELIRVERGISI", "Ödenmesi Gereken Gelir Vergisi"),
    ("IADESIGEREKENGELIRVERGISI", "İadesi Gereken Gelir Vergisi"),
    # --- Ikisinde de gecen ---
    ("MAHSUPEDILECEKVERGILERTOPLAMI", "Mahsup Edilecek Vergiler Toplamı"),
    ("MAHSUPEDILECEKVERGILER", "Mahsup Edilecek Vergiler Toplamı"),
    ("MAHSUPEDILECEKINDIRIMLERVEGECMISYILZARARLARI",
     "Mahsup Edilecek İndirimler ve Geçmiş Yıl Zararları"),
]

# Tek basina "KAR" / "ZARAR" gibi kisa etiketler bilerek yok: normalize edilmis
# metinde Turkce sozcuklerin icine dusup (KARSILIGI, ZARARLARI...) alakasiz bir
# tutari kaleme baglayabiliyorlar. Yanlis bir rakamin resmi belgeye girmesi,
# kalemin hic okunmamasindan kotudur.

# Beyanname turunu anlamak icin aranan basliklar
TUR_IPUCLARI = [
    ("KURUMLARVERGISIBEYANNAMESI", "Kurumlar Vergisi"),
    ("YILLIKGELIRVERGISIBEYANNAMESI", "Gelir Vergisi"),
    ("GELIRVERGISIBEYANNAMESI", "Gelir Vergisi"),
]

SATIR_TOLERANSI = 3.0        # ayni satir sayilacak dikey sapma (punto)
YIL = re.compile(r"\b(20\d{2})\b")


def _satirlara_bol(parcalar):
    """(sayfa, x, y, metin) parcalarini satirlara toplar.

    Doner: [(sayfa, y, [(x, metin), ...]), ...] — soldan saga sirali.
    """
    satirlar = []
    for sayfa, x, y, metin in parcalar:
        if not str(metin).strip():
            continue
        for satir in satirlar:
            if satir[0] == sayfa and abs(satir[1] - y) <= SATIR_TOLERANSI:
                satir[2].append((x, metin))
                break
        else:
            satirlar.append((sayfa, y, [(x, metin)]))
    for _s, _y, ogeler in satirlar:
        ogeler.sort(key=lambda o: o[0])
    return satirlar


def _turu_bul(satirlar):
    for _s, _y, ogeler in satirlar:
        birlesik = normalize("".join(m for _x, m in ogeler))
        for anahtar, ad in TUR_IPUCLARI:
            if anahtar in birlesik:
                return ad
    return ""


def _yili_bul(satirlar):
    for _s, _y, ogeler in satirlar:
        metin = " ".join(m for _x, m in ogeler)
        if "DÖNEM" in metin.upper() or "YIL" in metin.upper():
            bulunan = YIL.search(metin)
            if bulunan:
                return bulunan.group(1)
    for _s, _y, ogeler in satirlar:
        bulunan = YIL.search(" ".join(m for _x, m in ogeler))
        if bulunan:
            return bulunan.group(1)
    return ""


def _satirdaki_tutar(ogeler):
    """Satirdaki en sagdaki sayiyi dondurur; yoksa None."""
    for _x, metin in reversed(ogeler):
        tutar = tutar_coz(metin)
        if tutar is not None:
            return tutar
    return None


def ozet_oku(yol, dosya_adi=None):
    """Beyanname PDF'inden ozet kalemlerini okur.

    Doner: {"tur", "yil", "kalemler": [{"etiket", "tutar"}], "uyarilar": [...]}
    """
    parcalar = _parcalar(yol)
    satirlar = _satirlara_bol(parcalar)
    tur = _turu_bul(satirlar)
    yil = _yili_bul(satirlar)

    # Belgenin turu taninmadiysa hic kalem okunmaz. Baska bir beyannameden
    # (orn. KDV) rastgele eslesen bir tutarin tutanaga girmesi, ozetin bos
    # kalmasindan cok daha kotudur.
    if not tur:
        raise PdfHata(
            "Bu dosya yıllık Gelir veya Kurumlar Vergisi beyannamesi olarak "
            "tanınmadı. Beyannamenin başlığı okunamadığı için özet "
            "çıkarılmadı; yanlış bir tutarın tutanağa girmemesi için okuma "
            "durduruldu.")

    kalemler, gorulen = [], set()
    for _s, _y, ogeler in satirlar:
        birlesik = normalize("".join(m for _x, m in ogeler))
        if not birlesik:
            continue
        for anahtar, etiket in KALEMLER:
            if anahtar not in birlesik or etiket in gorulen:
                continue
            tutar = _satirdaki_tutar(ogeler)
            if tutar is None:
                continue
            kalemler.append({"etiket": etiket, "tutar": round(tutar, 2)})
            gorulen.add(etiket)
            break                     # bir satir en fazla bir kaleme karsilik gelir

    uyarilar = []
    if not kalemler:
        raise PdfHata(
            "Beyannamede tanınan özet kalemi bulunamadı. Bu bir yıllık Gelir "
            "veya Kurumlar Vergisi beyannamesi çıktısı olmayabilir; metin "
            "katmanı olan bir PDF gerekir.")
    return {"tur": tur, "yil": yil, "kalemler": kalemler, "uyarilar": uyarilar,
            "kaynak": dosya_adi or ""}


def kunye_metnine_cevir(ozet):
    """Okunan kalemleri kunyedeki "açıklama | tutar" bicimine getirir."""
    from . import turkce
    return "\n".join("%s | %s" % (k["etiket"], turkce.tl(k["tutar"]))
                     for k in ozet.get("kalemler") or [])
