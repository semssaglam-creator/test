"""Yerel web sunucusu: JSON API + tek sayfalik arayuz.

Yalnizca Python standart kutuphanesi kullanilir (http.server, json).
Sunucu 127.0.0.1 adresine baglanir; disaridan erisime acilmaz.
"""
import json
import os
import posixpath
import urllib.parse
from datetime import datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from . import db, hesap
from .excel_export import calisma_olustur
from .paste_parser import beyan_ayristir, tek_satir_ayristir, tutar_coz
from .rapor_metni import matrah_farki_ozeti
from .satirlar import (AYLAR, AYRISTIRMA_BLOKLARI, BEYAN_SATIRLARI, ELESTIRI_ALANLARI,
                       OZET_KOLONLARI, TARHIYAT_KOLONLARI, VERI_KODLARI)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WEB_DIR = os.path.join(BASE_DIR, "web")
CIKTI_DIR = os.path.join(BASE_DIR, "ciktilar")


class ApiHata(Exception):
    """Kullaniciya gosterilecek hata mesaji."""


def _inceleme_sonucu(inceleme_id):
    """Bir incelemenin verisini okur, hesaplar ve bulgulariyla birlikte dondurur."""
    veri = db.inceleme_verisi(inceleme_id)
    yillar = veri["yillar"]
    if not yillar:
        return veri, {"donemler": [], "yil_toplamlari": [], "genel_toplam": {}}, []
    baslangic = veri["inceleme"].get("devreden_baslangic")
    sonuc = hesap.seri_hesapla(yillar, devreden_baslangic=baslangic)
    sonuc["kaynak_analizi"] = hesap.kaynak_analizi(yillar, devreden_baslangic=baslangic)
    bulgular = hesap.beyan_tutarlilik_kontrol(yillar)
    return veri, sonuc, bulgular


def _yil_dogrula(inceleme_id, yil_id):
    """yil_id'nin gercekten bu incelemeye ait oldugunu dogrular."""
    veri = db.inceleme_verisi(inceleme_id)
    for y in veri["yillar"]:
        if y["yil_id"] == yil_id:
            return y
    raise ApiHata("Yıl kaydı bu incelemeye ait değil.")


class Istekci(BaseHTTPRequestHandler):
    server_version = "KDVIncelemeSunucu/1.0"

    def log_message(self, bicim, *args):  # sunucu gunlugunu sessizlestir
        pass

    # ------------------------------------------------------------------ yanit
    def _json_yanit(self, veri, kod=200):
        govde = json.dumps(veri, ensure_ascii=False).encode("utf-8")
        self.send_response(kod)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(govde)))
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
            elif yol == "/api/tanimlar":
                self._json_yanit({
                    "satirlar": [{"kod": k, "etiket": e, "baslik": b}
                                 for k, e, b in BEYAN_SATIRLARI],
                    "aylar": AYLAR,
                    "elestiri_alanlari": [{"kod": k, "etiket": e} for k, e in ELESTIRI_ALANLARI],
                    "ozet_kolonlari": [{"kod": k, "etiket": e} for k, e in OZET_KOLONLARI],
                    "tarhiyat_kolonlari": [{"grup": g, "kod": k, "etiket": e, "vurgu": v}
                                           for g, k, e, v in TARHIYAT_KOLONLARI],
                    "ayristirma_bloklari": [{"kod": k, "etiket": e, "aciklama": a}
                                            for k, e, a in AYRISTIRMA_BLOKLARI],
                })
            elif yol == "/api/mukellefler":
                self._json_yanit({"mukellefler": db.mukellefleri_listele()})
            elif yol == "/api/incelemeler":
                mid = params.get("mukellef_id", [None])[0]
                self._json_yanit({"incelemeler": db.incelemeleri_listele(
                    int(mid) if mid else None)})
            elif yol == "/api/inceleme":
                inceleme_id = int(params.get("id", [""])[0])
                veri, sonuc, bulgular = _inceleme_sonucu(inceleme_id)
                self._json_yanit({"inceleme": veri["inceleme"], "yillar": veri["yillar"],
                                  "sonuc": sonuc, "bulgular": bulgular})
            elif yol == "/api/rapor_metni":
                inceleme_id = int(params.get("id", [""])[0])
                veri, sonuc, bulgular = _inceleme_sonucu(inceleme_id)
                if not sonuc["donemler"]:
                    raise ApiHata("İncelemeye önce bir yıl ekleyin.")
                self._json_yanit({"metin": matrah_farki_ozeti(
                    veri["inceleme"], sonuc, bulgular)})
            elif yol == "/api/excel":
                self._excel_indir(params)
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
            if yol == "/api/calisma_hazirla":
                # Kullanici mukellef/dosya/yil tanimlamadan calisabilsin diye
                # varsa son dosyayi, yoksa yeni bir calismayi dondurur.
                self._json_yanit({"inceleme_id": db.varsayilan_calisma()})
            elif yol == "/api/mukellef":
                # Ad bos birakilabilir; yer tutucu adla olusturulur
                ad = (veri.get("ad_unvan") or "").strip() or db.ADSIZ_MUKELLEF
                yeni = db.mukellef_ekle(ad, veri.get("vkn_tckn"), veri.get("adres"))
                self._json_yanit({"id": yeni})
            elif yol == "/api/mukellef/guncelle":
                db.mukellef_guncelle(int(veri["id"]), veri.get("ad_unvan"),
                                     veri.get("vkn_tckn"), veri.get("adres"))
                self._json_yanit({"tamam": True})
            elif yol == "/api/mukellef/sil":
                try:
                    db.mukellef_sil(int(veri["id"]))
                except ValueError as exc:
                    raise ApiHata(str(exc))
                self._json_yanit({"tamam": True})
            elif yol == "/api/inceleme":
                # Mukellef secilmemisse yer tutucu mukellef, ad bossa
                # varsayilan dosya adi kullanilir
                mukellef_id = veri.get("mukellef_id")
                if not mukellef_id:
                    mukellef_id = db.mukellef_ekle(db.ADSIZ_MUKELLEF)
                ad = (veri.get("ad") or "").strip() or "Çalışma"
                yeni = db.inceleme_ekle(int(mukellef_id), ad, veri.get("notlar"))
                self._json_yanit({"id": yeni})
            elif yol == "/api/inceleme/guncelle":
                devreden = veri.get("devreden_baslangic")
                db.inceleme_guncelle(
                    int(veri["id"]), veri.get("ad"), veri.get("notlar"),
                    tutar_coz(devreden) if devreden not in (None, "") else None)
                self._json_yanit({"tamam": True})
            elif yol == "/api/inceleme/sil":
                db.inceleme_sil(int(veri["id"]))
                self._json_yanit({"tamam": True})
            elif yol == "/api/yil":
                yil = int(veri["yil"])
                if not 2000 <= yil <= 2100:
                    raise ApiHata("Yıl 2000-2100 aralığında olmalıdır.")
                yil_id = db.yil_ekle(int(veri["inceleme_id"]), yil,
                                     int(veri.get("ay_sayisi") or 12))
                self._json_yanit({"yil_id": yil_id})
            elif yol == "/api/yil/sil":
                _yil_dogrula(int(veri["inceleme_id"]), int(veri["yil_id"]))
                db.yil_sil(int(veri["yil_id"]))
                self._json_yanit({"tamam": True})
            elif yol == "/api/yil/guncelle":
                _yil_dogrula(int(veri["inceleme_id"]), int(veri["yil_id"]))
                try:
                    db.yil_guncelle(int(veri["yil_id"]), veri["yil"])
                except ValueError as exc:
                    raise ApiHata(str(exc))
                self._json_yanit({"tamam": True})
            elif yol == "/api/yil/ay_sayisi":
                _yil_dogrula(int(veri["inceleme_id"]), int(veri["yil_id"]))
                db.ay_sayisi_ayarla(int(veri["yil_id"]), int(veri["ay_sayisi"]))
                self._json_yanit({"tamam": True})
            elif yol == "/api/beyan/yapistir":
                self._json_yanit(self._beyan_yapistir(veri))
            elif yol == "/api/beyan/satir_yapistir":
                self._json_yanit(self._satir_yapistir(veri))
            elif yol == "/api/beyan/hucre":
                _yil_dogrula(int(veri["inceleme_id"]), int(veri["yil_id"]))
                try:
                    db.beyan_hucre_guncelle(int(veri["yil_id"]), veri["satir_kodu"],
                                            int(veri["ay"]), tutar_coz(veri.get("deger")) or 0.0)
                except ValueError as exc:
                    raise ApiHata(str(exc))
                self._json_yanit({"tamam": True})
            elif yol == "/api/elestiri":
                self._json_yanit(self._elestiri_kaydet(veri))
            elif yol == "/api/yedek_al":
                hedef = db.yedek_al()
                self._json_yanit({"dosya": os.path.basename(hedef)})
            elif yol == "/api/geri_yukle":
                dosya = posixpath.basename(veri.get("dosya", ""))
                if not dosya.endswith(".db"):
                    raise ApiHata("Geçersiz yedek dosyası.")
                db.yedekten_geri_yukle(dosya)
                self._json_yanit({"tamam": True})
            else:
                self._hata("Bulunamadı", 404)
        except ApiHata as exc:
            self._hata(str(exc))
        except (KeyError, ValueError) as exc:
            self._hata(f"Geçersiz istek: {exc}")
        except Exception as exc:  # noqa: BLE001
            self._hata(f"Sunucu hatası: {exc}", 500)

    # -------------------------------------------------------------- yardimci
    def _beyan_yapistir(self, veri):
        # Yil belirtilmemisse akisi kesmek yerine varsayilan bir yil olustur
        inceleme_id = int(veri["inceleme_id"])
        yil_id = veri.get("yil_id")
        if not yil_id:
            mevcut = db.inceleme_verisi(inceleme_id)["yillar"]
            yil_id = (mevcut[0]["yil_id"] if mevcut
                      else db.yil_ekle(inceleme_id, datetime.now().year - 1))
            veri["yil_id"] = yil_id
        _yil_dogrula(inceleme_id, int(yil_id))
        metin = veri.get("metin") or ""
        try:
            sonuc = beyan_ayristir(metin)
        except ValueError as exc:
            raise ApiHata(str(exc))
        db.beyan_kaydet(int(veri["yil_id"]), sonuc["degerler"])
        if veri.get("ay_sayisi_guncelle"):
            db.ay_sayisi_ayarla(int(veri["yil_id"]), sonuc["ay_sayisi"])
        return {"tamam": True, "uyarilar": sonuc["uyarilar"], "ay_sayisi": sonuc["ay_sayisi"]}

    def _satir_yapistir(self, veri):
        _yil_dogrula(int(veri["inceleme_id"]), int(veri["yil_id"]))
        kod = veri.get("satir_kodu")
        if kod not in VERI_KODLARI:
            raise ApiHata("Geçersiz satır seçimi.")
        try:
            degerler = tek_satir_ayristir(veri.get("metin") or "")
        except ValueError as exc:
            raise ApiHata(str(exc))
        db.beyan_satir_guncelle(int(veri["yil_id"]), kod, degerler)
        return {"tamam": True, "degerler": degerler}

    def _elestiri_kaydet(self, veri):
        _yil_dogrula(int(veri["inceleme_id"]), int(veri["yil_id"]))
        alanlar = veri.get("alanlar") or {}
        temiz = {}
        for alan, dizi in alanlar.items():
            if alan == "hesaplanan_otomatik":
                temiz[alan] = [bool(d) for d in dizi]
            elif alan == "kdv_orani":
                temiz[alan] = [None if d in (None, "") else tutar_coz(d) for d in dizi]
            else:
                temiz[alan] = [tutar_coz(d) or 0.0 for d in dizi]
        db.elestiri_kaydet(int(veri["yil_id"]), temiz)
        return {"tamam": True}

    def _excel_indir(self, params):
        inceleme_id = int(params.get("id", [""])[0])
        veri, sonuc, bulgular = _inceleme_sonucu(inceleme_id)
        if not sonuc["donemler"]:
            raise ApiHata("İncelemeye önce bir yıl ekleyin.")
        inceleme = veri["inceleme"]
        guvenli_ad = "".join(c for c in (inceleme.get("ad") or "kdv")
                             if c.isalnum() or c in " -_").strip() or "kdv"
        dosya_adi = f"KDV_calisma_{guvenli_ad}.xlsx".replace(" ", "_")
        dosya_yolu = os.path.join(CIKTI_DIR, dosya_adi)
        calisma_olustur(dosya_yolu, inceleme, veri["yillar"], sonuc, bulgular)
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

    def _dosya_gonder(self, dosya_yolu, icerik_turu):
        if not os.path.isfile(dosya_yolu):
            self._hata("Dosya bulunamadı", 404)
            return
        with open(dosya_yolu, "rb") as f:
            govde = f.read()
        self.send_response(200)
        self.send_header("Content-Type", icerik_turu)
        self.send_header("Content-Length", str(len(govde)))
        self.end_headers()
        self.wfile.write(govde)


def sunucu_baslat(port=8766):
    db.init_db()
    return ThreadingHTTPServer(("127.0.0.1", port), Istekci)
