"""Sahte verili takip listesi PDF'leri üretir (yalnızca geliştirme; reportlab gerekir).

Gerçek mükellef verisi KULLANMAYIN: depo herkese açık.
Düzen, kullanıcının gönderdiği ekran görüntüsündeki takip listesini taklit eder:
çizgisiz sütunlar, ortalanmış çok satırlı başlıklar, sağa yaslı tutarlar,
alt satıra taşan unvan/adres, sayfa sonunda tekrar eden başlık.

Üç üretim biçimi (PDF üreticileri metni farklı yazar):
  hucre  : her hücre satırı ayrı BT/Tj
  tek_bt : bütün sayfa tek BT bloğu içinde Tm ile konumlanmış
  harf   : unvan ve adres harf harf konumlanmış (harf aralığı ayarlı üreticiler)
  bolunmus: sayılar dikeyde ortalı; kayıtlar sayfa sonunda İKİ SAYFAYA bölünür
  tekrarli: bolunmus + devam parçasında Sıra No ve Vergi No tekrar yazılır

Kullanım: python3 tests/ornek_pdf_uret.py
"""
import os

from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas

BURADA = os.path.dirname(os.path.abspath(__file__))
pdfmetrics.registerFont(TTFont("D", "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"))
W, H = 1000, 595
FS, LH = 6.5, 7.6
# (sol x, genişlik, hizalama)
COLS = [(20, 22, "r"), (44, 48, "l"), (94, 52, "l"), (148, 36, "l"), (186, 92, "l"), (280, 118, "l"),
        (400, 58, "l"), (460, 22, "c"), (484, 22, "c"), (508, 100, "l"), (612, 100, "l"),
        (716, 50, "r"), (772, 36, "r"), (812, 36, "r"), (852, 50, "r")]
HEADS = [["Sıra", "No"], ["Vergi No"], ["TC Kimlik", "No"], ["Plaka", "No"], ["Soyad Ad/Unvanı"],
         ["Adres"], ["Vergi", "Dönemi"], ["Ana", "Vergi", "Kodu (*)"], ["Vergi", "Kodu", "(*)"],
         ["Ana Takip Dosya No"], ["Takip Dosya No"], ["Vergi Aslı", "Borcu", "Toplamı"],
         ["KGZ", "Toplamı"], ["Ceza", "Tutarı"], ["Toplam", "Borç"]]

ADRES_A = ["ÖRNEK MAH. 1001 SK. DENEME", "SİTESİ Kapı No:5 Daire", "No:7 KURGU İLÇE ÖRNEKİL"]
ADRES_B = ["DENEME CAD. TEST APT", "Kapı No:12 B Daire No:3", "MERKEZ ÖRNEKİL"]
ADRES_C = ["CUMHURİYET CAD. No:8", "ÖRNEKİL"]


def kayitlar():
    r = [("1", "1111111110", "", "", ["ÖRNEK BİLİŞİM", "İTHALAT İHRACAT", "SANAYİ VE TİCARET", "LİMİTED ŞİRKETİ"],
          ADRES_B, "07/2026-07/2026", "0015", "1048", "2026090900Euj0000001", "2026090900Eux0000001",
          "791,00", "0,00", "0,00", "791,00")]
    for i in range(2, 71):
        asli, ceza, top = ("64,10", "0,00", "64,10") if i % 3 else ("0,00", "125,00", "125,00")
        if i == 14:
            asli, top = "1.714,29", "1.714,29"
        kgz = "0,00"
        if i == 20:
            kgz = ""            # boş hücre: sıfır yazılmamalı, uyarı çıkmalı
        if i == 21:
            top = "99,99"       # aritmetik tutmuyor: uyarı çıkmalı
        r.append((str(i), "2222222220", "12345678901" if i == 7 else "", "34ABC123" if i == 8 else "",
                  (["UZUN UNVANLI ÖRNEK", "TEKSTİL GIDA İNŞAAT", "SANAYİ VE TİCARET", "ANONİM ŞİRKETİ"]
                   if i % 7 == 0 else ["DENEME KİŞİ", "ÖRNEKOĞLU"] if i % 2 else ["TEST İSİM SOYİSİM"]),
                  ADRES_C if i % 3 == 0 else ADRES_A if i % 2 else ADRES_B, "{:02d}/2021-{:02d}/2021".format(i % 12 + 1, i % 12 + 1),
                  "0033" if i % 4 == 0 else "0015", "1047" if i % 5 == 0 else "1048",
                  "2026090900Euj0000002", "2026090900Eux00000{:02d}".format(i),
                  asli, kgz, ceza, top))
    return r


def uret(yol, bicim):
    c = canvas.Canvas(yol, pagesize=(W, H))

    def yaz(x, y, s, al="l", harf=False):
        c.setFont("D", FS)
        w = pdfmetrics.stringWidth(s, "D", FS)
        x = {"l": x, "r": x - w, "c": x - w / 2}[al]
        if harf:
            for ch in s:
                c.drawString(x, y, ch)
                x += pdfmetrics.stringWidth(ch, "D", FS)
        elif bicim == "tek_bt":
            to = c.beginText()
            to.setFont("D", FS)
            to.setTextOrigin(x, y)
            to.textOut(s)
            c.drawText(to)
        else:
            c.drawString(x, y, s)

    def baslik():
        c.setFont("D", 9)
        c.drawString(300, H - 25, "ÖRNEK VERGİ DAİRESİ TAKİP LİSTESİ")
        c.setFont("D", FS)
        for (x, w, _), satirlar in zip(COLS, HEADS):
            for j, t in enumerate(satirlar):
                c.drawCentredString(x + w / 2, H - 50 - (j - len(satirlar) + 3) * 7.5, t)
        return H - 75

    def satir_ogeleri(r, n):
        """(satır kaydırması, x, metin, hizalama, harf_harf) listesi."""
        ogeler = []
        degerler = list(r[:4]) + [None, None] + list(r[6:])
        for k, ((x, w, al), v) in enumerate(zip(COLS, degerler)):
            if k in (4, 5):
                for j, t in enumerate(r[k]):
                    ogeler.append((j, x, t, "l", bicim == "harf"))
            elif v:
                # bolunmus: dönem ve sağdaki sayılar dikeyde ORTALI (satır bölününce
                # sıra/ad bir sayfada, dönem/tutarlar sonraki sayfada kalabilir)
                kay = (n - 1) / 2 if (bicim in ("bolunmus", "tekrarli") and k >= 6) else 0
                ogeler.append((kay, {"l": x, "r": x + w, "c": x + w / 2}[al], v, al, False))
        return ogeler

    bolunen = []
    y = baslik()
    for r in kayitlar():
        n = max(len(r[4]), len(r[5]), 1)
        sigan = int((y - 40) // LH) + 1      # bu sayfaya sığan satır sayısı
        if n > sigan and (bicim not in ("bolunmus", "tekrarli") or sigan < 1):
            c.setFont("D", 7)
            c.drawString(20, 20, "(*) Kodlar için bkz. açıklama")
            c.showPage()
            y, sigan = baslik(), n
        c.setFont("D", FS)
        ogeler = satir_ogeleri(r, n)
        for kay, x, t, al, harf in ogeler:
            if kay < sigan:
                yaz(x, y - kay * LH, t, al, harf)
        if n > sigan:                         # satır sayfa sonunda bölünüyor (alt çizgi yok)
            bolunen.append(int(r[0]))
            c.setFont("D", 7)
            c.drawString(20, 20, "(*) Kodlar için bkz. açıklama")
            c.showPage()
            y = baslik()
            c.setFont("D", FS)
            if bicim == "tekrarli":           # devam parçasında Sıra No ve VKN tekrar yazılır
                for kay, x, t, al, harf in ogeler[:2]:
                    yaz(x, y, t, al, harf)
            for kay, x, t, al, harf in ogeler:
                if kay >= sigan:
                    yaz(x, y - (kay - sigan) * LH, t, al, harf)
            y -= (n - sigan) * LH + 4
        else:
            y -= n * LH + 4
        c.setLineWidth(0.3)
        c.line(20, y + LH - 2, 905, y + LH - 2)
    c.save()
    return bolunen


if __name__ == "__main__":
    import json
    os.makedirs(os.path.join(BURADA, "ornekler"), exist_ok=True)
    bolunenler = {}
    for b in ("hucre", "tek_bt", "harf", "bolunmus", "tekrarli"):
        yol = os.path.join(BURADA, "ornekler", "sahte_takip_{}.pdf".format(b))
        bolunenler[b] = uret(yol, b)
        print(yol, "bölünen kayıtlar:", bolunenler[b])
    with open(os.path.join(BURADA, "ornekler", "bolunen_kayitlar.json"), "w") as f:
        json.dump(bolunenler, f)
