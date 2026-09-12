# -*- coding: utf-8 -*-
"""Beyanname okuyucusunun gerileme denetimi.

    python3 testler/beyanname_testi.py

Okuyucuyu PDF olmadan, METIN KATMANI DOKUMU uzerinde calistirir. Sahadan
gelen maskelenmis dokum, `_parcalar()`in donduruyle ayni bicimdedir
(sayfa, x, y, metin); bu yuzden `_parcalar` yerine konarak okuyucu bastan
sona islatilabilir. [MASKELI] alanlarin yerine, KONUMLARI korunarak
gercekci ornek degerler konulmustur - onemli olan metin degil, konumdur.

Bu kume iki gercek hatayi yakaladi; yeni bir beyanname bicimi ya da yeni
bir alan adi ogrenildiginde buraya ornek eklenmelidir:

  - "Matrah Toplamı" -> "Toplam Matrah" olunca matrah okunamiyor ama yeni
    bicimde eksik bolum "sifir" sayildigi icin SESSIZCE 0,00 gorunuyordu.
  - Unvanin ikinci satiri kayboluyordu: deger satirlari sola degil SAGA
    yasli olabiliyor, devam satiri birincinin cok saginda basliyor.
"""
import os
import sys

KOK = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, KOK)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import pdf_beyanname as P
from ornekler_eski_ve_yeni import YENI, ESKI
import ornek_yeni_matrahli as MATRAHLI

def oku(parcalar, ad):
    P._parcalar = lambda _yol: list(parcalar)
    return P.beyanname_oku("(bellek)", ad)


def yazdir(baslik, s):
    print("\n" + "=" * 70)
    print(baslik)
    print("=" * 70)
    for k in ("yil", "ay", "vkn", "unvan", "vergi_dairesi", "tur", "bicim",
              "donem_tipi", "onay_zamani", "onay_ts", "duzeltme_nedeni"):
        print("  %-16s %r" % (k, s[k]))
    print("  degerler:")
    for k in sorted(s["degerler"]):
        print("      %-28s %s" % (k, s["degerler"][k]))
    print("  ek:", s["ek"])
    print("  uyarilar:", s["uyarilar"] or "(yok)")
    print("  tanimsiz:", s["tanimsiz"])


def denetle(ad, s, beklenen):
    hata = 0
    for yol, bek in beklenen.items():
        gercek = s
        for parca in yol.split("."):
            gercek = gercek.get(parca) if isinstance(gercek, dict) else None
        if gercek != bek:
            print("  ! %s -> %s  (beklenen %r, okunan %r)" % (ad, yol, bek, gercek))
            hata = 1
    return hata


hata = 0

y = oku(YENI, "yeni.pdf")
yazdir("YENİ BİÇİM", y)
hata |= denetle("yeni", y, {
    "yil": 2026, "ay": 4, "bicim": "yeni", "tur": "kanuni",
    "donem_tipi": "AYLIK",
    "vkn": "1234567890",
    "unvan": "ÖRNEK İNŞAAT TAAHHÜT SANAYİ VE TİCARET LİMİTED ŞİRKETİ",
    "vergi_dairesi": "BEŞİKTAŞ VERGİ DAİRESİ MÜDÜRLÜĞÜ",
    "onay_zamani": "06/05/2026 06:01:51",
    "onay_ts": "2026-05-06T06:01:51",
    "degerler.indirimler_toplami": 8327.60,
    "degerler.onceki_donem_devreden": 5842.80,
    "degerler.yurtici_alim_kdv": 2484.80,
    "degerler.bu_donem_indirilecek": 2484.80,
    "degerler.diger_indirimler_toplami": 0.0,
    "degerler.sonraki_donem_devreden": 8327.60,
    "degerler.odenmesi_gereken_kdv": 0.0,
    "degerler.tecil_edilecek_kdv": 0.0,
    "degerler.iade_edilmesi_gereken_kdv": 0.0,
    "degerler.matrah_toplami": 0.0,
    "degerler.hesaplanan_kdv": 0.0,
    "degerler.toplam_kdv": 0.0,
    "degerler.teslim_bedel_aylik": 0.0,
    "degerler.teslim_bedel_kumulatif": 0.0,
    "degerler.kredi_karti_tahsilat": 0.0,
})
if y["uyarilar"]:
    print("  ! yeni bicimde uyari cikmamaliydi:", y["uyarilar"]); hata = 1

e = oku(ESKI, "eski.pdf")
yazdir("ESKİ BİÇİM (gerileme denetimi)", e)
hata |= denetle("eski", e, {
    "yil": 2025, "ay": 1, "bicim": "eski", "tur": "duzeltme",
    "donem_tipi": "",
    "vkn": "1234567890",
    "unvan": "ÖRNEK İNŞAAT TAAHHÜT SANAYİ VE TİCARET LİMİTED ŞİRKETİ",
    "vergi_dairesi": "BEŞİKTAŞ",
    "onay_zamani": "28.01.2025 - 22:07:21",
    "onay_ts": "2025-01-28T22:07:21",
    "duzeltme_nedeni": "Matrah artırımı sonrası indirim düzeltmesi",
    "degerler.matrah_toplami": 100000.0,
    "degerler.hesaplanan_kdv": 20000.0,
    "degerler.toplam_kdv": 20000.0,
    "degerler.ilave_edilecek_kdv": 0.0,
    "degerler.onceki_donem_devreden": 5000.0,
    "degerler.yurtici_alim_kdv": 12000.0,
    "degerler.bu_donem_indirilecek": 12000.0,
    "degerler.diger_indirimler_toplami": 0.0,
    "degerler.indirimler_toplami": 17000.0,
    "degerler.odenmesi_gereken_kdv": 3000.0,
    "degerler.sonraki_donem_devreden": 0.0,
    "degerler.teslim_bedel_aylik": 100000.0,
    "degerler.kredi_karti_tahsilat": 50000.0,
})
if e["uyarilar"]:
    print("  ! eski bicimde uyari cikmamaliydi:", e["uyarilar"]); hata = 1


# ---- YENİ BİÇİM + satış (matrah bölümü var) --------------------------------
# Örnekte matrah bölümü hiç yoktu; satış olan bir dönemde bölümün okunduğunu
# ve sıfırla doldurmanın gerçek değeri EZMEDİĞİNİ gösterir.
SATISLI = [p for p in YENI if not (p[0] == 0 and 306.0 >= p[2] >= 208.0)] + [
    (0, 240.0, 320.0, "MATRAH VE VERGİ BİLDİRİMİ"),
    (0, 41.0, 306.0, "Matrah Toplamı"),
    (0, 526.0, 306.0, "62.120,00"),
    (0, 41.0, 292.0, "Hesaplanan KDV"),
    (0, 526.0, 292.0, "12.424,00"),
    (0, 41.0, 278.0, "İlave Edilecek KDV"),
    (0, 540.0, 278.0, "0,00"),
    (0, 41.0, 264.0, "Toplam KDV"),
    (0, 526.0, 264.0, "12.424,00"),
    (0, 258.2, 240.0, "DİĞER BİLGİLER"),
    (0, 41.0, 226.0, "Teslim ve Hizmetlerin"),
    (0, 41.0, 218.0, "Karşılığını Teşkil Eden"),
    (0, 41.0, 210.0, "Bedel (Aylık)"),
    (0, 540.0, 226.0, "62.120,00"),
]
# Sonuc hesaplari da satisa gore degisir: 12.424,00 - 8.327,60 = 4.096,40
SATISLI = [(s, x, y, ("4.096,40" if (s, y) == (0, 368.0) and m == "0,00" else m))
           for s, x, y, m in SATISLI]
SATISLI = [(s, x, y, m) for s, x, y, m in SATISLI
           if not (s == 0 and y == 340.0 and m == "8.327,60")]
SATISLI.append((0, 526.0, 340.0, "0,00"))

s = oku(SATISLI, "yeni_satisli.pdf")
yazdir("YENİ BİÇİM — satış var", s)
hata |= denetle("yeni+satis", s, {
    "bicim": "yeni",
    "degerler.matrah_toplami": 62120.0,
    "degerler.hesaplanan_kdv": 12424.0,
    "degerler.ilave_edilecek_kdv": 0.0,
    "degerler.toplam_kdv": 12424.0,
    "degerler.indirimler_toplami": 8327.60,
    "degerler.odenmesi_gereken_kdv": 4096.40,
    "degerler.sonraki_donem_devreden": 0.0,
    "degerler.teslim_bedel_aylik": 62120.0,
})
if s["uyarilar"]:
    print("  ! aritmetik tutmalıydı:", s["uyarilar"]); hata = 1

# ---- YENİ BİÇİM düzeltme beyannamesi ---------------------------------------
DUZELTME = list(YENI) + [
    (0, 41.0, 700.0, "Beyanname Türü: Düzeltme Beyannamesi"),
    (0, 41.0, 690.0, "Düzeltme Nedeni: İndirim düzeltmesi"),
]
d = oku(DUZELTME, "yeni_duzeltme.pdf")
yazdir("YENİ BİÇİM — düzeltme", d)
hata |= denetle("yeni+duzeltme", d, {
    "tur": "duzeltme", "bicim": "yeni",
    "duzeltme_nedeni": "İndirim düzeltmesi",
})

# Örnek beyannamede "Değişiklik Nedeni" sütun başlığı var; bu, beyannameyi
# düzeltme beyannamesi SAYMAMALI.
if y["tur"] != "kanuni":
    print("  ! 'Değişiklik Nedeni' sütunu düzeltme sanıldı"); hata = 1


# ---- YENİ BİÇİM, matrah / ihraç kayıtlı teslim / istisna bölümleri dolu ----
# 2026/Mayıs beyannamesi. İlk yeni biçim örneğinde bu bölümler hiç yoktu.
P._parcalar = lambda _yol: MATRAHLI.parcalar()
m = P.beyanname_oku("(bellek)", "mayis.pdf")
yazdir("YENİ BİÇİM — matrah, ihraç kayıtlı teslim, istisna (düzeltme)", m)
hata |= denetle("yeni+matrah", m, {
    "yil": 2026, "ay": 5, "bicim": "yeni", "tur": "duzeltme",
    "duzeltme_nedeni": MATRAHLI.DUZELTME_ACIKLAMASI,
    "unvan": "ÖRNEK TEKSTİL SANAYİ VE TİCARET ANONİM ŞİRKETİ",
    # Okuyucu beyannamede YAZANI verir; daire kodu belgeye yazilirken
    # inceleme_kunyesi.daire_adi tarafindan kirpilir.
    "vergi_dairesi": "033254 - Örnek Vergi Dairesi Müdürlüğü",
    "degerler.matrah_toplami": 2209951.45,
    "degerler.hesaplanan_kdv": 441990.29,
    "degerler.toplam_kdv": 441990.29,
    "degerler.onceki_donem_devreden": 812096.82,
    "degerler.yurtici_alim_kdv": 156379.83,
    "degerler.sorumlu_sifatiyla_kdv": 0.0,
    "degerler.bu_donem_indirilecek": 156379.83,
    "degerler.indirimler_toplami": 968476.65,
    "degerler.iade_edilmesi_gereken_kdv": 199353.0,
    "degerler.sonraki_donem_devreden": 327133.36,
    "degerler.ihrac_teslim_bedeli": 306884.0,
    "degerler.tecil_edilebilir_kdv": 61376.8,
    "degerler.ihracat_tecil_edilemeyen": 61376.8,
    "degerler.ihracat_doneminde_iade": 61376.8,
    "degerler.istisna_toplam_teslim": 1714379.68,
    "degerler.iade_edilebilir_kdv": 199353.0,
    "degerler.teslim_bedel_aylik": 3924331.13,
    "degerler.teslim_bedel_kumulatif": 13482398.92,
    "degerler.kredi_karti_tahsilat": 908385.0,
})
if m["uyarilar"]:
    print("  ! aritmetik tutmalıydı:", m["uyarilar"]); hata = 1

# Düzeltme işareti, künye alanları gibi etiketi ve değeri AYRI parçalarda
# olabilir; iki düzende de yakalanmalı.
for etiket, deger, bek_tur in (
        ("Düzeltme Açıklaması", "SMMM tarafından yapılan düzeltme", "duzeltme"),
        ("Beyanname Türü", "Düzeltme Beyannamesi", "duzeltme"),
        ("Düzeltme Nedeni", "Sahte belge indirimlerinin çıkarılması", "duzeltme"),
        ("Beyanname Türü", "Kanuni Süresinde", "kanuni"),
        ("", "", "kanuni")):
    P._parcalar = lambda _yol, e=etiket, d=deger: MATRAHLI.parcalar(e, d)
    s2 = P.beyanname_oku("(bellek)", "x.pdf")
    if s2["tur"] != bek_tur:
        print("  ! %r / %r -> tür %s, beklenen %s"
              % (etiket, deger, s2["tur"], bek_tur)); hata = 1

# Uzun bir duzeltme aciklamasi alt satira tasar. Devami alinmali, ama
# 24 punto asagidaki SUTUN BASLIKLARI aciklamaya karismamali
# ("Beyannamenin Hangi Sıfatla Verildiği Bilgileri").
# Uc satira tasan aciklama, sutun basliklarinin bulundugu banda DEGER;
# iki satirda kalirsa aradaki bosluk zaten 16 punto olup satir araligini
# astigi icin sorun cikmaz. Denetim bu yuzden uc satirla yapilir.
_tasan = MATRAHLI.parcalar() + [(0, 145.6, 556.0, "İNDİRİMLERDEN"),
                                (0, 145.6, 548.0, "ÇIKARILMIŞTIR")]
P._parcalar = lambda _yol: _tasan
t = P.beyanname_oku("(bellek)", "tasan.pdf")
_bek = MATRAHLI.DUZELTME_ACIKLAMASI + " İNDİRİMLERDEN ÇIKARILMIŞTIR"
if t["duzeltme_nedeni"] != _bek:
    print("  ! taşan açıklama: beklenen %r, okunan %r"
          % (_bek, t["duzeltme_nedeni"])); hata = 1

# Daire kodu ("033254 - ") belgeye GECMEMELI: rapor "...Müdürlüğü'nün
# mükellefi" diye devam ediyor.
from app import inceleme_kunyesi as ik
_ad = ik.daire_adi(m["vergi_dairesi"])
if _ad != "Örnek Vergi Dairesi Müdürlüğü":
    print("  ! daire adı belgeye %r olarak geçiyor" % _ad); hata = 1

# Buyuk harfli girdide noktali İ / noktasiz I ayrimi kaybolabiliyor.
# Bilinen daireler dogru yazimiyla cikmali; BILINMEYENLER ise
# DEGISMEMELI - kor bir kural bunlari bozardi.
for _girdi, _bek in (
        ("LIMAN VD", "Liman Vergi Dairesi Müdürlüğü"),
        ("LİMAN VD", "Liman Vergi Dairesi Müdürlüğü"),
        ("liman", "Liman Vergi Dairesi Müdürlüğü"),
        ("033254 - LIMAN VD", "Liman Vergi Dairesi Müdürlüğü"),
        ("KADIKÖY VD", "Kadıköy Vergi Dairesi Müdürlüğü"),
        ("IŞIKLAR VD", "Işıklar Vergi Dairesi Müdürlüğü"),
        ("SARIYER VD", "Sarıyer Vergi Dairesi Müdürlüğü"),
        ("BEŞİKTAŞ VD", "Beşiktaş Vergi Dairesi Müdürlüğü"),
        ("12 Nolu Vergi Dairesi", "12 Nolu Vergi Dairesi Müdürlüğü"),
        ("Büyük Mükellefler Vergi Dairesi Başkanlığı",
         "Büyük Mükellefler Vergi Dairesi Başkanlığı")):
    _c = ik.daire_adi(_girdi)
    if _c != _bek:
        print("  ! daire adı %r -> %r, beklenen %r" % (_girdi, _c, _bek))
        hata = 1

print("\n" + ("BAŞARISIZ" if hata else "TÜMÜ GEÇTİ"))
sys.exit(hata)
