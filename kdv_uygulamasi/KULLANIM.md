# KDV İnceleme Çalışması — Kullanım Kılavuzu

Beyan edilen KDV rakamlarını kontrol etmek, matrah / indirilecek KDV üzerinde
eleştiri uygulamak ve bunun sonraki dönemlere devir yoluyla yansımasını görmek
için kullanılan yerel uygulamadır. Elde kullanılan Excel çalışmasının yerini
alır; hesap mantığı birebir aynıdır.

## Çalıştırma

```
python3 main.py
```

veya `calistir.sh`. Tarayıcı `http://127.0.0.1:8766/` adresinde kendiliğinden
açılır. Kurulum gerekmez; Excel çıktısı için gereken `openpyxl` kütüphanesi
`lib/` klasöründe birlikte gelir. Sunucu yalnızca bu bilgisayardan erişilebilir.

## Akış

Uygulama **Beyan Verisi** sekmesiyle açılır ve doğrudan yapıştırmaya hazırdır.
Mükellef, dosya veya yıl tanımlamak zorunda değilsiniz — açılışta bir çalışma
kendiliğinden hazırlanır. Bu bilgileri sonradan doldurabilir veya
değiştirebilirsiniz.

### 1. Beyan Verisi sekmesi

**Sorgunun tamamını yapıştırın.** Sistem sorgusunun üst kısmındaki künye
satırları da tanınır:

```
VERGİ NO:        6660666666
T.C. KİMLİK NO:  -----
UNVAN:           ... ANONİM ŞİRKETİ
VERGİ DAİRESİ:   ... VERGİ DAİRESİ (MERKEZ, FAAL)
YIL:             2022
RAPOR TARİHİ:    30/07/2026
DÖNEMİ           OCAK  ŞUBAT  ...
```

Bu alanlar bulunursa **yılı elle seçmeniz gerekmez** — dönem yılı sorgudan
alınır, dosyada yoksa oluşturulur; mükellef ünvanı, vergi kimlik numarası ve
vergi dairesi kendiliğinden doldurulur; rapor tarihi o yılın kaydına yazılır.
Okunan bilgiler yapıştırma kutusunun altında yeşil bir kutuda özetlenir.

Künyede yıl yoksa, yapıştırma kutusunun üstündeki listeden seçtiğiniz yıl
kullanılır. Yıl önemlidir: **KDV oranı bu yıla göre belirlenir** (10.07.2023
öncesi %18, sonrası %20) ve devir zinciri buna göre kurulur.

Açık dosyadaki mükellefin vergi numarası, yapıştırdığınız sorgudakinden
farklıysa mükellef bilgisi **değiştirilmez**; uyarı verilir ve veri açık
dosyaya işlenir. Farklı mükellef için Dosyalar sekmesinden yeni dosya açın.

**Blok yapıştırma:** Beyan bloğunu (etiket sütunu + 12 ay, Excel'deki 45–96
satırlarının karşılığı) kutuya yapıştırıp *Bloğu Aktar* deyin. Satırlar etiketlerine göre sırayla eşleştirilir; arada eksik veya fazla
satır olsa da hizalama bozulmaz. Grup başlıkları (İNDİRİMLER, SONUÇ HESAPLARI
gibi değer taşımayan satırlar) tanınır ve atlanır. Etiket sütunu olmayan
yapıştırmalarda satırlar sıraya göre atanır ve bu durum uyarı olarak bildirilir.

**Birden çok yıl (örneğin 6 yıllık uyum incelemesi):** Her yıl için yılı
değiştirip o yılın bloğunu yapıştırın. Yıllar arasında yapıştırma kutusunun
altındaki sekmelerden geçersiniz. Devir zinciri yıl sınırında kesilmez —
bir yılın Aralık ayındaki devir, izleyen yılın Ocak ayına taşınır. Bu yüzden
hiç tespit girmediğiniz yıllarda bile, önceki yıllardan gelen farklar
kendiliğinden hesaplanır ve *Sonuç ve Fark* ile *Tarhiyat Özeti*
sekmelerinde görünür.

**Elle düzenleme:** Yapıştırdıktan sonra ızgarada **bütün değerler görünür**
(sıfırlar dahil, soluk renkte). Her hücreyi doğrudan değiştirebilirsiniz; alanı
terk ettiğinizde kaydedilir ve seri anında yeniden hesaplanır. Böylece mevcut
veri üzerinde çalışırsınız.

**Tek satır yapıştırma:** Satır başındaki **⇥** düğmesiyle yalnızca o satırın
12 aylık değerini tek seferde yapıştırabilirsiniz. Değerler sekmeyle, boşlukla
veya alt alta ayrılmış olabilir; başta etiket sütunu bulunması sorun değildir.

Ay sayısının dışında kalan sütunlar soluk gösterilir; veri girilebilir ancak
hesaba katılmaz.

**Verileri Temizle:** Izgaranın üstündeki düğme üç kapsam sunar:

| Kapsam | Ne silinir |
|---|---|
| Bu yılın beyan verisi | Yalnızca o yılın 52 beyan satırı; tespitleriniz korunur |
| Bu yılın beyan verisi + tespitleri | İkisi birlikte; KDV oranları yılın varsayılanına döner |
| Tüm yıllar | Dosyadaki bütün yılların beyan verisi ve tespitleri |

Hiçbir durumda yıl kayıtları veya inceleme dosyası silinmez; yalnızca içerik
boşaltılır, yıllar boş olarak yerinde kalır. İşlem geri alınamaz — öncesinde
Yedekleme sekmesinden yedek almanız önerilir. Bir yılı tümüyle kaldırmak
isterseniz Dosyalar sekmesindeki *Sil* düğmesini kullanın.

### 2. Dosyalar sekmesi (isteğe bağlı)

Burası yalnızca gerektiğinde kullanılır:

- **Mükellef adı / VKN** — rapor metninin başlığında kullanılır. Boş bırakırsanız
  "(Adsız Mükellef)" olarak kalır, hesaplamayı etkilemez.
- **Yıl düzeltme** — otomatik oluşan yıl yanlışsa buradan değiştirin. KDV oranı
  varsayılanları da yeni yıla göre tazelenir (oranı elle değiştirmediyseniz).
- **Ay sayısı** — yıl içinde kısmi dönem inceleniyorsa düşürün.
- **Başlangıç devreden KDV** — inceleme döneminden önceki dönemden gelen ve
  düzeltilmiş devir tutarı varsa buraya yazın; seri bu tutarla başlar. Boş
  bırakılırsa ilk dönemin beyanındaki devir esas alınır.
- Birden çok mükellefle çalışıyorsanız ayrı dosyalar oluşturup aralarında
  buradan geçiş yaparsınız.

### 3. İnceleme Tespitleri sekmesi

Dönem dönem beş kalem girilir:

| Alan | Etkisi |
|---|---|
| KDV matrahına ilave | Matrahı ve (orana göre) hesaplanan KDV'yi artırır |
| Hesaplanan KDV ilave | Matrah ilavesinin vergisi |
| Önceki dönem devreden KDV'den çıkarılacak | O dönemin devir girdisini azaltır |
| İndirilecek KDV'den çıkarılacak | Reddedilen indirim (sahte belge vb.) |
| Yüklenilen KDV'den çıkarılacak | İade hakkı doğuran işlemlerde yüklenim reddi |

**KDV oranı:** Dönemine göre otomatik gelir (10.07.2023 öncesi %18, sonrası
%20). Farklı oranlı teslimlerde (%1, %10) oranı değiştirin. Hesaplanan KDV
ilavesini tamamen elle girmek isterseniz o dönemin **Oto** kutusunu kaldırın.

*Kaydet ve Hesapla* dediğinizde seri baştan sona yeniden hesaplanır.

### 4. Sonuç ve Fark sekmesi

Üç tablo yan yana gösterilir: **eleştirili**, **beyan edilen** ve **fark**.
Fark tablosunda sıfırdan farklı hücreler kırmızı vurgulanır. Tespit girilen
dönemler *tespit* rozetiyle işaretlenir.

**Bir tutarın nasıl çıktığını görmek için hücreye tıklayın.** Açılan balonda
hesabın formülü, kullanılan kalemler ve sonuç satır satır gösterilir. Örneğin
ödenecek KDV hücresine tıkladığınızda:

```
Ödenecek = (Toplam KDV − İndirimler) − Tecil edilecek KDV
  Toplam KDV                 2.281.743,46
  İndirimler toplamı        −2.254.565,06
  Tecil edilecek KDV                 0,00
  Sonuç                         27.178,40
```

Beyan tablosunda balon, tutarın beyannamenin hangi satırından geldiğini söyler.
Fark tablosunda ise farkın ne kadarının o dönemin tespitinden, ne kadarının
devirden geldiğini belirtir. Aynı balon Tarhiyat Özeti tablosunda da çalışır.
Kapatmak için balon dışına tıklayın veya Esc'e basın.

- **Excel Çalışmasını İndir** — her yıl için ayrı sayfa (eleştirili beyan,
  tespit girişi, ham beyan, üç özet tablo) ve ayrıca *Tarhiyat Özeti*,
  *Yıl Uyumu*, *Tespit Etkisi* ve *Özet* sayfaları.
- **Rapor Metnini Üret** — dönem dönem matrah farkı, tarhiyat özeti,
  tespitlerin ayrı ayrı etkisi ve tutarsızlık bulguları.
  Taslaktır; hukuki nitelendirme ve gerekçe rapora sizin tarafınızdan eklenir.

### 5. Tarhiyat Özeti sekmesi

Elde kullanılan tarhiyat tablosunun karşılığıdır. Her dönem için beyan edilen
ile olması gereken tutarlar yan yana konur ve üç tarhiyat kalemi hesaplanır:

| Sütun | İçerik |
|---|---|
| **1** | Re'sen tarhı gereken KDV = olması gereken ödenecek − beyan edilen |
| **2** | Aranması gereken KDV = beyan edilen iade − olması gereken iade |
| **1+2** | Re'sen tarhı gereken toplam |
| **3** | İade gerçekleşmişse haksız olarak iade edilen KDV |
| **1+2+3** | Toplam fark |

Üç sütun da yalnızca mükellef aleyhine olan yönü taşır. Ters yöndeki sapma
(mükellefin fazladan beyan ettiği vergi veya talep etmediği iade) tarhiyata
eklenmez, tablonun altında ayrıca bildirilir.

Aynı sekmedeki **Yıllara Göre Beyan Uyumu** tablosu, çok yıllı incelemelerde
her yıl için matrah farkını, re'sen tarhı gereken tutarı ve farkın ne kadarının
o yılın tespitinden, ne kadarının önceki yıllardan devirle geldiğini gösterir.

### 6. Tespit Etkisi sekmesi

Bir tespit yalnızca girildiği dönemi değil, devir zinciri yoluyla izleyen tüm
dönemleri etkiler. Bu sekme her tespitin katkısını **ayrı ayrı** gösterir.

Örnek: 2023/Ocak'ta matraha ilave, 2024/Şubat'ta indirim reddi yaptınız.
2026/Nisan'daki sonucun ne kadarının hangisinden geldiğini iki ayrı sütunda
görürsünüz.

- **Tespit kaynakları** tablosu: her tespitin ne olduğu, kaç dönemi etkilediği,
  hangi dönem aralığına yayıldığı ve seri genelindeki toplam etkisi.
- **Dönem × Kaynak dağılımı**: satırlarda dönemler, sütunlarda tespitler.
  Üstteki listeden ödenecek KDV, devreden KDV, iade, indirimler veya matrah
  büyüklüklerinden birini seçersiniz.

**Etkileşim sütunu:** KDV hesabı doğrusal değildir — ödenecek ile devreden
arasındaki eşikte alt/üst sınır uygulanır. Bu yüzden tespitlerin tek tek
etkilerinin toplamı, hepsi birlikte uygulandığındaki farkı her zaman tam
vermez. Aradaki bakiye kaynaklara dağıtılmaz; "Etkileşim" sütununda ayrıca
gösterilir. Bu sütun yalnızca gerçekten bakiye oluştuğunda görünür.

## Devir zinciri

Bir dönemde yapılan eleştiri, o dönemin *sonraki döneme devreden KDV*
tutarını değiştirir; bu tutar izleyen dönemin *önceki dönemden devreden KDV*
girdisi olur. Zincir **yıl sınırında kesilmez** — Aralık ayının düzeltilmiş
devri izleyen yılın Ocak ayına taşınır. Böylece tek bir dönemde yapılan tespit,
sonraki tüm dönemlere kendiliğinden yansır.

Toplam satırında devir sütunları toplanmaz (stok kalemidir); dönem sonu değeri
gösterilir.

## Beyan tutarlılık kontrolü

Excel çalışmasında bulunmayan bir denetimdir. Eleştiriden bağımsız olarak
beyannamelerin kendi içindeki tutarsızlıklarını bulur:

1. **Devir zinciri kopukluğu** — bir dönemin beyan edilen önceki devri, bir
   önceki dönemin beyan edilen sonraki devrine eşit değilse.
2. **İndirimler toplamı hatası** — toplam, alt kalemlerin toplamını tutmuyorsa.
3. **Sonuç hesabı hatası** — beyan edilen ödenecek / devreden tutarları,
   beyandaki rakamlarla hesaplanandan farklıysa.

Bulgular *Sonuç ve Fark* sekmesinde ve Excel'in *Özet* sayfasında listelenir.

## Yedekleme

*Yedekleme* sekmesinden veritabanının kopyası alınır (`yedekler/`). Geri yükleme
mevcut verilerin üzerine yazar.

## Veriler nerede

| Klasör | İçerik |
|---|---|
| `veritabani/kdv.db` | Tüm mükellef, dosya, beyan ve tespit kayıtları |
| `yedekler/` | Veritabanı yedekleri |
| `ciktilar/` | Üretilen Excel çalışma dosyaları |
