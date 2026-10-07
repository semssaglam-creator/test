# Takip PDF → Excel — Geliştirme Notları (proje hafızası)

Kullanıcının iş bilgisayarı için yazıldı. Genel kurallar kullanıcının verdiği
"İş Bilgisayarı İçin Uygulama Notları"ndadır (kurulum yok, saf Python + yerel
sunucu + tarayıcı, .tar.gz, denetimli paketleyici). Bu dosya pakete girmez.

## Ne yapar
Vergi dairesi takip listesi PDF'ini (sütun çizgisi yok, metin sütun
konumlarına göre yazılmış) kayıtlara ve 15 sütuna ayırır, .xlsx üretir.
Sütunlar: Sıra No, Vergi No, TC Kimlik No, Plaka No, Soyad Ad/Unvanı, Adres,
Vergi Dönemi, Ana Vergi Kodu, Vergi Kodu, Ana Takip Dosya No, Takip Dosya No,
Vergi Aslı Borcu Toplamı, KGZ Toplamı, Ceza Tutarı, Toplam Borç
(+ Excel'de "Kontrol" ve "Kaynak PDF").

## Yapı
- `main.py` — 127.0.0.1:8790.. sunucu; zaten açıksa yalnızca tarayıcıyı açar;
  sayfa 15 dk nabız göndermezse kapanır (konsolsuz başlatmada arka planda
  sonsuza dek kalmasın diye).
- `app/pdf_kelime.py` — pypdf ile konumlu kelimeler. pypdf'in layout-mode iç
  fonksiyonları (`recurs_to_target_op`, `TextStateManager`) kullanılıyor:
  her Tj/TJ için başlangıç x'i ve font genişliklerinden bitiş x'i.
- `app/ayristirici.py` — kayıt/sütun ayırma (yöntem dosya başında).
- `app/excel.py` — openpyxl, bellekte (BytesIO).
- `web/index.html` — tek dosya arayüz; veri tarayıcıda, sunucu durumsuz.
- `paketle.py` — denetler, sonra `dist/takip_pdf_excel-<sürüm>.tar.gz`.

## Verilmiş kararlar (yeniden açmayın)
1. **pypdf 4.3.1 sabit (lib/).** Layout-mode iç API'si kullanılıyor; sürüm
   değişirse kırılabilir. Güncellenecekse tests/ çalıştırılmalı. pdfminer.six
   seçilmedi: `cryptography`yi modül başında içe aktarıyor (derlenmiş paket).
   pypdf 3.17.4 (uzlaşma uygulamasındaki) seçilmedi: layout-mode yok.
2. **typing_extensions 4.13.2, `lib_ek/`, sys.path SONUNA.** pypdf 4.3.1
   Python < 3.11'de ister. 4.13.2, Python 3.8'i destekleyen son sürüm.
3. **Sistem `cryptography`si bozuksa engellenir** (`app/__init__.py`).
   Geliştirme makinesinde python3.11 + Debian `cryptography` `_cffi_backend`
   eksikliğinde Rust panic (BaseException) fırlattı; pypdf yalnızca
   ImportError yakaladığından uygulama hiç açılmadı. Test:
   `tests/test_bozuk_sistem_paketi.py` (korumayı kaldırınca kırıldığı görüldü).
   Bedeli: AES şifreli PDF açılamaz → kullanıcıya "PDF'e yazdır" önerilir.
4. **pypdf genişlik tablosu tamamlanıyor** (`_genislik_tamamla`): /Encoding'i
   olmayan TrueType alt kümelerinde pypdf width_map'i boş bırakıyor; harf harf
   yazılmış metin kelimeye birleşmiyordu.
5. **Okunamayan tutar asla 0 yazılmaz** (boş + kırmızı + Kontrol sütunu) ve
   her kayıtta Toplam Borç = Aslı + KGZ + Ceza denetlenir.
6. **Çapa = Vergi Dönemi hücresi.** Sıra No yerine dönem seçildi: her kaydın
   ilk satırında mutlaka var ve biçimi kesin (AA/YYYY-AA/YYYY). Dönem hücresi
   bitişik sütunla tek kelime gelirse (`OĞLU11/2021-11/2021`) ayrılır.
7. **ALL CAPS ad/adres olduğu gibi bırakılır.** Bu bir döküm, resmî belge
   değil; yazım düzeltmesi veriyi değiştirir.
8. **Arşiv .tar.gz; başlatıcı `Takip PDF Excel.desktop`** — `sh calistir.sh`
   ile çalıştırır, böylece calistir.sh'nin çalıştırma izni kaybolsa da açılır.

## Test
`python3 -m unittest discover -s tests` (stdlib). Örnek PDF'ler sahte veriyle
`tests/ornek_pdf_uret.py` ile üretilir (reportlab, yalnızca geliştirmede) —
üç yazım biçimi: hücre başına BT, tek BT, harf harf. Üçü de `beklenen.json` ile
birebir aynı çıkmalı. **Depo herkese açık: gerçek mükellef verisi koymayın.**
Arayüz headless Chromium (Playwright) ile denendi: yükleme, önizleme, kırmızı
hücreler, bozuk PDF mesajı, Excel indirme. Python 3.8 / 3.9 / 3.11 / 3.13'te
testler geçti.

## Bekleyen
- **Gerçek PDF ile doğrulanmadı.** Elimizde yalnızca ekran görüntüsü vardı;
  düzen ondan taklit edildi. Kullanıcıdan gerçek PDF gelince maskeli bir
  kopyasıyla gerileme testi eklenmeli.
- `.desktop` başlatıcısı (`%k` ile) gerçek GNOME/KDE masaüstünde denenmedi.
