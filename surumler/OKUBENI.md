# Sürümler

Bu klasör, indirilebilir **hazır paketleri** tutar. Kaynak koddan üretilirler
(`kdv_linux/paketle.sh`, `kdv_windows/paketle.sh`); burada durmalarının tek
sebebi, kalıcı bir indirme bağlantısı vermektir.

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

Paketleri yenilerken önce üretin, sonra buraya kopyalayın:

    cd kdv_linux && ./paketle.sh
    cp KDV_Inceleme_Calismasi_Linux.tar.gz ../surumler/

    cd kdv_windows && ./guncelleme_paketle.sh
    cp KDV_Guncelleme_Windows.zip ../surumler/
