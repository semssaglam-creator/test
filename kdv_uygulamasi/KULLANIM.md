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

## Kayıt modeli — önce anlayın

Uygulama, üzerinde çalıştığınız veriyi **kendiliğinden saklamaz**. Yapıştırdığınız
sorgular, elle yaptığınız düzeltmeler ve tespitler yalnızca açık pencerede tutulur;
hesaplama da bunun üzerinden yapılır. Veritabanına yazma yalnızca üstteki
**Kaydet** düğmesine bastığınızda olur.

Üst çubuktaki rozet durumu gösterir:

| Rozet | Anlamı |
|---|---|
| `boş` | Henüz veri yok |
| `kaydedilmedi` | Veri var, hiç kaydedilmemiş |
| `kaydedilmemiş değişiklik` | Kayıtlı çalışma açık ama üzerinde değişiklik yapılmış |
| `kayıtlı` | Ekrandaki her şey kayıtlı |

- **Kaydet** — açık çalışmayı kaydeder (kayıtlıysa üzerine yazar)
- **Farklı Kaydet** — yeni bir kayıt oluşturur, öncekine dokunmaz
- **Yeni** — boş çalışmaya geçer (kaydedilmemiş veri varsa uyarır)

Kaydedilmiş çalışmalar **Kayıtlı Çalışmalar** sekmesinde listelenir; oradan
açabilir veya silebilirsiniz. Pencereyi kaydetmeden kapatmaya çalışırsanız
tarayıcı uyarır.

## Akış

Uygulama **Beyan Verisi** sekmesiyle boş olarak açılır ve doğrudan yapıştırmaya
hazırdır. Mükellef veya yıl tanımlamak zorunda değilsiniz.

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

Açık çalışmadaki mükellefin vergi numarası, yapıştırdığınız sorgudakinden
farklıysa mükellef bilgisi **değiştirilmez**; uyarı verilir ve veri açık
çalışmaya işlenir. Farklı mükellef için üstteki **Yeni** düğmesini kullanın.

**Yıl içinde vergi dairesi değişikliği:** Mükellef yılın farklı aylarında farklı
vergi dairelerinde mükellefse, her daireden aldığınız sorguyu ayrı ayrı
yapıştırın. Aynı yıla ait ikinci sorgu **tek yılda birleştirilir**: yeni sorgu
yalnızca kendi dolu aylarını günceller, diğer aylar korunur. Hangi ayın hangi
daireden geldiği ızgaranın üstünde etiketler hâlinde görünür. Aynı ay iki
sorguda da doluysa üzerine yazılır ve uyarı verilir.

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
terk ettiğinizde seri anında yeniden hesaplanır. Böylece mevcut veri üzerinde
çalışırsınız. (Değişiklik kalıcı olmaz — Kaydet demeniz gerekir.)

**Yıl kulakçıkları:** Yıllar arasında kulakçıklardan geçersiniz. Bir kulakçıktaki
**×** ile o yılı çalışmadan çıkarırsınız; yanlışlıkla oluşmuş boş yıllar böyle
kaldırılır. Boş yıllar kulakçıkta *(boş)* ibaresiyle işaretlenir.
Bir yılın numarasını düzeltmek için **Yılı değiştir** kutusunu kullanın; oranı
elle değiştirmediyseniz KDV oranları da yeni yıla göre tazelenir.

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

Yıllar silinmez; yalnızca içerik boşaltılır, yıllar boş olarak yerinde kalır.
Bir yılı tümüyle kaldırmak için kulakçıktaki **×** düğmesini kullanın.

### 2. İnceleme Tespitleri sekmesi

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

Her değişiklikte seri baştan sona yeniden hesaplanır.

**Başlangıç devri:** İnceleme döneminden önceki dönemden gelen düzeltilmiş devir
tutarı varsa bu sekmenin altındaki kutuya yazın; seri bu tutarla başlar. Boş
bırakılırsa ilk dönemin beyanındaki devir esas alınır.

### 3. Sonuç ve Fark sekmesi

Yıl kulakçıklarından tek bir yılı seçebilir ya da **Tümü** kulakçığıyla bütün
yılları tek tabloda görebilirsiniz. Üç tablo yan yana gösterilir: **eleştirili**, **beyan edilen** ve **fark**.
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

- **Excel'e Aktar** — rapora yapıştırmak için. Üretilen dosya her yıl için ayrı
  bir sayfada eleştirili beyanı, tespit girişini, ham beyanı ve üç sonuç/fark
  tablosunu; ayrıca *Tarhiyat Özeti*, *Yıl Uyumu*, *Tespit Etkisi* ve tüm
  dönemleri birleştiren *Özet* sayfalarını içerir. Aynı düğme Tarhiyat Özeti
  sekmesinde de vardır; ikisi de aynı dosyayı üretir.
- **Rapor Metnini Üret** — dönem dönem matrah farkı, tarhiyat özeti,
  tespitlerin ayrı ayrı etkisi ve tutarsızlık bulguları.
  Taslaktır; hukuki nitelendirme ve gerekçe rapora sizin tarafınızdan eklenir.

### 4. Tarhiyat Özeti sekmesi

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

Bu sekmede de yıl kulakçıkları vardır; **Tümü** ile bütün yılları tek tabloda
görürsünüz. Toplam satırı seçili kapsama göre hesaplanır.

Aynı sekmedeki **Yıllara Göre Beyan Uyumu** tablosu, çok yıllı incelemelerde
her yıl için matrah farkını, re'sen tarhı gereken tutarı ve farkın ne kadarının
o yılın tespitinden, ne kadarının önceki yıllardan devirle geldiğini gösterir.

### 5. Tespit Etkisi sekmesi

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

*Kayıtlı Çalışmalar* sekmesinden veritabanının kopyası alınır (`yedekler/`).
Yedek yalnızca **kaydedilmiş** çalışmaları içerir; ekranda duran kaydedilmemiş
veri yedeğe girmez. Geri yükleme, kayıtlı çalışmaların tamamının üzerine yazar.

## Veriler nerede

| Klasör | İçerik |
|---|---|
| `veritabani/kdv.db` | Yalnızca **kaydettiğiniz** çalışmalar |
| `yedekler/` | Veritabanı yedekleri |
| `ciktilar/` | Üretilen Excel çalışma dosyaları |
