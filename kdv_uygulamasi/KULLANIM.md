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

### 1. Dosyalar sekmesi
1. **Mükellef** ekleyin (ad/ünvan, VKN).
2. Mükellefi seçip bir **inceleme dosyası** oluşturun (örn. "2022-2023 KDV").
3. Dosyaya **inceleme yıllarını** ekleyin. Yıl içinde kısmi dönem inceleniyorsa
   *ay sayısını* düşürün.

**Başlangıç devreden KDV:** İnceleme döneminden önceki dönemden gelen ve
düzeltilmiş devir tutarı varsa buraya yazın; seri bu tutarla başlar. Boş
bırakılırsa ilk dönemin beyanındaki devir esas alınır.

### 2. Beyan Verisi sekmesi

**Blok yapıştırma:** Sistemden kopyaladığınız beyan bloğunu (etiket sütunu +
12 ay, Excel'deki 45–96 satırlarının karşılığı) kutuya yapıştırıp *Bloğu Aktar*
deyin. Satırlar etiketlerine göre sırayla eşleştirilir; arada eksik veya fazla
satır olsa da hizalama bozulmaz. Etiket sütunu olmayan yapıştırmalarda satırlar
sıraya göre atanır ve bu durum uyarı olarak bildirilir.

**Elle düzenleme:** Izgaradaki her hücreyi doğrudan değiştirebilirsiniz; alanı
terk ettiğinizde kaydedilir ve seri anında yeniden hesaplanır.

**Tek satır yapıştırma:** Satır başındaki **⇥** düğmesiyle yalnızca o satırın
12 aylık değerini tek seferde yapıştırabilirsiniz. Değerler sekmeyle, boşlukla
veya alt alta ayrılmış olabilir; başta etiket sütunu bulunması sorun değildir.

Ay sayısının dışında kalan sütunlar soluk gösterilir; veri girilebilir ancak
hesaba katılmaz.

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

- **Excel Çalışmasını İndir** — her yıl için ayrı sayfa (eleştirili beyan,
  tespit girişi, ham beyan, üç özet tablo) ve tüm dönemleri birleştiren bir
  *Özet* sayfası.
- **Rapor Metnini Üret** — dönem dönem matrah farkı ve toplam sonuç metni.
  Taslaktır; hukuki nitelendirme ve gerekçe rapora sizin tarafınızdan eklenir.

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
