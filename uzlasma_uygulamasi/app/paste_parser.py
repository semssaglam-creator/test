"""Dijital Vergi Dairesi uzlasma talep dilekcesinden kopyalanan metni ayristirir.

Beklenen metin, dilekce PDF'inden secilip kopyalanan ham metindir. Asagidaki
bilgileri cikarmaya calisir:
  - Mukellef bilgileri (Ad Soyad/Unvan, Adres, VKN/TCKN, Telefon, Onay Zamani)
  - Teblig edilen ihbarnameler (fis no, duzenleme tarihi, teblig tarihi)
  - Ceza satirlari (fis no, vergi turu kodu, ceza kodu, ceza nedeni, miktar)
"""
import re

FIS_NO_RE = r"[0-9]{8,12}[A-Za-zÇĞİÖŞÜçğıöşü]{2,4}[0-9]{6,8}"

ALAN_ETIKETLERI = [
    "Ad Soyad / Ünvan",
    "Açık Adres",
    "Vergi Kimlik Numarası",
    "T.C. Kimlik Numarası",
    "Cep Telefonu",
    "Onay Zamanı",
    "Dijital VD İşlem Numarası",
]


def _alanlari_ayikla(metin):
    """':' ile ayrilan etiket: deger alanlarini, coklu satira yayilsa bile bulur."""
    sonuc = {}
    etiket_pattern = "|".join(re.escape(e) for e in ALAN_ETIKETLERI)
    # Her etiketin basladigi pozisyonu bul
    eslesmeler = list(re.finditer(rf"({etiket_pattern})\s*:\s*", metin))
    for i, m in enumerate(eslesmeler):
        etiket = m.group(1)
        baslangic = m.end()
        bitis = eslesmeler[i + 1].start() if i + 1 < len(eslesmeler) else len(metin)
        deger = metin[baslangic:bitis].strip()
        deger = re.sub(r"\s+", " ", deger)
        sonuc[etiket] = deger
    return sonuc


def mukellef_bilgisi_ayikla(metin):
    alanlar = _alanlari_ayikla(metin)
    vkn_tckn = alanlar.get("Vergi Kimlik Numarası") or alanlar.get("T.C. Kimlik Numarası") or ""
    return {
        "ad_unvan": alanlar.get("Ad Soyad / Ünvan", ""),
        "adres": alanlar.get("Açık Adres", ""),
        "vkn_tckn": vkn_tckn,
        "telefon": alanlar.get("Cep Telefonu", ""),
        "onay_zamani": alanlar.get("Onay Zamanı", ""),
    }


def ihbarname_tarihleri_ayikla(metin):
    """Teblig Edilen Ihbarnameler tablosundaki satirlari bulur.

    Donus: {fis_no: {"duzenleme_tarihi": ..., "teblig_tarihi": ...}}
    """
    sonuc = {}
    pattern = rf"({FIS_NO_RE})\s+([0-9]{{12}})\s+([0-9]{{8}})"
    for m in re.finditer(pattern, metin):
        fis_no, duzenleme, teblig = m.groups()
        sonuc[fis_no] = {"duzenleme_tarihi": duzenleme, "teblig_tarihi": teblig}
    return sonuc


def ceza_satirlari_ayikla(metin):
    """Ceza Satirlari tablosundaki satirlari bulur.

    Donus: liste of dict(fis_no, vergi_turu_kod, ceza_kodu, ceza_nedeni, miktar)
    """
    sonuc = []
    pattern = rf"({FIS_NO_RE})\s+([0-9]{{4}})\s+([0-9]{{4}})\s+(.+?)\s+([0-9]+(?:[.,][0-9]+)?)(?=\s*(?:{FIS_NO_RE}|\Z))"
    for m in re.finditer(pattern, metin, re.DOTALL):
        fis_no, vergi_turu, ceza_kodu, neden, miktar = m.groups()
        neden = re.sub(r"\s+", " ", neden).strip()
        miktar = float(miktar.replace(",", "."))
        sonuc.append({
            "fis_no": fis_no,
            "vergi_turu_kod": vergi_turu,
            "ceza_kodu": ceza_kodu,
            "ceza_nedeni": neden,
            "miktar": miktar,
        })
    return sonuc


def dilekce_ayristir(metin):
    """Tum dilekce metnini ayristirip yapilandirilmis bir sozluk dondurur."""
    mukellef = mukellef_bilgisi_ayikla(metin)
    ihbarname_tarihleri = ihbarname_tarihleri_ayikla(metin)
    ceza_satirlari = ceza_satirlari_ayikla(metin)

    # Fis no -> ceza satirlari grubu
    ihbarnameler = {}
    for fis_no, tarihler in ihbarname_tarihleri.items():
        ihbarnameler[fis_no] = {
            "fis_no": fis_no,
            "duzenleme_tarihi": tarihler["duzenleme_tarihi"],
            "teblig_tarihi": tarihler["teblig_tarihi"],
            "ceza_satirlari": [],
        }
    for satir in ceza_satirlari:
        fis_no = satir["fis_no"]
        if fis_no not in ihbarnameler:
            ihbarnameler[fis_no] = {
                "fis_no": fis_no,
                "duzenleme_tarihi": "",
                "teblig_tarihi": "",
                "ceza_satirlari": [],
            }
        ihbarnameler[fis_no]["ceza_satirlari"].append(satir)

    return {
        "mukellef": mukellef,
        "ihbarnameler": list(ihbarnameler.values()),
    }
