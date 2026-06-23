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
    # Uygulama zaten acik mi? 8766 doluysa ikinci bir sunucu BASLATMA (ayni veri
    # tabanina iki yazar -> "database is locked"). Var olan ornegi tarayicida ac.
    adres = f"http://127.0.0.1:{PORT}/"
    try:
        sunucu = sunucu_baslat(PORT)
    except OSError:
        print("Uygulama zaten calisiyor; tarayicida aciliyor:", adres)
        webbrowser.open(adres)
        return

    print("Toplu Tahakkuk Sorgulama Uygulamasi calisiyor:", adres)
    print("Kapatmak icin bu pencerede Ctrl+C tusuna basin.")
    threading.Timer(0.5, lambda: webbrowser.open(adres)).start()
    try:
        sunucu.serve_forever()
    except KeyboardInterrupt:
        print("\nUygulama kapatildi.")


if __name__ == "__main__":
    main()
