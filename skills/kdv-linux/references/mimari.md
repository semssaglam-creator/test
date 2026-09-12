# Mimari

## Agac

```
kdv_linux/                 Linux surumu (gelistirme burada yapilir)
  main.py                  acilis: port secer, sunucuyu kurar, tarayiciyi acar
  app/                     butun mantik
  web/index.html           tek sayfalik arayuz (~4300 satir, tek dosya)
  lib/                     vendor: openpyxl, pypdf, et_xmlfile
  lib_ek/                  vendor: typing_extensions (Python 3.11 oncesi pypdf icin)
  testler/                 beyanname okuyucusu gerileme kumesi (pakete girmez)
  ciktilar/ veritabani/ yedekler/     kullanici verisi (pakete girmez)
  calistir.sh kur.sh kaldir.sh
  paketle.sh
  GELISTIRME_NOTLARI.md    projenin hafizasi
kdv_windows/               Windows surumu; app/tani.py fazladan
esitle.sh                  ortak kodu linux -> windows tasir
surumler/                  indirilebilir hazir paketler
```

## Moduller

Satir sayilari buyuklugu gosterir; bir ise girmeden once ilgili modulun
ust aciklamasini okuyun, hepsinde niye oyle yazildigi anlatilir.

| Modul | Isi |
|---|---|
| `web_server.py` | JSON API + statik dosya. Butun uclar `Istekci` sinifinda. |
| `hesap.py` | KDV beyan zinciri: devir, indirim, odenecek, tarhiyat, ceza. |
| `satirlar.py` | Beyan satirlarinin tanimi. Yeni satir eklemek buradan baslar. |
| `faturalar.py` | Fatura listesi modeli, satici ozeti, sahteci secimi, oranlar. |
| `beyannameler.py` | Beyanname surumlerini donemlere ayirir, duzeltmeleri karsilastirir. |
| `pdf_beyanname.py` | KDV beyannamesi PDF'ini okur (iki cikti bicimi). |
| `vergi_beyannamesi.py` | Yillik Gelir / Kurumlar beyannamesinden ozet okur. |
| `fatura_oku.py` | Fatura listesi dosyalarini okur; tarihleri ISO'ya cevirir. |
| `paste_parser.py` | Sistemden yapistirilan beyan bloklarini ayristirir. |
| `inceleme_kunyesi.py` | Kunye alanlarinin tanimi + belge metni yardimcilari. |
| `tutanak.py` | Tutanak taslagi. |
| `sahte_belge_raporu.py` | Tarhiyatli sahte belge kullanma raporu. |
| `duzeltme_kabul_raporu.py` | Tarhiyatsiz rapor (VTR / VIR ayrimi). |
| `belge_docx.py` | Word uretimi; `Belge` sinifi, kirmizi yer tutucu. |
| `excel_export.py` | Excel calisma kitabi cikti. |
| `mevzuat.py` | Belgelerde gecen kanun metinleri. |
| `turkce.py` | Turkce yazim: buyuk/kucuk, unvan, ilgi eki, adres. |
| `db.py` | SQLite: calisma kaydet / ac / yedekle. |
| `rapor_metni.py` | Ekranda gosterilen ozet metinler. |

## Veri akisi

```
fatura listesi (xlsx/csv)  ─┐
beyanname PDF'leri         ─┼─> tarayicidaki "calisma" sozlugu ─> /api/... ─> hesap
elle yapistirilan beyan    ─┘                                                  │
                                                                    tutanak / rapor / excel
```

Sunucu durum tutmaz; her istek `calisma`yi bastan alir.

## `calisma` sozlugu

Belge ureten uclari elle denerken kuracaginiz yapi:

```python
calisma = {
  # Belge basliklari BURADAN okunur (web_server._inceleme_bilgisi):
  # ad_unvan, vkn_tckn, vergi_dairesi, adres. Anahtar adlarina dikkat —
  # "unvan" degil "ad_unvan"; yanlis yazarsaniz belgede
  # "(adsız Mükellef)" ve "[Vergi dairesi]" cikar, hata vermez.
  "mukellef": {"ad_unvan": "ÖRNEK LTD ŞTİ", "vkn_tckn": "1234567890",
               "vergi_dairesi": "LIMAN VD", "adres": ...},
  # Kunye, belgenin geri kalanini besler (inceleme_kunyesi.BOLUMLER).
  "kunye": {"mukellef_turu": "Kurum (sermaye şirketi)",
            "daire_adi": ..., "inceleme_konusu": ..., "is_emirleri": ...},
  "yillar": [{"yil": 2026,
              "beyan": {kod: [12 deger]},      # kodlar: satirlar.VERI_KODLARI
              "ay_sayisi": 12, "elestiri": {}}],
  "faturalar": [{"duzenleyen_vkn": ..., "alici_vkn": ...,
                 "tarih": "2026-04-15",       # ISO olmali
                 "matrah": ..., "kdv": ..., "toplam": ..., "dahil": True}],
  "saticilar": {"9999999999": {"unvan": ..., "kullanma": "Bilmeden kullanma",
                               "duzeltme_ile_cikarildi": "Evet",
                               "vtr_no": ..., "vtr_tarihi": ..., "is_emri": "Var"}},
  "beyannameler": [...],   # pdf_beyanname.beyanname_oku ciktilari
}
```

Dikkat: `faturalar` icindeki VKN alanlari `duzenleyen_vkn` / `alici_vkn`'dir;
`satici_vkn` bunlardan `faturalar.normalize()` tarafindan TURETILIR. Dogrudan
`satici_vkn` yazarsaniz normalize onu bosa cikarir ve satici bilgileri
eslesmez.

## Sunucu

Yalnizca loopback dinler: once `::1`, sonra `127.0.0.1`. Kullaniciya gosterilen
adres her zaman `localhost` olmali — sebebi `tuzaklar.md` icinde. Port 8766'dan
baslayarak bos port aranir.
