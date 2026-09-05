# Bu depoda ne var?

Klasörler **işletim sistemine göre** ayrılmıştır. Kendi bilgisayarınıza ait
klasörü indirin; diğerlerini indirmenize gerek yok, açmanıza hiç gerek yok.

| Klasör | Kime | İçinde ne var |
|---|---|---|
| `linux/` | **Sizin iş bilgisayarınız** | KDV İnceleme Çalışması ve Uzlaşma Takip uygulamaları. Çalışmaya hazır, kurulum gerekmez. |
| `windows/` | Windows kullananlar | Yalnızca Windows'a özgü başlatıcılar (`.bat`) ve Windows paketini üreten betik. Uygulamanın kendisi burada değil. |
| `mac/` | Mac kullananlar | Beyanname dökümü alma aracı (`.command`). |
| `gelistirme/` | Geliştirme | Notlar, örnek belgeler, rapor şablonu. Uygulamayı çalıştırmak için gerekmez. |

## Linux'ta başlatmak

```
linux/kdv_uygulamasi/    -> "KDV İnceleme Çalışmasını Başlat" dosyasına çift tıklayın
linux/uzlasma_uygulamasi/ -> calistir.sh
```

Kurulum ayrıntıları için `linux/kdv_uygulamasi/KURULUM.txt`.

## Neden ayrıldı?

Tek klasörde Windows ve Linux dosyaları birlikte duruyordu; başlatıcı
aralarında kayboluyor, hangi dosyanın çalıştırılacağı anlaşılmıyordu.
Artık `linux/` klasöründe tek bir `.bat` dosyası bile yok.

Uygulamanın **kaynağı tek yerde** durur: `linux/kdv_uygulamasi/`. Windows
paketi de oradan üretilir (`windows/kdv_uygulamasi/paketle.sh`), kopyası
tutulmaz — iki kopya zamanla birbirinden ayrılır ve hangisinin doğru
olduğu belirsizleşir.
