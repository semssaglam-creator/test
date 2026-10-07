#!/usr/bin/env python3
"""Takip PDF -> Excel: giriş noktası.

Yerel bir web sunucusu başlatır ve tarayıcıda arayüzü açar. Kurulum gerekmez;
Python 3 standart kütüphanesi + lib/ altındaki saf Python paketleri yeterlidir.
"""
import errno
import json
import os
import sys
import threading
import time
import urllib.request
import webbrowser

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(BASE_DIR, "lib"))
# Ortak modüller SONA: sistemde kurulu sürümü gölgelemesin (bkz. GELISTIRME_NOTLARI).
sys.path.append(os.path.join(BASE_DIR, "lib_ek"))
sys.path.insert(0, BASE_DIR)

from app.sunucu import UYGULAMA, bosta_kapat, sunucu_baslat  # noqa: E402

ILK_PORT = 8790


def zaten_acik(port):
    try:
        with urllib.request.urlopen("http://127.0.0.1:{}/api/kimlik".format(port), timeout=1) as y:
            return json.loads(y.read().decode("utf-8")).get("uygulama") == UYGULAMA
    except Exception:
        return False


def tarayici_ac(adres):
    if not webbrowser.open(adres):
        print("Tarayıcı açılamadı. Adresi tarayıcıya elle yazın:", adres)


def main():
    print(time.strftime("%Y-%m-%d %H:%M:%S"), "başlatılıyor, Python", sys.version.split()[0])
    sunucu = None
    for port in range(ILK_PORT, ILK_PORT + 10):
        if zaten_acik(port):
            adres = "http://127.0.0.1:{}/".format(port)
            print("Uygulama zaten açık; tarayıcıda gösteriliyor:", adres)
            tarayici_ac(adres)
            return
        try:
            sunucu = sunucu_baslat(port)
            break
        except OSError as e:
            if e.errno != errno.EADDRINUSE:
                raise
    if sunucu is None:
        print("Uygun port bulunamadı ({}-{} dolu).".format(ILK_PORT, ILK_PORT + 9))
        sys.exit(1)

    adres = "http://127.0.0.1:{}/".format(sunucu.server_address[1])
    print("Takip PDF -> Excel çalışıyor:", adres)
    print("Kapatmak için tarayıcı sekmesini kapatın (15 dk sonra kendiliğinden kapanır) "
          "ya da bu pencerede Ctrl+C.")
    bosta_kapat(sunucu)
    threading.Timer(0.5, tarayici_ac, args=(adres,)).start()
    try:
        sunucu.serve_forever()
    except KeyboardInterrupt:
        print("\nUygulama kapatıldı.")


if __name__ == "__main__":
    main()
