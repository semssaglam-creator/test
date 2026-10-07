# İş Bilgisayarı (Linux) İçin Uygulama Geliştirme — Ajan Notları

Bu notlar, bir vergi müfettişinin **iş bilgisayarında** çalışacak masaüstü
uygulamaları için yazıldı. Bir uygulama bu yolla yazıldı ve sahada kullanılıyor;
aşağıdaki kuralların çoğu teorik değil, kırılıp düzeltilmiş noktalardır.

**Bu dosyayı işe başlamadan önce okuyun.** Buradaki kısıtlar keyfi değil; her
birinin altında, gerekçesi bilinmezse "iyileştirme" diye geri bozulacak bir
sebep var.

---

## 1. Makine hakkında bilmeniz gerekenler

Kurumsal bir makine. Pratikte şu anlama gelir:

- **Kurulum yapılamaz.** `pip install`, `apt install`, sanal ortam, Docker,
  Node, derleyici — hiçbirine güvenmeyin. Kullanıcı yönetici değil ve kurumsal
  ilke kurulumu engelleyebilir.
- **Ağ kısıtlı olabilir.** Kurumsal proxy var. Uygulamanın çalışmak için
  internete ihtiyaç duymaması gerekir.
- **Python 3 kuruludur.** Hemen her dağıtımda gelir. Dayanılabilecek tek şey
  budur.
- Kullanıcı yazılımcı değil. Terminal kullanmasını bekleyemezsiniz; "çift
  tıkla, açılsın" olmalı.

Bunları kullanıcıya tekrar sormayın, ama **varsayımlarınızı ilk turda bir
cümleyle doğrulatın** — makine değişmiş olabilir.

---

## 2. Mimari: yerel sunucu + tarayıcı

Sahada işe yarayan kalıp:

```
main.py            → yerel HTTP sunucusu başlatır, tarayıcıyı açar
app/               → bütün mantık (saf Python)
web/index.html     → tek dosyalık arayüz (HTML + CSS + JS, hepsi içinde)
lib/               → gerekiyorsa vendor'lanmış saf Python paketleri
```

Neden bu kalıp:

- **Arayüz için hiçbir şey kurulmaz.** Tk, Qt, GTK, Electron — hepsi kurulum
  ya da sistem paketi ister. Tarayıcı zaten var.
- Aynı kod Linux'ta da Windows'ta da çalışır.
- Arayüzü tek HTML dosyasında tutmak derleme adımı gerektirmez: değiştir,
  sayfayı yenile. Bundler, npm, TypeScript yok.

Sunucu **yalnızca loopback** dinlesin (`127.0.0.1` ve `::1`). Dışarıya
açılmasın; iş makinesinde kurumsal veri var.

Veriyi sunucuda tutmayın. Tarayıcı veriyi bellekte taşısın, her hesap için
sunucuya göndersin, sunucu yalnızca hesaplayıp döndürsün. Kaydetme ancak
kullanıcı "Kaydet" dediğinde olsun. Böylece sunucu durumsuz kalır ve iki
sekme birbirini bozmaz.

---

## 3. Bağımlılık kuralı

**Önce standart kütüphane.** Gerçekten gerekiyorsa, yalnızca **saf Python**
(derlenmiş uzantısı olmayan) bir paketi klasöre kopyalayıp `sys.path`'e ekleyin:

```python
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(BASE_DIR, "lib"))
```

Böyle taşınabilenler: `openpyxl` (Excel), `pypdf` (PDF okuma), `et_xmlfile`.
Taşınamayanlar: numpy, pandas, Pillow, lxml, cryptography — derlenmiş uzantı
içerirler, o makinede derlenemezler.

### Sahada öğrenilmiş tuzak: ortak modülü başa eklemeyin

Bir paketin ihtiyaç duyduğu ortak bir modülü (`typing_extensions` gibi)
taşımanız gerekirse **`sys.path`in SONUNA ekleyin**, başına değil:

```python
sys.path.append(os.path.join(BASE_DIR, "lib_ek"))
```

Gerekçesi: başa eklerseniz sistemde kurulu sürümü gölgelersiniz. Bir kez,
sistemdeki Pillow bizim sürümümüzü yükleyip `AttributeError` fırlattı;
`openpyxl` bunu `ImportError` beklediğinden yakalayamadı ve **uygulama hiç
açılmadı**. Sona eklenince sistemdeki sürüm varsa o kullanılır, yoksa bizimki
yedek olarak devreye girer.

---

## 4. Teslim: paket ve başlatıcı

### `.tar.gz` kullanın, `.zip` değil

`zip` çalıştırma iznini her arşivleyicide korumaz. `calistir.sh`
çalıştırılamaz hâlde açılırsa uygulama **"hiç açılmıyor"** görünür — masaüstü
kısayolu hiçbir şey yazmadan başarısız olur. `tar` bu bilgiyi her zaman taşır.

### "Çift tıklayınca hiçbir şey olmuyor"

Linux masaüstlerinde çok olağandır ve uygulamayla ilgisi yoktur. Kullanıcıya
verdiğiniz OKUBENI dosyasında bunları **mutlaka** yazın:

1. Dosya yöneticileri (Nautilus, Nemo, Dolphin) `.sh` dosyalarını çift
   tıklayınca çalıştırmaz; metin düzenleyicide açar ya da hiçbir şey yapmaz.
2. Masaüstüne konan `.desktop` kısayolu "güvenilir" işaretlenmemişse sessizce
   hiçbir şey yapmaz — sağ tık → "Çalıştırmaya izin ver".
3. Arşiv sürükle-bırak ile açıldıysa çalıştırma izni kaybolmuş olabilir:
   `chmod +x calistir.sh`.

### Açılış kaydı — en değerli ayrıntı

Masaüstü kısayolundan çalıştırıldığında **konsol yoktur**: Python bir hata
verse bile ekrana hiçbir şey gelmez. Başlatıcı şunu yapsın:

```sh
if [ -t 1 ]; then
    exec python3 main.py          # terminalden çalıştı, çıktı zaten görünüyor
fi
python3 main.py >>"$KAYIT" 2>&1   # konsol yok: çıktıyı dosyaya yaz
```

Ve kullanıcıya şunu söyleyin: **dosyanın hiç oluşmamış olması da bir
cevaptır.** Oluştuysa uygulama çalışmış, hata varsa içinde yazıyor.
Oluşmadıysa betik hiç çalıştırılamamış — yani yukarıdaki 1/2/3 maddelerinden
biri. Bu ayrım, uzaktan teşhiste saatler kazandırır.

Başlatıcı ayrıca Python 3 yoksa bunu **pencerede** söylesin (`zenity` ya da
`kdialog` varsa onunla), çünkü konsol yok.

---

## 5. Paketleyici üretmekle kalmasın, DENETLESİN

Paketi üreten betik, bir koşul bozulursa **paket vermesin**. Bu yöntemin
kalbidir: kullanıcıda ortaya çıkacak hataları, paket daha üretilirken yakalar.

Denetim örnekleri: zorunlu dosyalar yerinde mi, `calistir.sh` çalıştırılabilir
mi, `.sh` dosyaları LF ile mi bitiyor, kullanıcı verisi (veritabanı, çıktılar)
pakete sızmış mı, geliştirme notları sızmış mı.

**Yeni bir kural öğrenildiğinde oraya bir denetim ekleyin.** Ve en önemlisi:

> Denetimi yazdıktan sonra, koruduğu şeyi **bilerek bozup** denetimin
> gerçekten attığını görün.

Bu boş bir tören değil. Bir kez, bir denetim test verisindeki bir metin yanlış
olduğu için bozuk sürümde bile geçiyordu — koruduğunu sandığımız şeyi hiç
korumuyordu. Geçen bir denetimin gerçekten koruduğunu ancak bozarak
anlarsınız.

---

## 6. Resmî belge / veri üreten kod yazıyorsanız

Bu kullanıcının çıktıları imzalanıyor ve kuruma gidiyor. En büyük risk çökme
değil, **sessizce yanlış sayı yazmaktır.**

- **Bilmediğiniz bir değeri uydurmayın.** Belgeye kırmızı bir yer tutucu
  bırakın (`[tutar]`, `[tarih]`). Kullanıcı kırmızıyı görüp doldurur; sessiz
  bir sıfır fark edilmez.
- **Eksik veriyi sıfır saymak tehlikelidir.** Bir alan adını tanımadığınız
  için okunamayan değer de sıfır görünür. Böyle bir tasarım kuruyorsanız,
  veriyi bağlayan bir aritmetik denetim de yazın (toplamlar tutuyor mu), yoksa
  hata sessiz kalır. Sahada tam olarak böyle oldu: alan adı değişti,
  2.209.951,45 TL matrah 0,00 yazıldı ve hiçbir uyarı çıkmadı.
- **Tarihleri içeride ISO tutun** (`2026-04-15`), ekranda yerel biçimde
  gösterin. Karışık biçimler ayrıştırmayı sessizce bozar.

### Türkçe yazım tuzakları

- **Büyük `I` ile `İ` ayrımı.** Python'un `.lower()`'ı Türkçe değildir.
  `"LIMAN".lower()` → `liman` (yanlış), Türkçe kuralı `lıman`. Kendi
  `kucuk()`/`buyuk()` fonksiyonlarınızı yazın.
  Ama dikkat: ALL CAPS girdide `I`nin `ı` mı `i` mi olduğu **gerçekten
  belirsizdir** (`KADIKÖY` doğru, `LIMAN` yanlış). Kör bir kural koymayın —
  bilinen adlardan oluşan küçük bir tablo ile noktadan bağımsız eşleştirin,
  eşleşme yoksa yazılana dokunmayın.
- **Kurum adlarında kesme işareti kullanılmaz:** "Müdürlüğünün", "Müdürlüğü'nün"
  değil.
- Sistem dökümlerinden ALL CAPS metin gelir; belgeye yazmadan önce yazım
  kurallarına çevirin.

---

## 7. Test etme — gerçek makine olmadan

- **Arayüzü gerçekten açın.** Headless Chromium ile sayfayı yükleyip konsol
  hatalarını toplayın, kutulara yazın, değerin veriye işlendiğini doğrulayın.
  "Kod doğru görünüyor" yetmez.
- **Sunucu uçlarını doğrudan çağırın.** Tarayıcı sürmeden, istek sınıfının
  metodunu elle çağırarak belge/çıktı üretimini uçtan uca çalıştırabilirsiniz.
- **Sahadan gelen gerçek veriyi (maskelenmiş olarak) saklayın** ve gerileme
  testi kurun. Girdi biçimi sizin denetiminizde değilse — başka bir kurumun
  ürettiği PDF, Excel dökümü — bir gün değişir. Elinizde o biçimin örneği
  yoksa değiştiğini ancak kullanıcı yanlış sayı gördüğünde anlarsınız.

---

## 8. Bu kullanıcıyla çalışma biçimi

- **Yazılımcı değil, alan uzmanı.** Hukuki ya da mesleki bir soruda kararı o
  verir; siz seçenekleri ve sonuçlarını gösterin, yerine karar vermeyin.
- **Gerçek işinde deneyip döner.** "Şurada şu çıkıyor, oysa şöyle olmalı"
  biçiminde geri bildirim gelir. Çoğu zaman sorun koddaki bir hata değil,
  bir alanın bulunamaması ya da bir varsayımın yanlış olmasıdır — düzeltmeden
  önce **neyi kastettiğini** anlayın.
- **Proje hafızası tutun.** Depoda bir `GELISTIRME_NOTLARI.md` bulundurun; ne
  yaptığınızı ve **neden** öyle yaptığınızı yazın. Sohbet kapandığında kalan
  tek şey odur.
- **Verilmiş kararları ayrı bir başlık altında yazın** ("yeniden açmayın")
  ve gerekçesini de yazın. Yoksa sonraki oturum ya da devralan ajan aynı
  tartışmayı yeniden açar.

---

## 9. Windows'a da taşınacaksa

Ayrı bir ağaçta tutun ve ortak kodu bir eşitleme betiğiyle taşıyın; tek ağaçta
yapılan düzeltme diğerinde sessizce eski davranış olarak yaşar.

Windows'a özgü, sahada doğrulanmış tuzaklar:

1. **Kullanıcıya `localhost` verin, `127.0.0.1` vermeyin.** Windows'un "yerel
   adresler için proxy kullanma" ayarı yalnızca NOKTASIZ adları kapsar;
   `127.0.0.1` kurumsal proxy'ye gider ve sunucu sorunsuz çalışırken kullanıcı
   "sayfaya ulaşılamadı" görür.
2. `localhost` Windows'ta önce `::1`e çözülür; sunucu çift dinlemeli. Ama
   **"IPv6 yok" ile "port dolu" durumlarını AYIRIN** (`errno.EADDRINUSE`);
   ayırmazsanız `::1`e bağlanamayan bir makinede bütün portlar dolu görünür ve
   uygulama "uygun port bulunamadı" deyip kapanır. Bu, tuzağı kapatan
   düzeltmenin kendisinin açtığı bir arızadır.
3. `.bat` dosyaları **CRLF** ile bitmeli; LF `goto` etiketlerini bozar.
4. Kullanıcıya okutulan `.txt` dosyaları CRLF **ve UTF-8 BOM'lu** olmalı;
   BOM'suz dosyayı eski Notepad ANSI sanar, Türkçe harfler bozulur.
5. `.bat` içinde yolları tırnaklayın — klasör adında boşluk olur ve `cmd` yolu
   ilk boşlukta keser.
6. Windows açık dosyayı kilitler; geçici dosyaya yazıp okumayın, akış
   (`io.BytesIO`) kullanın.
7. `webbrowser.open` hiçbir tarayıcı bulamazsa istisna fırlatmaz, sessizce
   `False` döner — dönüş değerini kontrol edin.

Kurulum gerektirmeyen bir Windows paketi için gömülü (embeddable) Python
kullanılabilir; `._pth` dosyasına uygulama klasörleri yazılmazsa
`ModuleNotFoundError` alırsınız.

---

## Özet — ilk turda yapılacaklar

1. Yukarıdaki kısıtları kullanıcıya bir cümleyle doğrulatın.
2. Kurulum gerektirmeyen bir yol seçin: saf Python + yerel sunucu + tarayıcı.
3. İskeleti kurun, **uygulamayı gerçekten açın**, sonra özellik yazmaya
   başlayın.
4. Paketleyiciyi en baştan denetimli yazın; her yeni kuralda denetim ekleyin
   ve denetimi bozarak sınayın.
5. Proje hafızası dosyasını ilk gün açın.
