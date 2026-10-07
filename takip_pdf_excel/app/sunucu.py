"""Yerel HTTP sunucusu (yalnızca 127.0.0.1). Durumsuz: veri tarayıcıda tutulur.

Uçlar:
  GET  /                -> web/index.html
  GET  /api/kimlik      -> uygulama adı (zaten açık mı denetimi için)
  POST /api/nabiz       -> sayfa açık sinyali (sayfa kapanınca sunucu kendini kapatır)
  POST /api/ayristir    -> gövde: PDF baytları  => JSON kayıtlar
  POST /api/excel       -> gövde: JSON kayıtlar => .xlsx baytları
"""
import json
import os
import threading
import time
import traceback
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from .ayristirici import COLUMNS, pdf_ayristir
from .excel import excel_olustur
from .pdf_kelime import PdfHata

UYGULAMA = "takip-pdf-excel"
WEB_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "web")
AZAMI_BOYUT = 100 * 1024 * 1024
BOSTA_KAPANMA_SN = 15 * 60

son_nabiz = [time.time()]


class Isleyici(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):  # her isteği kayda yazma
        pass

    def _gonder(self, kod, govde, tur, ek_basliklar=None):
        self.send_response(kod)
        self.send_header("Content-Type", tur)
        self.send_header("Content-Length", str(len(govde)))
        self.send_header("Cache-Control", "no-store")
        for k, v in (ek_basliklar or {}).items():
            self.send_header(k, v)
        self.end_headers()
        self.wfile.write(govde)

    def _json(self, kod, nesne):
        self._gonder(kod, json.dumps(nesne, ensure_ascii=False).encode("utf-8"),
                     "application/json; charset=utf-8")

    def _govde(self):
        n = int(self.headers.get("Content-Length") or 0)
        if n > AZAMI_BOYUT:
            raise PdfHata("Dosya çok büyük.")
        return self.rfile.read(n)

    def do_GET(self):
        if self.path in ("/", "/index.html"):
            with open(os.path.join(WEB_DIR, "index.html"), "rb") as f:
                self._gonder(200, f.read(), "text/html; charset=utf-8")
        elif self.path == "/api/kimlik":
            self._json(200, {"uygulama": UYGULAMA})
        else:
            self._json(404, {"hata": "Bulunamadı"})

    def do_POST(self):
        son_nabiz[0] = time.time()
        try:
            if self.path == "/api/nabiz":
                self._govde()
                self._json(200, {"tamam": True})
            elif self.path == "/api/ayristir":
                kayitlar = pdf_ayristir(self._govde())
                self._json(200, {"sutunlar": COLUMNS, "kayitlar": kayitlar})
            elif self.path == "/api/excel":
                veri = json.loads(self._govde().decode("utf-8"))
                xlsx = excel_olustur(veri["kayitlar"])
                self._gonder(200, xlsx,
                             "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
            else:
                self._json(404, {"hata": "Bulunamadı"})
        except PdfHata as e:
            self._json(400, {"hata": str(e)})
        except Exception as e:
            traceback.print_exc()
            self._json(500, {"hata": "Beklenmeyen hata: {}: {}".format(type(e).__name__, e)})


def sunucu_baslat(port):
    return ThreadingHTTPServer(("127.0.0.1", port), Isleyici)


def bosta_kapat(sunucu):
    """Sayfa kapandıktan sonra arka planda sonsuza dek çalışmasın."""
    def izle():
        while True:
            time.sleep(30)
            if time.time() - son_nabiz[0] > BOSTA_KAPANMA_SN:
                print("Sayfa {} dakikadır açık değil; uygulama kapanıyor.".format(BOSTA_KAPANMA_SN // 60))
                sunucu.shutdown()
                return
    threading.Thread(target=izle, daemon=True).start()
