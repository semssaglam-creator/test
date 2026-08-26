---
name: windows-paketi
description: >
  Python uygulamasini kurulum gerektirmeyen bir Windows paketine cevirir:
  gomulu Python, .bat baslaticilar, ikon, kullanici belgeleri ve denetimli bir
  zip. Kullanici Windows'a tasima, Windows paketi, Windows kurulumu, exe yapma,
  masaustu kisayolu, .bat baslatici, gomulu/tasinabilir Python, "Windows'ta
  calissin", "is bilgisayarinda acilsin", PyInstaller alternatifi, uygulamayi
  dagitma ya da paketleme konularindan birini actiginda MUTLAKA bu skill'i
  kullan. Cikti, kullanicinin cift tiklayip calistirdigi bir klasordur.
---

# Python Uygulamasini Windows Paketine Cevirme

Bu skill sahada dogrulanmis bir yontemi tasir: bir vergi inceleme uygulamasi bu
yolla kurumsal bir Windows makinesinde calistirildi. Icindeki uyarilar teorik
degil, o surecte kirilip duzeltilmis noktalardir.

Temel fikir: Python kodu genelde zaten tasinabilirdir. Is, kodu yeniden yazmak
degil; baslaticilari, gomulu Python'u ve Windows'a ozgu birkac gercek tuzagi
halletmektir.

## Adim 0 — Uygunluk

Bu yontem sunlara uyar:

- Saf Python (stdlib) veya saf Python bagimliliklar (openpyxl, pypdf gibi —
  derlenmis uzanti icermeyenler, `lib/` icine konabilir)
- Yerel sunucu + tarayici arayuzu, ya da konsol uygulamasi

Uymaz: derlenmis C uzantilari (numpy, pandas, Pillow), GUI cerceveleri (PyQt,
wxPython), platforma bagli sistem cagrilari. Bunlar varsa **once kullaniciya
soyleyin** — PyInstaller ya da farkli bir yol gerekir.

pip bagimliliklarini `lib/` icine indirip `sys.path`'e eklemek bu yontemin
parcasidir; sanal ortam ya da kurulum adimi yoktur.

## Adim 1 — Once oku: Windows tuzaklari

`references/windows-tuzaklari.md` dosyasini **kod yazmadan once** okuyun. Alti
tuzagin dordu "uygulama calisiyor ama kullanicida acilmiyor" biciminde ortaya
cikar; sonradan bulmak saatler alir.

En kritigi, bir cumlede: **tarayiciya `localhost` verin, `127.0.0.1`
vermeyin.** Windows'un "yerel adresler icin proxy kullanma" ayari yalnizca
noktasiz adlari kapsar; `127.0.0.1` kurumsal proxy'ye gider ve sunucu sorunsuz
calisirken kullanici "sayfaya ulasilamadi" gorur.

## Adim 2 — Kullaniciya iki soru

Devam etmeden once netlestirin:

1. **Hangi mimari?** `amd64` (neredeyse her zaman) ya da `arm64`.
2. **Tek kaynak mi, ayri kopya mi?** Tek kaynak onerilir: ayni klasor hem
   Linux/macOS hem Windows'a hizmet eder, `.bat` ve `.sh` yan yana durur. Ayri
   kopya isteniyorsa **her duzeltmenin iki yerde yapilacagini** soyleyin.

Uygulamanin kendisi hakkinda karar vermeyin — mevcut davranisi koruyun.

## Adim 3 — Iskeleti kur

```
~/.claude/skills/windows-paketi/arac/uyarla.sh <proje_dizini>
```

Sordugu degerler: uygulama adi, kisayol aciklamasi, paket klasoru, arsiv adi,
baslangic portu, tani dosyasi adi.

Projeye yerlesenler:

| Yol | Ne |
| --- | --- |
| `windows/*.bat` | `calistir`, `kur`, `kaldir`, `tani` — CRLF ile |
| `app/tani.py` | Tani araci (asagida) |
| `paketle.sh` | Paketi uretir ve **denetler** |
| `arac/` | `png2ico.py`, `belge_hazirla.py`, `python_indir.sh` |

Sonrasinda bu dosyalar **projenin kendi dosyalaridir**; skill'e geri donmeden
orada duzenlenir.

## Adim 4 — Kodu uyarla

`references/windows-tuzaklari.md` icindeki dort duzeltmeyi uygulayin:
`localhost` adresi, `::1` cift dinleme, `allow_reuse_address = False`, Chrome
onceligi. Hazir kod parcalari o dosyada — **oradaki kodu oldugu gibi alin.**

`::1` cift dinlemede kod parcasini kisaltmayin: `::1`'e baglanamama iki ayri
sebepten olur ve `errno` ile ayrilmazsa, tuzagi kapatmak icin yazdiginiz kod
butun portlari dolu gosterir. Sahada boyle oldu; ayrintisi 2. maddede.

Ayrica gozden gecirin:

- **Sabit adli gecici dosya var mi?** Windows'ta acik dosya silinemez ve uzerine
  yazilamaz — ikinci yukleme `PermissionError` verir. `io.BytesIO` kullanin;
  diske hic yazmayin.
- **Dosya adlari kullanici verisinden mi uretiliyor?** Uzun adlar MAX_PATH 260
  sinirini zorlar; ~60 karakterle sinirlayin.
- **`os.access(..., os.X_OK)` / `chmod` var mi?** Windows'ta anlamsiz;
  `if os.name == "nt": return` ile atlayin.
- **`posixpath.basename`** ters egik cizgiyi ayirici saymaz; `os.path` kullanin.
- **Konsol ciktilari ASCII olsun.** `.bat` icinde `chcp 65001` ve `PYTHONUTF8=1`
  var ama kisitli ortamlarda basarisiz olabilir.

## Adim 5 — Belgeler

Windows kullanicisi terminal kullanmaz; belgeler pakete girmeli.

`windows/KURULUM.txt` — ZIP'i "Tumunu Ayikla" ile acma (surukle-birak klasoru
eksik birakir), `kur.bat`, SmartScreen uyarisi, klasorun yazilabilir bir yerde
olmasi gerektigi (`C:\Program Files` olmaz — uygulama kendi klasorune yazar).

Mevcut bir kilavuzun platforma bagli bolumlerini degistirmek icin
`arac/belge_hazirla.py` kullanilir: parca dosyanin ilk satirindaki `##`
basligiyla eslesen bolumu degistirir, bulamazsa **durur** — boylece kilavuz
degistiginde uyarlama sessizce eskimez. Duz metinleri Not Defteri'nin dogru
actigi bicime (UTF-8 BOM + CRLF) de o cevirir.

## Adim 6 — Uret

```
./paketle.sh amd64
```

`paketle.sh` uretmekle kalmaz, **denetler**; bir kosul bozulursa paket vermez.
Denetimler:

- Linux'a ozgu dosyalar ve kullanici verisi sizmamis (`*.sh`, `*.db`,
  `__pycache__`, `.DS_Store`, `*.desktop`)
- Bulunmasi gereken dosyalar yerinde (modul listesini projeye gore duzenleyin)
- `.bat` dosyalari CRLF tasiyor
- Kilavuzda Linux anlatimi kalmamis
- Kodda ve belgelerde `http://127.0.0.1:` yok (proxy tuzagi)
- Sunucu `::1` dinliyor, `allow_reuse_address` kapali, Chrome onceligi var
- `.bat` dosyalarinda tirnaksiz `%PYEXE%` yok (bosluklu yolda kirilir)
- `::1` dinleyen kod "IPv6 yok" ile "port dolu"yu ayiriyor (`EADDRINUSE`);
  ayirmazsa butun portlar dolu gorunur
- Gomulu Python `._pth` dosyasi uygulama klasorlerini goruyor

Bu denetimler yontemin kalbidir: Windows'ta ancak kullanicida gorunen hatalari,
paket daha uretilirken yakalarlar. **Yeni bir kural ogrenildiginde buraya
denetim ekleyin.**

Gomulu Python `arac/onbellek/` altinda saklanir; ikinci uretimde ag gerekmez.
Bir kez indirdikten sonra o zip'i baska projeye kopyalayabilirsiniz.

## Adim 7 — Duman testi

Paket uzerinde, **dagitilacak klasorun kopyasinda** calistirin (test verisi
pakete bulasmasin). Sistem `python3`'unu kullanin; paketteki `python/` Windows
ikilisidir, macOS/Linux'ta calismaz.

Sunucu ayaga kalkiyor mu, ana akislar (veri girisi → hesap → cikti), kayit,
yedek. Sonra `find` ile paketin kirlenmedigini dogrulayin.

## Adim 8 — Gercek Windows testi

Bunu **siz yapamazsiniz**. Kullaniciya net bir liste verin ve dosya olarak da
birakin (`belge_hazirla.py --metin` ile UTF-8 BOM + CRLF'e cevirin — kullanici
Windows'ta sohbete erisemeyebilir).

Listede mutlaka olsun:

- Sayfa acildi mi, hangi tarayicida
- **Art arda iki dosya yukleme** (gecici dosya tuzagi burada ortaya cikar)
- Turkce karakterler dogru mu (arayuz + uretilen dosya adlari)
- Uygulama acikken **ikinci kez baslatma** → farkli port yazmali
- Kaydet → kapat → ac → veri duruyor mu

Sorun cikarsa ilk is `tani.bat`. Tahmin ettirmeyin: arac proxy'yi, IPv6'yi,
portu, eksik acilmis arsivi, yazma iznini ve Chrome politikasini sirayla dener,
sebebi adiyla soyler ve sonucu bir dosyaya yazar. Kullanici o dosyayi oldugu
gibi gonderir.

## Uyarlarken dikkat

- **Uretilen paket klasoru elle duzenlenmez.** Degisiklik kaynakta ya da
  `windows/` sablonlarinda yapilir, betik yeniden calistirilir. Aksi halde bir
  sonraki uretimde duzeltme kaybolur.
- **Kullanici verisi pakete girmez** — `*.db`, cikti dosyalari. Denetim bunu
  yakalar ama kaynakta da tutmayin.
- `.DS_Store` macOS'ta surekli yeniden dogar; `rsync --exclude` kalici cozum.
- Paket ~11 MB (gomulu Python ~24 MB acilmis). Flash diskle tasiniyorsa
  kopyaladiktan sonra `md5` dogrulayin ve diski duzgun cikarin.
