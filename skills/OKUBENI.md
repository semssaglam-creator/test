# Skill yedekleri

Bu klasör, Claude'un bu depoyla birlikte geliştirilen skill'lerini tutar.
Skill dosyaları uygulamaların çalışması için gerekli değildir; buraya,
oturum kapandığında ya da senkronizasyon sırasında üzerine yazıldığında
kaybolmasın diye konmuştur.

Geri yüklemek için:

    cp -r skills/windows-paketi ~/.claude/skills/
    cp -r skills/kdv-linux      ~/.claude/skills/
    chmod +x ~/.claude/skills/windows-paketi/arac/*.sh

## kdv-linux

KDV İnceleme Çalışması uygulamasını devralacak ajan için. Ağacı, değişmezleri
ve sahada pahalıya öğrenilmiş tuzakları taşır; amacı devralanın bunları
yeniden keşfetmek zorunda kalmaması.

- `SKILL.md` — değişmezler (iki ayrı ağaç + `esitle.sh`, yalnızca stdlib,
  sunucuda durum yok, paketleyicilerin denetleyici olması), uygulamayı
  çalıştırma, belge üreten kodu tarayıcısız deneme tarifi, beyanname
  okuyucusunun kırılganlığı, belgelerdeki hukuki ayrımlar
- `references/mimari.md` — ağaç, modül haritası, veri akışı, `calisma`
  sözlüğünün biçimi (anahtar adları dahil)
- `references/tuzaklar.md` — on gerçek arıza: sessiz sıfır, sağa yaslı
  değerler, devam satırının nerede bittiği, port hatası, proxy tuzağı,
  boşluklu yol, UTF-8 BOM, dosya kilidi, `.tar.gz` zorunluluğu, ve
  "geçen bir test gerçekten koruyor mu"
- `references/belge-kurallari.md` — sonucu değiştiren ayrımlar, düzeltme
  kabul raporunun iki dalı, cezanın matrahı, verilmiş kararlar, yazım

## windows-paketi

Python uygulamasını kurulum gerektirmeyen bir Windows paketine çevirir.

- `SKILL.md` — sekiz adımlı yöntem (uygunluk, iskelet, kod uyarlama,
  belgeler, üretim, duman testi, gerçek Windows testi)
- `references/windows-tuzaklari.md` — altı tuzak ve hazır düzeltme kodu:
  `localhost` adresi (proxy), `::1` çift dinleme, `allow_reuse_address`,
  Chrome önceliği, açık dosya kilidi, `.bat` içinde tırnaksız yol.
  Başında "Sahadan" bölümü var: gerçek bir kurumsal Windows makinesinden
  gelen tanı raporunun hangi tuzakları doğruladığı
- `arac/uyarla.sh` — iskeleti bir projeye kurar
- `arac/png2ico.py`, `arac/belge_hazirla.py`, `arac/python_indir.sh`
- `sablon/` — `.bat` başlatıcılar, `app/tani.py`, `paketle.sh`

Not: `vergi-inceleme-raporu` skill'inin yedeği ayrı yerdedir:
`kdv_uygulamasi/skill/`.
