# Geliştirme Notları

Kullanımda karşılaşılan eksikler, düzeltme istekleri ve fikirler burada
biriktirilir. Tek tek uygulanmaz; birikince toplu olarak ele alınır.

Bu dosya bilerek depodadır: sohbet kapansa da notlar kaybolmaz, sonraki
oturumda buradan devam edilir.

**Durum işaretleri:** `[ ]` bekliyor · `[~]` üzerinde çalışılıyor ·
`[x]` bitti (Yapılanlar bölümüne taşınır)

---

## Bekleyenler

- [ ] **Beyanname özeti alanı da sütunlu tabloya çevrilmeli.**
      `vergi_beyan_ozeti` (yıl | açıklama | tutar) defter alanıyla aynı
      tasarımda: serbest metin, dikey çizgiyle ayrılmış. Word/Excel'den
      yapıştırınca hücreler alt alta gelip hepsi ilk sütuna düşüyor — defter
      alanında sahada böyle çıktı. Çevirmeden önce dikkat: Gelir/Kurumlar
      beyannamesi PDF'inden okutma yolu (`vbAktar`) alanı doğrudan
      `$("k_vergi_beyan_ozeti").value = metin` ile dolduruyor; alan tabloya
      dönerse o satır sessizce etkisiz kalır ve ekran tazelenmez. Satır
      alanını yeniden çizen bir çağrıyla değiştirilmeli.

### Belge biçimi

- [~] **Belge biçimi dairenin formatına getirilecek.** Örnek tutanak ve rapor
      alındı (tek görevlendirmeli / tek sahteci; bilmeyerek kullanma).
      Çıkarılan format:
      - Times New Roman 12 punto, A4, kenar boşlukları 2,5 cm
      - **Tutanak:** başlıksız iki giriş paragrafı + kalın numaralı 1–12
        maddeler (ispat vasıtası / inceleme yeri / defter tablosu / gelir
        vergisi özeti / KDV beyan tablosu / ba-bs + fatura tablosu + muhasebe
        kaydı / sorular / RDK dinlenme / taslak tutanak / TÖU / özelge /
        başkaca itiraz) + kapanış + 2x3 imza tablosu
      - **Rapor:** I- GİRİŞ, II- USUL İNCELEMELERİ (A- Genel Usulsüzlük),
        III- HESAP İNCELEMELERİ (A- Mükellefin Beyanları: kanuni beyan /
        düzeltme / son hal tabloları), IV- TENKİT EDİLEN HUSUSLAR
        (A- Re'sen Takdir Nedeni, B- Re'sen Takdir Verileri + satıcı başına
        B1/B2…, C- Yasal Düzenlemeler ve Değerlendirme + "İndirilecek KDV
        Hesabından Çıkarılacak Tutar" tablosu, D- Tarh Edilecek KDV ile
        Kesilecek Cezalar + düzeltilmiş beyan tablosu + tarhiyat tablosu,
        E- Gelir/Kurumlar Vergisi Yönünden Yapılacak İşlem, F- VUK 359
        Değerlendirmesi), V- SONUÇ (numaralı maddeler + tarhiyat tablosu)
      - Kurum adlarında kesme işareti **kullanılmıyor**: "Müdürlüğünün"
      - Beyan tablosunda **İade Edil. KDV** sütunu da var (9 sütun)
      - Tarhiyat tablosu iki satırlı birleşik başlık taşıyor
      - Fatura tablosu = "Kopya Fatura Dökümü" biçimi
      — *Rapora uygulandı; tutanak üreticisi henüz eski düzende (sıradaki iş)*
- [x] Örnek belgelerdeki mantık ve yazım hataları düzeltildi; değişiklik
      listesi kullanıcıya sunuldu (DEGISIKLIK_LISTESI.md)
- [x] Tutanak üreticisi daire biçimine getirildi; her sahteci satıcı için
      ayrı numaralı madde açılıyor
- [x] **A1 geri alındı** — kullanıcı bildirimi: örnek raporun mükellefi
      şirkettir. "mükellef kurum" ve Kurumlar Vergisi bölümü korundu, belge
      yeniden üretildi; diğer düzeltmeler yerinde.
- [x] Değişiklik listesindeki bütün maddeler kapandı. A2–A5 uygulandı,
      B2–B3 öneri olarak uygulandı, B1 (yevmiye tarihleri) ve B5 (mükellef
      ifadeleri) bilinçli olarak değiştirilmedi, B4 (VKN) kullanıcı
      bildirimiyle kapandı — örnek belgelerde VKN uyumuna dikkat edilmemiş.

### Diğer

- [~] **Çıktı üzerinden ince ayar.** Kullanıcı üretilen tutanak ve raporları
      gerçek çalışmalarında kullanıp gördüğü aksaklıkları bildirecek;
      düzenlemeler o çıktılar üzerinden yapılacak. Bildirim geldikçe buraya
      not düşülür.

- [x] **vergi-inceleme-raporu skill'i güncellendi.** Uygulamayı geliştirirken
      çıkarılan gerçek biçim ve kurallar skill'e taşındı: I–V bölüm düzeni,
      tutanağın numaralı madde düzeni, sonucu değiştiren dört ayrım
      (kurum/gerçek kişi · bilerek/bilmeden · düzeltmeyle çıkarılmış satıcı ·
      re'sen takdir nedeni), oran hesabı, ceza paylaştırması, VUK mük. 355
      hesabı, kırmızı yer tutucu kuralı, dokunulmayacaklar listesi
      (mükellef ifadeleri, muhasebe verisi, mülga TCK atfı).
      Konum: ~/.claude/skills/vergi-inceleme-raporu/

<!-- Yeni notlar buraya eklenir -->

---

## Verilmiş kararlar (yeniden açmayın)

- **Bilerek kullanmada ceza ÜÇ KAT olarak kodlanır.** Müfettişin kararı
  (2026-09-07). Farklı bir durum çıkarsa raporu elle düzeltir; uygulamaya
  seçim eklenmeyecek. Gerekçe: dosyaların ezici çoğunluğu bu hâlde ve her
  ihtimali seçime bağlamak ekranı ağırlaştırıyor.

  Araştırmada çıkan ve **elle düzeltmeyi gerektiren** hâller — belgedeki
  yardım metni bunları sayar, kod dallanmaz:
  - *Pişmanlıkla verilen düzeltme (VUK 371):* vergi ziyaı cezası hiç
    kesilmez; ayrıca VUK 359'un son fıkrası "371'deki pişmanlık şartlarına
    uygun olarak durumu ilgili makamlara bildirenler hakkında bu madde
    hükmü uygulanmaz" dediği için vergi suçu raporu ve suç duyurusu da
    yazılmaz. Ancak 371'in kapısı dardır: ihbardan, incelemeye
    başlanmasından, takdire sevkten ve kaçakçılık fiilinin tespitinden önce
    olmalıdır — sahte belge dosyalarında karşıt/mukabil inceleme tutanağı
    düzenlenmişse pişmanlık kapanır.
  - *İzaha davet (VUK 370):* ceza %20. Sahte belge kullanmada tutar
    sınırlıdır (belge başına yıllık sınır ve o yılki toplam alışların
    %5'i).
  - *İnceleme başladıktan SONRA verilen düzeltme:* VUK 344 son fıkrasındaki
    %50 uygulanmaz; ceza tam kat kesilmiştir. Kodun "yarım kat kesilmiştir"
    varsayımı yalnızca inceleme öncesi düzeltmeler için doğrudur.
  - *Üç kat mı 1,5 kat mı:* Danıştay 9. Daire'nin 344/2 ile son fıkrayı
    birlikte uygulayıp 1,5 kata indiren kararları var; "fark cezanın hiç
    kesilemeyeceği" yönünde kararlar da olduğu belirtiliyor. Tartışmalı;
    uygulama üç kat yazar.

  Not: bu araştırma yalnızca arama motoru özetlerine dayanıyor; oturumun ağ
  politikası mevzuat.gov.tr ve gib.gov.tr dahil hemen her kaynağı engelledi.
  Madde metinleri birincil kaynaktan doğrulanmadı.

## Yapılanlar

- [x] 2026-10-02 — **İbraz edilen defterler sütunlu tabloya çevrildi.**
      Alan serbest metindi, hücreler dikey çizgiyle ayrılıyordu; kullanıcı
      Word/Excel'den yapıştırınca hücreler alt alta gelip hepsi ilk sütuna
      düşüyordu, elle yazmak da zahmetliydi. Artık `satirlar` türünde, dört
      sütunlu (Yılı · Defterin Türü · Tasdik Tarihi ve Numarası · Tasdik
      Makamı) ve "+ Defter ekle" düğmesi var — faaliyet konuları ve
      görevlendirme yazıları gibi.
      **Depolama biçimi değişmedi** (satır başına bir kayıt, hücreler dikey
      çizgiyle ayrılmış), bu yüzden eski çalışmalar olduğu gibi okunuyor ve
      belge üreticisi (`cizgili_satirlar`) hiç değişmedi.

- [x] 2026-10-02 — **Künyedeki genel beyan artık kapanış maddesine düşüyor.**
      Bir önceki düzeltme eksik kalmıştı: alanı görünür kıldım ama künyedeki
      metin hâlâ her satıcı maddesine yedek olarak giriyordu. Müfettişin
      kastı farklıymış — o metin mükellefin **incelemenin bütünü** hakkındaki
      beyanı ve tutanağın son maddelerine, itirazların yer aldığı yere ait.
      Artık `_genel_beyan_maddesi` ile kapanışta kendi maddesi olarak
      yazılıyor, "başkaca itiraz" maddesinden hemen önce. Satıcı maddelerine
      yalnızca o satıcıya ilişkin beyan giriyor; girilmemişse kırmızı
      **[mükellefin bu satıcıya ilişkin beyanı]** yer tutucusu kalıyor ki
      eksik olduğu belgede görünsün.
      Satıcı yoksa `_sorular_maddesi` beyanı zaten yazdığı için kapanış
      maddesi o dosyalarda tekrarlanmıyor (`genel_beyan` bayrağı).

- [x] 2026-10-02 — **Satıcı başına mükellef beyanı görünür kılındı.** Kullanıcı
      17 sahteci satıcılık bir dosyada künyedeki beyanı doldurup hepsinde aynı
      metnin çıktığını bildirdi. Alan aslında **vardı** ve doğru çalışıyordu
      (`SATICI_ALANLARI.cevap`, satıcı kartında); sorun bulunabilirlikti —
      künyedeki ortak alan hiçbir yerde "bu yalnızca yedek" demiyordu ve
      satıcı kartını açmadan hangisinin kendi beyanı olduğu görülemiyordu.
      Künyedeki alanın adı **"Mükellefin beyanı / itirazı (ortak)"** oldu ve
      ipucu, satıcı başına beyanın nereye yazılacağını söylüyor. Satıcı
      döküm tablosuna **Beyan** sütunu eklendi: "kendi beyanı" / "ortak",
      üzerine gelince metnin kendisi görünüyor. 17 satıcılık bir dosyada
      kartları tek tek açmadan eksikleri görmenin başka yolu yoktu.
      Kod değişmedi; davranış zaten doğruydu.

- [x] 2026-10-01 — **Malın cinsi ve yevmiye bilgileri artık fatura listesinden
      girilebiliyor.** Bu üç alan portal dökümlerinde gelmiyor, defter
      kaydından elle giriliyordu; ama girilecek bir yer yoktu — belgelerde
      hep kırmızı yer tutucu kalıyordu. Okunur "Not" sütununun yerine üç
      düzenlenebilir sütun geldi: **Malın Cinsi · Yevmiye Tarihi · Yevmiye
      No** (Not sütunu zaten bu iki alanı ve iptal/itirazı tekrar
      gösteriyordu; iptal/itirazın kendi kutusu var).
      Yevmiye tarihi gg.aa.yyyy yazılıp ISO saklanıyor (`tarihCoz`,
      `tarihGoster`in tersi); çözülemeyen metin reddedilip kutu eski değerine
      dönüyor. Deftere kaydedilmemiş faturanın yevmiye kutuları kapalı ve
      "kayıt yok" yazıyor — belgedeki hücreyle aynı.
      Excel çıktısına da yansıdı: "Not" yerine Defterde · Beyanda · Malın
      Cinsi · Yevmiye Tarihi · Yevmiye No sütunları.

- [x] 2026-10-01 — **Fatura düzenlenmesi / deftere kaydedilmesi / beyana
      yansıtılması üç ayrı olgu olarak ayrıldı.** Sahada çıktı: satıcı üç
      fatura düzenlemiş, mükellef bunlardan yalnızca birini deftere kaydedip
      indirimine almıştı; uygulamada bunu gösterecek bir yer yoktu.
      Faturaya iki tik eklendi (**Defterde**, **Beyanda**); ikisi de evet olup
      satıcı düzeltmeliyse durum "düzeltme beyannamesi var" olur
      (`faturalar.fatura_durumu`). **Reddedilen şey indirimdir:** beyana
      yansımamış fatura tarhiyata giremez — `normalize` bunu zorlar,
      arayüzde de "Dahil" kutusu kapanır.
      Tabloya **Sıra** sütunu kondu; durum paragrafları belgeyi sıra
      numarasıyla anıyor. Deftere kaydedilmemiş faturanın yevmiye hücrelerine
      "kayıt yok" yazılıyor (kırmızı yer tutucu yanıltıcı olurdu: orada
      doldurulacak bir bilgi yok).
      Kaldırılan paragrafların yerine dört durum paragrafı geldi
      (`tutanak.defter_beyan_paragraflari`), tekil/çoğul uyumlu ve tablo
      sırasına göre dizili. **Tutanak ve iki rapor aynı üreteçten besleniyor.**
      Muhasebe kaydı paragrafı ve sahte belge raporunun giriş cümlesi artık
      yalnızca deftere kayıtlı/beyana yansımış faturalar için yazılıyor;
      hepsini kapsayan eski cümle istisna varken gerçeğe aykırıydı.
      **Yan sonuç:** bütün faturaları beyan dışı olan satıcı tarhiyata hiç
      girmediği için düzeltme kabul raporunun uygunluk ölçütüne "tarhiyata
      giren KDV'si yok" hâli eklendi; yoksa tarhiyatı sıfır olan bir dosyada
      rapor "faturaları hâlâ tarhiyata giriyor" diye reddedilirdi.
- [x] 2026-10-01 — **Tutanaktan değerlendirme cümleleri çıkarıldı.** Satıcı
      maddelerinin 2. ve 3. paragrafları kaldırıldı: "…sahte belge
      kullanıldığı anlaşılmıştır" ile Vergi Tekniği Raporunun sonuç bölümünü
      tırnak içinde aktaran paragraf. Tutanak tespit belgesidir; değerlendirme
      ve sonuca yalnızca raporda varılabilir. Özel esaslar paragrafı kaldı —
      o idari bir durumdur, tespittir. Raporlar iki paragrafı da yazmaya
      devam ediyor (`satici_tespit_paragraflari(..., vtr_dahil=False)`).
      Kaybolmaması gereken **yıl bilgisi** Ba-Bs cümlesine taşındı:
      "Mükellef Kurumun **2021 hesap dönemi** Ba-Bs sorgulamasında…"
      (kurumda hesap dönemi, gerçek kişide takvim yılı).

- [x] 2026-09-12 — **Daire adında noktalı İ / noktasız I ayrımı.** Büyük
      harfle `LIMAN VD` yazıldığında belgeye `Lıman` geçiyordu. Kod Türkçe
      kuralına uygun çalışıyor; sorun gerçek bir **belirsizlik**: aynı harf
      `KADIKÖY`de noktasız olarak doğru, `LIMAN`da yanlış. Bu yüzden tahmin
      yürütülmedi — "büyük harfte I'yi hep i say" gibi kör bir kural bugün
      doğru çalışan Kadıköy, Işıklar, Sarıyer gibi adları bozardı.
      Bunun yerine `inceleme_kunyesi.BILINEN_DAIRELER` listesi eklendi; girdi
      genişletildikten sonra bu adlarla **noktadan bağımsız** karşılaştırılıyor
      ve tutarsa doğru yazım kullanılıyor. Eşleşme yoksa davranış hiç
      değişmiyor. **Liste tek satırla genişletilir** — adın tam ve doğru
      yazımını eklemek yeter. Beyanname yüklendiğinde daire adı zaten doğru
      yazımıyla okunduğu için bu liste yalnızca elle girişi ilgilendirir.
      Şu an yalnızca Liman var; kullanıcının çalıştığı daireler eklenecek.

- [x] 2026-09-11 — **Yeni biçimin matrahlı hâli okunuyor; iki hata düzeltildi.**
      Sahadan gelen ikinci örnek (2026/Mayıs) ilkinde hiç bulunmayan bölümleri
      taşıyordu: MATRAH, İHRAÇ KAYDIYLA TESLİMLER, İSTİSNALAR, MATRAH DETAYI,
      İSTİSNALAR DETAYI. İkisi gerçek hataydı:
      - **`matrah_toplami` sıfır okunuyordu.** Yeni biçim "Matrah Toplamı"
        değil **"Toplam Matrah"** yazıyor; alan adı tanınmayınca değer eksik
        kalıyor, eksik bölüm "sıfır" sayıldığı için de **sessizce** 0,00
        görünüyordu. Artık eşleniyor; ayrıca `_denetle`ye "matrahsız
        hesaplanan KDV olmaz" uyarısı eklendi — aynı hatanın bir daha sessiz
        kalmaması için.
      - **Ünvanın ikinci satırı kayboluyordu.** Değer satırları sola değil
        **sağa** yaslı olabiliyor; devam satırı birincinin çok sağında
        başlıyor (312.6 → 377.6). Hizaya bakan kural yerine artık şuna
        bakılıyor: bandın ETİKET sütunu boşsa devam satırıdır.
      Ayrıca düzeltme işareti, künye alanları gibi etiketi ve değeri **ayrı
      parçalarda** olabiliyor; iki düzen de destekleniyor.
      **Düzeltme işareti bulundu:** alanın adı **"Düzeltme Açıklaması"**
      (ne "Düzeltme Nedeni" ne "Beyanname Türü" — ikisi de denendi, üçüncüsü
      çıktı). Etiketi solda, serbest metin açıklama sağında; alan yalnızca
      düzeltme beyannamelerinde basılıyor, kanuni beyannamede o satır hiç yok
      ve altındaki her şey 24 punto yukarıda duruyor.
      **Vergi dairesi kod önekiyle geliyor** ("033254 - Liman Vergi Dairesi
      Müdürlüğü"); kod belgeye girmemeli, `inceleme_kunyesi.daire_adi` artık
      kırpıyor. Okuyucu beyannamede yazanı verir; kırpma belgeye yazarken olur.
      **`testler/` eklendi:** sahadan gelen üç döküm (eski biçim, yeni biçim,
      yeni biçim matrahlı) ve gerileme koşucusu. `python3
      testler/beyanname_testi.py`. Paketlere girmiyor. Yukarıdaki iki hata
      bilerek geri konarak denetimin gerçekten attığı doğrulandı.

- [x] 2026-09-06 — **Kullanma durumu artık belgenin TÜRÜNÜ değiştiriyor.**
      Faturaların tamamı düzeltmeyle çıkarılmışsa tarh edilecek vergi iki
      hâlde de yoktur, ama düzenlenecek belge farklıdır:
      *bilmeden* → **Vergi Tekniği Raporu** (vergi de ceza da yok);
      *bilerek* → **Vergi İnceleme Raporu** (tarhiyat yine önerilmez, ancak
      düzeltme beyannameleri üzerine VUK 344 son fıkra uyarınca kesilmiş olan
      **yarım kat** cezanın **üç kata tamamlanması** vergi dairesinden istenir
      ve VUK 359 kapsamında vergi suçu raporu düzenlenir). Belge başlığı ve
      dosya adı da buna göre değişiyor; ikisi ayrı belgedir ve aynı klasörde
      yan yana durabilmeli.
      **Cezanın matrahı düzeltildi:** eskiden faturalardaki KDV toplamı
      alınıyordu; doğrusu düzeltmeyle *ödenecek hâle gelen* vergidir
      (`beyannameler.duzeltmeyle_dogan_vergi`). Düzeltme önce devreden KDV'yi
      eritir; ziya ancak devir tükendikten sonra doğar. Bu yüzden üç hâl ayrı
      cümle gerektiriyor ve üçü de yazıldı: tutar bilinmiyor (beyanname
      yüklenmemiş → kırmızı yer tutucu), ziya doğmamış (yalnızca devir
      eridi → tamamlanacak ceza yok), ziya var (tutarlar yazılır).

- [x] 2026-09-06 — **Beyannamenin yeni çıktı biçimi okunuyor.** Aynı KDV
      beyannamesinin iki basımı dolaşımda; okuyucu ikisini de kabul ediyor ve
      hangisi olduğunu kendi anlıyor (`pdf_beyanname._yeni_bicim_mi`, ölçüt
      dönem bilgisinin "Yıl: 2026" gibi tek parçada basılması). Farklar:
      künye alanları "Etiket: Değer" olarak tek parçada; onay damgası
      `06/05/2026 06:01:51` (nokta yerine eğik çizgi, tire yok); alan adları
      kısaltılmış ("… Katma Değer Vergisi" → "… KDV"); vergi dairesi
      etiketsiz, dönem serisinin solunda; indirimler ayrıca "İNDİRİMLER
      DETAYI" bölümünde resmi satır koduyla ("108 - Yurtiçi Alımlara İlişkin
      KDV") dökülüyor. **En önemlisi:** yeni biçim, tutarı tümden sıfır olan
      BÖLÜMÜ başlığıyla birlikte hiç basmıyor (örnek beyannamede satış
      olmadığı için matrah bölümü yok), o yüzden eksik bölüm "okunamadı"
      değil "sıfır" demek. Yeni biçimde okunamayan çekirdek satırlar sıfır
      sayılıyor; yanlış okumayı örtmez, çünkü sıfır kabulü hatalı olsaydı
      `_denetle`nin "toplam KDV − indirimler = ödenecek / devreden"
      eşitliği tutmazdı. Ekranda sürüm satırında "yeni biçim" yazıyor.
      Elde bir düzeltme beyannamesinin yeni biçimli örneği yok; "Beyanname
      Türü: Düzeltme…" alanı destekleniyor ama örnekle doğrulanmadı.
- [x] 2026-09-06 — **Windows için güncelleme paketi** (`kdv_windows/
      guncelleme_paketle.sh`). Tam paketin küçük kardeşi: gömülü Python ve
      kurulum malzemesi taşımaz, yalnızca program dosyalarını (`main.py`,
      `app/`, `web/`) ve bunları kurulu uygulamanın üzerine koyan
      `guncelle.bat`'i taşır. Betik kurulu uygulamayı kendisi arar
      (bırakılan klasör, kendi klasörü ve bir üstü, Desktop/Downloads/
      Documents, OneDrive), bulamazsa klasörü sürükleyip bırakmayı ister;
      **önce yedek alır, alamazsa hiçbir dosyaya dokunmaz** ve kopyaladıktan
      sonra yeni sürümün gerçekten yerine geçtiğini bir işaret arayarak
      denetler. Paketleyici de denetliyor: CRLF, **UTF-8 BOM** (BOM'suz
      .txt'yi eski Notepad ANSI sanıp Türkçe harfleri bozuyor), tırnaksız
      `%HEDEF%`, kullanıcı klasörlerinin (ciktilar/veritabani/yedekler)
      pakete sızmaması, ve `guncelle.bat`'in aradığı işaretin pakette
      gerçekten bulunması — bulunmazsa betik başarılı bir güncellemeyi
      başarısız sanardı.
- [x] 2026-08-26 — **Linux sürümü çalışır durumda doğrulandı.** Uzun süren
      "hiç açılmıyor" arızasının sebebi bulundu: `::1` çift dinleme
      eklenirken "IPv6 yok" ile "port dolu" ayrılmamıştı. `_ipv6_var()`
      yalnızca soket AÇILABİLİYOR mu diye bakıyor; IPv6 çekirdekte açık
      olup `::1` adresi `lo` arayüzüne atanmamışsa soket açılıyor ama
      `bind` `EADDRNOTAVAIL` ile düşüyor. Bu hata "port dolu" sayıldığı
      için on portun onu birden dolu görünüyor ve uygulama
      "Uygun port bulunamadı (8766-8775 dolu)" deyip kapanıyordu.
      Artık `EADDRINUSE` gerçek çakışma sayılıp yukarı bildiriliyor,
      başka hata IPv6'nın kullanılamadığı anlamına geliyor ve IPv4 ile
      devam ediliyor. İki durum da zorlanarak sınandı.

      Ders: tuzağı kapatmak için yazılan düzeltmenin kendisi, kapattığı
      şeyden geniş bir arıza açabiliyor. Kural üç paketleyiciye de
      denetim olarak eklendi (`::1` varsa `EADDRINUSE` de olmalı).

- [x] 2026-08-26 — Linux ve Windows ayrı ağaçlara bölündü (`kdv_linux`,
      `kdv_windows`); ortak uygulama kodu `esitle.sh` ile eşitleniyor,
      `--denetle` fark olup olmadığını söylüyor. Her ağacın kendi
      paketleyicisi ve kendi denetimleri var. Linux paketi `.tar.gz`
      (zip çalıştırma iznini korumuyor), Windows paketi `.zip`.

- [x] 2026-08-26 — Başlatıcılar sessizce başarısız olmuyor: konsol
      yokken (masaüstü kısayolu) çıktı `ACILIS KAYDI.txt` dosyasına
      yazılıyor. Dosyanın hiç oluşmaması da bilgi: betik hiç
      çalıştırılamamış demektir.

- [x] 2026-08-14 — Windows başlatıcısı geri geldi: "KDV Uygulamasini
      Baslat.bat" ve KURULUM_WINDOWS.txt. Linux açılış yoluna
      dokunmuyor; Python yoksa taşınabilir Python'u kendisi indiriyor
- [x] 2026-08-14 — Tutanaktan değerlendirme cümlesi çıkarıldı (tutanak
      tespit belgesidir); düzeltme gerekçesi artık bütün düzeltme
      sürümlerinden toplanıp dökümün giriş cümlesinde yazılıyor
- [x] 2026-08-14 — Düzeltme ayrıntı tablosunda "İade Edilmesi Gereken
      KDV" sütunu, düzeltme öncesinde de sonrasında da tutar yoksa hiç
      açılmıyor
- [x] 2026-08-10 — Taslak vergi inceleme tutanağı (VUK 141) üretimi; künye
      formu; bağımlılık gerektirmeyen .docx yazıcı
- [x] 2026-08-10 — Fatura dökümü okuma (e-Arşiv / e-Fatura / elle hazırlanan),
      satıcı yönetimi, indirim reddine aktarım
- [x] 2026-08-10 — Sahte belge kullanma raporu taslağı; bilerek/bilmeden
      ayrımına göre ceza dağılımı
- [x] 2026-08-10 — Excel çıktısına Faturalar sayfası; kılavuz güncellemeleri
- [x] 2026-08-10 — Kasıt değerlendirmesine 5237 sayılı TCK md. 21 eklendi
      (mülga 765 sayılı Kanuna dayanan kalıp yerine)
- [x] 2026-08-10 — Elle doldurulacak yer tutucular belgede kırmızı yazılıyor;
      fatura tablosunda boş yevmiye tarih/no hücreleri de kırmızı tutucu
- [x] 2026-08-10 — Gelir / Kurumlar Vergisi beyannamesi PDF'inden özet okuma
      (türü tanınmayan dosyada okuma durduruluyor)
- [x] 2026-08-10 — Tutanak dairenin biçimine getirildi: iki giriş paragrafı +
      kalın numaralı maddeler, defter tablosu, gelir/kurumlar vergisi beyan
      özeti, satıcı başına ayrı ba-bs + fatura maddesi, RDK / taslak tutanak /
      TÖU / özelge / başkaca itiraz maddeleri, 2x3 imza tablosu
- [x] 2026-08-10 — Gerçek kişi mükellef kolu tamamlandı: suç duyurusu hedefi
      (kurumda kanuni temsilci, gerçek kişide mükellefin kendisi), kazanç
      mevzuatı (KVK 6/11 - GVK 37/40/mük.120), geçici vergi adlandırması
- [x] 2026-08-10 — Şirkette "hesap dönemi", gerçek kişide "takvim yılı"
- [x] 2026-08-10 — Rapor, dairenin biçimine getirildi (I–V, A/B/C/D/Ç);
      bilerek kullanma kolu, oran hesabı, VUK mük. 355 özel usulsüzlük,
      "İndirilecek KDV'den Çıkarılacak Tutar" tablosu, düzeltme beyannamesiyle
      çıkarılmış satıcıların tarhiyat dışı bırakılması
- [x] 2026-08-10 — Hesap incelemeleri tablosu: eksik olan *Önc. Dön. Dev. KDV*
      sütunu eklendi, punto 9'a düşürüldü, yıl başlığa taşındı, satırlarda
      yalnızca ay adı, "Toplam:" satırı vurgulandı. Diğer geniş tablolar da
      aynı puntoya çekildi. — *kullanıcı bildirimi, ekran görüntüsüyle*
- [x] 2026-08-10 — Tutanakta satıcı maddeleri veri/soru çifti hâlinde sürüyor:
      6. madde satıcının Ba-Bs tespiti ve fatura dökümü, 7. madde o faturalara
      ilişkin mükellefe sorulan hususlar ve cevabı; ikinci satıcıda 8/9,
      üçüncüde 10/11 diye devam ediyor. Soru maddesi veri maddesine numarasıyla
      atıf yapıyor. Satıcı kartına "Mükellefin bu satıcıya ilişkin beyanı"
      alanı eklendi; boş bırakılırsa künyedeki genel beyan kullanılıyor.
- [x] 2026-08-10 — Belgelerin sonundaki "Bu belge ... taslak olarak
      üretilmiştir" satırı kaldırıldı (hem tutanak hem rapor).
- [x] 2026-08-10 — Boş "Malın Cinsi" hücreleri artık kırmızı `[malın cinsi]`
      tutucusu; defter bilgileri tablosu künyede boş bırakılsa bile açılıyor,
      incelenen her yıl için bir satır kuruluyor ve tür / tasdik tarih-no /
      tasdik makamı kırmızı tutucu olarak bırakılıyor. Taslak üzerinde
      doldurulacak yerler belgede görünür duruyor. — *kullanıcı isteği*
- [x] 2026-08-11 — **Her yıl için ayrı rapor.** Tutanak bütün inceleme dönemi
      için tek düzenlenmeye devam ediyor; rapor ise incelenen her yıl için
      ayrı üretiliyor. Yıla göre daraltılan veriler: hesap tabloları, fatura
      dökümü, satıcı listesi, ceza dağılımı, oran hesabı, düzeltme
      beyannameleri, tutarlılık bulguları ve iş emri tablosu. Böylece bir yılın
      satıcısı bilmeden, diğerininki bilerek kullanma sayıldığında ceza katı,
      suç duyurusu ve uzlaşma kapsamı her raporda kendi yılına göre kuruluyor.
      Tek yıl varsa .docx, birden fazla yıl varsa raporlar tek .zip içinde
      iniyor; kopyaları yine ciktilar klasörüne bırakılıyor. — *kullanıcı isteği*
- [x] 2026-08-11 — "Görevlendirme ve İnceleme" bölümü tabloya çevrildi:
      Sıra No | İş Emri Tarihi | İş Emri Sayısı | Dönemi | Konusu. Sıra no
      kendiliğinden veriliyor, (+) düğmesi yeni satır açıyor, × satırı siliyor.
      Serbest metinli "İş emirleri" kutusu ile ayrı "Görevlendirme yazısı
      no / tarihi" alanları kaldırıldı; veri yine aynı biçimde saklandığından
      eski çalışmalar olduğu gibi açılıyor. İnceleme dosya no, rapor no,
      incelemeye başlama tarihi, inceleme türü ve inceleme gerekçesi alanları
      silindi (hiçbir belgede kullanılmıyorlardı). Tutanak ve raporda
      görevlendirme cümlesi artık tablodan kuruluyor; boş hücreler ve hiç satır
      girilmemiş olması kırmızı yer tutucu bırakıyor. — *kullanıcı isteği,
      ekran görüntüsüyle*
- [x] 2026-08-11 — Fatura listesine satıcı VKN süzgeci eklendi. Açılır listede
      her satıcı, unvanı ve fatura adediyle görünüyor. Süzme yapıldıktan sonra
      "Dahil" başlığındaki kutucuk süzülen satırların tamamını tek seferde
      dahil ediyor / çıkarıyor; süzgeç dışındaki satırlara dokunmuyor.
      — *kullanıcı isteği*
- [x] 2026-08-11 — Düzeltme beyannameleri tutanaktan çıkarıldı; yalnızca
      raporun III- HESAP İNCELEMELERİ bölümünde yer alıyor. — *kullanıcı isteği*
- [x] 2026-08-11 — Tutanağın 4. maddesi (Gelir / Kurumlar Vergisi beyanname
      dökümü) künyeye özet girilmemiş olsa da açılıyor: mükellef türüne göre
      olağan kalemler yazılıp tutarlar kırmızı `[tutar]` bırakılıyor. Beyanname
      PDF'i yüklenirse tablo veriden doluyor. — *kullanıcı isteği, örnek tutanak
      karşılaştırmasıyla*
- [x] 2026-08-11 — Fatura tarihleri her yerde GG.AA.YYYY gösteriliyor (fatura
      listesi, tutanak ve rapor tabloları, Excel'in Faturalar sayfası, yevmiye
      tarihi). Veri yine ISO biçiminde saklanıyor; sıralama ve karşılaştırma
      ona dayandığı için çevrim yalnızca gösterimde yapılıyor.
      — *kullanıcı isteği*
- [x] 2026-08-11 — Düzeltme gerekçesi artık tam okunuyor: uzun açıklama PDF'te
      birden çok parçaya bölünüyor ya da alt satıra taşıyorsa hepsi toplanıyor
      (tanınan bir alan başlığına veya satır aralığından büyük bir boşluğa
      rastlayınca duruluyor). — *kullanıcı bildirimi*
- [x] 2026-08-11 — Ad ve unvanlar yazım kurallarına göre yazılıyor: kişi
      adlarında ad ilk harf büyük / soyad tümü büyük ("Ahmet HASAN"), şirket
      unvanlarında her kelimenin ilk harfi büyük, kısaltmalar büyük, bağlaçlar
      küçük ("Deneme İnşaat Sanayi ve Ticaret A.Ş."). Türkçe i/I çifti doğru
      çevriliyor. Belgeye yazarken uygulanıyor; kullanıcının girdiği veri
      değiştirilmiyor. — *kullanıcı isteği*
- [x] 2026-08-11 — Raporda düzeltme beyannamesiyle çıkarılmış satıcının
      bölümüne ayrıntılı düzeltme tablosu eklendi: Dönemi | Beyanname Satırı |
      Düzeltme Öncesi Beyanname | Düzeltme Beyannamesi | Fark. Beyannameler
      yüklüyse dönemler ve tutarlar veriden geliyor; yüklü değilse künyedeki
      "Düzeltme beyannamesi verilen dönemler" alanına yazılan dönemler için
      tablo kırmızı yer tutucularla açılıyor. — *kullanıcı isteği, örnek
      tabloyla*

### 2026-08-11 — kullanıcının toplu düzeltme listesi

- [x] Tarhiyat özetinde tutar taşımayan iade sütunları gizleniyor; bileşenleri
      gizlenmişse "1+2" ve "1+2+3" toplamları da yazılmıyor. Tablo böylece
      Word'e yapıştırıldığında sayfaya sığıyor. Aynı ölçüt hem ekranda hem
      Excel'de geçerli (Excel formülleri artık sabit sütun harfi değil,
      gösterilen sütunların harflerini kullanıyor).
- [x] "Eleştirili" sözü ekranda ve Excel'de "Olması Gereken" olarak değişti.
- [x] Tarhiyat özetine **Vergi Ziyaı Cezası** sütunu eklendi; 1 kat / 3 kat
      seçimi ekranda yapılıyor, çalışmayla birlikte kaydediliyor.
- [x] Tutanakta madde gövdeleri ince puntoya çevrildi.
- [x] Tutanaktaki aritmetik denetim bulguları, KDV beyan tablosunun altına
      taşındı (son maddedeki liste kaldırıldı).
- [x] Raporda III. bölüm üç tablo: ilk beyannameler, düzeltme beyannameleri,
      beyanın son hali. Düzeltme tablosu taşmıyor: gerekçe sütunu tablodan
      çıkıp altta cümle oldu, tablo dar hücre boşluklarıyla 8 puntoda.
- [x] Raporda "Genel Usulsüzlük" bölümü kaldırıldı.
- [x] A- Re'sen Takdir Nedeni metni yeniden yazıldı; tutanağın satıcı veri
      maddelerine (6., 8., 10. …) atıf yapıyor ve ikinci paragraf VUK 30/6 ile
      uyumlu.
- [x] Vergi Tekniği Raporu cümlesi satıcıya ilişkin tespitle tamamlanıyor.
- [x] Düzeltmeyle çıkarılan faturalara ilişkin paragraf, düzeltilmiş beyan
      tablosunun hemen öncesine taşındı.
- [x] Beyanname yüklenip beyan verisine aktarıldığında mükellefin VKN, unvan
      ve vergi dairesi bilgileri de alınıyor; farklı VKN'li beyanname
      karışmışsa uyarı veriliyor.
- [x] Fatura dökümünde alıcı/satıcı sütunları varsa yön onlardan belirleniyor;
      mükellef VKN'si girilmemişse bütün satırlarda tekrar eden VKN mükellef
      sayılıyor. Döküm taraf sütunu taşımıyorsa mükellef alıcı kabul ediliyor.
- [x] İnceleme Tespitleri sekmesine "Bu dönemin indirilecek KDV'sini tümüyle
      reddet" düğmesi eklendi (defter ve belge ibraz edilmediği hâl).
- [x] Tutanakta da görevlendirme yazıları tablo hâlinde: raporla aynı düzen
      (Sıra No | İş Emri Tarihi | İş Emri Sayısı | Dönemi | Konusu). Hiç iş
      emri girilmemişse eski cümle kırmızı yer tutucularla yazılıyor.
- [x] Gelir / Kurumlar Vergisi beyanname özeti artık yıl yıl tutuluyor:
      künyede satırlar "yıl | açıklama | tutar", tutanakta her yıl için ayrı
      tablo. Beyanname PDF'i aktarımı önceki yılların üzerine yazmıyor,
      yalnızca kendi yılını yeniliyor. Eski (yılsız) kayıtlar incelemenin ilk
      yılına düşüyor.
- [x] Tutanakta incelemenin yapıldığı yer adresiyle yazılıyor; yalnızca
      "dairede" demiyor. Mükellefin iş yeri / uzaktan seçimleri de kendi
      cümlesini kuruyor, adres boşsa kırmızı tutucu kalıyor.
- [x] Alışlara ilişkin soru maddeleri kurumda "Mükellef Kurum Yetkilisine",
      gerçek kişide "Mükellefe" diye başlıyor; cevabı veren de aynı biçimde
      anılıyor.
- [x] Tutanakta yazım kuralları: vergi dairesi, adres, ad-soyad ve unvanlar
      belgeye yazılırken düzeltiliyor (adres için kısaltmalar korunuyor:
      "KURTULUŞ MAH. VD KAMPÜSÜ" → "Kurtuluş Mah. VD Kampüsü").
- [x] Tutanakta her madde paragraf başı girintisiyle başlıyor.
- [x] Satıcı fatura tablosunun altına muhasebe kaydı paragrafı standart olarak
      yazılıyor ("… söz konusu alışları [740-Hizmet Üretim Maliyeti ile
      191-İndirilecek KDV hesaplarına borç ve 320-Satıcılar hesabına alacak]
      kaydı ile 2022 yılı yevmiye defterine kaydettiği; …"). Hesap numaralarını
      içeren bölüm kırmızı: kullanılan hesap faaliyete göre değişiyor. Yıl,
      satıcının faturalarının kayıt yılından alınıyor. Künyeye metin
      yazılmışsa o kullanılıyor.
- [x] Raporda satıcı fatura tablosunun öncesine, tutanağın ilgili veri
      maddesine atıf yapan ve faturaları düzenleyen mükellefi anan paragraf
      eklendi.
- [x] Düzeltmeyle çıkarılmış satıcının bölümünde artık düzeltme anlatısı,
      örnekteki düzende ayrıntılı tablo (aylar satır; düzeltme öncesi /
      düzeltme beyannamesi / fark) ve "hangi satırdan çıkarıldığı" kapanış
      cümlesi yer alıyor. Bütün düzeltmeler değil, o satıcıya bağlanabilenler
      yazılıyor: faturalarının kaydedildiği aylar, gerekçesinde satıcının
      unvanı geçen aylar ve bunlardan sonra devir zincirini taşıyan aylar.
      Fatura listesinin altındaki serbest düzeltme açıklaması kaldırıldı.
- [x] **Rapordaki tutanak atıfları düzeltildi.** Rapor yıl yıl yazılıyor ama
      tutanak bütün yılları kapsayan tek belge; madde numaraları o yılın satıcı
      sayısından hesaplandığı için 2021 raporu tutanakta 2024 satıcısına ait
      olan maddeye atıf yapıyordu. Numaralar artık daraltmadan önce, bütün
      satıcılar üzerinden hesaplanıp VKN ile eşleştiriliyor; hem re'sen takdir
      nedeni hem satıcı bölümleri aynı eşlemeden okuyor. Dört yıllık, yedi
      satıcılı senaryoyla doğrulandı (madde_tutarlilik.py).
- [x] Vergi Tekniği Raporunun sonuç bölümünden aktarılan tespit tırnak içine
      alınıyor; girilmemişse kırmızı yer tutucu tırnaksız kalıyor. Metni
      tırnaklarıyla birlikte yapıştırdıysanız tırnak iki kez yazılmıyor —
      satıcı notundaki baştaki/sondaki tırnaklar temizlenip tek seviyeye
      indiriliyor (B.1 tırnaksız / B.2 tırnaklı görünümünün sebebi buydu).
- [x] Tutanağın giriş cümlesinde alışlar yıl yıl gruplanıyor: "2022 hesap
      döneminde A'dan alışları, 2023 hesap döneminde B ve C'den olan
      alışlarının…". Gruplar faturaların kayıt yılından kuruluyor; bir satıcı
      birden çok yılda geçiyorsa her yılın grubunda yer alıyor.
- [x] **Düzeltmeyle çıkarma takibi.** Bir dönemde indirimlerden çıkarılan KDV
      her zaman o ay ödenecek vergiye dönüşmez; devir varsa tutar devri azaltıp
      izleyen ayların "önceki dönemden devreden KDV" satırından düşülerek
      taşınır. Uygulama artık bunu izliyor: faturanın kaydedildiği aydan
      başlayıp, çıkarılan tutar ödenecek vergiye dönüşene kadar devir zinciri
      takip ediliyor; raporda çıkarılan tutar, ödenecek vergiye dönüşen kısım
      ve devirde izlenen bakiye ayrı ayrı yazılıyor. Faturadaki KDV'nin tamamı
      çıkarılmamışsa aradaki fark kırmızı bir uyarıyla belirtiliyor — o kısımda
      mükerrer tarhiyat söz konusu olmadığından tarhiyata alınıp alınmayacağı
      değerlendirilmeli. (beyannameler.duzeltme_takibi)
- [x] III. bölümdeki düzeltme beyannameleri kısmında yalnızca tablo var;
      gerekçe ne sütun ne de açıklama olarak yazılıyor.
- [x] Tarhiyat öncesi uzlaşma maddesi kullanıcının verdiği kalıba uyarlandı;
      talep edilmemiş hâli de aynı yapıda yazılıyor.
- [x] Tablolar içeriğe göre sığdırılıyor: kolon genişlikleri en uzun hücreden
      hesaplanıyor, sığmayan tabloda önce hücre boşlukları daraltılıyor,
      yetmezse punto oranlı olarak küçültülüyor (en az 7). Raporun tarhiyat
      tablosunda da boş iade sütunları yazılmıyor.
- [x] **Ceza tablosu ve uzlaşma bölümü.** Ceza tablosunun sütun başlıkları
      "Re'sen Tarh Edilecek KDV", "Bilerek Kullanılan Belgeler", "Vergi Ziyaı
      Cezası (3 kat)", "Bilmeden Kullanılan Belgeler", "Vergi Ziyaı Cezası
      (1 kat)" oldu; veri taşımayan sütunlar tabloya hiç girmiyor (tamamı
      bilerek kullanılmışsa bilmeden sütunları yazılmıyor). Uzlaşma bölümünde
      "hakkını kullanmıştır" yerine "tarhiyat öncesi uzlaşma talebi
      bulunmaktadır" yazılıyor; kısmen bilerek kısmen bilmeden kullanmada
      tarhiyatın dönem dönem uzlaşma kapsamındaki ve kapsam dışındaki kısmını
      gösteren tablo ekleniyor.
- [x] **Beyannamedeki "bu döneme ait indirilecek KDV" düzeltildi.** Beyanname
      PDF'inde bu satır, "oranlara göre dağılım" tablosunun toplamından
      okunuyordu; o tabloya "satıştan iade edilen, işlemi gerçekleşmeyen veya
      işleminden vazgeçilen mal ve hizmetler nedeniyle indirilmesi gereken KDV"
      (103) gibi kalemler de dağıtıldığından tutar şişiyor, 103+104+105 toplamı
      aynı tutarda eksiliyordu. Artık 108+109+110 kalemleri esas alınıyor; iki
      rakam farklıysa farkın nereden geldiğini söyleyen bir uyarı veriliyor.
      Kalemleri taşımayan eski biçim beyannamelerde dağılım toplamı kullanılmaya
      devam ediyor. — *kullanıcı bildirimi*
- [x] Fatura listesinde tarih, satıcı VKN, kayıt dönemi ve oran sütunlarına
      süzgeç eklendi. Tarih serbest metinle süzülüyor ("05.2023" o ayı, "2023"
      o yılı verir); diğerleri açılır listeden seçiliyor ve seçenekler diğer
      süzgeçlerden geçen satırlardan kuruluyor. Süzgeçler görünen kümeyi
      daralttığı için başlıktaki toplu seçim ve Excel aktarımı da aynı kümeye
      uyuyor.
- [x] **İptal/itiraz notu.** Satıcının faturaları arasında iptal/itiraz kaydı
      bulunanlar için, tutanak maddesinin ve rapor bölümündeki fatura
      tablosunun altına "gg.aa.yyyy tarihinde düzenlenen X numaralı fatura ile
      ilgili iptal/itiraz kaydı bulunduğu tespit edilmiştir." notu düşülüyor.
      Tarhiyata dahil edilmeyen faturalar tabloda görünmediğinden onlar için
      not "... söz konusu fatura tarhiyata dahil edilmemiştir." diye sürüyor.
- [x] **"Dikkat Edilmesi Gerekenler" kartı.** Bir dönemde listedeki
      faturaların KDV'si beyan edilen yurtiçi alımlara ilişkin KDV'yi aşıyorsa,
      Sonuç sekmesinde dönem dönem döküm veriliyor: beyan edilen tutar,
      listedeki fatura KDV'si, fazla tutar ve beyana oturan aday fatura
      birleşimleri. Aday önce **satıcı bütünlüğü korunarak** aranıyor —
      mükellef bir alışı beyan dışı bıraktığında bunu genellikle o satıcıyla
      olan alışlarının tamamıyla yapıyor. Aynı tutarı veren başka birleşim
      varsa sayısı yazılıyor; fatura bazında daha yüksek bir toplam mümkünse o
      da ayrıca belirtiliyor (bir satıcının faturalarını bölmek anlamına
      geldiği notuyla). "Faturaları beyana oturt" düğmesi, birleşim dışında
      kalan faturaların "Dahil" işaretini kaldırıp indirim reddini yeniden
      aktarıyor; böylece tarhiyat her zaman gerçek bir fatura kümesinin
      toplamına eşit kalıyor. Kart, adayların tespit değil varsayım olduğunu ve
      kesin belirlemenin defter kaydından yapılacağını açıkça yazıyor.
      (faturalar.dikkat_dokumu / altkume_secimi) — *kullanıcı bildirimi*
- [x] **"Mükellefe İlişkin Ek Bilgiler" bölümü genişletildi.** Vergi kimlik
      numarası, T.C. kimlik numarası ve faaliyet adresi künyeden alınıyor;
      boş bırakılırsa Çalışma Bilgilerine girilen değere düşülüyor. Faaliyet
      konusu tek satırlık metin olmaktan çıkıp (+) düğmesiyle satır eklenen
      bir alana dönüştü: birden çok faaliyet konusu varsa belgede
      "“a”, “b” ve “c” faaliyetleri ile iştigal etmektedir" biçiminde
      sıralanıyor. VKN ve TCKN birlikte girilirse ikisi de yazılıyor.
      Eski çalışmalardaki tek satırlık faaliyet konusu ilk satıra taşınıyor.
      — *kullanıcı isteği*
- [x] **Müfettişliğin çalışma adresi ayrı alan olmaktan çıkarıldı;**
      "Tutanağın düzenlendiği yer" kutusundan okunuyor — inceleme dairede ya
      da uzaktan yapıldığında tutanak da zaten o adreste düzenleniyor. Eski
      çalışmalardaki değer aktarılıyor. — *kullanıcı isteği*
- [x] **Seçilen satıcıların bütün faturaları belgelerde.** Fatura listesi
      mükellefin bütün alışlarını taşıyabildiğinden belgelere yalnızca **sahte
      belge düzenleyicisi olarak belirlenen** satıcılar giriyor: faturalarından
      en az biri "Dahil" işaretli olanlar ya da satıcı kartına bilgi
      (unvan, VTR, kullanma durumu, düzeltme…) girilmiş olanlar. Seçilen
      satıcının ise listedeki **bütün** faturaları tabloya giriyor — "Dahil"
      işareti kaldırılmış olanlar ve iptal/itiraz kaydı bulunanlar da.
      Mükellefin olağan alışları hiçbir yerde görünmüyor (fatura tablosu,
      DİKKAT notu, iptal açıklamaları, C bölümü dökümü).
      (`faturalar.sahteci_vknler`) Tarhiyat yine yalnızca indirim konusu yapıldığı anlaşılan
      faturalar üzerinden kuruluyor; aradaki farkın nedeni raporun C
      bölümünde, "İndirilecek KDV Hesabından Çıkarılacak Tutar" tablosunun
      hemen altında dört gerekçeye ayrılarak yazılıyor: iptal/itiraz kaydı,
      düzeltme beyannamesiyle çıkarılma, beyan edilen yurtiçi alımların
      aşılması, indirim konusu yapıldığının tespit edilememesi.
      (`satici_ozeti` artık `liste_*` rakamlarını da taşıyor.)
      — *kullanıcı isteği*
- [x] **DİKKAT notu artık listenin tamamına bakıyor.** Faturalar beyana
      oturtulup fazlası tarhiyat dışına alındığında not kayboluyordu; oysa
      mükellefin bazı alışlarını beyan dışı bırakmış olması tarhiyat
      düzeltilse de geçerli bir tespit. Ölçüt tarhiyata giren faturalar değil,
      listenin tamamı. Hiçbir satıcı maddesine düşmeyen dönemler için ayrı bir
      kırmızı not yazılıyor. — *kullanıcı bildirimi*
- [x] **İptal/itiraz sütunu.** Fatura tablosuna elle işaretlenebilen
      "İptal/itiraz" kutucuğu eklendi (önceden yalnızca portal dökümünde ayrı
      sayfa varsa işaretleniyordu). Faturası tarhiyata girmeyen satıcının
      iptal/itiraz açıklaması da artık belgede yer alıyor.
      — *kullanıcı bildirimi*
- [x] **Satıcıya ilişkin tespitler tutanağa da girdi.** Vergi Tekniği Raporu
      tarih/sayısı, raporun sonuç bölümündeki tespit (tırnak içinde) ve özel
      esaslar cümlesi yalnızca rapordaydı; artık tutanakta da her satıcının
      fatura dökümünden hemen önce yazılıyor. İki belge aynı üreteçten
      besleniyor (`satici_tespit_paragraflari`), böylece metinler birbirinden
      ayrışamıyor. — *kullanıcı bildirimi*
- [x] **Düzeltme beyannamesiyle çıkarılan satıcı tutanakta.** Faturaları
      düzeltmeyle indirimlerden çıkarılmış satıcı için tutanakta hiçbir şey
      yazmıyordu; artık hem tespit paragrafı ("… düzeltme beyannameleri ile
      ilgili dönem indirimlerinden çıkarıldığı tespit edilmiştir"), hem
      künyeye girilen düzeltme açıklaması, hem de beyannameler yüklüyse hangi
      dönemde hangi satırdan çıkarıldığının dökümü tutanakta yer alıyor —
      rapordakiyle aynı üreteçten. Düzeltme beyannamelerinin genel dökümü yine
      yalnızca raporun III. bölümünde. — *kullanıcı bildirimi*
- [x] Tutanakta madde numaraları kalın, madde gövdesi ince yazılıyor.
- [x] **DİKKAT notu.** Bir dönemde listedeki faturaların KDV'si, indirimden
      çıkarılabilecek tutardan (yurtiçi alımlara ilişkin KDV) fazlaysa, o
      dönemin faturalarını taşıyan tutanak maddesinin ve rapor bölümünün başına
      kırmızı ve kalın "DİKKAT: LİSTEDE BULUNAN İNDİRİLECEK KDV TUTARINDAN DAHA
      AZ İNDİRİLECEK KDV BEYAN EDİLMİŞTİR." notu düşülüyor; ilgili dönemler
      parantez içinde yazılıyor.
- [x] Fatura listesi, ekranda göründüğü hâliyle (yıl kulakçığı ve satıcı
      süzgeci neyi gösteriyorsa) tek sayfalık bir Excel dosyasına aktarılıyor.
      Tutarlar sayı olarak yazılıyor, TOPLAM satırı ekleniyor.
- [x] **İndirim aşımı uyarısı.** "Bu döneme ait indirilecek KDV" eksiye
      düşemez; dahası sahte belgelerin KDV'si yurtiçi alımlara ilişkin KDV
      içinden çıkarılır, en fazla o tutar kadar çıkarılabilir. İnceleme
      Tespitleri sekmesinde sınırı aşan dönemler kırmızı uyarıda dönem dönem
      listeleniyor (çıkarılan / sınır / fazla tutar) ve "Aşan dönemleri en fazla
      bu tutarla sınırla" düğmesi sunuluyor. İzgaradaki "ÇIKARMAYI YURTİÇİ
      ALIMLARLA SINIRLA" satırından ay ay da işaretlenebiliyor. İşaretli dönemde
      çıkarma sınırda duruyor; aşan tutar tarhiyata girmiyor ve bu belirtiliyor.
      Excel formülü de aynı şekilde MIN(...) ile kuruluyor. İndirimin tamamının
      reddi (defter ibraz edilmemesi) bilinçli bir iş olduğundan aşım
      sayılmıyor. Uyarı Sonuç sekmesindeki bulgu listesinde de görünüyor,
      belgelere girmiyor.
      (hesap.indirim_asimi_bulgulari, elestiri.indirim_sinirla)
- [x] Fatura listesine kayıt yılı kulakçıkları eklendi; satıcı VKN süzgeci ve
      başlıktaki toplu seçim kutucuğu seçili yılın içinde çalışıyor.
- [x] **Vergi dairesi adı tam yazılıyor.** Ekrana "liman" ya da "LİMAN VD"
      yazılsa da belgeye "Liman Vergi Dairesi Müdürlüğü" geçiyor; daire adının
      geçtiği kalıplarda ("... mükellefi ...") ilgi hali eki de ekleniyor:
      "Liman Vergi Dairesi Müdürlüğünün". Kurum adlarına gelen ek kesme
      işaretiyle ayrılmıyor. Tam yazılmış adlar ("Büyük Mükellefler Vergi
      Dairesi Başkanlığı") olduğu gibi korunuyor. (inceleme_kunyesi.daire_adi,
      turkce.ilgi_kurum)
- [x] Sonuç bölümündeki tarhiyat tablosu, maddelerin sonunda değil tarhiyatı
      öneren maddenin hemen altında duruyor ve vergi ziyaı cezası sütunu
      taşıyor. Ceza, bilerek/bilmeden ayrımına göre üç kat ve bir kat olarak
      paylaştırılmış tutardır; karma durumda maddenin kat ifadesi de buna göre
      yazılıyor.
- [x] **Defter ve belge ibraz etmeme raporu eklendi.**
      (`app/ibraz_etmeme_raporu.py`) Mükellef yasal defter ve belgelerini
      ibraz etmediğinde beyan edilen indirilecek KDV'nin KDVK 29 ve 34
      gereğince indirilebilirliği denetlenemez; **indirimlerin tamamı
      reddedilir** ve fark KDV VUK **30/3** uyarınca re'sen tarh edilir. Fiil
      aynı zamanda VUK **359/a-2**'de kaçakçılık suçudur: ceza **üç kat** ve
      raporla birlikte **VSR de üretilir**.

      Yapı müfettişin örnek raporundan: 1-GİRİŞ (isteme yazısı + ortaklık
      tablosu), 2-USUL, 3-HESAP (beyan tablosu), 4-TESPİT VE TENKİT (4.1
      re'sen takdir nedeni, 4.2.1 ibraz edilmemesi + tasdikli defterler,
      4.2.2 düzenlenen ve adına düzenlenen belgeler, 4.2.3 yasal
      düzenlemeler, 4.2.4 olması gereken tablo + tarhiyat), 5-SONUÇ.

      **Matrah kuralı:** beyan ile mükellefin DÜZENLEDİĞİ faturaların toplamı
      uyuşmadığında VUK 3/B gereği gerçek durum esas alınır — ama yalnızca
      mükellef **aleyhine** olan yönde. Faturalar beyandan azsa beyan esas
      alınır, matrah indirilmez. Hesaplanan KDV farkı faturaların kendi
      KDV'sinden gelir (`hesaplanan_otomatik` kapatılır), orana bölünmez:
      dökümde sıfır KDV'li satırlar bulunabiliyor.

      **Hesabı rapor değil `hesap.ibraz_etmeme_elestirisi` kuruyor** ve
      eleştiri alanlarına yazıyor; böylece tutanak, Excel ve sonuç bölümü
      aynı rakamları görüyor. Dolduran kullanıcı: "İbraz etmeme:
      indirimlerin tamamını reddet" düğmesi, girilmiş eleştiri varsa
      onaylatıyor — mevcut "Aşan dönemleri sınırla" düğmesinin kalıbı.
      Düğme ayrıca yılın başlangıç devrini sıfıra çekiyor; o devir de
      denetlenemeyen indirimlerden birikmiştir.

      Yeni künye bölümü "Defter ve Belge İbraz Etmeme Raporu": isteme
      yazısının tarih/sayısı, tebliğ tarihi ve teslim alan, ortaklık
      tablosu, mükellefin işe başlama/terk geçmişi (serbest metin, giriş
      paragrafının yerini alır). Satış/alış dökümleri Faturalar
      sekmesindeki `yon` alanından geliyor — yeni bir giriş yüzeyi yok.

      Mevzuat metinlerine VUK 30/3, 139, 253 ve 256 eklendi.

      Gerileme denetimi: `testler/ibraz_etmeme_testi.py`. Çapası örnek
      raporun kendi rakamları: yedi dolu ayın beyan tablosu → ödenecek
      **39.252,03** ve üç kat ceza **117.756,09**, ay ay da tutuyor.
- [x] **İbraz etmeme VSR'si örneğin yapısına getirildi.** Müfettişin ikinci
      örneği (ibraz etmeme VSR) geldi; yapı sahte belge VSR'sinden
      **farklı**: dört bölüm (1-GİRİŞ, 2-SUÇUN UNSURLARI, 3-SUÇUN FAİLİ,
      4-SONUÇ), "yapılan tespitler" bölümü ve tarhiyat önerisi tablosu
      **yok** — tarhiyat bilgileri ibraz etmeme raporunda yer alıyor.

      **359/a-2 madde metni artık birebir yazılı** (örnekten alındı); daha
      önce kasıtlı kırmızı yer tutucuydu. Dikkat: örnek 2022 tarihli ve hapis
      süresini "on sekiz aydan üç yıla" diye anıyor (5904 sayılı Kanun
      metni); 7394 sayılı Kanun bu süreyi değiştirdi, müfettiş inceleme
      yılında yürürlükte olan metni taslak üzerinde denetler.

      2.2'de kurumlarda VUK 10'a (kanuni temsilcilerin ödevi) dayanılıyor —
      failin temsilci olmasının dayanağı bu. Tasdikli defter tablosu
      künyedeki "İbraz edilen defterler" alanından geliyor; defterlerin
      VARLIĞI gizleme fiilinin ön koşulu. `defter_tasdik_makami` künye alanı
      kaldırıldı (tek satırlık makam adı yetmiyordu) ve `_tespitler`in ölü
      ibraz dalı silindi.
- [x] **Belge basım bilgileri tablosu eklendi — VARSA.** Müfettişin iki
      örneğinde de defter tasdik tablosunun yanında anlaşmalı matbaa /
      belge seri-numara aralığı tablosu var: tasdik kayıtları defterlerin,
      basım kayıtları da BELGELERİN varlığını ortaya koyuyor; gizleme
      fiilinin maddi unsuru ikisine birlikte dayanıyor.

      Yeni künye alanı `belge_basim_bilgileri` (İbraz Etmeme bölümünde,
      `ik.BELGE_BASIM_KOLONLARI`: anlaşmalı matbaa · belge teslim tarihi ·
      belge türü · seri no · başlangıç no · bitiş no · adet). İki örnek
      farklı sütun takımı kullanıyordu (birinde matbaa adı, diğerinde
      sisteme giriş tarihi); matbaa adlı takım alındı, "belge adedi"
      eklendi.

      **Yer tutucu KONULMUYOR**: bu bilgi her mükellefte yok (e-belgeye
      geçmişte hiç basım kaydı olmaz). Satır girilmediyse ne tablo ne de
      ona gönderme yapan cümle yazılıyor —
      `ik.belge_basim_satirlari` boş dönünce
      `ibraz_etmeme_raporu.belge_basim_tablosu` hemen çıkıyor
      (`_ortaklik_tablosu`un deseni). Müfettişin isteği buydu: "ama sorsun
      varsa eklesin".

      İki yere giriyor: ibraz etmeme raporunun 4.2.1'inde tasdik
      tablosundan sonra (kendi sorgulama cümlesiyle) ve ibraz VSR'sinin
      2.2'sinde tasdik tablosundan ÖNCE — örnek orada iki tabloyu tek
      cümleyle duyuruyor, o yüzden tablo oraya `cumle=False` ile çağrılıyor
      ve cümle "defter bilgileri **ve belge basım bilgilerinin**" diye
      kuruluyor (basım kaydı yoksa yine "defter bilgilerinin").

      Denetim: `ibraz_etmeme_testi.py` ve `vsr_testi.py` hem dolu hem boş
      hâli, sütun başlıklarını ve VSR'de tablo sırasını denetliyor; üç
      mutasyonla (koşulu kaldır, cümleyi koşulsuz yaz, tablo sırasını
      değiştir) kızardığı doğrulandı.
- [x] **İbraz etmeme VSR'sinde maddi unsur delil zincirine bağlandı.**
      Müfettişin isteği (2026-10-16): "diğer VSR ile kıyasla maddi unsur ve
      delilleri ibraz etmemeye göre hazırla". Sahte belge VSR'si maddi
      unsuru somut delillere bağlıyor (satıcı başına VTR, defter kayıtları,
      beyana dahil edilme, indirimler içindeki pay); ibraz etmemede 2.2
      yalnızca hukuki çerçeve + isteme yazısı + tablolardan ibaretti.

      Artık **"Fiile İlişkin Tespit ve Deliller"** başlığı altında beş
      numaralı madde yazılıyor:

      1. defterlerin (ve basım kaydı varsa belgelerin) **varlığı** —
         tasdik/basım tabloları; basım kaydı yoksa cümle yalnızca
         defterlerle sınırlı kalıyor (yoksa belgelerin varlığı tasdik
         kaydından çıkarılmış olurdu — hatalı olur)
      2. usulüne uygun **isteme** — yazı, tebliğ, yasal süre
         (`_ibraz_yazisi_paragrafi`a `onek` parametresi eklendi, madde
         numarasını alıyor)
      3. defterlere **kaydı gereken işlemlerin bulunduğu** —
         `_ibraz_islem_delili`, GİB belge dökümünden adet ve matrah.
         Sahte belgede bu yeri "yevmiye defteri kayıtlarında kaydedildiği"
         tespiti tutuyor; ibraz etmemede defter YOK, delil döküm.
         **Döküm girilmemişse sayı uydurulmuyor**, kırmızı yer tutucu ne
         yapılacağını söylüyor.
      4. **mücbir sebep** bulunmadığı (VUK 13) — ibraz etmeme savunmasının
         tipik dayanağı; raporun bunu kapatması gerekiyor
      5. **netice**: indirimlerin reddi ve vergi ziyaı. Tutar ibraz etmeme
         raporuna ATFEN anılıyor, bu rapor tarhiyat önermiyor (örnek de
         önermiyor).

      Zincir "tespit ve deliller bir arada değerlendirildiğinde ... maddi
      unsurun oluştuğu" cümlesiyle kapanıyor. `liste` (faturalar) bunun
      için `rapor_uret` → `_unsurlar` → `_ibraz_maddi_unsur` boyunca
      taşındı. Beş mutasyonla denetlendi.
- [x] **Re'sen takdir nedeni: 30/3 ve 30/6 birlikte.** Müfettişin kararı
      (2026-10-20): "ibraz etmeme raporunda re'sen tarh nedenine hem VUK
      30/3 hem de 30/6 olarak girelim, ikisi de olmalı".

      İki bendin dayandığı tespit AYRIDIR ve rapor bunu yazıyor:
      - **30/3** — defter ve belgelerin ibraz edilmemesi
      - **30/6** — düzenlenen belgelerin bir kısmının beyannamelere
        yansıtılmamış olması, yani "verilen beyannamelerin gerçek durumu
        yansıtmadığına dair delil"

      Dayanak DELİLE bağlı olduğundan 30/6 **yalnızca matrah ilavesi
      yapılan dosyalarda** anılıyor; delil yokken o bende dayanmak raporu
      itiraz edilebilir kılar. Matrah ilavesi yoksa eskisi gibi tek başına
      30/3 yazılıyor. (`_resen_dayanagi`, ölçüt `_matrah_ilavesi_var`.)

      Atıf dört yerde birden güncelleniyor: 4.1 (iki madde metni + hangi
      tespite dayandığını anlatan paragraf), 4.2.4 ve sonuç bölümündeki
      5.1 maddesi. Yazım da bent biçimine geçti: "30/3. maddesi" yerine
      "30 uncu maddesinin (3) ve (6) numaralı bentleri".
- [x] **Fazla hesaplanmış KDV de beyan edilmek zorundadır.** Müfettişin
      sözü: "asıl önemli olan faturada tahsil edilen KDV, fazla hesaplasa
      da beyan etmek zorunda". Uygulama zaten faturanın KENDİ KDV'sini
      esas alıyordu (orana bölmüyor); artık raporda gerekçesi de yazılı:
      KDVK 8/2 uyarınca belgede gösterilen KDV, kanunen hesaplanması
      gerekenden fazla dahi olsa beyan edilip ödenmesi gereken vergidir.
- [x] **Excel çıktısındaki ceza katı da dönem dönem.** Müfettişin isteği
      (2026-10-20). Tarhiyat sayfası katı tek formülle (`re'sen × kat`)
      bütün dönemlere uyguluyordu; üç kat uygulanan dosyalarda matrah
      farkından doğan paya da üç kat yazıyor ve Word raporuyla
      tutmuyordu.

      `_ceza_formulu` artık Word'deki ayrımın aynısını kuruyor ve formülü
      **canlı** tutuyor (tutarlar sayfada değişince ceza da değişir):

          =MIN(re'sen; MAX(eleştirili Toplam KDV − beyan Toplam KDV; 0))
           + (re'sen − o pay) × kat

      Bir kat uygulanan dosyalarda formül sadeleşiyor (`re'sen × 1`);
      ayrıştırmanın anlamı yok.

      Denetim `ceza_testi.py` 7. bölümde: formülün atıf yaptığı satırların
      gerçekten "Toplam KDV" satırları olduğu doğrulanıyor ve formülün
      aritmetiği dönem dönem motorun `vergi_ziyai_cezasi` değeriyle
      karşılaştırılıyor — Excel'i açan müfettiş Word raporundakinden başka
      bir rakam görmemeli. İki mutasyonla sınandı (eski tek formüle dön,
      yanlış satıra atıf yap).

      Not: LibreOffice bu ortamda üretilen dosyayı açamadığı için formül
      bir hesap motorunda ÇALIŞTIRILARAK değil, atıfları çözülüp
      aritmetiği denetlenerek doğrulandı.
- [x] **KDV'si sıfır belgeler beyan dışı olmayabilir: istisna / özel
      matrah uyarısı.** Müfettişin tespiti (2026-10-20): beyan dışı
      sandığı faturaların KDV'si sıfırdı ve bunlar **özel matrah şekline
      tabi işlem** olarak beyan edilmişti — yani beyan dışı değillerdi.

      Kök sorun kavramsal: matrah karşılaştırması beyannamenin "MATRAH
      TOPLAMI" satırına bakıyor, ama istisna kapsamındaki teslimler ve
      özel matrah şekline tabi işlemler o satırda YER ALMAZ; ayrı
      bölümlerde beyan edilir. Dolayısıyla KDV'si sıfır bir belge
      "beyan edilmemiş" gibi görünür.

      Uygulama artık bunları ayrı sayıyor ve beyannamenin ilgili
      bölümleriyle karşılaştırıyor (`tam_istisna_teslim`,
      `kismi_istisna_teslim`, `istisna_toplam_teslim`,
      `ozel_matrah_bedel`; istisna toplamında tam+kısmi ile toplam
      satırının büyüğü alınır ki aynı tutar iki kez sayılmasın).

      - `satis_donem_toplamlari`: `kdvsiz_adet` / `kdvsiz_matrah`
      - `satis_beyan_farki`: `beyan_istisna`, `beyan_ozel_matrah`
      - Satış kartında uyarı tablosu: Dönem | KDV'siz Belge | KDV'siz
        Matrah | Beyanda İstisna | Beyanda Özel Matrah | **Açıkta Kalan**
      - "Dikkat Edilecek Noktalar"a bulgu (`kdvsiz_satis`): beyanda
        karşılığı varsa "bu belgeler beyan dışı olmayabilir", yoksa
        "beyannamede tutar görünmüyor" diyor.

      **Otomatik çıkarma YAPILMIYOR**: hangi belgenin hangi istisnaya
      girdiği belge bazında bilinmiyor, karar müfettişindir. Uygulama
      rakamları yan yana koyup "denetleyin" diyor — müfettişin istediği
      de buydu ("en azından bir uyarı notu koysun").

      **Rapor da susmuyor** (müfettişin eki: "hatta rapora bir paragraf
      eklesin"). 4.2.4'te, matrah/KDV tablosunun hemen ardında: KDV'si
      sıfır belgelerin tutarı, beyannamenin istisna / özel matrah
      bölümlerindeki karşılığı ve — varsa — açıkta kalan tutar yazılıyor.
      Paragraf, bu tutarlar üzerinden **hesaplanan KDV'ye ilave
      yapılmadığını** da söylüyor; raporu okuyanın ilk soracağı şey bu.
      Hiç karşılığı yoksa "herhangi bir beyan bulunmadığı görülmüştür"
      diyor (sıfırlı garip cümle kurmuyor). KDV'si sıfır belge yoksa
      paragraf hiç yazılmıyor. `_beyan_ozeti` bunun için `istisna_teslim`
      ve `ozel_matrah` alanlarını da taşıyor.

      Denetim: `ibraz_etmeme_testi.py` 7. bölüm, iki mutasyonla
      doğrulandı. Not: ilk yazdığım denetim boş listede ÇÖKÜYORDU ve
      kendisinden sonraki denetimleri gizliyordu; mutasyon bunu da
      ortaya çıkardı, denetim çökmeyecek biçimde yeniden yazıldı.
- [x] **Ölçü “hesaplanan KDV” değil, beyannamenin TOPLAM KDV satırı.**
      Müfettişin kararı (2026-10-20): "tabloda hesaplanan KDV sütunu deme
      de toplam KDV sütunu koy". Doğrusu bu: Toplam KDV = hesaplanan +
      ilave edilecek, yani ölçüyü anlatmak için iki kalemi toplamaya gerek
      yok, beyannamenin kendi satırı zaten o.

      Sütunlar: "Düzenlenen Belgelerin KDV’si | Beyan Edilen Toplam KDV |
      Toplam KDV’ye İlave". Tablo adı da "...Matrah ve Katma Değer Vergisi
      İlavesi" oldu. Arayüzdeki satış kartında da KDV grubu üç sütuna
      indi; beyan hücresinin üzerine gelince hesaplanan / ilave edilecek
      dağılımı ipucu olarak görünüyor.

      Hesapta ölçü `max(toplam_kdv, hesaplanan + ilave_edilecek)`.
      **Büyüğü alınıyor**, çünkü yeni beyanname biçiminde tutarı sıfır
      olan bölüm hiç basılmıyor: okunamayan bir "TOPLAM KDV" satırı
      sessizce sıfır görünür ve beyan edilmiş vergi yeniden tarh edilirdi
      (bkz. tuzaklar, beyanname okuyucusu).
- [x] **Hesaplanan KDV karşılaştırması da gösteriliyor.** Müfettişin
      isteği (2026-10-20): "uygulama faturalarda hesaplanan KDV ile
      beyannamede bulunan hesaplanan KDV kıyaslaması da yapsın".
      Karşılaştırmayı motor zaten yapıyordu (bir önceki düzeltme), ama
      hiçbir yerde GÖRÜNMÜYORDU — matrah ilavesi büyükken KDV ilavesinin
      sıfır çıkması hesap hatası gibi duruyordu.

      `faturalar.satis_beyan_farki` artık KDV tarafını da taşıyor:
      `fatura_kdv`, `beyan_hesaplanan`, `beyan_ilave_edilecek`,
      `beyan_kdv` (ikisinin toplamı, ölçüt), `kdv_fark`.

      Satış kartındaki tablo iki gruplu başlığa geçti: **Matrah**
      (Faturalar / Beyan / İlave) ve **Hesaplanan KDV** (Faturalar /
      Beyan Hspl. / Beyan İlave Edil. / İlave). Beyan edilen hesaplanan
      ile ilave edilecek AYRI sütunlarda; verginin nerede beyan edildiği
      böylece görünüyor.

      İbraz etmeme raporunun tablosu da genişledi ve adı değişti: "Beyan
      Edilmeyen Belgelere İlişkin Matrah **ve Hesaplanan Katma Değer
      Vergisi** İlavesi". Yeni sütunlar: Düzenlenen Belgelerin Hesaplanan
      KDV'si | Beyan Edilen Hesaplanan KDV | Hesaplanan KDV'ye İlave.
      Önüne de ölçünün hesaplanan + ilave edilecek toplamı olduğunu ve
      matraha ilave yapılan bir dönemde vergiye ilave gerekmeyebileceğini
      anlatan bir paragraf eklendi — rapora itiraz eden, tablodaki "—"yi
      görüp soracaktır.
- [x] **Ödenecek KDV iki katına çıkıyordu: “İlave Edilecek KDV” satırı.**
      Müfettiş raporun kendi çıktısından yakaladı (2026-10-20): Ocak'ta
      matrah beyan edilmemiş, satış faturasının KDV'si 1.125 TL, ama
      yeniden düzenlenen tabloda ödenecek KDV **2.250 TL** çıkıyordu.

      Sebep: mükellef matrahı hiç beyan etmemiş ama faturanın 1.125 TL
      KDV'sini beyannamenin **“İlave Edilecek KDV”** satırında beyan
      etmişti. `matrah_ilavesi_yaz` hesaplanan KDV ilavesini yalnızca
      `hesaplanan_kdv` ile karşılaştırdığından (0) aynı vergiyi bir kez
      daha ekliyordu: 1.125 (beyandaki ilave edilecek) + 1.125 (eklenen
      hesaplanan) = 2.250.

      Ölçüt artık o dönemde **beyan edilen toplam hesaplanan vergi**:
      `hesaplanan_kdv + ilave_edilecek_kdv`. Fark eksiye düşerse
      eklenmiyor (beyan esas, yalnızca aleyhe yön).

      İkinci ve bunu görünmez kılan kusur: beyan dökümü tablosunda
      **“İlave Edilecek KDV” sütunu hiç yoktu**. Mükellefin kendi
      beyanında Ocak şöyle görünüyordu: matrah 0, hesaplanan 0, indirimler
      2.442,75, ödenecek 0, devir 1.317,75 — aradaki 1.125 TL tabloda
      hiçbir yerde yok ve tablo kendi içinde tutmuyordu. Sütun artık
      **tutar taşıyan dosyalarda** yazılıyor (taşımayanlarda tabloyu boş
      yere genişletmemek için koşullu, tarhiyat tablosundaki iade
      sütunlarının deseni). Hem beyan edilen hem yeniden düzenlenen tablo
      artık kendi içinde tutuyor.

      İki mutasyonla denetlendi (eski ölçüte dön, sütunu hiç yazma).
- [x] **İptal/itiraz tiki kaldırılınca matrah ilavesi güncellenmiyordu.**
      Müfettiş bildirdi (2026-10-19): "düzenlediği belgelerin 2 adedinde
      iptal itiraz kaydı var ancak onaylanmamış olduğu için matraha dahil
      etmem gerek. Tikleri kaldırıyorum ancak yine de matraha dahil
      etmiyor. Kısacası tik yoksa hesaba dahil edilmeli."

      Tik DOĞRU çalışıyordu: `satis_donem_toplamlari` tiki kalkan faturayı
      hemen görüyor. Sorun matrah ilavesinin **tek seferlik** yazılmasıydı
      — "İbraz etmeme: indirimlerin tamamını reddet" düğmesi onu bir kez
      eleştiriye yazıyor, sonraki fatura değişiklikleri o rakama
      yansımıyordu. Ekran dökümle tutmayan bir ilave gösteriyordu.

      - `hesap.matrah_ilavesi_yaz` ayrı bir işleve çıkarıldı; hem ibraz
        etmeme kuralı hem yeni akış onu çağırıyor (tek hesap). Döküm artık
        ilave gerektirmiyorsa **önce yazılmış tutarı da kaldırıyor** —
        yoksa tik geri konulduğunda asılı kalırdı.
      - Yeni uç `/api/matrah_ilavesi` ve satış kartında **"Matraha Aktar"**
        düğmesi: yalnızca matrah/hesaplanan KDV ilavesini günceller,
        indirim reddine dokunmaz.
      - Satış kartındaki tablo artık "Gereken Matrah İlavesi" ile
        "Tespitlerde Girili" sütunlarını yan yana gösteriyor; tutmayan
        hücreler kırmızı ve kart ne yapılacağını yazıyor. Alış tarafındaki
        `uygulama_farki` deseninin aynısı.

      Önceki turda satış kartına bilinçli olarak aktarım düğmesi
      koymamıştım ("ikinci bir yol rakamları ayrıştırır" diye); o karar bu
      çıkmazı doğurdu. Düğme artık var ama ayrı bir hesap yapmıyor, aynı
      işlevi çağırıyor.

      Tarayıcıda uçtan uca denendi: tik kalkınca kart farkı kırmızı
      gösteriyor, düğmeden sonra iki sütun eşitleniyor.
- [x] **Ceza katı artık KAYNAĞA göre: matrah farkı 1 kat, indirim reddi
      3 kat.** Müfettişin kararı (2026-10-19): "matrah farkından
      kaynaklanan tutarlara uygulanacak vergi ziyaı cezası 1 kat, ancak
      defter belge ibraz etmemekten yani indirimlerin reddinden doğan
      vergi ziyaı cezası 3 kat olacak".

      Dayanağı: matrah ilavesi VUK 359'da yazılı bir fiile dayanmaz, 344/1
      → bir kat. İbraz etmeme ise 359/a-2'de kaçakçılık suçudur, 344/2 →
      üç kat.

      Ayrım **motorda** yapılıyor (`hesap._tarhiyat_satiri`, yeni
      `matrah_kati` parametresi), rapor yalnızca yazıyor. Böylece ekran,
      Excel ve rapor aynı rakamı görüyor — iki yerde hesaplanan ceza
      birbirini tutmazdı. Ölçüt toplam KDV'deki artış: matrah ilavesi
      hesaplanan KDV'yi yükseltir, indirim reddi indirimleri düşürür.
      Pay önce matraha verilir; iki kaynak birlikteyken devir tarhın bir
      kısmını soğurduğunda düşük katı uygulamak mükellef lehinedir.

      Yeni alanlar: `ceza_matrah_payi`, `ceza_indirim_payi`,
      `ceza_matrah`, `ceza_indirim`; `vergi_ziyai_cezasi` artık ikisinin
      toplamı. `web_server._hesapla` üç kat uygulanan dosyalarda
      `matrah_kati=1` geçiyor.

      İbraz etmeme raporunda ceza, tarhiyat tablosundan ayrılıp **kendi
      bölümüne** taşındı (sahte belge raporunun deseni). Tablo:
      Dönemi | Re'sen Tarhı Gereken KDV | Beyan Dışı Bırakılan
      Belgelerden | İbraz Etmemeden (İndirim Reddi) | VZC (1 kat) |
      VZC (3 kat) | VZC Toplamı. Matrah payı hiç yoksa tablo üç sütuna
      daralıyor ve tek cümle yazılıyor — boş sütun rakamları alt satıra
      düşürüyordu. Sonuç bölümündeki 5.1 maddesi de iki katı ayrı ayrı
      istiyor; tek cümleyle "üç kat" demek tabloyla çelişirdi.

      Üç mutasyonla denetlendi (ayrımı kaldır, payları çakıştır, tabloyu
      daralt).
- [x] **Ceza katı artık tespitlerden türetiliyor (iki kaynak sorunu).**
      Müfettiş "hâlen 1 kat geliyor" dedi (2026-10-19). Önceki düzeltme
      ceza TABLOSUNU düzeltmişti ama tarhiyat tablosundaki "Vergi Ziyaı
      Cezası" sütunu BAŞKA bir kaynaktan besleniyordu: Tarhiyat Özeti
      sekmesindeki açılır kutu (`ziya_kati`), **varsayılanı 1 kat**.
      Yani rapor metni tespitlerden "üç kat" derken tablo kutunun
      varsayılanını yazıyordu ve kimse kutuyu değiştirmeyi hatırlamak
      zorunda kalmamalıydı.

      `_ziya_kati` artık, çalışmada açıkça 1 ya da 3 seçilmemişse katı
      TÜRETİYOR: satıcılarda "Bilerek kullanma" varsa (359/b) ya da
      künyede "Defter ve belge ibrazı = İbraz edilmedi" ise (359/a-2) üç
      kat, aksi halde bir kat. Müfettişin elle seçimi her zaman üstündür.

      Kutuya "Otomatik (tespitlere göre)" seçeneği eklendi ve varsayılan o
      oldu. Yanında hangi katın uygulandığı ve gerekçesi yazıyor; elle
      seçim tespitlerle çelişiyorsa kırmızı uyarı çıkıyor ("elle 1 kat
      seçtiniz, tespitler 3 kat gerektiriyor... tablo ile çelişebilir").
      `/api/hesapla` yanıtı `ziya_kati` ve `ziya_kati_turetilen` taşıyor.

      **İbraz etmeme de 359 kapsamındadır** (müfettişin sözü): satıcı
      nitelendirmesi hiç olmasa bile üç kat. `ceza_dagilimi` de bunu
      biliyor — yeni `dayanaksiz_kat` parametresi, ibraz etmeme halinde
      sahte belgeye atfedilemeyen kalan tutara da üç kat uyguluyor.

      Üç mutasyonla denetlendi; tarayıcıda hem otomatik hem elle seçim
      hâli doğrulandı (uyarı metni dahil).

      Bilinen sınır: Excel çıktısındaki tarhiyat sayfası katı tek bir
      formülle bütün dönemlere uyguluyor. İncelenen yıllardan sonraki
      devir düzeltme yıllarında ceza bir kat olmalı; Word raporunda o
      tablo ceza sütunu taşımadığı için sorun çıkmıyor, Excel'de
      çıkabilir.
- [x] **Ceza tablosu metinle çelişiyordu: fatura satırı olmayan dönemler
      bir kat yazılıyordu.** Müfettiş bildirdi (2026-10-19): "vergi ziyaına
      ilişkin açıklamaya 3 kat kesilmesi gerek demişsin ancak tabloda 1 kat
      kesmişsin, tabloda da 3 kat olmalı".

      Sebep `faturalar.ceza_dagilimi`de: ceza katı **fatura satırlarından**
      belirleniyordu. Fatura dökümü her dönemi kapsamıyor olabilir —
      müfettiş indirim reddini beyandan okuyup elle girdiğinde o dönemde
      satır bulunmaz, `red_toplam` sıfır çıkar ve tutar "dayanaksız"
      sayılıp **bir kat** yazılırdı. Rapor metni "üç kat uygulanması
      gerekmektedir" derken tablo bir kat gösteriyordu.

      Artık **tespitten doğan kısım da** dosya geneli kategori karmasıyla
      dağıtılıyor (devir payında zaten böyleydi). Ölçüt motorun kendi
      ayrıştırması: `fark_tespit["odenecek"]`.

      **Matrah ilavesi bunun dışında**, bir kat kalıyor: o 359 kapsamında
      bir fiil değil. Ayrım yine motordan geliyor —
      `fark_tespit["toplam_kdv"]` matrah/hesaplanan KDV ilavesinden,
      kalanı indirim reddinden gelir. İki mutasyonla denetlendi (tespit
      payını geri çıkar → eski hata; matrah ilavesini de üç kat yap →
      yakalanıyor).

      `ceza_testi.py` bu kararı kodluyordu ve değişti: "fatura satırı
      olmayan indirim reddi bir kattır" denetimi, yerini "üç kattır"a
      bıraktı. İki katın birlikte bulunduğu dosyayı kuran yeni bir
      `karma_ornek()` eklendi (Ocak sahte belge üç kat + Şubat matrah
      ilavesi bir kat); tablo sütunları ve uzlaşma ayrımı bölümleri artık
      onu kullanıyor.
- [x] **Matrah ilavesinin dayanağı VUK'tan KDV Kanununa taşındı.**
      Müfettişin kararı (2026-10-19): "beyan edilmeyen faturaların matraha
      eklenmesine ilişkin paragrafa Vergi Usul Kanunu delili sunma, ona
      ilişkin KDV Kanununda madde var — fatura düzenlendiyse veya KDV
      hesaplandıysa beyan zorunlu".

      4.2.4'teki gerekçe artık VUK 3/B değil, KDVK'nın kendi zinciri:

      - **1/1** verginin konusu (teslim ve hizmetler)
      - **2** teslim, **3** teslim sayılan haller
      - **20** matrah = işlemin karşılığını teşkil eden bedel
      - **10/a-b** vergiyi doğuran olay. (b) bendi belirleyici: teslimden
        ÖNCE fatura verilmişse, **belgede gösterilen miktarla sınırlı
        olmak üzere** faturanın düzenlenmesi anında vergiyi doğuran olay
        meydana gelir → fatura düzenlenmişse vergi doğmuştur
      - **8/2** vergiye tabi bir işlem olmasa DAHİ vesikada KDV
        gösterenler o vergiyi ödemekle mükelleftir → faturada KDV
        hesaplanmışsa beyan ve ödeme zorunludur
      - **40** beyan esası; işlemi olmayan mükellef dahi beyanname verir

      Maddelerin metinleri `mevzuat.py`ye eklendi (`kdv_1`, `kdv_2`,
      `kdv_3`, `kdv_8_2`, `kdv_10`, `kdv_20`, `kdv_40`) ve 4.2.3'e
      **yalnızca matrah ilavesi varsa** giriyor — ilave yokken rapora
      ilgisiz hüküm doldurmak okuyanı yorar. İki mutasyonla denetlendi.

      Not: bu madde metinleri de bilgiden yazıldı, birincil kaynaktan
      doğrulanmadı (bkz. "İbraz etmemede bekleyen"). 1, 2, 3, 8/2, 10, 20
      ve 40 esasa ilişkin olarak uzun süredir değişmedi, yine de taslak
      üzerinde bir kez denetlenmeli.
- [x] **Sürüm damgası, port uyarısı ve paketin gerçekten teslim edilmesi.**
      Müfettiş "deniyorum yine aynı uygulama geliyor" dedi (2026-10-19).
      Sebep koddaki bir değişiklik değil, **teslimdi**: `surumler/`
      klasörüne kopyalama OKUBENI.md'de elle bir adım olarak yazılıydı ve
      üç tur boyunca atlandı — paketleyici her seferinde yeni paket üretti,
      kullanıcıya ise `surumler/` içindeki 16 Ekim tarihli dosya gitti.

      Üç düzeltme:

      1. **Paketleyiciler `surumler/`e kendileri kopyalıyor.** Elle adım
         atlanabilir; betik atlamaz. OKUBENI.md'deki `cp` yönergesi kalktı.
      2. **Sürüm damgası.** Paketleyiciler `surum.txt` yazıyor (tarih + git
         kısa kimliği); `web_server.surum_damgasi` okuyor, `/api/tanimlar`
         taşıyor, arayüz sağ üstte gösteriyor. Geliştirme ağacında
         "geliştirme sürümü" yazar. Hangi kopyaya bakıldığını başka hiçbir
         şey söylemiyordu.
      3. **Port kayması artık sessiz değil.** Uygulamanın önceki kopyası
         8766'yı tutuyorsa yeni kopya 8767'ye kayıyordu ve kullanıcının
         tarayıcısındaki eski adres ESKİ sürümü göstermeye devam ediyordu.
         `main.py` bunu yüksek sesle yazıyor; rozet de portu gösteriyor ve
         8766 değilse uyarı rengine dönüyor.

      Ayrıca **`guncelle.bat`in denetimi sahteydi**: kopyalama sonrası
      yıllardır kaynakta duran `YENI_BICIM_SIFIRLAR` metnini arıyordu. O
      metin ESKİ sürümde de bulunduğundan, dosyalar hiç yenilenmese bile
      "GÜNCELLEME TAMAM" diyordu. Ölçüt artık sürüm damgasının birebir
      eşitliği (`fc /b`), ve `guncelleme_paketle.sh` hem damganın pakette
      olmasını hem betiğin onu karşılaştırmasını denetliyor — eski ölçüte
      dönülürse paket üretilmiyor. (Bu denetimi damgayı pakete koymayı
      bırakarak sınadım: paket üretilmedi.)
- [x] **Alış ve satış fatura listeleri ayrıldı.** Müfettiş bildirdi
      (2026-10-19): "uygulamaya satış faturalarını ekledim ancak listenin
      altında indirim reddine aktar butonu ve tablosu çıktı. mükellefin
      düzenledikleri matraha eklenir aldıkları indirime onun için
      ayrıştırılması gerek".

      Faturalar sekmesine **yön kulakçığı** geldi: "Alış Faturaları —
      indirim" / "Satış Faturaları — matrah" (yönü belirsiz satır varsa
      üçüncü kulak). Liste, yıl kulakçıkları, süzgeçler ve toplam satırı
      artık seçili yöne ait. Toplam satırında ölçüt de yöne göre değişiyor:
      alışta "dahil" işaretli satırlar (indirim reddine girecekler),
      satışta iptal edilmemiş bütün satırlar — "dahil" alış tarafının
      kavramı, satış satırlarında hep boş olduğundan toplamı sıfır
      gösterirdi.

      **"İndirim Reddine Aktar" kartı yalnızca alış kulağında.** Satış
      kulağında onun yerine "Satış Faturaları — Matrah" kartı var: dönem
      dönem düzenlenen fatura matrahı / beyan edilen matrah / matraha ilave
      karşılaştırması (`faturalar.satis_beyan_farki`, `/api/fatura_ozet`
      içinde). Orada **aktarım düğmesi yok**, bilinçli: matrah ilavesini
      ibraz etmeme kuralı yazıyor, ikinci bir yol rakamları ayrıştırırdı —
      kart bunun yerine o düğmeye yönlendiriyor.

      Tarayıcıda denendi (Playwright): alışta aktar kartı açık / satış
      kartı kapalı, satışta tersi; konsol hatası yok.
- [x] **İbraz raporunda matrah ilavesinin değerlendirmesi yazıldı.**
      Müfettişin isteği: "değerlendirme kısmına da bir paragraf açıklama
      ekle beyan edilmeyen faturaların matraha eklenmesine ilişkin".
      Tarhiyatın en tartışmalı kalemi tek cümleyle geçiyordu.

      4.2.4'te artık dört paragraf + tablo: (1) tespit — düzenlenen
      belgelerin toplamı beyanla uyuşmuyor, (2) ölçüt — defter ibraz
      edilmediğinden beyanın doğruluğu denetlenemez, VUK 3/B gereği gerçek
      mahiyet esas ve mükellefin kendi düzenlediği belge en güvenilir
      dayanak, (3) yöntem — karşılaştırma dönem dönem, yalnızca aleyhe
      yönde ilave; belgeler beyandan azsa beyan esas (döküm teslimlerin
      tamamını kapsamayabilir), hesaplanan KDV belgelerin kendi KDV'sinden
      alınır, orana bölünmez, (4) tablo — dönem / belge adedi / fatura
      matrahı / beyan / ilave, TOPLAM satırlı. İlave yapılmayan dönemler
      tabloya girmiyor.

      4.2.2'ye de iki dökümün işlevini ayıran bir paragraf eklendi:
      düzenlenen belgeler matrahın, adına düzenlenenler indirimin
      dayanağı. Üç mutasyonla denetlendi.
- [x] **İbraz etmemede matrah ilavesi hiç yapılmıyordu: yön tayini.**
      Müfettiş sahada bildirdi (2026-10-19): "mükellefin düzenlediği ancak
      beyan etmediği faturaları matraha ekleme işlemini yapmamış".

      Sebep `faturalar.normalize`de: dökümde hem alıcı hem düzenleyen sütunu
      yoksa (`_taraf_sutunu_var` yanlış) VKN'ye **hiç bakılmadan** ALIŞ
      yazılıyordu. Mükellefin kendi düzenlediği belgelerin dökümü ise çoğu
      zaman tek taraflıdır (yalnızca düzenleyen sütunu) — bu döküm alış
      sayılınca `satis_donem_toplamlari` boş dönüyor ve matrah ilavesi
      sessizce hiç yapılmıyordu.

      Artık tek taraflı dökümde de VKN karşılaştırması yapılıyor, ama
      **yalnızca açıkça girilmiş VKN ile**. Bu ayrım kritik: ilk denemem
      tahmin edilen VKN'yi (`_ortak_vkn`) de kullanıyordu ve tek satıcılı
      bir ALIŞ listesinde satıcıyı "mükellef" sanıp bütün listeyi satışa
      çeviriyordu — indirimler bir anda yok olurdu. Kendi testim yakaladı;
      sekiz yön durumu artık `ibraz_etmeme_testi.py` 0. bölümünde ve iki
      mutasyonla (eski davranışa dön / tahmine güven) denetlendi.

      Not: VKN Çalışma Bilgilerine girilmemişse tek taraflı satış dökümü
      hâlâ alış sayılır. Bilinçli: tahmine güvenmek yukarıdaki felaketi
      doğuruyor. Arayüz iletisi artık bunu söylüyor.
- [x] **"Matrahlar yükseltildi" iletisi yalan söylüyordu.** İbraz etmeme
      düğmesinin iletisi her durumda "matrahlar düzenlenen faturalara göre
      yükseltildi" diyordu — düzenlenen fatura hiç girilmemişken de. Uç
      artık bir `ozet` döndürüyor (`indirim_donem`, `matrah_donem`,
      `satis_adet`, `donemsiz_satis`) ve arayüz dört ayrı ileti veriyor:
      yükseltildi / satış faturası yok (uyarı) / kayıt dönemi çözülemedi
      (uyarı) / ilave gerekmedi (beyan esas).
- [x] **Kural uygulanmadan ibraz raporu inmiyor.** Kural elle uygulanıyor
      (düğme); uygulanmadan rapor indirilirse belge "indirimlerin tamamı
      reddedilmiştir" der ama tablolar boş çıkar ve bu çelişki vergi
      dairesine gider. `_ibraz_raporu_hazirla` artık hiçbir dönemde
      reddedilen indirim **ve** matrah ilavesi yoksa anlaşılır bir hatayla
      duruyor. Elle girilmiş eleştiri varsa engel yok.
- [x] **359 hapis süreleri 7394 sayılı Kanunla değişik hâle getirildi.**
      Müfettişin isteği: "sen kanunun son hâlini ekle". Örnek raporlar 2022
      tarihliydi ve eski süreleri anıyordu. (a) fıkrası on sekiz aydan
      **beş** yıla, (b) fıkrası üç yıldan **sekiz** yıla; `mevzuat.vuk_359`
      de süresiz kalmaktan çıkarıldı. 15.04.2022'den ÖNCE işlenen
      fiillerde lehe olan eski süre geçerlidir (TCK 7) — çok yıllı
      dosyalarda taslak üzerinde denetlenmeli. **Birincil kaynaktan
      doğrulanmadı**, bkz. "İbraz etmemede bekleyen".
- [x] **Vergi ziyaı cezası, tarh edilecek tutarın TAMAMI üzerinden.** Ceza
      tablosundan matrah sütunları ("Bilerek / Bilmeden Kullanılan Belgeler")
      kaldırıldı (müfettişin kararı, 2026-10-15). Tablo artık:
      Dönemi | Re'sen Tarh Edilecek KDV | VZC (3 kat) | VZC (1 kat) | Toplam.
      Tek kat varsa "Toplamı" sütunu yazılmıyor — aynısını tekrarlardı.

      Önceki davranış: ceza yalnızca sahte belgeye atfedilebilen kısım
      (`min(tarh, reddedilen KDV)`) üzerinden hesaplanıyordu; tarhiyatın
      matrah ilavesi gibi başka bir tespitten gelen kısmı **cezasız**
      kalıyordu. Artık o kısım da ceza taşıyor.

      **Devirden doğan fark da aynı katı taşıyor.** Sahte belgenin KDV'si
      indirimlerden çıkarılınca sonraki döneme devreden KDV de azalıyor;
      devir zinciri reddi bir ay soğurup vergiyi sonraki aya taşıdığında o
      ayda reddedilen belge bulunmasa bile fark aynı fiilden doğuyor. İlk
      sürümde o tutar "dayanaksız" sayılıp bir kat yazılıyordu ve devir
      devreye girdiği anda üç kat kayboluyordu (müfettişin düzeltmesi,
      2026-10-15).

      Tutar kaynağına göre üçe ayrılıyor; ceza katı kaynağa bağlı:
      1. Dönemin **kendi** sahte belgesi → o dönemin kategori karması
      2. **Devir** zincirinden gelen kısım (`fark_devir["odenecek"]`, hesap
         motorunun kendi ayrıştırması) → dosya genelindeki kategori karması
      3. Kalan (beyan hatası, matrah ilavesi) → 359 fiili değil, bir kat

      3. kalem `pay_dayanaksiz` / `ceza_dayanaksiz` diye **ayrı bir kalemde**
      tutuluyor, `pay_belirsiz`e karıştırılmıyor — "belirsiz" kullanma durumu
      SEÇİLMEMİŞ satıcıları işaret eder ve rapor bunun için kullanıcıya uyarı
      yazar; karıştırılsa bütün satıcılar sınıflandırılmış olsa bile uyarı
      yersiz çıkardı (ilk denemede tam bu oldu).

      Rapordaki açıklama paragrafı devir zincirini de gerekçelendiriyor;
      aksi hâlde raporu okuyan "o ayda fatura yok, neden üç kat?" diye
      sorardı.

      `pay_*` alanları veriden kaldırılmadı: uzlaşma kapsamı ayrımı (Ç
      bölümü) onlardan besleniyor. 359 dayanağı olmayan tutar uzlaşma
      kapsamı İÇİNDE sayılıyor, çünkü matrah ilavesi 359 fiili değil.

      Sonuç bölümündeki tablonun ceza sütunu aynı dağılımdan beslendiği için
      kendiliğinden yeni tutarı yazıyor.

      Gerileme denetimi: `testler/ceza_testi.py`. İki ayırt edici fikstür:
      - Ocak'ta sahte belge (6.000 × 3), Şubat'ta faturası olmayan bir tespit
        (4.000 × 1) → 22.000; cezanın tarhın tamamını kapsadığını gösterir
        (eski kodda 18.000'di).
      - Red bir ayı soğurup vergiyi sonraki aylara taşıyan devir zinciri:
        Ocak'ta red var ama tarhiyat yok, Şubat ve Mart'ta fatura yok ama
        tarhiyat var → her biri 5.000 × 3 = 15.000, toplam 30.000 = tarh × 3
        (devir düzeltmesinden önce 10.000'di).
- [x] **Devir düzeltme raporu eklendi.** (`app/devir_duzeltme_raporu.py`)
      Sahte belge raporu bir yılın indirimlerini reddettiğinde o yılın Aralık
      devri küçülür. Devir ileriye aktığı için **incelenmeyen sonraki
      yılların** beyanları da gerçek durumu yansıtmaz hâle gelir; küçük
      devirle yeniden kurulan zincirde bir dönemde ödenecek vergi doğarsa o
      yıl için ayrı bir rapor düzenlenir. Müfettişin örnek raporundan
      çıkarılan yapı: I-GİRİŞ, II-USUL (tenkitler asıl rapordadır),
      III-HESAP (III.1 beyan tablosu), IV-TESPİT VE TENKİT (IV.A re'sen
      takdir nedeni, IV.B verileri, IV.C düzeltme + tarhiyat), V-SONUÇ.

      **Rapor tarhiyat önerir:** kendi yılında doğan fark vergiyi ve VUK 341
      ile 344 gereği **1 (bir) kat** vergi ziyaı cezasını ister. Dayanak VUK
      30'un 4 ve 6 numaralı bentleri (beyanın gerçek durumu yansıtmaması).

      Raporun en işlevsel maddesi V. bölümün 3. maddesi: bu yılın Aralık
      devri de değiştiğinden **sonraki yılın Ocak devrinin vergi dairesince
      düzeltilmesi** istenir. Zincir böylece elle devam ettirilir.

      **Yıl seçimi üç koşul arıyor** (`rapor_yillari`), üçü de gerekli:
      1. O yılda sahte belge YOK — belgesi olan yıl incelenen yıldır.
      2. Önünden gelen devir GERÇEKTEN değişmiş (önceki yılın Aralık ayında
         beyan edilen ≠ olması gereken). Bu olmadan fark, müfettişin o yıla
         girdiği bir matrah ilavesinden de gelebilir ve yazılacak belge bu
         rapor değildir. Önceki yıl çalışmada yoksa yıl seçilmez.
      3. O yılda re'sen tarhı gereken bir fark VAR — devir küçülmesi her
         zaman vergi doğurmaz, zincir farkı soğurabilir.

      Bu yıllar `sahte_belge_raporu.rapor_yillari`'ndan **çıkarılıyor**;
      aksi hâlde aynı yıl için iki belge üretiliyordu. `_rapor_hazirla`
      artık `(yıl, belge, dosya adı)` üçlüsü döndürüyor — iki rapor türü
      üretildiği için adı üreten yerin belirlemesi gerekiyor.

      Gerileme denetimi: `testler/devir_duzeltme_testi.py`. Fikstür devir
      zincirini elle kuruyor (beyan bloğu gerçekte beyannameden gelir ve
      devir sütunlarını kendisi taşır).

      **Fikstür yazarken üç tuzak:** (a) beyana `onceki_donem_devreden` /
      `sonraki_donem_devreden` yazılmazsa beyan devri sıfır kalır ve rapor
      tersine okunur; (b) `odenmesi_gereken_kdv` yazılmazsa yıl, devirle
      ilgisi olmayan bir fark üretir; (c) "devir değişmediyse rapor yazılmaz"
      denetimi ilk yazıldığında farkı da sıfır olan bir fikstüre dayanıyordu,
      yanlış sebepten geçiyordu ve koşul kaldırıldığında hiç kızarmadı —
      fikstür farkın gerçekten doğduğu bir hâle çevrildi.
- [x] **Elle eklenen satıcı artık yalnızca kendi yılının raporunda.** Sahada
      böyle çıktı (2026-10-14): fatura listesi bulunmayan, elle eklenmiş bir
      satıcı (örn. yalnızca 2021 için sahteci, iş emri yok) HER yılın
      raporunda görünüyordu. Sebep: rapor yıl yıl yazılırken fatura listesi
      daraltılıyor, ama elle eklenen satıcının fatura satırı YOK — daraltma
      onu elemiyordu. `satici_ozeti` artık bir `yil` alıyor ve elle eklenen
      satıcıyı kendi `elle_yil`ine göre süzüyor.

      Yılı **girilmemişse** satıcı yine her yılda görünüyor: sessizce
      düşürmek, müfettişin hiç farketmeyeceği bir veri kaybı olurdu. Alanın
      ipucu metni bu etkiyi artık söylüyor.

      Aynı kusur `bilerek_yillari`nda da vardı — elle eklenen satıcıların
      yılı hiç görülmüyordu, dolayısıyla yalnızca elle eklenmiş bir bilerek
      satıcı bulunan yıl VSR'de atlanırdı. O da düzeltildi.

      Tuzak: ünvanlar belgede Türkçe küçültmeden geçiyor. Denetim yazarken
      Türkçe'ye özgü harf taşımayan bir ünvan seçin — "YILSIZ" → "yılsız"
      olur ve düz arama tutmaz (bu tuzağa bir kez düşüldü).
- [x] **Vergi Suçları Raporu (VSR) eklendi.** (`app/vergi_sucu_raporu.py`)
      Örnek rapordan çıkarılan yapı: I-GİRİŞ, II-YAPILAN TESPİTLER,
      III-SUÇUN UNSURLARI (3.1 kanuni / 3.2 maddi / 3.3 manevi), IV-SUÇUN
      FAİLİ (kimlik tablosu), V-SONUÇ (üç numaralı madde + tarhiyat önerisi
      tablosu). Rapor **kendisi tarhiyat önermez**; tarhiyatı öneren raporu
      V. bölümdeki tabloda anar, etkin pişmanlık (VUK geçici 34) için gereken
      bilgiler de o tabloyla verilir.

      **Elle istenmesi gerekmiyor:** sahte belge raporu ya da düzeltme kabul
      raporu indirilirken, "Bilerek kullanma" işaretliyse VSR de üretilip
      pakete konuyor (paket adı "..._ve_VSR_..." olur). Bilmeden kullanmada
      üretilmiyor — 306 Sıra No'lu Tebliğ gereği suç yok.

      **VSR bütün inceleme dönemi için TEK düzenlenir** — tarhiyat raporu gibi
      yıl yıl değil (müfettişin kararı, 2026-10-09; ilk sürüm yanlış olarak
      yıl yıl ayrı rapor üretiyordu). Yıllar raporun içinde: giriş ve sonuç
      bölümleri yılları birlikte anıyor, atıflar çoğullaşıyor ("...sayılı,
      ...sayılı Vergi İnceleme Raporlarında"), V. bölümdeki tablo her yıl
      için bir satır açıp sonuna TOPLAM satırı koyuyor. Her satırın vergi ve
      ceza tutarı o yılın verisinden hesaplanıyor; dosya toplamını her satıra
      yazmak cezayı yıl sayısı kadar büyük gösterirdi.

      Künyedeki "Tarhiyat öneren rapor(lar)" alanı bu yüzden satır tablosu:
      her yılın raporunun tarih ve sayısı ayrı satıra girilir (2020 ·
      20.10.2025 · 2025-[2013]/72). Tek yıl inceleniyorsa yıl hücresi boş
      bırakılabilir. İlk sürümdeki tek alanlı biçim (`vir_tarihi`,
      `vir_sayisi`) `normalize` içinde göç ettiriliyor — göç ORADA olmak
      zorunda, çünkü normalize tanımsız anahtarları atıyor ve eski değerler
      aksi hâlde okuyucuya hiç ulaşmıyor.

      Fail ayrımı: kurumlarda kanuni temsilci, gerçek kişide mükellefin
      kendisi; hapis cezası tüzel kişiye uygulanamadığı için IV. bölümdeki
      kimlik tablosu ve ceza cümlesi buna göre kuruluyor.

      Düzeltme kabul raporuna eklenen VSR'de tutarlar farklı: tarh edilecek
      vergi 0,00 (tutar beyandan çıkarılmıştır), ceza ise düzeltme üzerine
      kesilen yarım katın **üç kata tamamlanmış** hâli. Oran da ebeveyn
      raporla aynı ölçütten (`duzeltme_kabul_orani`) alınıyor; sahte belge
      ölçütü o dosyada sıfır döner.

      Künyeye "Vergi Suçları Raporu" bölümü eklendi: tarhiyat öneren raporun
      tarih/sayısı, yetkili Cumhuriyet Başsavcılığı (yalnızca yer adı yeter),
      failin baba-anne adı / doğum yeri / doğum tarihi / adresi ve ibraz
      etmeme raporu için defter tasdik makamı. Hiçbiri zorunlu alan değil;
      boş kalanlar belgede kırmızı yer tutucu olur.

      **VSR yalnızca bilerek kullanma olan yıllara ilişkindir.** Dört yıllık
      bir incelemede üç yıl bilerek, bir yıl bilmeyerek ise o dördüncü yıl
      raporda hiç anılmıyor — ne giriş/sonuç cümlelerinde ne V. bölümdeki
      tabloda. Bilmeyerek kullanmada 306 Sıra No'lu Tebliğ gereği kasıt,
      dolayısıyla suç yok. (Sahada böyle çıktı, 2026-10-14; önce dört yıl
      birlikte anılıyordu.) Ölçüt `faturalar.bilerek_yillari`; `sayilir`
      kullanılmıyor, çünkü tutar düzeltmeyle çıkarılmış olsa da fiil
      işlenmiştir.

      **3.2'deki oran YIL YIL yazılıyor** (müfettişin kararı, 2026-10-14):
      "…payının 2020 hesap döneminde %5,00, 2021 hesap döneminde %30,00 ve
      2022 hesap döneminde %10,00 olarak hesaplandığı görülmektedir." Tek bir
      birleşik yüzde, bir yılın ağır diğerinin hafif olduğu dosyalarda ikisini
      de yanlış temsil ediyordu. Her yılın payı o yılın faturalarından, böleni
      o yılın beyan edilen indiriminden kuruluyor
      (`sahte_belge_orani_yillara`), böylece yıllar birbirinden bağımsız
      okunabiliyor. Tek yıl kalırsa yıl adı tekrarlanmıyor, sade yüzde
      yazılıyor. "Gibi yüksek oranlara tekabül ettiği" nitelemesi yalnızca
      BÜTÜN yıllar eşiğin üstündeyse yazılıyor.

      **3.2'deki oran da yalnızca bilerek kullanılan belgelerden kuruluyor.**
      Oran orada KASTIN delili olarak sunulduğundan, bilmeyerek kullanılan
      tutarı paya katmak kasıt kurulmayan bir rakamla kasıt kanıtlamak olur.
      `sahte_belge_orani` / `duzeltme_kabul_orani` artık bir `vkn_suzgeci`
      alıyor; VSR bunu `bilerek_vknler` ile veriyor, böylece bölen de
      yalnızca bilerek olan yılların indirimine iniyor.

      Giriş cümlesi sadeleştirildi: "kasıtlı olarak, yani bilerek ve
      isteyerek" üç kez aynı şeyi söylüyordu; artık "bilerek kullandığı
      tespit edilmiştir" (müfettişin kararı, 2026-10-14).

      Gerileme denetimi: `testler/vsr_testi.py`. Üretilip üretilmediğini, KAÇ
      belge üretildiğini (tek rapor), çoğul ek uyumunu, yıl yıl tablo
      satırlarını, **bilmeyerek olan yılın rapora hiç girmediğini**, **oranın
      süzgeçten geçtiğini** ve metindeki ek hatalarını kolluyor;
      mutasyonlarla gerçekten tuttuğu doğrulandı.

- [x] **Belge alma özel usulsüzlüğü (VUK 353/1) eklendi.** Mükellef, gerçekten
      aldığı mal ve hizmeti sahte faturayla belgelendirdiğinde "alınması icap
      eden fatura"yı almamış olur. Fiil mükerrer 355'teki tevsik etmemeden
      **ayrıdır** ve aynı raporda yan yana durabilir:
      - muk. 355 → ödeme banka/PTT belgesiyle tevsik edilmemiş → %5
      - 353/1 → gerçek fatura hiç alınmamış → %10

      Rapordaki yeri: II/A altında ikinci alt başlık ("2- ... 353/1. Maddesine
      Göre Gerçek Fatura Almama Fiili"). Tevsik bölümü kapalıysa "1-" olur;
      numara sabit yazılmıyor, sonuç bölümündeki atıf da buna göre kayıyor.

      **Ceza oranı kanunda yazılı olduğu için sabit (%10); alt ve üst sınırlar
      künyeden TARİH ARALIKLI alınıyor.** Yıl bazlı tek bir alan yetmiyor:
      2022'de 7417 sayılı Kanunla sınırlar yıl İÇİNDE değişti (01.08.2022'den
      itibaren 500 → 1.000 ve 190.000 → 500.000). Künyedeki "Belge alma cezası
      hadleri" tablosu başlangıç | bitiş | alt sınır | yıllık üst sınır
      alıyor; bitiş boş bırakılırsa "o tarihten sonrası" demek. Bir faturanın
      tarihi hiçbir satıra denk gelmezse **cezası uydurulmuyor**, satır
      işaretleniyor ve belgede kırmızı yer tutucu kalıyor.

      Hesaba giren faturalar: "dahil" bırakılan ve hakkında VTR bulunan
      satıcılardan alınanlar. Ölçüt **tarhiyata bakmıyor**: tutar düzeltme
      beyannamesiyle indirimlerden çıkarılmış olsa bile gerçek fatura
      alınmamış olması değişmez. Bu yüzden `sayilir` KULLANILMIYOR —
      kullanılsaydı düzeltmeli dosyalarda küme boşalırdı.

      **Kapsamı künyeden iki süzgeç daraltıyor** (müfettişin kararı,
      2026-10-14). 353/1 kasıt aramayan nesnel bir fiil olduğu ve kanun
      bilerek/bilmeden ayrımı yapmadığı için bu ayrım uygulamaya değil
      müfettişe bırakıldı:
      - **Kapsam** (`ouc353_kapsam`): "Yalnızca bilerek kullanma olan
        belgeler" (varsayılan) / "Bütün sahte belgeler". Ayrım satıcı satıcı
        yapılıyor, yıl bütünüyle elenmiyor — karma bir yılda yalnızca bilerek
        satıcının belgeleri sayılır. O satıcılardan belgesi olmayan yılda
        bölüm hiç açılmaz.
      - **Hariç yıllar** (`ouc353_haric_yillar`): "2019, 2023" gibi. Kapsam
        seçiminden bağımsız; zamanaşımı gibi başka gerekçeler için. Yıl
        sonunu aşan belgelerde hem fatura hem kayıt yılına bakılıyor, böylece
        müfettiş hangisini yazarsa o tutuyor.

      Yıllık üst sınır yıl yıl uygulanıyor; yıl içinde sınır değiştiyse yılın
      SON geçerli sınırı esas alınıyor (ceza yıl kapandıktan sonra kesilir).
      Tartışmalı bir hâl çıkarsa raporu elle düzeltin.

      Hadleri okuyan `_had_tutari` ayrı yazıldı: `paste_parser.tutar_coz`
      "1.000" ve "190.000"ı 1,0 ve 190,0 diye okuyor. Beyan dökümlerinde bu
      doğru bir varsayım ama bu alana yazılanlar kanundaki yuvarlak
      sınırlardır, müfettiş binlik ayraçla yazar — tek noktadan sonra tam üç
      hane varsa nokta binlik ayracı sayılıyor.

      Belgedeki had tablosu **raporun kendi yıllarına daraltılıyor.** Künyeye
      bütün inceleme dönemine ait sınırlar bir arada girildiğinden, daraltma
      olmadan 2022 raporu 2023'ün sınırlarını da yazıyordu (sahada böyle
      çıktı, 2026-10-09). Bir yılı kısmen kapsayan sınır dönemi o yıla girer.

      Gerileme denetimi: `testler/belge_alma_testi.py`. Çapası müfettişin
      örnek raporunun **131 satırının tamamı**: her satırın cezası ve iki
      TOPLAM rakamı (2.352.614,70 ve 236.943,99) birebir tutuyor. 01.08.2022
      geçişi gerçek tarihler üzerinde 77./78. satırlarda doğrulanıyor. Had
      tablosunun yıla daralması ayrıca kolluyor.

---

## Özel usulsüzlükte bekleyen

- [ ] **Düzeltme kabul raporunda 353/1 bölümü yok.** Hesap düzeltmeli
      satıcıları bilerek kapsıyor (fatura alınmamış olması düzeltmeyle
      değişmez), ama o raporda yazdıracak bir bölüm henüz yok. Faturaların
      TAMAMI düzeltmeyle çıkarılmış bir dosyada 353/1 cezası hesaplanıyor
      fakat belgeye girmiyor. Müfettiş isterse eklenecek.
- [ ] **TOPLAM satırındaki "Ceza Alt Sınırı" hücresi boş.** Örnek raporda bu
      hücrede alt sınırların toplamı (92.500,00) yazıyor; anlamlı bir toplam
      olmadığı için boş bırakıldı. Dairenin formatına birebir uyulması
      isteniyorsa doldurulur.

---

## İbraz etmemede bekleyen

- [ ] **359 hapis süreleri: ikincil kaynaklardan doğrulandı, birincil
      kaynaktan doğrulanamadı.** Müfettişin isteği üzerine araştırıldı
      (2026-10-20). Birbirinden bağımsız birkaç hukuk yayını, 7394 sayılı
      Kanunla (15.04.2022) **359/a için on sekiz aydan beş yıla** ve
      **359/b için üç yıldan sekiz yıla** sürelerini tutarlı biçimde
      veriyor; uygulamadaki metin bunlarla uyuşuyor ve 7394'ten sonra
      değiştiklerine dair bir bulguya rastlanmadı.

      **mevzuat.gov.tr, gib.gov.tr ve resmigazete.gov.tr bu ağdan
      çözümlenemiyor** (DNS reddediliyor), bu yüzden resmî metinden
      doğrulama yapılamadı. Müfettiş taslak üzerinde bir kez denetlemeli.
      Kaynaklarda 359/c için verilen süreler birbirini tutmuyor; raporlar
      o bendi zaten alıntılamıyor.

      7394 ayrıca 359'a pişmanlık ve **etkin pişmanlık** fıkraları ekledi:
      vergi, gecikme faizi ve cezanın yarısı soruşturma evresinde
      ödenirse hapis cezası yarıya, kovuşturma evresinde ödenirse üçte
      bir oranında iniyor (dava açılmaması ya da feragat şartıyla).
      Raporlar bu fıkraları **alıntılamıyor**: resmî metni
      doğrulanamadığından, uydurulmuş bir hüküm yazmaktansa hiç
      yazmamak yeğlendi. İstenirse eklenir.

---

## Not düşerken

Şunlar yazılırsa iş kolaylaşır:

- **Nerede**: hangi sekme, hangi düğme, hangi belge bölümü
- **Ne oldu / ne olmalıydı**: beklenen ile görülen
- Ekran görüntüsü ya da çıktı dosyası varsa iyi olur

Biçim önemli değil; tek satır not da yeter, ayrıntı da.
