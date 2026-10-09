# -*- coding: utf-8 -*-
"""Vergi suclari raporunun (VSR) gerileme denetimi.

    python3 testler/vsr_testi.py

VSR, VUK 359 kapsamindaki fiiller icin tarhiyat oneren rapora EK OLARAK
duzenlenir. Bu yuzden denetlenen sey yalnizca metin degil, raporun hangi
hallerde URETILDIGI ve hangi hallerde URETILMEDIGI:

  - sahte belgeyi BILEREK kullanma isaretli -> uretilir
  - BILMEDEN kullanma -> uretilmez (306 Sira No'lu Teblig; suc yoktur)
  - cok yilli dosyada -> yalnizca bilerek kullanmanin oldugu yil icin
  - duzeltme kabul raporunda (bilerek) -> uretilir, ama tarh edilecek vergi
    yoktur ve ceza duzeltme uzerine kesilen yarim katin UC KATA tamamlanmis
    halidir

Ayrica daha once uretilen metinde gorulen dilbilgisi kusurlarini kolluyor;
bunlar `%s` kaliplarina yanlis ek secilmesinden dogmustu ve belgede
gozden kacacak kadar kucuk, ama resmi bir raporda okunacak kadar belirgin:

  - "mükellef kurumun hakkında düzenlenen" (ilgi eki fazla)
  - "...Vergi İnceleme Raporu mükellefin..." (bulunma eki eksik)
"""
import io
import os
import sys
import zipfile

KOK = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, KOK)

from app import vergi_sucu_raporu as V                               # noqa: E402
from app import web_server as W                                      # noqa: E402
from app.satirlar import VERI_KODLARI                                # noqa: E402

HATA = []


def denetle(kosul, aciklama):
    if kosul:
        print("  [ok] %s" % aciklama)
    else:
        print("  [HATA] %s" % aciklama)
        HATA.append(aciklama)


# ------------------------------------------------------------------- ornek
def ornek(kurum=True, bilerek=True, duzeltme=False, iki_yil=False):
    """Tek saticili, tek yilli en kucuk dosya; her hal icin uyarlanir."""
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

    def elestiri():
        e = {k: [0.0] * 12 for k in ("matrah_ilave", "hesaplanan_kdv_ilave",
                                     "devir_cikar", "indirim_cikar",
                                     "yuklenilen_cikar")}
        if not duzeltme:
            for ay in range(12):
                e["indirim_cikar"][ay] = 5000.0
        return e

    fat = [{"duzenleyen_vkn": "1111111111", "alici_vkn": "1234567890",
            "tarih": "2020-03-10", "fatura_no": "A-1", "matrah": 30000.0,
            "kdv": 6000.0, "toplam": 36000.0, "dahil": True}]
    sat = {"1111111111": {
        "unvan": "SAHTECİ-1 LTD",
        "kullanma": "Bilerek kullanma" if bilerek else "Bilmeden kullanma",
        "vergi_dairesi": "5 OCAK VD", "vtr_no": "2025-[2014]/11",
        "vtr_tarihi": "04.03.2025", "is_emri": "Var",
        "not": "mükellefin düzenlemiş olduğu tüm faturaların gerçek bir mal "
               "teslimine dayanmaksızın düzenlendiği"}}
    if duzeltme:
        # Duzeltme kabul raporu, faturalarin TAMAMI beyandan cikarilmis
        # dosyalar icindir; aksi halde uretim engellenir.
        sat["1111111111"]["duzeltme_ile_cikarildi"] = "Evet"

    yillar = [{"yil": 2020, "beyan": beyan(), "ay_sayisi": 12,
               "elestiri": elestiri()}]
    if iki_yil:
        # Ikinci yilda yalnizca BILMEDEN kullanilan bir satici var; o yil
        # icin suc duyurusu gerekmez, dolayisiyla VSR de uretilmemeli.
        yillar.append({"yil": 2021, "beyan": beyan(), "ay_sayisi": 12,
                       "elestiri": elestiri()})
        fat.append({"duzenleyen_vkn": "3333333333", "alici_vkn": "1234567890",
                    "tarih": "2021-04-10", "fatura_no": "B-1",
                    "matrah": 10000.0, "kdv": 2000.0, "toplam": 12000.0,
                    "dahil": True})
        sat["3333333333"] = {"unvan": "BİLMEDEN-1 LTD",
                             "kullanma": "Bilmeden kullanma",
                             "vergi_dairesi": "5 OCAK VD",
                             "vtr_no": "2025-[2014]/9",
                             "vtr_tarihi": "04.03.2025",
                             "not": "sahte belge düzenlediği"}

    return {
        "mukellef": {"ad_unvan": "ÖRNEK İNŞAAT LTD ŞTİ" if kurum
                     else "AHMET YILMAZ",
                     "vkn_tckn": "1234567890",
                     "vergi_dairesi": "ZİYAPAŞA VD", "adres": "SEYHAN / ADANA"},
        "kunye": {"mukellef_turu": "Kurum (sermaye şirketi)" if kurum
                  else "Gerçek kişi",
                  "faaliyet_konulari": "inşaat taahhüt işleri",
                  "faaliyet_adresi": "SEYHAN / ADANA",
                  "grup_baskanligi": "Adana Denetim Daire Başkanlığının",
                  "is_emirleri": "10.06.2025 | E-663.05[25255]-7777 | 2020 | "
                                 "Sahte Belge Kullanma",
                  "kanuni_temsilci": "MEHMET DEMİR",
                  "temsilci_tckn": "11111111110",
                  "mukellef_tckn": "22222222220",
                  "vir_tarihi": "20.10.2025", "vir_sayisi": "2025-[2013]/72",
                  "vsr_savcilik": "Adana", "fail_baba_anne": "Ali - Ayşe",
                  "fail_dogum_yeri": "ADANA",
                  "fail_dogum_tarihi": "05.04.1983"},
        "yillar": yillar, "faturalar": fat, "saticilar": sat,
    }


def istekci():
    """Sunucu ayaga kaldirilmadan istek isleyicinin metotlarini cagirmak icin."""
    h = W.Istekci.__new__(W.Istekci)
    h.gonderilen = []
    h._belge_gonder = lambda govde, ad, tur: h.gonderilen.append((ad, tur, govde))
    h._ciktilara_yaz = lambda dosyalar: None
    return h


def paket_icerigi(govde):
    with zipfile.ZipFile(io.BytesIO(govde)) as z:
        return sorted(z.namelist())


# ------------------------------------------------------- 1) sahte belge raporu
print("\n1) Sahte belge raporu istenirken")
h = istekci()
c = ornek(bilerek=True)
_belgeler, _inceleme, vsr = h._rapor_hazirla({"calisma": c})
denetle([y for y, _ in vsr] == [2020], "bilerek kullanmada VSR üretiliyor")
h._rapor_gonder({"calisma": c})
ad, tur, govde = h.gonderilen[-1]
icerik = paket_icerigi(govde) if tur == "application/zip" else [ad]
denetle(any("Vergi_suclari_raporu" in n for n in icerik),
        "indirilen pakette VSR dosyası var")
denetle("VSR" in ad, "paket adı VSR içerdiğini söylüyor")

metin = vsr[0][1].duz_metin()
denetle("kurumun hakkında" not in metin,
        "“hakkında” yalın ad ile kullanılıyor (ilgi eki fazla değil)")
denetle("Vergi İnceleme Raporu mükellefin" not in metin
        and "Vergi İnceleme Raporunda mükellefin bilerek sahte belge "
            "kullandığı" in metin,
        "rapora atıf bulunma hâlinde (“Raporunda”)")
denetle("Vergi İnceleme Raporu ayrıntılı" not in metin,
        "3.2'deki atıf da bulunma hâlinde")
denetle("söz konusu mükellefler tarafından" not in metin,
        "I. bölümde satıcılar tanıtılmadan “söz konusu mükellefler” denmiyor")
denetle("Adana Cumhuriyet Başsavcılığına" in metin,
        "savcılık adı yönelme hâlinde yazılıyor")
denetle("11111111110 T.C. kimlik numaralı kanuni temsilci Mehmet DEMİR"
        in metin, "kurumda fiil kanuni temsilciye isnat ediliyor")
denetle("Dolayısıyla kanuni temsilci hakkında" in metin,
        "kurumda ceza kanuni temsilci hakkında isteniyor")
# %1,25'lik bir pay "yuksek" diye nitelenmemeli.
denetle("gibi yüksek bir orana" not in metin,
        "düşük oran “yüksek” diye nitelenmiyor")

print("\n2) Bilmeden kullanmada")
h = istekci()
c = ornek(bilerek=False)
_b, _i, vsr = h._rapor_hazirla({"calisma": c})
denetle(vsr == [], "VSR üretilmiyor")

print("\n3) Gerçek kişi mükellefte")
h = istekci()
c = ornek(kurum=False, bilerek=True)
_b, _i, vsr = h._rapor_hazirla({"calisma": c})
denetle(len(vsr) == 1, "VSR üretiliyor")
m = vsr[0][1].duz_metin()
denetle("kanuni temsilci" not in m, "kanuni temsilciden söz edilmiyor")
denetle("Dolayısıyla mükellef hakkında" in m,
        "ceza mükellefin kendisi hakkında isteniyor")

print("\n4) İki yıllı dosyada")
h = istekci()
c = ornek(bilerek=True, iki_yil=True)
belgeler, _i, vsr = h._rapor_hazirla({"calisma": c})
denetle([y for y, _ in belgeler] == [2020, 2021], "her yıl için rapor var")
denetle([y for y, _ in vsr] == [2020],
        "VSR yalnızca bilerek kullanmanın olduğu yıl için üretiliyor")

# ---------------------------------------------------- 5) duzeltme kabul raporu
print("\n5) Düzeltme kabul raporu istenirken")
h = istekci()
c = ornek(bilerek=True, duzeltme=True)
_b, _i, bilerek, vsr = h._kabul_raporu_hazirla({"calisma": c})
denetle(bilerek and len(vsr) == 1, "bilerek kullanmada VSR üretiliyor")
m = vsr[0][1].duz_metin()
denetle("düzeltme beyannameleri ile katma değer vergisi indirimlerinden "
        "çıkarılmış" in m, "tutarların beyandan çıkarıldığı yazılıyor")
denetle("[ceza tutarı]" in m,
        "beyanname yüklenmemişken ceza tutarı kırmızı yer tutucu")
denetle("[oran]" not in m, "oran düzeltme ölçütünden hesaplanıyor")

h = istekci()
c = ornek(bilerek=False, duzeltme=True)
_b, _i, bilerek, vsr = h._kabul_raporu_hazirla({"calisma": c})
denetle(not bilerek and vsr == [],
        "bilmeden kullanmada (vergi tekniği raporu) VSR üretilmiyor")

print("\n6) Düzeltmede tutarlar")
c = ornek(bilerek=True, duzeltme=True)
sonuc, _bulgular = W._hesapla(c)
belge = V.rapor_uret(W._inceleme_bilgisi(c), c["kunye"], W._yillari_coz(c),
                     sonuc, c, V.FIIL_SAHTE_BELGE, 2020, {"ziya": 20000.0})
son = belge.duz_metin().strip().split("\n")[-1]
denetle("\t0,00\t" in son, "tarh edilecek vergi 0,00 yazılıyor")
denetle("60.000,00" in son, "ceza 3 kat (20.000 x 3) yazılıyor")

print("\n7) İbraz etmeme halinde")
c = ornek(bilerek=True)
c["kunye"]["defter_ibraz"] = "İbraz edilmedi"
c["kunye"]["defter_tasdik_makami"] = "Adana 7. Noterliği tasdik kayıtları"
sonuc, _bulgular = W._hesapla(c)
belge = V.rapor_uret(W._inceleme_bilgisi(c), c["kunye"], W._yillari_coz(c),
                     sonuc, c, V.FIIL_IBRAZ_ETMEME, 2020)
m = belge.duz_metin()
denetle(V.gerekli_mi(c, V.FIIL_IBRAZ_ETMEME), "ibraz etmeme VSR'yi gerektiriyor")
denetle("359 uncu maddesinin a bendinde" in m, "359/a bendine atıf yapılıyor")
denetle("Adana 7. Noterliği tasdik kayıtları" in m,
        "defterlerin tasdik makamı yazılıyor")
# 359/a metni henuz dogrulanmadi; uydurulmamis olmasi KASITLI.
denetle("[213 sayılı Vergi Usul Kanununun 359 uncu maddesinin (a) bendinin"
        in m, "359/a madde metni kırmızı yer tutucu olarak bırakılmış")

print()
if HATA:
    print("BAŞARISIZ: %d denetim" % len(HATA))
    for h_ in HATA:
        print("  -", h_)
    sys.exit(1)
print("Tüm denetimler geçti.")
