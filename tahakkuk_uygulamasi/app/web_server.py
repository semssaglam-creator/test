"""Yerel web sunucusu: JSON API + tek sayfalik arayuz.

Excel okuma disinda yalnizca Python standart kutuphanesi kullanilir.
Sunucu yalnizca 127.0.0.1'i dinler; Host/Origin kontrolleri tarayici
uzerinden dolayli erisime (DNS rebinding / CSRF) karsidir.
"""
import base64
import json
import os
import urllib.parse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from . import db
from .excel_export import sorgu_excel
from .excel_okuyucu import OkumaHatasi, excel_oku
from .pdf_okuyucu import pdf_oku
from .tarih_util import donem_metni, iso_to_tr

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WEB_DIR = os.path.join(BASE_DIR, "web")


class ApiHata(Exception):
    """Kullaniciya gosterilecek hata mesaji."""


def _tutar_coz(deger):
    if deger in (None, ""):
        return None
    if isinstance(deger, (int, float)):
        return float(deger)
    s = str(deger).strip()
    if not s:
        return None
    if "," in s:
        s = s.replace(".", "").replace(",", ".")
    try:
        return float(s)
    except ValueError:
        raise ApiHata(f"Geçersiz tutar: {deger}")


def _kayitlari_zenginlestir(kayitlar):
    """Her kayda okunabilir donem metni ve vergi kodu adini ekler."""
    adlar = db.vergi_kodu_adlari()
    for k in kayitlar:
        k["vergi_donemi_metin"] = donem_metni(k.get("vergi_donemi", ""))
        k["vergi_kodu_adi"] = adlar.get(k.get("vergi_kodu", ""), "")
    return kayitlar


def _dosya_yukle(veri):
    ad = (veri.get("dosya_adi") or "yukleme.xls").strip()
    icerik_b64 = veri.get("icerik") or ""
    try:
        icerik = base64.b64decode(icerik_b64, validate=True)
    except Exception:  # noqa: BLE001
        raise ApiHata("Dosya içeriği çözülemedi.")
    if not icerik:
        raise ApiHata("Boş dosya gönderildi.")
    # Uzanti veya icerik PDF ise PDF okuyucuya yonlendir.
    pdf_mi = ad.lower().endswith(".pdf") or icerik[:5] == b"%PDF-"
    try:
        kayitlar = pdf_oku(icerik, ad) if pdf_mi else excel_oku(icerik, ad)
    except OkumaHatasi as exc:
        raise ApiHata(str(exc))
    yukleme_id = db.yukleme_ekle(ad, kayitlar)
    ozet = db.yukleme_ozeti(yukleme_id)
    return {"yukleme_id": yukleme_id, "satir_sayisi": len(kayitlar), "ozet": ozet}


def _karsilastir(params):
    a_id = params.get("a", [""])[0]
    b_id = params.get("b", [""])[0]
    if not a_id or not b_id:
        raise ApiHata("Karşılaştırma için iki yükleme seçin.")
    if a_id == b_id:
        raise ApiHata("Lütfen farklı iki yükleme seçin.")
    bazda = params.get("bazda", ["vkn"])[0]
    satirlar = db.karsilastir(int(a_id), int(b_id), bazda)
    say = {"yeni": 0, "cikan": 0, "degisti": 0, "ayni": 0}
    for s in satirlar:
        say[s["durum"]] = say.get(s["durum"], 0) + 1
    return {"bazda": bazda, "satirlar": satirlar, "ozet": say}


def _sorgu_yap(params):
    yukleme_id = params.get("yukleme_id", [""])[0]
    if not yukleme_id:
        yukleme_id = db.son_yukleme_id()
    if not yukleme_id:
        return {"kayitlar": [], "ozet": {"satir": 0, "fis": 0, "mukellef": 0, "toplam": 0}}
    yukleme_id = int(yukleme_id)
    kayitlar = db.kayitlari_sorgula(
        yukleme_id,
        vkn=params.get("vkn", [""])[0],
        vergi_kodu=params.get("vergi_kodu", [""])[0],
        tutar_min=_tutar_coz(params.get("tutar_min", [""])[0]),
        tutar_max=_tutar_coz(params.get("tutar_max", [""])[0]),
        siralama=params.get("siralama", ["fis"])[0],
    )
    _kayitlari_zenginlestir(kayitlar)
    sonuc_toplam = round(sum(k.get("odenecek_tutar") or 0 for k in kayitlar), 2)
    return {
        "yukleme_id": yukleme_id,
        "kayitlar": kayitlar,
        "ozet": db.yukleme_ozeti(yukleme_id),
        "sonuc_satir": len(kayitlar),
        "sonuc_toplam": sonuc_toplam,
    }


class Istekci(BaseHTTPRequestHandler):
    server_version = "TahakkukApp/1.0"

    def log_message(self, format, *args):  # noqa: A002 - sessiz calis
        pass

    def _json_yanit(self, veri, durum=200):
        govde = json.dumps(veri, ensure_ascii=False).encode("utf-8")
        self.send_response(durum)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(govde)))
        self.end_headers()
        self.wfile.write(govde)

    def _hata(self, mesaj, durum=400):
        self._json_yanit({"hata": mesaj}, durum)

    def _govdeyi_oku(self):
        uzunluk = int(self.headers.get("Content-Length", 0))
        if uzunluk == 0:
            return {}
        return json.loads(self.rfile.read(uzunluk).decode("utf-8"))

    def _istek_guvenli_mi(self, yazma=False):
        host = (self.headers.get("Host") or "").split(":")[0].strip("[]").lower()
        if host not in ("127.0.0.1", "localhost", "::1"):
            self._hata("Geçersiz Host başlığı.", 403)
            return False
        if yazma:
            origin = self.headers.get("Origin")
            if origin:
                o = urllib.parse.urlparse(origin)
                if (o.hostname or "").lower() not in ("127.0.0.1", "localhost", "::1"):
                    self._hata("İstek reddedildi (siteler arası).", 403)
                    return False
        return True

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

    def _excel_indir(self, params):
        sonuc = _sorgu_yap(params)
        adlar = db.vergi_kodu_adlari()
        govde = sorgu_excel(sonuc["kayitlar"], adlar)
        dosya_adi = "tahakkuk_sorgu.xlsx"
        self.send_response(200)
        self.send_header("Content-Type",
                         "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
        self.send_header("Content-Disposition",
                         f'attachment; filename="{urllib.parse.quote(dosya_adi)}"')
        self.send_header("Content-Length", str(len(govde)))
        self.end_headers()
        self.wfile.write(govde)

    def do_GET(self):
        if not self._istek_guvenli_mi():
            return
        parsed = urllib.parse.urlparse(self.path)
        yol = parsed.path
        params = urllib.parse.parse_qs(parsed.query)
        try:
            if yol in ("/", "/index.html"):
                self._dosya_gonder(os.path.join(WEB_DIR, "index.html"),
                                   "text/html; charset=utf-8")
            elif yol == "/api/yuklemeler":
                yuklemeler = db.yuklemeleri_listele()
                for y in yuklemeler:
                    y["yukleme_zamani_tr"] = iso_to_tr(y["yukleme_zamani"])
                self._json_yanit(yuklemeler)
            elif yol == "/api/sorgu":
                self._json_yanit(_sorgu_yap(params))
            elif yol == "/api/karsilastir":
                self._json_yanit(_karsilastir(params))
            elif yol == "/api/vergi_kodlari":
                self._json_yanit(db.vergi_kodu_adlari())
            elif yol == "/disa_aktar":
                self._excel_indir(params)
            else:
                self._hata("Bulunamadı", 404)
        except ApiHata as exc:
            self._hata(str(exc))
        except Exception as exc:  # noqa: BLE001
            self._hata(f"Sunucu hatası: {exc}", 500)

    def do_POST(self):
        if not self._istek_guvenli_mi(yazma=True):
            return
        parsed = urllib.parse.urlparse(self.path)
        yol = parsed.path
        try:
            veri = self._govdeyi_oku()
            if yol == "/api/yukle":
                self._json_yanit(_dosya_yukle(veri))
            elif yol == "/api/yukleme/sil":
                db.yukleme_sil(int(veri["id"]))
                self._json_yanit({"tamam": True})
            elif yol == "/api/vergi_kodu":
                kod = (veri.get("kod") or "").strip()
                if not kod:
                    raise ApiHata("Kod boş olamaz.")
                db.vergi_kodu_ad_ekle(kod, (veri.get("ad") or "").strip())
                self._json_yanit({"tamam": True})
            else:
                self._hata("Bulunamadı", 404)
        except ApiHata as exc:
            self._hata(str(exc))
        except (KeyError, ValueError) as exc:
            self._hata(f"Geçersiz istek: {exc}")
        except Exception as exc:  # noqa: BLE001
            self._hata(f"Sunucu hatası: {exc}", 500)


def sunucu_baslat(port=8766):
    db.init_db()
    return ThreadingHTTPServer(("127.0.0.1", port), Istekci)
