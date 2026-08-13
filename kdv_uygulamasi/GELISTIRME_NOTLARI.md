# Geliştirme Notları

Kullanımda karşılaşılan eksikler, düzeltme istekleri ve fikirler burada
biriktirilir. Tek tek uygulanmaz; birikince toplu olarak ele alınır.

Bu dosya bilerek depodadır: sohbet kapansa da notlar kaybolmaz, sonraki
oturumda buradan devam edilir.

**Durum işaretleri:** `[ ]` bekliyor · `[~]` üzerinde çalışılıyor ·
`[x]` bitti (Yapılanlar bölümüne taşınır)

---

## Bekleyenler

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

## Yapılanlar

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
      alınıyor; girilmemişse kırmızı yer tutucu tırnaksız kalıyor.
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

---

## Not düşerken

Şunlar yazılırsa iş kolaylaşır:

- **Nerede**: hangi sekme, hangi düğme, hangi belge bölümü
- **Ne oldu / ne olmalıydı**: beklenen ile görülen
- Ekran görüntüsü ya da çıktı dosyası varsa iyi olur

Biçim önemli değil; tek satır not da yeter, ayrıntı da.
