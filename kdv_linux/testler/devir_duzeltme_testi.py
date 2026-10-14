# -*- coding: utf-8 -*-
"""Devir duzeltme raporunun gerileme denetimi.

    python3 testler/devir_duzeltme_testi.py

Sahte belge kullanma raporu bir yilin indirimlerini reddettiginde o yilin
Aralik devri kuculur. Devir ileriye aktigi icin INCELENMEYEN sonraki
yillarin beyanlari da gercek durumu yansitmaz hale gelir; kucuk devirle
yeniden kurulan zincirde bir donemde odenecek vergi dogarsa o yil icin ayri
bir rapor duzenlenir (mufettisin ornek raporu, 2026-10-14).

Fikstur devir zincirini ELLE kuruyor, cunku beyan bloku gercekte
beyannameden gelir ve devir sutunlarini kendisi tasir. Denetimin anlamli
olmasi icin sahada olan sey birebir kurulmali:

  2022 (incelenen): indirim > hesaplanan, devir birikiyor; 8.000/ay red
                    -> Aralik devri 120.000 yerine 24.000
  2023 (sonraki)  : kucuk devir eriyor, Mayis'tan itibaren odenecek cikiyor
                    -> fark 36.000, devir duzeltme raporu gerekiyor

Dikkat - fikstur yazarken iki kez tuzaga dusuldu:
  - Beyan bloguna `onceki_donem_devreden` / `sonraki_donem_devreden`
    yazilmazsa beyan devri sifir kalir ve "olmasi gereken" devirden BUYUK
    gorunur; rapor tersine okunur.
  - `odenmesi_gereken_kdv` yazilmazsa beyan edilen odenecek sifir olur ve
    yil, devirle ilgisi olmayan bir fark uretir. `rapor_yillari` bu yuzden
    devrin GERCEKTEN degistigini de ariyor.
"""
import io
import os
import sys
import zipfile

KOK = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, KOK)

from app import devir_duzeltme_raporu as D                           # noqa: E402
from app import faturalar as F                                       # noqa: E402
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


# ------------------------------------------------------------------- fikstur
def yil_beyan(onceki_devir, hesaplanan, indirim):
    """Bir yilin beyan blogu; devir zinciri ay ay elle kurulur."""
    b = {k: [0.0] * 12 for k in VERI_KODLARI}
    devir = onceki_devir
    for ay in range(12):
        b["matrah_toplami"][ay] = round(hesaplanan / 0.18, 2)
        b["hesaplanan_kdv"][ay] = hesaplanan
        b["toplam_kdv"][ay] = hesaplanan
        b["yurtici_alim_kdv"][ay] = indirim
        b["bu_donem_indirilecek"][ay] = indirim
        b["onceki_donem_devreden"][ay] = devir
        toplam_indirim = devir + indirim
        b["indirimler_toplami"][ay] = toplam_indirim
        if toplam_indirim >= hesaplanan:
            b["odenmesi_gereken_kdv"][ay] = 0.0
            devir = round(toplam_indirim - hesaplanan, 2)
        else:
            b["odenmesi_gereken_kdv"][ay] = round(hesaplanan - toplam_indirim, 2)
            devir = 0.0
        b["sonraki_donem_devreden"][ay] = devir
    return b


def elestiri(cikar=0.0):
    e = {k: [0.0] * 12 for k in ("matrah_ilave", "hesaplanan_kdv_ilave",
                                 "devir_cikar", "indirim_cikar",
                                 "yuklenilen_cikar")}
    for ay in range(12):
        e["indirim_cikar"][ay] = cikar
    return e


def ornek(sonraki_yil=True, sonraki_indirim=85000.0, tou="Talep edildi",
          vir="2022 | 08.11.2025 | 2025-A-xxxx/24"):
    yillar = [{"yil": 2022, "beyan": yil_beyan(0.0, 90000.0, 100000.0),
               "ay_sayisi": 12, "elestiri": elestiri(8000.0)}]
    if sonraki_yil:
        yillar.append({"yil": 2023,
                       "beyan": yil_beyan(120000.0, 90000.0, sonraki_indirim),
                       "ay_sayisi": 12, "elestiri": elestiri()})
    return {
        "mukellef": {"ad_unvan": "GRUP NAKLİYAT LTD ŞTİ",
                     "vkn_tckn": "1111111111",
                     "vergi_dairesi": "LİMAN VD",
                     "adres": "TOROSLAR / MERSİN"},
        "kunye": {"mukellef_turu": "Kurum (sermaye şirketi)",
                  "faaliyet_konulari": "kara yolu yük nakliyat "
                                       "komisyoncularının faaliyetleri",
                  "faaliyet_adresi": "TOROSLAR / MERSİN",
                  "e_tebligat": "Kapsamda",
                  "grup_baskanligi": "Adana Denetim Daire Başkanlığının",
                  "is_emirleri": "08.10.2025 | E-23929873-663.05[1111]-43834 "
                                 "| 2022 | Sahte Belge Kullanma",
                  "vir_bilgileri": vir,
                  "eleman_ad": "AHMET MÜFETTİŞ",
                  "eleman_unvan": "Vergi Müfettişi",
                  "tou_talebi": tou},
        "yillar": yillar,
        "faturalar": [{"duzenleyen_vkn": "2222222222",
                       "alici_vkn": "1111111111", "tarih": "2022-05-10",
                       "fatura_no": "A-1", "matrah": 400000.0,
                       "kdv": 96000.0, "toplam": 496000.0, "dahil": True}],
        "saticilar": {"2222222222": {
            "unvan": "DEMİR ÇELİK SAN VE TİC LTD ŞTİ",
            "kullanma": "Bilmeden kullanma",
            "vergi_dairesi": "HASAN TAHSİN VD", "vtr_no": "2025/7",
            "vtr_tarihi": "01.02.2025", "not": "sahte belge düzenlediği"}},
    }


def istekci():
    h = W.Istekci.__new__(W.Istekci)
    h.gonderilen = []
    h._belge_gonder = lambda g, a, t: h.gonderilen.append((a, t, g))
    h._ciktilara_yaz = lambda d: None
    return h


def coz(c):
    sonuc, _bulgular = W._hesapla(c)
    liste = F.normalize(c["faturalar"], c["mukellef"]["vkn_tckn"])
    return sonuc, liste


# --------------------------------------------------------- 1) zincir dogru mu
print("\n1) Devir zinciri")
c = ornek()
sonuc, liste = coz(c)
d2022 = [d for d in dolu_donemler(sonuc) if d["yil"] == 2022]
d2023 = [d for d in dolu_donemler(sonuc) if d["yil"] == 2023]
esit(d2022[-1]["beyan"]["sonraki_devir"], 120000.0,
     "2022 Aralık beyan edilen devir")
esit(d2022[-1]["elestirili"]["sonraki_devir"], 24000.0,
     "2022 Aralık olması gereken devir (8.000 x 12 reddedildi)")
esit(sum(d["tarhiyat"]["toplam_fark"] for d in d2022), 0.0,
     "2022'de fark yok: devir farkı soğurdu")
esit(sum(d["tarhiyat"]["toplam_fark"] for d in d2023), 36000.0,
     "2023'te devir eridikçe fark doğuyor")

# ------------------------------------------------------------- 2) yil secimi
print("\n2) Rapor düzenlenecek yıllar")
denetle(D.rapor_yillari(sonuc, liste, c["saticilar"]) == [2023],
        "yalnızca 2023 seçiliyor (2022 incelenen yıl)")

# Sonraki yilda odenecek cikmiyorsa rapor gerekmez: devir farki sogurur.
c_bol = ornek(sonraki_indirim=200000.0)
s2, l2 = coz(c_bol)
denetle(D.rapor_yillari(s2, l2, c_bol["saticilar"]) == [],
        "sonraki yılda ödenecek çıkmıyorsa rapor üretilmiyor")

# Onceki yil calismada yoksa devrin degistigi bilinemez.
c_tek = ornek(sonraki_yil=False)
s3, l3 = coz(c_tek)
denetle(D.rapor_yillari(s3, l3, c_tek["saticilar"]) == [],
        "sonraki yıl girilmemişse rapor üretilmiyor")

# Sahte belgesi olan yil INCELENEN yildir; onun belgesi bu rapor degildir.
c_sahte = ornek()
c_sahte["faturalar"].append({"duzenleyen_vkn": "2222222222",
                             "alici_vkn": "1111111111",
                             "tarih": "2023-04-10", "fatura_no": "B-1",
                             "matrah": 10000.0, "kdv": 2400.0,
                             "toplam": 12400.0, "dahil": True})
s4, l4 = coz(c_sahte)
denetle(D.rapor_yillari(s4, l4, c_sahte["saticilar"]) == [],
        "o yılda sahte belge varsa devir düzeltme raporu üretilmiyor")

# Devir DEGISMEDIYSE, yilda fark olsa bile bu rapor yazilmaz: fark baska
# bir sebepten gelmis olabilir ve o zaman yazilacak belge bu DEGILDIR.
# Ayirt edici fikstur: 2022'de hic red yok (devir aynen duruyor), 2023'te
# ise devirle ilgisi olmayan bir matrah ilavesi var.
#
# Bu denetim ilk yazildiginda 2023'un farki da SIFIRDI, dolayisiyla
# `rapor_yillari` "fark yok" diye bos donuyordu ve denetim yanlis sebepten
# geciyordu - devir kosulu kaldirildiginda hic kizarmadi. Fikstur bu yuzden
# farkin GERCEKTEN dogdugu bir hale cevrildi.
c_devirsiz = ornek()
c_devirsiz["yillar"][0]["elestiri"] = elestiri(0.0)
e_ilave = elestiri(0.0)
for _ay in range(12):
    e_ilave["matrah_ilave"][_ay] = 100000.0
    e_ilave["hesaplanan_kdv_ilave"][_ay] = 18000.0
c_devirsiz["yillar"][1]["elestiri"] = e_ilave
s5, l5 = coz(c_devirsiz)
onceki = [d for d in dolu_donemler(s5) if d["yil"] == 2022][-1]
denetle(abs(onceki["beyan"]["sonraki_devir"]
            - onceki["elestirili"]["sonraki_devir"]) < 0.005,
        "önceki yılın devri değişmedi (ön koşul)")
esit(sum(d["tarhiyat"]["toplam_fark"]
         for d in dolu_donemler(s5) if d["yil"] == 2023), 168000.0,
     "2023'te fark VAR (ön koşul: denetim dişli olsun)")
denetle(D.rapor_yillari(s5, l5, c_devirsiz["saticilar"]) == [],
        "devir değişmediyse fark olsa bile rapor üretilmiyor")

# --------------------------------------------------------------- 3) metin
print("\n3) Rapor metni")
belge = D.rapor_uret(W._inceleme_bilgisi(c), c["kunye"], sonuc, c, 2023)
m = belge.duz_metin()

for baslik in ("I- GİRİŞ", "II- USUL İNCELEMELERİ", "III- HESAP İNCELEMELERİ",
               "III.1- Mükellefin Katma Değer Vergisi Beyanı",
               "IV- TESPİT VE TENKİT EDİLEN HUSUSLAR",
               "IV.A- Re’sen Takdir Nedeni", "IV.B- Re’sen Takdir Verileri",
               "IV.C- Mükellefin Katma Değer Vergisi Beyanlarının "
               "Düzeltilmesi ve Yapılacak İşlemler", "V- SONUÇ"):
    denetle(baslik in m, "bölüm var: %s" % baslik.split("-")[0].strip())

denetle("Söz konusu raporda tespit edilen hususlar nedeniyle 2023 yılı katma "
        "değer vergisi beyanlarının yeniden düzenlenmesi gereği hasıl "
        "olduğundan, ayrıca bu rapor tanzim edilmiştir." in m,
        "giriş, raporun hangi raporun sonucu olduğunu söylüyor")

# Rapora atiflar bulunma halinde olmali; VSR'de ayni kusur bir kez yasandi.
denetle("Vergi İnceleme Raporunda yer verildiğinden" in m,
        "II. bölümdeki atıf bulunma hâlinde")
denetle("Vergi İnceleme Raporu yer verildiğinden" not in m,
        "eksik ekli biçim geri gelmemiş")
denetle("sayılı Vergi İnceleme Raporunda, mükellef kurum tarafından" in m,
        "IV.B'deki atıf bulunma hâlinde")
denetle("sayılı Vergi İnceleme Raporunda, Aralık/2022 döneminden" in m,
        "IV.C'deki atıf bulunma hâlinde")

# IV.A'da ust uste iki ilgi eki olmamali.
denetle("döneminin hesap ve işlemlerinin" not in m,
        "“döneminin hesap ve işlemlerinin” çift ilgi eki yok")
denetle("2022 hesap dönemi hesap ve işlemlerinin" in m,
        "dönem yalın hâlde yazılıyor")

# Devir tutarlari dogru yerde
denetle("2022 Aralık dönemi sonraki döneme devreden katma değer vergisi "
        "tutarı 24.000,00-TL olarak değişmiş" in m,
        "IV.A önceki yılın düzeltilmiş devrini yazıyor")
denetle("beyanında yer aldığı üzere 120.000,00-TL olmayıp 24.000,00-TL" in m,
        "IV.C beyan edilen ve olması gereken devri karşılaştırıyor")

# Raporun en islevsel maddesi: zincirin sonraki yila tasinmasi.
denetle("2024/Ocak dönemi önceki dönemden devreden katma değer vergisi "
        "tutarının 0,00-TL olarak dikkate alınması ve 2024/Ocak dönemi katma "
        "değer vergisi beyannamesinin buna göre vergi dairesince "
        "düzeltilmesi gerektiği," in m,
        "sonuç, sonraki yılın Ocak devrinin düzeltilmesini istiyor")

# Tarhiyat ve ceza
denetle("36.000,00" in m, "re'sen tarhı gereken tutar yazılıyor")
denetle("1 (bir) kat vergi ziyaı cezası" in m, "bir kat ceza isteniyor")
denetle("30. maddesinin 4 ve 6 numaralı bendi" in m,
        "VUK 30/4 ve 30/6'ya dayandırılıyor")
denetle("4- Mükellefin tarhiyat öncesi uzlaşma talebinin" in m,
        "uzlaşma talebi maddesi ekleniyor")

# Sekiz donem cumle icinde tek tek sayilmamali; tablo zaten gosteriyor.
denetle("belirtilen dönemler için hesap edilen" in m,
        "çok dönemde adlar sayılmıyor")

c_tou = ornek(tou="Talep edilmedi")
s6, _l6 = coz(c_tou)
m6 = D.rapor_uret(W._inceleme_bilgisi(c_tou), c_tou["kunye"], s6,
                  c_tou, 2023).duz_metin()
denetle("tarhiyat öncesi uzlaşma" not in m6,
        "uzlaşma talep edilmemişse madde eklenmiyor")

# Rapor kunyesi girilmemisse kirmizi yer tutucu kalmali, uydurulmamali.
c_virsiz = ornek(vir="")
s7, _l7 = coz(c_virsiz)
m7 = D.rapor_uret(W._inceleme_bilgisi(c_virsiz), c_virsiz["kunye"], s7,
                  c_virsiz, 2023).duz_metin()
denetle("[rapor tarihi] tarih ve [rapor sayısı] sayılı" in m7,
        "rapor künyesi girilmemişse yer tutucu kalıyor")

# ------------------------------------------------------- 4) uc noktaya baglanti
print("\n4) Rapor indirilirken")
h = istekci()
belgeler, inceleme, _vsr = h._rapor_hazirla({"calisma": c})
adlar = {yil: ad for yil, _b, ad in belgeler}
denetle(sorted(adlar) == [2022, 2023], "iki yıl için de belge üretiliyor")
denetle("Sahte_belge_raporu" in adlar[2022],
        "2022 sahte belge kullanma raporu")
denetle("Devir_duzeltme_raporu" in adlar[2023],
        "2023 devir düzeltme raporu")
denetle("Sahte_belge_raporu" not in adlar[2023],
        "2023 için ayrıca sahte belge raporu ÜRETİLMİYOR")

h._rapor_gonder({"calisma": c})
ad, tur, govde = h.gonderilen[-1]
denetle(tur == "application/zip", "iki belge zip içinde iniyor")
with zipfile.ZipFile(io.BytesIO(govde)) as z:
    icerik = sorted(z.namelist())
denetle(any("Devir_duzeltme" in n for n in icerik),
        "pakette devir düzeltme raporu var")
denetle(sum(1 for n in icerik if "Sahte_belge_raporu" in n) == 1,
        "pakette tek sahte belge raporu var")

onizleme = h._rapor_onizleme({"calisma": c})
denetle("DEVİR DÜZELTME RAPORU" in onizleme["metin"],
        "önizlemede ayraç raporun türünü söylüyor")

print()
if HATA:
    print("BAŞARISIZ: %d denetim" % len(HATA))
    for x in HATA:
        print("  -", x)
    sys.exit(1)
print("Tüm denetimler geçti.")
