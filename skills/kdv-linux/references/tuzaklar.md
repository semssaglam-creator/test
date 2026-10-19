# Sahada kirilmis noktalar

Hepsi gercek arizalardir. Cogunun ortak ozelligi su: uygulama calisiyordu,
kullanicida calismiyordu — ya da daha kotusu, calisiyor gorunup yanlis sayi
yaziyordu.

## 0. Elle eklenen saticinin fatura satiri YOKTUR

Rapor yil yil yazilirken `_yila_indirge` fatura listesini daraltir. Elle
eklenen satici (`elle: "Evet"`) bu daraltmadan GECMEZ, cunku listede hic
satiri yoktur; yilini kendi kaydinda (`elle_yil`) tasir. `satici_ozeti`'ye
`yil` vermeyi unutursaniz satici BUTUN yillarin raporunda gorunur — sahada
boyle cikti. Yil cikaran her hesap icin ayni tuzak gecerli;
`bilerek_yillari` de bu yuzden elle saticilara ayrica bakar.

Yil girilmemisse satici her yilda gorunmeye devam eder. Sessizce dusurmek
mufettisin farketmeyecegi bir veri kaybi olurdu.

## 0b. Unvanlar belgede Turkce kucultmeden gecer

Denetim yazarken Turkce'ye ozgu harf TASIMAYAN bir unvan secin: "YILSIZ"
belgede "yılsız" olur ve `"yilsiz" in metin` tutmaz. "ELLE-X" gibi notr bir
ad kullanin. Bu tuzak bir kez yanlis olcume yol acti: duzeltmenin
gerilemeye sebep oldugu sanildi, oysa yalnizca arama tutmuyordu.

## 1. Sessiz sifir (en tehlikelisi)

Yeni beyanname bicimi, tutari tumden sifir olan BOLUMU basligiyla birlikte
hic basmiyor. Okuyucu bu yuzden eksik bolumu "sifir" sayiyor
(`YENI_BICIM_SIFIRLAR`) — dogru davranis. Ama taninmayan bir alan adi da ayni
sekilde sifir gorunur.

Sahada boyle cikti: "Matrah Toplamı" adi yeni bicimde "Toplam Matrah" oldu,
esleme tutmadi, 2.209.951,45 TL matrah **0,00 yazildi ve hicbir uyari
cikmadi**. Beyannamenin kendi aritmetigi bunu yakalamiyordu, cunku matrahi
baglayan bir esitlik denetlenmiyordu.

Ders: sifirla doldurma, okunamayan alani gizler. Her yeni alan icin "bu alan
neyle tutmali" sorusunu sorun ve tutuyorsa `_denetle`ye yazin. Simdi
"matrahsiz hesaplanan KDV olmaz" denetimi var.

## 2. Yerine gore saga yasli degerler

Beyannamedeki deger satirlari sola degil SAGA yasli olabiliyor. Unvan iki
satira tastiginda ikinci satir birincinin cok saginda basliyor (x 312.6 ->
377.6) ve sola hizaya bakan bir kural onu eliyor — unvanin yarisi belgeye
gitmiyordu.

Dogru olcut hiza degil: **bandin ETIKET sutunu bossa o satir devamdir.**

## 3. Devam satiri nerede biter

Bir alanin devamini toplarken durmayi bilmek gerekiyor. Duzeltme aciklamasi
uc satira tastiginda, 24 punto asagidaki kunye sutun basliklari satir
araligina giriyor ve aciklamaya karisiyordu ("... CIKARILMISTIR Beyannamenin
Hangi Sifatla Verildigi"). "Beyanname..." ile baslayan parcalar bu yuzden
durdurucu sayiliyor.

## 4. Port bulunamadi — duzeltmenin actigi ariza

`localhost` Windows'ta once `::1`'e cozulur, bu yuzden sunucu cift dinler.
Ama "IPv6 yok" ile "port dolu" AYRILMAZSA, `::1`'e baglanamayan bir makinede
butun portlar dolu gorunur ve uygulama "Uygun port bulunamadi (8766-8775
dolu)" deyip kapanir.

```python
except OSError as hata:
    if hata.errno == errno.EADDRINUSE:   # gercekten dolu
        raise
    sunucular = []                       # IPv6 yok; yalniz IPv4 ile devam
```

Bu, bir tuzagi kapatan duzeltmenin kendisinin actigi bir arizaydi. Yeni bir
dinleme yolu eklerken hata kodlarini ayirin. Paketleyici bunu denetler.

## 5. Proxy tuzagi: `localhost` mu `127.0.0.1` mi

Windows'un "yerel adresler icin proxy kullanma" ayari yalnizca NOKTASIZ
adlari kapsar. `127.0.0.1` kurumsal proxy'ye gider; sunucu sorunsuz calisirken
kullanici "sayfaya ulasilamadi" gorur. Kullaniciya gosterilen her adres
`localhost` olmali. Paketleyici `http://127.0.0.1:` gecen dosya arar.

Tek istisna `app/tani.py`: o, iki adresi bilerek karsilastirir.

## 6. Bosluklu yol ve tirnak

Klasor adi "KDV Inceleme Calismasi" — icinde bosluk var. `.bat` icinde
tirnaksiz bir degisken cmd tarafindan ilk boslukta kesilir. Sahada boyle
kirildi. Ayrica Python cagrisi bazen `py -3` gibi iki parcali oldugu icin
yalnizca tirnak da yetmez; bu yuzden `PYEXE` ve `PYARG` ayri tutulur ve cagri
her zaman `"%PYEXE%" %PYARG% main.py` bicimindedir.

## 7. UTF-8 BOM

Kullaniciya okutulan `.txt` dosyalari CRLF **ve BOM'lu** olmali. BOM'suz bir
dosyayi eski Notepad ANSI sanar, Turkce harfler bozulur ve kullanici kilavuzu
okuyamaz. Paketleyici denetler.

## 8. Windows acik dosyayi kilitler

Gecici dosyaya yazip okumayin; okuyucular akis (`io.BytesIO`) kabul ediyor.
Sabit adli bir gecici dosya, art arda iki yuklemede
`PermissionError: [WinError 32]` verir — virus tarayicilar da yeni yazilan
dosyayi kisa sure acik tutar.

## 9. Linux paketi `.tar.gz` olmali

`zip` calistirma iznini her arsivleyicide korumaz. `calistir.sh`
calistirilamaz halde acilirsa uygulama "hic acilmiyor" gorunur — masaustu
kisayolu hicbir sey yazmadan basarisiz olur. `tar` bu bilgiyi her zaman tasir.

## 10. Test verisinin kendisi yanlis olabilir

Bir denetim yazdiginizda korudugu seyi **bilerek bozup** denetimin attigini
gorun. Bu oturumda bir denetim, fixture'daki bir metin tahminle yazildigi icin
bozuk surumde bile geciyordu: korudugunu sandigimiz seyi hic korumuyordu.
Gercek metin ogrenilince denetim atmaya basladi.

Gecen bir test, gecmesi gerektigi icin mi geciyor — bunu ancak bozarak
anlarsiniz.

## 11. Fatura yonu: tek tarafli dokum ve TAHMIN edilen VKN

`faturalar.normalize` yonu VKN karsilastirmasiyla bulur. Iki tuzak var ve
ikisi de sessiz yanlis sayi uretir:

**Tek tarafli dokum.** Dokumde yalnizca duzenleyen sutunu varsa (mukellefin
KENDI duzenledigi belgelerin dokumu cogu zaman boyle) eskiden VKN'ye hic
bakilmadan ALIS yaziliyordu. Boylece `satis_donem_toplamlari` bos donuyor ve
ibraz etmemede matrah ilavesi hic yapilmiyordu — kullaniciya "matrahlar
yukseltildi" denerek.

**Tahmin edilen VKN.** `_ortak_vkn`, butun satirlarda tekrar eden VKN'yi
mukellef sayar. Tek tarafli dokumde buna GUVENILMEZ: tek saticili bir alis
listesinin saticisi her satirda tekrar eder, "mukellef" sanilir ve butun
liste SATISA doner — indirimler bir anda yok olur. Tek tarafli dokumde
yalnizca calismaya ACIKCA girilmis VKN kullanilir.

Yon mantigina dokunuyorsaniz `ibraz_etmeme_testi.py` 0. bolumundeki sekiz
durumu calistirin; ikisi tam bu iki tuzagi tutuyor.

## 12. Paketi uretmek, kullaniciya ULASTIRMAK demek degildir

`surumler/` klasoru indirme baglantilarini tasir ve eskiden paketleyiciden
oraya kopyalama ELLE yapiliyordu. Bir oturumda bu adim atlandi: paketleyici
uc kez calistirildi, her seferinde kullaniciya `surumler/` icindeki
HAFTALAR ONCEKI dosya gonderildi ve butun degisiklikler "yapilmamis"
gorundu. Kullanici "yine ayni uygulama geliyor" dedi; sorun koddaki
degisiklikte degil, teslimdeydi.

Artik paketleyiciler `surumler/`e kendileri kopyaliyor. Kullaniciya dosya
gonderirken yine de uretim zamanina bakin: `ls -la surumler/`.

Ayni ailenin ikinci tuzagi: her paket `surum.txt` tasir (tarih + git kisa
kimligi) ve uygulama bunu sag ustte gosterir. "Guncelledim ama ayni
uygulama geliyor" sorusunu ancak bu cevapliyor, cunku uygulamanin onceki
bir kopyasi 8766'yi tutuyorsa yeni kopya 8767'ye kayar ve tarayicidaki
eski adres ESKI surumu gostermeye devam eder. `main.py` bu kaymayi artik
yuksek sesle yaziyor, rozet de portu gosteriyor.

Ucuncusu: `guncelle.bat`in kopyalama sonrasi denetimi yillardir kaynakta
duran bir metni ariyordu; o metin ESKI surumde de bulundugundu icin
kopyalama hic olmasa bile "GUNCELLEME TAMAM" diyordu. Olcut artik surum
damgasinin BIREBIR esitligi. (Bkz. 10: gecen bir denetim, gecmesi
gerektigi icin mi geciyor?)
