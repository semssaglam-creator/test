"""Paket denetimleri gerçekten koruyor mu? Her birini BİLEREK BOZUP sınar.

Geçen bir denetimin gerçekten koruduğunu ancak bozarak anlarsınız.
"""
import os
import shutil
import sys
import tempfile
import unittest

KOK = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, KOK)

from paketle import denetle  # noqa: E402


class PaketDenetimi(unittest.TestCase):
    def setUp(self):
        self.gecici = tempfile.mkdtemp()
        self.kok = os.path.join(self.gecici, "uyg")
        shutil.copytree(KOK, self.kok, ignore=shutil.ignore_patterns("dist", "__pycache__", ".git"))

    def tearDown(self):
        shutil.rmtree(self.gecici)

    def yol(self, *p):
        return os.path.join(self.kok, *p)

    def bozuk(self, parca):
        hatalar = denetle(self.kok)
        self.assertTrue(any(parca in h for h in hatalar), "Denetim atmadı; hatalar: {}".format(hatalar))

    def test_saglam_kopya_temiz(self):
        self.assertEqual(denetle(self.kok), [])

    def test_zorunlu_dosya_eksik(self):
        os.remove(self.yol("web", "index.html"))
        self.bozuk("Zorunlu dosya yok: web/index.html")

    def test_calistirma_izni_yok(self):
        os.chmod(self.yol("calistir.sh"), 0o644)
        self.bozuk("Çalıştırılabilir değil")

    def test_crlf(self):
        with open(self.yol("calistir.sh"), "rb") as f:
            veri = f.read()
        with open(self.yol("calistir.sh"), "wb") as f:
            f.write(veri.replace(b"\n", b"\r\n"))
        self.bozuk("CRLF")

    def test_kabuk_sozdizimi(self):
        with open(self.yol("calistir.sh"), "a") as f:
            f.write("\nif then fi\n")
        self.bozuk("sözdizimi")

    def test_kullanici_verisi_sizar(self):
        open(self.yol("cikti.xlsx"), "wb").close()
        open(self.yol("acilis_kaydi.txt"), "w").close()
        hatalar = denetle(self.kok)
        self.assertTrue(any("cikti.xlsx" in h for h in hatalar))
        # acilis_kaydi.txt paket dışında tutulur (sızmaz), hata da üretmez
        self.assertFalse(any("acilis_kaydi" in h for h in hatalar))

    def test_ornek_pdf_sizar(self):
        shutil.copy(self.yol("tests", "ornekler", "sahte_takip_hucre.pdf"), self.yol("ornek.pdf"))
        self.bozuk("ornek.pdf")

    def test_derlenmis_dosya(self):
        open(self.yol("lib", "hizli.so"), "wb").close()
        self.bozuk("Derlenmiş")

    def test_gelistirme_notu_sizar(self):
        os.makedirs(self.yol("belgeler"))
        open(self.yol("belgeler", "GELISTIRME_NOTLARI_ESKI.md"), "w").close()
        self.bozuk("Geliştirme dosyası")

    def test_internetten_kaynak(self):
        with open(self.yol("web", "index.html"), "a", encoding="utf-8") as f:
            f.write('<script src="https://cdn.example.com/x.js"></script>')
        self.bozuk("internetten")

    def test_lib_ek_basa_eklenmis(self):
        p = self.yol("main.py")
        with open(p, encoding="utf-8") as f:
            m = f.read()
        bozuk = m.replace('sys.path.append(os.path.join(BASE_DIR, "lib_ek"))',
                          'sys.path.insert(0, os.path.join(BASE_DIR, "lib_ek"))')
        self.assertNotEqual(m, bozuk, "Bozma işe yaramadı: main.py'deki satır değişmiş")
        with open(p, "w", encoding="utf-8") as f:
            f.write(bozuk)
        self.bozuk("lib_ek")


if __name__ == "__main__":
    unittest.main()
