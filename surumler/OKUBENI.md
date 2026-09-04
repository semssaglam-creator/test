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

## Güncelleme

Paketi yenilerken önce üretin, sonra buraya kopyalayın:

    cd kdv_linux && ./paketle.sh
    cp KDV_Inceleme_Calismasi_Linux.tar.gz ../surumler/
