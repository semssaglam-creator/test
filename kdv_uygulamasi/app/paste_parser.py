"""Sistemden kopyalanan KDV beyan blogunu ayristirir.

Beklenen bicim, Excel calismasindaki 45-96 satirlarinin aynisidir:

    DÖNEMİ            OCAK      ŞUBAT     ...  ARALIK
    MATRAH TOPLAMI    343869,40 176004,00 ...
    HESAPLANAN KDV     61896,49  31680,72 ...

Ayristirma iki asamalidir:
1) Satir etiketleri `satirlar.BEYAN_SATIRLARI` sirasiyla sirali olarak
   eslestirilir. Boylece tekrar eden etiketler ("TOP. TESLİM VE HİZ. TUTARI"
   gibi) dogru gruba dusier ve arada eksik/fazla satir olsa da hizalama bozulmaz.
2) Hicbir etiket eslesmezse satirlar konum sirasina gore atanir; bu, etiket
   sutunu olmadan yalnizca rakamlarin yapistirildigi durumu karsilar.
"""
import re

from .satirlar import AYLAR_BUYUK, BEYAN_SATIRLARI, VERI_KODLARI


def _normalize(metin):
    """Etiket karsilastirmasi icin buyuk/kucuk harf, noktalama ve bosluk farklarini siler."""
    metin = (metin or "").upper()
    metin = metin.replace("İ", "I").replace("I", "I").replace("Ş", "S").replace("Ğ", "G")
    metin = metin.replace("Ü", "U").replace("Ö", "O").replace("Ç", "C")
    return re.sub(r"[^A-Z0-9]", "", metin)


_HEDEF_ETIKETLER = [(kod, _normalize(etiket), baslik) for kod, etiket, baslik in BEYAN_SATIRLARI]


def tutar_coz(ham):
    """'1.234,56', '1234.56', '(1.234)', '-' gibi bicimleri float'a cevirir."""
    if ham is None:
        return None
    if isinstance(ham, (int, float)):
        return float(ham)
    metin = str(ham).strip()
    if not metin or metin in {"-", "—", "."}:
        return None
    negatif = metin.startswith("(") and metin.endswith(")")
    metin = metin.strip("()").replace("TL", "").replace("₺", "").replace(" ", "")
    metin = metin.replace(" ", "")
    if not metin:
        return None
    if "," in metin and "." in metin:
        # Hangisi sonda ise ondalik ayracidir
        if metin.rfind(",") > metin.rfind("."):
            metin = metin.replace(".", "").replace(",", ".")
        else:
            metin = metin.replace(",", "")
    elif "," in metin:
        metin = metin.replace(",", ".")
    elif metin.count(".") > 1:
        metin = metin.replace(".", "")
    try:
        deger = float(metin)
    except ValueError:
        return None
    return -deger if negatif else deger


def _hucrelere_bol(satir):
    """Sekme varsa sekmeye, yoksa 2+ bosluga gore boler."""
    if "\t" in satir:
        return [h.strip() for h in satir.split("\t")]
    return [h.strip() for h in re.split(r"\s{2,}", satir.strip())]


def _sayisal_mi(hucre):
    return tutar_coz(hucre) is not None


def _baslik_satiri_mi(hucreler):
    """Ay adlarini iceren 'DÖNEMİ OCAK ŞUBAT ...' satirini tanir."""
    norm = {_normalize(h) for h in hucreler}
    return len(norm & {_normalize(a) for a in AYLAR_BUYUK}) >= 3


# Sistem sorgusunun ust kismindaki kunye alanlari.
# Anahtar: normalize edilmis etiket, deger: donen sozlukteki alan adi.
_KUNYE_ETIKETLERI = {
    "VERGINO": "vkn",
    "VERGIKIMLIKNO": "vkn",
    "TCKIMLIKNO": "tckn",
    "TCKNO": "tckn",
    "UNVAN": "unvan",
    "ADSOYADUNVAN": "unvan",
    "VERGIDAIRESI": "vergi_dairesi",
    "YIL": "yil",
    "DONEMYILI": "yil",
    "RAPORTARIHI": "rapor_tarihi",
}


def _kunye_alani(hucreler):
    """Satir bir kunye alani ise (alan_adi, deger) dondurur, degilse None."""
    if not hucreler or not hucreler[0]:
        return None
    etiket = _normalize(hucreler[0].rstrip(":").strip())
    alan = _KUNYE_ETIKETLERI.get(etiket)
    if alan is None:
        return None
    deger = " ".join(h for h in hucreler[1:] if h).strip()
    return alan, deger


def kunye_ayikla(metin):
    """Yapistirmanin ust kismindaki mukellef ve donem bilgisini okur.

    Sistem sorgusu, beyan tablosunun uzerinde su alanlari tasir:
        VERGİ NO / T.C. KİMLİK NO / UNVAN / VERGİ DAİRESİ / YIL / RAPOR TARİHİ
    Bu alanlar bulunursa mukellef kaydi ve inceleme yili kullaniciya sorulmadan
    doldurulur. Bulunamazsa sozluk bos doner; yapistirma yine calisir.
    """
    kunye = {}
    for satir in (metin or "").replace("\r", "").split("\n"):
        if not satir.strip():
            continue
        bulgu = _kunye_alani(_hucrelere_bol(satir))
        if bulgu is None:
            continue
        alan, deger = bulgu
        # Bos veya yer tutucu degerleri ("-----", "-") yok say
        if not deger or not deger.strip("-. "):
            continue
        if alan == "yil":
            e = re.search(r"(19|20)\d{2}", deger)
            if e:
                kunye["yil"] = int(e.group(0))
            continue
        if alan in ("vkn", "tckn"):
            rakamlar = re.sub(r"\D", "", deger)
            if rakamlar:
                kunye[alan] = rakamlar
            continue
        kunye[alan] = re.sub(r"\s+", " ", deger).strip()
    return kunye


def beyan_ayristir(metin):
    """Yapistirilan metni {satir_kodu: [12 aylik deger]} sozlugune cevirir.

    Donen sozluk: {"degerler": {...}, "uyarilar": [...], "ay_sayisi": n,
                   "kunye": {...}}
    Eslesmeyen satirlar uyari olarak bildirilir; hesaplama yine de yapilabilir.
    """
    ham_satirlar = [s for s in (metin or "").replace("\r", "").split("\n") if s.strip()]
    if not ham_satirlar:
        raise ValueError("Yapıştırılan metin boş.")

    kunye = kunye_ayikla(metin)

    veri_satirlari = []  # (etiket, [12 deger])
    for satir in ham_satirlar:
        hucreler = _hucrelere_bol(satir)
        if not hucreler:
            continue
        if _baslik_satiri_mi(hucreler):
            continue
        # Kunye satirlari tabloya karismasin
        if _kunye_alani(hucreler) is not None:
            continue
        # Etiket sutunu: ilk hucre sayisal degilse etikettir
        if hucreler and not _sayisal_mi(hucreler[0]):
            etiket = hucreler[0]
            sayilar = hucreler[1:]
        else:
            etiket = ""
            sayilar = hucreler
        degerler = [tutar_coz(h) for h in sayilar][:12]
        degerler += [None] * (12 - len(degerler))
        veri_satirlari.append((etiket, degerler))

    if not veri_satirlari:
        raise ValueError("Yapıştırılan metinde veri satırı bulunamadı.")

    etiketli = sum(1 for e, _d in veri_satirlari if e)
    if etiketli >= len(veri_satirlari) / 2:
        sonuc = _etikete_gore_esle(veri_satirlari)
    else:
        sonuc = _konuma_gore_esle(veri_satirlari)
    sonuc["kunye"] = kunye
    return sonuc


def _etikete_gore_esle(veri_satirlari):
    """Etiketleri hedef sirayla ilerleyerek eslestirir."""
    degerler = {}
    uyarilar = []
    imlec = 0
    for etiket, satir_degerleri in veri_satirlari:
        norm = _normalize(etiket)
        if not norm:
            continue
        bulundu = None
        for i in range(imlec, len(_HEDEF_ETIKETLER)):
            kod, hedef_norm, baslik = _HEDEF_ETIKETLER[i]
            if norm == hedef_norm or (len(norm) >= 8 and (norm in hedef_norm or hedef_norm in norm)):
                bulundu = (i, kod, baslik)
                break
        if bulundu is None:
            uyarilar.append(f"Eşleşmeyen satır atlandı: {etiket[:60]}")
            continue
        i, kod, baslik = bulundu
        imlec = i + 1
        if not baslik:
            degerler[kod] = [d if d is not None else 0.0 for d in satir_degerleri]

    eksik = [k for k in VERI_KODLARI if k not in degerler]
    if eksik:
        uyarilar.append(f"{len(eksik)} satır yapıştırmada bulunamadı, sıfır kabul edildi.")
        for kod in eksik:
            degerler[kod] = [0.0] * 12
    return {"degerler": degerler, "uyarilar": uyarilar, "ay_sayisi": _ay_sayisi(degerler)}


def _konuma_gore_esle(veri_satirlari):
    """Etiket sutunu olmadan yapistirilan bloklari sira ile atar.

    Grup basliklari (bos satirlar) yapistirmada yer aliyorsa onlar da sirada
    tuketilir; almiyorsa yalnizca veri satirlari doldurulur.
    """
    degerler = {}
    uyarilar = []
    hedefler = BEYAN_SATIRLARI if len(veri_satirlari) >= len(BEYAN_SATIRLARI) else [
        (kod, "", False) for kod in VERI_KODLARI
    ]
    for (kod, _etiket, baslik), (_e, satir_degerleri) in zip(hedefler, veri_satirlari):
        if baslik:
            continue
        degerler[kod] = [d if d is not None else 0.0 for d in satir_degerleri]

    eksik = [k for k in VERI_KODLARI if k not in degerler]
    if eksik:
        uyarilar.append(
            f"Yapıştırma {len(veri_satirlari)} satır içeriyor; {len(eksik)} satır sıfır kabul edildi."
        )
        for kod in eksik:
            degerler[kod] = [0.0] * 12
    uyarilar.append("Etiket sütunu bulunamadı; satırlar sıraya göre eşleştirildi, kontrol edin.")
    return {"degerler": degerler, "uyarilar": uyarilar, "ay_sayisi": _ay_sayisi(degerler)}


def tek_satir_ayristir(metin):
    """Tek bir satirlik yapistirmayi 12 aylik deger listesine cevirir.

    Kullanici tek bir beyan satirini (ornegin yalnizca 'BU DÖN. AİT İND. KDV')
    duzeltmek istediginde kullanilir. Basta etiket sutunu bulunabilir; satir
    sekme, satir sonu veya 2+ boslukla ayrilmis olabilir.
    """
    ham = (metin or "").replace("\r", "").strip()
    if not ham:
        raise ValueError("Yapıştırılan satır boş.")
    # Dikey (her ay alt alta) yapistirmayi da kabul et
    if "\n" in ham and "\t" not in ham:
        hucreler = [s.strip() for s in ham.split("\n") if s.strip()]
    else:
        hucreler = []
        for parca in ham.split("\n"):
            hucreler.extend(_hucrelere_bol(parca))
    if hucreler and not _sayisal_mi(hucreler[0]):
        hucreler = hucreler[1:]
    degerler = [tutar_coz(h) for h in hucreler if h != ""][:12]
    if not degerler:
        raise ValueError("Yapıştırılan satırda sayı bulunamadı.")
    degerler = [d if d is not None else 0.0 for d in degerler]
    return degerler + [0.0] * (12 - len(degerler))


def _ay_sayisi(degerler):
    """Veri iceren son ayi bulur (yil ici kismi donemler icin)."""
    son = 0
    for ay in range(12):
        if any(abs(degerler.get(kod, [0] * 12)[ay] or 0) > 0 for kod in VERI_KODLARI):
            son = ay + 1
    return son or 12
