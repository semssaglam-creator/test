# -*- coding: utf-8 -*-
"""Fatura basina duzeltme isareti ve belgelerde yil ayrimi.

    python3 testler/duzeltme_isareti_testi.py

Iki degisiklik birlikte denetlenir, cunku ikisi de ayni sahadaki tespitten
dogdu (2026-10-23): birden fazla yili incelenen bir mukellef, ayni saticinin
BIR yildaki faturalarini duzeltme beyannamesiyle indirimlerden cikarmis,
diger yildakileri cikarmamisti.

  1) "Duzeltme beyannamesiyle cikarildi" isareti artik FATURA satirindadir
     (`duzeltme_cikarildi`). Satici duzeyindeki tek isaret o dosyada ya
     butun yillari tarhiyat disinda birakiyor ya hepsini iceri aliyordu.
     Eski calismalarda isaret satici kaydinda durdugundan o da okunmaya
     devam eder.

  2) Vergilendirme hesap donemi bazinda yapildigindan, ayni saticidan farkli
     yillarda alinan belgeler tutanakta ve raporda AYRI paragraf ve AYRI
     tabloyla anlatilir. Madde tek kalir; ayrilan sey yillardir.

Burada korunan sey ozellikle su: tek yila ait bir dosyada cikti ESKISIYLE
AYNI kalmali (ek giris paragrafi yazilmamali), cok yilli dosyada ise her
yilin kendi tablosu ve kendi tespitleri bulunmali.
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
    denetle(bulunan == beklenen,
            "%s (beklenen %r, bulunan %r)" % (aciklama, beklenen, bulunan))


# ------------------------------------------------------------------- ornek
def beyan():
    b = {k: [0.0] * 12 for k in VERI_KODLARI}
    for ay in range(12):
        b["matrah_toplami"][ay] = 500000.0
        b["hesaplanan_kdv"][ay] = 100000.0
        b["toplam_kdv"][ay] = 100000.0
        b["yurtici_alim_kdv"][ay] = 80000.0
        b["bu_donem_indirilecek"][ay] = 80000.0
        b["indirimler_toplami"][ay] = 80000.0
        b["odenmesi_gereken_kdv"][ay] = 20000.0
    return b


def elestiri(aylar=None):
    """`aylar`: {ay_no(1-12): indirimden cikarilacak tutar}"""
    e = {k: [0.0] * 12 for k in ("matrah_ilave", "hesaplanan_kdv_ilave",
                                 "devir_cikar", "indirim_cikar",
                                 "yuklenilen_cikar")}
    for ay, tutar in (aylar or {}).items():
        e["indirim_cikar"][ay - 1] = tutar
    return e


def fatura(tarih, no, matrah, duzeltildi=False):
    return {"duzenleyen_vkn": "1111111111", "alici_vkn": "1234567890",
            "tarih": tarih, "fatura_no": no, "matrah": matrah,
            "kdv": round(matrah * 0.2, 2), "toplam": round(matrah * 1.2, 2),
            "dahil": True, "mal_cinsi": "demir",
            "yevmiye_tarih": tarih, "yevmiye_no": "100",
            "duzeltme_cikarildi": "Evet" if duzeltildi else "Hayır"}


SATICI = {"1111111111": {
    "unvan": "SAHTECİ LTD", "kullanma": "Bilmeden kullanma",
    "vergi_dairesi": "5 OCAK VD", "is_emri": "Var",
    "not": "sahte belge düzenlediği",
    "duzeltme_aciklama": "söz konusu faturaların indirimlerden çıkarılması"}}


def ornek(faturalar, yillar):
    return {
        "mukellef": {"ad_unvan": "ÖRNEK İNŞAAT LTD ŞTİ",
                     "vkn_tckn": "1234567890",
                     "vergi_dairesi": "ZİYAPAŞA VD", "adres": "SEYHAN / ADANA"},
        "kunye": {"mukellef_turu": "Kurum (sermaye şirketi)",
                  "faaliyet_konulari": "inşaat taahhüt işleri"},
        "yillar": yillar,
        "faturalar": faturalar,
        "saticilar": {vkn: dict(bilgi) for vkn, bilgi in SATICI.items()},
    }


def istekci():
    return W.Istekci.__new__(W.Istekci)


def tutanak_metni(calisma):
    return W.Istekci._tutanak_onizleme(istekci(), {"calisma": calisma})["metin"]


def rapor_metni(calisma):
    return W.Istekci._rapor_onizleme(istekci(), {"calisma": calisma})["metin"]


# ---------------------------------------------- 1) fatura basina isaret
print("\n1) Fatura başına düzeltme işareti")
kismi = [fatura("2022-03-10", "A-1", 40000.0, duzeltildi=True),
         fatura("2022-04-11", "B-1", 25000.0)]
liste = F.normalize(kismi, "1234567890")
esit([f["duzeltme_cikarildi"] for f in liste], ["Evet", "Hayır"],
     "işaret normalize sonrası korunuyor")
esit(F.sayilir(liste[0], SATICI), False,
     "düzeltilmiş fatura tarhiyata girmiyor")
esit(F.sayilir(liste[1], SATICI), True,
     "düzeltilmemiş fatura tarhiyata giriyor")
# Tarhiyata giren tutar YALNIZCA duzeltilmemis faturadir: eskiden satici
# duzeyindeki isaret ikisini birden disarida ya da iceride birakiyordu.
esit(F.indirim_dizileri(liste, SATICI)[2022][3], 5000.0,
     "indirim dizisine yalnızca düzeltilmemiş faturanın KDV'si giriyor")
esit(sum(F.indirim_dizileri(liste, SATICI)[2022]), 5000.0,
     "düzeltilmiş faturanın KDV'si indirim dizisine hiç girmiyor")

s = F.satici_ozeti(liste, SATICI)[0]
esit(s["kdv"], 5000.0, "satıcı özetinde tarhiyata giren KDV")
esit(s["duz_kdv"], 8000.0, "satıcı özetinde düzeltmeyle çıkarılan KDV")
esit(s["liste_kdv"], 13000.0, "satıcı özetinde listedeki toplam KDV")
# Faturalarin bir kismi tarhiyata girdigi surece duzeltme kabul raporu
# YAZILAMAZ; o rapor eleştirilecek husus kalmamis dosyalar icindir.
esit(F.duzeltme_kabul_uygun_mu([s])[0], False,
     "kısmen düzeltilmiş dosyada düzeltme kabul raporu engelleniyor")
hepsi = F.satici_ozeti(
    F.normalize([fatura("2022-03-10", "A-1", 40000.0, duzeltildi=True),
                 fatura("2022-04-11", "B-1", 25000.0, duzeltildi=True)],
                "1234567890"), SATICI)
esit(F.duzeltme_kabul_uygun_mu(hepsi)[0], True,
     "faturaların tamamı işaretliyse kabul raporu yazılabiliyor")
esit(hepsi[0]["kdv"], 0.0, "tamamı düzeltilmişse tarhiyata giren KDV sıfır")

# Eski calismalarda isaret satici kaydindaydi ve butun faturalari kapsiyordu.
eski_satici = {"1111111111": dict(SATICI["1111111111"],
                                  duzeltme_ile_cikarildi="Evet")}
eski = F.normalize([fatura("2022-03-10", "A-1", 40000.0),
                    fatura("2022-04-11", "B-1", 25000.0)], "1234567890")
esit([F.sayilir(f, eski_satici) for f in eski], [False, False],
     "eski satıcı düzeyindeki işaret hâlâ okunuyor")
esit(F.satici_ozeti(eski, eski_satici)[0]["duz_kdv"], 13000.0,
     "eski işarette tutar düzeltme takımına yazılıyor")


# ------------------------------------------ 2) raporda iki tutar yan yana
print("\n2) Raporda düzeltilen ve kalan tutar ayrı ayrı")
metin = rapor_metni(ornek(kismi, [{"yil": 2022, "beyan": beyan(),
                                   "ay_sayisi": 12,
                                   "elestiri": elestiri({4: 5000.0})}]))
denetle("1 sıra numaralı belgeye ait 8.000,00 TL tutarındaki katma değer "
        "vergisi, mükellef kurum tarafından verilen düzeltme beyannameleri"
        in metin,
        "düzeltilen belge sıra numarasıyla ve tutarıyla anılıyor")
denetle("kullanılan 2 sıra numaralı belgeye isabet eden" in metin
        and "5.000,00 TL tutarındaki katma değer vergisinin indiriminin "
            "reddedilmesi" in metin,
        "kalan belgenin indiriminin reddi ayrıca isteniyor")
denetle("13.000,00 TL tutarındaki katma değer vergisinin indiriminin "
        "reddedilmesi" not in metin,
        "düzeltilen tutar reddedilecek tutara eklenmiyor")
# Degerlendirme bolumu de ayni ayrimi yapmali: mukerrer tarhiyat gerekcesi
# duzeltilen tutar uzerinden, tarhiyat kalan tutar uzerinden kurulur.
denetle("toplam 8.000,00 TL katma değer vergisi içeren faturalar" in metin,
        "değerlendirmede mükerrer tarhiyat gerekçesi düzeltilen tutar üzerinden")
denetle("toplam 5.000,00 TL tutarındaki katma değer vergisinin sahte "
        "belgelere dayandığı" in metin,
        "değerlendirmede indirimi reddedilen tutar kalan tutar")


# --------------------------------------------------- 3) tek yil: degisiklik yok
print("\n3) Tek yıllı dosyada ek giriş paragrafı yazılmıyor")
tek = tutanak_metni(ornek(kismi, [{"yil": 2022, "beyan": beyan(),
                                   "ay_sayisi": 12,
                                   "elestiri": elestiri({4: 5000.0})}]))
denetle("ait olan, 2 adet belge ile" not in tek,
        "tek yılda yıl bloğu giriş cümlesi yok (madde cümlesi zaten söylüyor)")
esit(tek.count("Sıra\tFatura Tarih\tFatura No"), 1,
     "tek yılda tek fatura tablosu var")


# --------------------------------------------------- 4) cok yil: ayri bloklar
print("\n4) Çok yıllı dosyada yıllar ayrı paragraf ve tablo")
cok_fatura = [fatura("2021-03-10", "A-1", 30000.0, duzeltildi=True),
              fatura("2021-07-15", "A-2", 20000.0, duzeltildi=True),
              fatura("2022-04-11", "B-1", 25000.0),
              fatura("2022-09-20", "B-2", 35000.0)]
cok = ornek(cok_fatura, [
    {"yil": 2021, "beyan": beyan(), "ay_sayisi": 12, "elestiri": elestiri()},
    {"yil": 2022, "beyan": beyan(), "ay_sayisi": 12,
     "elestiri": elestiri({4: 5000.0, 9: 7000.0})}])
metin = tutanak_metni(cok)
esit(metin.count("Sıra\tFatura Tarih\tFatura No"), 2,
     "her yıl için ayrı fatura tablosu açılıyor")
denetle("2021 hesap dönemine ait olan, 2 adet belge ile KDV hariç "
        "50.000,00 TL" in metin,
        "2021 bloğunun girişi o yılın adedini ve tutarını yazıyor")
denetle("2022 hesap dönemine ait olan, 2 adet belge ile KDV hariç "
        "60.000,00 TL" in metin,
        "2022 bloğunun girişi o yılın adedini ve tutarını yazıyor")
# Her tablonun TOPLAM satiri kendi bloğunun toplamini gostermeli; satici
# toplami (110.000,00) hicbir tabloda tek basina durmamali.
denetle("\tTOPLAM\t\t\t50.000,00\t10.000,00\t60.000,00" in metin
        and "\tTOPLAM\t\t\t60.000,00\t12.000,00\t72.000,00" in metin,
        "her tablonun TOPLAM satırı kendi yılının toplamı")
denetle("TOPLAM\t\t\t110.000,00" not in metin,
        "satıcı toplamı yıl tablosunun altına yazılmıyor")
# Sira numaralari bloklar boyunca kesintisiz ilerler; "2 sira numarali
# belge" diyen paragraf iki tablo arasinda belirsiz kalmasin.
denetle("\n3\t11.04.2022\tB-1" in metin,
        "ikinci yılın tablosu 3. sıradan devam ediyor")
# Duzeltme tespiti YALNIZCA duzeltmenin verildigi yilin blogunda.
esit(metin.count("sonrasında verilen düzeltme beyannameleri ile söz konusu "
                 "tutarların indirimlerden çıkarıldığı"), 1,
     "düzeltme tespiti yalnızca düzeltilen yılın bloğunda")
denetle("1 ve 2 sıra numaralı, toplam 60.000,00 TL tutarlı belgelerin" in metin,
        "düzeltme tespiti 2021 belgelerinin sıra numaralarını anıyor")
# Satici maddesi TEK kalir: iki yil icin iki veri maddesi acilmaz.
esit(metin.count("Ba-Bs sorgulamasında"), 1,
     "iki yıl için tek satıcı maddesi açılıyor")
# Muhasebe kaydi paragrafi her blokta o yilin yevmiye defterini anmali.
denetle("2021 yılı yevmiye defterine" in metin
        and "2022 yılı yevmiye defterine" in metin,
        "muhasebe kaydı paragrafı her blokta kendi yılını yazıyor")


# ------------------------------------------- 5) yil yil rapor: dogru akibet
print("\n5) Yıl yıl raporda doğru âkıbet")
metin = rapor_metni(cok)
y2021 = metin.split("2022 YILI RAPORU")[0]
y2022 = metin.split("2022 YILI RAPORU")[-1]
denetle("10.000,00 TL tutarındaki katma değer vergisi, mükellef kurum "
        "tarafından verilen düzeltme beyannameleri" in y2021,
        "2021 raporunda tutarın düzeltmeyle çıkarıldığı yazıyor")
denetle("indiriminin reddedilmesi" not in y2021,
        "2021 raporunda indirim reddi istenmiyor (tutar beyandan çıkmış)")
denetle("12.000,00 TL tutarındaki katma değer vergisinin indiriminin "
        "reddedilmesi" in y2022,
        "2022 raporunda indirim reddi isteniyor")
denetle("düzeltme beyannameleri ile ilgili dönem indirimlerinden "
        "çıkarılmıştır" not in y2022,
        "2022 raporunda düzeltme anlatısı yazılmıyor")


print("\n" + ("BAZI DENETİMLER BAŞARISIZ" if HATA else "Tüm denetimler geçti."))
sys.exit(1 if HATA else 0)
