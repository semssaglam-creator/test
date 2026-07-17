# Fatura İnceleme Uygulaması — Kullanım Kılavuzu

PDF faturaları (e-Fatura / e-Arşiv / taranmış) okuyup yerel bir veritabanına
işler; **ürün, fatura no, tarih, alıcı/satıcı** bazında sorgulama ve iki
sayfalı **Excel** raporu (Fatura Özeti + Kalem Detayı) üretir.

Tüm veriler bilgisayarınızda kalır; uygulama internete hiçbir şey göndermez.

## Başlatma

- **Linux:** `calistir.sh` dosyasını çalıştırın (veya `python3 main.py`).
- **Windows:** `calistir.bat` dosyasına çift tıklayın (Python 3 kurulu olmalı,
  kurarken "Add python to PATH" işaretlenmeli).

Tarayıcıda `http://127.0.0.1:8766/` açılır. Kurulum gerekmez; gerekli
kütüphaneler `lib/` klasöründe paketli gelir.

## Günlük kullanım

1. **Ayarlar / Durum** sekmesinde incelenen mükellefin **VKN/TCKN**'sini girin.
   Böylece her fatura otomatik sınıflanır: mükellef **alıcıysa alış**,
   **satıcıysa satış** faturası. (Sonradan girerseniz "yönleri yeniden hesapla"
   kutusu işaretliyken kaydedin.)
2. **Fatura Yükle** sekmesine PDF'leri sürükleyip bırakın (toplu seçilebilir).
   - Metin tabanlı e-Fatura/e-Arşiv PDF'leri doğrudan okunur.
   - Taranmış PDF'ler OCR ile okunur; OCR araçları yoksa **"OCR bekliyor"**
     olarak kaydedilir (aşağıya bakın).
   - Aynı fatura (ETTN veya fatura no + satıcı VKN) ikinci kez eklenmez.
3. **Sorgula** sekmesinde filtreleri doldurun:
   - *Ürün içeriği*: ör. `elma` → kalemlerinde "elma" geçen faturalar.
     Yön filtresini `Alış` yapıp ürün alanına `gübre` yazarsanız
     "alış faturalarında gübre içerenler" listelenir.
   - *Görünüm*: "Fatura bazında" (fatura başına satır) veya
     "Kalem bazında" (ürün satırı başına satır).
   - **Excel İndir**: o anki filtreye uyan kayıtları iki sayfalı
     (Fatura Özeti + Kalem Detayı) dosya olarak indirir; bir kopyası
     `raporlar/` klasörüne de kaydedilir.
4. Satıra tıklayınca **detay penceresi** açılır: alanları düzeltebilir,
   kalemleri ekleyip silebilir, saklanan **PDF'i açıp** yan yana
   karşılaştırabilir, ham okunan metni görebilirsiniz.
   "Kaydet ve Onayla" kaydı **Tamam** durumuna getirir.

## Durum rozetleri

| Rozet | Anlamı |
|---|---|
| **Tamam** | Alanlar sorunsuz ayrıştırıldı ya da elle onaylandı. |
| **Kontrol** | Ayrıştırmada eksik/uyumsuz alan var (uyarı sütununda nedeni yazar). Detayda düzeltip onaylayın. OCR ile okunan her fatura önce bu duruma düşer. |
| **OCR bekliyor** | Taranmış PDF, OCR araçları kurulu olmadığı için okunamadı. PDF saklanır; OCR kurulunca "PDF'ten Yeniden Oku" ile işlenir veya alanlar elle girilir. |

> **Önemli:** OCR hiçbir zaman %100 doğru değildir. İncelemeye dayanak
> yapmadan önce "Kontrol" durumundaki faturaların tutarlarını mutlaka asıl
> PDF ile karşılaştırın.

## Taranmış faturalar için OCR kurulumu

İki araç gerekir: **Tesseract** (yazı tanıma) ve **Poppler/pdftoppm**
(PDF'i görüntüye çevirme). Uygulama bunları önce kendi `araclar/`
klasöründe, sonra sistemde arar. Durumu **Ayarlar / Durum** sekmesinden
görebilirsiniz.

### Windows — tek tıkla kurulum (önerilen)

Uygulama klasöründeki **`OCR_KUR.bat`** dosyasına çift tıklayın. Betik:

1. Poppler'ı otomatik indirip `araclar\` klasörüne açar (yönetici yetkisi
   gerekmez),
2. Tesseract kurulum sihirbazını indirip başlatır — sihirbazda
   **"Additional language data"** altından **Turkish**'i işaretlemeniz
   yeterli,
3. sonunda "OCR HAZIR" doğrulamasını gösterir.

İnternet bağlantısı gerekir; indirme engellenirse betik elle indirme
adreslerini gösterir.

### Windows (elle kurulum)

1. Tesseract: https://github.com/UB-Mannheim/tesseract/wiki adresinden
   kurulum dosyasını indirin. Kurulumda **"Additional language data"**
   altından **Turkish**'i işaretleyin.
2. Poppler: https://github.com/oschwartz10612/poppler-windows/releases
   adresinden zip'i indirin.

### Windows (kurulumsuz, taşınabilir)

Kurulum yetkiniz yoksa iki aracın da taşınabilir sürümü `araclar/`
klasörüne açılabilir:

1. Poppler zip'ini `araclar\` içine çıkarın
   (içinde `...\Library\bin\pdftoppm.exe` bulunmalı).
2. Tesseract'ı başka bir bilgisayarda kurup `C:\Program Files\Tesseract-OCR`
   klasörünü olduğu gibi `araclar\Tesseract-OCR\` olarak kopyalamak da
   çalışır (`tessdata` içinde `tur.traineddata` bulunduğundan emin olun).

Uygulamayı yeniden başlatın; Ayarlar sekmesinde "OCR hazır" görünmelidir.

### Linux (kurulum yetkisi varsa)

```bash
sudo apt install tesseract-ocr tesseract-ocr-tur poppler-utils
```

Kurulum yetkisi olmayan Linux makinede taranmış faturalar "OCR bekliyor"
olarak birikir; bu PDF'leri Windows makinede işleyebilir ya da elle
girebilirsiniz. Metin tabanlı e-Faturalar her makinede sorunsuz okunur.

## Bilgisayarlar arası taşıma

Uygulama klasörünü olduğu gibi (USB vb. ile) kopyalamak yeterlidir. Tüm
veri şu klasörlerdedir:

- `veritabani/faturalar.db` — kayıtlar
- `belgeler/` — yüklenen PDF'lerin saklanan kopyaları
- `raporlar/` — üretilen Excel dosyaları

Büyük işlerde ara ara **Ayarlar → Yedek Al** kullanın; yedekler
`yedekler/` klasörüne düşer.

## Sık sorulanlar

- **10.000 fatura kaldırır mı?** Evet; kayıtlar SQLite'ta tutulur, sorgular
  sayfalanır. Yüklemeyi parça parça yapmanız (ör. 500'erlik gruplar)
  yeterlidir; mükerrer kontrolü sayesinde aynı dosyayı iki kez yüklemek
  sorun çıkarmaz.
- **Kalemler yanlış/eksik ayrıştı.** Her firmanın PDF şablonu farklı
  olduğundan kalem tablosu her zaman tam çözülemeyebilir; fatura "Kontrol"
  durumuna düşer. Detay penceresinde ham metne bakarak kalemleri hızla
  düzeltebilirsiniz.
- **Port çakışması:** Uygulama 8766 portunu kullanır (uzlaşma uygulaması
  8765'te çalışır; ikisi aynı anda açılabilir).
