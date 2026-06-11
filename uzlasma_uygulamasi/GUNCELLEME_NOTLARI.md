# Güncelleme Notları (kullanıcı geri bildirimleri — toplu yapılacak)

## 1. PDF yükleme (kopyala-yapıştır yerine / yanında)
- Dilekçe PDF'ini sürükle-bırak veya dosya seçici ile yükleyebilmeli.
- Tek tek veya **toplu** (birden çok dilekçe aynı anda) yüklenebilmeli.
- Not: PDF metin çıkarma stdlib'de yok; saf Python pdf metin çıkarıcı
  (vendored, ör. pdfminer benzeri hafif çözüm) veya PDF'in metin
  katmanını zipsiz ham ayrıştırma gerekecek. Çıkan metin mevcut
  `paste_parser.dilekce_ayristir`'a verilecek.

## 2. Tutanak tablosu sadeleştirme
- Tutanakta **Ceza Nedeni** ve **Dönem** kolonlarına gerek yok.
- Yeterli kolonlar: İhbarname Numarası, Ceza Türü (vergi/ceza kodu),
  Ceza Tutarı (+ uzlaşılan tutar).
- Dönem dilekçede zaten yok; elle giriş zorunluluğu da kalkacak —
  kayıt ekranında Dönem/Ceza Nedeni alanları sadeleştirilebilir.
- "Kopyaladığımda gereksiz bilgiler geliyor" → ayrıştırıcı yalnızca
  fiş no + vergi türü + ceza kodu + tutar alacak şekilde sadeleşecek.

## 3. Dilekçe Kaydı ekranı — tablo sadeleştirme
- "İhbarname / Ceza Satırları" giriş tablosundan **Vergi Türü**,
  **Ceza Nedeni** ve **Dönem** kolonları kaldırılacak.
- Kalacak kolonlar: İhbarname Fiş No, Ceza Kodu, Miktar (TL),
  Düzenleme T., Tebliğ T.
- Soru (toplu güncellemede netleştir): tutanaktaki "Vergi ve Cezanın
  Türü" kolonu şimdiye dek "vergiTürü/cezaKodu" (örn. 0015/3080)
  biçimindeydi; vergi türü girilmeyecekse tutanakta yalnızca ceza
  kodu mu yazılsın?

## Uygulananlar (11.06.2026)
- [x] Tutanak Excel'leri A4 dikey, "genişliğe sığdır" yazdırma ayarlı;
      satır yükseklikleri metne göre otomatik (adres/paragraf kesilmez)
- [x] Davetiye tarihi alanı her sonuçta aktif (yalnızca Gelmedi'de
      zorunlu); uzlaşıldı/uzlaşılamadı tutanak başlığına da yazılıyor
- [x] Komisyon üyeleri seçimi belirgin onay kutulu liste (çoktan seçmeli)
- [x] İstatistiklere mükellef bazında tablo eklendi

## Bekleyenler (toplu güncelleme)
- [ ] Not 1: PDF sürükle-bırak / toplu dilekçe yükleme
- [ ] Not 2-3: Vergi türü / ceza nedeni / dönem kolonlarının kaldırılması
