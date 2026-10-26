"""Vergi Suclari Raporunun EK-3 ozet tablolarini doldurur.

"EK-3: Sahte Belge Kullanma Fiili Nedeniyle Duzenlenen Raporlara Iliskin
Ozet Tablolar", vergi suclari raporunun ekidir ve dairenin kendi Word
formudur. Uygulama formu YENIDEN CIZMEZ: kullanicinin yukledigi dosyayi
acar, tablolarini bulur ve hucrelerini doldurup ayni dosyayi geri verir
(`docx_form`). Form degisirse - daire yeni bir surum yayimlarsa - kullanici
yeni dosyayi yukler, kod degismez.

Kapsam VSR ile AYNIDIR: rapor yalnizca "bilerek kullanma" tespit edilen
saticilara iliskindir (306 Sira No'lu Teblig geregi bilmeden kullanmada suc
yoktur), bu yuzden EK-3 tablolari da yalnizca o saticilarin belgelerini
tasir. Ayni kumeyi iki belgede farkli kurmak, eki raporu tutmayan bir
belgeye cevirirdi.

Faturalarin olcutu `dahil` isaretidir, `sayilir` DEGILDIR: tutar duzeltme
beyannamesiyle indirimlerden cikarilmis olsa bile belge KULLANILMISTIR ve
fiil islenmistir (ayni olcut `faturalar.bilerek_yillari` icinde de boyle).

Tablolar sira numarasiyla degil BASLIKLARIYLA bulunur: formun satir duzeni
degisebilir, sutun adlari kolay kolay degismez. Bulunamayan tablo sessizce
atlanmaz; `rapor` listesinde "bulunamadı" diye doner ve ekranda gorunur.
"""
from . import faturalar as F
from . import inceleme_kunyesi as ik
from . import turkce
from .docx_form import Form, FormHata, karsilastir
from .satirlar import AYLAR

_tl = turkce.tl

# Bir tablonun hangi tablo oldugunu anlamak icin aranan sutun adlari.
IMZALAR = {
    "kullanim": ("fatura no", "yevmiye no"),
    "duzenleyen": ("vergi kimlik numarası", "mükellef yetkilisi"),
    "e_defter": ("dönemi", "e-defter türü"),
    "noter": ("tasdik numarası", "tasdik dönemi"),
}

# Sutun adi -> alan kodu. Ad TAM esitlik aranmaz, sutun adinin ICINDE
# gecmesi yeter: formda "Hakkında VTR Düzenlenen Mükellefin Ünvanı" yaziyor.
KULLANIM_SUTUNLARI = [
    ("sıra no", "sira"),
    ("fatura no", "fatura_no"),
    ("fatura tarihi", "tarih"),
    ("muhteviyat", "muhteviyat"),
    ("kdv tutarı", "kdv"),          # "tutarı"ndan ONCE: ikisi de eslesiyor
    ("toplam tutar", "toplam"),
    ("tutarı", "matrah"),
    ("deftere kayıt tarihi", "kayit_tarihi"),
    ("yevmiye no", "yevmiye_no"),
]

DUZENLEYEN_SUTUNLARI = [
    ("ünvan", "unvan"),
    ("unvan", "unvan"),
    ("yetkilinin t.c. kimlik numarası", "yetkili_tckn"),
    ("vergi kimlik numarası", "vkn"),
    ("mükellef yetkilisi", "yetkili_ad"),
]

NOTER_SUTUNLARI = [
    ("sıra no", "sira"),
    ("noter t.c. kimlik no", None),
    ("noter unvanı", "makam"),
    ("noter vergi dairesi", None),
    ("noterlik", None),
    ("tasdik tarihi", "tasdik_tarihi"),
    ("tasdik numarası", "tasdik_no"),
    ("bildirim tarihi", None),
    ("nevi", "nevi"),
    ("tasdik türü", None),
    ("tasdik dönemi", "yil"),
]


def _sutun_haritasi(basliklar, esleme):
    """{alan kodu: sutun sirasi}. Eslesmeyen sutun haritada yer almaz."""
    harita = {}
    for i, baslik in enumerate(basliklar):
        duz = karsilastir(baslik)
        if not duz:
            continue
        for anahtar, kod in esleme:
            if anahtar in duz:
                if kod and kod not in harita:
                    harita[kod] = i
                break
    return harita


def _satir(harita, sutun_sayisi, degerler):
    """Alan kodlarindan olusan sozlugu tablonun sutun sirasina dizer."""
    satir = [""] * sutun_sayisi
    for kod, deger in degerler.items():
        if kod in harita and harita[kod] < sutun_sayisi:
            satir[harita[kod]] = deger
    return satir


def kullanilan_belgeler(calisma):
    """EK-3'e girecek faturalar: BILEREK kullanilan saticilarin belgeleri.

    Olcut `dahil` isaretidir; duzeltme beyannamesiyle indirimlerden
    cikarilmis belgeler de girer, cunku fiil islenmistir.
    """
    mukellef_vkn = (calisma.get("mukellef") or {}).get("vkn_tckn")
    liste = F.normalize(calisma.get("faturalar"), mukellef_vkn)
    saticilar = calisma.get("saticilar") or {}
    bilerek = F.bilerek_vknler(saticilar)
    secilen = [f for f in liste
               if f.get("dahil") and f.get("yon") != F.YON_SATIS
               and (f.get("satici_vkn") or "") in bilerek]
    secilen.sort(key=lambda f: (f.get("kayit_yil") or 0, f.get("kayit_ay") or 0,
                                str(f.get("tarih") or ""),
                                str(f.get("fatura_no") or "")))
    return secilen


def duzenleyiciler(calisma):
    """EK-3'e girecek saticilar: bilerek kullanma tespit edilenler."""
    mukellef_vkn = (calisma.get("mukellef") or {}).get("vkn_tckn")
    liste = F.normalize(calisma.get("faturalar"), mukellef_vkn)
    saticilar = calisma.get("saticilar") or {}
    return F.bilerek_kullananlar(F.satici_ozeti(liste, saticilar))


def gerekli_mi(calisma):
    """Form doldurulabilir mi: en az bir bilerek kullanma saticisi var mi."""
    return bool(duzenleyiciler(calisma or {}))


# ------------------------------------------------------------ tablo doldurma
def _kullanim_tablosu(tablo, indeks, belgeler, rapor):
    basliklar = tablo.basliklar(indeks)
    harita = _sutun_haritasi(basliklar, KULLANIM_SUTUNLARI)
    satirlar = []
    for sira, f in enumerate(belgeler, 1):
        kayit_tarihi, yevmiye_no = F.yevmiye_hucreleri(f)
        satirlar.append(_satir(harita, len(basliklar), {
            "sira": str(sira),
            "fatura_no": f.get("fatura_no") or "",
            "tarih": F.tarih_goster(f.get("tarih")),
            "muhteviyat": F.mal_cinsi_hucresi(f),
            "matrah": _tl(f.get("matrah")),
            "kdv": _tl(f.get("kdv")),
            "toplam": _tl(f.get("toplam")),
            "kayit_tarihi": kayit_tarihi,
            "yevmiye_no": yevmiye_no,
        }))
    toplam = {}
    for kod, alan in (("matrah", "matrah"), ("kdv", "kdv"),
                      ("toplam", "toplam")):
        if kod in harita:
            toplam[harita[kod]] = _tl(sum(float(f.get(alan) or 0.0)
                                          for f in belgeler))
    tablo.doldur(satirlar, baslik_satiri=indeks + 1, toplam=toplam)
    rapor.append(("Sahte belge kullanım bilgileri",
                  "%d belge yazıldı" % len(satirlar)))


def _duzenleyen_tablosu(tablo, indeks, satici_satirlari, rapor):
    basliklar = tablo.basliklar(indeks)
    harita = _sutun_haritasi(basliklar, DUZENLEYEN_SUTUNLARI)
    satirlar = []
    for s in satici_satirlari:
        satirlar.append(_satir(harita, len(basliklar), {
            "unvan": ik.satici_unvani(s),
            "vkn": s.get("vkn") or "[VKN]",
            # Satici yetkilisi uygulamaya satici kartindan girilir; bos
            # birakilirsa kose parantezli tutucu yazilir ki formda
            # doldurulacak yer gorunsun.
            "yetkili_ad": (s.get("yetkili_ad") or "").strip()
                          or "[yetkilinin adı soyadı]",
            "yetkili_tckn": (s.get("yetkili_tckn") or "").strip()
                            or "[T.C. kimlik no]",
        }))
    tablo.doldur(satirlar, baslik_satiri=indeks + 1)
    rapor.append(("Belgeleri düzenleyen mükellef bilgileri",
                  "%d mükellef yazıldı" % len(satirlar)))


def _e_defter_tablosu(tablo, indeks, kunye, yillar, rapor):
    if not ik.secim_mi(kunye, "e_defter", "Kapsamda"):
        rapor.append(("E-defter bilgisi",
                      "künyede e-Defter kapsamı seçili değil, boş bırakıldı"))
        return
    basliklar = tablo.basliklar(indeks)
    harita = _sutun_haritasi(basliklar, [("dönem", "donem"),
                                         ("e-defter türü", "tur")])
    satirlar = [_satir(harita, len(basliklar),
                       {"donem": str(yil),
                        "tur": "Yevmiye Defteri, Büyük Defter"})
                for yil in yillar]
    tablo.doldur(satirlar, baslik_satiri=indeks + 1)
    rapor.append(("E-defter bilgisi", "%d dönem yazıldı" % len(satirlar)))


def _tasdik_parcala(metin):
    """"12.01.2021 - 4521" -> ("12.01.2021", "4521"); cozulemezse ("", "").

    Kunyedeki defter tablosunda tasdik tarihi ve numarasi TEK hucrededir;
    formda iki ayri sutun var. Ayrim ancak metin gg.aa.yyyy ile basliyorsa
    guvenle yapilabilir - yapilamiyorsa iki hucre de bos birakilir, cunku
    yanlis sutuna yazilan bir tasdik numarasi formu sessizce bozar.
    """
    parca = str(metin or "").strip()
    if len(parca) < 10:
        return "", ""
    bas, kalan = parca[:10], parca[10:]
    bolum = bas.split(".")
    if len(bolum) != 3 or not all(b.isdigit() for b in bolum):
        return "", ""
    return bas, kalan.strip(" -–/,;")


def _noter_tablosu(tablo, indeks, kunye, rapor):
    satirlar_kunye = ik.cizgili_satirlar(kunye, "defter_bilgileri", 4, None)
    if not satirlar_kunye:
        rapor.append(("Noter tasdik bilgileri",
                      "künyede defter bilgisi yok, boş bırakıldı"))
        return
    basliklar = tablo.basliklar(indeks)
    harita = _sutun_haritasi(basliklar, NOTER_SUTUNLARI)
    satirlar = []
    for sira, hucreler in enumerate(satirlar_kunye, 1):
        hucreler = list(hucreler) + [""] * 4
        tarih, no = _tasdik_parcala(hucreler[2])
        satirlar.append(_satir(harita, len(basliklar), {
            "sira": str(sira),
            "yil": hucreler[0],
            "nevi": hucreler[1],
            "tasdik_tarihi": tarih,
            "tasdik_no": no,
            "makam": hucreler[3],
        }))
    tablo.doldur(satirlar, baslik_satiri=indeks + 1)
    rapor.append(("Noter tasdik bilgileri",
                  "%d defter yazıldı" % len(satirlar)))


def _etiketli_hucre(form, anahtar, deger, rapor, ad):
    """"Etiket | deger" bicimindeki kucuk tablolarin deger hucresini yazar."""
    anahtar = karsilastir(anahtar)
    for tablo in form.tablolar():
        for i, satir in enumerate(tablo.metinler()):
            if len(satir) < 2 or anahtar not in karsilastir(satir[0]):
                continue
            tablo.hucreye_yaz(i, 1, deger)
            rapor.append((ad, "yazıldı"))
            return True
    rapor.append((ad, "tablo bulunamadı"))
    return False


def _son_beyan_tarihi(belgeler):
    """Son sahte belgenin dustugu donemin beyanname son verilme tarihi.

    GUNU UYDURMUYORUZ: KDV beyannamesinin verilme gunu yillar icinde
    degisti (ayin 24'u, 26'si, 28'i). Donem kesin olarak biliniyor, gun
    bilinmiyor; bu yuzden ay ve yil yazilip gun kose parantezli birakilir.
    Mufettis taslakta kirmizi gibi duran bu tutucuyu doldurur.
    """
    donemler = sorted({(f.get("kayit_yil"), f.get("kayit_ay")) for f in belgeler
                       if f.get("kayit_yil") and f.get("kayit_ay")})
    if not donemler:
        return ""
    yil, ay = donemler[-1]
    # Beyanname IZLEYEN ayda verilir; Aralik donemi ertesi yilin Ocak'inda.
    izleyen_ay = 1 if ay == 12 else ay + 1
    izleyen_yil = yil + 1 if ay == 12 else yil
    return ("[gün].%02d.%d (%d/%s dönemi KDV beyannamesi)"
            % (izleyen_ay, izleyen_yil, yil, AYLAR[ay - 1]))


# ------------------------------------------------------------------- uretim
def form_doldur(ham, kunye, calisma):
    """Yuklenen EK-3 formunu doldurur.

    Doner: (yeni dosyanin baytlari, [(tablo adi, yapilan), ...])
    """
    kunye = ik.normalize(kunye)
    calisma = calisma or {}
    form = Form(ham)
    rapor = []

    belgeler = kullanilan_belgeler(calisma)
    saticilar = duzenleyiciler(calisma)
    yillar = sorted({f["kayit_yil"] for f in belgeler if f.get("kayit_yil")})

    bulunan = {}
    for kod, anahtarlar in IMZALAR.items():
        for tablo in form.tablolar():
            indeks = tablo.baslik_indeksi(anahtarlar)
            if indeks is not None and kod not in bulunan:
                bulunan[kod] = (tablo, indeks)

    if "kullanim" in bulunan:
        _kullanim_tablosu(*bulunan["kullanim"], belgeler, rapor)
    else:
        rapor.append(("Sahte belge kullanım bilgileri", "tablo bulunamadı"))

    if "duzenleyen" in bulunan:
        _duzenleyen_tablosu(*bulunan["duzenleyen"], saticilar, rapor)
    else:
        rapor.append(("Belgeleri düzenleyen mükellef bilgileri",
                      "tablo bulunamadı"))

    if "e_defter" in bulunan:
        _e_defter_tablosu(*bulunan["e_defter"], kunye, yillar, rapor)
    if "noter" in bulunan:
        _noter_tablosu(*bulunan["noter"], kunye, rapor)

    _etiketli_hucre(form, "vergi türü", "Katma Değer Vergisi", rapor,
                    "Vergi türü")
    son = _son_beyan_tarihi(belgeler)
    if son:
        _etiketli_hucre(form, "sahte belgenin kullanıldığı dönemlere ait", son,
                        rapor, "Beyannamenin verilmesi gereken son tarih")

    yabanci = [(s.get("yetkili_yabanci") or "").strip() for s in saticilar]
    yabanci = [y for y in yabanci if y]
    if yabanci:
        _etiketli_hucre(form, "temsile yetkili kişi yabancı uyruklu",
                        "\n".join(yabanci), rapor,
                        "Yabancı uyruklu temsilci bilgileri")

    return form.bayt(), rapor


def dosya_adi(inceleme):
    ad = "".join(c for c in (inceleme.get("ad_unvan") or "rapor")
                 if c.isalnum() or c in " -_").strip() or "rapor"
    return ("EK-3_Ozet_tablolar_%s.docx" % ad).replace(" ", "_")
