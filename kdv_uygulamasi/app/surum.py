"""Uygulama surum damgasi.

Neden var: uygulama bilgisayara kurulunca masaustu kisayoluna kurulum
anindaki klasor yolu yazilir (kur.sh -> Exec=...). Yeni bir surum baska bir
klasore acilirsa kisayol eski kopyayi baslatmaya devam eder; guncelleme
yapildigi halde hicbir sey degismemis gibi gorunur.

Bu yuzden hem arayuzun basliginda hem tani raporunda surum damgasi ve
uygulamanin CALISTIGI KLASOR gosterilir. Boylece hangi kopyanin acik oldugu
bir bakista anlasilir.

Yeni bir paket cikarilirken SURUM guncellenir.
"""
import os

SURUM = "2026.08.04"
SURUM_ADI = "Beyanname sürümleri"

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def surum_bilgisi():
    return {
        "surum": SURUM,
        "surum_adi": SURUM_ADI,
        "klasor": BASE_DIR,
    }
