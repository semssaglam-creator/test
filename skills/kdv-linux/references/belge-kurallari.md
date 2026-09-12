# Belge kurallari

Tutanak ve rapor ureten kodu degistirirken bilinmesi gerekenler. Bunlar
bicimsel tercih degil; yanlisi belgeyi hukuken hatali yapar.

## Sonucu degistiren ayrimlar

**Kurum / gercek kisi** (`kunye.mukellef_turu`). Kurumda "mukellef kurum"
denir ve Kurumlar Vergisi / Kurum Gecici Vergisi yazilir; gercek kiside
"mukellef" denir ve Gelir Vergisi / Gecici Vergi yazilir. `inceleme_kunyesi`
icindeki `mukellef_sozu`, `gelir_vergisi_adi`, `gecici_vergi_adi` bunu
yonetir — bu adlari elle yazmayin, fonksiyondan alin.

**Bilerek / bilmeden kullanma** (`satici.kullanma`). 306 Sira No'lu VUK Genel
Tebligi'ne dayanir. Bilmeden kullanmada kasit unsuru olusmaz, VUK 359
kapsaminda islem yapilmaz. Bilerek kullanmada vergi sucu raporu duzenlenir ve
suc duyurusunda bulunulur.

**Duzeltmeyle cikarilmis / kayda alinmamis satici**
(`duzeltme_ile_cikarildi`, `kayda_alinmadi`). Faturalarin tamami boyleyse
reddedilecek indirim zaten beyanda degildir: tarh edilecek vergi kalmaz.
`faturalar.duzeltme_kabul_uygun_mu` bunu denetler.

## Duzeltme kabul raporu — belgenin TURU degisir

Faturalarin tamami duzeltmeyle cikarilmis ya da hic kayda alinmamissa tarh
edilecek vergi iki halde de yoktur, ama duzenlenecek belge farklidir:

| Kullanma | Belge | Sonuc |
|---|---|---|
| Bilmeden | **Vergi Teknigi Raporu** | Vergi de ceza da yok |
| Bilerek | **Vergi Inceleme Raporu** | Tarhiyat yok; yarim kat cezanin uc kata tamamlanmasi istenir; vergi sucu raporu |

Baslik ve dosya adi da tura gore degisir (`belge_turu`, `dosya_adi`).

## Cezanin matrahi

Faturalardaki KDV toplami **degildir**. Duzeltme indirimi cikarir, ama
cikarilan indirim once devreden KDV'yi eritir; odenecek vergi ancak devir
tukendikten sonra dogar. Yalnizca devri eriten bir duzeltmede ziya YOKTUR ve
vergi dairesince ceza da kesilmemistir.

`beyannameler.duzeltmeyle_dogan_vergi()` bunu duzeltme zincirini adim adim
gezerek toplar — ilk/son karsilastirmasiyla degil, cunku ayni doneme birden
cok duzeltme verilmisse her adimda dogan vergi ayri ayri tahakkuk eder.

Uc hal ayri cumle gerektirir ve ucu de yazilidir:

- **bilinmiyor** (beyanname yuklenmemis) -> kirmizi yer tutucu
- **ziya yok** (yalnizca devir eridi) -> tamamlanacak ceza yok
- **ziya var** -> tutarlar yazilir

## Verilmis karar: uc kat

Ceza UC KAT olarak kodlanir. Farkli bir durum cikarsa mufettis raporu elle
duzeltir; uygulamaya secim eklenmeyecek. Elle duzeltmeyi gerektiren haller
ekrandaki yardim metninde sayilir:

- **Pismanlikla verilen duzeltme (VUK 371):** ceza hic kesilmez; ayrica VUK
  359'un son fikrasi geregi 359 hukmu uygulanmaz, yani vergi sucu raporu ve
  suc duyurusu da yazilmaz.
- **Izaha davet (VUK 370):** ceza %20.
- **Inceleme BASLADIKTAN SONRA verilen duzeltme:** VUK 344 son fikrasindaki
  %50 uygulanmaz, ceza tam kat.

Bu karari yeniden acmayin; gerekcesi `GELISTIRME_NOTLARI.md` icinde.

## Yazim

**Kirmizi yer tutucu.** Bilinmeyen bir deger icin sayi uydurmayin;
`belge_docx.YER_TUTUCU_RENGI` ile kirmizi bir yer tutucu birakin. Mufettis
kirmiziyi gorup doldurur; sessiz bir sifir fark edilmez.

**Kurum adlarinda kesme isareti kullanilmaz:** "Mudurlugunun", "Mudurlugu'nun"
degil. `turkce.ilgi_kurum` bunu yapar.

**Daire adi** belgede tam yazilir ("Liman Vergi Dairesi Mudurlugu").
`inceleme_kunyesi.daire_adi` kisa girisi genisletir, beyannameden gelen
kod onekini ("033254 - ") kirpar ve `BILINEN_DAIRELER` listesiyle noktali I /
noktasiz I ayrimini duzeltir. Bu listeyi genisletmek tek satirdir; tahmin
yurutmeyin, adin dogru yazimini ekleyin.

**Buyuk harfli metin.** Sistem dokumlerinden ALL CAPS gelir; `turkce.unvan`,
`turkce.adres`, `turkce.kisi_adi` yazim kurallarina cevirir. Belgeye ham
buyuk harf yazmayin.

## Dokunulmayacaklar

- Mukellefin kendi ifadeleri (tutanaga oldugu gibi gecer)
- Muhasebe kaydi verisi
- Mulga TCK atiflari (ornek belgelerde oyle)
