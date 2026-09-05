#!/usr/bin/env python3
"""Belge hazirlama araci: bolum degistirme ve Windows metin bicimi.

Iki isi var.

1) --bolum: Ortak bir kilavuzun platforma bagli bolumunu degistirir.

   Parca dosyanin ILK satirindaki "## Baslik" hangi bolumse, hedef
   kilavuzdaki ayni baslikli bolum onunla degistirilir. Baslik bulunamazsa
   arac DURUR ve hicbir sey yazmaz.

   Bu inatcilik bilerektir: kilavuz zamanla degisir, baslik yeniden
   adlandirilir ve degistirme sessizce hicbir seye denk gelmez. O zaman
   uretilen pakette Linux anlatimi kalir, kimse fark etmez. Durmak, sessizce
   eskimekten iyidir.

2) --metin: Duz metni Not Defteri'nin dogru actigi bicime cevirir.

   UTF-8 BOM + CRLF. BOM olmadan eski Not Defteri surumleri Turkce
   karakterleri bozar; CRLF olmadan dosyayi tek satir gosterir.

Kullanim:
    python3 belge_hazirla.py --bolum parca.md KILAVUZ.md
    python3 belge_hazirla.py --metin girdi.txt cikti.txt
"""
import io
import re
import sys


def _basligi_al(metin):
    ilk = metin.lstrip().splitlines()[0] if metin.strip() else ""
    eslesme = re.match(r"^(#{1,6})\s+(.*?)\s*$", ilk)
    if not eslesme:
        raise ValueError(
            "parca dosyanin ilk satiri bir markdown basligi olmali "
            "(ornek: '## Kurulum'); bulunan: %r" % ilk[:60])
    return len(eslesme.group(1)), eslesme.group(2)


def bolum_degistir(parca_yolu, hedef_yolu):
    with io.open(parca_yolu, encoding="utf-8") as f:
        parca = f.read()
    with io.open(hedef_yolu, encoding="utf-8") as f:
        hedef = f.read()

    derinlik, baslik = _basligi_al(parca)

    # Ayni derinlikteki basligi bul; bolum, ayni ya da daha ust duzeydeki
    # bir sonraki basliga kadar surer.
    baslik_deseni = re.compile(
        r"^#{%d}\s+%s\s*$" % (derinlik, re.escape(baslik)),
        re.MULTILINE)
    eslesme = baslik_deseni.search(hedef)
    if not eslesme:
        print("hata: '%s' basligi %s icinde bulunamadi.\n"
              "      Kilavuzdaki baslik degismis olabilir; parca dosyanin "
              "ilk satirini\n      guncelleyin. Hicbir sey yazilmadi."
              % (baslik, hedef_yolu), file=sys.stderr)
        return 1

    sonraki = re.compile(r"^#{1,%d}\s+" % derinlik, re.MULTILINE)
    devam = sonraki.search(hedef, eslesme.end())
    bitis = devam.start() if devam else len(hedef)

    yeni_parca = parca.rstrip() + "\n\n"
    yeni = hedef[:eslesme.start()] + yeni_parca + hedef[bitis:]

    if yeni == hedef:
        print("degisiklik yok: '%s' bolumu zaten guncel." % baslik)
        return 0

    with io.open(hedef_yolu, "w", encoding="utf-8") as f:
        f.write(yeni)
    print("'%s' bolumu degistirildi: %s" % (baslik, hedef_yolu))
    return 0


def metin_cevir(girdi_yolu, cikti_yolu):
    with io.open(girdi_yolu, encoding="utf-8") as f:
        metin = f.read()
    # newline="" verilmezse Python kendi cevirisini yapar ve Windows'ta
    # CRLF iki kez uygulanip CRCRLF olur.
    with io.open(cikti_yolu, "w", encoding="utf-8-sig", newline="\r\n") as f:
        f.write(metin)
    print("%s -> %s (UTF-8 BOM + CRLF)" % (girdi_yolu, cikti_yolu))
    return 0


def main(argv):
    if len(argv) != 4 or argv[1] not in ("--bolum", "--metin"):
        print(__doc__.strip())
        return 2
    if argv[1] == "--bolum":
        return bolum_degistir(argv[2], argv[3])
    return metin_cevir(argv[2], argv[3])


if __name__ == "__main__":
    sys.exit(main(sys.argv))
