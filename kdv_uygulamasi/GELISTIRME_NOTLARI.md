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

---

## Not düşerken

Şunlar yazılırsa iş kolaylaşır:

- **Nerede**: hangi sekme, hangi düğme, hangi belge bölümü
- **Ne oldu / ne olmalıydı**: beklenen ile görülen
- Ekran görüntüsü ya da çıktı dosyası varsa iyi olur

Biçim önemli değil; tek satır not da yeter, ayrıntı da.
