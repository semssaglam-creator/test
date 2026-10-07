"""Gerileme testleri (yalnızca standart kütüphane): python3 -m unittest discover -s tests"""
import io
import json
import os
import sys
import unittest
import warnings

KOK = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(KOK, "lib"))
sys.path.append(os.path.join(KOK, "lib_ek"))
sys.path.insert(0, KOK)
warnings.simplefilter("ignore")

from openpyxl import load_workbook  # noqa: E402

from app.ayristirici import COLUMNS, pdf_ayristir  # noqa: E402
from app.excel import excel_olustur  # noqa: E402
from app.pdf_kelime import PdfHata  # noqa: E402

ORNEK = os.path.join(KOK, "tests", "ornekler")
BICIMLER = ("hucre", "tek_bt", "harf", "bolunmus", "tekrarli")


def oku(bicim):
    with open(os.path.join(ORNEK, "sahte_takip_{}.pdf".format(bicim)), "rb") as f:
        return pdf_ayristir(f.read())


class Ayristirma(unittest.TestCase):
    def test_beklenen_ciktiyla_birebir(self):
        with open(os.path.join(ORNEK, "beklenen.json"), encoding="utf-8") as f:
            beklenen = json.load(f)
        for b in BICIMLER:
            with self.subTest(bicim=b):
                # "sayfa" bölünme biçimine göre değişir; değer ve uyarılar birebir aynı olmalı
                self.assertEqual([(k["degerler"], k["uyarilar"], k["sorunlu"]) for k in oku(b)],
                                 [(k["degerler"], k["uyarilar"], k["sorunlu"]) for k in beklenen])

    def test_bos_tutar_sifir_yazilmaz(self):
        k = {r["degerler"][0]: r for r in oku("hucre")}
        kgz = COLUMNS.index("KGZ Toplamı")
        self.assertIsNone(k[20]["degerler"][kgz])
        self.assertIn("KGZ Toplamı", k[20]["sorunlu"])
        self.assertEqual(k[19]["degerler"][kgz], 0.0)

    def test_aritmetik_denetim(self):
        k = {r["degerler"][0]: r for r in oku("hucre")}
        self.assertIn("Toplam Borç", k[21]["sorunlu"])
        self.assertTrue(any("≠" in u for u in k[21]["uyarilar"]))

    def test_sayfa_gecisi_ve_alanlar(self):
        k = oku("hucre")
        self.assertEqual([r["degerler"][0] for r in k], list(range(1, 71)))
        self.assertGreater(k[-1]["sayfa"], 1)
        r7 = {r["degerler"][0]: r for r in k}[7]["degerler"]
        self.assertEqual(r7[COLUMNS.index("TC Kimlik No")], "12345678901")
        r8 = {r["degerler"][0]: r for r in k}[8]["degerler"]
        self.assertEqual(r8[COLUMNS.index("Plaka No")], "34ABC123")
        for r in k:  # alt bilgi kayda karışmamalı
            self.assertNotIn("Kodlar", " ".join(str(v) for v in r["degerler"]))

    def test_sayfa_bolunmesi_gercekten_var(self):
        """Örnekte bölünen kayıt yoksa yukarıdaki birebir test bölünmeyi korumaz."""
        with open(os.path.join(ORNEK, "bolunen_kayitlar.json"), encoding="utf-8") as f:
            bolunen = json.load(f)
        for b in ("bolunmus", "tekrarli"):
            with self.subTest(bicim=b):
                self.assertGreaterEqual(len(bolunen[b]), 2)

    def test_uzun_liste_1den_1100e(self):
        """Ortalı Sıra No sütununda 1-4 haneli numaraların hepsi tanınmalı."""
        k = oku("uzun")
        self.assertEqual([r["degerler"][0] for r in k], list(range(1, 1101)))
        beklenen = {r["degerler"][0]: r for r in oku("hucre")}
        for r in k[:70]:   # ilk 70 kayıt kısa listeyle aynı veri
            self.assertEqual(r["degerler"], beklenen[r["degerler"][0]]["degerler"])
        # yalnızca örneğe bilerek konan iki hatalı kayıt uyarı vermeli
        self.assertEqual([r["degerler"][0] for r in k if r["uyarilar"]], [20, 21])

    def test_ayni_sira_no_birlesir(self):
        k = oku("tekrarli")
        sira = [r["degerler"][0] for r in k]
        self.assertEqual(sira, sorted(set(sira)))

    def test_pdf_olmayan_dosya(self):
        with self.assertRaises(PdfHata):
            pdf_ayristir(b"bu bir pdf degil")


class Excel(unittest.TestCase):
    def test_excel_icerigi(self):
        kayitlar = oku("hucre")
        for r in kayitlar:
            r["dosya"] = "sahte.pdf"
        ws = load_workbook(io.BytesIO(excel_olustur(kayitlar))).active
        self.assertEqual([c.value for c in ws[1]][:15], COLUMNS)
        self.assertEqual(ws.max_row, len(kayitlar) + 2)          # başlık + kayıtlar + TOPLAM
        self.assertEqual(ws.cell(2, 2).value, "1111111110")      # VKN metin, baştaki sıfırlar korunur
        satir20 = 1 + [r["degerler"][0] for r in kayitlar].index(20) + 1
        self.assertIsNone(ws.cell(satir20, COLUMNS.index("KGZ Toplamı") + 1).value)
        self.assertTrue(ws.cell(satir20, 16).value)              # Kontrol sütununda uyarı
        self.assertTrue(str(ws.cell(ws.max_row, 15).value).startswith("=SUM("))


if __name__ == "__main__":
    unittest.main()
