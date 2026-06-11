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
