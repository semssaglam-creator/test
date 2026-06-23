"""Toplu tahakkuk PDF dosyalarini okur (vendored pypdf).

PDF, Excel'in yazici ciktisidir; ayni sutunlari icerir. Metin satir satir
cozulur ve guclu capa alanlar (12 haneli vergi donemi, harf+rakam iceren
tahakkuk fis no) yardimiyla ayristirilir. Vergi kodu/tutar disindaki alanlar
bos satirlarda bir ustteki degerden tasinir (excel_okuyucu ile ortak mantik).

Not: Bu ayristirici Excel sutun duzenine gore ayarlanmistir. PDF bicimi cok
farkliysa Excel yuklemeniz onerilir.
"""
import re

from .excel_okuyucu import OkumaHatasi, kayitlardan_uret

_FIS_RE = re.compile(r"^\d{3,}[A-Za-z]{1,}\w*\d+$")  # ornek: 2026062001AAA0000001
_DONEM_RE = re.compile(r"^\d{12}$")
_VKN_RE = re.compile(r"^\d{10,11}$")
_KOD_RE = re.compile(r"^\d{3,4}$")
# Para: TR (1.234,56 / 939,70) veya US (1234.56) ondalik AYRACI ZORUNLU.
# Boylece kod/numara gibi tam sayilar yanlislikla tutar sayilmaz.
_PARA_RE = re.compile(r"^-?\d{1,3}(\.\d{3})*,\d{1,2}$|^-?\d+,\d{1,2}$|^-?\d+\.\d{1,2}$")
_ATLA = ("vergi kimlik", "tahakkuk fis", "odenecek", "toplam", "sayfa", "plaka")


def _pdf_metni(icerik):
    from pypdf import PdfReader

    import io
    try:
        okuyucu = PdfReader(io.BytesIO(icerik))
    except Exception as exc:  # noqa: BLE001
        raise OkumaHatasi(f"PDF dosyasi okunamadi: {exc}")
    parcalar = []
    for sayfa in okuyucu.pages:
        try:
            parcalar.append(sayfa.extract_text() or "")
        except Exception:  # noqa: BLE001 - tek sayfa hatasi tum dosyayi durdurmasin
            continue
    return "\n".join(parcalar)


def _para_mi(token):
    return bool(_PARA_RE.match(token))


def _satir_coz(tokenler):
    """Bir metin satirindaki tokenlerden alan->deger dict uretir (cozulebildigi kadar)."""
    if not tokenler:
        return None

    donem_idx = next((i for i, t in enumerate(tokenler) if _DONEM_RE.match(t)), None)
    fis = next((t for t in tokenler if _FIS_RE.match(t)), None)

    # Tutar: en sagdaki ondalikli para token'i (kod/numara karismaz).
    tutar = next((t for t in reversed(tokenler) if _para_mi(t)), None)

    # Vergi kodu: donem varsa ondan sonraki ilk 3-4 haneli kod; yoksa
    # (devam satiri) ilk 3-4 haneli kod. Tutar token'i kod sayilmaz.
    baslangic = (donem_idx + 1) if donem_idx is not None else 0
    vergi_kodu = None
    for t in tokenler[baslangic:]:
        if t == tutar:
            break
        if _KOD_RE.match(t) and not _VKN_RE.match(t):
            vergi_kodu = t
            break

    vkn = next((t for t in tokenler if _VKN_RE.match(t)), None)
    donem = tokenler[donem_idx] if donem_idx is not None else None

    # 4 haneli islem/thk turu: fis ile donem arasindaki kodlar (varsa).
    islem = thk = None
    if fis is not None and donem_idx is not None:
        try:
            fis_idx = tokenler.index(fis)
        except ValueError:
            fis_idx = -1
        aradakiler = [t for t in tokenler[fis_idx + 1:donem_idx] if _KOD_RE.match(t)]
        if len(aradakiler) >= 1:
            islem = aradakiler[0]
        if len(aradakiler) >= 2:
            thk = aradakiler[1]

    # Gecerli bir tahakkuk satiri icin hem vergi kodu hem de para tutari sart.
    # Boylece baslik/aciklama/kod-listesi gibi satirlar elenir.
    if vergi_kodu is None or tutar is None:
        return None

    return {
        "vergi_kimlik_no": vkn,
        "tahakkuk_fis_no": fis,
        "islem_turu": islem,
        "thk_turu": thk,
        "vergi_donemi": donem,
        "vergi_kodu": vergi_kodu,
        "odenecek_tutar": tutar,
    }


def pdf_oku(icerik, dosya_adi=""):
    """PDF icerigini (bytes) okuyup kayit dict listesi dondurur."""
    metin = _pdf_metni(icerik)
    if not metin.strip():
        raise OkumaHatasi("PDF'ten metin cikarilamadi (taranmis/resim PDF olabilir).")

    ham_satirlar = []
    for satir in metin.splitlines():
        s = satir.strip()
        if not s:
            continue
        # Baslik/altbilgi satirlarini atla.
        dusuk = s.lower()
        if any(a in dusuk for a in _ATLA) and not any(_FIS_RE.match(t) for t in s.split()):
            continue
        coz = _satir_coz(s.split())
        if coz:
            ham_satirlar.append(coz)

    kayitlar = kayitlardan_uret(ham_satirlar)
    if not kayitlar:
        raise OkumaHatasi(
            "PDF'te okunabilir tahakkuk satiri bulunamadi. Lutfen Excel yukleyin "
            "veya ornek PDF paylasin ki ayristirici ayarlanabilsin."
        )
    return kayitlar
