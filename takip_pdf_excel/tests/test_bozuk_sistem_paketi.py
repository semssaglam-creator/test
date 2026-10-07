"""Sistemde bozuk bir 'cryptography' kurulu olsa da uygulama açılmalı."""
import os
import subprocess
import sys
import unittest

KOK = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SAHTE = os.path.join(KOK, "tests", "sahte_bozuk_paket")
PDF = os.path.join(KOK, "tests", "ornekler", "sahte_takip_hucre.pdf")

KOD = """
import sys
sys.path.insert(0, {kok!r} + "/lib")
sys.path.append({kok!r} + "/lib_ek")
sys.path.insert(0, {kok!r})
sys.path.insert(0, {sahte!r})   # bozuk paket, sistemdekinden önce bulunsun
from app.ayristirici import pdf_ayristir
print(len(pdf_ayristir(open({pdf!r}, "rb").read())))
"""


class BozukSistemPaketi(unittest.TestCase):
    def test_bozuk_cryptography_uygulamayi_dusurmez(self):
        r = subprocess.run([sys.executable, "-I", "-c", KOD.format(kok=KOK, sahte=SAHTE, pdf=PDF)],
                           capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, r.stderr[-2000:])
        self.assertEqual(r.stdout.strip(), "32")
        self.assertIn("'cryptography' paketi yüklenemedi", r.stderr)


if __name__ == "__main__":
    unittest.main()
