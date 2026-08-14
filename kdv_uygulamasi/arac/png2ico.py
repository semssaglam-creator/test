#!/usr/bin/env python3
"""PNG dosyasini Windows .ico dosyasina cevirir. Yalnizca standart kutuphane.

Pillow kullanilmaz: bu yontemin tamami "derlenmis bagimlilik yok" ilkesine
dayanir, ikon uretmek icin ona istisna acmak tutarsiz olur.

Vista'dan beri .ico dosyalari PNG verisini oldugu gibi tasiyabiliyor; bu
yuzden goruntuyu yeniden kodlamaya gerek yok, PNG baytlarinin onune bir dizin
basligi eklemek yetiyor. Olceklendirme yapilmaz (bunun icin gercek bir goruntu
kutuphanesi gerekirdi), o yuzden kaynak PNG 256x256 olmalidir; Windows onu
gerektiginde kendisi kucultur.

Kullanim:
    python3 png2ico.py ikon.png ikon.ico
"""
import struct
import sys


def png_boyutu(veri):
    """PNG basligindan (genislik, yukseklik) okur."""
    if veri[:8] != b"\x89PNG\r\n\x1a\n":
        raise ValueError("PNG dosyasi degil (imza tutmuyor)")
    # 8 bayt imza, 4 bayt uzunluk, 4 bayt "IHDR", sonra genislik ve yukseklik
    if veri[12:16] != b"IHDR":
        raise ValueError("PNG bozuk: IHDR bolumu bulunamadi")
    genislik, yukseklik = struct.unpack(">II", veri[16:24])
    return genislik, yukseklik


def ico_yap(png_verisi):
    genislik, yukseklik = png_boyutu(png_verisi)
    if genislik != yukseklik:
        print("uyari: ikon kare degil (%dx%d); Windows bozuk gosterebilir."
              % (genislik, yukseklik), file=sys.stderr)
    if genislik > 256 or yukseklik > 256:
        raise ValueError(
            "ikon en fazla 256x256 olabilir (%dx%d verildi). Kaynak gorseli "
            "kucultun." % (genislik, yukseklik))
    if genislik < 32:
        print("uyari: %dx%d cok kucuk; masaustunde bulanik gorunur."
              % (genislik, yukseklik), file=sys.stderr)

    # ICO dizininde 256, sifir bayt ile gosterilir (alan tek bayttir).
    b_gen = 0 if genislik == 256 else genislik
    b_yuk = 0 if yukseklik == 256 else yukseklik

    basliklar = struct.pack("<HHH", 0, 1, 1)          # rezerve, tur=ikon, adet
    dizin = struct.pack(
        "<BBBBHHII",
        b_gen, b_yuk,
        0,          # palet rengi yok
        0,          # rezerve
        1,          # renk duzlemi
        32,         # piksel basina bit
        len(png_verisi),
        6 + 16,     # veri, baslik + dizin girisinden hemen sonra baslar
    )
    return basliklar + dizin + png_verisi


def main(argv):
    if len(argv) != 3:
        print(__doc__.strip())
        return 2
    kaynak, hedef = argv[1], argv[2]
    with open(kaynak, "rb") as f:
        png = f.read()
    try:
        ico = ico_yap(png)
    except ValueError as hata:
        print("hata: %s" % hata, file=sys.stderr)
        return 1
    with open(hedef, "wb") as f:
        f.write(ico)
    genislik, yukseklik = png_boyutu(png)
    print("%s -> %s (%dx%d, %d bayt)"
          % (kaynak, hedef, genislik, yukseklik, len(ico)))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
