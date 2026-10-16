# -*- coding: utf-8 -*-
"""Vergi suclari raporunun (VSR) gerileme denetimi.

    python3 testler/vsr_testi.py

VSR, VUK 359 kapsamindaki fiiller icin tarhiyat oneren rapora EK OLARAK
duzenlenir. Bu yuzden denetlenen sey yalnizca metin degil, raporun hangi
hallerde URETILDIGI ve hangi hallerde URETILMEDIGI:

  - sahte belgeyi BILEREK kullanma isaretli -> uretilir
  - BILMEDEN kullanma -> uretilmez (306 Sira No'lu Teblig; suc yoktur)
  - cok yilli dosyada -> yine TEK rapor; yillar V. bolumdeki tabloda yil yil
    satirlanir ve atiflar cogullasir ("Vergi Inceleme Raporlarinda")
  - duzeltme kabul raporunda (bilerek) -> uretilir, ama tarh edilecek vergi
    yoktur ve ceza duzeltme uzerine kesilen yarim katin UC KATA tamamlanmis
    halidir

Tek rapor olmasi mufettisin karari (2026-10-09): tarhiyat raporu yil yil
duzenlenir, VSR butun donem icin tek. Ilk surum yil yil ayri rapor
uretiyordu, yanlisti - bu yuzden "kac belge uretildigi" burada denetleniyor.

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

from app import faturalar as F                                       # noqa: E402
from app import inceleme_kunyesi as IK                               # noqa: E402
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
def ornek(kurum=True, bilerek=True, duzeltme=False, iki_yil=False,
          ikinci_yil_bilerek=False):
    """Tek saticili, tek yilli en kucuk dosya; her hal icin uyarlanir.

    `iki_yil` ikinci bir yil ekler. O yilin saticisi varsayilan olarak
    BILMEDEN kullanma; `ikinci_yil_bilerek` ile bilerek yapilir. Ikisi ayri
    hal: birincisi "bilmeyerek olan yil rapora girmemeli"yi, ikincisi
    "iki bilerek yil tek raporda cogul anilmali"yi denetler.
    """
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
        yillar.append({"yil": 2021, "beyan": beyan(), "ay_sayisi": 12,
                       "elestiri": elestiri()})
        # KDV'si birinci yilin saticisindan BUYUK secildi: oran suzgeci
        # calismazsa pay belirgin olarak degisir, boylece denetim ayirt eder.
        fat.append({"duzenleyen_vkn": "3333333333", "alici_vkn": "1234567890",
                    "tarih": "2021-04-10", "fatura_no": "B-1",
                    "matrah": 100000.0, "kdv": 20000.0, "toplam": 120000.0,
                    "dahil": True})
        sat["3333333333"] = {"unvan": ("BİLEREK-2 LTD" if ikinci_yil_bilerek
                                       else "BİLMEDEN-1 LTD"),
                             "kullanma": ("Bilerek kullanma"
                                          if ikinci_yil_bilerek
                                          else "Bilmeden kullanma"),
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
                  # Tarhiyat raporu yil yil duzenlenir; her yilin tarih ve
                  # sayisi ayri satirda girilir.
                  "vir_bilgileri": "2020 | 20.10.2025 | 2025-[2013]/72"
                  + ("\n2021 | 25.10.2025 | 2025-[2013]/80" if iki_yil else ""),
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
denetle(vsr is not None, "bilerek kullanmada VSR üretiliyor")
h._rapor_gonder({"calisma": c})
ad, tur, govde = h.gonderilen[-1]
icerik = paket_icerigi(govde) if tur == "application/zip" else [ad]
denetle(any("Vergi_suclari_raporu" in n for n in icerik),
        "indirilen pakette VSR dosyası var")
denetle("VSR" in ad, "paket adı VSR içerdiğini söylüyor")
denetle(not any(n.startswith("2020_") and "Vergi_suclari" in n
                for n in icerik),
        "VSR dosya adında yıl yok (tek rapor)")

metin = vsr.duz_metin()
denetle("kurumun hakkında" not in metin,
        "“hakkında” yalın ad ile kullanılıyor (ilgi eki fazla değil)")
denetle("Vergi İnceleme Raporu mükellef" not in metin
        and "Vergi İnceleme Raporunda mükellef kurumun bilerek sahte belge "
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
# Giris cumlesi sadelestirildi: "kasitli olarak, yani bilerek ve isteyerek"
# uc kez ayni seyi soyluyordu (mufettisin karari, 2026-10-14).
denetle("faturaları bilerek kullandığı tespit edilmiştir" in metin,
        "giriş cümlesi sade: “bilerek kullandığı tespit edilmiştir”")
denetle("kasıtlı olarak, yani" not in metin,
        "eş anlamlı kelimeler yan yana yazılmıyor")

print("\n2) Bilmeden kullanmada")
h = istekci()
c = ornek(bilerek=False)
_b, _i, vsr = h._rapor_hazirla({"calisma": c})
denetle(vsr is None, "VSR üretilmiyor")

print("\n3) Gerçek kişi mükellefte")
h = istekci()
c = ornek(kurum=False, bilerek=True)
_b, _i, vsr = h._rapor_hazirla({"calisma": c})
denetle(vsr is not None, "VSR üretiliyor")
m = vsr.duz_metin()
denetle("kanuni temsilci" not in m, "kanuni temsilciden söz edilmiyor")
denetle("Dolayısıyla mükellef hakkında" in m,
        "ceza mükellefin kendisi hakkında isteniyor")

print("\n4) İki yıllı dosyada TEK VSR")
h = istekci()
c = ornek(bilerek=True, iki_yil=True)
belgeler, inceleme, vsr = h._rapor_hazirla({"calisma": c})
denetle([u[0] for u in belgeler] == [2020, 2021],
        "tarhiyat raporu her yıl için ayrı")
denetle(vsr is not None, "VSR üretiliyor")
h._rapor_gonder({"calisma": c})
ad, tur, govde = h.gonderilen[-1]
icerik = paket_icerigi(govde)
denetle(sum(1 for n in icerik if "Vergi_suclari_raporu" in n) == 1,
        "pakette TEK VSR var, yıl yıl değil")

m = vsr.duz_metin()
# Bu dosyada 2021 BILMEDEN kullanma. VSR yalnizca suc islenen yillara
# iliskindir; 2021 raporda HIC anilmamali - ne cumlelerde ne tabloda.
# (Sahada boyle cikti: dort yillik bir incelemede uc yil bilerek, bir yil
# bilmedenken VSR dort yili birlikte aniyordu.)
denetle("2020 hesap dönemi" in m and "2020 ve 2021" not in m,
        "giriş bölümü yalnızca bilerek olan yılı anıyor")
denetle("2021" not in m, "bilmeyerek olan yıl raporda hiç geçmiyor")
denetle("2025-[2013]/80" not in m,
        "bilmeyerek olan yılın tarhiyat raporuna atıf yapılmıyor")
denetle("Vergi İnceleme Raporu " in m and "Vergi İnceleme Raporları" not in m,
        "tek yıl kaldığı için atıf tekil")
tablo = [s for s in m.strip().split("\n") if "\tKDV\t" in s]
denetle(len(tablo) == 1, "tablo yalnızca bilerek olan yıl için satır açıyor")
denetle(tablo[0].startswith("20.10.2025\t2025-[2013]/72\t2020"),
        "satır 2020'nin raporunu taşıyor")
denetle("TOPLAM" not in m, "tek satırlı tabloda TOPLAM satırı yok")

# Oran, 3.2'de KASTIN delili. Bilmeden kullanilan 20.000 TL KDV paya
# GIRMEMELI: payda yalnizca bilerek kullanilan 6.000 TL olmali ve bolen de
# yalnizca 2020'nin indirimine inmeli (12 x 80.000 = 960.000).
# 6.000 / 960.000 = %0,62 (0,625 Python'da 0,62'ye yuvarlanir).
# Suzgec calismazsa 26.000 / 1.920.000 = %1,35 cikiyor - ayirt edici deger bu.
denetle("payının %0,62" in m,
        "oran yalnızca bilerek kullanılan belgelerden hesaplanıyor")
denetle("%1,35" not in m, "bilmeyerek kullanılan tutar orana girmiyor")
# Tek bilerek yil kaldi; yil adi yazilmasin, sade yuzde yeter.
denetle("2020 hesap döneminde %0,62" not in m,
        "tek yılda oran yıl adı tekrarlanmadan yazılıyor")

print("\n4b) İki yılın İKİSİ de bilerek")
h = istekci()
c = ornek(bilerek=True, iki_yil=True, ikinci_yil_bilerek=True)
_b, _i, vsr2 = h._rapor_hazirla({"calisma": c})
m2 = vsr2.duz_metin()
denetle("2020 ve 2021 hesap dönemleri" in m2,
        "giriş bölümü iki yılı birlikte anıyor")
denetle("Vergi İnceleme Raporları" in m2,
        "iki rapora atıf çoğul yazılıyor (“Raporları”)")
denetle("Vergi İnceleme Raporlarında" in m2, "çoğul atıf bulunma hâlinde")
denetle("2025-[2013]/72" in m2 and "2025-[2013]/80" in m2,
        "her yılın rapor sayısı metinde geçiyor")
denetle("Söz konusu raporlarda" in m2, "“söz konusu raporlarda” çoğul")
denetle("2025-[2013]/72 sayılı, 25.10.2025 tarih" in m2,
        "raporlar virgülle sıralanıyor (“sayılı ve ... tarih ve” değil)")
tablo2 = [s for s in m2.strip().split("\n") if "\tKDV\t" in s]
denetle(len(tablo2) == 2, "tablo iki yıl için iki satır açıyor")
denetle(tablo2[0].startswith("20.10.2025\t2025-[2013]/72\t2020")
        and tablo2[1].startswith("25.10.2025\t2025-[2013]/80\t2021"),
        "her satır o yılın raporunun tarih/sayısını taşıyor")
denetle("TOPLAM" in m2.strip().split("\n")[-1],
        "çok yıllı tabloda TOPLAM satırı var")

# ---------------------------------------------------- 5) duzeltme kabul raporu
print("\n5) Düzeltme kabul raporu istenirken")
h = istekci()
c = ornek(bilerek=True, duzeltme=True)
_b, _i, bilerek, vsr = h._kabul_raporu_hazirla({"calisma": c})
denetle(bilerek and vsr is not None, "bilerek kullanmada VSR üretiliyor")
m = vsr.duz_metin()
denetle("düzeltme beyannameleri ile katma değer vergisi indirimlerinden "
        "çıkarılmış" in m, "tutarların beyandan çıkarıldığı yazılıyor")
denetle("[ceza tutarı]" in m,
        "beyanname yüklenmemişken ceza tutarı kırmızı yer tutucu")
denetle("[oran]" not in m, "oran düzeltme ölçütünden hesaplanıyor")

h = istekci()
c = ornek(bilerek=False, duzeltme=True)
_b, _i, bilerek, vsr = h._kabul_raporu_hazirla({"calisma": c})
denetle(not bilerek and vsr is None,
        "bilmeden kullanmada (vergi tekniği raporu) VSR üretilmiyor")

print("\n6) Düzeltmede tutarlar")
c = ornek(bilerek=True, duzeltme=True)
sonuc, _bulgular = W._hesapla(c)
belge = V.rapor_uret(W._inceleme_bilgisi(c), c["kunye"], W._yillari_coz(c),
                     sonuc, c, V.FIIL_SAHTE_BELGE,
                     {"yil_ziyasi": {2020: 20000.0}})
son = belge.duz_metin().strip().split("\n")[-1]
denetle("\t0,00\t" in son, "tarh edilecek vergi 0,00 yazılıyor")
denetle("60.000,00" in son, "ceza 3 kat (20.000 x 3) yazılıyor")

# Cok yilli duzeltmede her satirin cezasi O YILIN ziyasindan gelmeli;
# dosya toplamini her satira yazmak cezayi yil sayisi kadar buyutur.
# Iki yilin IKISI de bilerek olmali: bilmeyerek olan yil rapora hic
# girmediginden tablo tek satira duser ve bu denetim anlamsizlasir.
c = ornek(bilerek=True, duzeltme=True, iki_yil=True, ikinci_yil_bilerek=True)
sonuc, _bulgular = W._hesapla(c)
belge = V.rapor_uret(W._inceleme_bilgisi(c), c["kunye"], W._yillari_coz(c),
                     sonuc, c, V.FIIL_SAHTE_BELGE,
                     {"yil_ziyasi": {2020: 20000.0, 2021: 10000.0}})
tablo = [s for s in belge.duz_metin().strip().split("\n") if "\tKDV\t" in s]
denetle(len(tablo) == 2 and "60.000,00" in tablo[0]
        and "30.000,00" in tablo[1],
        "her yılın cezası o yılın ziyasından hesaplanıyor")
denetle("90.000,00" in belge.duz_metin().strip().split("\n")[-1],
        "TOPLAM satırı yılların cezasını topluyor")

print("\n7) Künyedeki rapor bilgileri")
# Tek yilli dosyada yil hucresi bos birakilabilmeli.
c = ornek(bilerek=True)
c["kunye"]["vir_bilgileri"] = " | 20.10.2025 | 2025-[2013]/72"
sonuc, _bulgular = W._hesapla(c)
m = V.rapor_uret(W._inceleme_bilgisi(c), c["kunye"], W._yillari_coz(c),
                 sonuc, c).duz_metin()
denetle("20.10.2025 tarih ve 2025-[2013]/72 sayılı" in m,
        "yıl hücresi boş bırakılan satır tek yıla bağlanıyor")
# Sahte belge VSR'sinde de 359/b hapis suresi 7394 sonrasi olmali.
denetle("üç yıldan sekiz yıla kadar hapis cezası" in m,
        "359/b hapis süresi 7394 sonrası (sekiz yıl)")
denetle("üç yıldan beş yıla" not in m, "eski (b) süresi kalmamış")
tablo = [s for s in m.strip().split("\n") if "\tKDV\t" in s]
denetle(len(tablo) == 1 and "\t2020\t" in tablo[0],
        "tabloda yıl künyeden değil incelemeden geliyor")

# VSR'nin ilk surumunde tarih ve sayi tek alanda tutuluyordu; once
# kaydedilmis calismalarda belge sessizce bos cikmamali.
c = ornek(bilerek=True)
del c["kunye"]["vir_bilgileri"]
c["kunye"]["vir_tarihi"] = "20.10.2025"
c["kunye"]["vir_sayisi"] = "2025-[2013]/72"
sonuc, _bulgular = W._hesapla(c)
m = V.rapor_uret(W._inceleme_bilgisi(c), c["kunye"], W._yillari_coz(c),
                 sonuc, c).duz_metin()
denetle("20.10.2025 tarih ve 2025-[2013]/72 sayılı" in m,
        "eski tek alanlı biçim de okunuyor")

# Hic girilmemisse kirmizi yer tutucu kalmali, sessizce bos gecmemeli.
c = ornek(bilerek=True)
del c["kunye"]["vir_bilgileri"]
sonuc, _bulgular = W._hesapla(c)
m = V.rapor_uret(W._inceleme_bilgisi(c), c["kunye"], W._yillari_coz(c),
                 sonuc, c).duz_metin()
denetle("[rapor tarihi] tarih ve [rapor sayısı] sayılı" in m,
        "girilmemiş rapor bilgisi kırmızı yer tutucu bırakıyor")

print("\n4c) Oran yıl yıl yazılıyor")
# Mufettisin karari (2026-10-14): tek bir birlesik yuzde, bir yilin agir
# digerinin hafif oldugu dosyalarda ikisini de yanlis temsil ediyordu.
# Yillara belirgin olarak farkli buyuklukte sahte belge konuldu.
c = ornek(bilerek=True, iki_yil=True, ikinci_yil_bilerek=True)
# 2020: 6.000 / 960.000 = %0,62   |   2021: 20.000 / 960.000 = %2,08
h = istekci()
_b, _i, vsr3 = h._rapor_hazirla({"calisma": c})
m3 = vsr3.duz_metin()
denetle("2020 hesap döneminde %0,62 ve 2021 hesap döneminde %2,08" in m3,
        "her yılın oranı ayrı ayrı ve yıl adıyla yazılıyor")
denetle("payının 2020" in m3, "cümle ilgi ekiyle kuruluyor (“payının”)")
# Birlesik oran 26.000 / 1.920.000 = %1,35; artik hic yazilmamali.
denetle("%1,35" not in m3, "yılları birleştiren tek oran yazılmıyor")

# Cumlenin butun bicimleri. "yuksek" nitelemesi yalnizca BUTUN yillar
# esigin ustundeyse yazilir; %1'lik bir payi "yuksek" demek raporu itiraz
# edilebilir hale getirir.
kurum = IK.normalize({"mukellef_turu": "Kurum (sermaye şirketi)"})
gercek = IK.normalize({"mukellef_turu": "Gerçek kişi"})
denetle(V._oran_ifadesi(kurum, [{"yil": 2020, "oran": 1.25}])
        == "%1,25 olarak hesaplandığı görülmektedir.",
        "tek yıl, düşük oran: sade yüzde")
denetle("gibi yüksek bir orana tekabül ettiği"
        in V._oran_ifadesi(kurum, [{"yil": 2020, "oran": 42.5}]),
        "tek yıl, yüksek oran: “yüksek bir orana”")
karisik = V._oran_ifadesi(kurum, [{"yil": 2020, "oran": 5.0},
                                  {"yil": 2021, "oran": 30.0}])
denetle("yüksek" not in karisik,
        "bir yıl eşiğin altındaysa “yüksek” denmiyor")
ikisi_yuksek = V._oran_ifadesi(kurum, [{"yil": 2020, "oran": 40.0},
                                       {"yil": 2021, "oran": 55.0}])
denetle("gibi yüksek oranlara tekabül ettiği" in ikisi_yuksek,
        "iki yıl da yüksekse çoğul: “yüksek oranlara”")
denetle("2020 takvim yılında" in V._oran_ifadesi(
            gercek, [{"yil": 2020, "oran": 8.0}, {"yil": 2021, "oran": 9.0}]),
        "gerçek kişide “takvim yılında” deniyor")
denetle(V._oran_ifadesi(kurum, []) == "[oran] olarak hesaplandığı görülmektedir.",
        "ölçülemeyen oran kırmızı yer tutucu bırakıyor")
denetle(V._oran_ifadesi(kurum, [{"yil": 2020, "oran": None}])
        == "[oran] olarak hesaplandığı görülmektedir.",
        "oranı None olan yıl yer tutucuya düşüyor")

print("\n7b) Elle eklenen satıcı yalnızca kendi yılının raporunda")
# Sahada boyle cikti (2026-10-14): fatura listesi bulunmayan, elle eklenen
# bir satici (2021 icin sahteci, is emri yok) HER yilin raporunda
# goruluyordu. Sebep: rapor yil yil yazilirken `faturalar` daraltiliyor ama
# elle eklenen saticinin fatura satiri YOK, daraltma onu elemiyordu.
#
# Unvanlar belgede Turkce kucultmeden geciyor; denetimde Turkce'ye ozgu
# harf TASIMAYAN bir unvan secildi ("ELLE-X" -> "elle-x"). "YILSIZ" gibi
# bir unvan "yılsız" olur ve duz arama tutmaz - bu tuzaga bir kez dusuldu.
ELLE_VKN = "4444444444"


def elle_satici_ile(elle_yil):
    c = ornek(bilerek=True, iki_yil=True, ikinci_yil_bilerek=True)
    c["saticilar"][ELLE_VKN] = {
        "elle": "Evet", "unvan": "ELLE-X LTD", "kullanma": "Bilerek kullanma",
        "vergi_dairesi": "5 OCAK VD", "vtr_no": "2025/55",
        "vtr_tarihi": "01.02.2025", "elle_yil": elle_yil, "elle_adet": "3",
        "elle_matrah": "90.000", "elle_kdv": "18.000",
        "not": "sahte belge düzenlediği"}
    h = istekci()
    belgeler, _inceleme, _vsr = h._rapor_hazirla({"calisma": c})
    return {yil: "elle-x" in belge.duz_metin().lower()
            for yil, belge, _ad in belgeler}


gorunum = elle_satici_ile("2021")
denetle(gorunum.get(2021) is True, "kendi yılının raporunda görünüyor")
denetle(gorunum.get(2020) is False, "başka yılın raporunda GÖRÜNMÜYOR")

# Yil girilmemisse sessizce dusurulmemeli: mufettisin farketmeyecegi bir
# veri kaybi olurdu. Her yilda gorunur, alanin ipucu bunu soyluyor.
yilsiz = elle_satici_ile("")
denetle(all(yilsiz.values()),
        "yılı girilmemiş satıcı her yılda görünüyor (sessizce düşmüyor)")

# Elle eklenen bilerek satici, VSR'nin yil kapsamina da girmeli: fatura
# satiri olmadigindan `bilerek_yillari` onu atlarsa o yil hic bilerek
# sayilmaz ve VSR yili atlardi.
c = ornek(bilerek=False, iki_yil=False)          # listedeki satici bilmeden
c["saticilar"][ELLE_VKN] = {
    "elle": "Evet", "unvan": "ELLE-X LTD", "kullanma": "Bilerek kullanma",
    "elle_yil": "2020", "elle_adet": "3", "elle_matrah": "90.000",
    "elle_kdv": "18.000", "not": "sahte belge düzenlediği"}
liste = F.normalize(c["faturalar"], c["mukellef"]["vkn_tckn"])
denetle(F.bilerek_yillari(liste, c["saticilar"]) == [2020],
        "elle eklenen bilerek satıcının yılı VSR kapsamına giriyor")

print("\n8) İbraz etmeme halinde")
# Ibraz etmeme VSR'sinin YAPISI sahte belgeden farklidir (mufettisin ornek
# raporu, 2026-10-16): dort bolum (1-GIRIS, 2-SUCUN UNSURLARI, 3-SUCUN
# FAILI, 4-SONUC), "yapilan tespitler" bolumu ve tarhiyat onerisi tablosu
# YOK. Tarhiyat bilgileri ibraz etmeme raporunda yer aliyor.
c = ornek(bilerek=True)
c["kunye"]["defter_ibraz"] = "İbraz edilmedi"
c["kunye"]["ibraz_yazi_tarihi"] = "17.08.2025"
c["kunye"]["ibraz_yazi_sayisi"] = "E-2222222-000[A]-30478"
c["kunye"]["ibraz_teblig_tarihi"] = "22.08.2025"
c["kunye"]["defter_bilgileri"] = (
    "2020 | Yevmiye Defteri | 18.12.2019-38254 | Adana 11. Noterliği")
sonuc, _bulgular = W._hesapla(c)
belge = V.rapor_uret(W._inceleme_bilgisi(c), c["kunye"], W._yillari_coz(c),
                     sonuc, c, V.FIIL_IBRAZ_ETMEME)
m = belge.duz_metin()
denetle(V.gerekli_mi(c, V.FIIL_IBRAZ_ETMEME), "ibraz etmeme VSR'yi gerektiriyor")

for baslik in ("1- GİRİŞ", "2. SUÇUN UNSURLARI", "2.1. Suçun Kanuni Unsuru",
               "2.2. Suçun Maddi Unsurları", "2.3. Suçun Manevi Unsurları",
               "3. SUÇUN FAİLİ", "4- SONUÇ"):
    denetle(baslik in m, "bölüm var: %s" % baslik)
denetle("YAPILAN TESPİTLER" not in m,
        "tespitler bölümü YOK (sahte belge yapısı sızmamış)")
denetle("Raporun Tarihi" not in m and "Etkin" not in m,
        "tarhiyat önerisi tablosu YOK")
denetle("III-" not in m and "IV-" not in m and "V-" not in m,
        "sahte belge bölüm numaraları sızmamış")

# 359/a-2 bendi ve metni. Metin mufettisin ornek VSR'sinden BIREBIR alindi;
# daha once kirmizi yer tutucuydu ve uydurulmamisti.
denetle("359 uncu maddesinin (a-2) bendinde" in m,
        "kanuni unsur 359/a-2 bendine dayandırılıyor")
denetle("Defter, kayıt ve belgeleri tahrif edenler veya gizleyenler" in m,
        "359/a-2 madde metni birebir yazılıyor")
denetle("gizleme olarak kabul edilir" in m,
        "ibraz etmemenin gizleme sayıldığı hüküm yazılıyor")
denetle("[213 sayılı Vergi Usul Kanununun 359 uncu maddesinin (a) bendinin"
        not in m, "eski kırmızı yer tutucu kalkmış")
denetle("359/a-2 maddesinde yer alan kaçakçılık fiilinin işlendiği" in m,
        "maddi unsur fiili 359/a-2'ye bağlıyor")

# Defterlerin VARLIGI gizleme fiilinin on kosulu; tasdik tablosu bunu
# ortaya koyuyor ve artik tek satirlik bir makam adindan degil
# "İbraz edilen defterler" tablosundan geliyor.
denetle("İbraz Edilmeyen Defter Tasdik Bilgileri" in m,
        "tasdik tablosu başlığı yazılıyor")
denetle("Adana 11. Noterliği" in m and "18.12.2019-38254" in m,
        "tasdik satırı künyedeki defter tablosundan geliyor")

# Belge basim bilgileri VARSA yazilir. Girilmemisken ne tablo ne de ona
# gonderme yapan cumle bulunmali - her mukellefte bu kayit yok.
denetle("İbraz Edilmeyen Belgelerin Basım Bilgileri" not in m,
        "basım kaydı girilmemişse tablo yazılmıyor")
denetle("belge basım bilgilerinin" not in m,
        "basım kaydı yoksa cümle de defterle sınırlı kalıyor")
denetle("defter bilgilerinin aşağıdaki gibi" in m,
        "basım kaydı yokken defter cümlesi bozulmuyor")

c_basim = dict(c)
c_basim["kunye"] = dict(c["kunye"], belge_basim_bilgileri=(
    "H A | 11.10.2013 | Fatura | A | 539001 | 539500 | 10\n"
    "A Y | 02.11.2018 | İrsaliyeli Fatura | A | 253651 | 253900 | 5"))
m_basim = V.rapor_uret(W._inceleme_bilgisi(c_basim), c_basim["kunye"],
                       W._yillari_coz(c_basim), sonuc, c_basim,
                       V.FIIL_IBRAZ_ETMEME).duz_metin()
denetle("İbraz Edilmeyen Belgelerin Basım Bilgileri" in m_basim,
        "basım kaydı varsa tablo yazılıyor")
denetle("defter bilgileri ve belge basım bilgilerinin aşağıdaki gibi"
        in m_basim, "cümle iki tabloyu birlikte duyuruyor")
denetle("539001" in m_basim and "253900" in m_basim,
        "iki basım satırı da yazılıyor")
denetle("Anlaşmalı Matbaa" in m_basim and "Belge Adedi" in m_basim,
        "başlıklar alan bildiriminden geliyor")
denetle(m_basim.find("Basım Bilgileri") < m_basim.find("Defter Tasdik"),
        "örnekteki gibi basım tablosu tasdik tablosundan önce")
denetle("1- Mükellef Kurum" in m_basim
        and "defter ve belgelerin varlığı aşağıdaki tasdik ve basım "
            "kayıtlarıyla sabittir" in m_basim,
        "basım varsa 1. delil belgelerin varlığını da kapsıyor")
denetle("defterlerin varlığı aşağıdaki tasdik kayıtlarıyla sabittir" in m,
        "basım yoksa 1. delil yalnızca defterlerle sınırlı")

# ------- maddi unsur: delil zinciri (mufettisin istegi, 2026-10-16:
# "diger vsr ile kiyasla maddi unsur ve delilleri ibraz etmemeye gore")
denetle("Fiile İlişkin Tespit ve Deliller" in m, "delil listesi başlığı var")
for no in ("1-", "2-", "3-", "4-", "5-"):
    denetle(("\n%s " % no) in m or ("\n%s" % no) in m,
            "delil maddesi var: %s" % no)
denetle("253 üncü maddesi" in m and "256 ncı maddesi" in m,
        "muhafaza ve ibraz ödevi VUK 253/256'ya dayandırılıyor")
denetle(m.count("2- Müfettişliğimizce düzenlenen") == 1,
        "isteme yazısı delil listesinde numaralı yazılıyor")
denetle("13 üncü maddesinde sayılan mücbir sebep" in m,
        "mücbir sebep bulunmadığı tespiti yazılıyor")
denetle("yasal defterlere kaydı gereken hesap ve işlemlerin bulunduğu" in m,
        "kaydı gereken işlemlerin varlığı delil olarak yazılıyor")
denetle("adet belge" in m and "adına 1 adet belge düzenlendiği" in m,
        "belge dökümünden sayısal tespit yazılıyor")
denetle("vergi ziyaına sebebiyet vermiştir" in m,
        "maddi unsur neticeye (ziyaa) bağlanıyor")
denetle("suçun maddi unsurunun oluştuğu anlaşılmaktadır" in m,
        "delil zinciri değerlendirme cümlesiyle kapanıyor")
# Tutar ONERILMIYOR, ibraz etmeme raporuna atfen aniliyor.
denetle("re’sen tarh edilmesi gerektiği sonucuna varıldığı" not in m,
        "VSR kendisi tarhiyat önermiyor")

# Fatura dokumu yoksa sayi UYDURULMAMALI.
c_dokumsuz = dict(c, faturalar=[])
m_dokumsuz = V.rapor_uret(W._inceleme_bilgisi(c_dokumsuz), c["kunye"],
                          W._yillari_coz(c), sonuc, c_dokumsuz,
                          V.FIIL_IBRAZ_ETMEME).duz_metin()
denetle("adet belge" not in m_dokumsuz,
        "döküm yoksa belge sayısı uydurulmuyor")
denetle("Faturalar sekmesine girildiğinde" in m_dokumsuz,
        "döküm yoksa yer tutucu ne yapılacağını söylüyor")

# 359 hapis sureleri 7394 sayili Kanunla degisik hali olmali.
denetle("on sekiz aydan beş yıla kadar hapis" in m,
        "359/a hapis süresi 7394 sonrası (beş yıl)")
denetle("on sekiz aydan üç yıla" not in m, "eski (a) süresi kalmamış")

denetle("GİB Intranet sisteminden yapılan sorgulama neticesinde mükellef "
        "kurumun anlaşmalı matbaalara" not in m_basim,
        "VSR'de basım tablosu için ayrı sorgulama cümlesi tekrar edilmiyor")

# Isteme yazisi hem girişte hem maddi unsurda aniliyor (ornek de boyle).
denetle(m.count("Defter ve Belge İsteme yazısı") == 2,
        "isteme yazısı giriş ve maddi unsurda anılıyor")
denetle("17.08.2025" in m and "22.08.2025" in m,
        "yazı ve tebliğ tarihleri yazılıyor")

# Kurumda odev kanuni temsilciye dusuyor; dayanak VUK 10.
denetle("10 uncu maddesi kanuni temsilcilerin ödevini" in m,
        "kurumda VUK 10'a dayanılıyor")
m_gercek = V.rapor_uret(
    W._inceleme_bilgisi(ornek(kurum=False)),
    dict(ornek(kurum=False)["kunye"], defter_ibraz="İbraz edilmedi"),
    W._yillari_coz(c), sonuc, c, V.FIIL_IBRAZ_ETMEME).duz_metin()
denetle("kanuni temsilcilerin ödevini" not in m_gercek,
        "gerçek kişide VUK 10 anılmıyor")

denetle("4.1- Defter ve belge ibraz etmeme fiili nedeniyle kaçakçılık suçu "
        "işlediği tespit edilen" in m,
        "sonuç bölümü suç duyurusunu istiyor")
denetle("re’sen tarh" not in m[m.find("4- SONUÇ"):],
        "sonuç bölümü tarhiyat istemiyor (o, ibraz etmeme raporunun işi)")

print()
if HATA:
    print("BAŞARISIZ: %d denetim" % len(HATA))
    for h_ in HATA:
        print("  -", h_)
    sys.exit(1)
print("Tüm denetimler geçti.")
