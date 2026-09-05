#!/usr/bin/env python3
"""Uzlasma Takip Uygulamasi - giris noktasi.

Yerel bir web sunucusu baslatir ve varsayilan tarayicida arayuzu acar.
Kurulum gerektirmez; yalnizca Python 3 standart kutuphanesi yeterlidir.
"""
import os
import sys
import threading
import webbrowser

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(BASE_DIR, "lib"))
sys.path.insert(0, BASE_DIR)

from app.web_server import sunucu_baslat

PORT = 8765


def main():
    port = PORT
    sunucu = None
    # Port doluysa (ornegin uygulama zaten acik) sonraki portlari dene
    for aday in range(PORT, PORT + 10):
        try:
            sunucu = sunucu_baslat(aday)
            port = aday
            break
        except OSError:
            continue
    if sunucu is None:
        print("Uygun port bulunamadi (8765-8774 dolu).")
        sys.exit(1)

    adres = f"http://127.0.0.1:{port}/"
    print("Uzlasma Takip Uygulamasi calisiyor:", adres)
    print("Kapatmak icin bu pencerede Ctrl+C tusuna basin.")
    threading.Timer(0.5, lambda: webbrowser.open(adres)).start()
    try:
        sunucu.serve_forever()
    except KeyboardInterrupt:
        print("\nUygulama kapatildi.")


if __name__ == "__main__":
    main()
