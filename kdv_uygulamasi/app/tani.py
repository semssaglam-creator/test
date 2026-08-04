"""Sorun giderme raporu.

Ayri bir modulde durur ve yalnizca `main.py --tani` ile calisir. Normal
acilis yoluna hicbir sekilde karismaz: buradaki denetimlerden biri
basarisiz olsa bile uygulamanin acilisi etkilenmez.
"""
import os
import socket
import sys


def _yaz(satirlar, metin=""):
    satirlar.append(metin)
    try:
        print(metin)
        sys.stdout.flush()
    except Exception:
        pass


def _erisim(port, konak):
    import urllib.error
    import urllib.request

    adres = "http://%s:%d/api/tanimlar" % (konak, port)
    # Vekil sunucu ayarlari devre disi: yerel adrese vekilden gitmek zaten
    # aradigimiz arizanin kendisi olabilir
    acici = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    try:
        with acici.open(adres, timeout=4) as yanit:
            if yanit.status == 200 and yanit.read(16):
                return "ULASILDI"
            return "beklenmedik yanit (%s)" % yanit.status
    except urllib.error.URLError as exc:
        return "ULASILAMADI (%s)" % getattr(exc, "reason", exc)
    except Exception as exc:
        return "ULASILAMADI (%s: %s)" % (type(exc).__name__, exc)


def raporu_yaz(port_basi, base_dir, kayit_yolu):
    satirlar = []
    yaz = lambda m="": _yaz(satirlar, m)                            # noqa: E731

    yaz("KDV Inceleme Calismasi - TANI RAPORU")
    yaz("=" * 52)
    yaz()
    yaz("--- ortam ---")
    try:
        from .surum import SURUM
    except Exception:
        SURUM = "?"
    yaz("Surum       : %s" % SURUM)
    yaz("Python      : %s (%s)" % (sys.version.split()[0], sys.executable))
    yaz("Isletim sis.: %s / %s" % (sys.platform, os.name))
    yaz("Klasor      : %s" % base_dir)
    for ad in ("web/index.html", "app/web_server.py", "lib/openpyxl", "lib/pypdf"):
        yol = os.path.join(base_dir, *ad.split("/"))
        yaz("  %-18s %s" % (ad, "var" if os.path.exists(yol) else "YOK"))

    yaz()
    yaz("--- moduller ---")
    for ad in ("sqlite3", "json", "http.server", "webbrowser"):
        try:
            __import__(ad)
            yaz("  %-18s tamam" % ad)
        except Exception as exc:
            yaz("  %-18s HATA: %s" % (ad, exc))
    try:
        import openpyxl
        yaz("  %-18s tamam (%s)" % ("openpyxl", openpyxl.__version__))
    except Exception as exc:
        yaz("  %-18s HATA: %s  (Excel ciktisi calismaz)" % ("openpyxl", exc))
    try:
        from .pdf_beyanname import _kripto_saglayicisini_ele
        _kripto_saglayicisini_ele()
        import pypdf
        yaz("  %-18s tamam (%s)" % ("pypdf", pypdf.__version__))
    except Exception as exc:
        yaz("  %-18s HATA: %s  (beyanname PDF okunamaz)" % ("pypdf", exc))

    yaz()
    yaz("--- ag ---")
    try:
        cozum = sorted({a[4][0] for a in socket.getaddrinfo("localhost", None)})
        yaz("  localhost -> %s" % ", ".join(cozum))
    except Exception as exc:
        yaz("  localhost cozulemedi: %s" % exc)
    for vekil in ("HTTP_PROXY", "http_proxy", "ALL_PROXY", "NO_PROXY", "no_proxy"):
        if os.environ.get(vekil):
            yaz("  %s = %s" % (vekil, os.environ[vekil]))

    yaz()
    yaz("--- sunucu ---")
    import threading

    from .web_server import sunucu_baslat

    sunucu = port = None
    for aday in range(port_basi, port_basi + 10):
        try:
            sunucu = sunucu_baslat(aday)
            port = aday
            break
        except OSError:
            yaz("  port %d dolu" % aday)
    if sunucu is None:
        yaz("  HICBIR PORT ACILAMADI")
    else:
        threading.Thread(target=sunucu.serve_forever, daemon=True).start()
        yaz("  dinlenen: 127.0.0.1 : %d" % port)
        for konak in ("127.0.0.1", "localhost"):
            yaz("  http://%s:%d/  ->  %s" % (konak, port, _erisim(port, konak)))
        sunucu.shutdown()

    yaz()
    yaz("Rapor dosyasi: %s" % kayit_yolu)
    try:
        with open(kayit_yolu, "a", encoding="utf-8") as f:
            f.write("\n" + "\n".join(satirlar) + "\n")
    except OSError:
        pass
    return 0
