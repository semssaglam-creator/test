# Windows tuzaklari

Alti tuzak. Dordu ayni belirtiyle ortaya cikar: **uygulama sorunsuz calisir,
kullanicida acilmaz.** Sunucu ayaktadir, konsol adresi yazar, hicbir hata
yoktur; kullanici bos bir tarayici sayfasi gorur. Linux/macOS'ta hicbiri
gorunmez, o yuzden gelistirici makinesinde test etmek bunlari yakalamaz.

Sirasiyla: adres, IPv6, port, tarayici, dosya kilidi, tirnak.

## Sahadan

Bir vergi inceleme uygulamasi kurumsal bir Windows makinesinde bu yolla
calistirildi. Oradan gelen tani raporu iki maddeyi dogruladi, birini de
gereksiz kildi:

- **2 gercek.** `localhost` o makinede once `::1`'e cozuluyordu. Yalnizca
  `127.0.0.1` dinleyen surum orada tarayicida acilmazdi.
- **6 gercek ve en pahalisi.** Paket klasorunun adinda bosluk oldugu icin
  hicbir `.bat` calismadi. Duman testi Linux'ta yapildigindan hic gorunmemisti.
- **1 o makinede gereksizdi:** proxy kapaliydi (`ProxyEnable 0`), `127.0.0.1`
  de calisirdi. Yine de `localhost` kullanmanin bedeli yok; proxy'li bir
  makinede fark yaratacak olan tek sey odur.

Ders: tuzaklarin hangisinin vuracagi makineye gore degisir, o yuzden hepsi
bastan kapatilir.

---

## 1. `127.0.0.1` kurumsal proxy'ye gider — `localhost` gitmez

**Belirti:** Konsolda "calisiyor: http://127.0.0.1:8766/" yazar, tarayici
"Bu siteye ulasilamiyor" ya da proxy hata sayfasi gosterir.

**Sebep:** Windows'un proxy ayarindaki "Yerel (intranet) adresler icin proxy
sunucusu kullanma" kutusu — kayit defterinde `ProxyOverride` icindeki
`<local>` belirteci — yalnizca **noktasiz** ana bilgisayar adlarini kapsar.
`127.0.0.1` nokta icerdigi icin "yerel" sayilmaz ve istek kurumsal proxy'ye
gonderilir. Proxy de kendi agindan sizin makinenizin loopback adresine
ulasamaz. `localhost` noktasizdir, dogrudan gider.

Kurum ilkesiyle dayatilan proxy'lerde bu ayar cogu zaman kilitlidir; kullanici
duzeltemez. Cozum bizde.

**Duzeltme:** Kullaniciya gosterilen ve tarayiciya verilen adres **her zaman**
`localhost` olsun.

```python
adres = f"http://localhost:{port}/"
```

Sunucunun neye **baglandigi** ayri konudur (bkz. 2); bu madde yalnizca
tarayiciya verilen metinle ilgilidir. `paketle.sh` kodda ve belgelerde
`http://127.0.0.1:` gecmesini yasaklar.

> `ProxyOverride` degerine `127.0.0.1;<local>` eklemek de calisir ama kayit
> defterini kullanici adina degistirmek gerekir; yapmayin.

---

## 2. `localhost` once `::1`'e cozulur — IPv4 dinleyen sunucu bulunamaz

**Belirti:** Tarayici "baglanti reddedildi" der. `curl 127.0.0.1:8766` calisir,
`curl localhost:8766` calismaz.

**Sebep:** Windows'ta `localhost` hem `::1` (IPv6) hem `127.0.0.1` (IPv4)
adresine cozulur ve **once `::1` denenir**. `ThreadingHTTPServer(("127.0.0.1",
port))` yalnizca IPv4 dinler. Tarayici `::1`'e baglanmaya calisir, kimse
dinlemiyordur.

Tarayicilarin cogu bir sure sonra IPv4'e duser ("Happy Eyeballs"), ama
kurumsal makinelerde bu geri dusme kapali olabiliyor ve baglanti dogrudan
basarisiz oluyor. 1. maddeyi duzeltip bunu atlarsaniz sorun **yer degistirir**,
kaybolmaz.

**Duzeltme:** Iki aileyi de dinleyin. Ikisinden biri baglanamazsa, digerini de
kapatip hata firlatin — yarim baglanmis sunucu, "port bos" sanildigi icin
3. maddedeki hataya yol acar.

```python
import socket
import threading
from http.server import ThreadingHTTPServer


class _Sunucu(ThreadingHTTPServer):
    # Bkz. 3. madde: Windows'ta True, dolu portu "calmaya" izin verir.
    allow_reuse_address = False
    daemon_threads = True


class _SunucuV6(_Sunucu):
    address_family = socket.AF_INET6


class CiftSunucu:
    """IPv4 ve IPv6 loopback'i birlikte dinleyen sunucu ciftidir.

    Windows'ta localhost once ::1'e cozuldugu icin yalnizca 127.0.0.1
    dinlemek yetmez; yalnizca ::1 dinlemek de IPv6'si kapali makinelerde
    yetmez. Ikisi birden dinlenir.
    """

    def __init__(self, sunucular):
        self._sunucular = sunucular

    def serve_forever(self):
        for s in self._sunucular[1:]:
            threading.Thread(target=s.serve_forever, daemon=True).start()
        self._sunucular[0].serve_forever()

    def shutdown(self):
        for s in self._sunucular:
            s.shutdown()

    def server_close(self):
        for s in self._sunucular:
            s.server_close()


def ipv6_var():
    """Makine gercekten IPv6 soketi acabiliyor mu?

    socket.has_ipv6 BU SORUYU CEVAPLAMAZ: o, Python'un IPv6 destegiyle
    derlendigini soyler ve cekirdekte IPv6 kapatilmis olsa bile True kalir.
    Boyle bir makinede AF_INET6 soketi acmak "OSError: [Errno 97] Address
    family not supported by protocol" verir. Tek guvenilir yol denemektir.
    """
    if not socket.has_ipv6:
        return False
    try:
        socket.socket(socket.AF_INET6, socket.SOCK_STREAM).close()
        return True
    except OSError:
        return False


def sunucu_baslat(port, istekci):
    """Verilen portu iki loopback ailesinde birden acar.

    IPv6 KULLANILABILIYORSA iki aile de zorunludur: biri acilip digeri
    acilamazsa acilan da kapatilir ve OSError firlatilir. Boylece cagiran
    taraf portu "dolu" sayip sonrakini dener; yarim acik sunucu kalmaz.

    Bu ayrim onemli: ::1 baglanamadiginda "IPv6 yok" ile "portu baskasi
    tutuyor" ayni istisnayi verir. Ikincisini gormezden gelirsek, calisan
    bir kopya varken ikincisi yalnizca IPv4'te ayaga kalkar; localhost once
    ::1'e cozuldugu icin tarayici ESKI kopyaya baglanir ve kullanici
    kaydettigi verinin kayboldugunu sanir.
    """
    sunucular = []
    try:
        if ipv6_var():
            sunucular.append(_SunucuV6(("::1", port), istekci))
        sunucular.append(_Sunucu(("127.0.0.1", port), istekci))
    except OSError:
        for s in sunucular:
            s.server_close()
        raise
    return CiftSunucu(sunucular)
```

`_SunucuV6` icin `IPV6_V6ONLY` ayarina dokunulmaz: Windows'ta varsayilan zaten
1'dir, yani `::1` soketi IPv4 baglantilarini almaz ve ayni portu 127.0.0.1
soketiyle paylasabilir. Linux'ta `::1`'e baglanmak da yalnizca IPv6 loopback'i
kapsar. Ikisinde de catisma olmaz.

---

## 3. `allow_reuse_address = True` Windows'ta dolu portu **calar**

**Belirti:** Uygulama zaten acikken ikinci kez baslatilir. Ikinci pencere ayni
portu yazar, tarayici acilir — ama istekler bazen birinciye, bazen ikinciye
gider. Kaydedilen veri kaybolur ya da eski surumu gorunur.

**Sebep:** Bu, Unix ve Windows'un ayni bayrakla farkli sey yapmasindan
kaynaklanir. Unix'te `SO_REUSEADDR`, yalnizca `TIME_WAIT` bekleyen bir adresin
yeniden kullanilmasina izin verir; **aktif** bir dinleyici varsa `bind`
yine de basarisiz olur. Windows'ta ayni bayrak, **halihazirda dinlenen** bir
adrese ikinci bir soketin baglanmasina izin verir; hangisinin baglantiyi
alacagi tanimsizdir.

`socketserver.TCPServer` varsayilan olarak `allow_reuse_address = 1` tasir.
Sonuc: "port dolu mu?" diye deneyip `OSError` bekleyen kod Windows'ta **hicbir
zaman hata almaz**, portu dolu sanmaz, sonraki porta gecmez.

**Duzeltme:** Sinifta acikca kapatin (yukaridaki `_Sunucu` icinde var):

```python
class _Sunucu(ThreadingHTTPServer):
    allow_reuse_address = False
```

Cagiran taraftaki "sonraki portu dene" dongusu de boylece anlam kazanir:

```python
for aday in range(PORT, PORT + 10):
    try:
        sunucu = sunucu_baslat(aday, Istekci)
        port = aday
        break
    except OSError:
        continue
```

Unix'te `allow_reuse_address = False` yapmanin bedeli, uygulamayi kapatip hemen
yeniden baslatinca portun `TIME_WAIT` yuzunden bir sure dolu gorunmesidir.
Dongu zaten sonraki porta gecer; kullanici farki gormez.

---

## 4. `webbrowser.open` kurumsal makinede yanlis tarayiciyi acar

**Belirti:** Sayfa Internet Explorer'da ya da eski bir Edge'de acilir; arayuz
bozuk gorunur veya bos kalir. Bazen hicbir sey acilmaz.

**Sebep:** `webbrowser` modulu Windows'ta isletim sisteminin varsayilan
tarayicisini cagirir. Kurumsal makinelerde varsayilan cogu zaman ilke ile
IE/Edge'e sabitlenmistir; ayrica `webbrowser.open` bir tarayici bulamazsa
sessizce `False` doner — istisna firlatmaz, kimse fark etmez.

**Duzeltme:** Once Chrome'u bilinen yollarda arayin, yoksa varsayilana dusun.
Donus degerini kontrol edin ve basarisizsa adresi ekrana yazin — kullanici
elle yapistirabilsin.

```python
import os
import webbrowser

_CHROME_YOLLARI = (
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
    os.path.expandvars(
        r"%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe"),
)


def tarayici_ac(adres):
    """Adresi tarayicida acar; basarisizsa False doner.

    Kurumsal Windows makinelerinde varsayilan tarayici ilke ile eski bir
    surume sabitlenmis olabiliyor. Chrome varsa once o denenir. webbrowser
    hicbir tarayici bulamazsa istisna firlatmaz, sessizce False doner; bu
    yuzden donus degeri kontrol edilir.
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
```

Cagiran tarafta:

```python
if not tarayici_ac(adres):
    print("Tarayici acilamadi. Su adresi tarayiciya elle yapistirin:")
    print("   ", adres)
```

Bu cagriyi bir zamanlayici ipliginde yapin ve iplik `daemon` olsun; masaustu
olmayan bir oturumda cagri takilirsa Ctrl+C ile kapanmayi engellemesin.

---

## 5. Windows acik dosyayi silmez, uzerine yazdirmaz

**Belirti:** Ilk dosya yukleme calisir, **ikincisi** `PermissionError: [WinError
32] The process cannot access the file because it is being used by another
process` verir. Kullanici "bir kez calisiyor, sonra bozuluyor" der.

**Sebep:** Unix'te acik bir dosyayi silmek ya da uzerine yazmak serbesttir.
Windows'ta dosya baska bir tanitici tarafindan aciksa engellenir. Sabit adli
bir gecici dosyaya yazip (`gecici.xlsx`) sonra okuyan kod, tanitici tam
kapanmadan ikinci cagri gelince patlar. Virus tarayicilar da yeni yazilan
dosyayi kisa sure acik tutar; kod dogru gorunse bile arada patlayabilir.

**Duzeltme:** Diske hic yazmayin. Uretilen belgeyi bellekte tutup dogrudan
yanit govdesine verin:

```python
import io

tampon = io.BytesIO()
calisma_kitabi.save(tampon)          # openpyxl, python-docx, zipfile hepsi kabul eder
govde = tampon.getvalue()
```

Gecici dosya gercekten sart ise `tempfile.NamedTemporaryFile(delete=False)`
kullanin, taniticiyi kapatin, isiniz bitince `os.unlink` deneyin ve
basarisizligi yutun.

### Ayni aileden, ayni anda bakilacaklar

- **MAX_PATH 260.** Kullanici verisinden uretilen dosya adlari
  (`Rapor_2024_COK_UZUN_UNVAN_A_S.docx`) derin bir `Downloads` yolunda siniri
  asar; uzun yol destegi varsayilan olarak kapalidir. Adi ~60 karaktere
  kirpin.
- **Yasakli karakterler.** `< > : " / \ | ? *` Windows dosya adinda gecemez;
  `CON`, `PRN`, `AUX`, `NUL`, `COM1`, `LPT1` ayrilmis adlardir. Kullanici
  verisinden ad uretiyorsaniz suzun.
- **`posixpath.basename`** ters egik cizgiyi ayirici saymaz:
  `posixpath.basename(r"C:\a\b.txt")` tum metni doner. Yuklenen dosya adini
  ayiklarken `os.path.basename` kullanin (ya da her iki ayiriciyi da elle
  bolun — tarayici bazen istemci yolunu tam gonderir).
- **`os.access(yol, os.X_OK)` ve `chmod`** Windows'ta anlamsizdir; `X_OK`
  neredeyse her zaman `True` doner. Bu kontrole dayali "baslaticiyi onar"
  mantigini `if os.name == "nt": return` ile atlayin.
- **Satir sonu.** Uretilen `.txt` dosyalarini Not Defteri dogru gostersin diye
  UTF-8 BOM + CRLF yazin (`arac/belge_hazirla.py --metin`). Modern Not Defteri
  LF'i de acar ama eski surumler tek satir gosterir.

---

## 6. `.bat` icinde tirnaksiz yol, ilk boslukta kirilir

**Belirti:** Hicbir `.bat` calismaz. Pencere acilir ve tek satir yazar:

```
'C:\Users\ad.soyad\Desktop\KDV' is not recognized as an internal or
external command, operable program or batch file.
```

Yolun yarisinda kesildigine dikkat edin: `...\Desktop\KDV` — devami
(`Inceleme Calismasi\python\python.exe`) yok.

**Sebep:** Uygulama klasorunun yolunda bosluk var ve degisken tirnaksiz
yazilmis:

```bat
set "PY=%~dp0python\python.exe"
%PY% main.py
```

`%~dp0` acildiginda satir soyle olur:

```
C:\Users\ad.soyad\Desktop\KDV Inceleme Calismasi\python\python.exe main.py
```

cmd, komut adini **ilk boslukta** biter sayar ve `C:\Users\...\Desktop\KDV`
adinda bir program arar.

Bu, "bazen olur" turunden bir sey degil: paket klasorunun adinda bosluk varsa
**her kurulumda** olur. Kullanicinin bir hatasi yoktur, Windows'un
`Program Files` / `OneDrive - Firma` gibi varsayilan yollarinda da bosluk
vardir.

**Duzeltme — tirnak tek basina yetmez.** Degisken bazen bir yol
(`...\python.exe`), bazen argumanli bir komut (`py -3`) olur.
`"%PY%" main.py` yazarsaniz ikinci durumda cmd bu kez `py -3` **adinda** bir
dosya arar. Cozum degiskeni ikiye bolmektir:

```bat
rem _python_bul.bat icinde:
set "PYEXE=%~dp0python\python.exe"   &  rem  ... ya da:
set "PYEXE=py"
set "PYARG=-3"

rem Cagiran tarafta HER ZAMAN:
"%PYEXE%" %PYARG% main.py
```

`PYEXE` daima tirnak icinde, `PYARG` daima tirnaksiz. `echo` ve `rem`
satirlarinda tirnaksiz gecmesi zararsizdir; cmd orada komut aramaz.

**Denetim** (`paketle.sh` icinde):

```bash
tirnaksiz="$(grep -nE '(^|[^"])%PYEXE%' "$PAKET"/*.bat 2>/dev/null \
  | grep -viE ':[[:space:]]*(echo|rem)\b' || true)"
```

Desendeki `(^|...)` onemli: `%PYEXE% main.py` satirin ilk sozcuguyse onunde
karakter olmaz ve yalnizca `[^"]%PYEXE%` yazan bir desen onu **kacirir**. Bu
denetim tam da o yuzden bir kez yaniltici bicimde "gecti" dedi; kasitli bozuk
bir surumle sinamadan dogru kabul etmeyin.

Bu tuzak digerlerinden ayrilir: `.bat` dosyalari duman testinde hic
calistirilmaz (Linux'ta `python3 main.py` dogrudan cagrilir), bu yuzden
**yalnizca gercek Windows'ta** ortaya cikar. Tek savunma denetimdir.

---

## Bunlar neden gelistirici makinesinde gorunmez

| Tuzak | Linux/macOS'ta | Windows'ta |
| --- | --- | --- |
| 1 — adres | proxy yok, `127.0.0.1` gider | `<local>` noktasiz ad ister, istek proxy'ye gider |
| 2 — IPv6 | `localhost` cogu dagitimda once IPv4 | once `::1` denenir |
| 3 — port | `SO_REUSEADDR` aktif dinleyiciyi engeller | ikinci baglanmaya izin verir |
| 4 — tarayici | varsayilan tarayici makul | ilke ile IE/Edge'e sabitlenmis olabilir |
| 5 — dosya | acik dosya silinir/uzerine yazilir | kilitlidir |
| 6 — tirnak | `.bat` hic calistirilmaz | bosluklu yolda her seferinde kirilir |

Bu yuzden `paketle.sh` denetimleri kaynak kodun uzerinde calisir: gercek
Windows testi yapilamadigi icin, kurallara uyuldugunu **paket uretilirken**
dogrulamak tek savunmadir.
