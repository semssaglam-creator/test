#!/usr/bin/env python3
"""KDV Inceleme Calismasi - giris noktasi.

Yerel bir web sunucusu baslatir ve varsayilan tarayicida arayuzu acar.
Kurulum gerektirmez; yalnizca Python 3 standart kutuphanesi yeterlidir
(Excel ciktisi icin openpyxl, beyanname PDF'leri icin pypdf lib/ klasorunde
birlikte gelir).

Acilis yolu bilerek sade tutulmustur: sunucu baglanir, adres yazilir,
tarayici acilir. Buraya hicbir on kosul eklenmemelidir. Bir donem, tarayici
acilmadan once sunucuya kendi uzerinden HTTP istegi atan bir "saglik
denetimi" vardi; denetim tutmadiginda uygulama kapaniyor ve ekranda hicbir
sey gorunmuyordu. Denetimler `--tani` altinda durur, normal acilisi
etkilemez.

Sorun giderme: `python3 main.py --tani` (ya da TANI.sh / TANI.bat).
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
KAYIT_YOLU = os.path.join(BASE_DIR, "baslatma_kaydi.txt")


def _kayda_ekle(metin):
    """Baslatma kaydina ekler; yazamamak uygulamayi durdurmaz."""
    try:
        with open(KAYIT_YOLU, "a", encoding="utf-8") as f:
            f.write(metin + "\n")
    except OSError:
        pass


def main():
    if "--tani" in sys.argv:
        from app.tani import raporu_yaz
        return raporu_yaz(PORT, BASE_DIR, KAYIT_YOLU)

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
        print(f"Uygun port bulunamadi ({PORT}-{PORT + 9} dolu).")
        print("Uygulama zaten acik olabilir; acik pencereyi kullanin.")
        _kayda_ekle(f"Uygun port bulunamadi ({PORT}-{PORT + 9} dolu).")
        sys.exit(1)

    adres = f"http://127.0.0.1:{port}/"
    print("KDV Inceleme Calismasi calisiyor:", adres)
    print(f"Acilmazsa sunu da deneyin: http://localhost:{port}/")
    print("Kapatmak icin bu pencerede Ctrl+C tusuna basin.")
    sys.stdout.flush()
    _kayda_ekle(f"Sunucu acildi: {adres} (Python {sys.version.split()[0]}, {BASE_DIR})")

    # daemon: tarayiciyi acan cagri (xdg-open vb.) takilirsa Ctrl+C ile
    # kapanmayi engellemesin
    zamanlayici = threading.Timer(0.5, lambda: webbrowser.open(adres))
    zamanlayici.daemon = True
    zamanlayici.start()
    try:
        sunucu.serve_forever()
    except KeyboardInterrupt:
        print("\nKapatiliyor...")
        sunucu.shutdown()


if __name__ == "__main__":
    main()
