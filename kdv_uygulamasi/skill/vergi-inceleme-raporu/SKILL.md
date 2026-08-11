---
name: vergi-inceleme-raporu
description: >
  Türk vergi incelemesi için vergi inceleme raporu ve vergi inceleme tutanağı
  üretir. Sahte belge kullanma, KDV indirim reddi, re'sen tarhiyat ve usul
  incelemelerini kapsar. Kullanıcı vergi incelemesi, vergi raporu, inceleme
  raporu, inceleme tutanağı, VUK 30, resen tarhiyat, vergi ziyaı, KDV indirim
  reddi, sahte belge, naylon fatura, matrah farkı, usul incelemesi, özel
  usulsüzlük, vergi mahremiyeti ifadelerinden herhangi birini kullandığında
  MUTLAKA bu skill'i kullan. Çıktı .docx belgesidir.
---

# Vergi İnceleme Raporu ve Tutanağı

Bu skill'in düzeni, sahada fiilen kullanılan üç belgeden çıkarılmıştır:
bilmeden kullanma raporu, bilerek kullanma raporu ve tek sahteci tutanağı.
Genel bir GİB şablonu değil, gerçek bir denetim biriminin kullandığı biçimdir.

---

## Adım 0 — Hangi belge isteniyor

| İstek | Üretilecek |
|---|---|
| "tutanak", "inceleme tutanağı", "VUK 141" | Vergi inceleme tutanağı |
| "rapor", "inceleme raporu", "sahte belge raporu" | Vergi inceleme raporu |
| İkisi de | Önce tutanak, sonra rapor (rapor tutanağa atıf yapar) |

**Kaç belge:** Tutanak, inceleme dönemi kaç yılı kapsarsa kapsasın **tek**
düzenlenir. Rapor ise **her yıl için ayrı** düzenlenir — 2022 ve 2023
incelendiyse iki ayrı rapor yazılır. Her raporun içinde yalnızca kendi yılının
hesap tabloları, fatura dökümü, satıcıları, iş emri satırları ve düzeltme
beyannameleri yer alır. Ceza katı, vergi suçu raporu / suç duyurusu ve
tarhiyat öncesi uzlaşma kapsamı da o yılın satıcılarına göre kurulur: bir yılın
satıcısı bilmeden, diğerininki bilerek kullanma sayılabilir.

---

## Adım 1 — Sonucu Değiştiren Dört Ayrım

Bunlar sorulmadan rapor yazılmaz. Her biri metnin birçok yerini birden
değiştirir.

### 1. Mükellef türü: kurum mu, gerçek kişi mi

| | Kurum (sermaye şirketi) | Gerçek kişi |
|---|---|---|
| Metinde anılışı | "mükellef kurum" | "mükellef" |
| Dönem | "hesap dönemi" | "takvim yılı" |
| Kazanç vergisi | Kurumlar Vergisi | Gelir Vergisi |
| Geçici vergi | kurum geçici vergisi | geçici vergi |
| Kazanç mevzuatı | KVK 6, KVK 11 | GVK 37, GVK 40, GVK mük. 120 |
| Suç duyurusu kimin hakkında | Kanuni temsilci (adı + T.C. kimlik no) | Mükellefin kendisi |

> Gerçek kişiyi "mükellef kurum" diye anmak yalnızca üslup hatası değildir;
> raporun kazanç vergisi bölümünün de yanlış Kanuna dayandırılmasına yol açar.

### 2. Bilerek mi bilmeden mi kullanma

| | Bilmeden kullanma | Bilerek kullanma |
|---|---|---|
| KDV indirimi | Reddedilir | Reddedilir |
| Vergi ziyaı cezası | **1 kat** (VUK 344/1) | **3 kat** (VUK 344/2, 359 kapsamı) |
| Vergi suçu raporu | Düzenlenmez | Düzenlenir |
| Suç duyurusu | Yok | Cumhuriyet Başsavcılığına |
| Tarhiyat öncesi uzlaşma | Kapsamda | **Kapsam dışı** (VUK Ek 11) |
| Kazanç vergisi | Maliyet kabul edilir, eleştiri yok | Ayrıca değerlendirilir |

Bu ayrım **satıcı bazındadır**. Bir raporda bir satıcı bilerek, diğeri
bilmeden sayılabilir; ceza da buna göre paylaştırılır (bkz. Adım 4).

**Bilerek kullanma kanaatinin dayanağı orandır:** sahte faturalara ait KDV'nin,
aynı dönemde indirim konusu yapılan toplam KDV içindeki payı. Yüksek oran
(örn. %80'in üzeri) bilmediğinin kabulünü güçleştirir. Oranı mutlaka hesapla
ve rapora yaz.

### 3. Faturalar düzeltme beyannamesiyle çıkarılmış mı

Mükellef bir satıcının faturalarını **kendi düzeltme beyannamesiyle**
indirimlerinden çıkardıysa, aynı tutarı bir de raporla tarh etmek **mükerrer
tarhiyattır**.

O satıcının faturaları:
- B bölümünde tablosuyla **gösterilir**,
- hesaplamaya ve tarhiyata **girmez**,
- hem kendi bölümünde hem değerlendirmede **neden dahil edilmediği yazılır**.

### 4. Re'sen takdir nedeni

- **VUK 30/4** — defter ve belgeler ihticaca salih değil (sahte belge
  kullanımında en yaygın)
- **VUK 30/6** — beyanname gerçek durumu yansıtmıyor
- İkisi birlikte de yazılabilir: "30/4. ve 6. maddeleri uyarınca"

Belge içinde **tutarlı** olmalı: bir yerde 30/4, başka yerde 30/4 ve 6
yazılmamalı.

---

## Adım 2 — Toplanacak Bilgiler

Eksikleri tek mesajda sor. Hiçbirini tahmin etme.

**Mükellef:** unvan/ad, VKN, vergi dairesi, adres, faaliyet konusu,
e-Defter/e-Fatura kapsamı, e-Tebligat (VUK 107/A), kanuni temsilci ve T.C.
kimlik no (kurumsa)

**Görevlendirme:** her görevlendirme yazısı için tarih, sayı, dönem ve konu —
birden çoksa raporda "Sıra No | İş Emri Tarihi | İş Emri Sayısı | Dönemi |
Konusu" tablosu, tutanakta ise hepsi tek cümlede sayılır ("… tarih ve … sayılı,
… tarih ve … sayılı görevlendirme yazıları ile"). Ayrıca denetim daire
başkanlığı, incelenen dönem, inceleme konusu. Girilmemiş hücreler `[iş emri
tarihi]` gibi kırmızı yer tutucu olarak bırakılır.

İnceleme dosya no, rapor no, incelemeye başlama tarihi, inceleme türü ve
inceleme gerekçesi belgede geçmez; sorma.

**Satıcı başına:** unvan, VKN, vergi dairesi, VTR tarih ve sayısı, özel
esaslara alınma tarihi, bilerek/bilmeden, düzeltmeyle çıkarılmış mı, fatura
dökümü (tarih, no, malın cinsi, tutar, KDV, toplam, yevmiye tarih/no)

**Beyan verisi:** dönem dönem KDV matrahı, hesaplanan KDV, önceki dönem
devreden, bu dönem indirilecek, indirimler toplamı, ödenecek, sonraki dönem
devreden, iade edilecek

**Usul:** defter tasdik durumu, ibraz, beyanname süresi, usulsüzlük derecesi,
ödemeleri tevsik etmeme (varsa)

**Tutanak için ayrıca:** inceleme yeri (çalışma adresi), ibraz edilen
defterler, gelir/kurumlar vergisi beyan özeti, muhasebe kaydı, sorulan
hususlar ve alınan cevap, RDK'da dinlenme talebi, taslak tutanak talebi,
tarhiyat öncesi uzlaşma talebi, özelge, başkaca itiraz, hazır bulunanlar,
tutanak tarih/yer/sayfa/nüsha

---

## Adım 3 — Belge Düzeni

Cümle kalıpları için `references/sablonlar.md` dosyasını **oku**.
Madde metinleri için `references/kanun-maddeleri.md`.

### Rapor

Belge doğrudan **I- GİRİŞ** ile başlar. Başlık, "taslak" ibaresi ve rapor
no/tarih bloğu **konmaz** — bunlar kapak sayfasında yer alır.

```
I- GİRİŞ
      mükellef tanıtımı · iş emirleri (tablo) · iş emri gerekçeleri
      imzaya davet / gıyabi tutanak notu · kapsam
II- USUL İNCELEMELERİ
      A- Genel Usulsüzlük
      B- Özel Usulsüzlük Cezası (VUK mük. 355) + ceza tablosu
III- HESAP İNCELEMELERİ
      kanuni beyan tablosu · düzeltme beyannameleri · son hal tablosu
      beyan tetkiki bulguları
IV- ELEŞTİRİLEN HUSUSLAR
      A- Re'sen Takdir Nedeni
      B- Re'sen Takdir Verileri     B.1, B.2… (satıcı başına, fatura tablosuyla)
      C- İlgili Mevzuat             + "İndirilecek KDV'den Çıkarılacak Tutar" tablosu
      D- Değerlendirme              1- KDV · 2- Vergi ziyaı cezası · 3- Kazanç vergisi ve kaçakçılık
      Ç- Tarhiyat Öncesi Uzlaşma
V- SONUÇ
      numaralı maddeler · tarhiyat tablosu · "Sonucuna varılmıştır." · imza
```

### Tutanak

Başlık **ortalı**: `VERGİ İNCELEME TUTANAĞI`. Ardından iki giriş paragrafı
(başlıksız), sonra **kalın numaralı maddeler**:

1. Bu tutanaktaki hususların ispatlama vasıtası olduğunun açıklandığı
2. İncelemenin yapıldığı çalışma adresi
3. İbraz edilen defterler (tablo: Yılı · Türü · Tasdik Tarihi ve No · Makam)
4. Gelir/Kurumlar Vergisi beyan özeti (tablo)
5. KDV beyan özeti (tablo)
6. Düzeltme beyannameleri (varsa)
7. **Her sahteci satıcı için ayrı madde**: Ba-Bs tespiti + fatura dökümü,
   ardından muhasebe kaydı paragrafı
8. Sorulan hususlar ve alınan cevap
9. RDK'da dinlenme talebi
10. Taslak tutanak talebi
11. Tarhiyat öncesi uzlaşma
12. Özelge
13. Başkaca itiraz ve mülahaza

Kapanış: "Durumu tespit eden bu tutanak N (yazıyla) sayfada M (yazıyla) örnek
düzenlendi…" + yer, tarih. Sonra 2x3 imza tablosu (inceleme elemanı | boş |
mükellef).

> Koşullu maddeler atlandığında numaralarda boşluk bırakma; sayaçla üret.

---

## Adım 4 — Hesaplar

### Ceza dağılımı (birden çok satıcı varsa)

Bir dönemde reddedilen KDV ile tarh edilen vergi eşit olmayabilir: devir
zinciri reddin bir kısmını soğurabilir, ya da tarhiyatın bir kısmı matrah
ilavesi gibi başka tespitlerden gelebilir.

1. Tarh edilen tutarın sahte belgeye atfedilebilecek kısmını ayır
   (reddedilen KDV'yi aşamaz)
2. Bu kısmı, kategorilerin reddedilen KDV'leri oranında böl
3. Bilerek paya 3 kat, bilmeden paya 1 kat ceza uygula
4. Kalan tutarı "diğer tespitler" olarak ayrı göster

### Özel usulsüzlük (VUK mük. 355 — ödemeleri tevsik etmeme)

- Tevsik haddi: 2017'den itibaren 7.000 TL (459 Sıra No'lu Tebliğ);
  öncesinde 8.000 TL
- Ceza: işlem tutarının (KDV dahil) **%5'i**, yıla ait **alt haddin**
  altına inemez
- Bir takvim yılında kesilecek toplam ceza **üst sınırı** aşamaz
- Alt had ve üst sınır yıl yıl değişir — **kullanıcıya sor, tahmin etme**

### Tarhiyat tablosu

İki satırlı birleşik başlık taşır:

| Dönemi | Ödenecek KDV || Re'sen Tarhı Gereken | İade Edil. KDV || Aranması Ger. | Re'sen Tarhı Ger. Toplam |
|---|---|---|---|---|---|---|---|
| | Olması Gereken | Beyan Edilen | | Olması Gereken | Beyan Edilen | | |

TOPLAM satırı **gösterilen satırların** toplamı olmalı; farkı sıfır olan
dönemler tabloya alınmadığından genel toplam kullanılırsa tablo kendi içinde
tutmaz.

---

## Adım 5 — Biçim

- A4, kenar boşlukları 2,5 cm
- Times New Roman **12 punto**, 1,5 satır aralığı
- Bölüm başlıkları **sola dayalı**, kalın (belge başlığı hariç — o ortalı)
- Çok sütunlu tutar tabloları **9 punto** — 12 puntoda başlıklar bölünür,
  rakamlar taşar
- Tablo başlık satırı gri zeminli, TOPLAM satırı kalın ve açık gri
- Beyan tablosu 8 sütun: Dönemi *(yıl başlıkta)* · KDV Matrahı · Hspl. KDV ·
  Önc. Dön. Dev. KDV · Bu Dön. İndl. KDV · İndirimler Toplamı · Ödenecek KDV ·
  Son. Dön. Dev. KDV. İade varsa 9. sütun eklenir. Satırlarda yalnızca ay adı.
- Fatura tablosu 8 sütun: Fatura Tarih · Fatura No · Malın Cinsi · Tutar ·
  KDV · Toplam Tutar · Yevmiye Tarih · Yevmiye No
- Kurum adlarında kesme işareti **kullanılmaz**: "Müdürlüğünün", "Başkanlığının"

### Elle doldurulacak yerler kırmızı

Bilinmeyen her alan köşeli parantez içinde ve **kırmızı** (C00000) yazılır:
`[VTR no]`, `[yevmiye tarihi]`, `[Sonuç bölümüne eklenecek tespit notu]`.
Sessizce boş bırakma — okuyan nereyi dolduracağını görmeli.

---

## Adım 6 — Yapılmayacaklar

- **Mükellef ifadelerine dokunma.** Tırnak içindeki beyan, imla hataları
  dahil aynen korunur. Tutanağa geçmiş söz düzeltilmez.
- **Muhasebe verisini uydurma.** Yevmiye tarihi bilinmiyorsa kırmızı yer
  tutucu bırak; tahmin etme.
- **Mülga Kanuna atıf yapma.** Kasıt tartışmasında 765 sayılı TCK'nın
  cürüm-kabahat ayrımı değil, **5237 sayılı TCK md. 21** yazılır. 306 Sıra
  No'lu Tebliğ'e atıf korunur.
- **Tutarları tekrar hesaplatmadan yazma.** Sütun toplamlarını ve devir
  zincirini denetle.

---

## Adım 7 — Vergi Mahremiyeti

Belgeler paylaşılacaksa (örnek, eğitim, dış inceleme) mükellef ve üçüncü kişi
kimlikleri anonimleştirilir:

| Gerçek | Raporda |
|---|---|
| Mükellef | Mükellef-A |
| Satıcı firmalar | Satıcı-A, Satıcı-B… |
| VKN | 1111111111 |
| Adres | [İnceleme Adresi] |

Kurum içi kullanımda gerçek kimlikler yazılır. Hangisinin isteneceğini
**kullanıcıya sor**.

---

## Referans Dosyalar

- `references/sablonlar.md` — bölüm bölüm cümle kalıpları; **rapor
  yazılmadan önce oku**
- `references/kanun-maddeleri.md` — VUK, KDVK, GVK, KVK, TCK madde metinleri
