#!/usr/bin/env python3
"""{{UYGULAMA_ADI}} - tani araci.

Uygulama acilmiyorsa sebebini bulur. Windows'ta "acilmiyor" belirtisinin bes
ayri sebebi var ve besi de disaridan ayni gorunuyor; bu arac hepsini sirayla
dener, hangisinin bozuk oldugunu adiyla soyler ve sonucu bir dosyaya yazar.

Kullanicidan hicbir sey bilmesi beklenmez: tani.bat'e cift tiklar, olusan
dosyayi oldugu gibi gonderir.

Yalnizca standart kutuphane kullanilir. Cikti bilerek ASCII'dir: kisitli kod
sayfasi olan konsollarda Turkce karakterler okunamaz hale gelebiliyor.
"""
import os
import socket
import sys
import threading
import urllib.error
import urllib.request
from datetime import datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PORT = {{PORT}}
SONUC_DOSYASI = "{{TANI_DOSYASI}}"

# Arsiv eksik acilmissa (surukle-birak ile) bunlardan biri kayip olur.
BEKLENEN = [
    "main.py",
    "app",
    "web",
]

satirlar = []
sorunlar = []


def yaz(metin=""):
    print(metin)
    satirlar.append(metin)


def baslik(metin):
    yaz()
    yaz(metin)
    yaz("-" * len(metin))


def sorun(kisa, aciklama):
    sorunlar.append((kisa, aciklama))


# --------------------------------------------------------------- 1) ortam

def ortam():
    baslik("1) Ortam")
    yaz("Zaman   : %s" % datetime.now().strftime("%d.%m.%Y %H:%M:%S"))
    yaz("Python  : %s" % sys.version.replace("\n", " "))
    yaz("Yorumcu : %s" % sys.executable)
    yaz("Sistem  : %s" % sys.platform)
    yaz("Klasor  : %s" % BASE_DIR)
    if sys.version_info < (3, 9):
        sorun("Python surumu eski",
              "Python %d.%d bulundu; en az 3.9 gerekiyor."
              % sys.version_info[:2])


# ---------------------------------------------------- 2) klasor butunlugu

def klasor():
    baslik("2) Uygulama dosyalari")
    eksik = [ad for ad in BEKLENEN
             if not os.path.exists(os.path.join(BASE_DIR, ad))]
    for ad in BEKLENEN:
        var = os.path.exists(os.path.join(BASE_DIR, ad))
        yaz("  %-28s %s" % (ad, "var" if var else "YOK"))
    if eksik:
        sorun("Arsiv eksik acilmis",
              "Su dosyalar yok: %s. ZIP surukle-birak ile acilirsa alt "
              "klasorler eksik kalir; ZIP'e sag tiklayip 'Tumunu Ayikla' "
              "demek gerekir." % ", ".join(eksik))


# ------------------------------------------------------- 3) yazma izni

def yazma():
    baslik("3) Yazma izni")
    deneme = os.path.join(BASE_DIR, "tani_yazma_denemesi.tmp")
    try:
        with open(deneme, "w") as f:
            f.write("deneme")
        os.unlink(deneme)
        yaz("  Klasore yazilabiliyor.")
    except OSError as hata:
        yaz("  YAZILAMIYOR: %s" % hata)
        sorun("Klasore yazilamiyor",
              "Uygulama kendi klasorune yazar (veritabani, ciktilar). "
              "'Program Files' ya da salt okunur bir konum yerine "
              "Masaustu veya Belgeler altina tasiyin.")


# --------------------------------------------------- 4) localhost cozumu

def ad_cozumu():
    baslik("4) localhost cozumlemesi")
    try:
        bilgi = socket.getaddrinfo("localhost", PORT, proto=socket.IPPROTO_TCP)
    except socket.gaierror as hata:
        yaz("  COZULEMEDI: %s" % hata)
        sorun("localhost cozulemiyor",
              "Sistemdeki hosts dosyasi bozuk olabilir. Icinde "
              "'127.0.0.1 localhost' satiri bulunmali.")
        return []
    adresler = []
    for aile, _tur, _proto, _ad, sockaddr in bilgi:
        adresler.append((aile, sockaddr[0]))
        yaz("  %-6s %s" % ("IPv6" if aile == socket.AF_INET6 else "IPv4",
                           sockaddr[0]))
    if adresler and adresler[0][0] == socket.AF_INET6:
        yaz()
        yaz("  Not: localhost ONCE ::1 (IPv6) adresine cozuluyor.")
        yaz("  Sunucunun ::1 dinlemesi sart; yalnizca 127.0.0.1 yetmez.")
    return adresler


# ------------------------------------------------------------ 5) portlar

def ipv6_var():
    """Makine gercekten IPv6 soketi acabiliyor mu?

    socket.has_ipv6 bunu soylemez: Python'un IPv6 destegiyle derlendigini
    soyler ve cekirdekte IPv6 kapaliyken de True kalir. Boyle bir makinede
    AF_INET6 soketi acmak dogrudan OSError verir. Tek yol denemektir.
    """
    if not socket.has_ipv6:
        return False
    try:
        socket.socket(socket.AF_INET6, socket.SOCK_STREAM).close()
        return True
    except OSError:
        return False


IPV6 = ipv6_var()


def _port_bos_mu(aile, adres, port):
    try:
        s = socket.socket(aile, socket.SOCK_STREAM)
    except OSError:
        return None
    try:
        # allow_reuse_address BILEREK ayarlanmaz: Windows'ta acilmasi dolu
        # portu bos gostermeye yol acar, tam da olcmek istedigimiz seyi bozar.
        s.bind((adres, port))
        return True
    except OSError:
        return False
    finally:
        s.close()


def portlar():
    baslik("5) Port durumu")
    if not IPV6:
        yaz("  Not: bu makinede IPv6 kapali; yalnizca IPv4 denetlenir.")
    bos_bulundu = None
    for aday in range(PORT, PORT + 10):
        v4 = _port_bos_mu(socket.AF_INET, "127.0.0.1", aday)
        v6 = _port_bos_mu(socket.AF_INET6, "::1", aday) if IPV6 else None
        durum = "bos" if (v4 and v6 is not False) else "DOLU"
        yaz("  %-6d IPv4 %-4s  IPv6 %-4s  -> %s"
            % (aday,
               "bos" if v4 else "dolu",
               "-" if v6 is None else ("bos" if v6 else "dolu"),
               durum))
        if durum == "bos" and bos_bulundu is None:
            bos_bulundu = aday
    if bos_bulundu is None:
        sorun("Bos port yok",
              "%d-%d araligindaki portlarin hepsi dolu. Uygulamanin baska "
              "bir kopyasi acik olabilir; tum pencereleri kapatip yeniden "
              "deneyin." % (PORT, PORT + 9))
    else:
        yaz()
        yaz("  Kullanilabilecek ilk port: %d" % bos_bulundu)
    return bos_bulundu


# ------------------------------------------------- 6) gercek baglanti testi

class _Sessiz(BaseHTTPRequestHandler):
    def do_GET(self):
        govde = b"tani"
        self.send_response(200)
        self.send_header("Content-Length", str(len(govde)))
        self.end_headers()
        self.wfile.write(govde)

    def log_message(self, bicim, *args):
        pass


class _SunucuV6(ThreadingHTTPServer):
    address_family = socket.AF_INET6
    allow_reuse_address = False
    daemon_threads = True


class _Sunucu(ThreadingHTTPServer):
    allow_reuse_address = False
    daemon_threads = True


def _dene(adres, proxy_ile):
    """Adrese HTTP istegi atar; (basarili, aciklama) doner."""
    if proxy_ile:
        acici = urllib.request.build_opener()
    else:
        acici = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    try:
        with acici.open(adres, timeout=5) as yanit:
            yanit.read()
        return True, "baglandi"
    except urllib.error.URLError as hata:
        return False, str(getattr(hata, "reason", hata))
    except Exception as hata:              # timeout, socket hatalari
        return False, "%s: %s" % (type(hata).__name__, hata)


def baglanti(port):
    baslik("6) Gercek baglanti denemesi")
    if port is None:
        yaz("  Bos port bulunamadigi icin atlandi.")
        return
    adaylar = [(_Sunucu, "127.0.0.1")]
    if IPV6:
        adaylar.insert(0, (_SunucuV6, "::1"))
    sunucular = []
    for sinif, adres in adaylar:
        try:
            sunucular.append(sinif((adres, port), _Sessiz))
        except OSError as hata:
            yaz("  %s dinlenemedi: %s" % (adres, hata))
    if not sunucular:
        sorun("Sunucu ayaga kalkmiyor",
              "Ne ::1 ne 127.0.0.1 dinlenebildi. Guvenlik duvari ya da "
              "kurum ilkesi yerel sunucuyu engelliyor olabilir.")
        return
    for s in sunucular:
        threading.Thread(target=s.serve_forever, daemon=True).start()
    yaz("  Deneme sunucusu %d portunda ayakta (%d adres)."
        % (port, len(sunucular)))
    yaz()

    sonuc = {}
    for etiket, adres in (("localhost", "http://localhost:%d/" % port),
                          ("127.0.0.1", "http://127.0.0.1:%d/" % port)):
        for proxy_ile in (False, True):
            ok, aciklama = _dene(adres, proxy_ile)
            sonuc[(etiket, proxy_ile)] = ok
            yaz("  %-10s %-16s %s%s"
                % (etiket,
                   "sistem proxy'si" if proxy_ile else "proxy'siz",
                   "TAMAM" if ok else "BASARISIZ",
                   "" if ok else "  (%s)" % aciklama))

    for s in sunucular:
        s.shutdown()
        s.server_close()

    yaz()
    if sonuc.get(("localhost", True)) and not sonuc.get(("127.0.0.1", True)):
        yaz("  Teshis: 127.0.0.1 proxy'ye gidiyor, localhost gitmiyor.")
        yaz("  Uygulama localhost adresi kullandigi icin bu SORUN DEGIL.")
    elif not sonuc.get(("localhost", True)) and sonuc.get(("localhost", False)):
        sorun("Proxy localhost'u da yakaliyor",
              "Proxy ayarindaki istisna listesi ('Yerel adresler icin proxy "
              "kullanma') kapali gorunuyor. Tarayicida sayfa acilmayacaktir; "
              "bilgi islemden localhost'un istisna listesine eklenmesini "
              "isteyin.")
    elif not sonuc.get(("localhost", False)):
        sorun("Yerel baglanti kurulamiyor",
              "Proxy devre disiyken bile localhost'a baglanilamadi. "
              "Guvenlik duvari ya da bir guvenlik yazilimi engelliyor.")


# ------------------------------------------------------- 7) proxy ayarlari

def proxy_ayarlari():
    baslik("7) Proxy ayarlari")
    ortam_degiskenleri = [(ad, os.environ[ad]) for ad in
                          ("HTTP_PROXY", "HTTPS_PROXY", "NO_PROXY",
                           "http_proxy", "https_proxy", "no_proxy")
                          if ad in os.environ]
    if ortam_degiskenleri:
        for ad, deger in ortam_degiskenleri:
            yaz("  %-12s %s" % (ad, deger))
    else:
        yaz("  Ortam degiskeni yok.")

    if os.name != "nt":
        yaz("  (Kayit defteri denetimi yalnizca Windows'ta calisir.)")
        return
    try:
        import winreg
    except ImportError:
        return
    yol = r"Software\Microsoft\Windows\CurrentVersion\Internet Settings"
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, yol) as anahtar:
            def oku(ad):
                try:
                    return winreg.QueryValueEx(anahtar, ad)[0]
                except OSError:
                    return None
            acik = oku("ProxyEnable")
            sunucu = oku("ProxyServer")
            istisna = oku("ProxyOverride")
            yaz("  ProxyEnable   %s" % acik)
            yaz("  ProxyServer   %s" % (sunucu or "-"))
            yaz("  ProxyOverride %s" % (istisna or "-"))
            if acik and not (istisna and "<local>" in str(istisna)):
                sorun("Yerel adres istisnasi kapali",
                      "Proxy acik ama 'Yerel (intranet) adresler icin proxy "
                      "kullanma' isaretli degil. Tarayici localhost'u da "
                      "proxy'ye gonderir ve sayfa acilmaz.")
    except OSError as hata:
        yaz("  Kayit defteri okunamadi: %s" % hata)


# ---------------------------------------------------------- 8) tarayicilar

def tarayicilar():
    baslik("8) Tarayicilar")
    if os.name != "nt":
        yaz("  (Yalnizca Windows'ta anlamli.)")
        return
    adaylar = [
        ("Chrome", r"C:\Program Files\Google\Chrome\Application\chrome.exe"),
        ("Chrome",
         r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"),
        ("Chrome", os.path.expandvars(
            r"%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe")),
        ("Edge", r"C:\Program Files (x86)\Microsoft\Edge\Application"
                 r"\msedge.exe"),
        ("Firefox", r"C:\Program Files\Mozilla Firefox\firefox.exe"),
    ]
    bulunan = []
    for ad, yol in adaylar:
        if os.path.isfile(yol):
            bulunan.append(ad)
            yaz("  %-8s %s" % (ad, yol))
    if not bulunan:
        yaz("  Bilinen yollarda tarayici bulunamadi.")
        sorun("Tarayici bulunamadi",
              "Chrome/Edge/Firefox bilinen konumlarda yok. Uygulama adresi "
              "ekrana yazacaktir; tarayiciya elle yapistirin.")
    elif "Chrome" not in bulunan:
        yaz()
        yaz("  Chrome yok; varsayilan tarayici kullanilacak.")


# ---------------------------------------------------------------- rapor

def main():
    yaz("=" * 60)
    yaz("{{UYGULAMA_ADI}} - tani raporu")
    yaz("=" * 60)
    ortam()
    klasor()
    yazma()
    ad_cozumu()
    port = portlar()
    baglanti(port)
    proxy_ayarlari()
    tarayicilar()

    baslik("SONUC")
    if sorunlar:
        for sira, (kisa, aciklama) in enumerate(sorunlar, 1):
            yaz("%d) %s" % (sira, kisa))
            for parca in _sar(aciklama, 66):
                yaz("   %s" % parca)
            yaz()
    else:
        yaz("Engelleyici bir sorun bulunamadi.")
        yaz("Uygulama bu bilgisayarda calisabilir gorunuyor.")

    hedef = os.path.join(BASE_DIR, SONUC_DOSYASI)
    try:
        with open(hedef, "w", encoding="utf-8-sig", newline="\r\n") as f:
            f.write("\n".join(satirlar) + "\n")
        print()
        print("Bu rapor su dosyaya yazildi:")
        print("   %s" % hedef)
        print("Dosyayi oldugu gibi gonderin.")
    except OSError as hata:
        print()
        print("Rapor dosyaya yazilamadi (%s)." % hata)
        print("Yukaridaki metni secip kopyalayarak gonderin.")
    return 1 if sorunlar else 0


def _sar(metin, genislik):
    """Metni verilen genislige gore boler (textwrap'siz, ASCII icin yeterli)."""
    kelimeler = metin.split()
    satir, cikti = "", []
    for kelime in kelimeler:
        if satir and len(satir) + 1 + len(kelime) > genislik:
            cikti.append(satir)
            satir = kelime
        else:
            satir = "%s %s" % (satir, kelime) if satir else kelime
    if satir:
        cikti.append(satir)
    return cikti


if __name__ == "__main__":
    sys.exit(main())
