#!/usr/bin/env python3
"""Maskelenmis bir dokumu ayristiriciya vererek okumayi dener.

PDF'in kendisi olmadan bicim uzerinde calisabilmek icin: dokum, _parcalar()
ile ayni bicimde (sayfa, x, y, metin) listesi uretir ve ayristiricinin geri
kalani oldugu gibi calisir.

    python3 gelistirme/dokum_test.py gelistirme/ornek_dokumler/*.txt
"""
import os
import sys

KOK = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(KOK, "linux", "kdv_uygulamasi"))

from app import pdf_beyanname as pb          # noqa: E402


def dokumu_oku(yol):
    parcalar = []
    with open(yol, encoding="utf-8") as f:
        for satir in f:
            if satir.startswith("#") or not satir.strip():
                continue
            alanlar = satir.rstrip("\n").split("\t")
            if len(alanlar) != 4:
                continue
            s, x, y, metin = alanlar
            parcalar.append((int(s), float(x), float(y), metin))
    return parcalar


def dene(yol):
    parcalar = dokumu_oku(yol)
    print("=" * 70)
    print(os.path.basename(yol), "-", len(parcalar), "parca")
    print("=" * 70)

    kunye = pb._kunye(parcalar)
    print("KUNYE:")
    for k in ("yil", "ay", "vkn", "unvan", "vergi_dairesi", "onay_zamani",
              "duzeltme_nedeni"):
        print("   %-16s %r" % (k, kunye[k]))

    degerler, tanimsiz = pb._alanlari_topla(parcalar)
    print("\nOKUNAN ALANLAR (%d):" % len(degerler))
    for k in sorted(degerler):
        print("   %-28s %s" % (k, degerler[k]))

    degerler = pb._turet(dict(degerler))
    print("\nTURETILEN SONRASI (%d):" % len(degerler))
    for k in sorted(degerler):
        print("   %-28s %s" % (k, degerler[k]))

    nedenler = pb._indirim_nedenleri(parcalar)
    print("\nINDIRIM NEDENLERI (%d):" % len(nedenler))
    for n in nedenler:
        print("   %r" % n)

    uyarilar = pb._denetle(degerler)
    print("\nUYARILAR (%d):" % len(uyarilar))
    for u in uyarilar:
        print("   - " + u)

    print("\nTANIMSIZ METINLER (%d):" % len(tanimsiz))
    for t in tanimsiz:
        print("   " + t)

    # Ucdan uca: beyanname_oku'nun kendisi (donem denetimi, tur, ek alanlar)
    gercek = pb._parcalar
    pb._parcalar = lambda _yol: parcalar
    try:
        kayit = pb.beyanname_oku("dokum", dosya_adi=os.path.basename(yol))
        print("\nBEYANNAME_OKU: %s/%s  tur=%s  onay_ts=%s  ek=%s"
              % (kayit["yil"], kayit["ay"], kayit["tur"], kayit["onay_ts"], kayit["ek"]))
    except pb.PdfHata as exc:
        print("\nBEYANNAME_OKU HATA: %s" % exc)
    finally:
        pb._parcalar = gercek


if __name__ == "__main__":
    for yol in sys.argv[1:]:
        dene(yol)
