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
# lib_ek SONA eklenir, basa degil.
#
# Icinde yalnizca baska paketlerin de kullandigi ortak bir modul durur
# (typing_extensions). Basa eklenirse bilgisayarda kurulu surumu golgeler ve
# ona guvenen paketleri bozar: bir kez, sistemdeki Pillow bizim surumumuzu
# yukleyip AttributeError firlatmis, openpyxl bunu ImportError beklediginden
# yakalayamamis ve uygulama hic acilmamisti. Sona eklenince sistemdeki surum
# varsa o kullanilir, yoksa bizimki yedek olarak devreye girer.
sys.path.append(os.path.join(BASE_DIR, "lib_ek"))

PORT = 8766
HATA_DOSYASI = "KDV HATA - BUNU GONDERIN.txt"

# Kurumsal Windows makinelerinde isletim sisteminin varsayilan tarayicisi
# ilke ile eski bir Edge/IE surumune sabitlenmis olabiliyor; arayuz orada
# bozuk gorunur. Chrome kuruluysa once o denenir.
_CHROME_YOLLARI = (
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
    os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe"),
)


def tarayici_ac(adres):
    """Adresi tarayicida acar; acamazsa False doner.

    webbrowser.open hicbir tarayici bulamadiginda istisna firlatmaz, sessizce
    False doner. Donus degeri kontrol edilmezse kullanici bos bir ekrana bakip
    uygulamanin acilmadigini sanir; oysa sunucu ayaktadir ve adres yalnizca
    elle yapistirilmayi bekler.
    """
    if os.name == "nt":
        for yol in _CHROME_YOLLARI:
            if os.path.isfile(yol):
                try:
                    webbrowser.register(
                        "chrome", None, webbrowser.BackgroundBrowser(yol))
                    return webbrowser.get("chrome").open(adres)
                except webbrowser.Error:
                    break
    try:
        return webbrowser.open(adres)
    except webbrowser.Error:
        return False


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


def _baslaticiyi_onar():
    """calistir.sh'in "calistirilabilir" isaretini gerekiyorsa geri koyar.

    Uygulama yeni bir surumle guncellenirken dosyalar kopyalanip yapistirilinca
    bu isaret kaybolabiliyor. Kisayol calistir.sh'i calistiramiyor, ekranda
    hicbir sey olmuyor ve uygulama "hic acilmiyor" gorunuyor. Uygulama bir kez
    calistiysa bunu kendisi duzeltir.

    Basarisiz olmasi onemsizdir; acilisi hicbir kosulda engellemez.
    """
    # Windows'ta "calistirilabilir" isareti diye bir sey yok: os.access(X_OK)
    # neredeyse her zaman True doner ve chmod bir ise yaramaz. Orada baslatici
    # .bat dosyasidir, boyle bir onarima da ihtiyac duymaz.
    if os.name == "nt":
        return
    try:
        yol = os.path.join(BASE_DIR, "calistir.sh")
        if os.path.isfile(yol) and not os.access(yol, os.X_OK):
            os.chmod(yol, os.stat(yol).st_mode | 0o111)
            print("Baslatici onarildi: calistir.sh calistirilabilir yapildi.")
    except OSError:
        pass


def main():
    _baslaticiyi_onar()
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
        # Buraya gelmenin en olagan sebebi, onceki denemelerin arka planda
        # calisir halde kalmasidir: uygulama masaustu kisayolundan acildiginda
        # konsol olmadigi icin gorunmez, kullanici "acilmadi" sanip yeniden
        # dener ve her deneme bir portu daha tutar.
        print(f"Uygun port bulunamadi ({PORT}-{PORT + 9} dolu).")
        print()
        print("En olagan sebep: uygulamanin onceki kopyalari halen calisiyor.")
        print("Acik pencereleri kapatin. Pencere gorunmuyorsa arka planda")
        print("calisiyor olabilir; su komut hepsini kapatir:")
        print()
        print("    pkill -f 'python3 main.py'")
        print()
        print("Sonra uygulamayi yeniden baslatin.")
        sys.exit(1)

    # Adres BILEREK localhost; 127.0.0.1 degil. Windows'un "yerel adresler
    # icin proxy kullanma" ayari yalnizca noktasiz adlari kapsadigindan,
    # 127.0.0.1 kurumsal proxy'ye gider ve sunucu sorunsuz calisirken
    # kullanici "sayfaya ulasilamadi" gorur.
    adres = f"http://localhost:{port}/"
    print("KDV Inceleme Calismasi calisiyor:", adres)
    print("Kapatmak icin bu pencerede Ctrl+C tusuna basin.")

    def _ac():
        if not tarayici_ac(adres):
            print("\nTarayici kendiliginden acilamadi.")
            print("Su adresi tarayiciya elle yapistirin:\n   ", adres)

    # daemon: tarayiciyi acan cagri takilirsa (ornegin masaustu olmayan bir
    # makinede ya da SSH oturumunda) Ctrl+C ile kapanmayi engellemesin
    zamanlayici = threading.Timer(0.5, _ac)
    zamanlayici.daemon = True
    zamanlayici.start()
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
