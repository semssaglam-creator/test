# Çizgisiz Tablo Ayıklayıcı

Sütunları çizgiyle ayrılmamış PDF tablolarını (ör. amme alacakları borç listesi) Excel'e çeviren, **tek dosyalık ve çevrimdışı** çalışan araç.

## İndir ve kullan

1. [`pdf-tablo-ayiklayici.html`](https://github.com/semssaglam-creator/test/raw/HEAD/pdf-tablo-ayiklayici/pdf-tablo-ayiklayici.html) dosyasını indir.
2. Firefox ya da Chrome ile aç (Linux, macOS, Windows). Kurulum ve internet gerekmez.
3. **PDF aç…** ile dosyanı seç ya da sayfaya sürükle; **Excel'e aktar** de.

PDF tarayıcının içinde işlenir, hiçbir sunucuya gönderilmez.

## Nasıl çalışır

- Her kelimenin sayfadaki gerçek konumu PDF işlem listesinden hesaplanır; dar sütun aralıkları da ayrılır.
- Başlık listesindeki sütun sayısına göre en belirgin dikey boşluklar sütun sınırı seçilir. Sınırlar önizlemede elle eklenip kaydırılabilir.
- Anahtar sütunu (Sıra No) boş, tutarı olmayan satırlar üstteki kaydın devamı sayılır (alta kayan Ad, Adres, takip no).
- Tutarı olan ek kalemler ayrı satır kalır; seçilen kimlik sütunları üstten doldurulur.
- Tutarlar sayı olur; VKN, TCKN, takip dosya no ve sıfırla başlayan kodlar metin kalır.

Taranmış (görüntü) PDF'leri okumaz; metni seçilebilen PDF gerekir.

## Kaynak

`kaynak/` klasöründe arayüz (`app.html`), ayrıştırma çekirdeği (`core.js`), paketleme betiği (`build.py`) ve sahte verili örnek PDF üreticisi (`mk3.py`) var. Paketleme için pdfjs-dist 3.11.174 ve xlsx 0.18.5 gerekir.

## Linux betiği (arayüzsüz)

Tarayıcı kullanmadan, doğrudan PDF'ten Excel üretir:

```bash
wget https://github.com/semssaglam-creator/test/raw/HEAD/pdf-tablo-ayiklayici/tablo2excel.py
wget https://github.com/semssaglam-creator/test/raw/HEAD/pdf-tablo-ayiklayici/cevir.sh
chmod +x cevir.sh
./cevir.sh liste.pdf                  # liste.xlsx oluşur
./cevir.sh liste.pdf --sayfalar 1     # yalnızca 1. sayfa
./cevir.sh liste.pdf --parola 1234    # parolalı PDF
```

İlk çalıştırmada `pdfplumber` ve `openpyxl` paketlerini `~/.tablo2excel` klasörüne kurar; sonra internet gerekmez.
