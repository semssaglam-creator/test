"""Yerel web sunucusu: JSON API + tek sayfalik arayuz.

Calisma verisi sunucuda tutulmaz. Tarayici, uzerinde calisilan veriyi bellekte
tasir ve her hesaplama icin sunucuya gonderir; sunucu yalnizca hesaplar ve
sonucu dondurur. Veritabanina yazma, kullanici acikca "Kaydet" dediginde
gerceklesir.

Yalnizca Python standart kutuphanesi kullanilir (http.server, json).
Sunucu 127.0.0.1 adresine baglanir; disaridan erisime acilmaz.
"""
import base64
import binascii
import io
import json
import os
import posixpath
import urllib.parse
import zipfile
from datetime import datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from . import db, hesap
from .excel_export import calisma_olustur, fatura_listesi_olustur
from .paste_parser import (beyan_ayristir, ozet_ayristir, ozet_tablosu_mu,
                           tek_satir_ayristir, tutar_coz)
from .rapor_metni import matrah_farki_ozeti
from .satirlar import (AYLAR, AYRISTIRMA_BLOKLARI, BEYAN_SATIRLARI,
                       BEYAN_TOPLAM_TURLERI, ELESTIRI_ALANLARI,
                       OZET_HEDEF_SECENEKLERI, OZET_KOLONLARI, TARHIYAT_KOLONLARI,
                       TOPLAM_ACIKLAMALARI, TOPLAM_EK_BILGI, TOPLAM_TURLERI,
                       VERI_KODLARI)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WEB_DIR = os.path.join(BASE_DIR, "web")
CIKTI_DIR = os.path.join(BASE_DIR, "ciktilar")


class ApiHata(Exception):
    """Kullaniciya gosterilecek hata mesaji."""


def _dosya_basligi(dosya_adi):
    """Content-Disposition basligini Turkce karakterlerle birlikte kurar.

    Yalnizca `filename="..."` kullanip icine yuzde kodlamasi koymak ise
    yaramiyor: tarayici o metni cozmez, dosyayi "download" adiyla kaydeder.
    Dogrusu, ASCII'ye indirgenmis bir yedek ad ile birlikte RFC 5987
    bicimindeki `filename*` alanini vermektir.
    """
    yedek = dosya_adi.encode("ascii", "replace").decode("ascii").replace("?", "_")
    return ('attachment; filename="%s"; filename*=UTF-8\'\'%s'
            % (yedek, urllib.parse.quote(dosya_adi)))


def _beyanname_modulu():
    """Beyanname okuma modullerini ilk ihtiyac aninda yukler.

    Bilerek modul basinda degil burada yuklenir: beyanname okuma pypdf'e
    dayanir ve pypdf uygulamanin geri kalaninin calismasi icin gerekli
    degildir. Bu yuzden oradaki bir aksilik yalnizca beyanname yukleme
    ekraninda bir hata mesajina donusur; uygulamanin acilisini ya da
    yapistirarak calisma yontemini hicbir bicimde etkilemez.
    """
    from . import beyannameler
    return beyannameler


def _belge_modulleri():
    """Tutanak/rapor uretimini ilk ihtiyac aninda yukler.

    Ayni gerekce: bu modullerdeki bir aksilik uygulamanin acilisini degil,
    yalnizca belge uretme dugmesini etkilesin.
    """
    from . import inceleme_kunyesi, tutanak
    return inceleme_kunyesi, tutanak


def _fatura_modulu():
    """Fatura modelini ilk ihtiyac aninda yukler."""
    from . import faturalar
    return faturalar


# --------------------------------------------------------------------- yardimci
def _yillari_coz(calisma):
    """Istemciden gelen calismayi hesap motorunun bekledigi bicime getirir."""
    yillar = []
    for ham in calisma.get("yillar") or []:
        try:
            yil = int(ham.get("yil"))
        except (TypeError, ValueError):
            raise ApiHata("Yıl değeri geçersiz.")
        beyan = {}
        gelen = ham.get("beyan") or {}
        for kod in VERI_KODLARI:
            dizi = gelen.get(kod) or []
            beyan[kod] = [_sayi(d) for d in (list(dizi) + [0.0] * 12)[:12]]
        elestiri = hesap.bos_elestiri()
        gelen_e = ham.get("elestiri") or {}
        for alan in ("matrah_ilave", "hesaplanan_kdv_ilave", "devir_cikar",
                     "indirim_cikar", "yuklenilen_cikar"):
            dizi = gelen_e.get(alan) or []
            elestiri[alan] = [_sayi(d) for d in (list(dizi) + [0.0] * 12)[:12]]
        oranlar = (gelen_e.get("kdv_orani") or []) + [None] * 12
        elestiri["kdv_orani"] = [None if o in (None, "") else _sayi(o) for o in oranlar[:12]]
        otomatik = (gelen_e.get("hesaplanan_otomatik") or []) + [True] * 12
        elestiri["hesaplanan_otomatik"] = [bool(o) for o in otomatik[:12]]
        # "indirim_sifirla" bu alanin onceki adiydi; eski kayitlar acilabilsin
        sinirla = (gelen_e.get("indirim_sinirla")
                   or gelen_e.get("indirim_sifirla") or []) + [False] * 12
        elestiri["indirim_sinirla"] = [bool(s) for s in sinirla[:12]]
        pin = ham.get("devir_baslangic")
        yillar.append({
            "yil": yil,
            "ay_sayisi": max(1, min(int(ham.get("ay_sayisi") or 12), 12)),
            "devir_baslangic": None if pin in (None, "") else _sayi(pin),
            "beyan": beyan,
            "elestiri": elestiri,
        })
    # Eski kayitlarda calisma duzeyinde tutulan baslangic devri, ilk yilin
    # kendi degeri yoksa o yila uygulanir (geriye donuk uyum)
    ham_baslangic = calisma.get("devreden_baslangic")
    if yillar and ham_baslangic not in (None, ""):
        ilk = min(yillar, key=lambda y: y["yil"])
        if ilk["devir_baslangic"] is None:
            ilk["devir_baslangic"] = _sayi(ham_baslangic)
    return yillar


def _sayi(deger):
    if isinstance(deger, (int, float)):
        return float(deger)
    return tutar_coz(deger) or 0.0


def _ziya_kati(calisma):
    """Vergi ziyai cezasinin kati: bilerek kullanmada uc, aksi halde bir kat."""
    try:
        kat = int(str((calisma or {}).get("ziya_kati") or 1).strip()[0])
    except (ValueError, IndexError):
        kat = 1
    return 3 if kat == 3 else 1


def _hesapla(calisma):
    """Calismayi hesaplar; veritabanina dokunmaz."""
    yillar = _yillari_coz(calisma)
    if not yillar:
        return {"donemler": [], "yil_toplamlari": [], "genel_toplam": {},
                "tarhiyat_toplami": {}, "yil_uyumu": [],
                "kaynak_analizi": {"kaynaklar": [], "donemler": [], "etkilesim_var": False}}, []
    # Baslangic devri artik yil bazinda tutulur; _yillari_coz eski kayitlardaki
    # calisma duzeyindeki degeri ilk yila tasidi.
    sonuc = hesap.seri_hesapla(yillar, ziya_kati=_ziya_kati(calisma))
    sonuc["kaynak_analizi"] = hesap.kaynak_analizi(yillar)
    sonuc["dikkat"] = _dikkat_dokumu(calisma, yillar)
    return sonuc, (hesap.indirim_asimi_bulgulari(yillar)
                   + hesap.beyan_tutarlilik_kontrol(yillar))


def _dikkat_dokumu(calisma, yillar):
    """Fatura listesinin beyan edilen indirimi astigi donemlerin dokumu.

    Fatura listesi yuklenmemisse bos doner; fatura modulundeki bir aksilik de
    hesabin geri kalanini engellemez.
    """
    if not (calisma or {}).get("faturalar"):
        return []
    try:
        faturalar = _fatura_modulu()
        liste = faturalar.normalize(calisma["faturalar"],
                                    (calisma.get("mukellef") or {}).get("vkn_tckn"))
        sinirlar = {}
        for yil_kaydi in yillar:
            for ay in range(int(yil_kaydi.get("ay_sayisi") or 12)):
                sinirlar[(int(yil_kaydi["yil"]), ay + 1)] = hesap.indirim_siniri(
                    yil_kaydi.get("beyan") or {}, ay)
        return faturalar.dikkat_dokumu(liste, sinirlar,
                                       calisma.get("saticilar") or {})
    except Exception:  # noqa: BLE001
        return []


def _inceleme_bilgisi(calisma):
    """Excel ve rapor basliklarinda kullanilan mukellef bilgisi."""
    mukellef = calisma.get("mukellef") or {}
    return {
        "ad": calisma.get("ad") or "Çalışma",
        "ad_unvan": mukellef.get("ad_unvan") or db.ADSIZ_MUKELLEF,
        "vkn_tckn": mukellef.get("vkn_tckn") or "",
        "vergi_dairesi": mukellef.get("vergi_dairesi") or "",
        "adres": mukellef.get("adres") or "",
    }


class Istekci(BaseHTTPRequestHandler):
    server_version = "KDVIncelemeSunucu/2.0"

    def log_message(self, bicim, *args):  # sunucu gunlugunu sessizlestir
        pass

    # ------------------------------------------------------------------ yanit
    def _json_yanit(self, veri, kod=200):
        govde = json.dumps(veri, ensure_ascii=False).encode("utf-8")
        self.send_response(kod)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(govde)))
        self._onbellek_kapali()
        self.end_headers()
        self.wfile.write(govde)

    def _hata(self, mesaj, kod=400):
        self._json_yanit({"hata": mesaj}, kod)

    def _govde_oku(self):
        uzunluk = int(self.headers.get("Content-Length") or 0)
        if not uzunluk:
            return {}
        ham = self.rfile.read(uzunluk).decode("utf-8")
        try:
            return json.loads(ham)
        except json.JSONDecodeError as exc:
            raise ApiHata(f"Geçersiz istek gövdesi: {exc}")

    # -------------------------------------------------------------------- GET
    def do_GET(self):
        ayrisik = urllib.parse.urlparse(self.path)
        yol = ayrisik.path
        params = urllib.parse.parse_qs(ayrisik.query)
        try:
            if yol in ("/", "/index.html"):
                self._dosya_gonder(os.path.join(WEB_DIR, "index.html"),
                                   "text/html; charset=utf-8")
            elif yol in ("/favicon.ico", "/ikon.png"):
                self._dosya_gonder(os.path.join(BASE_DIR, "ikon.png"),
                                   "image/png", onbellek_kapali=False)
            elif yol == "/api/tanimlar":
                self._json_yanit({
                    "satirlar": [{"kod": k, "etiket": e, "baslik": b,
                                  "toplam_turu": BEYAN_TOPLAM_TURLERI.get(k)}
                                 for k, e, b in BEYAN_SATIRLARI],
                    "aylar": AYLAR,
                    "elestiri_alanlari": [{"kod": k, "etiket": e} for k, e in ELESTIRI_ALANLARI],
                    "ozet_kolonlari": [{"kod": k, "etiket": e} for k, e in OZET_KOLONLARI],
                    "tarhiyat_kolonlari": [{"grup": g, "kod": k, "etiket": e, "vurgu": v}
                                           for g, k, e, v in TARHIYAT_KOLONLARI],
                    "ayristirma_bloklari": [{"kod": k, "etiket": e, "aciklama": a}
                                            for k, e, a in AYRISTIRMA_BLOKLARI],
                    "ozet_hedefleri": [{"kod": k, "etiket": e}
                                       for k, e in OZET_HEDEF_SECENEKLERI],
                    "toplam_turleri": TOPLAM_TURLERI,
                    "toplam_aciklamalari": TOPLAM_ACIKLAMALARI,
                    "toplam_ek_bilgi": {k: {"etiket": e, "alan": a}
                                       for k, (e, a) in TOPLAM_EK_BILGI.items()},
                    "bu_yil": datetime.now().year,
                    "kunye_bolumleri": _belge_modulleri()[0].BOLUMLER,
                    "satici_alanlari": _fatura_modulu().SATICI_ALANLARI,
                    "fatura_yonleri": [{"kod": k, "etiket": e} for k, e in
                                       _fatura_modulu().YON_ETIKETLERI.items()],
                })
            elif yol == "/api/calismalar":
                self._json_yanit({"calismalar": db.calismalari_listele()})
            elif yol == "/api/calisma":
                self._json_yanit({"calisma": db.calisma_getir(int(params["id"][0]))})
            elif yol == "/api/yedekler":
                self._json_yanit({"yedekler": db.yedekleri_listele()})
            else:
                self._hata("Bulunamadı", 404)
        except ApiHata as exc:
            self._hata(str(exc))
        except (KeyError, ValueError, IndexError) as exc:
            self._hata(f"Geçersiz istek: {exc}")
        except Exception as exc:  # noqa: BLE001
            self._hata(f"Sunucu hatası: {exc}", 500)

    # ------------------------------------------------------------------- POST
    def do_POST(self):
        yol = urllib.parse.urlparse(self.path).path
        try:
            veri = self._govde_oku()
            if yol == "/api/hesapla":
                sonuc, bulgular = _hesapla(veri.get("calisma") or {})
                self._json_yanit({"sonuc": sonuc, "bulgular": bulgular})
            elif yol == "/api/ayristir":
                self._json_yanit(self._ayristir(veri))
            elif yol == "/api/satir_ayristir":
                try:
                    self._json_yanit({"degerler": tek_satir_ayristir(veri.get("metin") or "")})
                except ValueError as exc:
                    raise ApiHata(str(exc))
            elif yol == "/api/kaydet":
                calisma = veri.get("calisma") or {}
                if not (calisma.get("yillar") or []):
                    raise ApiHata("Kaydedilecek veri yok; önce beyan bloğunu yapıştırın.")
                yeni = db.calisma_kaydet(calisma, veri.get("id"))
                self._json_yanit({"id": yeni, "calismalar": db.calismalari_listele()})
            elif yol == "/api/calisma/sil":
                try:
                    db.calisma_sil(int(veri["id"]))
                except ValueError as exc:
                    raise ApiHata(str(exc))
                self._json_yanit({"tamam": True, "calismalar": db.calismalari_listele()})
            elif yol == "/api/rapor_metni":
                calisma = veri.get("calisma") or {}
                sonuc, bulgular = _hesapla(calisma)
                if not sonuc["donemler"]:
                    raise ApiHata("Önce beyan bloğunu yapıştırın.")
                self._json_yanit({"metin": matrah_farki_ozeti(
                    _inceleme_bilgisi(calisma), sonuc, bulgular)})
            elif yol == "/api/pdf_oku":
                self._json_yanit(self._pdf_oku(veri))
            elif yol == "/api/beyanname_ozet":
                self._json_yanit(self._beyanname_ozet(veri))
            elif yol == "/api/beyanname_uygula":
                self._json_yanit(self._beyanname_uygula(veri))
            elif yol == "/api/vergi_beyani_oku":
                self._json_yanit(self._vergi_beyani_oku(veri))
            elif yol == "/api/fatura_oku":
                self._json_yanit(self._fatura_oku(veri))
            elif yol == "/api/fatura_ozet":
                self._json_yanit(self._fatura_ozet(veri))
            elif yol == "/api/tutanak":
                self._tutanak_gonder(veri)
            elif yol == "/api/tutanak_onizleme":
                self._json_yanit(self._tutanak_onizleme(veri))
            elif yol == "/api/sahte_belge_raporu":
                self._rapor_gonder(veri)
            elif yol == "/api/sahte_belge_onizleme":
                self._json_yanit(self._rapor_onizleme(veri))
            elif yol == "/api/excel":
                self._excel_gonder(veri)
            elif yol == "/api/fatura_excel":
                self._fatura_excel_gonder(veri)
            elif yol == "/api/yedek_al":
                self._json_yanit({"dosya": os.path.basename(db.yedek_al())})
            elif yol == "/api/geri_yukle":
                dosya = posixpath.basename(veri.get("dosya", ""))
                if not dosya.endswith(".db"):
                    raise ApiHata("Geçersiz yedek dosyası.")
                db.yedekten_geri_yukle(dosya)
                db.init_db()
                self._json_yanit({"tamam": True, "calismalar": db.calismalari_listele()})
            else:
                self._hata("Bulunamadı", 404)
        except ApiHata as exc:
            self._hata(str(exc))
        except (KeyError, ValueError) as exc:
            self._hata(f"Geçersiz istek: {exc}")
        except Exception as exc:  # noqa: BLE001
            self._hata(f"Sunucu hatası: {exc}", 500)

    # --------------------------------------------------------------- yardimci
    def _ayristir(self, veri):
        """Yapistirmayi ayristirir ve sonucu dondurur; hicbir sey saklanmaz.

        Iki bicim taninir ve kendiliginden ayirt edilir:
        - Sistem sorgusu: satirlar beyan kalemleri, sutunlar aylar
        - Ozet tablo: satirlar donemler, sutunlar buyuklukler (Sonuc ve Fark
          sekmesinden veya rapordan kopyalanan, mahkeme kararindan sonra
          degismis olabilecek tablo)
        """
        metin = veri.get("metin") or ""
        if ozet_tablosu_mu(metin):
            try:
                sonuc = ozet_ayristir(metin, veri.get("esleme"))
            except ValueError as exc:
                raise ApiHata(str(exc))
            return {"tur": "ozet", "satirlar": sonuc["satirlar"], "yil": sonuc["yil"],
                    "yillar": sonuc["yillar"], "kolonlar": sonuc["kolonlar"],
                    "tanimsiz": sonuc["tanimsiz"], "uyarilar": sonuc["uyarilar"]}
        try:
            sonuc = beyan_ayristir(metin)
        except ValueError as exc:
            raise ApiHata(str(exc))
        return {"tur": "beyan", "degerler": sonuc["degerler"], "uyarilar": sonuc["uyarilar"],
                "ay_sayisi": sonuc["ay_sayisi"], "kunye": sonuc.get("kunye") or {},
                "dolu_aylar": sonuc.get("dolu_aylar") or []}

    # ------------------------------------------------------- beyanname PDF
    def _pdf_oku(self, veri):
        """Yuklenen PDF'leri okur. Bir dosyadaki hata digerlerini durdurmaz."""
        dosyalar = veri.get("dosyalar") or []
        if not dosyalar:
            raise ApiHata("Okunacak dosya gelmedi.")
        from .pdf_beyanname import PdfHata, beyanname_oku
        okunanlar, hatalar = [], []
        for dosya in dosyalar:
            ad = dosya.get("ad") or "beyanname.pdf"
            try:
                ham = base64.b64decode(dosya.get("veri") or "", validate=True)
            except (binascii.Error, ValueError):
                hatalar.append({"ad": ad, "mesaj": "Dosya içeriği çözülemedi."})
                continue
            if not ham.startswith(b"%PDF"):
                hatalar.append({"ad": ad, "mesaj": "Bu bir PDF dosyası değil."})
                continue
            gecici = os.path.join(CIKTI_DIR, "_yuklenen.pdf")
            try:
                os.makedirs(CIKTI_DIR, exist_ok=True)
                with open(gecici, "wb") as f:
                    f.write(ham)
                okunanlar.append(beyanname_oku(gecici, ad))
            except PdfHata as exc:
                hatalar.append({"ad": ad, "mesaj": str(exc)})
            except Exception as exc:                      # beklenmedik bicim
                hatalar.append({"ad": ad, "mesaj": "Okunamadı: %s" % exc})
            finally:
                try:
                    os.remove(gecici)
                except OSError:
                    pass
        return {"beyannameler": okunanlar, "hatalar": hatalar}

    def _beyanname_ozet(self, veri):
        beyannameler = _beyanname_modulu()
        duzen = beyannameler.duzenle(veri.get("beyannameler") or [])
        yalniz = veri.get("yalniz_degisen")
        yalniz = True if yalniz is None else bool(yalniz)
        return {
            "duzen": duzen,
            "genel_bakis": beyannameler.genel_bakis(duzen),
            "tablolar": {d["anahtar"]: beyannameler.karsilastirma_tablosu(d, yalniz)
                         for d in duzen["donemler"]},
            "secilen": {a: s["sira"] for a, s in
                        beyannameler.secimi_coz(duzen, veri.get("secim")).items()},
            "duzeltme_tablosu": beyannameler.duzeltme_tablosu(duzen),
            "duzeltme_kolonlari": [{"kod": k, "etiket": e}
                                   for k, e in beyannameler.DUZELTME_KOLONLARI],
        }

    def _beyanname_uygula(self, veri):
        beyannameler = _beyanname_modulu()
        duzen = beyannameler.duzenle(veri.get("beyannameler") or [])
        if not duzen["donemler"]:
            raise ApiHata("Önce beyanname PDF'i yükleyin.")
        return beyannameler.beyana_cevir(duzen, veri.get("secim"))

    def _vergi_beyani_oku(self, veri):
        """Yillik Gelir / Kurumlar Vergisi beyannamesinden ozet okur.

        Okunan kalemler dogrudan kunyeye yazilmaz; kullaniciya gosterilir,
        onaylayan kullanici kunyeye aktarir.
        """
        dosyalar = veri.get("dosyalar") or []
        if not dosyalar:
            raise ApiHata("Okunacak dosya gelmedi.")
        from .pdf_beyanname import PdfHata
        from . import vergi_beyannamesi

        dosya = dosyalar[0]
        ad = dosya.get("ad") or "beyanname.pdf"
        try:
            ham = base64.b64decode(dosya.get("veri") or "", validate=True)
        except (binascii.Error, ValueError):
            raise ApiHata("Dosya içeriği çözülemedi.")
        if not ham.startswith(b"%PDF"):
            raise ApiHata("Bu bir PDF dosyası değil.")
        gecici = os.path.join(CIKTI_DIR, "_yuklenen_vergi.pdf")
        try:
            os.makedirs(CIKTI_DIR, exist_ok=True)
            with open(gecici, "wb") as f:
                f.write(ham)
            ozet = vergi_beyannamesi.ozet_oku(gecici, ad)
        except PdfHata as exc:
            raise ApiHata(str(exc))
        except Exception as exc:                              # beklenmedik bicim
            raise ApiHata("Okunamadı: %s" % exc)
        finally:
            try:
                os.remove(gecici)
            except OSError:
                pass
        ozet["metin"] = vergi_beyannamesi.kunye_metnine_cevir(ozet)
        return ozet

    # ---------------------------------------------------------------- fatura
    def _fatura_oku(self, veri):
        """Yuklenen Excel dokumlerini okur. Bir dosyadaki hata digerlerini durdurmaz."""
        dosyalar = veri.get("dosyalar") or []
        if not dosyalar:
            raise ApiHata("Okunacak dosya gelmedi.")
        from .fatura_oku import FaturaHata, dosya_oku
        faturalar = _fatura_modulu()

        okunanlar, hatalar, sayfalar, uyarilar = [], [], [], []
        for dosya in dosyalar:
            ad = dosya.get("ad") or "fatura.xlsx"
            try:
                ham = base64.b64decode(dosya.get("veri") or "", validate=True)
            except (binascii.Error, ValueError):
                hatalar.append({"ad": ad, "mesaj": "Dosya içeriği çözülemedi."})
                continue
            if not ham.startswith(b"PK"):
                hatalar.append({"ad": ad, "mesaj": "Bu bir .xlsx dosyası değil."})
                continue
            gecici = os.path.join(CIKTI_DIR, "_yuklenen_fatura.xlsx")
            try:
                os.makedirs(CIKTI_DIR, exist_ok=True)
                with open(gecici, "wb") as f:
                    f.write(ham)
                sonuc = dosya_oku(gecici, ad)
                okunanlar.extend(sonuc["faturalar"])
                sayfalar.extend({"dosya": ad, **s} for s in sonuc["sayfalar"])
                uyarilar.extend("%s: %s" % (ad, u) for u in sonuc["uyarilar"])
            except FaturaHata as exc:
                hatalar.append({"ad": ad, "mesaj": str(exc)})
            except Exception as exc:                          # beklenmedik bicim
                hatalar.append({"ad": ad, "mesaj": "Okunamadı: %s" % exc})
            finally:
                try:
                    os.remove(gecici)
                except OSError:
                    pass

        # VKN tasimayan dokumlerde (elle hazirlanan fatura listesi) saticiyi
        # kullanici yukleme sirasinda bildirir; yalnizca bos olanlara yazilir.
        satici_vkn = "".join(ch for ch in str(veri.get("satici_vkn") or "")
                             if ch.isdigit())
        if satici_vkn:
            for f in okunanlar:
                if not f.get("duzenleyen_vkn") and not f.get("alici_vkn"):
                    f["duzenleyen_vkn"] = satici_vkn
                    f["alici_vkn"] = "".join(
                        ch for ch in str(veri.get("mukellef_vkn") or "")
                        if ch.isdigit())

        mukellef_vkn = (veri.get("calisma") or {}).get("mukellef", {}).get("vkn_tckn")
        return {"faturalar": faturalar.normalize(okunanlar, mukellef_vkn),
                "hatalar": hatalar, "sayfalar": sayfalar, "uyarilar": uyarilar}

    def _fatura_bloku(self, calisma):
        """Excel'in Faturalar sayfasi icin duzlestirilmis satirlar.

        Satici unvani ve kullanma durumu fatura satirinda tutulmaz; rapordaki
        tabloyla ayni bilgi gorunsun diye satici kaydindan buraya tasinir.
        Fatura okuma modullerindeki bir aksilik Excel ciktisinin geri kalanini
        engellemesin diye cagrisi korumalidir.
        """
        if not calisma.get("faturalar"):
            return None
        try:
            faturalar = _fatura_modulu()
            mukellef_vkn = (calisma.get("mukellef") or {}).get("vkn_tckn")
            liste = faturalar.normalize(calisma.get("faturalar"), mukellef_vkn)
            saticilar = calisma.get("saticilar") or {}
            satirlar = []
            for f in liste:
                if not faturalar.sayilir(f, saticilar):
                    continue
                bilgi = saticilar.get(f.get("satici_vkn") or "") or {}
                yevmiye = " / ".join(
                    p for p in (faturalar.tarih_goster(f.get("yevmiye_tarih")),
                                f.get("yevmiye_no")) if p)
                satirlar.append({
                    "satici_vkn": f.get("satici_vkn") or "",
                    "satici_unvan": bilgi.get("unvan") or "",
                    "kullanma": bilgi.get("kullanma") or "Belirlenmedi",
                    "fatura_no": f.get("fatura_no") or "",
                    "tarih": faturalar.tarih_goster(f.get("tarih")),
                    "kayit_donemi": ("%s/%02d" % (f["kayit_yil"], f["kayit_ay"])
                                     if f.get("kayit_yil") and f.get("kayit_ay") else ""),
                    "matrah": f.get("matrah") or 0.0,
                    "kdv": f.get("kdv") or 0.0,
                    "toplam": f.get("toplam") or 0.0,
                    "mal_cinsi": f.get("mal_cinsi") or "",
                    "yevmiye": yevmiye,
                    "kaynak": f.get("kaynak") or "",
                })
            if not satirlar:
                return None
            satirlar.sort(key=lambda s: (s["satici_vkn"], s["kayit_donemi"],
                                         s["fatura_no"]))
            return {"faturalar": satirlar,
                    "toplam": faturalar.toplamlar(liste, saticilar)}
        except Exception:                                     # noqa: BLE001
            return None

    def _fatura_ozet(self, veri):
        """Calismadaki fatura listesini ozetler; hicbir sey saklanmaz."""
        faturalar = _fatura_modulu()
        calisma = veri.get("calisma") or {}
        mukellef_vkn = (calisma.get("mukellef") or {}).get("vkn_tckn")
        liste = faturalar.normalize(calisma.get("faturalar"), mukellef_vkn)
        saticilar = calisma.get("saticilar") or {}
        yillar = calisma.get("yillar") or []
        return {
            "faturalar": liste,
            "saticilar": faturalar.satici_ozeti(liste, saticilar),
            "toplamlar": faturalar.toplamlar(liste, saticilar),
            "donem_ozeti": {str(y): a
                            for y, a in faturalar.donem_ozeti(liste, saticilar).items()},
            "indirim_dizileri": {
                str(y): d
                for y, d in faturalar.indirim_dizileri(liste, saticilar).items()},
            "uygulama_farki": faturalar.uygulama_farki(liste, yillar, saticilar),
            "bulgular": faturalar.bulgular(liste, yillar, saticilar),
            # Sahte belgelerin toplam indirimler icindeki payi; "bilerek
            # kullanma" degerlendirmesinin dayanagidir, ekranda da gorunsun.
            "oran": faturalar.sahte_belge_orani(liste, _hesapla(calisma)[0],
                                                saticilar),
        }

    # ------------------------------------------------------- belge taslaklari
    def _tutanak_hazirla(self, veri):
        """Tutanak taslagini uretir; hem indirme hem onizleme bunu kullanir."""
        _ik, tutanak = _belge_modulleri()
        calisma = veri.get("calisma") or {}
        sonuc, bulgular = _hesapla(calisma)
        yillar = _yillari_coz(calisma)
        inceleme = _inceleme_bilgisi(calisma)
        # Duzeltme beyannamelerinin genel dokumu tutanaga girmez (raporun III.
        # bolumunde yer alir); ancak faturalari duzeltmeyle cikarilmis satici
        # icin hangi donemde hangi satirdan cikarildigi tutanakta da yazilir.
        belge = tutanak.tutanak_uret(inceleme, calisma.get("kunye"), yillar, sonuc,
                                     bulgular, calisma,
                                     self._duzeltme_karsilastirmalari(calisma))
        return belge, inceleme

    def _rapor_hazirla(self, veri):
        """Sahte belge kullanma raporu taslaklarini uretir.

        Tutanak butun inceleme donemi icin tek duzenlenirken rapor her yil
        icin ayri duzenlenir. Bu yuzden burada (yil, belge) ciftlerinden olusan
        bir liste doner; tek yil incelenmisse listede tek eleman bulunur.
        """
        from . import sahte_belge_raporu
        calisma = veri.get("calisma") or {}
        sonuc, bulgular = _hesapla(calisma)
        yillar = _yillari_coz(calisma)
        inceleme = _inceleme_bilgisi(calisma)
        duzeltme = self._duzeltme_dokumu(calisma)
        karsilastirmalar = self._duzeltme_karsilastirmalari(calisma)
        dokumler = self._beyan_dokumleri(calisma)
        rapor_yillari = sahte_belge_raporu.rapor_yillari(sonuc) or [None]
        belgeler = [
            (y, sahte_belge_raporu.rapor_uret(inceleme, calisma.get("kunye"),
                                              yillar, sonuc, calisma, bulgular,
                                              duzeltme, y, karsilastirmalar,
                                              dokumler))
            for y in rapor_yillari]
        return belgeler, inceleme

    def _beyan_dokumleri(self, calisma):
        """Raporun III. bolumu icin ilk beyan ve son hal dokumleri."""
        if not calisma.get("beyannameler"):
            return None
        try:
            beyannameler = _beyanname_modulu()
            duzen = beyannameler.duzenle(calisma["beyannameler"])
            return {"ilk": beyannameler.surum_dokumu(duzen, "ilk"),
                    "son": beyannameler.surum_dokumu(duzen, "son")}
        except Exception:                                     # noqa: BLE001
            return None

    def _duzeltme_dokumu(self, calisma):
        """Duzeltme beyannameleri tablosu; okunamazsa belge yine uretilir."""
        return self._duzeltmeden_uret(calisma, "duzeltme_tablosu")

    def _duzeltme_karsilastirmalari(self, calisma):
        """Duzeltme donemlerinde satir bazinda oncesi / sonrasi dokumu."""
        return self._duzeltmeden_uret(calisma, "duzeltme_karsilastirmalari")

    def _duzeltmeden_uret(self, calisma, islev):
        """Yuklenen beyannamelerden istenen dokumu uretir.

        Beyanname okumasi belge uretimini engellememeli: dosya bozuksa ya da
        beklenmedik bir bicimdeyse belge, o tablo olmadan yine uretilir.
        """
        if not calisma.get("beyannameler"):
            return None
        try:
            beyannameler = _beyanname_modulu()
            return getattr(beyannameler, islev)(
                beyannameler.duzenle(calisma["beyannameler"]))
        except Exception:                                     # noqa: BLE001
            return None

    def _rapor_onizleme(self, veri):
        ik, _tutanak = _belge_modulleri()
        belgeler, _inceleme = self._rapor_hazirla(veri)
        kunye = ik.normalize((veri.get("calisma") or {}).get("kunye"))
        # Birden cok yil varsa onizleme raporlari alt alta gosterir; hangi
        # yila ait olduklari araya konan ayrac satiriyla belli olur.
        parcalar = []
        for yil, belge in belgeler:
            if yil and len(belgeler) > 1:
                parcalar.append("=" * 30 + (" %s YILI RAPORU " % yil)
                                + "=" * 30 + "\n")
            parcalar.append(belge.duz_metin())
        return {"metin": "\n".join(parcalar),
                "eksikler": ik.eksik_alanlar(kunye)}

    def _rapor_gonder(self, veri):
        from . import sahte_belge_raporu
        belgeler, inceleme = self._rapor_hazirla(veri)
        dosyalar = [(sahte_belge_raporu.dosya_adi(inceleme, yil), belge.bayt())
                    for yil, belge in belgeler]
        self._ciktilara_yaz(dosyalar)
        if len(dosyalar) == 1:
            ad, govde = dosyalar[0]
            self._belge_gonder(govde, ad,
                               "application/vnd.openxmlformats-officedocument."
                               "wordprocessingml.document")
            return
        # Her yilin raporu ayri bir belge; tarayiciya tek dosya inebildigi
        # icin hepsi bir zip icinde gonderilir.
        paket = io.BytesIO()
        with zipfile.ZipFile(paket, "w", zipfile.ZIP_DEFLATED) as z:
            for ad, govde in dosyalar:
                z.writestr(ad, govde)
        self._belge_gonder(paket.getvalue(), sahte_belge_raporu.paket_adi(inceleme),
                           "application/zip")

    def _ciktilara_yaz(self, dosyalar):
        """Uretilen belgelerin birer kopyasini ciktilar klasorune birakir."""
        try:
            os.makedirs(CIKTI_DIR, exist_ok=True)
            for ad, govde in dosyalar:
                with open(os.path.join(CIKTI_DIR, ad), "wb") as f:
                    f.write(govde)
        except OSError:
            pass

    def _tutanak_onizleme(self, veri):
        ik, _tutanak = _belge_modulleri()
        belge, _inceleme = self._tutanak_hazirla(veri)
        kunye = ik.normalize((veri.get("calisma") or {}).get("kunye"))
        return {"metin": belge.duz_metin(), "eksikler": ik.eksik_alanlar(kunye)}

    def _tutanak_gonder(self, veri):
        _ik, tutanak = _belge_modulleri()
        belge, inceleme = self._tutanak_hazirla(veri)
        govde = belge.bayt()
        dosya_adi = tutanak.dosya_adi(inceleme)
        # Excel ciktisinda oldugu gibi bir kopya klasorde de birakilir; evde
        # terminalden calisirken tarayici indirmesine bagli kalinmasin.
        try:
            os.makedirs(CIKTI_DIR, exist_ok=True)
            with open(os.path.join(CIKTI_DIR, dosya_adi), "wb") as f:
                f.write(govde)
        except OSError:
            pass
        self._belge_gonder(govde, dosya_adi,
                           "application/vnd.openxmlformats-officedocument."
                           "wordprocessingml.document")

    def _belge_gonder(self, govde, dosya_adi, icerik_turu):
        self.send_response(200)
        self.send_header("Content-Type", icerik_turu)
        self.send_header("Content-Disposition", _dosya_basligi(dosya_adi))
        self.send_header("Content-Length", str(len(govde)))
        self.end_headers()
        self.wfile.write(govde)

    def _fatura_excel_gonder(self, veri):
        """Ekranda gorunen fatura listesini Excel olarak gonderir.

        Satirlar istemciden gelir: ekranda hangi yil kulakcigi ve satici
        suzgeci acikca o kume yazilir, sutun duzeni de tablonunkiyle ayni olur.
        """
        basliklar = [str(x) for x in (veri.get("basliklar") or [])]
        satirlar = veri.get("satirlar") or []
        if not basliklar or not satirlar:
            raise ApiHata("Listede yazılacak satır yok.")
        guvenli = "".join(c for c in (veri.get("ad") or "fatura listesi")
                          if c.isalnum() or c in " -_").strip() or "fatura listesi"
        dosya_adi = f"Fatura_listesi_{guvenli}.xlsx".replace(" ", "_")
        dosya_yolu = os.path.join(CIKTI_DIR, dosya_adi)
        fatura_listesi_olustur(dosya_yolu, veri.get("baslik") or "FATURA LİSTESİ",
                               basliklar, satirlar, veri.get("sayisal") or [],
                               veri.get("toplanan"))
        with open(dosya_yolu, "rb") as f:
            govde = f.read()
        self.send_response(200)
        self.send_header("Content-Type", "application/vnd.openxmlformats-"
                                         "officedocument.spreadsheetml.sheet")
        self.send_header("Content-Disposition", _dosya_basligi(dosya_adi))
        self.send_header("Content-Length", str(len(govde)))
        self._onbellek_kapali()
        self.end_headers()
        self.wfile.write(govde)

    def _excel_gonder(self, veri):
        calisma = veri.get("calisma") or {}
        sonuc, bulgular = _hesapla(calisma)
        if not sonuc["donemler"]:
            raise ApiHata("Önce beyan bloğunu yapıştırın.")
        inceleme = _inceleme_bilgisi(calisma)
        guvenli = "".join(c for c in (calisma.get("ad") or "kdv")
                          if c.isalnum() or c in " -_").strip() or "kdv"
        dosya_adi = f"KDV_calisma_{guvenli}.xlsx".replace(" ", "_")
        dosya_yolu = os.path.join(CIKTI_DIR, dosya_adi)
        # Duzeltme sayfasi yalnizca beyanname yuklendiyse eklenir; eklenemezse
        # Excel ciktisinin geri kalani yine de uretilir.
        duzeltmeler = None
        if calisma.get("beyannameler"):
            try:
                beyannameler = _beyanname_modulu()
                duzeltmeler = beyannameler.duzeltme_tablosu(
                    beyannameler.duzenle(calisma["beyannameler"]))
            except Exception:
                duzeltmeler = None
        calisma_olustur(dosya_yolu, inceleme, _yillari_coz(calisma), sonuc, bulgular,
                        duzeltmeler, self._fatura_bloku(calisma),
                        _ziya_kati(calisma))
        with open(dosya_yolu, "rb") as f:
            govde = f.read()
        self.send_response(200)
        self.send_header("Content-Type",
                         "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
        self.send_header("Content-Disposition", _dosya_basligi(dosya_adi))
        self.send_header("Content-Length", str(len(govde)))
        self.end_headers()
        self.wfile.write(govde)

    def _onbellek_kapali(self):
        """Tarayici sayfayi saklamasin.

        Uygulama guncellendiginde tarayicinin sakladigi eski arayuz yeni
        sunucuyla birlikte calisirsa sayfa acilir ama bozuk davranir ve
        ekranda hicbir hata gorunmez. Yerel bir uygulamada onbellegin
        kazanci yok.
        """
        self.send_header("Cache-Control", "no-store, no-cache, must-revalidate")
        self.send_header("Pragma", "no-cache")
        self.send_header("Expires", "0")

    def _dosya_gonder(self, dosya_yolu, icerik_turu, onbellek_kapali=True):
        if not os.path.isfile(dosya_yolu):
            self._hata("Dosya bulunamadı", 404)
            return
        with open(dosya_yolu, "rb") as f:
            govde = f.read()
        self.send_response(200)
        self.send_header("Content-Type", icerik_turu)
        self.send_header("Content-Length", str(len(govde)))
        if onbellek_kapali:
            self._onbellek_kapali()
        self.end_headers()
        self.wfile.write(govde)


def sunucu_baslat(port=8766):
    db.init_db()
    return ThreadingHTTPServer(("127.0.0.1", port), Istekci)
