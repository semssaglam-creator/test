# -*- coding: utf-8 -*-
"""Vergi ziyai cezasinin gerileme denetimi.

    python3 testler/ceza_testi.py

Mufettisin karari (2026-10-15): ceza, re'sen tarh edilecek tutarin TAMAMI
uzerinden hesaplanir ve raporun ceza tablosundan matrah sutunlari
("Bilerek / Bilmeden Kullanilan Belgeler") kaldirilir.

Onceki davranis: ceza yalnizca sahte belgeye atfedilebilen kisim
(`min(tarh, reddedilen KDV)`) uzerinden hesaplaniyordu. Tarhiyatin baska bir
tespitten gelen kismi CEZASIZ kaliyordu - denetimin ayirt edici hali bu.

Devreden KDV sahte belgeler yuzunden degistigi icin, DEVIRDEN dogan fark da
sahte belgeye baglidir ve ayni kati tasir (mufettisin duzeltmesi,
2026-10-15). Devir zinciri reddi bir ay sogurup vergiyi sonraki aya
tasidiginda uc kat kaybolmamali.

Uc kat yalnizca VUK 359'daki fiillere baglidir; beyan hatasi ya da matrah
ilavesi gibi 359 dayanagi olmayan tutar bir kat tasir.

`pay_*` alanlari veriden KALDIRILMAZ: ceza tablosundan cikarildilar ama
uzlasma kapsami ayrimi (Ç bolumu) onlardan besleniyor - `pay_bilerek`
kapsam disi, `pay_bilmeden` + `pay_belirsiz` kapsam ici tutardir.
"""
import os
import sys

KOK = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, KOK)

from app import faturalar as F                                       # noqa: E402
from app import web_server as W                                      # noqa: E402
from app.satirlar import VERI_KODLARI                                # noqa: E402

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


# ------------------------------------------------------------------- fikstur
# Her ay: hesaplanan 90.000, indirim 80.000 -> beyan edilen odenecek 10.000.
# Indirim cikarildikca odenecek artar ve fark = cikarilan tutar olur.
def beyan():
    b = {k: [0.0] * 12 for k in VERI_KODLARI}
    for ay in range(12):
        b["matrah_toplami"][ay] = 500000.0
        b["hesaplanan_kdv"][ay] = 90000.0
        b["toplam_kdv"][ay] = 90000.0
        b["yurtici_alim_kdv"][ay] = 80000.0
        b["bu_donem_indirilecek"][ay] = 80000.0
        b["indirimler_toplami"][ay] = 80000.0
        b["odenmesi_gereken_kdv"][ay] = 10000.0
    return b


def ornek(kullanma="Bilerek kullanma", subat_cikar=0.0):
    """Ocak'ta sahte belge, Subat'ta (istege gore) baska bir tespit.

    Subat'ta fatura YOK ama indirim cikariliyor: tarhiyatin sahte belgeye
    atfedilemeyen kismini temsil eder. Eski kodda o tutar cezasiz kalirdi.
    """
    e = {k: [0.0] * 12 for k in ("matrah_ilave", "hesaplanan_kdv_ilave",
                                 "devir_cikar", "indirim_cikar",
                                 "yuklenilen_cikar")}
    e["indirim_cikar"][0] = 6000.0          # Ocak: sahte belgenin KDV'si
    e["indirim_cikar"][1] = subat_cikar     # Şubat: başka bir tespit
    return {
        "mukellef": {"ad_unvan": "ÖRNEK İNŞAAT LTD ŞTİ",
                     "vkn_tckn": "9999999999",
                     "vergi_dairesi": "ZİYAPAŞA VD", "adres": "ADANA"},
        "kunye": {"mukellef_turu": "Kurum (sermaye şirketi)",
                  "faaliyet_konulari": "inşaat taahhüt işleri",
                  "tou_talebi": "Talep edildi",
                  "eleman_ad": "AHMET MÜFETTİŞ",
                  "eleman_unvan": "Vergi Müfettişi"},
        "yillar": [{"yil": 2022, "beyan": beyan(), "ay_sayisi": 12,
                    "elestiri": e}],
        "faturalar": [{"duzenleyen_vkn": "1111111111",
                       "alici_vkn": "9999999999", "tarih": "2022-01-10",
                       "fatura_no": "A-1", "matrah": 30000.0, "kdv": 6000.0,
                       "toplam": 36000.0, "dahil": True}],
        "saticilar": {"1111111111": {
            "unvan": "SAHTECI-1 LTD", "kullanma": kullanma,
            "vergi_dairesi": "5 OCAK VD", "vtr_no": "2025/1",
            "vtr_tarihi": "04.03.2025", "not": "sahte belge düzenlediği"}},
    }


def devir_ornegi(kullanma="Bilerek kullanma"):
    """Red bir ayi sogurur, vergi SONRAKI aylara tasinir.

    Ocak'ta buyuk bir devir var; 10.000 TL'lik red o ayin devrini eritir ve
    tarhiyat Subat ile Mart'ta dogar. O aylarda FATURA YOKTUR - ceza kati
    yalnizca devir zincirinden okunabilir.
    """
    b = {k: [0.0] * 12 for k in VERI_KODLARI}
    devir = 0.0
    for ay in range(12):
        b["matrah_toplami"][ay] = 500000.0
        b["hesaplanan_kdv"][ay] = 90000.0
        b["toplam_kdv"][ay] = 90000.0
        ind = 100000.0 if ay == 0 else 85000.0
        b["yurtici_alim_kdv"][ay] = ind
        b["bu_donem_indirilecek"][ay] = ind
        b["onceki_donem_devreden"][ay] = devir
        toplam = devir + ind
        b["indirimler_toplami"][ay] = toplam
        if toplam >= 90000.0:
            b["odenmesi_gereken_kdv"][ay] = 0.0
            devir = round(toplam - 90000.0, 2)
        else:
            b["odenmesi_gereken_kdv"][ay] = round(90000.0 - toplam, 2)
            devir = 0.0
        b["sonraki_donem_devreden"][ay] = devir

    e = {k: [0.0] * 12 for k in ("matrah_ilave", "hesaplanan_kdv_ilave",
                                 "devir_cikar", "indirim_cikar",
                                 "yuklenilen_cikar")}
    e["indirim_cikar"][0] = 10000.0          # yalnızca Ocak'ta red
    c = ornek(kullanma=kullanma)
    c["yillar"] = [{"yil": 2022, "beyan": b, "ay_sayisi": 12, "elestiri": e}]
    c["faturalar"] = [{"duzenleyen_vkn": "1111111111",
                       "alici_vkn": "9999999999", "tarih": "2022-01-10",
                       "fatura_no": "A-1", "matrah": 50000.0,
                       "kdv": 10000.0, "toplam": 60000.0, "dahil": True}]
    return c


def dagilim(c):
    sonuc, _b = W._hesapla(c)
    liste = F.normalize(c["faturalar"], c["mukellef"]["vkn_tckn"])
    return F.ceza_dagilimi(liste, c["saticilar"], sonuc), sonuc


def rapor(c):
    h = W.Istekci.__new__(W.Istekci)
    h._belge_gonder = lambda *a: None
    h._ciktilara_yaz = lambda d: None
    belgeler, _inceleme, _vsr = h._rapor_hazirla({"calisma": c})
    return belgeler[0][1].duz_metin()


def satir(dag, ay):
    return next(s for s in dag["satirlar"] if s["ay"] == ay)


# ------------------------------------------------- 1) tamami uzerinden ceza
print("\n1) Ceza, tarh edilecek tutarın tamamı üzerinden")
c = ornek(subat_cikar=4000.0)
dag, _sonuc = dagilim(c)

ocak = satir(dag, 1)
esit(ocak["tarh"], 6000.0, "Ocak re'sen tarh edilecek KDV")
esit(ocak["ceza_bilerek"], 18000.0, "Ocak cezası 3 kat (6.000 x 3)")
esit(ocak["ceza_toplam"], 18000.0, "Ocak ceza toplamı")

# Ayirt edici hal: Subat'ta fatura yok, tarhiyat baska bir tespitten.
subat = satir(dag, 2)
esit(subat["tarh"], 4000.0, "Şubat re'sen tarh edilecek KDV")
esit(subat["red_toplam"], 0.0, "Şubat'ta reddedilen sahte belge KDV'si yok")
esit(subat["ceza_toplam"], 4000.0,
     "Şubat cezası 1 kat — ESKİ KODDA SIFIRDI")
esit(subat["ceza_bilerek"], 0.0,
     "Şubat'a üç kat yazılmıyor (359 dayanağı yok)")
# 359 dayanagi olmayan tutar AYRI kalemde tutulur, "belirsiz"e
# karistirilmaz: "belirsiz" kullanma durumu SECILMEMIS saticilari isaret
# eder ve rapor bunun icin kullaniciya uyari yazar. Karistirilirsa butun
# saticilar siniflandirilmis olsa bile uyari yersiz cikar.
esit(subat["pay_dayanaksiz"], 4000.0,
     "359 dayanağı olmayan tutar ayrı kalemde (“dayanaksız”)")
esit(subat["pay_belirsiz"], 0.0,
     "“belirsiz” kirletilmiyor — orası sınıflandırılmamış satıcılar için")

esit(dag["toplam"]["tarh"], 10000.0, "toplam tarh")
esit(dag["toplam"]["ceza_toplam"], 22000.0,
     "toplam ceza = 6.000x3 + 4.000x1")

# Cezanin matrahi, tarhin tamamini kapsamali.
esit(sum(s["pay_bilerek"] + s["pay_bilmeden"] + s["pay_belirsiz"]
         + s["pay_dayanaksiz"] for s in dag["satirlar"]), 10000.0,
     "payların toplamı tarhın tamamına eşit")

# Butun saticilar siniflandirilmis: "nitelendirme yapilmamis" uyarisi
# YERSIZ olur. Bu uyari `ceza_belirsiz`den tetiklendigi icin, kalan tutarin
# oraya eklenmesi uyariyi yanlis yere dusuruyordu.
denetle(all(s["ceza_belirsiz"] == 0.0 for s in dag["satirlar"]),
        "sınıflandırılmamış satıcı yokken “belirsiz” cezası sıfır")

# ------------------------------------------------ 1b) devirden dogan fark
print("\n1b) Devirden doğan fark da aynı katı taşıyor")
# Reddi bir ay sogurup vergiyi sonraki aya tasiyan hal. Subat ve Mart'ta
# FATURA YOK; eski kodda o aylarin cezasi bir kat yaziliyordu ve devir
# zinciri devreye girdigi anda uc kat kayboluyordu.
c_devir = devir_ornegi()
dag_d, sonuc_d = dagilim(c_devir)


def ay_satiri(dag, ay_adi):
    return next(s for s in dag["satirlar"] if s["ay_adi"] == ay_adi)


esit(ay_satiri(dag_d, "Ocak")["tarh"], 0.0,
     "Ocak'ta tarhiyat yok: devir reddi soğurdu")
esit(ay_satiri(dag_d, "Ocak")["red_toplam"], 10000.0,
     "Ocak'ta reddedilen KDV 10.000")
for ay in ("Şubat", "Mart"):
    s = ay_satiri(dag_d, ay)
    esit(s["tarh"], 5000.0, "%s tarhiyatı devirden doğuyor" % ay)
    esit(s["red_toplam"], 0.0, "%s'ta fatura yok" % ay)
    esit(s["ceza_bilerek"], 15000.0,
         "%s cezası ÜÇ kat (5.000 x 3) — eski kodda bir kattı" % ay)
    esit(s["ceza_dayanaksiz"], 0.0,
         "%s'ta tutar “dayanaksız” sayılmıyor" % ay)

esit(dag_d["toplam"]["tarh"], 10000.0, "devirli dosyada toplam tarh")
esit(dag_d["toplam"]["ceza_toplam"], 30000.0,
     "toplam ceza = tarh x 3 (eski kodda 10.000'di)")

# Bilmeden kullanmada ayni zincir bir kat tasimali.
dag_db, _s = dagilim(devir_ornegi(kullanma="Bilmeden kullanma"))
esit(dag_db["toplam"]["ceza_toplam"], 10000.0,
     "bilmeden kullanmada devirden doğan fark bir kat")

# ------------------------------------------------------------- 2) kat ayrimi
print("\n2) Kat ayrımı korunuyor")
c_bilmeden = ornek(kullanma="Bilmeden kullanma", subat_cikar=4000.0)
dag2, _s2 = dagilim(c_bilmeden)
esit(satir(dag2, 1)["ceza_toplam"], 6000.0,
     "bilmeden kullanmada Ocak cezası 1 kat")
esit(dag2["toplam"]["ceza_toplam"], 10000.0, "bilmeden toplam ceza")

# ------------------------------------------------------- 3) tablo sutunlari
print("\n3) Ceza tablosundan matrah sütunları kaldırıldı")
m = rapor(ornek(subat_cikar=4000.0))
denetle("Bilerek Kullanılan" not in m,
        "“Bilerek Kullanılan Belgeler” sütunu yok")
denetle("Bilmeden Kullanılan" not in m,
        "“Bilmeden Kullanılan Belgeler” sütunu yok")
denetle("Re’sen Tarh\nEdilecek KDV" in m or "Edilecek KDV" in m,
        "“Re'sen Tarh Edilecek KDV” sütunu duruyor")
denetle("Vergi Ziyaı Cezası\n(3 kat)" in m, "3 kat sütunu duruyor")
denetle("Vergi Ziyaı Cezası\n(1 kat)" in m, "1 kat sütunu duruyor")
denetle("re’sen tarh edilmesi gereken katma değer vergisinin tamamı "
        "üzerinden hesaplanmıştır" in m,
        "açıklama paragrafı yeni hesabı anlatıyor")
# Fatura bulunmayan bir donemin neden ayni kati tasidigi belgede yazmali;
# aksi halde raporu okuyan "Subat'ta fatura yok, neden uc kat?" diye sorar.
denetle("devir zincirinden doğan vergi farkı da aynı fiilden kaynaklanmakta "
        "olup aynı ceza katına tabidir" in m,
        "paragraf devir zincirini de gerekçelendiriyor")
denetle("paylaştırma tarh edilen tutar üzerinden" not in m,
        "eski açıklama paragrafı kalkmış")

# Tek kat varsa toplam sutunu onun aynisi olurdu; yazilmamali.
m_tek = rapor(ornek(subat_cikar=0.0))
denetle("Vergi Ziyaı Cezası\n(3 kat)" in m_tek, "tek katta 3 kat sütunu var")
denetle("Vergi Ziyaı Cezası\nToplamı" not in m_tek,
        "tek katta “Toplamı” sütunu yazılmıyor")
denetle("Vergi Ziyaı Cezası\nToplamı" in m,
        "iki kat varsa “Toplamı” sütunu yazılıyor")

# ---------------------------------------------------- 4) sonuc bolumu tablosu
print("\n4) Sonuç bölümündeki tablo")
# Sonuc tablosundaki ceza sutunu da ayni dagilimdan besleniyor; tarhin
# tamami uzerinden hesaplanan tutari yazmali.
sonuc_bolumu = m[m.find("V- SONUÇ"):]
denetle("22.000,00" in sonuc_bolumu,
        "sonuç tablosundaki ceza tarhın tamamı üzerinden (22.000)")
denetle("Bilerek Kullanılan" not in sonuc_bolumu,
        "sonuç tablosunda da matrah sütunu yok")
denetle("Vergi Ziyaı\nCezası" in sonuc_bolumu,
        "sonuç tablosunda ceza sütunu duruyor")

# ------------------------------------------- 5) uzlasma ayrimi bozulmamis
print("\n5) Uzlaşma kapsamı ayrımı")
# `pay_*` alanlari ceza tablosundan cikarildi ama veriden KALDIRILMADI:
# uzlasma bolumu onlardan besleniyor. 359 dayanagi olmayan tutar kapsam
# ICINDE olmali - matrah ilavesi 359 fiili degildir.
esit(dag["toplam"]["pay_bilerek"], 6000.0,
     "kapsam dışı tutar (bilerek) 6.000")
esit(dag["toplam"]["pay_bilmeden"] + dag["toplam"]["pay_belirsiz"]
     + dag["toplam"]["pay_dayanaksiz"], 4000.0,
     "kapsam içi tutar 4.000 (359 dayanağı olmayan tutar dahil)")
denetle("Uzlaşma Kapsamı Dışında" in m,
        "karma dosyada uzlaşma dağılım tablosu yazılıyor")
# Dagilim tablosunun satirlari kendi icinde tutmali.
denetle("6.000,00\t4.000,00\t10.000,00" in m
        or "4.000,00\t6.000,00\t10.000,00" in m,
        "uzlaşma dağılım tablosu kapsam içi + dışı = toplam veriyor")

# Nitelendirme uyarisi, gercekten siniflandirilmamis satici varken cikmali.
m_belirsiz = rapor(ornek(kullanma="Belirlenmedi", subat_cikar=4000.0))
denetle("nitelendirmesi yapılmamış satıcılar" in m_belirsiz,
        "sınıflandırılmamış satıcı varsa uyarı çıkıyor")
denetle("nitelendirmesi yapılmamış satıcılar" not in m,
        "hepsi sınıflandırılmışsa uyarı ÇIKMIYOR")

print()
if HATA:
    print("BAŞARISIZ: %d denetim" % len(HATA))
    for x in HATA:
        print("  -", x)
    sys.exit(1)
print("Tüm denetimler geçti.")
