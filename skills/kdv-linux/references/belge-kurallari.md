# Belge kurallari

Tutanak ve rapor ureten kodu degistirirken bilinmesi gerekenler. Bunlar
bicimsel tercih degil; yanlisi belgeyi hukuken hatali yapar.

## Sonucu degistiren ayrimlar

**Kurum / gercek kisi** (`kunye.mukellef_turu`). Kurumda "mukellef kurum"
denir ve Kurumlar Vergisi / Kurum Gecici Vergisi yazilir; gercek kiside
"mukellef" denir ve Gelir Vergisi / Gecici Vergi yazilir. `inceleme_kunyesi`
icindeki `mukellef_sozu`, `gelir_vergisi_adi`, `gecici_vergi_adi` bunu
yonetir — bu adlari elle yazmayin, fonksiyondan alin.

**Bilerek / bilmeden kullanma** (`satici.kullanma`). 306 Sira No'lu VUK Genel
Tebligi'ne dayanir. Bilmeden kullanmada kasit unsuru olusmaz, VUK 359
kapsaminda islem yapilmaz. Bilerek kullanmada vergi sucu raporu duzenlenir ve
suc duyurusunda bulunulur.

**Duzeltmeyle cikarilmis fatura** (fatura satirinda `duzeltme_cikarildi`).
Isaret FATURA BASINADIR, satici basina degil: mukellef ayni saticinin bir
yildaki faturalarini duzeltme beyannamesiyle indirimlerden cikarip diger
yildakileri cikarmis olmayabilir ve vergilendirme hesap donemi bazinda
yapildigindan bu ayrim tarhiyati dogrudan degistirir (sahada boyle cikti,
2026-10-23). Olcut `faturalar.fatura_duzeltildi_mi`; eski calismalarda
isaret satici kaydinda (`duzeltme_ile_cikarildi`) duruyor olabilir ve orasi
"butun faturalari" demektir — ekran acilista isareti faturalara tasir.
Fatura listesi bulunmayan ELLE eklenen saticilarda isaret satici kaydinda
kalir; tasiyacak fatura satiri yoktur.

**Kayda alinmamis satici** (`kayda_alinmadi`) satici duzeyindedir; fatura
basina karsiligi "deftere kaydedildi" tikidir.

Faturalarin tamami boyleyse reddedilecek indirim zaten beyanda degildir:
tarh edilecek vergi kalmaz. `faturalar.duzeltme_kabul_uygun_mu` bunu
satici satirindaki `kdv` (= tarhiyata giren) uzerinden denetler.

Satici ozetindeki uc takim karistirilmamali:
`adet/matrah/kdv/toplam` tarhiyata GIRENLER (`sayilir`), `duz_*`
duzeltmeyle cikarilanlar, `liste_*` listedeki butun faturalar.

## Duzeltme kabul raporu — belgenin TURU degisir

Faturalarin tamami duzeltmeyle cikarilmis ya da hic kayda alinmamissa tarh
edilecek vergi iki halde de yoktur, ama duzenlenecek belge farklidir:

| Kullanma | Belge | Sonuc |
|---|---|---|
| Bilmeden | **Vergi Teknigi Raporu** | Vergi de ceza da yok |
| Bilerek | **Vergi Inceleme Raporu** | Tarhiyat yok; yarim kat cezanin uc kata tamamlanmasi istenir; vergi sucu raporu |

Baslik ve dosya adi da tura gore degisir (`belge_turu`, `dosya_adi`).

## Satici bolumu YIL YIL ayrilir

Vergilendirme hesap donemi bazinda yapildigindan, ayni saticidan farkli
yillarda alinan belgeler tek tabloda toplanmaz. Tutanakta madde TEKtir
(tespit ayni tespittir), ama govdesi yil yil bloklanir: her yil icin giris
paragrafi, kendi tablosu ve o yila ait tespitler — defter/beyan durumu,
muhasebe kaydi, iptal/itiraz kaydi, duzeltme dokumu
(`tutanak._satici_yil_bloklari`). Rapor zaten yil yil yazildigindan orada
blok cogu zaman tektir, ama ayni uretec kullanilir
(`satici_fatura_tablosu`, `defter_beyan_paragraflari`).

Iki kural:

- **Tek yilda cikti degismez.** Yil giris paragrafi yalnizca birden fazla
  yil varsa yazilir; maddenin Ba-Bs cumlesi zaten yili ve tutari soyluyor.
- **Sira numaralari bloklar boyunca kesintisiz ilerler** (2021 tablosu 1-3,
  2022 tablosu 4-7). Her tabloda 1'den baslamak, "2 sira numarali belge"
  diyen paragraflari iki tablo arasinda belirsiz birakirdi.

Her tablonun TOPLAM satiri KENDI satirlarindan kurulur; satici ozetindeki
`liste_*` takimi bir blogun toplami degildir.

## Iki ozel usulsuzluk fiili ayridir

Raporun II/A bolumunde iki ayri fiil yan yana durabilir; karistirmayin:

| Fiil | Madde | Oran | Olcut |
|---|---|---|---|
| Odemeyi banka/PTT belgesiyle tevsik etmeme | muk. 355 | %5 | Fatura satirinda "tevsik edilmemis" tiki |
| Gercek faturayi hic almama | 353/1 | %10 | "Dahil" birakilan + hakkinda VTR bulunan saticidan alinan faturalarin TAMAMI |

353/1'in olcutu **tarhiyata BAKMAZ**: tutar duzeltme beyannamesiyle
indirimlerden cikarilmis olsa bile gercek fatura alinmamis olmasi degismez.
Bu yuzden `sayilir` KULLANILMAZ — kullanilsaydi duzeltmeli dosyalarda kume
bosalirdi.

**Bilerek / bilmeden ayrimi KODA GOMULMEZ.** 353/1 kasit aramayan nesnel bir
fiildir ve kanun bu ayrimi yapmaz; dolayisiyla ayrim mufettisin tercihidir ve
kunyeden gelir (`belge_alma_kapsami`, varsayilan "yalnizca bilerek"). Ayrim
satici satici uygulanir, yil butunuyle elenmez. Ayrica kapsam seciminden
BAGIMSIZ bir "haric tutulacak yillar" alani var (`ouc353_haric_yillar`):
zamanasimi gibi baska gerekceler icin.

Ceza orani kanunda yazili oldugu icin sabit; **alt ve ust sinirlar kunyeden
TARIH ARALIKLI alinir** (`belge_alma_hadleri`). Yil bazli tek bir alan
yetmez: 2022'de 7417 sayili Kanunla sinirlar yil ICINDE degisti. Bir
faturanin tarihi hicbir had satirina denk gelmezse cezasi UYDURULMAZ; satir
`had_yok` ile isaretlenir ve belgede kirmizi yer tutucu kalir.

Hadleri okurken `paste_parser.tutar_coz` KULLANILMAZ: "1.000" ve "190.000"i
1,0 ve 190,0 diye okur. `inceleme_kunyesi._had_tutari` bunun icin var.

## Devir zinciri incelenen yillarin OTESINE gecer

Bir yilin indirimleri reddedildiginde o yilin Aralik devri kuculur ve devir
ILERIYE akar. Mufettis sonraki yillari da calismaya ekler (devirin ne kadar
etkilendigini gormek icin); kucuk devirle yeniden kurulan zincirde bir
donemde odenecek vergi dogarsa o yil icin **devir duzeltme raporu**
duzenlenir (`devir_duzeltme_raporu.py`), sahte belge kullanma raporu degil.
O yillar `sahte_belge_raporu.rapor_yillari`'ndan cikarilir; aksi halde ayni
yil icin iki belge uretilir.

Yil secimi uc kosul arar ve ucu de gerekli: (1) o yilda sahte belge yok,
(2) onunden gelen devir GERCEKTEN degismis, (3) o yilda fark var. Ikinci
kosul olmadan, mufettisin o yila girdigi bir matrah ilavesinden dogan fark
da bu raporu tetiklerdi - oysa o halde yazilacak belge bu DEGILDIR.

Raporun en islevsel maddesi sonuc bolumunun "sonraki yilin Ocak devri vergi
dairesince duzeltilsin" maddesidir; zincir boylece elle devam ettirilir.
Yeni bir yil raporu eklerseniz bu maddeyi atlamayin.

## Ibraz etmeme: indirimin TAMAMI reddedilir

**Re'sen takdir nedeni iki benttir ve ikisinin DELILI ayridir:** ibraz
etmeme VUK 30/3'tur; duzenlenen belgelerin bir kismi beyannamelere
yansitilmamissa bu, "verilen beyannamelerin gercek durumu yansitmadigina
dair delil" oldugundan ayrica 30/6'dir. 30/6 yalnizca matrah ilavesi
yapilan dosyalarda anilir - delil yokken o bende dayanmak raporu itiraz
edilebilir kilar (`_resen_dayanagi`).

Defter ve belgeler ibraz edilmediginde beyan edilen indirilecek KDV'nin
KDVK 29 ve 34 geregince indirilebilirligi denetlenemez; indirimlerin tamami
reddedilir ve fark KDV VUK 30/3 uyarinca re'sen tarh edilir. Hesap motoru
bu hali zaten taniyor (`tam_ret`): `indirim_cikar` beyan edilen "bu donem
indirilecek KDV"ye esitlendiginde yurtici alim siniri uygulanmaz.

Hesabi RAPOR DEGIL `hesap.ibraz_etmeme_elestirisi` kurar ve elestiri
alanlarina yazar; boylece tutanak, Excel ve sonuc bolumu ayni rakamlari
gorur. Yeni bir rapor eklerken ayni yolu izleyin - rapor kendi rakamini
hesaplarsa belgeler birbirini tutmaz.

**Olcut "hesaplanan KDV" DEGIL, beyannamenin TOPLAM KDV satiridir**
(= hesaplanan + ilave edilecek). Hesapta `max(toplam_kdv, hesaplanan +
ilave_edilecek)` alinir: yeni beyanname biciminde tutari sifir olan bolum
hic basilmadigindan okunamayan bir satir sessizce sifir gorunur.
Mukellef matrahi hic beyan etmeden
faturanin KDV'sini "Ilave Edilecek KDV" satirinda beyan etmis olabilir;
yalnizca hesaplanan ile karsilastirmak ayni vergiyi iki kez tarh ettirir.
Beyan dokumu tablosu da ilave edilecek KDV tasidiginda o sutunu yazar -
yoksa tablo kendi icinde tutmaz ve hata gorunmez kalir (sahada boyle
cikti, 2026-10-20).

**KDV'si SIFIR belgeler beyan disi olmayabilir.** Matrah karsilastirmasi
beyannamenin "MATRAH TOPLAMI" satirina bakar; istisna kapsamindaki
teslimler ve OZEL MATRAH sekline tabi islemler o satirda YER ALMAZ, ayri
bolumlerde beyan edilir. Bu yuzden KDV'si sifir bir belge "beyan
edilmemis" gibi gorunur. Uygulama bunlari ayri sayip (`kdvsiz_adet`,
`kdvsiz_matrah`) beyannamenin istisna / ozel matrah bolumleriyle
karsilastirir ve UYARIR; otomatik cikarmaz, cunku hangi belgenin hangi
istisnaya girdigi belge bazinda bilinmez - karar mufettisindir. RAPOR da
susmaz: 4.2.4'te tutarlar, beyannamedeki karsiligi ve varsa acikta kalan
kisim yazilir; ayrica bu tutarlar uzerinden hesaplanan KDV'ye ilave
YAPILMADIGI belirtilir.

**Matrah kurali:** beyan ile mukellefin DUZENLEDIGI faturalarin toplami
uyusmadiginda VUK 3/B geregi gercek durum esas alinir, ama yalnizca
mukellef ALEYHINE olan yonde. Faturalar beyandan azsa beyan esas alinir.
Hesaplanan KDV farki faturalarin kendi KDV'sinden gelir, orana BOLUNMEZ:
dokumde sifir KDV'li satirlar bulunabiliyor.

**Ilavenin dayanagi VUK DEGIL, KDV Kanunudur** (mufettisin karari,
2026-10-19). Zincir: 1/1 verginin konusu -> 2 ve 3 teslim ve teslim
sayilan haller -> 20 matrah -> **10/b** teslimden once fatura verilmisse
BELGEDE GOSTERILEN MIKTARLA SINIRLI olmak uzere faturanin duzenlenmesi
aninda vergiyi doguran olay dogar -> **8/2** vergiye tabi islem olmasa
DAHI vesikada KDV gosteren o vergiyi odemekle mukelleftir -> 40 beyan
esasi. Kisacasi: fatura duzenlendiyse vergi dogmus, faturada KDV
hesaplandiysa beyan zorunlu hale gelmistir. VUK 3/B'yi buraya dayanak
yapmayin.

Bu kural raporda yalnizca madde atfiyla gecistirilmez: 4.2.4 tespiti,
yukaridaki olcutu, yontemi (donem donem, yalnizca aleyhe; beyandan asagi
inilmez cunku dokum teslimlerin tamamini kapsamayabilir) ve donem donem
karsilastirma tablosunu yazar. Tarhiyatin en tartismali kalemi budur;
gerekce yazilmazsa itiraz edilebilir kalir.

**Alis ve satis AYRI yerlere gider:** alinan faturalar indirime, duzenlenen
faturalar matraha. Arayuzde liste yon kulakciklariyla ayrilir ve "indirim
reddine aktar" yalnizca ALIS kulaginda cikar; satis kulaginda matrah
karsilastirmasi gorunur, orada aktarim dugmesi YOKTUR (matrah ilavesini
ibraz etmeme kurali yazar, ikinci bir yol rakamlari ayristirirdi).

Fiil ayni zamanda VUK 359/a-2'de kacakcilik sucudur: ceza uc kat ve VSR de
uretilir. Ibraz etmeme VSR'sinin YAPISI sahte belgeden farklidir (dort
bolum, tespitler bolumu ve tarhiyat tablosu yok).

Ibraz etmeme VSR'sinin maddi unsuru, sahte belge VSR'si gibi somut DELIL
zincirine baglanir ("Fiile Iliskin Tespit ve Deliller", bes madde):
varlik (tasdik/basim kayitlari) -> usulune uygun isteme (yazi, teblig,
sure) -> defterlere kaydi GEREKEN islemlerin bulundugu (GIB belge dokumu;
sahte belgede bu yeri defter kayitlari tutuyor, burada defter YOK) ->
mucbir sebep bulunmadigi (VUK 13) -> netice (indirimlerin reddi ve ziya,
ibraz etmeme raporuna ATFEN - VSR tarhiyat onermez).

Gizleme fiilinin maddi unsuru, defter ve belgelerin VAR oldugunun ortaya
konmasina dayanir: defterleri noter tasdik tablosu (`defter_bilgileri`),
belgeleri anlasmali matbaa basim tablosu (`belge_basim_bilgileri`)
gosterir. Basim tablosu **yalnizca satir girilmisse** yazilir
(`ibraz_etmeme_raporu.belge_basim_tablosu`, hem rapor hem VSR ayni yeri
cagirir) — e-belgeye gecmis mukellefte bu kayit hic bulunmadigi icin
kirmizi yer tutucu konmaz. Ayni olcut kunyeye bagli her istege dair
kuraldir: **her mukellefte bulunmayan bir veride yer tutucu birakmayin,
veri yokken o cumleyi hic kurmayin.**

## Vergi Suclari Raporu (VSR) — ayri belge, elle istenmez

VUK 359 kapsamindaki fiil tespit edildiginde, tarhiyat oneren rapordan AYRI
bir vergi suclari raporu duzenlenir ve VUK 367 geregince Rapor
Degerlendirme Komisyonunun mutalaasiyla savciliga bildirilir.
`vergi_sucu_raporu.py` bunu uretir. Iki seyi karistirmayin:

- VSR **tarhiyat onermez.** Onerilen tarhiyat ebeveyn rapordadir; VSR onu
  yalnizca V. bolumdeki tabloda anar (etkin pismanlik, VUK gecici 34).
- VSR **ayri istenmez.** Sahte belge raporu ya da duzeltme kabul raporu
  indirilirken, `gerekli_mi(calisma)` dogru donuyorsa uretilip ayni pakete
  konur. Yeni bir rapor turu eklerseniz ayni seyi yapin; mufettisin ikinci
  bir dugmeye basmasi gerekmesin.
- VSR **yalnizca BILEREK kullanma olan yillara iliskindir.** Dort yilin
  ucunde bilerek, birinde bilmeden kullanma varsa o dorduncu yil raporda HIC
  anilmaz: ne cumlelerde ne V. bolumdeki tabloda (`bilerek_yillari`).
- **3.2'deki oran da yalnizca bilerek kullanilan belgelerden kurulur.** Oran
  orada KASTIN delilidir; bilmeden kullanilan tutari paya katmak, kasit
  kurulmayan bir rakamla kasit kanitlamak olur. `sahte_belge_orani` ve
  `duzeltme_kabul_orani` bunun icin `vkn_suzgeci` alir.
- VSR **butun inceleme donemi icin TEK duzenlenir**, tarhiyat raporu gibi
  yil yil DEGIL. Yillar raporun icinde: atiflar cogullasir ve V. bolumdeki
  tablo her yil icin bir satir acar. Her satirin vergi/ceza tutari O YILIN
  verisinden hesaplanir (`_yil_tutarlari`); dosya toplamini her satira
  yazmak cezayi yil sayisi kadar buyutur. Kunyedeki "Tarhiyat oneren
  rapor(lar)" alani bu yuzden yil-tarih-sayi satir tablosudur.

**Fail**, kurumlarda kanuni temsilci, gercek kiside mukellefin kendisidir
(`suc_duyurusu_hedefi`). Hapis cezasi tuzel kisiye uygulanamaz; "mukellef
hakkinda ceza" yazmak faili yanlis gosterir.

**Duzeltme kabul halinde** tutarlar farklidir: tarh edilecek vergi 0,00,
ceza ise duzeltme uzerine kesilen yarim katin uc kata tamamlanmis hali.
`rapor_uret(..., kabul={"ziya": tutar})` bu hali kurar.

**359/a (defter-belge gizleme) madde metni kirmizi yer tutucudur** ve bu
KASITLIDIR: bendin dogrulanmis metni elde yok, uydurulmadi. Birincil
kaynaktan dogrulanmadan yazmayin.

## Vergi ziyai cezasi tarhin TAMAMI uzerinden

Ceza, re'sen tarh edilecek tutarin tamami uzerinden hesaplanir. Daha once
yalnizca sahte belgeye atfedilebilen kisim (`min(tarh, reddedilen KDV)`)
cezalandiriliyordu ve tarhiyatin baska bir tespitten gelen kismi cezasiz
kaliyordu.

Tutar kaynagina gore uce ayrilir, cunku ceza kati KAYNAGA baglidir:

1. Donemin kendi sahte belgesi -> o donemin kategori karmasi
2. **Devir zincirinden gelen kisim** -> dosya genelindeki karma. Sahte
   belgenin KDV'si indirimlerden cikarilinca devreden KDV de azalir; devir
   reddi bir ay sogurup vergiyi sonraki aya tasidiginda o ayda reddedilen
   belge bulunmasa bile fark AYNI fiilden dogar ve ayni kati tasir. Olcut
   hesap motorunun kendi ayristirmasidir: `fark_devir["odenecek"]`.
2b. **Tespitten gelen kisim** (`fark_tespit["odenecek"]`) -> yine dosya
   genelindeki karma. Ceza kati FATURA SATIRINA baglanamaz: fatura dokumu
   her donemi kapsamiyor olabilir, mufettis indirim reddini beyandan
   okuyup elle girdiginde o donemde satir bulunmaz. Bu tutar eskiden
   "dayanaksiz" sayilip bir kat yaziliyordu ve rapor metni uc kat derken
   tablo bir kat gosteriyordu (mufettisin duzeltmesi, 2026-10-19).
3. Kalan -> 359 fiili degil, bir kat. Buraya artik yalnizca beyan hatasi
   ve MATRAH ILAVESI dusuyor; ikincisinin olcutu
   `fark_tespit["toplam_kdv"]`dir (matrah/hesaplanan KDV ilavesi), kalani
   indirim reddi sayilir.
   `pay_dayanaksiz` / `ceza_dayanaksiz` diye AYRI kalemde tutulur,
   `pay_belirsiz`e karistirilmaz: "belirsiz" kullanma durumu SECILMEMIS
   saticilari isaret eder ve rapor bunun icin uyari yazar; karistirilirsa
   uyari yersiz cikar.

Devir zinciri yuzunden fatura bulunmayan bir donem de uc kat tasiyabilir;
rapordaki aciklama paragrafi bunu gerekcelendirir. Kaldirmayin.

Ceza tablosunda matrah sutunu YOKTUR (sadece tarh + kat basina ceza).
`pay_*` alanlari veride durur, cunku uzlasma kapsami ayrimi onlardan
beslenir: `pay_bilerek` kapsam disi, digerleri kapsam ici.

## Cezanin matrahi

Faturalardaki KDV toplami **degildir**. Duzeltme indirimi cikarir, ama
cikarilan indirim once devreden KDV'yi eritir; odenecek vergi ancak devir
tukendikten sonra dogar. Yalnizca devri eriten bir duzeltmede ziya YOKTUR ve
vergi dairesince ceza da kesilmemistir.

`beyannameler.duzeltmeyle_dogan_vergi()` bunu duzeltme zincirini adim adim
gezerek toplar — ilk/son karsilastirmasiyla degil, cunku ayni doneme birden
cok duzeltme verilmisse her adimda dogan vergi ayri ayri tahakkuk eder.

Uc hal ayri cumle gerektirir ve ucu de yazilidir:

- **bilinmiyor** (beyanname yuklenmemis) -> kirmizi yer tutucu
- **ziya yok** (yalnizca devir eridi) -> tamamlanacak ceza yok
- **ziya var** -> tutarlar yazilir

## Ceza kati KAYNAGA gore degisir

Tek bir dosyada iki kat birlikte bulunabilir (mufettisin karari,
2026-10-19):

- matrah farkindan (beyan disi birakilan belgelerden) dogan tutar -> 359'da
  yazili bir fiile dayanmaz, 344/1 geregi BIR kat
- indirimlerin reddinden (defter-belge ibraz etmemekten) dogan tutar ->
  359/a-2 kacakcilik sucu, 344/2 geregi UC kat

Ayrim MOTORDA yapilir (`hesap._tarhiyat_satiri`, `matrah_kati`); rapor
yalnizca yazar. Ikinci bir yerde hesaplamayin: ekran, Excel ve rapor ayni
alanlardan okuyor (`ceza_matrah_payi`, `ceza_indirim_payi`, `ceza_matrah`,
`ceza_indirim`, toplam `vergi_ziyai_cezasi`). Olcut toplam KDV'deki
ARTISTIR; pay once matraha verilir, cunku devir tarhin bir kismini
sogurdugunda dusuk kati uygulamak mukellef lehinedir.

Ibraz etmeme raporunda ceza kendi bolumundedir ve tablo kaynak paylarini
ayri sutunlarda gosterir. Matrah payi hic yoksa tablo daralir ve tek
cumle yazilir.

## Ceza katinin kaynagi: tespitler

Kat iki yerde belirleniyordu ve biri sessizce yaniliyordu: ceza tablosu
satici siniflandirmasindan, tarhiyat tablosu ise Tarhiyat Ozeti
sekmesindeki acilir kutudan (varsayilani BIR KAT). Rapor metni uc kat
derken tablo bir kat yaziyordu.

`web_server._ziya_kati` artik, calismada ACIKCA 1 ya da 3 secilmemisse
kati TURETIR (`_ziya_kati_turet`):

- satici "Bilerek kullanma" -> 359/b -> uc kat
- kunye "Defter ve belge ibrazi = Ibraz edilmedi" -> 359/a-2 -> uc kat
- aksi halde bir kat

Mufettisin elle secimi her zaman ustundur ama celiski ekranda kirmizi
yazilir. `/api/hesapla` yaniti `ziya_kati` ve `ziya_kati_turetilen`
tasir; yeni bir ceza kaynagi eklerseniz ikisini de besleyin.

Ibraz etmeme de 359 kapsamindadir: satici nitelendirmesi hic olmasa bile
uc kat. `ceza_dagilimi`in `dayanaksiz_kat` parametresi bunun icindir.

## Verilmis karar: uc kat

Ceza UC KAT olarak kodlanir. Farkli bir durum cikarsa mufettis raporu elle
duzeltir; uygulamaya secim eklenmeyecek. Elle duzeltmeyi gerektiren haller
ekrandaki yardim metninde sayilir:

- **Pismanlikla verilen duzeltme (VUK 371):** ceza hic kesilmez; ayrica VUK
  359'un son fikrasi geregi 359 hukmu uygulanmaz, yani vergi sucu raporu ve
  suc duyurusu da yazilmaz.
- **Izaha davet (VUK 370):** ceza %20.
- **Inceleme BASLADIKTAN SONRA verilen duzeltme:** VUK 344 son fikrasindaki
  %50 uygulanmaz, ceza tam kat.

Bu karari yeniden acmayin; gerekcesi `GELISTIRME_NOTLARI.md` icinde.

## Yazim

**Kirmizi yer tutucu.** Bilinmeyen bir deger icin sayi uydurmayin;
`belge_docx.YER_TUTUCU_RENGI` ile kirmizi bir yer tutucu birakin. Mufettis
kirmiziyi gorup doldurur; sessiz bir sifir fark edilmez.

**Kurum adlarinda kesme isareti kullanilmaz:** "Mudurlugunun", "Mudurlugu'nun"
degil. `turkce.ilgi_kurum` bunu yapar.

**Daire adi** belgede tam yazilir ("Liman Vergi Dairesi Mudurlugu").
`inceleme_kunyesi.daire_adi` kisa girisi genisletir, beyannameden gelen
kod onekini ("033254 - ") kirpar ve `BILINEN_DAIRELER` listesiyle noktali I /
noktasiz I ayrimini duzeltir. Bu listeyi genisletmek tek satirdir; tahmin
yurutmeyin, adin dogru yazimini ekleyin.

**Buyuk harfli metin.** Sistem dokumlerinden ALL CAPS gelir; `turkce.unvan`,
`turkce.adres`, `turkce.kisi_adi` yazim kurallarina cevirir. Belgeye ham
buyuk harf yazmayin.

## Dokunulmayacaklar

- Mukellefin kendi ifadeleri (tutanaga oldugu gibi gecer)
- Muhasebe kaydi verisi
- Mulga TCK atiflari (ornek belgelerde oyle)
