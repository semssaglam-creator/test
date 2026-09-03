# Uzlaşma Takip Uygulaması — Kullanım Kılavuzu

Bu kılavuz, Vergi Usul Kanunu (VUK) kapsamındaki **uzlaşma sürecini**
(dilekçe kaydı → uzlaşma toplantısı → tutanak → istatistik) baştan sona
yönetmenizi sağlayan masaüstü uygulamasının kullanımını anlatır.

---

## 1. Genel Bilgiler

- Uygulama **tamamen offline** çalışır, internet bağlantısı gerekmez.
- **Kurulum gerektirmez**: klasörü kopyalayıp doğrudan çalıştırabilirsiniz.
- Tüm veriler bilgisayarınızdaki `veritabani/uzlasma.db` dosyasında saklanır.
- Arayüz tarayıcınızda açılır ama veriler **internete gönderilmez**;
  sunucu yalnızca kendi bilgisayarınızda (127.0.0.1) çalışır.

### Nasıl Çalıştırılır?

- **Masaüstü kısayolu ile**: Kurulumda oluşturulan "Uzlaşma Takip" simgesine
  çift tıklayın.
- **Elle**: Uygulama klasöründe `./calistir.sh` dosyasını çalıştırın
  (veya `python3 main.py`).
- Açılan terminal penceresinde "Uzlasma Takip Uygulamasi calisiyor:
  http://127.0.0.1:8765/" yazısını gördükten kısa bir süre sonra
  tarayıcınızda uygulama otomatik olarak açılır.
- **Kapatmak için**: terminal penceresinde `Ctrl+C` tuşuna basın
  (tarayıcı sekmesini kapatmak yeterli değildir, sunucu arka planda
  çalışmaya devam eder).

> Not: 8765 portu doluysa (uygulama zaten açıksa) program otomatik olarak
> 8766, 8767... gibi bir sonraki boş portu kullanır.

### Üst Menü (Sekmeler)

Uygulamanın üst kısmında 6 sekme bulunur:

1. **Dilekçe Kaydı** — Mükellef ve ihbarname/ceza bilgilerini sisteme kaydetme
2. **Uzlaşma İşlemi** — Uzlaşma toplantısı yapıp tutanak üretme
3. **Tutanak Geçmişi** — Geçmiş tutanaklar, puantaj cetveli, komisyon imza geçmişi
4. **Vergi/Ceza Türleri** — Kod listelerini yönetme
5. **İstatistikler** — Dönemsel raporlar
6. **Ayarlar** — Kurum bilgileri, tutanak numarası, komisyon üyeleri, yedekleme

---

## 2. Dilekçe Kaydı

Mükelleflerin "Dijital Vergi Dairesi" üzerinden gönderdiği **uzlaşma talep
dilekçelerindeki** bilgileri sisteme kaydettiğiniz ekrandır.

### 2.1 Mükellef Bilgileri

- **Kayıtlı mükellef ara**: Daha önce kayıtlı bir mükellefe yeni ihbarname
  eklemek istiyorsanız, ad/ünvan, VKN/TCKN veya ihbarname fiş numarasıyla
  (en az 3 karakter) arama yapın ve listeden seçin — bilgiler otomatik
  doldurulur.
- Yeni bir mükellef için **Ad Soyad / Ünvan** (zorunlu), **VKN/TCKN**,
  **Telefon** ve **Adres** alanlarını elle doldurun.

> 💡 Mükellef aramasında büyük/küçük harf farkı gözetilmez; "özkan",
> "ÖZKAN" ve "Özkan" aynı sonucu verir. Türkçe'de karışan I/İ/ı/i
> harfleri de birbirinin yerine geçer ("istanbul" → "İSTANBUL" bulur).

### 2.2 Dilekçe Bilgilerini Aktarma — 3 Yöntem

Dilekçedeki ihbarname ve ceza satırlarını aşağıdaki tablo formuna **üç
farklı yolla** aktarabilirsiniz:

**a) PDF Yükleme (önerilen)**
- "Dilekçe PDF Yükle" alanına PDF dosyasını sürükleyip bırakın veya
  tıklayıp seçin.
- **Birden fazla dilekçeyi aynı anda** seçebilirsiniz (toplu yükleme).
  Tek dosya yüklerseniz bilgiler forma aktarılır, kontrol edip
  kaydedebilirsiniz. Birden fazla dosya yüklerseniz her dilekçe
  "İhbarname / Ceza Satırları" bölümünde **ayrı bir kulakçığa** yerleşir;
  kulakçıklar arasında gezip her dilekçeyi kontrol edebilir, gerekirse
  düzeltebilirsiniz. Tek **Kaydet** ile hepsi birden kaydedilir ve
  "*n* adet dilekçe ile *m* adet ihbarname kaydedildi" bildirimi çıkar.
- Okunamayan dosyalar kulakçıkta ⚠ ile işaretlenir ve kaydedilmez;
  diğer dilekçelerin kaydı bundan etkilenmez.

**b) Kopyala-Yapıştır**
- Dilekçe PDF'ini bir PDF görüntüleyicide açıp tüm metni kopyalayın
  (Ctrl+A, Ctrl+C).
- "Dilekçeden Kopyala-Yapıştır" kutusuna yapıştırın ve
  **"Metni Ayrıştır ve Forma Aktar"** butonuna basın.
- Mükellef bilgileri ve ihbarname/ceza satırları otomatik olarak alttaki
  tabloya doldurulur.

**c) Elle Giriş**
- "Satır Ekle" butonuyla tabloya yeni satır ekleyip, **İhbarname Fiş No**,
  **Vergi Türü**, **Ceza Kodu**, **Miktar (TL)**, **Düzenleme Tarihi** ve
  **Tebliğ Tarihi** bilgilerini elle yazın.

### 2.3 Tabloyu Kontrol Etme ve Kaydetme

- Otomatik aktarılan bilgileri kaydetmeden önce **kontrol edin**;
  hatalı/eksik alanları düzeltin.
- Bir ihbarnameye ait birden fazla ceza satırı varsa, her satırı ayrı bir
  tablo satırı olarak ekleyin (aynı **İhbarname Fiş No**'yu tekrar yazın).
- Satır silmek için satırın sonundaki **🗑** simgesine tıklayın.
- Her şey doğruysa **"Kaydet"** butonuna basın.

> ⚠️ **Mükerrer kayıt koruması**: Aynı ihbarname fiş numarası daha önce
> kaydedilmişse, sistem kaydı reddeder ve hangi fiş numaralarının zaten
> kayıtlı olduğunu belirtir. Bu, aynı dilekçenin yanlışlıkla iki kez
> kaydedilmesini önler.

> 💡 Vergi Türü veya Ceza Kodu listede yoksa, önce **"Vergi/Ceza Türleri"**
> sekmesinden ekleyin (bkz. Bölüm 5).

---

## 3. Uzlaşma İşlemi

Uzlaşma günü geldiğinde, mükellefi seçip o mükellefin **bekleyen tüm
ihbarnamelerini** listeleyip uzlaşma sonucuna göre tutanak üretirsiniz.

### 3.1 Mükellef Arama

- "Mükellef Ara" kutusuna ad/ünvan, VKN/TCKN veya ihbarname fiş numarasının
  bir kısmını (en az 3 karakter) yazın, çıkan öneri listesinden mükellefi
  seçin.
- Seçilen mükellef üstte "Seçili mükellef: ..." satırında görünür.

### 3.2 İhbarname Listesi

- Seçilen mükellefe ait **tüm** ihbarnameler ve ceza satırları tabloda
  görünür:
  - **BEKLEYEN** (yeşil rozet): Henüz uzlaşmaya konu olmamış, **bu
    tutanağa otomatik dahil edilecek** satırlar. Bu satırlarda Vergi
    Türü, Ceza Kodu, Miktar ve İndirim % alanları **düzenlenebilir** —
    değişiklik yaptığınızda otomatik kaydedilir.
  - **UZLAŞILDI** (mavi), **UZLAŞILAMADI** (turuncu), **GELMEDİ** (kırmızı):
    Geçmişte sonuçlanmış kayıtlar; sadece bilgi amaçlıdır, tutanağa dahil
    edilmez.
- **İndirim Oranı**: Her bekleyen satır için varsayılan %80 indirim
  uygulanır (yani tutarın %20'si "kalan tutar" olarak hesaplanır). Bu oranı:
  - Tek bir satır için, o satırın "İndirim %" kutusunu değiştirerek,
  - Tüm satırlar için aynı anda, üstteki **"Varsayılan İndirim Oranı %"**
    kutusuna değer yazıp **"Tümüne Uygula"** butonuna basarak
    değiştirebilirsiniz.
- "Kalan Tutar (TL)" sütunu, indirim sonrası uzlaşılacak/önerilecek tutarı
  otomatik gösterir. Bu tutar **10 TL'nin bir üst katına yuvarlanır** ve
  kuruş hanesi 00 olur (ör. 1.660,50 → 1.670,00; 1.230,00 olduğu gibi
  kalır). Tutanağa yazılan tutar ekranda görünenle aynıdır.
- **Bir ihbarnameyi silmek** (mükellefin uzlaşmadan tamamen vazgeçmesi gibi
  durumlarda): satırın sonundaki kırmızı **"Sil"** butonuna basın. Bu işlem
  ilgili ihbarnameyi ve tüm ceza satırlarını veritabanından tamamen siler —
  geri alınamaz, dikkatli kullanın.

### 3.3 Tutanak Bilgileri ve Oluşturma

1. **Sonuç** seçin:
   - **Uzlaşıldı**: Komisyon ile mükellef uzlaşmaya vardı → "Uzlaşma
     Tutanağı" üretilir, mükellef imza satırı içerir.
   - **Uzlaşılamadı**: Toplantı yapıldı ama anlaşma sağlanamadı → "Uzlaşma
     Tutanağı" üretilir (dava açma süresi notu eklenir).
   - **Gelmedi**: Mükellef toplantıya gelmedi → "Uzlaşma Komisyon Karar
     Tutanağı" üretilir (mükellef imzası yok, "Önerilen Tutar" sütunu yok).
2. **Toplantı Tarih/Saat**: Varsayılan olarak şu anki tarih/saat
   doldurulur, gerekirse düzenleyin (GG.AA.YYYY SS:DD formatında).
3. **Davetiye Tebliğ Tarih/Saat**: Mükellefe gönderilen davetiyenin tebliğ
   tarihi. **"Gelmedi"** seçildiğinde bu alan **zorunludur**; diğer
   sonuçlarda boş bırakılabilir ama tutanakta bilgi olarak yer alır.
4. **Başkan / Üye 1 / Üye 2**: Toplantıya katılan komisyon üyelerini
   açılır listelerden seçin (listeler "Ayarlar" sekmesinde tanımlanır).
5. **"Tutanak Oluştur"** butonuna basın.

Tutanak oluşturulduğunda:
- Otomatik bir **tutanak numarası** atanır (örn. `2026/30` — yıl bazlı
  artan sıra numarası, yıl değişince sıfırlanır).
- Seçilen sonuca uygun **Excel tutanağı** üretilir ve `tutanaklar/`
  klasörüne kaydedilir (dosya, "Tutanak Geçmişi" sekmesinden indirilebilir).
- Tutanağa dahil edilen ihbarnamelerin durumu (Uzlaşıldı/Uzlaşılamadı/
  Gelmedi) güncellenir; bu ihbarnameler artık "bekleyen" listesinden çıkar.

---

## 4. Tutanak Geçmişi

### 4.1 Tüm Tutanaklar

- Geçmişte oluşturulan tüm tutanakları (tarih, tutanak no, mükellef,
  VKN/TCKN, sonuç) listeler.
- **Dosya** sütunundaki bağlantıdan tutanağın Excel çıktısını
  indirebilirsiniz.
- **İşlem** sütunu:
  - **Sonucu Düzelt**: Yanlış girilen bir sonucu (örn. "Gelmedi" yerine
    "Uzlaşılamadı" olması gerekiyorsa) sonradan değiştirmenizi sağlar —
    Excel dosyası yeni sonuca göre yeniden üretilir.
  - **Sil** (kırmızı): Tutanağı tamamen siler. Tutanağa bağlı ihbarnameler
    otomatik olarak yeniden **"beklemede"** durumuna döner (yani "Uzlaşma
    İşlemi" ekranında tekrar listelenir) ve üretilmiş Excel dosyası da
    silinir. Hatalı oluşturulmuş bir tutanağı düzeltmek için kullanılır.

### 4.2 Aylık Huzur Hakkı Puantaj Cetveli

- Komisyon üyelerinin bir ay içinde katıldığı toplantı sayısına göre huzur
  hakkı puantaj cetveli üretir.
- **Ay** ve **Yıl** seçip **"Cetveli İndir (Excel)"** butonuna basın;
  Excel dosyası otomatik indirilir.

### 4.3 Komisyon Üyesi İmza Geçmişi

- Açılır listeden bir komisyon üyesi seçtiğinizde, o üyenin imzaladığı
  tüm tutanakların (tarih, tutanak no, mükellef, sonuç) listesi gösterilir.
- Üyenin geçmiş katılımlarını/imzalarını kontrol etmek için kullanılır.

---

## 5. Vergi/Ceza Türleri

- **Vergi Türleri**: Vergi türü kodları (örn. `0015`) ve açıklamalarını
  (örn. "Gelir Vergisi") buradan ekleyip yönetirsiniz.
- **Ceza Kodları**: Ceza kodları (örn. `3074`, `3080`) ve "Ceza Nedeni"
  açıklamalarını (tutanakta paragraf metninde kullanılır) buradan
  ekleyip yönetirsiniz.
- Her iki listede de:
  - **Kod** ve **Açıklama** alanlarını doldurup **"Ekle"** ile yeni kayıt
    ekleyebilirsiniz.
  - Satırların yanındaki butonla bir kodu **pasif** yapabilirsiniz (pasif
    kodlar yeni kayıtlarda seçilemez ama geçmiş kayıtlarda görünmeye
    devam eder).

> 💡 Dilekçe kaydı sırasında bir vergi türü/ceza kodu listede yoksa, önce
> buradan ekleyin, sonra Dilekçe Kaydı ekranına geri dönün.

---

## 6. İstatistikler

Belirli bir tarih aralığındaki uzlaşma faaliyetlerinin özetini ve
ceza/vergi türü bazında dağılımını gösterir.

### 6.1 Tarih Aralığı

- **Başlangıç** ve **Bitiş** tarihlerini GG.AA.YYYY formatında girip
  **"Hesapla"** butonuna basın. Boş bırakırsanız tüm kayıtlar dahil edilir.
- Hızlı seçim butonları: **Aylık**, **3 Aylık**, **6 Aylık**, **Yıllık**
  (bugünden geriye doğru ilgili dönemi otomatik doldurur).
- **"PDF Çıktısı Al (A4)"** butonu, ekrandaki istatistik tablolarını A4
  formatında yazdırma/PDF kaydetme önizlemesine açar.

### 6.2 Genel Özet

- **Başvuru (dilekçe) sayısı**: Seçilen tarih aralığında **kayıt edilen**
  (dilekçe onay zamanına göre) farklı dilekçe sayısı.
- **Başvuran mükellef sayısı**: Seçilen tarih aralığında **tutanak
  düzenlenen** farklı mükellef sayısı.
- **Uzlaşıldı / Uzlaşılamadı / Gelmedi** sayıları: Tutanak sonuçlarının
  toplantı tarihine göre dağılımı.

### 6.3 Ceza Türü ve Vergi Türü Bazında Tablolar

İki tablo da aynı sütun yapısına sahiptir, biri ceza kodu (3073, 3074 vb.)
bazında, diğeri vergi türü + vergi ziyaı cezası (3080) bazında
("0015/3080" gibi) gruplanır:

| Sütun | Açıklama |
|---|---|
| Vergi/Ceza Kodu, Açıklama | Grup kodu ve açıklaması |
| Başvuru Sayısı (dilekçe) | Bu kod için kayıtlı dilekçe sayısı |
| Toplam Başvuru Tutarı | Bu koda ait ceza satırlarının toplam (indirimsiz) tutarı |
| **Düzenlenen Tutanak Sayısı** → Uzlaşılan / Uzlaşılamayan / Gelmeyen | Bu kod için, seçilen tarih aralığında düzenlenen tutanakların sonuca göre sayıları |
| Toplam Uzlaşılan Tutar | "Uzlaşıldı" sonuçlu tutanaklarda, indirim uygulanmış (uzlaşılan) tutarların toplamı |
| Toplam Uzlaşılamayan Tutar | "Uzlaşılamadı" + "Gelmedi" sonuçlu tutanaklardaki ceza satırlarının **orijinal (indirimsiz) başvuru tutarlarının** toplamı — bu ihbarnamelerde tutar değişmediği için |

- Her tablonun altında **"GENEL TOPLAM"** satırı tüm sütunların toplamını
  gösterir.

---

## 7. Ayarlar

### 7.1 Kurum Bilgileri

- **Defterdarlık** ve **Vergi Dairesi Müdürlüğü** adlarını girin.
- Bu bilgiler, üretilen tüm tutanak Excel belgelerinin başlık bölümünde
  ve "Bağlı Bulunduğu Vergi Dairesi" alanında otomatik kullanılır.
- Değişiklik yaptıktan sonra **"Kaydet"** butonuna basın.

### 7.2 Tutanak Numarası

- O ana kadar verilmiş tutanak sayısı ve geçerli yıl bilgisini gösterir.
- **Sonraki tutanak sıra numarası**: Uygulamaya yıl ortasında geçiyorsanız
  (örn. elle takip ettiğiniz son tutanak "2026/45" ise), buraya `46`
  yazıp **"Kaydet"** ile devam numarasını ayarlayın.
- Tutanak numarası her yeni tutanakta otomatik bir artar; yıl değiştiğinde
  otomatik olarak 1'den başlar (örn. 2026/52 → 2027/1).

### 7.3 Komisyon Üyeleri

- **Ad Soyad**, **Ünvan** (örn. "Müdür Yardımcısı") ve **Görev**
  (Başkan/Üye) bilgileriyle komisyon üyesi ekleyin.
- Eklenen üyeler "Uzlaşma İşlemi" ekranındaki Başkan/Üye seçim
  listelerinde ve puantaj cetvelinde görünür.
- **Düzenle** ile üyenin ad/ünvan/görev bilgisini ve durumunu satır
  içinde değiştirebilirsiniz; pasif bir üyeyi buradan yeniden **Aktif**
  yapabilirsiniz.
- Bir üyeyi listeden kaldırmak için (geçmiş kayıtları silmeden) **Pasif
  Yap**'ı kullanın; pasif üyeler yeni tutanaklarda seçilemez ama geçmiş
  imza kayıtlarında görünmeye devam eder.
- **Sil**, üyeyi kayıttan tümüyle kaldırır ve geri alınamaz. Tutanak
  imzalamış bir üye silinemez (uygulama uyarır) — çünkü tutanak, o üyenin
  adıyla düzenlenmiş resmi bir belgedir; böyle bir üye için "Pasif Yap"
  kullanılır.

> 💡 Puantaj cetvelinde "Başkan" görevindeki üyenin ünvanı otomatik olarak
> "Müdür" olarak yazılır (resmi belge gerekliliği).

### 7.4 Veritabanı Yedekleme

- **"Yedek Al"** butonu, o anki veritabanının tarih damgalı bir kopyasını
  `yedekler/` klasörüne kaydeder. Tablo, alınmış yedeklerin listesini
  gösterir; buradan **geri yükleme** de yapılabilir (geri yüklemeden önce
  mevcut veritabanı otomatik olarak yedeklenir).
- **"Tüm Kayıtları İndir (ODS)"**: Tüm mükellef/ihbarname/ceza
  satırı/tutanak kayıtlarının düz bir dökümünü, LibreOffice/Excel ile
  açılabilen `.ods` formatında indirir — genel arşivleme/inceleme için
  kullanışlıdır.

> 💡 **Düzenli yedek almanız önerilir.** Yedekleri ayrıca harici bir
> diske/USB belleğe de kopyalamanız veri kaybına karşı ek güvence sağlar.

---

## 8. Uygulamayı Taşıma / Yedekleme

- Tüm veriler ve ayarlar uygulama klasörünün içindedir
  (`veritabani/uzlasma.db`, `tutanaklar/`, `puantajlar/`, `yedekler/`).
- Uygulamayı başka bir bilgisayara taşımak için **tüm klasörü** kopyalamanız
  yeterlidir — ek bir kurulum adımı gerekmez.
- Masaüstü kısayolunu yeni konumda yeniden oluşturmak için
  `kisayol_olustur.sh` betiğini çalıştırın.

---

## 9. Sık Sorulan Sorular

**S: Bir ihbarnameyi yanlışlıkla kaydettim, nasıl silerim?**
C: "Uzlaşma İşlemi" sekmesinde mükellefi arayıp seçin; ihbarname hâlâ
"BEKLEYEN" durumdaysa satırın sonundaki kırmızı **"Sil"** butonuyla
silebilirsiniz.

**S: Bir tutanağı yanlış sonuçla oluşturdum, ne yapmalıyım?**
C: "Tutanak Geçmişi" sekmesinde ilgili tutanağın **"Sonucu Düzelt"**
seçeneğiyle sonucu değiştirebilir, veya tamamen **"Sil"** ile silip
ihbarnameyi "Uzlaşma İşlemi" ekranından yeniden işleyebilirsiniz.

**S: Aynı mükellefin başka bir dilekçesini nasıl eklerim?**
C: "Dilekçe Kaydı" ekranında "Kayıtlı mükellef ara" kutusundan mükellefi
bulup seçin, ardından yeni dilekçenin ihbarname/ceza satırlarını
ekleyip kaydedin.

**S: Uygulama açılmıyor / tarayıcı açılmadı?**
C: Terminal penceresindeki `http://127.0.0.1:8765/` adresini elle
tarayıcınıza yapıştırarak açabilirsiniz. Port doluysa 8766, 8767 gibi
bir sonraki numarayı deneyin (terminaldeki yazıda hangi port
kullanıldığı belirtilir).

**S: Veriler güvende mi, internete gönderiliyor mu?**
C: Hayır. Sunucu yalnızca kendi bilgisayarınızda (127.0.0.1/localhost)
çalışır, dışarıdan erişilemez ve hiçbir veri internete gönderilmez.
