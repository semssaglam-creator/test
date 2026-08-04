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
import json
import os
import posixpath
import urllib.parse
from datetime import datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from . import db, hesap
from .excel_export import calisma_olustur
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


def _hesapla(calisma):
    """Calismayi hesaplar; veritabanina dokunmaz."""
    yillar = _yillari_coz(calisma)
    if not yillar:
        return {"donemler": [], "yil_toplamlari": [], "genel_toplam": {},
                "tarhiyat_toplami": {}, "yil_uyumu": [],
                "kaynak_analizi": {"kaynaklar": [], "donemler": [], "etkilesim_var": False}}, []
    # Baslangic devri artik yil bazinda tutulur; _yillari_coz eski kayitlardaki
    # calisma duzeyindeki degeri ilk yila tasidi.
    sonuc = hesap.seri_hesapla(yillar)
    sonuc["kaynak_analizi"] = hesap.kaynak_analizi(yillar)
    return sonuc, hesap.beyan_tutarlilik_kontrol(yillar)


def _inceleme_bilgisi(calisma):
    """Excel ve rapor basliklarinda kullanilan mukellef bilgisi."""
    mukellef = calisma.get("mukellef") or {}
    return {
        "ad": calisma.get("ad") or "Çalışma",
        "ad_unvan": mukellef.get("ad_unvan") or db.ADSIZ_MUKELLEF,
        "vkn_tckn": mukellef.get("vkn_tckn") or "",
        "vergi_dairesi": mukellef.get("vergi_dairesi") or "",
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
            elif yol == "/api/excel":
                self._excel_gonder(veri)
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
                        duzeltmeler)
        with open(dosya_yolu, "rb") as f:
            govde = f.read()
        self.send_response(200)
        self.send_header("Content-Type",
                         "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
        self.send_header("Content-Disposition",
                         f'attachment; filename="{urllib.parse.quote(dosya_adi)}"')
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
