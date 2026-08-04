#!/usr/bin/env python3
"""KDV Inceleme Calismasi - giris noktasi.

Yerel bir web sunucusu baslatir ve varsayilan tarayicida arayuzu acar.
Kurulum gerektirmez; yalnizca Python 3 standart kutuphanesi yeterlidir
(Excel ciktisi icin openpyxl, beyanname PDF'leri icin pypdf lib/
klasorunde birlikte gelir).

Sunucu hem 127.0.0.1 (IPv4) hem de mumkunse ::1 (IPv6) uzerinde dinler.
Boylece tarayici "localhost" adresini hangisine cozerse cozsun ulasir. Bu
onemlidir: kurum bilgisayarlarindaki vekil sunucu (proxy) ayarlari cogu kez
"nokta icermeyen adresler icin vekil kullanma" seklindedir; bu durumda
http://localhost:8766/ dogrudan gider ama http://127.0.0.1:8766/ vekile
yonlendirilip "sayfaya ulasilamiyor" hatasi verir.

Sorun giderme: `python main.py --tani` calistirin. Ekrana ve
baslatma_kaydi.txt dosyasina ayrintili bir rapor yazar.
"""
import os
import socket
import sys
import threading
import time
import traceback
import webbrowser

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(BASE_DIR, "lib"))
sys.path.insert(0, BASE_DIR)

PORT = 8766
KAYIT_YOLU = os.path.join(BASE_DIR, "baslatma_kaydi.txt")
_kayit_satirlari = []


def yaz(metin=""):
    """Ekrana ve baslatma kaydina birlikte yazar."""
    _kayit_satirlari.append(metin)
    # Masaustu kisayolundan acildiginda (Terminal=false) stdout kapali
    # olabilir; yazamamak uygulamayi durdurmamali
    try:
        print(metin)
        sys.stdout.flush()
    except Exception:
        try:
            print(metin.encode("ascii", "replace").decode("ascii"))
        except Exception:
            pass


def kaydi_yaz():
    try:
        with open(KAYIT_YOLU, "w", encoding="utf-8") as f:
            f.write("\n".join(_kayit_satirlari) + "\n")
    except OSError:
        pass


def ortam_bilgisi():
    yaz("--- ortam ---")
    yaz("Python      : %s (%s)" % (sys.version.split()[0], sys.executable))
    yaz("Isletim sis.: %s / %s" % (sys.platform, os.name))
    yaz("Uygulama    : %s" % BASE_DIR)
    yaz("Calisma diz.: %s" % os.getcwd())
    for ad, yol in (("web/index.html", os.path.join(BASE_DIR, "web", "index.html")),
                    ("app/web_server.py", os.path.join(BASE_DIR, "app", "web_server.py")),
                    ("lib/openpyxl", os.path.join(BASE_DIR, "lib", "openpyxl")),
                    ("lib/pypdf", os.path.join(BASE_DIR, "lib", "pypdf"))):
        yaz("  %-18s %s" % (ad, "var" if os.path.exists(yol) else "YOK"))


def modulleri_dene():
    """Gerekli moduller yuklenebiliyor mu."""
    tamam = True
    for ad in ("sqlite3", "json", "http.server", "socketserver", "webbrowser"):
        try:
            __import__(ad)
            yaz("  %-18s tamam" % ad)
        except Exception as exc:
            yaz("  %-18s HATA: %s" % (ad, exc))
            tamam = False
    try:
        import openpyxl
        yaz("  %-18s tamam (%s)" % ("openpyxl", openpyxl.__version__))
    except Exception as exc:
        yaz("  %-18s HATA: %s  (Excel ciktisi calismaz)" % ("openpyxl", exc))
    try:
        from app.pdf_beyanname import _kripto_saglayicisini_ele
        _kripto_saglayicisini_ele()
        import pypdf
        yaz("  %-18s tamam (%s)" % ("pypdf", pypdf.__version__))
    except Exception as exc:
        yaz("  %-18s HATA: %s  (beyanname PDF okunamaz)" % ("pypdf", exc))
    return tamam


def _dinle(port):
    """Verilen portta IPv4 ve mumkunse IPv6 sunucularini baslatir.

    Doner: (sunucular, adresler); port doluysa (None, None).
    """
    from app.web_server import sunucu_baslat

    try:
        dortlu = sunucu_baslat(port, "127.0.0.1")
    except OSError:
        return None, None

    sunucular = [dortlu]
    adresler = ["127.0.0.1"]
    # IPv6 istege baglidir: yoksa da uygulama calisir
    try:
        sunucular.append(sunucu_baslat(port, "::1"))
        adresler.append("[::1]")
    except OSError as exc:
        yaz("  IPv6 (::1) dinlenemedi, yalnizca IPv4: %s" % exc)

    for s in sunucular:
        threading.Thread(target=s.serve_forever, daemon=True).start()
    return sunucular, adresler


def erisim_denemesi(port, konak):
    """Sunucuya gercek bir HTTP istegi atar; (tamam, aciklama) dondurur.

    Vekil sunucu ayarlari devre disi birakilir: yerel adrese vekil uzerinden
    gidilmesi zaten aradigimiz arizanin ta kendisidir.
    """
    import urllib.error
    import urllib.request

    adres = "http://%s:%d/api/tanimlar" % (konak, port)
    acici = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    try:
        with acici.open(adres, timeout=8) as yanit:
            if yanit.status == 200 and yanit.read(16):
                return True, "tamam"
            return False, "beklenmedik yanit (%s)" % yanit.status
    except urllib.error.URLError as exc:
        return False, str(getattr(exc, "reason", exc))
    except Exception as exc:
        return False, "%s: %s" % (type(exc).__name__, exc)


def _port_ac():
    """Bos bir port bulup sunuculari baslatir. Doner: (sunucular, adresler, port)."""
    for aday in range(PORT, PORT + 10):
        sunucular, adresler = _dinle(aday)
        if sunucular:
            return sunucular, adresler, aday
        yaz("Port %d dolu, sonraki deneniyor..." % aday)
    return None, None, None


def tani():
    """Sorun giderme raporu uretir."""
    yaz("KDV Inceleme Calismasi - TANI RAPORU")
    yaz("=" * 52)
    yaz()
    ortam_bilgisi()
    yaz()
    yaz("--- moduller ---")
    modulleri_dene()
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
    sunucular, adresler, port = _port_ac()
    if not sunucular:
        yaz("  HICBIR PORT ACILAMADI (%d-%d)" % (PORT, PORT + 9))
        return 1
    yaz("  dinlenen: %s : %d" % (", ".join(adresler), port))
    for konak in ("127.0.0.1", "localhost"):
        tamam, aciklama = erisim_denemesi(port, konak)
        yaz("  http://%s:%d/  ->  %s (%s)"
            % (konak, port, "ULASILDI" if tamam else "ULASILAMADI", aciklama))
    for s in sunucular:
        s.shutdown()
    yaz()
    yaz("Rapor dosyasi: %s" % KAYIT_YOLU)
    return 0


def main():
    if "--tani" in sys.argv:
        sonuc = tani()
        kaydi_yaz()
        return sonuc

    ortam_bilgisi()
    yaz()

    sunucular, adresler, port = _port_ac()
    if not sunucular:
        yaz("Uygun port bulunamadi (%d-%d dolu)." % (PORT, PORT + 9))
        yaz("Uygulama zaten acik olabilir; acik pencereyi kullanin.")
        kaydi_yaz()
        return 1

    yaz("Dinlenen adresler: %s : %d" % (", ".join(adresler), port))

    # Tarayiciyi acmadan once sunucuya gercekten ulasilabiliyor mu, denenir
    calisan = None
    for konak in ("localhost", "127.0.0.1"):
        tamam, aciklama = erisim_denemesi(port, konak)
        yaz("  http://%s:%d/  ->  %s"
            % (konak, port, "tamam" if tamam else "ULASILAMADI: " + aciklama))
        if tamam and calisan is None:
            calisan = konak

    yaz()
    if calisan is None:
        yaz("!!! Sunucu baslatildi ama kendi kendine ulasamadi.")
        yaz("    Bir guvenlik yazilimi yerel baglantiyi engelliyor olabilir.")
        yaz("    Ayrintili rapor: TANI.bat (Windows) veya python main.py --tani")
        kaydi_yaz()
        yaz()
        _bekle()
        return 1

    adres = "http://%s:%d/" % (calisan, port)
    yedek = "127.0.0.1" if calisan == "localhost" else "localhost"
    yaz("KDV Inceleme Calismasi calisiyor.")
    yaz()
    yaz("    %s" % adres)
    yaz("    (acilmazsa: http://%s:%d/ )" % (yedek, port))
    yaz()
    yaz("Tarayici kendiliginden acilmazsa yukaridaki adresi adres cubuguna")
    yaz("kopyalayin. Kapatmak icin bu pencerede Ctrl+C tusuna basin.")
    kaydi_yaz()

    def tarayiciyi_ac():
        try:
            webbrowser.open(adres)
        except Exception as exc:                          # tarayici yoksa sorun degil
            yaz("(Tarayici acilamadi: %s - adresi elle yazin.)" % exc)

    # daemon: tarayiciyi acan cagri (xdg-open vb.) takilirsa Ctrl+C ile
    # kapanmayi engellememeli
    zamanlayici = threading.Timer(0.5, tarayiciyi_ac)
    zamanlayici.daemon = True
    zamanlayici.start()
    try:
        # Kisa araliklarla uyumak Ctrl+C'nin (SIGINT) her seferinde ana is
        # parcaciginda yakalanmasini saglar; uzun bir kilit bekleyisinde
        # sinyal gozden kacabiliyor
        while True:
            time.sleep(0.5)
    except KeyboardInterrupt:
        yaz("")
        yaz("Kapatiliyor...")
        for s in sunucular:
            s.shutdown()
    return 0


def _bekle():
    try:
        input("Kapatmak icin Enter'a basin...")
    except (EOFError, KeyboardInterrupt):
        pass


if __name__ == "__main__":
    try:
        sys.exit(main())
    except SystemExit:
        raise
    except Exception:
        yaz()
        yaz("!!! Uygulama beklenmedik bir hatayla durdu:")
        yaz(traceback.format_exc())
        kaydi_yaz()
        yaz("Bu metni ve baslatma_kaydi.txt dosyasini bildirin.")
        _bekle()
        sys.exit(1)
