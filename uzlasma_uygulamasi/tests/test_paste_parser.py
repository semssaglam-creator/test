"""paste_parser regresyon testleri (stdlib unittest; pip gerekmez).

Calistirma:  python3 -m unittest tests.test_paste_parser   (proje kokunden)
"""
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.paste_parser import dilekce_ayristir, ceza_satirlari_ayikla


def _satir_sayisi(sonuc):
    return sum(len(ih["ceza_satirlari"]) for ih in sonuc["ihbarnameler"])


class FisNoBuyukKucukHarf(unittest.TestCase):
    """Fis no'da 'Ev'den sonraki harf buyuk ya da kucuk olabilir.

    Gercek dilekce ornegi: kucuk harfli fiş no (2026090113Eva0000004) ceza
    satirlarinin hic okunmamasina ve 'kaydedilecek satir yok' hatasina yol
    aciyordu.
    """

    ORNEK_KUCUK_HARF = (
        "İhbarname Fiş Numarası Düzenleme ve Tanzim Tarihi İhbarname Tebliğ Tarihi\n"
        "2026090113Eva0000004 202609111106 20260906\n"
        "Ceza Satırları\n"
        "İhbarname Fiş Numarası Vergi Türü Ceza Kodu Ceza Nedeni Ceza Miktarı\n"
        "2026090113Eva0000004 3074 213 Sayılı VUK 353/2 Maddesi Gereğince 17000.0\n"
        "2026090113Eva0000004 3074 213 Sayılı VUK 353/2 Maddesi Gereğince 17000.0\n"
        "2026090113Eva0000004 3074 213 Sayılı VUK 353/2 Maddesi Gereğince 17000.0\n"
        "2026090113Eva0000004 3074 213 Sayılı VUK 353/2 Maddesi Gereğince 17000.0\n"
    )

    def test_kucuk_harf_fis_no_okunur(self):
        sonuc = dilekce_ayristir(self.ORNEK_KUCUK_HARF)
        self.assertEqual(len(sonuc["ihbarnameler"]), 1)
        self.assertEqual(_satir_sayisi(sonuc), 4)

    def test_kucuk_harf_tutarlar_dogru(self):
        satirlar = ceza_satirlari_ayikla(self.ORNEK_KUCUK_HARF)
        self.assertEqual([s["ceza_kodu"] for s in satirlar], ["3074"] * 4)
        self.assertEqual([s["miktar"] for s in satirlar], [17000.0] * 4)

    def test_buyuk_harf_hala_okunur(self):
        # Eski (buyuk harfli) bicim bozulmamali
        metin = (
            "İhbarname Fiş Numarası Düzenleme ve Tanzim Tarihi İhbarname Tebliğ Tarihi\n"
            "2026041113EvU0000001 202604111036 20260415\n"
            "Ceza Satırları\n"
            "2026041113EvU0000001 0015 3080 213 sayılı VUK 341. Madde Gereğince 2965.46\n"
        )
        satirlar = ceza_satirlari_ayikla(metin)
        self.assertEqual(len(satirlar), 1)
        self.assertEqual(satirlar[0]["vergi_turu_kod"], "0015")
        self.assertEqual(satirlar[0]["ceza_kodu"], "3080")
        self.assertEqual(satirlar[0]["miktar"], 2965.46)


class VergiTuruBos(unittest.TestCase):
    """Vergi turu kolonu bos olan ceza satiri da okunmali (yalnizca ceza kodu)."""

    def test_bos_vergi_turu(self):
        metin = (
            "Ceza Satırları\n"
            "2026090113Eva0000004 3074 213 Sayılı VUK 353/2 Maddesi Gereğince 17000.0\n"
        )
        satirlar = ceza_satirlari_ayikla(metin)
        self.assertEqual(len(satirlar), 1)
        self.assertEqual(satirlar[0]["vergi_turu_kod"], "")
        self.assertEqual(satirlar[0]["ceza_kodu"], "3074")
        self.assertEqual(satirlar[0]["miktar"], 17000.0)


if __name__ == "__main__":
    unittest.main()
