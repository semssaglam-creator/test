# Terminalden Çalışma

Bu dosya, uygulamayı terminal üzerinden çalıştırmak isteyenler içindir.
Grafik arayüzden (çift tıklayarak) kullanım için `KURULUM.txt` dosyasına
bakın.

## Kaynağı almak

Uygulama şu depoda, `claude/dosya-gorunurlugu-3p8f9d` dalında duruyor:

```
git clone -b claude/dosya-gorunurlugu-3p8f9d \
    https://github.com/semssaglam-creator/test.git
cd test/kdv_uygulamasi
```

Sonradan güncelleme almak için:

```
git pull origin claude/dosya-gorunurlugu-3p8f9d
```

Git kullanmak istemezseniz depo sayfasındaki **Code > Download ZIP**
bağlantısı da aynı işi görür; dalın seçili olduğundan emin olun.

## Gereksinim

Python 3.8 veya üzeri. Başka hiçbir şey kurmanız gerekmez: Excel çıktısı
için `openpyxl`, beyanname PDF'leri için `pypdf` uygulamayla birlikte
`lib/` ve `lib_ek/` klasörlerinde gelir.

Sürümünüzü görmek için:

```
python3 -V
```

## Çalıştırma

```
python3 main.py
```

Ekrana çalıştığı adresi yazar (varsayılan `http://127.0.0.1:8766/`) ve
varsayılan tarayıcınızda açar. Kapatmak için **Ctrl+C**.

Port doluysa — örneğin uygulama zaten açıksa — sıradaki boş port denenir
(8766–8775). Hangi portta çalıştığı ekranda yazar.

Sunucu yalnızca `127.0.0.1` adresine bağlanır; ağdaki başka bir makineden
erişilemez. Veriler bilgisayardan dışarı çıkmaz.

Masaüstü olmayan bir makinede ya da SSH oturumunda tarayıcı açılamaz;
uygulama yine de çalışır, adresi elle açmanız yeterlidir.

## Kısayol kurmak (isteğe bağlı)

Menüye ve masaüstüne kısayol eklemek için:

```
bash kur.sh
```

Kurulum bittiğinde uygulamayı da başlatır. Sisteme dosya kopyalamaz,
yönetici yetkisi istemez. Kaldırmak için `bash kaldir.sh`.

Kısayol, kurulumu yaptığınız andaki klasörü açar. Uygulamayı başka bir
klasöre taşırsanız `bash kur.sh` komutunu orada yeniden çalıştırın.

## Veriler nerede

| Klasör        | İçerik                                              |
|---------------|-----------------------------------------------------|
| `veritabani/` | `kdv.db` — kaydettiğiniz bütün çalışmalar           |
| `yedekler/`   | Arayüzdeki **Yedek Al** ile alınan yedekler         |
| `ciktilar/`   | Üretilen Excel dosyaları                            |

Hepsi uygulama klasörünün içindedir. Başka bir bilgisayara taşırken bu
klasörleri de kopyalayın. Depoya gönderilmezler (`.gitignore` içinde).

Elle yedek almak için `veritabani/kdv.db` dosyasını kopyalamanız yeterli;
uygulama kapalıyken yapın.

## Sorun giderme

Uygulama açılmazsa gerekçe ekrana yazılır. Masaüstü kısayolundan
açtığınızda ekran olmadığı için gerekçe

```
KDV HATA - BUNU GONDERIN.txt
```

dosyasına yazılır (yazılamıyorsa ev dizinine). Yalnızca hata halinde
oluşur; başarılı açılışta böyle bir dosya olmaz.

Beyanname PDF'leri okunamıyorsa yalnızca o ekran hata verir; uygulamanın
geri kalanı etkilenmez. PDF okuyucu ancak beyanname yüklendiğinde devreye
girer.

Kütüphane sürümleri Python 3.8 gözetilerek seçilmiştir
(`pypdf` 5.9.0, `typing_extensions` 4.13.2). `lib_ek/` klasörü arama
yolunun **sonuna** eklenir; bilgisayarınızda kurulu bir `typing_extensions`
varsa o kullanılır, böylece ona güvenen başka paketler (örneğin Pillow)
bozulmaz.

## Kullanım

Uygulamanın kendisi hakkında ayrıntılı anlatım için `KULLANIM.md`.
