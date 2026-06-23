#!/usr/bin/env python3
"""Toplu Tahakkuk Sorgulama Uygulamasi - giris noktasi.

Yerel bir web sunucusu baslatir ve varsayilan tarayicida arayuzu acar.
Kurulum gerektirmez; Excel okuma kutuphaneleri 'lib/' icinde gomulu gelir.
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
    port = PORT
    sunucu = None
    # Port doluysa (uygulama zaten acik olabilir) sonraki portlari dene.
    for aday in range(PORT, PORT + 10):
        try:
            sunucu = sunucu_baslat(aday)
            port = aday
            break
        except OSError:
            continue
    if sunucu is None:
        print("Uygun port bulunamadi (8766-8775 dolu).")
        sys.exit(1)

    adres = f"http://127.0.0.1:{port}/"
    print("Toplu Tahakkuk Sorgulama Uygulamasi calisiyor:", adres)
    print("Kapatmak icin bu pencerede Ctrl+C tusuna basin.")
    threading.Timer(0.5, lambda: webbrowser.open(adres)).start()
    try:
        sunucu.serve_forever()
    except KeyboardInterrupt:
        print("\nUygulama kapatildi.")


if __name__ == "__main__":
    main()
