"""Dijital Vergi Dairesi uzlasma dilekcesi metnini ayristirir.

Metin iki kaynaktan gelebilir:
- PDF dosyasinin uygulamaya yuklenmesi (pypdf ile metin cikarilir)
- Kullanicinin PDF goruntuleyiciden kopyalayip yapistirdigi metin

Iki kaynak da ayni alanlari icerir ancak satir bolunmeleri farklilasabilir;
bu yuzden ayristirma satir duzenine degil, alan kaliplarina dayanir.
"""
import re

# Ornek: 2026041113EvU0000001
FIS_NO_RE = r"\d{10}Ev[A-Z]\d{7}"

_ALAN_ETIKETLERI = (
    "Ad Soyad / Ünvan",
    "Açık Adres",
    "Vergi Kimlik Numarası",
    "T.C. Kimlik Numarası",
    "Cep Telefonu",
    "Onay Zamanı",
    "Dijital VD İşlem Numarası",
)


def _alan_degeri(metin, etiket):
    """'Etiket : deger' kalibini yakalar; deger bir sonraki etikete kadar surebilir."""
    digerleri = "|".join(re.escape(e) for e in _ALAN_ETIKETLERI if e != etiket)
    kalip = re.escape(etiket) + r"\s*:\s*(.*?)(?=(?:" + digerleri + r")\s*:|TEBLİĞ EDİLEN|$)"
    e = re.search(kalip, metin, re.DOTALL)
    if not e:
        return ""
    return re.sub(r"\s+", " ", e.group(1)).strip()


def _tarih_12(ham):
    """'202606021036' -> '02.06.2026' (saat bilgisi atilir)."""
    if len(ham) >= 8:
        return f"{ham[6:8]}.{ham[4:6]}.{ham[0:4]}"
    return ham


def _tarih_8(ham):
    """'20260522' -> '22.05.2026'."""
    if len(ham) == 8:
        return f"{ham[6:8]}.{ham[4:6]}.{ham[0:4]}"
    return ham


def mukellef_bilgisi_ayikla(metin):
    vkn = _alan_degeri(metin, "Vergi Kimlik Numarası") or _alan_degeri(metin, "T.C. Kimlik Numarası")
    vkn = re.sub(r"\D", "", vkn)
    return {
        "ad_unvan": _alan_degeri(metin, "Ad Soyad / Ünvan"),
        "adres": _alan_degeri(metin, "Açık Adres"),
        "vkn_tckn": vkn,
        "telefon": re.sub(r"\D", "", _alan_degeri(metin, "Cep Telefonu")),
        "onay_zamani": _alan_degeri(metin, "Onay Zamanı"),
    }


def ihbarname_tarihleri_ayikla(metin):
    """Teblig tablosu satirlari: fisno + 12 haneli duzenleme + 8 haneli teblig."""
    tarihler = {}
    for e in re.finditer(rf"({FIS_NO_RE})\s+(\d{{12}})\s+(\d{{8}})", metin):
        tarihler[e.group(1)] = {
            "duzenleme_tarihi": _tarih_12(e.group(2)),
            "teblig_tarihi": _tarih_8(e.group(3)),
        }
    return tarihler


def _tutar_cevir(ham):
    """'1593.9', '17000.0', '17.000,50', '1.593' gibi bicimleri float'a cevirir."""
    ham = ham.strip().rstrip(".,")
    if "," in ham:
        # Turkce bicim: nokta binlik, virgul ondalik
        return float(ham.replace(".", "").replace(",", "."))
    if ham.count(".") > 1:
        # Birden cok nokta: hepsi binlik ayraci
        return float(ham.replace(".", ""))
    return float(ham)


def ceza_satirlari_ayikla(metin):
    """Ceza satirlari: fisno [vergi turu] ceza kodu ... tutar.

    Bir satirin govdesi (ceza nedeni) PDF'te birden cok satira bolunebilir;
    tutar govdenin sonundaki son sayidir. Vergi turu kolonu bos olabilir.
    """
    # Teblig tablosu satirlarini ele; kalan fisno gecisleri ceza satiri adayidir
    temiz = re.sub(rf"({FIS_NO_RE})\s+\d{{12}}\s+\d{{8}}", "", metin)
    # Dilekce paragrafindaki "fisno, fisno, ... fis nolu" sayimlarini da ele
    temiz = re.sub(rf"({FIS_NO_RE})\s*,", "", temiz)

    satirlar = []
    kalip = re.compile(
        rf"({FIS_NO_RE})\s+(\d{{4}})(?![\d.,])(?:\s+(\d{{4}})(?![\d.,]))?(.*?)"
        rf"(?=(?:{FIS_NO_RE})\s*\d{{4}}|Bu belge|\Z)",
        re.DOTALL,
    )
    for e in kalip.finditer(temiz):
        fis_no, kod1, kod2, govde = e.group(1), e.group(2), e.group(3), e.group(4) or ""
        if kod2:
            vergi_turu, ceza_kodu = kod1, kod2
        elif kod1.startswith("3"):
            vergi_turu, ceza_kodu = "", kod1     # tek kod ceza kodudur (3xxx)
        else:
            vergi_turu, ceza_kodu = kod1, ""

        # Tutar: govdedeki ondalikli son sayi ("341. Madde" gibi yasal metin
        # sayilariyla karismamasi icin ondalik kismi zorunlu tutulur)
        sayilar = re.findall(r"\d[\d.]*[.,]\d+", govde)
        miktar = 0.0
        ceza_nedeni = govde
        if sayilar:
            ham = sayilar[-1]
            son = govde.rfind(ham)
            ceza_nedeni = govde[:son]
            miktar = _tutar_cevir(ham)
        else:
            # Ondalikli sayi yoksa govdenin son belirteci tam sayi tutar olabilir
            son_kelime = govde.strip().split()[-1] if govde.strip() else ""
            if re.fullmatch(r"\d{3,}", son_kelime):
                miktar = float(son_kelime)
                ceza_nedeni = govde[:govde.rfind(son_kelime)]

        ceza_nedeni = re.sub(r"\s+", " ", ceza_nedeni).strip(" -:")
        satirlar.append({
            "fis_no": fis_no,
            "vergi_turu_kod": vergi_turu,
            "ceza_kodu": ceza_kodu,
            "ceza_nedeni": ceza_nedeni,
            "miktar": miktar,
        })
    return satirlar


def dilekce_ayristir(metin):
    """Dilekce metnini mukellef + ihbarname listesine cevirir."""
    metin = metin or ""
    mukellef = mukellef_bilgisi_ayikla(metin)
    tarihler = ihbarname_tarihleri_ayikla(metin)
    ceza_satirlari = ceza_satirlari_ayikla(metin)

    ihbarnameler = []
    sira = {}
    for satir in ceza_satirlari:
        fis_no = satir["fis_no"]
        if fis_no not in sira:
            t = tarihler.get(fis_no, {})
            sira[fis_no] = {
                "fis_no": fis_no,
                "duzenleme_tarihi": t.get("duzenleme_tarihi", ""),
                "teblig_tarihi": t.get("teblig_tarihi", ""),
                "ceza_satirlari": [],
            }
            ihbarnameler.append(sira[fis_no])
        sira[fis_no]["ceza_satirlari"].append({k: v for k, v in satir.items() if k != "fis_no"})

    # Ceza satiri bulunamayan ama teblig tablosunda olan ihbarnameler de eklensin
    for fis_no, t in tarihler.items():
        if fis_no not in sira:
            ihbarnameler.append({
                "fis_no": fis_no,
                "duzenleme_tarihi": t.get("duzenleme_tarihi", ""),
                "teblig_tarihi": t.get("teblig_tarihi", ""),
                "ceza_satirlari": [],
            })

    return {"mukellef": mukellef, "ihbarnameler": ihbarnameler}


def pdf_metni_cikar(pdf_bytes):
    """PDF dosya icereginden metin cikarir (gomulu pypdf ile)."""
    import io
    import pypdf
    okuyucu = pypdf.PdfReader(io.BytesIO(pdf_bytes))
    return "\n".join((sayfa.extract_text() or "") for sayfa in okuyucu.pages)
