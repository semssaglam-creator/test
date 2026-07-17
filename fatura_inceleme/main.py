#!/usr/bin/env python3
"""Fatura Inceleme Uygulamasi - giris noktasi.

PDF faturalari (e-Fatura / e-Arsiv / taranmis) okuyup veritabanina isler;
urun, fatura, tarih, alici/satici bazinda sorgulama ve Excel aktarimi sunar.

Yerel bir web sunucusu baslatir ve varsayilan tarayicida arayuzu acar.
Kurulum gerektirmez; Python 3 ve paketli kutuphaneler (lib/) yeterlidir.
Taranmis faturalar icin istege bagli Tesseract + Poppler kullanilir
(bkz. KULLANIM_KILAVUZU.md).
"""
import os
import sys
import threading
import webbrowser

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(BASE_DIR, "lib"))
sys.path.insert(0, BASE_DIR)

from app.web_server import sunucu_baslat

PORT = 8766


def main():
    try:
        sunucu = sunucu_baslat(PORT)
    except OSError:
        # Port kullaniliyor: uygulama zaten acik olabilir, sadece tarayiciyi ac
        webbrowser.open(f"http://127.0.0.1:{PORT}/")
        print(f"Uygulama zaten calisiyor gorunuyor: http://127.0.0.1:{PORT}/")
        return

    adres = f"http://127.0.0.1:{PORT}/"
    print("Fatura Inceleme Uygulamasi calisiyor:", adres)
    print("Kapatmak icin bu pencerede Ctrl+C yapin.")
    threading.Timer(0.8, lambda: webbrowser.open(adres)).start()
    try:
        sunucu.serve_forever()
    except KeyboardInterrupt:
        print("\nKapatiliyor...")
        sunucu.shutdown()


if __name__ == "__main__":
    main()
