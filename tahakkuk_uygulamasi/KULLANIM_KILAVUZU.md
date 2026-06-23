# Toplu Tahakkuk Sorgulama Uygulaması

Toplu tahakkuk Excel dosyalarını bir veri tabanı gibi kullanıp; **vergi kimlik
numarası**, **vergi kodu** ve **ödenecek tutar** bazında sorgulama yapmanızı
sağlayan, internet gerektirmeyen masaüstü uygulamasıdır. Her gün yüklediğiniz
dosya tarihiyle birlikte saklanır; geçmiş yüklemeleri istediğiniz zaman tekrar
açıp sorgulayabilirsiniz.

## Çalıştırma (Linux — çift tıkla)

1. `tahakkuk_uygulamasi` klasörünü bilgisayarınıza kopyalayın.
2. Bir kez **`kisayol_olustur.sh`** dosyasını çalıştırın → masaüstüne ve uygulama
   menüsüne **"Toplu Tahakkuk Sorgulama"** kısayolu eklenir.
3. Artık kısayola çift tıklayın. Tarayıcıda arayüz açılır; tüm veriler kendi
   bilgisayarınızda kalır.

Kısayol kullanmadan da `calistir.sh` dosyasına çift tıklayarak (veya terminalde
`./calistir.sh`) başlatabilirsiniz.

> Kurulum gerekmez. Yalnızca **Python 3** gereklidir (Linux'ta genelde kuruludur).
> Excel okuma/yazma kütüphaneleri `lib/` klasöründe gömülü gelir.

## Kullanım

### 1. Dosya Yükle
Üstteki kutuya dosyayı sürükleyin ya da tıklayıp seçin. **`.xls`, `.xlsx` ve
`.pdf`** desteklenir. Her yükleme, **yükleme tarihi** ile saklanır. Satır
sayısında **sınır yoktur** (on binlerce satır sorunsuz çalışır).

> **PDF hakkında:** PDF ayrıştırıcı, Excel'deki sütun düzenine göre ayarlıdır
> (vergi kimlik no, tahakkuk fiş no, dönem, vergi kodu, tutar). PDF'iniz çok
> farklı bir düzendeyse Excel yüklemeniz daha güvenlidir; örnek bir tahakkuk
> PDF'i paylaşırsanız ayrıştırıcı ona göre ince ayarlanabilir.

- **Boş satırlar** otomatik olarak bir üstteki mükellefin/fişin devamı kabul
  edilir; ilgili bilgiler (vergi kimlik no, fiş no, dönem...) aşağı taşınır.
- **Vergi Dönemi** `052026052026` → *Mayıs 2026*, `012026122026` → *2026
  (Yıllık)* şeklinde okunabilir gösterilir.

### 2. Sorgu
- **Yükleme (geçmiş):** Hangi günün listesi üzerinde çalışacağınızı seçin.
- **Vergi Kimlik No** / **Vergi Kodu:** Yazdığınız değeri içeren satırlar gelir.
- **Tutar (min/max):** Ödenecek tutar aralığı.
- **Sıralama:**
  - **Fiş bazında — en yüksek tutar üstte:** En yüksek tutarı içeren tahakkuk
    fişi en üstte gelir ve o fişin **bütün** satırları birlikte listelenir
    (fiş bütünlüğü korunur).
  - **Mükellef toplamı — en yüksek üstte:** Mükellefler, toplam ödenecek
    tutarlarına göre büyükten küçüğe sıralanır; her mükellefin tüm satırları
    bir arada gelir.
  - **Tutar — azalan / artan:** Satır bazında tutara göre sıralar.
  - **Vergi Kimlik No:** Mükellef bazında sıralar.

Sütun başlıklarına tıklayarak da hızlıca sıralayabilirsiniz.

### 3. Günleri Karşılaştır
İki farklı yüklemeyi (örn. dünkü ve bugünkü liste) seçip karşılaştırın.
**Vergi Kimlik No** (mükellef) veya **Tahakkuk Fiş No** bazında, her anahtarın
iki gündeki toplam tutarı, farkı ve durumu listelenir:

- **Yeni:** Yalnızca B (sonraki) yüklemede var.
- **Çıkan:** Yalnızca A (önceki) yüklemede var.
- **Değişti:** İki günde de var, tutar farklı.
- **Aynı:** İki günde de aynı tutar.

### Excel'e Aktar
**⬇ Excel'e Aktar** ile o anki sorgu sonucunu `.xlsx` olarak kaydedebilirsiniz.

### Geçmiş Yüklemeler
En alttaki listeden eski yüklemeleri **Aç**'abilir veya **Sil**'ebilirsiniz.

## Vergi Kodu Adları
Uygulama, resmî vergi türü kodlarının (0001, 0003, 1046, 1048, ...) açıklamalı
adlarıyla birlikte gelir; sonuçlarda kodun yanında adı da görünür. Liste,
gerekirse uygulama içinden güncellenebilir.

## Veriler nerede saklanıyor?
- Veri tabanı: `veritabani/tahakkuk.db` (SQLite — tek dosya).
- Yedeklemek için bu dosyayı kopyalamanız yeterlidir.
