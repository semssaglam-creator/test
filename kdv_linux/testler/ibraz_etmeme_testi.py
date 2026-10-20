# -*- coding: utf-8 -*-
"""Defter ve belge ibraz etmeme raporunun gerileme denetimi.

    python3 testler/ibraz_etmeme_testi.py

Mukellef yasal defter ve belgelerini ibraz etmediginde beyan edilen
indirilecek KDV'nin KDVK 29 ve 34 geregince indirilebilirligi
denetlenemez; indirimlerin TAMAMI reddedilir ve fark KDV VUK 30/3 uyarinca
re'sen tarh edilir. Fiil ayni zamanda VUK 359/a-2'de kacakcilik sucudur:
ceza UC KAT ve ayrica vergi suclari raporu duzenlenir.

Capa, mufettisin ornek raporunun KENDI rakamlari: 2021'in yedi dolu ayinin
beyan tablosu buraya aynen alindi; indirimlerin tamami reddedildiginde
odenecek KDV 39.252,03 ve uc kat ceza 117.756,09 cikmali.

Matrah kurali: beyan ile mukellefin DUZENLEDIGI faturalarin toplami
uyusmadiginda VUK 3/B geregi gercek durum esas alinir - ama yalnizca
mukellef ALEYHINE olan yonde. Faturalar beyandan azsa beyan esas alinir.
"""
import io
import os
import sys
import zipfile

KOK = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, KOK)

from app import faturalar as F                                       # noqa: E402
from app import hesap                                                # noqa: E402
from app import ibraz_etmeme_raporu as IB                            # noqa: E402
from app import web_server as W                                      # noqa: E402
from app.satirlar import VERI_KODLARI                                # noqa: E402
from app.tutanak import dolu_donemler                                # noqa: E402

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


# Ornek raporun BEYAN tablosu (2021, yedi dolu ay):
# matrah, toplam KDV, onceki devir, bu donem indirilecek, indirimler,
# odenecek, sonraki devir
ORNEK_BEYAN = [
    (     0.00,  1125.00,     0.00,  2442.75,  2442.75, 0.0,  1317.75),
    (     0.00,     0.00,  1317.75,   516.93,  1834.68, 0.0,  1834.68),
    ( 99970.00,  5970.96,  1834.68, 20785.17, 22619.85, 0.0, 16648.89),
    (249985.00,  4499.73, 16648.89,  8113.66, 24762.55, 0.0, 20262.82),
    (131061.00,  2359.10, 20262.82,  1053.46, 21316.28, 0.0, 18957.18),
    (210132.00,  3782.38, 18957.18,  6994.03, 25951.21, 0.0, 22168.83),
    (403270.00, 21514.86, 22168.83,  3128.78, 25297.61, 0.0,  3782.75),
]
ORNEK_ODENECEK = 39252.03
ORNEK_CEZA = 117756.09


def beyan():
    b = {k: [0.0] * 12 for k in VERI_KODLARI}
    for ay, (m, tk, od, bd, it, ode, sd) in enumerate(ORNEK_BEYAN):
        b["matrah_toplami"][ay] = m
        b["hesaplanan_kdv"][ay] = tk
        b["toplam_kdv"][ay] = tk
        b["onceki_donem_devreden"][ay] = od
        b["bu_donem_indirilecek"][ay] = bd
        b["yurtici_alim_kdv"][ay] = bd
        b["indirimler_toplami"][ay] = it
        b["odenmesi_gereken_kdv"][ay] = ode
        b["sonraki_donem_devreden"][ay] = sd
    return b


def yil_kaydi():
    return {"yil": 2021, "ay_sayisi": 7, "beyan": beyan(),
            "elestiri": hesap.bos_elestiri(), "devir_baslangic": None}


SATIS = [("2021-01-07", "GIB2021000000001", 6250.0, 1125.0),
         ("2021-03-11", "GIB2021000000010", 74220.0, 13359.60)]
ALIS = [("2021-03-15", "GIB2021000000059", 81212.50, 14618.25)]


def ornek(ibraz="İbraz edilmedi", satis=True, uygula=True):
    fat = []
    if satis:
        for tarih, no, m, k in SATIS:
            fat.append({"duzenleyen_vkn": "4444444444",
                        "alici_vkn": "1231231231", "yon": "satis",
                        "tarih": tarih, "fatura_no": no, "matrah": m,
                        "kdv": k, "toplam": m + k, "dahil": True})
    for tarih, no, m, k in ALIS:
        fat.append({"duzenleyen_vkn": "9999999999",
                    "alici_vkn": "4444444444", "yon": "alis",
                    "tarih": tarih, "fatura_no": no, "matrah": m,
                    "kdv": k, "toplam": m + k, "dahil": True})

    yk = yil_kaydi()
    c = {
        "mukellef": {"ad_unvan": "KOMPOZIT AMBALAJ LTD ŞTİ",
                     "vkn_tckn": "4444444444",
                     "vergi_dairesi": "SEYHAN VD", "adres": "SEYHAN / ADANA"},
        "ziya_kati": 3,
        "kunye": {"mukellef_turu": "Kurum (sermaye şirketi)",
                  "faaliyet_konulari": "metal dışı atıkların geri kazanılması",
                  "faaliyet_adresi": "CEMALPAŞA MAH. SEYHAN ADANA",
                  "defter_ibraz": ibraz,
                  "grup_baskanligi": "Adana Denetim Daire Başkanlığının",
                  "is_emirleri": "26.02.2026 | E-2222222-663.05[y]-6817 "
                                 "| 2021 | Sahte Belge Kullanma",
                  "ibraz_yazi_tarihi": "11.04.2025",
                  "ibraz_yazi_sayisi": "E-22222222-000[2015]-13028",
                  "ibraz_teblig_tarihi": "16.04.2025",
                  "ibraz_teblig_alan": "şirket müdürü O.Ç.N.'ye",
                  "ortaklik_bilgileri": "222 | 555 | OÇN | %100 | Müdür",
                  "defter_bilgileri":
                      "2021 | Yevmiye Defteri | 31.12.2020-38435 | "
                      "Adana 15. Noterliği",
                  "vir_bilgileri": "2021 | 11.08.2026 | 2026-[2013]/20",
                  "vsr_savcilik": "Adana",
                  "temsilci_tckn": "11111111110",
                  "kanuni_temsilci": "O Ç N",
                  "eleman_ad": "A BAŞMÜFETTİŞ",
                  "eleman_unvan": "Vergi Başmüfettişi",
                  "tou_talebi": "Talep edilmedi"},
        "yillar": [yk],
        "faturalar": fat,
        "saticilar": {"9999999999": {
            "unvan": "PLASTİK METAL LTD ŞTİ", "kullanma": "Bilerek kullanma",
            "vergi_dairesi": "YENİ BOSNA VD", "vtr_no": "2024-[2014]/36",
            "vtr_tarihi": "18.10.2024", "not": "sahte belge düzenlediği"}},
    }
    if uygula:
        liste = F.normalize(fat, "4444444444")
        el, _d = hesap.ibraz_etmeme_elestirisi(
            yk, F.satis_donem_toplamlari(liste))
        yk["elestiri"] = el
        yk["devir_baslangic"] = 0.0
    return c


def istekci():
    h = W.Istekci.__new__(W.Istekci)
    h.gonderilen = []
    h._belge_gonder = lambda g, a, t: h.gonderilen.append((a, t, g))
    h._ciktilara_yaz = lambda d: None
    return h


# ------------------------------------------------- 0) yon tayini (matrahin
# dayanagi). Mukellefin KENDI duzenledigi belgelerin dokumu cogu zaman TEK
# TARAFLIDIR (yalnizca duzenleyen sutunu). Bu dokum alis sayilirsa matrah
# ilavesi sessizce hic yapilmaz - sahada boyle cikti (2026-10-19).
print("\n0) Fatura yönünün tayini")
M_VKN = "4444444444"
YON_DURUMLARI = [
    ("tek taraflı satış dökümü, VKN girili",
     [{"duzenleyen_vkn": M_VKN, "tarih": "2021-01-15"}], M_VKN, ["satis"]),
    # VKN girilmemisse tahmine guvenilmez: tek saticili bir ALIS listesinin
    # saticisi "mukellef" sanilip butun liste satisa donerdi.
    ("tek taraflı satış dökümü, VKN boş",
     [{"duzenleyen_vkn": M_VKN, "tarih": "2021-01-15"}], None, ["alis"]),
    ("tek satırlı alış dökümü, VKN boş",
     [{"duzenleyen_vkn": "9999999999", "tarih": "2021-01-15"}], None,
     ["alis"]),
    ("tek satıcılı alış listesi, VKN boş",
     [{"duzenleyen_vkn": "9999999999", "tarih": "2021-01-15"},
      {"duzenleyen_vkn": "9999999999", "tarih": "2021-02-15"}], None,
     ["alis", "alis"]),
    ("tek taraflı alış dökümü, VKN girili",
     [{"duzenleyen_vkn": "9999999999", "tarih": "2021-01-15"}], M_VKN,
     ["alis"]),
    ("alıcı sütunlu alış dökümü",
     [{"alici_vkn": M_VKN, "tarih": "2021-01-15"}], M_VKN, ["alis"]),
    ("çift taraflı döküm",
     [{"duzenleyen_vkn": "9999999999", "alici_vkn": M_VKN,
       "tarih": "2021-01-15"},
      {"duzenleyen_vkn": M_VKN, "alici_vkn": "1111111111",
       "tarih": "2021-02-15"}], M_VKN, ["alis", "satis"]),
]
for ad, ham, vkn, beklenen in YON_DURUMLARI:
    bulunan = [f["yon"] for f in F.normalize(ham, vkn)]
    denetle(bulunan == beklenen, "%s → %s" % (ad, beklenen))

# Tek tarafli satis dokumu matrah ilavesini gercekten besliyor mu.
tek_tarafli = F.normalize(
    [{"duzenleyen_vkn": M_VKN, "tarih": "2021-01-15",
      "matrah": 6250.0, "kdv": 1125.0}], M_VKN)
esit((F.satis_donem_toplamlari(tek_tarafli).get((2021, 1)) or {}).get("matrah"),
     6250.0, "tek taraflı satış dökümü dönem toplamına giriyor")


# -------------------------------------------- 1) ornegin rakamlari birebir
print("\n1) Örnek raporun rakamları")
# Satis faturalari olmadan: yalnizca indirimlerin reddi. Ornegin
# duzeltilmis tablosu da matrahi degistirmiyor, bu yuzden olcut bu.
c = ornek(satis=False)
sonuc, _b = W._hesapla(c)
donemler = [d for d in dolu_donemler(sonuc) if d["yil"] == 2021]
esit(sum(d["elestirili"]["toplam_kdv"] for d in donemler), ORNEK_ODENECEK,
     "toplam hesaplanan KDV örnekle aynı")
esit(sum(d["elestirili"]["indirimler"] for d in donemler), 0.0,
     "indirimlerin tamamı reddedildi")
esit(sum(d["elestirili"]["sonraki_devir"] for d in donemler), 0.0,
     "devir zinciri sıfırlandı")
esit(sum(d["tarhiyat"]["resen_tarhi_gereken"] for d in donemler),
     ORNEK_ODENECEK, "re'sen tarhı gereken KDV örnekle aynı")
esit(sum(d["tarhiyat"]["vergi_ziyai_cezasi"] for d in donemler), ORNEK_CEZA,
     "üç kat vergi ziyaı cezası örnekle aynı")

# Ay ay da tutmali; tek bir toplam yanlis dagilimi gizleyebilir.
BEKLENEN_AY = [1125.00, 0.0, 5970.96, 4499.73, 2359.10, 3782.38, 21514.86]
for d, beklenen in zip(sorted(donemler, key=lambda x: x["ay"]), BEKLENEN_AY):
    esit(d["tarhiyat"]["resen_tarhi_gereken"], beklenen,
         "%s re'sen tarhı gereken" % d["ay_adi"])

# ------------------------------------------------------------ 2) matrah kurali
print("\n2) Matrah kuralı")
# Ocak'ta beyan matrahi 0, duzenlenen fatura 6.250 -> matrah yukseltilir.
c_satis = ornek(satis=True)
el = c_satis["yillar"][0]["elestiri"]
esit(el["matrah_ilave"][0], 6250.0,
     "Ocak matrahı düzenlenen faturaya göre yükseltiliyor")
esit(el["hesaplanan_kdv_ilave"][0], 0.0,
     "faturanın KDV'si beyandakiyle aynı olduğundan hesaplanan artmıyor")
denetle(el["hesaplanan_otomatik"][0] is False,
        "hesaplanan KDV orana bölünmüyor, faturanın kendi KDV'si alınıyor")
# Mart'ta beyan matrahi 99.970, fatura 74.220 -> BEYAN esas alinir.
esit(el["matrah_ilave"][2], 0.0,
     "düzenlenen fatura beyandan AZSA matrah indirilmiyor")
# Indirimin tamami her ay reddedilmis olmali.
for ay, (_m, _tk, _od, bd, _it, _o, _sd) in enumerate(ORNEK_BEYAN):
    esit(el["indirim_cikar"][ay], bd,
         "%d. ayın indirimi tamamen reddedildi" % (ay + 1))

# ---------------------------------------------------------- 3) rapor metni
print("\n3) Rapor metni")
c = ornek()
sonuc, _b = W._hesapla(c)
m = IB.rapor_uret(W._inceleme_bilgisi(c), c["kunye"], sonuc, c, 2021).duz_metin()

for baslik in ("1- GİRİŞ", "2- USUL İNCELEMELERİ", "3- HESAP İNCELEMELERİ",
               "4- TESPİT VE TENKİT EDİLEN HUSUSLAR",
               "4.1- Re’sen Takdir Nedeni", "4.2- Re’sen Takdir Verileri",
               "4.2.1- Yasal Defter ve Belgelerin İncelemeye İbraz "
               "Edilmemesi",
               "4.2.2- Mükellef Tarafından Düzenlenen ve Mükellef Adına "
               "Düzenlenen Belgeler",
               "4.2.3- Konuya İlişkin Yasal Düzenlemeler",
               "4.2.4- Olması Gereken Katma Değer Vergisi Beyan Tablosu",
               "5- SONUÇ"):
    denetle(baslik in m, "bölüm var: %s" % baslik.split("-")[0].strip())

# Re'sen takdir nedeni: ibraz etmeme 30/3, duzenlenen belgelerin beyan
# disi birakilmasi ise beyannamelerin gercek durumu yansitmadigina DELIL
# oldugundan 30/6. Mufettisin karari (2026-10-20): matrah ilavesi varsa
# ikisi birlikte yazilir.
denetle("30 uncu maddesinin (3) ve (6) numaralı bentleri" in m,
        "matrah ilavesi varsa 30/3 ve 30/6 birlikte anılıyor")
denetle("md. 30/3" in m and "md. 30/6" in m,
        "iki bendin metni de yazılıyor")
denetle("beyannamelerin gerçek durumu yansıtmadığına dair delil "
        "niteliğinde" in m, "30/6'nın dayandığı delil açıklanıyor")
denetle("359/a-2 maddesine göre “defter, kayıt ve belgeleri gizlemek”" in m,
        "sonuç 359/a-2'den suç duyurusu istiyor")
denetle("Vergi Suçları Raporu düzenlenmesi" in m,
        "sonuç VSR düzenlenmesini istiyor")
denetle("üç kat vergi ziyaı cezası" in m, "üç kat ceza isteniyor")
denetle("%s" % "117.756,09" in m, "ceza tutarı metinde geçiyor")
denetle("39.252,03" in m, "tarhiyat tutarı metinde geçiyor")

# Iki belge dokumu de rapora girmeli.
denetle("Mükellef Tarafından Düzenlenen Belgeler" in m,
        "düzenlenen belgeler tablosu var")
denetle("Mükellef Adına Düzenlenen Belgeler" in m,
        "adına düzenlenen belgeler tablosu var")
denetle("GIB2021000000001" in m and "GIB2021000000059" in m,
        "iki dökümün satırları yazılıyor")

denetle("İbraz edilen defterler" not in m and "Adana 15. Noterliği" in m,
        "tasdikli defter bilgileri künyeden geliyor")
denetle("OÇN" in m and "Müdür" in m, "ortaklık tablosu yazılıyor")

# Belge basim bilgileri: VARSA tablo yazilir, yoksa hic yazilmaz (e-belgeye
# gecmis mukellefte bu kayit bulunmuyor; kirmizi yer tutucu yanlis olurdu).
denetle("İbraz Edilmeyen Belgelerin Basım Bilgileri" not in m,
        "basım kaydı girilmemişse tablo yazılmıyor")
denetle("anlaşmalı matbaalara bastırdığı" not in m,
        "basım kaydı yoksa sorgulama cümlesi de yazılmıyor")

c_basim = ornek()
c_basim["kunye"]["belge_basim_bilgileri"] = (
    "H A | 11.10.2013 | Fatura | A | 539001 | 539500 | 10\n"
    "A Y | 02.11.2018 | İrsaliyeli Fatura | A | 253651 | 253900 | 5")
m_basim = IB.rapor_uret(W._inceleme_bilgisi(c_basim), c_basim["kunye"],
                        W._hesapla(c_basim)[0], c_basim, 2021).duz_metin()
denetle("İbraz Edilmeyen Belgelerin Basım Bilgileri" in m_basim,
        "basım kaydı varsa tablo yazılıyor")
denetle("anlaşmalı matbaalara bastırdığı belgelere ilişkin basım "
        "bilgilerinin" in m_basim, "tabloya gönderme yapan cümle yazılıyor")
denetle("539001" in m_basim and "253900" in m_basim,
        "iki basım satırı da yazılıyor")
denetle("Anlaşmalı Matbaa" in m_basim and "Belge Adedi" in m_basim,
        "başlıklar alan bildiriminden geliyor")
# Tablo, defterlerin varligini ortaya koyan 4.2.1 bolumunde kalmali.
denetle(m_basim.find("Basım Bilgileri")
        < m_basim.find("4.2.2- Mükellef Tarafından Düzenlenen"),
        "basım tablosu 4.2.1 bölümünde yazılıyor")
denetle("11.04.2025" in m and "16.04.2025" in m,
        "isteme yazısı ve tebliğ tarihleri yazılıyor")
denetle("Kurumlar Vergisi ve Kurum Geçici Vergisi yönünden" in m,
        "gelir/kurumlar yönünden işlem olmadığı yazılıyor")
# Cift ilgi eki olmamali ("kurumun ... doneminin ... islemlerinin").
denetle("döneminin" not in m, "üst üste ilgi eki yok")

# Iki dokumun rapordaki islevi AYRI ve bu okuyana soyleniyor.
denetle("katma değer vergisi matrahının" in m
        and "indirim konusu yapılan katma değer vergisinin dayanağıdır" in m,
        "düzenlenen belgeler matraha, adına düzenlenenler indirime bağlanıyor")

# Matrah ilavesinin dayanagi VUK DEGIL, KDV Kanununun kendi hukumleri
# (mufettisin karari, 2026-10-19): fatura duzenlenmisse vergiyi doguran
# olay gerceklesmis, faturada KDV gosterilmisse o vergi odenmesi gereken
# vergi haline gelmistir.
denetle("3 üncü maddesinin (B) fıkrası" not in m,
        "matrah ilavesi artık VUK 3/B'ye dayandırılmıyor")
denetle("10 uncu maddesinin (a) bendinde" in m
        and "belgelerde gösterilen miktarla sınırlı olmak üzere" in m,
        "vergiyi doğuran olay KDVK 10/a-b ile kuruluyor")
denetle("8 inci maddesinin ikinci fıkrası" in m
        and "bu vergiyi ödemekle mükellef" in m,
        "faturada KDV gösterilmişse ödeme mecburiyeti KDVK 8/2'ye bağlanıyor")
denetle("beyan edilip ödenmesi gereken bir vergi hâline gelmiştir" in m,
        "hesaplanan KDV'nin beyan zorunluluğu sonucu yazılıyor")
denetle("40 ıncı maddesi" in m and "yazılı beyanları üzerine tarh" in m,
        "beyan esası KDVK 40'a dayandırılıyor")
denetle("1 inci maddesinin birinci fıkrası" in m
        and "20 nci maddesine göre teslim ve hizmet işlemlerinde matrah" in m,
        "verginin konusu ve matrah KDVK 1 ve 20 ile kuruluyor")
denetle("teslim sayılan haller ise 3 üncü maddede" in m,
        "teslim sayılan haller anılıyor")
# Maddelerin METINLERI de 4.2.3'e girmeli, yalnizca atif yetmez.
denetle("md. 10 — Vergiyi Doğuran Olayın Meydana Gelmesi" in m
        and "md. 8/2 — Belgede Gösterilen Verginin Ödenmesi" in m,
        "KDVK madde metinleri yasal düzenlemeler bölümüne giriyor")

# Degerlendirme paragrafi: yalnizca madde atfi degil, GEREKCE ve yontem de
# yazilmali (mufettisin istegi, 2026-10-19).
denetle("ilgili dönem katma değer vergisi beyannamesine yansıtmadığı "
        "belgeler" in m, "beyan dışı bırakılan belgelere bağlanıyor")
denetle("yalnızca mükellef kurumun aleyhine olan yönde ilave" in m,
        "yalnızca aleyhe yönde ilave yapıldığı yazılıyor")
denetle("beyan esas alınarak matrah indirilmemiştir" in m,
        "belgeler beyandan azsa beyanın esas alındığı yazılıyor")
denetle("matraha oran uygulanmak suretiyle bulunmamıştır" in m,
        "hesaplanan KDV'nin kaynağı açıklanıyor")
# Mufettisin sozu (2026-10-20): "asil onemli olan faturada tahsil edilen
# KDV fazla hesaplasa da beyan etmek zorunda". Dayanak KDVK 8/2.
denetle("kanunen hesaplanması gerekenden fazla dahi olsa, beyan edilip "
        "ödenmesi gereken vergidir" in m,
        "fazla hesaplanmış KDV'nin de beyan zorunluluğu yazılıyor")
denetle("Beyan Edilmeyen Belgelere İlişkin Matrah ve Katma Değer "
        "Vergisi İlavesi" in m,
        "dönem dönem karşılaştırma tablosu yazılıyor")
denetle("Düzenlenen\nBelgelerin Matrahı" in m
        and "Matraha\nİlave" in m,
        "tablonun matrah sütunları karşılaştırmayı gösteriyor")
# Mufettisin istegi (2026-10-20): faturalardaki hesaplanan KDV ile
# beyannamedeki hesaplanan KDV de KIYASLANSIN.
# Olcu, beyannamenin TOPLAM KDV satiridir (mufettisin karari,
# 2026-10-20): "hesaplanan kdv sutunu deme de toplam kdv sutunu koy".
denetle("Düzenlenen\nBelgelerin KDV’si" in m
        and "Beyan Edilen\nToplam KDV" in m
        and "Toplam KDV’ye\nİlave" in m,
        "tabloda KDV karşılaştırması Toplam KDV olarak var")
denetle("Hesaplanan KDV’ye" not in m,
        "sütun adı artık “hesaplanan” değil")
denetle("beyannamenin TOPLAM KATMA DEĞER VERGİSİ satırıdır" in m,
        "ölçünün Toplam KDV satırı olduğu yazılıyor")
denetle("2021/Ocak" in m and "6.250,00" in m,
        "tabloda ilave yapılan dönem ve tutarı var")
# Ilave yapilmayan donemler TABLOYA girmemeli: "—" dolu satir yaniltir.
# Olcut tablonun KENDISI olmali; "2021/Mart" raporun baska tablolarinda
# (beyan dokumu, tarhiyat) zaten geciyor.
_bas = m.find("Beyan Edilmeyen Belgelere İlişkin Matrah ve Katma")
_ilave_tablosu = m[_bas:m.find("Buna göre", _bas)]
denetle("2021/Ocak" in _ilave_tablosu,
        "ilave yapılan dönem tabloda")
denetle("2021/Mart" not in _ilave_tablosu,
        "ilave yapılmayan dönem tabloya girmiyor")
m_satissiz = IB.rapor_uret(W._inceleme_bilgisi(ornek(satis=False)),
                           ornek(satis=False)["kunye"],
                           W._hesapla(ornek(satis=False))[0], ornek(satis=False),
                           2021).duz_metin()
denetle("8 inci maddesinin ikinci fıkrası" not in m_satissiz,
        "matrah ilavesi yoksa KDVK gerekçe paragrafı yazılmıyor")
denetle("30 uncu maddesinin (3) numaralı bendi" in m_satissiz
        and "(3) ve (6) numaralı bentleri" not in m_satissiz,
        "matrah ilavesi yoksa yalnızca 30/3'e dayanılıyor")
denetle("md. 30/6" not in m_satissiz,
        "delil yoksa 30/6 metni de yazılmıyor")
denetle("md. 8/2 — Belgede Gösterilen Verginin Ödenmesi" not in m_satissiz,
        "matrah ilavesi yoksa KDVK maddeleri de listelenmiyor")


# ------------------------------------------- 3b) ceza kati KAYNAGA gore
# Mufettisin karari (2026-10-19): matrah farkindan (beyan disi birakilan
# belgelerden) dogan tutara BIR kat, defter-belge ibraz etmemekten yani
# indirimlerin reddinden dogan tutara UC kat.
print("\n3b) Ceza katı kaynağına göre ayrılıyor")
c_ayrim = ornek()
e_a = c_ayrim["yillar"][0]["elestiri"]
e_a["matrah_ilave"][1] = 100000.0          # Şubat: beyan dışı belge
e_a["hesaplanan_kdv_ilave"][1] = 18000.0
e_a["hesaplanan_otomatik"][1] = False
sonuc_a, _b = W._hesapla(c_ayrim)
subat = next(d for d in sonuc_a["donemler"] if d["ay"] == 2)
ocak = next(d for d in sonuc_a["donemler"] if d["ay"] == 1)
esit(subat["tarhiyat"]["ceza_matrah_payi"], 18000.0,
     "Şubat tarhı matrah farkından sayılıyor")
esit(subat["tarhiyat"]["vergi_ziyai_cezasi"], 18000.0,
     "matrah farkına BİR kat (18.000 x 1)")
esit(ocak["tarhiyat"]["ceza_indirim_payi"], 1125.0,
     "Ocak tarhı indirim reddinden sayılıyor")
esit(ocak["tarhiyat"]["vergi_ziyai_cezasi"], 3375.0,
     "indirim reddine ÜÇ kat (1.125 x 3)")
# Paylarin toplami tarhin tamamini kapsamali; bir tutar cezasiz kalmamali.
for d in sonuc_a["donemler"]:
    t = d["tarhiyat"]
    esit(round(t["ceza_matrah_payi"] + t["ceza_indirim_payi"], 2),
         t["resen_tarhi_gereken"],
         "%s payları tarhın tamamını kapsıyor" % d["ay_adi"])

m_a = IB.rapor_uret(W._inceleme_bilgisi(c_ayrim), c_ayrim["kunye"],
                    sonuc_a, c_ayrim, 2021).duz_metin()
for baslik in ("Beyan Dışı Bırakılan\nBelgelerden",
               "İbraz Etmemeden\n(İndirim Reddi)",
               "Vergi Ziyaı\nCezası (1 kat)",
               "Vergi Ziyaı\nCezası (3 kat)",
               "Vergi Ziyaı Cezası\nToplamı"):
    denetle(baslik in m_a, "sütun var: %s" % baslik.replace("\n", " "))
denetle("vergi ziyaı cezasının katı bu iki tespitte AYNI DEĞİLDİR" in m_a,
        "iki katın gerekçesi yazılıyor")
denetle("birinci fıkrası gereğince BİR KAT" in m_a,
        "matrah farkı 344/1'e bağlanıyor")
denetle("ikinci fıkrası gereğince ÜÇ KAT" in m_a,
        "indirim reddi 344/2'ye bağlanıyor")
# Toplam satiri: 18.000 x 1 + 39.252,03 x 3 = 135.756,09
denetle("135.756,09" in m_a, "ceza toplamı iki katın toplamı")
denetle("18.000,00\t39.252,03" in m_a,
        "kaynak payları dönem toplamında ayrı duruyor")
# Sonuc maddesi de iki kati istemeli, tek cumleyle "uc kat" dememeli.
sonuc_blok = m_a[m_a.find("5.1-"):]
denetle("bir kat, defter ve belgelerin ibraz edilmemesi" in sonuc_blok,
        "sonuç maddesi iki katı ayrı ayrı istiyor")

# Matrah payi YOKSA tablo daralmali ve tek cumle yazilmali.
denetle("Beyan Dışı Bırakılan" not in m,
        "matrah payı yoksa kaynak sütunları yazılmıyor")
denetle("tamamı defter ve belgelerin ibraz edilmemesi nedeniyle "
        "indirimlerin reddinden kaynaklandığından" in m,
        "matrah payı yoksa tek cümle yazılıyor")
denetle("117.756,09" in m, "tek katta ceza üç kat olarak yazılıyor")

# --------------------------------------------------- 4) uc noktaya baglanti
print("\n4) Rapor indirilirken")
h = istekci()
c = ornek()
belgeler, inceleme, vsr = h._ibraz_raporu_hazirla({"calisma": c})
denetle([y for y, _b, _a in belgeler] == [2021], "2021 için rapor üretiliyor")
denetle(vsr is not None, "VSR de üretiliyor (fiil 359/a-2 kapsamında)")
h._ibraz_raporu_gonder({"calisma": c})
ad, tur, govde = h.gonderilen[-1]
denetle(tur == "application/zip", "rapor ve VSR zip içinde iniyor")
with zipfile.ZipFile(io.BytesIO(govde)) as z:
    icerik = sorted(z.namelist())
denetle(any("Ibraz_etmeme_raporu" in n for n in icerik),
        "pakette ibraz etmeme raporu var")
denetle(any("Vergi_suclari_raporu" in n for n in icerik),
        "pakette VSR var")

# Kunye "İbraz edilmedi" degilse rapor uretilmemeli.
h2 = istekci()
try:
    h2._ibraz_raporu_hazirla({"calisma": ornek(ibraz="İbraz edildi")})
    denetle(False, "ibraz edilmişse rapor üretimi engelleniyor")
except W.ApiHata as hata:
    denetle("İbraz edilmedi" in str(hata),
            "ibraz edilmişse anlaşılır hata veriliyor")

# Kural UYGULANMADAN rapor inmemeli: belge "indirimlerin tamami
# reddedilmistir" der ama tablolar bos cikar ve celiski vergi dairesine
# gider. Elle girilmis elestiri varsa engel yok.
h5 = istekci()
try:
    h5._ibraz_raporu_hazirla({"calisma": ornek(uygula=False)})
    denetle(False, "kural uygulanmadan rapor üretimi engelleniyor")
except W.ApiHata as hata:
    denetle("henüz uygulanmamış" in str(hata),
            "kural uygulanmadan rapor üretimi engelleniyor")
    denetle("düğmesine basın" in str(hata),
            "hata ne yapılacağını söylüyor")

# Elestiriyi dolduran akis
h3 = istekci()
yan = h3._ibraz_elestirisi({"calisma": ornek(uygula=False)})
gelen = yan["yillar"][0]["elestiri"]
esit(gelen["indirim_cikar"][2], 20785.17,
     "akış indirimin tamamını reddediyor")
esit(gelen["matrah_ilave"][0], 6250.0, "akış matrahı da yükseltiyor")

# Arayuz iletisinin DOGRU seyi soyleyebilmesi icin ozet. Daha once ileti her
# durumda "matrahlar yukseltildi" diyordu; duzenlenen fatura girilmemisken
# de boyle yaziyordu ve mufettis ilavenin yapildigini saniyordu.
ozet = yan["ozet"]
esit(ozet["matrah_donem"], 1, "özet, matrah yükseltilen dönem sayısını veriyor")
denetle(ozet["indirim_donem"] == 7, "özet, indirimi reddedilen dönemleri sayıyor")
denetle(ozet["satis_adet"] >= 1, "özet, düzenlenen fatura adedini veriyor")
esit(ozet["donemsiz_satis"], 0, "dönemi çözülemeyen satış faturası yok")

# Duzenlenen fatura HIC yoksa ozet bunu soylemeli (arayuz uyari gosterir).
h4 = istekci()
c_satissiz = ornek(satis=False, uygula=False)
ozet_bos = h4._ibraz_elestirisi({"calisma": c_satissiz})["ozet"]
esit(ozet_bos["matrah_donem"], 0, "satış yoksa matrah ilavesi yapılmıyor")
esit(ozet_bos["satis_adet"], 0, "satış yoksa özet bunu bildiriyor")
denetle(ozet_bos["indirim_donem"] > 0,
        "satış yokken de indirimlerin reddi sürüyor")


# ------------------------------------- 5) iptal/itiraz tikinin etkisi
# Sahada cikti (2026-10-19): bir satirin iptal/itiraz tiki kaldirilinca
# satis dokumu degisiyor ama BIR KEZ yazilmis matrah ilavesi oldugu yerde
# kaliyordu. "Tik yoksa hesaba dahil edilmeli."
print("\n5) İptal/itiraz tiki ve matrah ilavesi")
h6 = istekci()


def satis_iptali(c, deger):
    for f in c["faturalar"]:
        if f.get("duzenleyen_vkn") == c["mukellef"]["vkn_tckn"]:
            f["iptal"] = deger


def elestiriyi_yaz(c, yan):
    for y in yan["yillar"]:
        kayit = next(k for k in c["yillar"] if k["yil"] == y["yil"])
        kayit["elestiri"] = y["elestiri"]


c_iptal = ornek(uygula=False)
satis_iptali(c_iptal, True)
elestiriyi_yaz(c_iptal, h6._ibraz_elestirisi({"calisma": c_iptal}))
esit(c_iptal["yillar"][0]["elestiri"]["matrah_ilave"][0], 0.0,
     "iptal işaretliyken matraha dahil edilmiyor")

# Tik kaldirilinca dokum degisiyor; "Matraha Aktar" bunu yaziyor.
satis_iptali(c_iptal, False)
liste_i = F.normalize(c_iptal["faturalar"], c_iptal["mukellef"]["vkn_tckn"])
esit((F.satis_donem_toplamlari(liste_i).get((2021, 1)) or {}).get("matrah"),
     6250.0, "tik kaldırılınca döküm faturayı görüyor")
yan_m = h6._matrah_ilavesi({"calisma": c_iptal})
esit(yan_m["ozet"]["matrah_donem"], 1, "akış bir dönemde ilave yazıyor")
elestiriyi_yaz(c_iptal, yan_m)
esit(c_iptal["yillar"][0]["elestiri"]["matrah_ilave"][0], 6250.0,
     "tik yoksa matraha dahil ediliyor")
# INDIRIM tarafina dokunulmamali: iki akis ayri kalemleri yaziyor.
esit(c_iptal["yillar"][0]["elestiri"]["indirim_cikar"][0], 2442.75,
     "matrah akışı indirim reddine dokunmuyor")
esit(W._hesapla(c_iptal)[0]["donemler"][0]["fark_tespit"]["matrah"], 6250.0,
     "hesap matrah farkını görüyor")

# Tik GERI konulursa once yazilmis ilave de kalkmali; yoksa dokumle
# tutmayan bir tutar asili kalir.
satis_iptali(c_iptal, True)
yan_g = h6._matrah_ilavesi({"calisma": c_iptal})
esit(yan_g["yillar"][0]["elestiri"]["matrah_ilave"][0], 0.0,
     "tik geri konulunca ilave kaldırılıyor")
esit(yan_g["yillar"][0]["elestiri"]["indirim_cikar"][0], 2442.75,
     "geri alırken de indirim reddi korunuyor")


# ------------------------- 6) ILAVE EDILECEK KDV ile beyan edilmis vergi
# Sahada cikti (2026-10-20): mukellef Ocak'ta matrahi HIC beyan etmemis
# ama duzenledigi faturanin 1.125 TL KDV'sini "Ilave Edilecek KDV"
# satirinda beyan etmisti. Hesaplanan KDV ilavesi yalnizca
# "hesaplanan_kdv" ile karsilastirilinca ayni vergi bir kez daha eklenip
# odenecek KDV iki katina cikiyordu (1.125 yerine 2.250).
print("\n6) İlave Edilecek KDV satırında beyan edilmiş vergi")


def ilave_ornegi(ilave_edilecek):
    beyan = {k: [0.0] * 12 for k in VERI_KODLARI}
    beyan["bu_donem_indirilecek"][0] = 2442.75
    beyan["indirimler_toplami"][0] = 2442.75
    beyan["ilave_edilecek_kdv"][0] = ilave_edilecek
    return {
        "mukellef": {"ad_unvan": "ÖRNEK LTD", "vkn_tckn": "4444444444",
                     "vergi_dairesi": "SEYHAN VD", "adres": "ADANA"},
        "ziya_kati": 3,
        "kunye": {"mukellef_turu": "Kurum (sermaye şirketi)",
                  "defter_ibraz": "İbraz edilmedi"},
        "yillar": [{"yil": 2021, "ay_sayisi": 1, "beyan": beyan,
                    "elestiri": hesap.bos_elestiri()}],
        # Mukellefin duzenledigi tek fatura: 6.250 matrah, 1.125 KDV.
        "faturalar": [{"duzenleyen_vkn": "4444444444",
                       "alici_vkn": "5350030213", "tarih": "2021-01-07",
                       "fatura_no": "GIB2021000000001", "matrah": 6250.0,
                       "kdv": 1125.0, "toplam": 7375.0}],
        "saticilar": {},
    }


h7 = istekci()
c_ilave = ilave_ornegi(1125.00)
c_ilave["yillar"][0]["elestiri"] = \
    h7._ibraz_elestirisi({"calisma": c_ilave})["yillar"][0]["elestiri"]
c_ilave["yillar"][0]["devir_baslangic"] = 0.0
e_i = c_ilave["yillar"][0]["elestiri"]
esit(e_i["matrah_ilave"][0], 6250.0, "matrah ilavesi yapılıyor (beyan 0)")
esit(e_i["hesaplanan_kdv_ilave"][0], 0.0,
     "KDV zaten beyan edilmiş; ikinci kez eklenmiyor")
d_i = W._hesapla(c_ilave)[0]["donemler"][0]
esit(d_i["elestirili"]["toplam_kdv"], 1125.0,
     "toplam KDV faturanın KDV'si kadar (iki katı DEĞİL)")
esit(d_i["elestirili"]["odenecek"], 1125.0, "ödenecek KDV 1.125 (2.250 değil)")
esit(d_i["tarhiyat"]["resen_tarhi_gereken"], 1125.0, "re'sen tarh 1.125")

# Ilave edilecek satirinda bir sey YOKSA eski davranis surmeli: faturanin
# KDV'si hesaplanan ilavesi olarak eklenir.
c_yok = ilave_ornegi(0.0)
c_yok["yillar"][0]["elestiri"] = \
    h7._ibraz_elestirisi({"calisma": c_yok})["yillar"][0]["elestiri"]
c_yok["yillar"][0]["devir_baslangic"] = 0.0
esit(c_yok["yillar"][0]["elestiri"]["hesaplanan_kdv_ilave"][0], 1125.0,
     "beyan edilmemişse KDV ilave ediliyor")
esit(W._hesapla(c_yok)[0]["donemler"][0]["elestirili"]["odenecek"], 1125.0,
     "o halde de ödenecek 1.125")

# Tablo, ilave edilecek KDV tasiyan dosyada o sutunu YAZMALI; yoksa
# hesaplanan KDV sifir gorunurken odenecek vergi cikar ve tablo kendi
# icinde tutmaz.
m_i = IB.rapor_uret(W._inceleme_bilgisi(c_ilave), c_ilave["kunye"],
                    W._hesapla(c_ilave)[0], c_ilave, 2021).duz_metin()
denetle("İlave Edil. KDV" in m_i,
        "ilave edilecek KDV sütunu tabloya giriyor")
denetle("İlave Edil. KDV" not in m,
        "taşımayan dosyada sütun yazılmıyor")


# --------------------------- 7) KDV'si sifir belgeler: istisna / ozel matrah
# Mufettisin tespiti (2026-10-20): beyan disi sandigi faturalarin KDV'si
# sifirdi ve bunlar OZEL MATRAH olarak beyan edilmisti. Uygulama matraha
# ilave etmeden once uyarmali.
print("\n7) KDV'si sıfır belgeler istisna / özel matrah olabilir")


def kdvsiz_ornegi(ozel_matrah=0.0, istisna=0.0):
    beyan = {k: [0.0] * 12 for k in VERI_KODLARI}
    beyan["ozel_matrah_bedel"][0] = ozel_matrah
    beyan["tam_istisna_teslim"][0] = istisna
    return ({"yil": 2021, "ay_sayisi": 1, "beyan": beyan,
             "elestiri": hesap.bos_elestiri()},
            F.normalize([
                {"duzenleyen_vkn": "4444444444", "alici_vkn": "1",
                 "tarih": "2021-01-07", "matrah": 6250.0, "kdv": 1125.0},
                {"duzenleyen_vkn": "4444444444", "alici_vkn": "2",
                 "tarih": "2021-01-15", "matrah": 26280.0, "kdv": 0.0},
                {"duzenleyen_vkn": "4444444444", "alici_vkn": "3",
                 "tarih": "2021-01-15", "matrah": 24850.0, "kdv": 0.0}],
                "4444444444"))


yil_kaydi, liste_k = kdvsiz_ornegi(ozel_matrah=51130.0)
satir_k = F.satis_beyan_farki(liste_k, [yil_kaydi])[0]
esit(satir_k["kdvsiz_adet"], 2, "KDV'si sıfır belge sayısı ayrı tutuluyor")
esit(satir_k["kdvsiz_matrah"], 51130.0, "KDV'siz belgelerin matrahı")
esit(satir_k["beyan_ozel_matrah"], 51130.0,
     "beyannamedeki özel matrah okunuyor")
bulgu = [b for b in F.bulgular(liste_k, [yil_kaydi], {})
         if b["tur"] == "kdvsiz_satis"]
denetle(len(bulgu) == 1, "uyarı bulgusu çıkıyor")
# Bos listede coken bir denetim, kendisinden SONRAKI denetimleri de
# gizler; mesaj yoksa bos metinle devam edilir.
_mesaj = bulgu[0]["mesaj"] if bulgu else ""
denetle("beyan dışı olmayabilir" in _mesaj,
        "beyanda karşılığı varsa uyarı bunu söylüyor")
denetle("51.130,00" in _mesaj, "tutarlar uyarıda yazılı")

# Istisna bolumunden okunursa da ayni uyari cikmali.
yil_i, liste_i2 = kdvsiz_ornegi(istisna=51130.0)
esit(F.satis_beyan_farki(liste_i2, [yil_i])[0]["beyan_istisna"], 51130.0,
     "istisna bölümü de okunuyor")

# Beyanda karsiligi YOKSA uyari yine cikar ama baska soyler.
yil_y, liste_y = kdvsiz_ornegi()
bulgu_y = [b for b in F.bulgular(liste_y, [yil_y], {})
           if b["tur"] == "kdvsiz_satis"]
denetle(len(bulgu_y) == 1, "beyanda karşılığı yokken de uyarı çıkıyor")
denetle("tutar görünmüyor" in (bulgu_y[0]["mesaj"] if bulgu_y else ""),
        "karşılığı yoksa uyarı bunu söylüyor")

# KDV'si sifir belge YOKSA uyari CIKMAMALI.
liste_t = F.normalize([{"duzenleyen_vkn": "4444444444", "alici_vkn": "1",
                        "tarih": "2021-01-07", "matrah": 6250.0,
                        "kdv": 1125.0}], "4444444444")
denetle(not [b for b in F.bulgular(liste_t, [yil_y], {})
             if b["tur"] == "kdvsiz_satis"],
        "KDV'si sıfır belge yoksa uyarı çıkmıyor")


# Rapor da susmamali: KDV'si sifir belgeler ve beyannamedeki karsiliklari
# 4.2.4'te bir paragraf olarak yaziliyor (mufettisin istegi: "hatta
# rapora bir paragraf eklesin").
def ibraz_raporu(c):
    return IB.rapor_uret(W._inceleme_bilgisi(c), c["kunye"],
                         W._hesapla(c)[0], c, 2021).duz_metin()


def kdvsiz_calisma(ozel_matrah):
    beyan = {k: [0.0] * 12 for k in VERI_KODLARI}
    beyan["bu_donem_indirilecek"][0] = 2442.75
    beyan["indirimler_toplami"][0] = 2442.75
    beyan["ilave_edilecek_kdv"][0] = 1125.0
    beyan["toplam_kdv"][0] = 1125.0
    beyan["ozel_matrah_bedel"][0] = ozel_matrah
    c = {"mukellef": {"ad_unvan": "ÖRNEK LTD", "vkn_tckn": "4444444444",
                      "vergi_dairesi": "SEYHAN VD", "adres": "ADANA"},
         "ziya_kati": 3,
         "kunye": {"mukellef_turu": "Kurum (sermaye şirketi)",
                   "defter_ibraz": "İbraz edilmedi"},
         "yillar": [{"yil": 2021, "ay_sayisi": 1, "beyan": beyan,
                     "elestiri": hesap.bos_elestiri()}],
         "faturalar": [
             {"duzenleyen_vkn": "4444444444", "alici_vkn": "1",
              "tarih": "2021-01-07", "matrah": 6250.0, "kdv": 1125.0},
             {"duzenleyen_vkn": "4444444444", "alici_vkn": "2",
              "tarih": "2021-01-15", "matrah": 26280.0, "kdv": 0.0}],
         "saticilar": {}}
    h = istekci()
    c["yillar"][0]["elestiri"] = \
        h._ibraz_elestirisi({"calisma": c})["yillar"][0]["elestiri"]
    c["yillar"][0]["devir_baslangic"] = 0.0
    return c


m_ortulu = ibraz_raporu(kdvsiz_calisma(26280.0))
denetle("26.280,00 TL tutarındaki kısmı, üzerinde katma değer vergisi "
        "hesaplanmamış belgelerden oluşmaktadır" in m_ortulu,
        "rapor KDV'siz belgelerin tutarını yazıyor")
denetle("istisna kapsamına giren işlemler ile özel matrah şekline tabi "
        "işlemlere ilişkin bölümlerinde toplam 26.280,00 TL beyan" in m_ortulu,
        "beyannamedeki karşılığı yazılıyor")
denetle("hesaplanan katma değer vergisine ilave yapılmamıştır" in m_ortulu,
        "üzerlerinden vergi hesaplanmadığı yazılıyor")
denetle("anılan bölümlerde de beyan edilmemiştir" not in m_ortulu,
        "tamamı beyan edilmişse açıkta kalan cümlesi yazılmıyor")

m_acik = ibraz_raporu(kdvsiz_calisma(10000.0))
denetle("16.280,00 TL’lik kısmı ise anılan bölümlerde de beyan edilmemiştir"
        in m_acik, "açıkta kalan tutar yazılıyor")
m_yok = ibraz_raporu(kdvsiz_calisma(0.0))
denetle("herhangi bir beyan bulunmadığı görülmüştür" in m_yok,
        "beyanda hiç karşılığı yoksa öyle yazılıyor")
denetle("0,00 TL beyan bulunduğu" not in m_yok,
        "sıfırlı garip cümle kurulmuyor")
# KDV'si sifir belge YOKSA paragraf hic yazilmamali.
denetle("üzerinde katma değer vergisi hesaplanmamış belgelerden" not in m,
        "KDV'si sıfır belge yoksa paragraf yazılmıyor")

print()
if HATA:
    print("BAŞARISIZ: %d denetim" % len(HATA))
    for x in HATA:
        print("  -", x)
    sys.exit(1)
print("Tüm denetimler geçti.")
