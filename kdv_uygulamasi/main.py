#!/usr/bin/env python3
"""KDV Inceleme Calismasi - giris noktasi.

Yerel bir web sunucusu baslatir ve varsayilan tarayicida arayuzu acar.
Kurulum gerektirmez; yalnizca Python 3 standart kutuphanesi yeterlidir
(Excel ciktisi icin gereken openpyxl lib/ klasorunde birlikte gelir).
"""
import os
import sys
import threading
import traceback
import webbrowser
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(BASE_DIR, "lib"))
sys.path.insert(0, BASE_DIR)

PORT = 8766
HATA_DOSYASI = "KDV HATA - BUNU GONDERIN.txt"


def _hatayi_yaz(metin):
    """Acilis basarisiz olursa gerekceyi okunabilir bir dosyaya birakir.

    Uygulama masaustu kisayolundan acildiginda ekrana yazilanlar hicbir yere
    gitmez; bir hata olursa ekranda hicbir sey olmaz ve uygulama "hic
    acilmiyor" gorunur. Terminal kullanilamayan bilgisayarlarda gerekceyi
    ogrenmenin baska yolu kalmadigi icin metin bir dosyaya yazilir; kullanici
    dosyaya cift tiklayip icerigini okuyabilir.

    Yalnizca HATA halinde calisir. Dosya yazilamazsa sessizce vazgecilir:
    burasi hicbir kosulda acilisi engellememelidir.
    """
    ortam = [
        "KDV Inceleme Calismasi - acilis hatasi",
        "Zaman   : %s" % datetime.now().strftime("%d.%m.%Y %H:%M:%S"),
        "Python  : %s" % sys.version.replace("\n", " "),
        "Yorumcu : %s" % sys.executable,
        "Klasor  : %s" % BASE_DIR,
        "Sistem  : %s" % sys.platform,
        "",
        metin,
    ]
    icerik = "\n".join(ortam)
    for klasor in (BASE_DIR, os.path.expanduser("~")):
        try:
            yol = os.path.join(klasor, HATA_DOSYASI)
            with open(yol, "w", encoding="utf-8") as f:
                f.write(icerik)
            return yol
        except OSError:
            continue
    return None


# Uygulama modulleri burada yuklenir. Yukleme aninda olusan bir hata
# ("hic acilmiyor" durumlarinin en sik sebebi) da gerekcesiyle kayda gecsin
# diye import da sarmalanmistir; hata yine yukari firlatilir.
try:
    from app.web_server import sunucu_baslat
except BaseException:
    _hatayi_yaz(traceback.format_exc())
    raise


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
        print(f"Uygun port bulunamadi ({PORT}-{PORT + 9} dolu).")
        sys.exit(1)

    adres = f"http://127.0.0.1:{port}/"
    print("KDV Inceleme Calismasi calisiyor:", adres)
    print("Kapatmak icin bu pencerede Ctrl+C tusuna basin.")
    threading.Timer(0.5, lambda: webbrowser.open(adres)).start()
    try:
        sunucu.serve_forever()
    except KeyboardInterrupt:
        print("\nKapatiliyor...")
        sunucu.shutdown()


if __name__ == "__main__":
    # Acilis yolu degismedi; yalnizca cokme halinde gerekce kayda gecer.
    try:
        main()
    except (KeyboardInterrupt, SystemExit):
        raise
    except BaseException:
        yazilan = _hatayi_yaz(traceback.format_exc())
        if yazilan:
            print("Acilis basarisiz. Gerekce su dosyaya yazildi:\n  %s" % yazilan)
        raise
