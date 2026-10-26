# -*- coding: utf-8 -*-
"""Vergi suclari raporu EK-3 ozet tablolarinin doldurulmasi.

    python3 testler/ek3_testi.py

EK-3, dairenin kendi Word formudur; uygulama onu YENIDEN CIZMEZ, acip
hucrelerini doldurur. Denetim bu yuzden iki ayri seyi kolluyor:

  1) **Dosya saglam kaliyor mu.** Word, ad alani bildirimi eksik bir
     belgeyi "okunamayan icerik" diye reddeder ve dosya hic acilmaz. Bu
     sessiz bir kayiptir: uygulama hata vermez, mufettis formu acmaya
     calisana kadar da anlasilmaz. Denetim, kok etiketteki butun xmlns
     bildirimlerinin ve `mc:Ignorable` oneklerinin korundugunu dogrular.

  2) **Dogru kume yaziliyor mu.** EK-3 vergi suclari raporunun ekidir ve
     VSR yalnizca BILEREK kullanma tespit edilen saticilara iliskindir
     (306 Sira No'lu Teblig). Bilmeden kullanilan bir belgenin EK-3'e
     girmesi, suc duyurusuna dayanak yapilan tabloya kasit kurulmamis bir
     belge koymak olurdu.

Capa, mufettisin kullandigi GERCEK formdur (`ornek_ek3_formu.docx`): form
degisirse ya da kod formu tanimaz hale gelirse denetim kirmizi doner.
"""
import os
import sys

KOK = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, KOK)

from app import docx_form as D                                       # noqa: E402
from app import vergi_sucu_raporu as V                               # noqa: E402
from app import vsr_ek3                                              # noqa: E402
from app import web_server as W                                      # noqa: E402
from app.satirlar import VERI_KODLARI                                # noqa: E402

FORM_YOLU = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                         "ornek_ek3_formu.docx")
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


def fatura(tarih, no, matrah, vkn, duzeltildi=False):
    return {"duzenleyen_vkn": vkn, "alici_vkn": "1234567890", "tarih": tarih,
            "fatura_no": no, "matrah": matrah, "kdv": round(matrah * 0.2, 2),
            "toplam": round(matrah * 1.2, 2), "dahil": True,
            "mal_cinsi": "inşaat malzemesi", "yevmiye_tarih": tarih,
            "yevmiye_no": "Y" + no,
            "duzeltme_cikarildi": "Evet" if duzeltildi else "Hayır"}


def ornek():
    return {
        "mukellef": {"ad_unvan": "ÖRNEK İNŞAAT LTD ŞTİ",
                     "vkn_tckn": "1234567890",
                     "vergi_dairesi": "ZİYAPAŞA VD", "adres": "SEYHAN / ADANA"},
        "kunye": {"mukellef_turu": "Kurum (sermaye şirketi)",
                  "e_defter": "Kapsamda",
                  "defter_bilgileri":
                      "2021 | Yevmiye Defteri | 24.12.2020 - 14521 | "
                      "Adana 5. Noterliği\n"
                      "2022 | Yevmiye Defteri | Aralık 2021, 19034 | Adana 5. Noterliği"},
        "yillar": [{"yil": 2021, "beyan": beyan(), "ay_sayisi": 12,
                    "elestiri": {}},
                   {"yil": 2022, "beyan": beyan(), "ay_sayisi": 12,
                    "elestiri": {}}],
        "faturalar": [
            # bilerek kullanilan belgeler (EK-3'e girer)
            fatura("2022-09-20", "B-1", 35000.0, "1111111111"),
            fatura("2021-03-10", "A-1", 30000.0, "1111111111"),
            # duzeltmeyle cikarilmis ama BILEREK kullanilmis: yine girer
            fatura("2021-07-15", "A-2", 20000.0, "2222222222",
                   duzeltildi=True),
            # bilmeden kullanma: GIRMEZ
            fatura("2022-04-11", "C-1", 50000.0, "3333333333"),
        ],
        "saticilar": {
            "1111111111": {"unvan": "SAHTECİ-1 LTD",
                           "kullanma": "Bilerek kullanma",
                           "vergi_dairesi": "5 OCAK VD",
                           "yetkili_ad": "MEHMET DEMİR",
                           "yetkili_tckn": "11111111110"},
            "2222222222": {"unvan": "SAHTECİ-2 A.Ş.",
                           "kullanma": "Bilerek kullanma",
                           "vergi_dairesi": "SEYHAN VD",
                           "yetkili_yabanci": "IVAN PETROV, pasaport ES123"},
            "3333333333": {"unvan": "BİLMEDEN LTD",
                           "kullanma": "Bilmeden kullanma",
                           "vergi_dairesi": "SEYHAN VD"},
        },
    }


HAM = open(FORM_YOLU, "rb").read()


def tablolari_oku(baytlar):
    """{imza: [[hucre, ...], ...]} - doldurulmus formun tablolari."""
    cikti = {}
    for tablo in D.Form(baytlar).tablolar():
        for kod, anahtarlar in vsr_ek3.IMZALAR.items():
            if tablo.baslik_indeksi(anahtarlar) is not None:
                cikti.setdefault(kod, tablo.metinler())
        cikti.setdefault("_tumu", []).append(tablo.metinler())
    return cikti


# ------------------------------------------------- 1) dosya sağlam kalıyor
print("\n1) Dosya sağlam kalıyor")
import re                                                            # noqa: E402
import zipfile                                                       # noqa: E402
import io                                                            # noqa: E402

dolu, rapor = vsr_ek3.form_doldur(HAM, ornek()["kunye"], ornek())
eski_zip = zipfile.ZipFile(io.BytesIO(HAM))
yeni_zip = zipfile.ZipFile(io.BytesIO(dolu))
esit(yeni_zip.namelist(), eski_zip.namelist(), "arşivin parçaları aynı")
degisen = [ad for ad in eski_zip.namelist()
           if eski_zip.read(ad) != yeni_zip.read(ad)]
esit(degisen, ["word/document.xml"], "yalnızca document.xml değişiyor")

x_eski = eski_zip.read("word/document.xml").decode("utf-8")
x_yeni = yeni_zip.read("word/document.xml").decode("utf-8")
onek = lambda metin: set(re.findall(r'xmlns:([\w.-]+)=', metin[:2000]))
esit(sorted(onek(x_yeni)), sorted(onek(x_eski)),
     "kök etiketteki ad alanı önekleri korunuyor")
# Word, mc:Ignorable icindeki bir onek bildirilmemisse dosyayi hic acmaz.
ignorable = re.search(r'mc:Ignorable="([^"]*)"', x_yeni)
denetle(ignorable is not None, "mc:Ignorable korunuyor")
denetle(ignorable is not None
        and all(o in onek(x_yeni) for o in ignorable.group(1).split()),
        "mc:Ignorable'daki öneklerin hepsi bildirilmiş")
denetle(D.Form(dolu).tablolar() and True, "üretilen dosya yeniden açılabiliyor")

try:
    vsr_ek3.form_doldur(b"bu bir docx degil", {}, ornek())
    denetle(False, "docx olmayan dosya reddediliyor")
except D.FormHata as exc:
    denetle("docx" in str(exc), "docx olmayan dosya anlaşılır hatayla reddediliyor")


# ------------------------------------------------------- 2) kullanım tablosu
print("\n2) Sahte belge kullanım bilgileri")
tablolar = tablolari_oku(dolu)
kullanim = tablolar["kullanim"]
# 0: baslik, 1: sutun adlari, sonra belgeler, en sonda TOPLAM
belgeler = kullanim[2:-1]
esit([s[1] for s in belgeler], ["A-1", "A-2", "B-1"],
     "belgeler kayıt dönemi sırasında yazılıyor")
denetle(all("C-1" != s[1] for s in belgeler),
        "bilmeden kullanılan belge EK-3'e girmiyor")
denetle(any(s[1] == "A-2" for s in belgeler),
        "düzeltmeyle çıkarılmış belge EK-3'e giriyor (fiil işlenmiştir)")
esit(belgeler[0][2], "10.03.2021", "fatura tarihi gg.aa.yyyy yazılıyor")
esit(belgeler[0][4], "30.000,00", "tutar sütunu matrah")
esit(belgeler[0][5], "6.000,00", "KDV sütunu")
esit(belgeler[0][6], "36.000,00", "toplam sütunu")
esit(belgeler[0][7], "10.03.2021", "deftere kayıt tarihi yevmiye tarihinden")
esit(belgeler[0][8], "YA-1", "yevmiye no")
toplam = kullanim[-1]
esit(toplam[3], "TOPLAM", "TOPLAM satırı korunuyor")
esit((toplam[4], toplam[5], toplam[6]),
     ("85.000,00", "17.000,00", "102.000,00"),
     "TOPLAM satırı yazılan belgelerin toplamı")


# -------------------------------------------------- 3) düzenleyen mükellefler
print("\n3) Belgeleri düzenleyen mükellefler")
duzenleyen = tablolar["duzenleyen"][2:]
esit([s[1] for s in duzenleyen], ["1111111111", "2222222222"],
     "yalnızca bilerek kullanma satıcıları yazılıyor")
esit(duzenleyen[0][0], "Sahteci-1 LTD", "unvan sütunu")
esit(duzenleyen[0][2], "MEHMET DEMİR", "satıcı yetkilisi satıcı kartından")
esit(duzenleyen[0][3], "11111111110", "yetkilinin T.C. kimlik numarası")
denetle(duzenleyen[1][2].startswith("["),
        "yetkili girilmemişse köşeli parantezli yer tutucu kalıyor")


# ------------------------------------------------------- 4) tekil hücreler
print("\n4) Tekil hücreler")
duz_metin = "\n".join(" | ".join(s) for t in tablolar["_tumu"] for s in t)
denetle("Vergi Türü | Katma Değer Vergisi" in duz_metin, "vergi türü yazılıyor")
# Son sahte belge 2022/Eylul; beyanname IZLEYEN ayda verilir. Gun UYDURULMAZ:
# KDV beyannamesinin verilme gunu yillar icinde degisti.
denetle("[gün].10.2022" in duz_metin,
        "beyanname son tarihi izleyen aya yazılıyor, gün yer tutucu kalıyor")
denetle("IVAN PETROV" in duz_metin,
        "yabancı uyruklu temsilci bilgisi yazılıyor")
denetle("2021 | Yevmiye Defteri, Büyük Defter" in duz_metin,
        "e-defter bilgisi künyedeki yıllardan yazılıyor")
# Tasdik tarihi ve numarasi kunyede TEK hucrede; ikiye ancak gg.aa.yyyy ile
# baslayan metin guvenle bolunur, bolunemezse iki hucre de BOS kalir.
noter = tablolar["noter"][2:]
esit((noter[0][5], noter[0][6]), ("24.12.2020", "14521"),
     "tasdik tarihi ve numarası ayrıştırılıyor")
esit((noter[1][5], noter[1][6]), ("", ""),
     "ayrıştırılamayan tasdik bilgisi boş bırakılıyor (yanlış sütuna yazılmıyor)")

e_defter_yok = ornek()
e_defter_yok["kunye"]["e_defter"] = "Kapsamda değil"
_govde, rapor2 = vsr_ek3.form_doldur(HAM, e_defter_yok["kunye"], e_defter_yok)
denetle(any(ad == "E-defter bilgisi" and "boş" in ne for ad, ne in rapor2),
        "e-defter kapsamı yoksa tablo boş bırakılıyor ve bildiriliyor")


# ------------------------------------------------- 5) VSR'deki EK-3 atfı
print("\n5) Vergi suçları raporunda EK-3 atfı")


def vsr_metni(calisma):
    h = W.Istekci.__new__(W.Istekci)
    sonuc, _bulgular = W._hesapla(calisma)
    belge = V.rapor_uret(W._inceleme_bilgisi(calisma), calisma["kunye"],
                         W._yillari_coz(calisma), sonuc, calisma)
    return belge.duz_metin()


formsuz = ornek()
denetle("EK-3" not in vsr_metni(formsuz),
        "form yüklenmemişse rapor EK-3'e atıf YAPMIYOR")
formlu = ornek()
formlu["ek3_formu"] = {"ad": "ek3.docx", "veri": "QUJD"}
metin = vsr_metni(formlu)
denetle("EK-3 sayılı “Sahte Belge Kullanma Fiili Nedeniyle Düzenlenen "
        "Raporlara İlişkin Özet Tablolar”da yer verildiği" in metin,
        "form yüklüyse sonuç bölümünde EK-3 maddesi var")
sonuc_bolumu = metin.split("V- SONUÇ")[-1]
denetle(sonuc_bolumu.index("EK-3")
        < sonuc_bolumu.index("suç duyurusunda bulunulması"),
        "EK-3 maddesi suç duyurusu maddesinden önce geliyor")


# ------------------------------------------------- 6) rapor paketine giriyor
print("\n6) Rapor paketi")
import zipfile as Z                                                  # noqa: E402

h = W.Istekci.__new__(W.Istekci)
h.gonderilen = []
h._belge_gonder = lambda govde, ad, tur: h.gonderilen.append((ad, tur, govde))
h._ciktilara_yaz = lambda dosyalar: None
import base64                                                        # noqa: E402

paketli = ornek()
paketli["ek3_formu"] = {"ad": "ek3.docx",
                        "veri": base64.b64encode(HAM).decode("ascii")}
W.Istekci._rapor_gonder(h, {"calisma": paketli})
_ad, tur, govde = h.gonderilen[-1]
esit(tur, "application/zip", "birden fazla belge zip içinde iniyor")
adlar = Z.ZipFile(io.BytesIO(govde)).namelist()
denetle(any(a.startswith("EK-3_Ozet_tablolar") for a in adlar),
        "doldurulmuş EK-3 rapor paketine giriyor")
denetle(any("Vergi_suclari_raporu" in a for a in adlar),
        "vergi suçları raporu da pakette")

# Bilerek kullanma yoksa VSR uretilmez; EK-3 de pakete GIRMEZ.
bilmeden = ornek()
for bilgi in bilmeden["saticilar"].values():
    bilgi["kullanma"] = "Bilmeden kullanma"
bilmeden["ek3_formu"] = paketli["ek3_formu"]
h.gonderilen = []
W.Istekci._rapor_gonder(h, {"calisma": bilmeden})
_ad, tur, govde = h.gonderilen[-1]
adlar = (Z.ZipFile(io.BytesIO(govde)).namelist()
         if tur == "application/zip" else [_ad])
denetle(not any(a.startswith("EK-3") for a in adlar),
        "bilerek kullanma yokken EK-3 pakete girmiyor (VSR de yok)")


print("\n" + ("BAZI DENETİMLER BAŞARISIZ" if HATA else "Tüm denetimler geçti."))
sys.exit(1 if HATA else 0)
