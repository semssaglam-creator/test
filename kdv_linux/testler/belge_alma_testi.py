# -*- coding: utf-8 -*-
"""VUK 353/1 belge alma ozel usulsuzlugunun gerileme denetimi.

    python3 testler/belge_alma_testi.py

Olcut, mufettisin verdigi ORNEK RAPORUN kendi rakamlari: ornegin 131
satirlik tablosundan secilen satirlar ve TOPLAM satiri buraya aynen
alinmistir. Hesap bu rakamlari tutmuyorsa bozulmus demektir.

Ornekten cikan ve kolay kacirilan uc kural:

  - Alt sinir YIL ICINDE degisiyor: 2022'de 7417 sayili Kanunla 01.08.2022
    itibariyle 500 TL'den 1.000 TL'ye cikti. Yil bazli tek bir alan bu yili
    yanlis hesaplar, bu yuzden hadler TARIH ARALIKLI tutuluyor.
  - Ceza = max(tutarin %10'u, alt sinir). Ornegin 105. satiri bunu
    gosteriyor: %10 = 974,68 < 1.000 oldugu icin ceza 1.000,00 yazilmis.
  - Hadler TL biciminde yaziliyor ("1.000", "190.000"). `tutar_coz` bunlari
    1,0 ve 190,0 diye okuyor; bu yuzden hadler icin ayri bir cozucu var.
"""
import os
import sys

KOK = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, KOK)

from app import faturalar as F                                       # noqa: E402
from app import inceleme_kunyesi as ik                               # noqa: E402

HATA = []


def denetle(kosul, aciklama):
    if kosul:
        print("  [ok] %s" % aciklama)
    else:
        print("  [HATA] %s" % aciklama)
        HATA.append(aciklama)


def esit(bulunan, beklenen, aciklama):
    denetle(abs(float(bulunan or 0.0) - beklenen) < 0.005,
            "%s (beklenen %s, bulunan %s)" % (aciklama, beklenen, bulunan))


# Ornek rapordaki 2022 hadleri. Mufettisin kunyeye yazacagi bicimde.
HADLER_METNI = ("01.01.2022 | 31.07.2022 | 500 | 190.000\n"
                "01.08.2022 |  | 1.000 | 500.000")

# Ornek tablodan secilen satirlar: (sira, tarih, fatura no, tutar, ceza).
# Ilk ucu alt sinirin ustunde, sonraki ikisi 01.08 sonrasi, son ikisi
# alt sinirin ALTINDA kalip alt sinira yuvarlanan satirlar.
ORNEK_SATIRLAR = [
    (1, "2022-01-17", "GIB-190", 30385.00, 3038.50),
    (15, "2022-01-31", "GIB-37", 13776.50, 1377.65),
    (50, "2022-05-17", "GIB-459", 84370.00, 8437.00),
    (78, "2022-08-02", "GIB-778", 14396.00, 1439.60),
    (89, "2022-08-22", "GIB-789", 16267.80, 1626.78),
    (105, "2022-09-26", "GIB-677", 9746.80, 1000.00),   # %10 = 974,68 < 1.000
    (110, "2022-10-10", "GIB-46", 7552.00, 1000.00),    # %10 = 755,20 < 1.000
]
ORNEK_TOPLAM_TUTAR = 2352614.70
ORNEK_TOPLAM_CEZA = 236943.99


# Mufettisin ornek raporundaki 131 satirlik tablonun TAMAMI:
#   fatura tarihi (ISO) | fatura no | belge toplam tutari | kesilen ceza
# Son iki sutun ornegin KENDI rakamlari. Bu blok, uygulamanin gercek bir
# raporu birebir uretebildiginin capasidir; 7 ornek satir kurallari
# gosteriyor, bu tablo ise 131 gercek tarih uzerinde donem sinirlarinin
# dogru calistigini gosteriyor (01.08.2022 gecisi 77/78. satirlarda).
ORNEK_TABLO = """\
2022-01-17 GIB-190 30.385,00 3.038,50
2022-01-18 GIB-191 28.910,00 2.891,00
2022-01-19 GIB-192 32.922,00 3.292,20
2022-01-20 GIB-193 28.438,00 2.843,80
2022-01-21 GIB-194 29.500,00 2.950,00
2022-01-22 GIB-195 28.910,00 2.891,00
2022-01-24 GIB-196 27.730,00 2.773,00
2022-01-25 GIB-197 29.382,00 2.938,20
2022-01-26 GIB-198 29.795,00 2.979,50
2022-01-27 GIB-199 28.969,00 2.896,90
2022-01-28 GIB-200 28.851,00 2.885,10
2022-01-29 GIB-201 28.320,00 2.832,00
2022-01-31 GIB-202 31.860,00 3.186,00
2022-01-28 GIB-36 28.320,00 2.832,00
2022-01-31 GIB-37 13.776,50 1.377,65
2022-02-02 GIB-113 12.862,00 1.286,20
2022-02-04 GIB-114 11.800,00 1.180,00
2022-02-07 GIB-115 12.390,00 1.239,00
2022-02-10 GIB-116 12.803,00 1.280,30
2022-02-14 GIB-117 11.092,00 1.109,20
2022-02-16 GIB-118 11.210,00 1.121,00
2022-02-18 GIB-119 13.098,00 1.309,80
2022-02-19 GIB-120 12.626,00 1.262,60
2022-02-21 GIB-121 11.505,00 1.150,50
2022-02-23 GIB-122 11.387,00 1.138,70
2022-02-25 GIB-123 13.452,00 1.345,20
2022-02-28 GIB-124 13.570,00 1.357,00
2022-04-01 GIB-451 14.632,00 1.463,20
2022-04-02 GIB-452 16.992,00 1.699,20
2022-04-04 GIB-453 17.228,00 1.722,80
2022-04-05 GIB-454 16.402,00 1.640,20
2022-04-06 GIB-455 16.284,00 1.628,40
2022-04-07 GIB-456 18.124,80 1.812,48
2022-04-08 GIB-457 17.464,00 1.746,40
2022-04-09 GIB-458 16.520,00 1.652,00
2022-04-11 GIB-459 15.930,00 1.593,00
2022-04-12 GIB-460 16.579,00 1.657,90
2022-04-13 GIB-461 16.874,00 1.687,40
2022-04-14 GIB-462 16.992,00 1.699,20
2022-04-15 GIB-463 18.880,00 1.888,00
2022-04-16 GIB-464 18.762,00 1.876,20
2022-04-18 GIB-465 18.231,00 1.823,10
2022-04-19 GIB-466 16.520,00 1.652,00
2022-04-20 GIB-467 21.240,00 2.124,00
2022-04-21 GIB-468 18.644,00 1.864,40
2022-04-22 GIB-469 21.771,00 2.177,10
2022-04-25 GIB-470 18.172,00 1.817,20
2022-04-26 GIB-471 15.930,00 1.593,00
2022-04-28 GIB-472 15.340,00 1.534,00
2022-05-17 GIB-459 84.370,00 8.437,00
2022-05-18 GIB-463 73.160,00 7.316,00
2022-05-19 GIB-468 63.720,00 6.372,00
2022-07-01 GIB-181 14.278,00 1.427,80
2022-07-04 GIB-182 14.726,40 1.472,64
2022-07-06 GIB-183 13.688,00 1.368,80
2022-07-08 GIB-184 15.222,00 1.522,20
2022-07-11 GIB-185 13.216,00 1.321,60
2022-07-15 GIB-186 15.930,00 1.593,00
2022-07-18 GIB-187 12.744,00 1.274,40
2022-07-20 GIB-188 13.924,00 1.392,40
2022-07-25 GIB-189 16.992,00 1.699,20
2022-07-27 GIB-190 17.080,50 1.708,05
2022-07-05 GIB-102 16.520,00 1.652,00
2022-07-06 GIB-103 17.346,00 1.734,60
2022-07-07 GIB-104 17.228,00 1.722,80
2022-07-09 GIB-105 26.432,00 2.643,20
2022-07-11 GIB-106 28.910,00 2.891,00
2022-07-13 GIB-107 28.320,00 2.832,00
2022-07-15 GIB-108 32.332,00 3.233,20
2022-07-16 GIB-109 17.936,00 1.793,60
2022-07-18 GIB-110 22.302,00 2.230,20
2022-07-19 GIB-111 22.892,00 2.289,20
2022-07-20 GIB-112 20.272,40 2.027,24
2022-07-21 GIB-113 21.889,00 2.188,90
2022-07-22 GIB-114 19.470,00 1.947,00
2022-07-23 GIB-115 21.122,00 2.112,20
2022-07-25 GIB-116 21.240,00 2.124,00
2022-08-02 GIB-778 14.396,00 1.439,60
2022-08-04 GIB-779 15.930,00 1.593,00
2022-08-05 GIB-780 15.576,00 1.557,60
2022-08-08 GIB-781 15.930,00 1.593,00
2022-08-09 GIB-782 15.812,00 1.581,20
2022-08-10 GIB-783 16.520,00 1.652,00
2022-08-11 GIB-784 17.287,00 1.728,70
2022-08-13 GIB-785 16.284,00 1.628,40
2022-08-15 GIB-786 16.697,00 1.669,70
2022-08-17 GIB-787 15.930,00 1.593,00
2022-08-19 GIB-788 15.989,00 1.598,90
2022-08-22 GIB-789 16.267,80 1.626,78
2022-08-24 GIB-790 16.048,00 1.604,80
2022-08-27 GIB-791 15.104,00 1.510,40
2022-09-01 GIB-664 11.800,00 1.180,00
2022-09-03 GIB-665 12.390,00 1.239,00
2022-09-05 GIB-666 13.688,00 1.368,80
2022-09-07 GIB-667 14.101,00 1.410,10
2022-09-09 GIB-668 13.216,00 1.321,60
2022-09-12 GIB-669 11.328,00 1.132,80
2022-09-13 GIB-670 12.980,00 1.298,00
2022-09-15 GIB-671 13.452,00 1.345,20
2022-09-17 GIB-672 13.629,00 1.362,90
2022-09-19 GIB-673 12.567,00 1.256,70
2022-09-20 GIB-674 13.747,00 1.374,70
2022-09-21 GIB-675 12.803,00 1.280,30
2022-09-23 GIB-676 12.283,80 1.228,38
2022-09-26 GIB-677 9.746,80 1.000,00
2022-09-29 GIB-678 11.168,70 1.116,87
2022-10-06 GIB-43 10.620,00 1.062,00
2022-10-07 GIB-44 10.856,00 1.085,60
2022-10-08 GIB-45 9.440,00 1.000,00
2022-10-10 GIB-46 7.552,00 1.000,00
2022-10-11 GIB-47 8.260,00 1.000,00
2022-10-12 GIB-48 9.204,00 1.000,00
2022-10-13 GIB-49 9.558,00 1.000,00
2022-10-14 GIB-50 8.850,00 1.000,00
2022-10-15 GIB-51 9.912,00 1.000,00
2022-10-17 GIB-52 11.682,00 1.168,20
2022-10-18 GIB-53 8.555,00 1.000,00
2022-10-19 GIB-54 8.850,00 1.000,00
2022-10-20 GIB-55 7.670,00 1.000,00
2022-10-21 GIB-56 9.086,00 1.000,00
2022-10-22 GIB-57 10.620,00 1.062,00
2022-10-24 GIB-58 7.906,00 1.000,00
2022-10-25 GIB-59 9.263,00 1.000,00
2022-10-26 GIB-60 9.322,00 1.000,00
2022-12-22 GIB--134 14.986,00 1.498,60
2022-12-23 GIB-135 16.520,00 1.652,00
2022-12-24 GIB-136 13.570,00 1.357,00
2022-12-26 GIB-137 14.278,00 1.427,80
2022-12-27 GIB-138 16.225,00 1.622,50
2022-12-28 GIB-139 18.880,00 1.888,00
2022-12-29 GIB-140 17.641,00 1.764,10
"""


def kunye(hadler=HADLER_METNI):
    return ik.normalize({"ouc353_uygula": "Evet", "ouc353_hadleri": hadler})


def faturalar(satirlar):
    """(tarih, no, tutar) uclulerinden fatura listesi."""
    return [{"duzenleyen_vkn": "1111111111", "alici_vkn": "1234567890",
             "tarih": tarih, "fatura_no": no,
             "matrah": round(tutar / 1.18, 2), "kdv": round(tutar - tutar / 1.18, 2),
             "toplam": tutar, "dahil": True}
            for tarih, no, tutar in satirlar]


SATICILAR = {"1111111111": {"unvan": "SAHTECİ-1 LTD",
                            "kullanma": "Bilmeden kullanma"}}


# ------------------------------------------------------- 1) had cozumlemesi
print("\n1) Künyeye yazılan hadler")
hadler = ik.belge_alma_hadleri(kunye())
denetle(len(hadler) == 2, "iki sınır dönemi okundu")
esit(hadler[0]["alt_sinir"], 500.0, "ilk dönemin alt sınırı")
esit(hadler[0]["ust_sinir"], 190000.0, "ilk dönemin üst sınırı")
esit(hadler[1]["alt_sinir"], 1000.0, "ikinci dönemin alt sınırı")
esit(hadler[1]["ust_sinir"], 500000.0, "ikinci dönemin üst sınırı")
denetle(hadler[0]["bitis"] == (2022, 7, 31), "bitiş tarihi okundu")
denetle(hadler[1]["bitis"] is None, "boş bitiş “ve sonrası” demek")

# "1.000" ve "190.000" Turkce binlik ayracli; 1,0 ve 190,0 OKUNMAMALI.
esit(ik._had_tutari("1.000"), 1000.0, "“1.000” bin olarak okunuyor")
esit(ik._had_tutari("190.000"), 190000.0, "“190.000” okunuyor")
esit(ik._had_tutari("5.500.000"), 5500000.0, "“5.500.000” okunuyor")
esit(ik._had_tutari("7.500,50"), 7500.50, "kuruşlu tutar okunuyor")
esit(ik._had_tutari("500"), 500.0, "ayraçsız tutar okunuyor")

# ------------------------------------------------- 2) ornek satirlar birebir
print("\n2) Örnek rapordaki satırlar")
liste = F.normalize(faturalar([(t, n, tut) for _s, t, n, tut, _c
                               in ORNEK_SATIRLAR]), "1234567890")
sonuc = F.belge_alma_usulsuzlugu(liste, hadler, SATICILAR)
denetle(len(sonuc["satirlar"]) == len(ORNEK_SATIRLAR),
        "her fatura için bir satır")
for (sira, tarih, no, tutar, ceza) in ORNEK_SATIRLAR:
    satir = next((s for s in sonuc["satirlar"] if s["fatura_no"] == no
                  and s["tarih"] == tarih), None)
    if satir is None:
        denetle(False, "%d. satır (%s) bulunamadı" % (sira, no))
        continue
    esit(satir["ceza"], ceza, "%d. satır (%s) cezası" % (sira, no))

# 105. satir: %10 alt sinirin ALTINDA kaldigi icin alt sinira yuvarlaniyor.
kucuk = next(s for s in sonuc["satirlar"] if s["fatura_no"] == "GIB-677")
esit(kucuk["yuzde_on"], 974.68, "%10 hesabı ham tutarı koruyor")
esit(kucuk["alt_sinir"], 1000.0, "01.08 sonrası alt sınır uygulanıyor")
denetle(kucuk["ceza"] > kucuk["yuzde_on"],
        "ceza alt sınıra yükseltiliyor")

# 01.08 oncesi / sonrasi ayrimi gercekten calisiyor mu
once = next(s for s in sonuc["satirlar"] if s["fatura_no"] == "GIB-190")
sonra = next(s for s in sonuc["satirlar"] if s["fatura_no"] == "GIB-778")
esit(once["alt_sinir"], 500.0, "01.08 öncesi alt sınır 500")
esit(sonra["alt_sinir"], 1000.0, "01.08 sonrası alt sınır 1.000")

# -------------------------------------------------------- 3) ornegin toplami
print("\n3) Örnek raporun 131 satırı birebir")


def _tl_coz(ham):
    return float(ham.replace(".", "").replace(",", "."))


tam = []
for satir in ORNEK_TABLO.strip().split("\n"):
    tarih, no, tutar, ceza = satir.split(" ")
    tam.append((tarih, no, _tl_coz(tutar), _tl_coz(ceza)))

denetle(len(tam) == 131, "örnek tablonun 131 satırı okundu")
tam_liste = F.normalize(faturalar([(t, n, tut) for t, n, tut, _c in tam]),
                        "1234567890")
tam_sonuc = F.belge_alma_usulsuzlugu(tam_liste, hadler, SATICILAR)

sapan = []
for sira, (tarih, no, _tutar, ceza) in enumerate(tam, 1):
    bulunan = next((x for x in tam_sonuc["satirlar"]
                    if x["fatura_no"] == no and x["tarih"] == tarih), None)
    if bulunan is None or abs((bulunan["ceza"] or 0.0) - ceza) > 0.005:
        sapan.append("%d. satır (%s)" % (sira, no))
denetle(not sapan, "her satırın cezası örnekle aynı%s"
        % ("" if not sapan else " — sapanlar: " + ", ".join(sapan[:5])))

# Mufettisin raporundaki TOPLAM satiri. Uygulamanin gercek bir raporu
# birebir uretebildiginin capasi bu iki rakam.
esit(tam_sonuc["belge_tutari"], ORNEK_TOPLAM_TUTAR,
     "TOPLAM belge tutarı örnekle aynı")
esit(tam_sonuc["ham_toplam"], ORNEK_TOPLAM_CEZA,
     "TOPLAM ceza örnekle aynı")
# 236.943,99, 2022'nin son gecerli ust siniri olan 500.000'in altinda;
# mufettis de ham toplami kesmis. Hesap ayni sonuca varmali.
esit(tam_sonuc["kesilecek"], ORNEK_TOPLAM_CEZA,
     "üst sınır aşılmadığından kesilecek = ham toplam")
denetle(not tam_sonuc["ust_sinir_uygulandi"], "üst sınır uygulanmadı")
# 01.08.2022 gecisi gercek tarihler uzerinde: 77. satir oncesi, 78. sonrasi.
esit(tam_sonuc["satirlar"][76]["alt_sinir"], 500.0,
     "77. satır (25.07.2022) eski alt sınırda")
esit(tam_sonuc["satirlar"][77]["alt_sinir"], 1000.0,
     "78. satır (02.08.2022) yeni alt sınırda")

# --------------------------------------------------------- 4) ust sinir
print("\n4) Üst sınır")
buyuk = F.belge_alma_usulsuzlugu(
    F.normalize(faturalar([("2022-03-01", "A-%d" % i, 500000.0)
                           for i in range(10)]), "1234567890"),
    hadler, SATICILAR)
# 10 x 500.000 x %10 = 500.000 ham ceza. 2022'nin son gecerli ust siniri
# 500.000 oldugundan tam sinirda kaliyor; asmiyor.
esit(buyuk["ham_toplam"], 500000.0, "ham toplam")
denetle(not buyuk["ust_sinir_uygulandi"], "sınıra eşit tutar aşım saymıyor")

cok = F.belge_alma_usulsuzlugu(
    F.normalize(faturalar([("2022-03-01", "B-%d" % i, 600000.0)
                           for i in range(10)]), "1234567890"),
    hadler, SATICILAR)
esit(cok["ham_toplam"], 600000.0, "ham toplam sınırı aşıyor")
denetle(cok["ust_sinir_uygulandi"], "aşım işaretlendi")
esit(cok["kesilecek"], 500000.0, "kesilecek ceza üst sınıra iniyor")

# -------------------------------------------------- 5) kume: hangi faturalar
print("\n5) Hesaba giren faturalar")
# Tarhiyat disi birakilmis (duzeltmeyle cikarilmis) satici da hesaba GIRER:
# tutar beyandan cikarilmis olsa bile gercek fatura alinmamis olmasi
# degismez. `sayilir` kullanilmis olsaydi bu kume bosalirdi.
sat_duz = {"1111111111": dict(SATICILAR["1111111111"],
                              duzeltme_ile_cikarildi="Evet")}
duz = F.belge_alma_usulsuzlugu(liste, hadler, sat_duz)
denetle(len(duz["satirlar"]) == len(ORNEK_SATIRLAR),
        "düzeltmeyle çıkarılmış satıcının faturaları da hesaba giriyor")

# Bilerek / bilmeden ayrimi 353/1'i DEGISTIRMEZ: nesnel bir fiildir.
sat_bilerek = {"1111111111": dict(SATICILAR["1111111111"],
                                  kullanma="Bilerek kullanma")}
bilerek = F.belge_alma_usulsuzlugu(liste, hadler, sat_bilerek)
esit(bilerek["ham_toplam"], sonuc["ham_toplam"],
     "bilerek/bilmeden ayrımı cezayı değiştirmiyor")

# "Dahil" kaldirilan satir hesaba girmez: mufettisin tek suzgeci bu.
disi = F.normalize(faturalar([("2022-01-17", "GIB-190", 30385.00)]),
                   "1234567890")
disi[0]["dahil"] = False
denetle(F.belge_alma_usulsuzlugu(disi, hadler, SATICILAR)["satirlar"] == [],
        "“Dahil” kaldırılan satır hesaba girmiyor")

# Hakkinda VTR bulunmayan saticidan alinan fatura girmez.
yabanci = F.normalize(faturalar([("2022-01-17", "X-1", 30385.00)]),
                      "1234567890")
denetle(F.belge_alma_usulsuzlugu(yabanci, hadler, {})["satirlar"] == [],
        "sahteci olmayan satıcının faturası hesaba girmiyor")

# --------------------------------------------------- 6) haddi girilmemis hal
print("\n6) Haddi girilmemiş fatura")
eksik = F.belge_alma_usulsuzlugu(
    F.normalize(faturalar([("2021-05-10", "C-1", 20000.0)]), "1234567890"),
    hadler, SATICILAR)
denetle(eksik["eksik_had"], "2021 için had yok, satır işaretlendi")
denetle(eksik["satirlar"][0]["ceza"] is None,
        "cezası uydurulmuyor, boş bırakılıyor")
esit(eksik["satirlar"][0]["yuzde_on"], 2000.0, "%10 yine hesaplanıyor")

# ------------------------------------------------------ 7) yil yil ayirma
print("\n7) İki yıllı dosya")
iki_yil_hadler = ik.belge_alma_hadleri(kunye(
    HADLER_METNI + "\n01.01.2023 |  | 2.000 | 1.000.000"))
iki = F.belge_alma_usulsuzlugu(
    F.normalize(faturalar([("2022-03-01", "D-1", 100000.0),
                           ("2023-03-01", "D-2", 100000.0)]), "1234567890"),
    iki_yil_hadler, SATICILAR)
denetle([y["yil"] for y in iki["yillar"]] == [2022, 2023],
        "yıllar ayrı ayrı özetleniyor")
esit(iki["yillar"][0]["ust_sinir"], 500000.0, "2022 üst sınırı")
esit(iki["yillar"][1]["ust_sinir"], 1000000.0, "2023 üst sınırı")
esit(iki["ham_toplam"], 20000.0, "iki yılın toplamı")

print()
if HATA:
    print("BAŞARISIZ: %d denetim" % len(HATA))
    for h in HATA:
        print("  -", h)
    sys.exit(1)
print("Tüm denetimler geçti.")
