"""Sahte belge kullanmaya konu fatura listesi ve satici dokumu.

Portal dokumlerinden okunan ham satirlar burada incelemeye baglanir:

- **Yon**: her satirin VKN'leri mukellefin VKN'siyle karsilastirilir. Alici
  mukellefse fatura bir ALIStir (sahte belge kullanmaya konu olan budur);
  duzenleyen mukellefse SATIStir. VKN tasimayan elle hazirlanmis dokumlerde
  yon belirsiz kalir ve kullanici belirler.
- **Kayit donemi**: KDV indirimi belgenin deftere kaydedildigi donemde
  yapilir; tarhiyat da o doneme yazilir. Yevmiye tarihi varsa donem oradan,
  yoksa fatura tarihinden alinir. Kullanici satir bazinda degistirebilir.
- **Satici**: portal dokumu saticinin yalnizca VKN'sini tasir (dokum onun
  kendi portalindan alinmistir, unvan alani ALICInin unvanidir). Satici
  unvani ve hakkindaki tespit (VTR, ozel esaslar) kullanici tarafindan
  girilir.

Fatura KDV'lerinin donem donem toplami, eleştirideki "İndirilecek KDV'den
çıkarılacak" satirina yazilir. Boylece rapordaki fatura tablosu ile tarhiyat
ozeti ayni veriden gelir ve birbirini tutmak zorunda kalir.
"""
from datetime import date

from .satirlar import AYLAR

# Turkiye'de uygulanan KDV oranlari; disina cikan satir kullaniciya bildirilir
BILINEN_ORANLAR = (0.0, 1.0, 8.0, 10.0, 18.0, 20.0)
ORAN_TOLERANSI = 0.3          # yuzde puan

YON_ALIS = "alis"
YON_SATIS = "satis"
YON_BELIRSIZ = "belirsiz"

YON_ETIKETLERI = {
    YON_ALIS: "Alış (mükellef alıcı)",
    YON_SATIS: "Satış (mükellef düzenleyen)",
    YON_BELIRSIZ: "Belirsiz",
}

# Satici bazinda bilerek/bilmeden ayrimi. Sonucu bastan sona degistirdigi
# icin varsayilani yoktur; kullanici acikca secmelidir.
KULLANMA_SECENEKLERI = ["Belirlenmedi", "Bilmeden kullanma", "Bilerek kullanma"]

SATICI_ALANLARI = [
    {"kod": "unvan", "etiket": "Satıcı unvanı", "tur": "metin"},
    {"kod": "kullanma", "etiket": "Kullanma durumu", "tur": "secim",
     "secenekler": KULLANMA_SECENEKLERI, "varsayilan": "Belirlenmedi"},
    {"kod": "vtr_no", "etiket": "VTR no", "tur": "metin"},
    {"kod": "vtr_tarihi", "etiket": "VTR tarihi", "tur": "tarih"},
    {"kod": "ozel_esaslar", "etiket": "Özel esaslara alınma tarihi", "tur": "tarih"},
    {"kod": "not", "etiket": "Satıcı hakkındaki tespit", "tur": "uzun"},
]


def _tarihi_coz(metin):
    """ISO tarihten (yil, ay) uretir; cozulemezse None."""
    parcalar = str(metin or "").split("-")
    if len(parcalar) < 2:
        return None
    try:
        return int(parcalar[0]), int(parcalar[1])
    except ValueError:
        return None


def _vkn(deger):
    return "".join(ch for ch in str(deger or "") if ch.isdigit())


def yonu_belirle(fatura, mukellef_vkn):
    """Faturanin alis mi satis mi oldugunu VKN karsilastirmasiyla bulur."""
    mukellef = _vkn(mukellef_vkn)
    if not mukellef:
        return YON_BELIRSIZ
    if _vkn(fatura.get("alici_vkn")) == mukellef:
        return YON_ALIS
    if _vkn(fatura.get("duzenleyen_vkn")) == mukellef:
        return YON_SATIS
    return YON_BELIRSIZ


def normalize(ham_faturalar, mukellef_vkn=None):
    """Ham fatura satirlarini calismada saklanacak bicime getirir.

    Kullanicinin elle degistirdigi alanlar (yon, kayit donemi, dahil) varsa
    korunur; yalnizca bos olanlar veriden turetilir.
    """
    sonuc = []
    for ham in ham_faturalar or []:
        f = dict(ham)
        f.setdefault("iptal", False)

        if not f.get("yon"):
            f["yon"] = yonu_belirle(f, mukellef_vkn)

        if not f.get("kayit_yil") or not f.get("kayit_ay"):
            # Once yevmiye tarihi: KDV indirimi kayit doneminde yapilir
            donem = _tarihi_coz(f.get("yevmiye_tarih")) or _tarihi_coz(f.get("tarih"))
            if donem:
                f["kayit_yil"], f["kayit_ay"] = donem
            else:
                f["kayit_yil"], f["kayit_ay"] = None, None

        if "dahil" not in f:
            # Iptal edilmis ve alis olmayan belgeler bastan disarida kalir;
            # kullanici isterse geri alir.
            f["dahil"] = bool(f["yon"] == YON_ALIS and not f["iptal"])

        f["satici_vkn"] = (_vkn(f.get("duzenleyen_vkn")) if f["yon"] != YON_SATIS
                           else _vkn(f.get("alici_vkn")))
        sonuc.append(f)
    return sonuc


def kdv_orani(fatura):
    """Faturanin ima ettigi KDV oranini yuzde olarak verir; matrah yoksa None."""
    matrah = float(fatura.get("matrah") or 0.0)
    if abs(matrah) < 0.005:
        return None
    return round(float(fatura.get("kdv") or 0.0) / matrah * 100.0, 2)


def satici_ozeti(faturalar, saticilar=None):
    """Satici bazinda fatura adedi ve tutar toplamlari.

    Yalnizca dahil edilen alis faturalari sayilir; rapordaki satici tablosu
    ile tarhiyat ayni kumeden gelsin.
    """
    saticilar = saticilar or {}
    gruplar = {}
    for f in faturalar or []:
        if not f.get("dahil"):
            continue
        vkn = f.get("satici_vkn") or ""
        grup = gruplar.setdefault(vkn, {
            "vkn": vkn, "adet": 0, "matrah": 0.0, "kdv": 0.0, "toplam": 0.0,
            "donemler": set(),
        })
        grup["adet"] += 1
        grup["matrah"] += float(f.get("matrah") or 0.0)
        grup["kdv"] += float(f.get("kdv") or 0.0)
        grup["toplam"] += float(f.get("toplam") or 0.0)
        if f.get("kayit_yil") and f.get("kayit_ay"):
            grup["donemler"].add((f["kayit_yil"], f["kayit_ay"]))

    satirlar = []
    for vkn, grup in gruplar.items():
        bilgi = saticilar.get(vkn) or {}
        donemler = sorted(grup.pop("donemler"))
        grup.update({
            "unvan": bilgi.get("unvan") or "",
            "kullanma": bilgi.get("kullanma") or "Belirlenmedi",
            "vtr_no": bilgi.get("vtr_no") or "",
            "vtr_tarihi": bilgi.get("vtr_tarihi") or "",
            "ozel_esaslar": bilgi.get("ozel_esaslar") or "",
            "not": bilgi.get("not") or "",
            "matrah": round(grup["matrah"], 2),
            "kdv": round(grup["kdv"], 2),
            "toplam": round(grup["toplam"], 2),
            "donem_sayisi": len(donemler),
            "ilk_donem": "%d/%s" % (donemler[0][0], AYLAR[donemler[0][1] - 1])
                         if donemler else "",
            "son_donem": "%d/%s" % (donemler[-1][0], AYLAR[donemler[-1][1] - 1])
                         if donemler else "",
        })
        satirlar.append(grup)
    satirlar.sort(key=lambda s: (-s["kdv"], s["vkn"]))
    return satirlar


def donem_ozeti(faturalar):
    """Dahil edilen alis faturalarinin donem donem toplami.

    Doner: {yil: {ay(1-12): {"adet", "matrah", "kdv"}}}
    """
    ozet = {}
    for f in faturalar or []:
        if not f.get("dahil"):
            continue
        yil, ay = f.get("kayit_yil"), f.get("kayit_ay")
        if not yil or not ay or not (1 <= int(ay) <= 12):
            continue
        hucre = ozet.setdefault(int(yil), {}).setdefault(int(ay), {
            "adet": 0, "matrah": 0.0, "kdv": 0.0})
        hucre["adet"] += 1
        hucre["matrah"] += float(f.get("matrah") or 0.0)
        hucre["kdv"] += float(f.get("kdv") or 0.0)
    for aylar in ozet.values():
        for hucre in aylar.values():
            hucre["matrah"] = round(hucre["matrah"], 2)
            hucre["kdv"] = round(hucre["kdv"], 2)
    return ozet


def indirim_dizileri(faturalar):
    """Her yil icin 12 elemanli "indirilecek KDV'den cikarilacak" dizisi."""
    ozet = donem_ozeti(faturalar)
    diziler = {}
    for yil, aylar in ozet.items():
        dizi = [0.0] * 12
        for ay, hucre in aylar.items():
            dizi[ay - 1] = hucre["kdv"]
        diziler[yil] = dizi
    return diziler


def uygulama_farki(faturalar, yillar):
    """Fatura toplami ile calismadaki elestiri girdisini karsilastirir.

    Fatura listesi tarhiyata otomatik yazilabildigi icin, elle girilmis bir
    tutarin sessizce ezilmesi ya da iki kaynagin birbirinden ayrilmasi
    tehlikelidir. Bu yuzden fark satir satir bildirilir.
    """
    diziler = indirim_dizileri(faturalar)
    mevcut = {}
    for yil_kaydi in yillar or []:
        try:
            yil = int(yil_kaydi.get("yil"))
        except (TypeError, ValueError):
            continue
        elestiri = yil_kaydi.get("elestiri") or {}
        dizi = list(elestiri.get("indirim_cikar") or [])
        mevcut[yil] = [float(d or 0.0) for d in (dizi + [0.0] * 12)[:12]]

    farklar = []
    for yil in sorted(set(diziler) | set(mevcut)):
        fatura_dizi = diziler.get(yil) or [0.0] * 12
        mevcut_dizi = mevcut.get(yil) or [0.0] * 12
        for ay in range(12):
            fark = round(fatura_dizi[ay] - mevcut_dizi[ay], 2)
            if abs(fark) > 0.005:
                farklar.append({
                    "yil": yil, "ay": ay + 1, "ay_adi": AYLAR[ay],
                    "fatura": round(fatura_dizi[ay], 2),
                    "mevcut": round(mevcut_dizi[ay], 2),
                    "fark": fark,
                    "yil_var": yil in mevcut,
                })
    return farklar


def bulgular(faturalar, yillar=None, saticilar=None):
    """Fatura listesindeki dikkat gerektiren noktalari bildirir.

    Bunlar birer hata degil, kullaniciya "buraya bak" demektir; hicbiri
    kendiliginden veriyi degistirmez.
    """
    saticilar = saticilar or {}
    bilinen_yillar = {int(y.get("yil")) for y in (yillar or [])
                      if str(y.get("yil") or "").isdigit()}
    sonuc = []
    gorulen_no = {}

    for f in faturalar or []:
        etiket = f.get("fatura_no") or f.get("uuid") or "(numarasız)"

        if f.get("iptal") and f.get("dahil"):
            sonuc.append({"tur": "iptal", "fatura": etiket,
                          "mesaj": "%s iptal/itiraz listesinde görünüyor ama "
                                   "tarhiyata dahil edilmiş." % etiket})

        yevmiye = _tarihi_coz(f.get("yevmiye_tarih"))
        fatura_tarihi = f.get("tarih")
        if yevmiye and fatura_tarihi and f.get("yevmiye_tarih") < fatura_tarihi:
            sonuc.append({"tur": "yevmiye_tarihi", "fatura": etiket,
                          "mesaj": "%s: yevmiye tarihi (%s) fatura tarihinden "
                                   "(%s) önce." % (etiket, f["yevmiye_tarih"],
                                                   fatura_tarihi)})

        oran = kdv_orani(f)
        if oran is not None and f.get("dahil"):
            if not any(abs(oran - o) <= ORAN_TOLERANSI for o in BILINEN_ORANLAR):
                sonuc.append({"tur": "kdv_orani", "fatura": etiket,
                              "mesaj": "%s: KDV oranı %%%s çıkıyor; bilinen "
                                       "oranlardan biri değil." % (etiket, oran)})

        if f.get("dahil") and not (f.get("kayit_yil") and f.get("kayit_ay")):
            sonuc.append({"tur": "donem_yok", "fatura": etiket,
                          "mesaj": "%s: kayıt dönemi belirlenemedi; tarhiyata "
                                   "yazılamaz." % etiket})
        elif f.get("dahil") and bilinen_yillar and f.get("kayit_yil") not in bilinen_yillar:
            sonuc.append({"tur": "yil_disi", "fatura": etiket,
                          "mesaj": "%s: kayıt dönemi %s, ancak bu yıl için beyan "
                                   "verisi yüklenmemiş." % (etiket, f["kayit_yil"])})

        if f.get("fatura_no"):
            anahtar = (f["fatura_no"].upper(), f.get("satici_vkn") or "")
            gorulen_no[anahtar] = gorulen_no.get(anahtar, 0) + 1

    for (no, _vkn_), adet in gorulen_no.items():
        if adet > 1:
            sonuc.append({"tur": "yinelenen", "fatura": no,
                          "mesaj": "%s numaralı fatura listede %d kez var." % (no, adet)})

    for satici in satici_ozeti(faturalar, saticilar):
        if satici["kullanma"] == "Belirlenmedi":
            sonuc.append({
                "tur": "kullanma_secilmedi", "fatura": satici["vkn"],
                "mesaj": "%s VKN'li satıcı için bilerek/bilmeden kullanma "
                         "belirlenmemiş. Bu seçim vergi ziyaı cezasının 1 kat mı "
                         "3 kat mı uygulanacağını belirler."
                         % (satici["vkn"] or "(VKN yok)")})
        if not satici["unvan"]:
            sonuc.append({"tur": "unvan_yok", "fatura": satici["vkn"],
                          "mesaj": "%s VKN'li satıcının unvanı girilmemiş; "
                                   "belgelerde boş kalır." % (satici["vkn"] or "(VKN yok)")})
    return sonuc


def toplamlar(faturalar):
    """Dahil edilen alis faturalarinin genel toplami."""
    dahil = [f for f in (faturalar or []) if f.get("dahil")]
    return {
        "adet": len(dahil),
        "matrah": round(sum(float(f.get("matrah") or 0.0) for f in dahil), 2),
        "kdv": round(sum(float(f.get("kdv") or 0.0) for f in dahil), 2),
        "toplam": round(sum(float(f.get("toplam") or 0.0) for f in dahil), 2),
        "toplam_satir": len(faturalar or []),
    }
