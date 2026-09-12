---
name: kdv-linux
description: >
  KDV Inceleme Calismasi uygulamasinda gelistirme yapar: sahte belge kullanma
  incelemesi icin KDV beyan hesabi tutan, fatura listesi okuyan, beyanname
  PDF'i ayristiran ve Word tutanak / rapor taslagi ureten yerel bir Python
  uygulamasi. Kullanici kdv_linux ya da kdv_windows agacinda calismak
  istediginde; beyanname okuma, fatura listesi, beyan tablosu, satici dokumu,
  tutanak, sahte belge raporu, duzeltme kabul raporu, Excel cikti, paketleme
  ya da "uygulamaya su ozelligi ekle" dediginde MUTLAKA bu skill'i kullan.
  Uygulamanin adini anmadan "beyannameyi okuyamiyor", "rapora su maddeyi
  ekle", "tutanakta su yazsin" dedigi durumlar da buraya girer. Skill,
  agactaki degismezleri ve sahada pahaliya ogrenilmis tuzaklari tasir.
---

# KDV Inceleme Calismasi — gelistirme

Bu uygulamayi bir vergi mufettisi gercek incelemelerde kullaniyor. Cikti resmi
bir belgeye donusuyor: tutanak imzalaniyor, rapor vergi dairesine gidiyor. Bu
yuzden buradaki en buyuk risk cokme degil, **sessizce yanlis sayi yazmaktir**.
Asagidaki kurallarin cogu bu tek cumleden turer.

Once `references/mimari.md` dosyasini okuyun; agacin nasil kuruldugunu ve
hangi modulun neye baktigini anlatir. Sahada kirilmis noktalar
`references/tuzaklar.md` icinde.

## Degismezler

Bunlar tartisma konusu degil; bozarsaniz ya kullanici acamaz ya da belgeye
yanlis bilgi girer.

**Iki agac ayridir, ortak kod `esitle.sh` ile tasinir.** `kdv_linux/` ve
`kdv_windows/` ayri koklerdir. Ortak olan `main.py`, `app/`, `web/`, `lib/`,
`lib_ek/`, `KULLANIM.md`; `app/tani.py` yalnizca Windows'ta bulunur. Duzeltmeyi
`kdv_linux/` icinde yapin, sonra kokten `./esitle.sh` calistirin,
`./esitle.sh --denetle` ile iki agacin ayni oldugunu dogrulayin. Tek agacta
birakilan duzeltme, digerinde sessizce eski davranis olarak yasar.

**Yalnizca standart kutuphane.** `openpyxl`, `pypdf` ve `et_xmlfile` `lib/`
icinde, `typing_extensions` `lib_ek/` icinde vendor'lanmistir. Yeni bir pip
bagimliligi eklemeyin: uygulama kurulum gerektirmeden, kurumsal bir makinede
cift tiklanarak calisiyor. Yeni bir ise ihtiyaciniz varsa once stdlib ile
yazmayi deneyin.

**Calisma verisi sunucuda tutulmaz.** Tarayici veriyi bellekte tasir, her
hesap icin sunucuya gonderir, sunucu yalnizca hesaplayip dondurur. Veritabanina
yazma ancak kullanici "Kaydet" dediginde olur. Sunucuya durum koymayin.

**Paketleyiciler yalnizca uretmez, DENETLER.** `paketle.sh` bir kosul
bozulursa paket vermez. Yeni bir kural ogrenildiginde oraya denetim eklenir.
Onemli olan kisim su: **yeni bir denetim yazdiginizda, korudugu seyi bilerek
bozup denetimin gercekten attigini gorun.** Bu oturumda bir denetim, test
verisindeki bir metin yanlis oldugu icin bozuk surumde bile geciyordu — yani
korudugunu sandigimiz seyi hic korumuyordu.

## Once calistirin, sonra degistirin

```
cd kdv_linux && ./calistir.sh          # tarayicida acilir
python3 testler/beyanname_testi.py     # beyanname okuyucusu gerileme denetimi
```

Uygulamayi acmadan bir sey degistirmek, bu agacta dusunulenden pahaliya mal
olur: hesap zinciri uzundur ve bir satirin yanlis okunmasi belgenin sonuna
kadar sessizce tasinir.

## Belge ureten kodu denemenin yolu

Tarayiciyi surmeden, `Istekci` sinifinin ucunu dogrudan cagirin. Bu, belge
uretimini uctan uca — kunye, hesap, satici dokumu, metin — calistirir:

```python
import sys; sys.path.insert(0, ".")
from app import web_server as W

h = W.Istekci.__new__(W.Istekci)          # __init__ calistirmadan
sonuc = W.Istekci._kabul_raporu_onizleme(h, {"calisma": calisma})
print(sonuc["metin"])
```

`calisma` sozlugunun bicimi `references/mimari.md` icinde ornekle anlatiliyor.
Fatura tarihlerinin **ISO** olmasi gerektigine dikkat edin (`2026-04-15`);
`15.04.2026` yazarsaniz kayit donemi cozulemez ve satici yil suzgecinden
dusup belgeden sessizce kaybolur. Gercek akista `fatura_oku` tarihleri zaten
ISO'ya cevirir — bu yalnizca elle kurulan test verisi icin bir tuzaktir.

## Beyanname okuyucusu

En kirilgan yer burasi, cunku girdi bizim denetimimizde degil: GIB ciktiyi
degistirdiginde alan adlari degisiyor. Iki bicim dolasimda ve okuyucu ikisini
de kabul ediyor (`pdf_beyanname`).

Yeni bicimde **tutari tumden sifir olan BOLUM basligiyla birlikte hic
basilmiyor**. Bu yuzden eksik bolum "okunamadi" degil "sifir" demek ve
okuyucu oyle davraniyor. Tehlike de burada: taninmayan bir alan adi da sifir
gorunur. 2026/Mayis beyannamesinde "Matrah Toplamı" adi "Toplam Matrah"
olunca 2.209.951,45 TL matrah sessizce 0,00 yazildi ve hicbir uyari cikmadi.

Bu yuzden `_denetle` icindeki aritmetik denetimleri ciddiye alin ve yeni bir
alan eklediginizde o alani baglayan bir esitlik varsa denetim de ekleyin.
Beyannamenin kendi aritmetigi, okumanin dogrulugunu ucretsiz ispatlar:

```
toplam KDV - indirimler = odenecek  ya da  devreden + iade
hesaplanan + ilave       = toplam KDV
devir + bu donem + diger = indirimler toplami
matrah 0 iken hesaplanan KDV 0'dan buyuk olamaz
```

Yeni bir beyanname bicimi geldiginde `testler/` icine ornek ekleyin. Oradaki
dokumler `(sayfa, x, y, metin)` bicimindedir — `_parcalar()` ne donuyorsa o —
ve `P._parcalar` yerine konarak okuyucu PDF olmadan bastan sona calistirilir.
Kisisel bilgi yerine konum korunarak ornek deger yazilir; **onemli olan metin
degil, konumdur.**

## Belgelerdeki hukuki ayrimlar

Bunlar kozmetik degil; sonucu degistirirler. Ayrintisi
`references/belge-kurallari.md` icinde, ama ozu:

- **Kurum / gercek kisi:** "mukellef kurum" mu "mukellef" mi, Kurumlar
  Vergisi mi Gelir Vergisi mi.
- **Bilerek / bilmeden kullanma:** duzeltme kabul raporunda bu ayrim belgenin
  TURUNU degistirir — bilmeden ise Vergi Teknigi Raporu, bilerek ise Vergi
  Inceleme Raporu.
- **Duzeltmeyle cikarilmis satici:** faturalarin tamami duzeltme
  beyannamesiyle indirimlerden cikarilmissa tarh edilecek vergi kalmaz.
- **Cezanin matrahi**, faturalardaki KDV toplami DEGILDIR: duzeltme once
  devreden KDV'yi eritir, vergi ziyai ancak devir tukendikten sonra dogar.

Bilinmeyen bir tutar icin sayi uydurmayin; belge uretecinde **kirmizi yer
tutucu** birakin (`belge_docx.YER_TUTUCU_RENGI`). Mufettis kirmiziyi gorup
doldurur; sessiz bir sifir ise fark edilmez.

## Kullaniciyla calisma bicimi

Kullanici vergi mufettisidir, yazilimci degildir. Hukuki bir soruda karari o
verir — siz secenekleri ve sonuclarini gosterin, yerine karar vermeyin.

Verilmis kararlar `kdv_linux/GELISTIRME_NOTLARI.md` icinde "Verilmis kararlar
(yeniden acmayin)" basligi altinda durur. Bir konuyu yeniden acmadan once
oraya bakin; orada gerekcesiyle kapanmis tartismalar var.

Ayni dosya projenin hafizasidir: yaptiginiz isi ve **neden** oyle yaptiginizi
oraya yazin. Sohbet kapandiginda kalan tek sey odur.

## Paketleme

```
cd kdv_linux  && ./paketle.sh                 # .tar.gz  (zip calistirma iznini korumaz)
cd kdv_windows && ./paketle.sh                # .zip, gomulu Python ile
cd kdv_windows && ./guncelleme_paketle.sh     # kurulu uygulamanin uzerine giden kucuk paket
```

Windows tarafinda `.bat` dosyalari CRLF, kullaniciya okutulan `.txt` dosyalari
CRLF **ve UTF-8 BOM'lu** olmali — BOM'suz bir dosyayi eski Notepad ANSI sanar
ve Turkce harfler bozulur. Bunlarin hepsi paketleyicide denetlenir; denetim
attiginda duzeltmeyi **kaynakta** yapin, pakette degil.
