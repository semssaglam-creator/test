# Skill yedekleri

Bu klasör, Claude'un bu depoyla birlikte geliştirilen skill'lerini tutar.
Skill dosyaları uygulamaların çalışması için gerekli değildir; buraya,
oturum kapandığında ya da senkronizasyon sırasında üzerine yazıldığında
kaybolmasın diye konmuştur.

Geri yüklemek için:

    cp -r skills/windows-paketi ~/.claude/skills/
    chmod +x ~/.claude/skills/windows-paketi/arac/*.sh

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
