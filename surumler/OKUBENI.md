# Sürümler

Bu klasör, indirilebilir **hazır paketleri** tutar. Kaynak koddan üretilirler
(`kdv_linux/paketle.sh`, `kdv_windows/paketle.sh`); burada durmalarının tek
sebebi, kalıcı bir indirme bağlantısı vermektir.

**Her paket bir sürüm damgası taşır** (`surum.txt`: tarih + git kısa
kimliği). Uygulama bu damgayı sağ üstte gösterir; indirdiğiniz paketin
gerçekten çalıştığını oradan doğrularsınız. Damganın yanındaki port
numarası 8766 değilse, uygulamanın önceki bir kopyası hâlâ çalışıyor
demektir ve tarayıcıdaki eski adres ESKİ sürümü gösterir.

**Bu paketlerdeki son değişiklikler (2026-10-19):** ibraz etmeme raporu ve
vergi suçları raporu (defter-belge gizleme, VUK 359/a-2); devir düzeltme
raporu; VUK 353/1 belge alma özel usulsüzlüğü; belge basım bilgileri
tablosu; alış ve satış fatura listelerinin ayrılması; ibraz etmemede
matrah ilavesi ve değerlendirmesi; VUK 359 hapis sürelerinin 7394 sayılı
Kanunla değişik hâli.

## Linux

    https://github.com/semssaglam-creator/test/raw/refs/heads/claude/dosya-gorunurlugu-3p8f9d/surumler/KDV_Inceleme_Calismasi_Linux.tar.gz

İndirdikten sonra:

    tar -xzf KDV_Inceleme_Calismasi_Linux.tar.gz
    cd "KDV Inceleme Calismasi"
    ./kur.sh          # masaüstü kısayolu kurar
    # ya da doğrudan: ./calistir.sh

`.tar.gz` kullanılır, `.zip` değil: zip çalıştırma iznini her arşivleyicide
korumaz ve `calistir.sh` çalıştırılamaz halde açılırsa uygulama "hiç
açılmıyor" görünür.

## Windows — güncelleme paketi

Kurulu bir Windows uygulamasının **yalnızca program dosyalarını** yeniler
(`main.py`, `app/`, `web/`). Gömülü Python taşımaz; çalışan bir kurulum
yoksa işe yaramaz, o durumda tam paket gerekir.

    https://github.com/semssaglam-creator/test/raw/refs/heads/claude/dosya-gorunurlugu-3p8f9d/surumler/KDV_Guncelleme_Windows.zip

İndirdikten sonra: zip'e sağ tık > "Tümünü ayıkla", uygulamayı kapat, çıkan
klasörde `guncelle.bat`. Betik kurulu uygulamayı kendisi arar, önce yedek
alır, kopyalar, sonra yeni sürümün gerçekten yerine geçtiğini denetler.
Yedek alamazsa hiçbir dosyaya dokunmaz.

## Güncelleme

Paketleyiciyi çalıştırmak yeter; paketler buraya **kendiliğinden**
kopyalanır:

    cd kdv_linux  && ./paketle.sh
    cd kdv_windows && ./guncelleme_paketle.sh

Eskiden kopyalama elle yapılıyordu ve atlandığında bu klasörde haftalar
öncesinin paketi kalıyor, indiren kullanıcıya eski uygulama gidiyordu.
Paketleyici artık kendisi kopyalıyor; yine de indirdiğiniz paketin
sürüm damgasına bakın.
