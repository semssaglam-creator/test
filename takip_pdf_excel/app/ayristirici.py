"""Takip listesi PDF'ini kayıtlara ve 15 sütuna ayırır.

Tabloda sütun çizgisi yok; metin sütun konumlarına göre yazılmış. Yöntem:
- Her kaydın çapası Vergi Dönemi hücresidir (AA/YYYY-AA/YYYY). Kaydın dikey
  aralığı, kendi çapasından bir sonrakine kadardır.
- Ad/Unvan ve Adres sola hizalı sütunlardır; sol kenarları bütün belgedeki en
  sık x başlangıcından bulunur (kalibrasyon). Çok satırlı hücreler birleşir.
- Dönemin sağındaki 8 değer, tam 8 değeri olan kayıtlardan öğrenilen sütun
  merkezlerine göre yerleşir; boş hücre olsa da değer yanlış sütuna kaymaz.
- Okunamayan değer ASLA sıfır yazılmaz: hücre boş kalır, kayda uyarı düşer.
  Toplam Borç = Aslı + KGZ + Ceza aritmetik denetimi her kayıtta yapılır.
"""
import re
from collections import Counter

from .pdf_kelime import PdfHata, pdf_kelimeleri

RIGHT_COLS = [
    "Ana Vergi Kodu", "Vergi Kodu", "Ana Takip Dosya No", "Takip Dosya No",
    "Vergi Aslı Borcu Toplamı", "KGZ Toplamı", "Ceza Tutarı", "Toplam Borç",
]
COLUMNS = ["Sıra No", "Vergi No", "TC Kimlik No", "Plaka No", "Soyad Ad/Unvanı",
           "Adres", "Vergi Dönemi"] + RIGHT_COLS
AMOUNT_COLS = RIGHT_COLS[4:]

PERIOD_IN = re.compile(r"\d{2}/\d{4}-\d{2}/\d{4}")
PERIOD = re.compile("^" + PERIOD_IN.pattern + "$")
INT = re.compile(r"^\d{1,6}$")
VKN = re.compile(r"^\d{10}$")
TCKN = re.compile(r"^\d{11}$")
PLAKA = re.compile(r"^\d{2}[A-ZÇĞİÖŞÜ]{1,3}\d{2,5}$")
AMOUNT = re.compile(r"^-?\d{1,3}(\.\d{3})*,\d{2}$")
HEADER_WORDS = {
    "sıra", "no", "vergi", "tc", "kimlik", "plaka", "soyad", "ad/unvanı",
    "adres", "dönemi", "ana", "kodu", "(*)", "takip", "dosya", "aslı", "borcu",
    "toplamı", "kgz", "ceza", "tutarı", "toplam", "borç",
}


def kucuk(s):
    """Türkçe küçük harf (Python'un lower()'ı I/İ'yi yanlış çevirir)."""
    return s.replace("I", "ı").replace("İ", "i").lower()


def tutar_oku(s):
    """'1.234,56' -> 1234.56; biçim tutmazsa None (asla 0 değil)."""
    return float(s.replace(".", "").replace(",", ".")) if AMOUNT.match(s) else None


def _is_header_line(words):
    hits = sum(kucuk(w["text"]) in HEADER_WORDS for w in words)
    return hits >= max(2, len(words) * 0.6)


def _lines(words, tol=2.0):
    lines = []
    for w in sorted(words, key=lambda w: (w["top"], w["x0"])):
        if lines and abs(w["top"] - lines[-1][0]["top"]) <= tol:
            lines[-1].append(w)
        else:
            lines.append([w])
    return [sorted(l, key=lambda w: w["x0"]) for l in lines]


def _join(words):
    return " ".join(" ".join(w["text"] for w in l) for l in _lines(words))


def _cut_at_gap(words, max_gap):
    """Satırlar arası boşluk max_gap'i aşınca kes (alt bilgi kayda karışmasın)."""
    out, prev = [], None
    for line in _lines(words):
        if prev is not None and line[0]["top"] - prev > max_gap:
            break
        out.extend(line)
        prev = line[0]["top"]
    return out


def _mode(values, step=2.0):
    if not values:
        return None
    bucket = Counter(round(v / step) for v in values).most_common(1)[0][0]
    return min(v for v in values if round(v / step) == bucket)


def _split_fused(words):
    """Bitişik sütunlar tek kelime gelirse (ör. 'OĞLU11/2021-11/2021') dönemden ayır."""
    out = []
    for w in words:
        m = PERIOD_IN.search(w["text"])
        if not m or (m.start() == 0 and m.end() == len(w["text"])):
            out.append(w)
            continue
        n, width = len(w["text"]), w["x1"] - w["x0"]
        for s, e in ((0, m.start()), (m.start(), m.end()), (m.end(), n)):
            if s < e:
                out.append(dict(w, text=w["text"][s:e],
                                x0=w["x0"] + width * s / n, x1=w["x0"] + width * e / n))
    return out


def _collect_records(sayfalar):
    records = []
    for page_no, _, words in sayfalar:
        words = _split_fused(words)
        anchors = sorted((w for w in words if PERIOD.match(w["text"])), key=lambda w: w["top"])
        if not anchors:
            continue
        h = anchors[0]["bottom"] - anchors[0]["top"]
        eps = h * 0.5

        # Sayfa başında, başlık bloğunun altında kalan satırlar önceki kaydın devamıdır.
        pre = [w for w in words if w["top"] < anchors[0]["top"] - eps]
        header_bottom = max((l[-1]["bottom"] for l in _lines(pre) if _is_header_line(l)), default=None)
        if records and header_bottom is not None:
            cont = [w for w in pre if w["top"] > header_bottom]
            records[-1]["cont"].extend(_cut_at_gap(cont, h * 2.5))

        for i, a in enumerate(anchors):
            top = a["top"] - eps
            bottom = anchors[i + 1]["top"] - eps if i + 1 < len(anchors) else float("inf")
            body = [w for w in words if top <= w["top"] < bottom]
            records.append({"anchor": a, "h": h, "words": _cut_at_gap(body, h * 2.5),
                            "cont": [], "page": page_no})
    return records


def _right_tokens(r):
    return sorted((w for w in r["words"] if w["x0"] > r["anchor"]["x1"]), key=lambda w: w["x0"])


def ayristir(sayfalar):
    """Kelime listesinden kayıtları çıkar.

    Dönüş: [{"degerler": [COLUMNS sırasında], "uyarilar": [str], "sorunlu": [sütun adı]}]
    Tutarlar float, okunamayanlar None.
    """
    records = _collect_records(sayfalar)
    if not records:
        raise PdfHata("PDF'te takip kaydı bulunamadı. Metni seçilebilen bir takip listesi "
                      "PDF'i mi? (Taranmış/görüntü PDF okunamaz.)")

    # Kalibrasyon: ad sütunu sol kenarı (n0) ve adres sütunu sol kenarı (a0)
    name_starts = []
    for r in records:
        a = r["anchor"]
        first = [w for w in r["words"] if abs(w["top"] - a["top"]) <= r["h"] * 0.6 and w["x1"] < a["x0"]]
        text = [w for w in sorted(first, key=lambda w: w["x0"])
                if not (INT.match(w["text"]) or VKN.match(w["text"]) or TCKN.match(w["text"])
                        or PLAKA.match(w["text"]))]
        if text:
            name_starts.append(text[0]["x0"])
        r["first"] = first
    n0 = _mode(name_starts)
    if n0 is None:
        raise PdfHata("Ad/Unvan sütunu tespit edilemedi; PDF biçimi beklenenden farklı.")
    a0 = _mode([w["x0"] for r in records for w in r["words"] + r["cont"]
                if n0 + 15 < w["x0"] and w["x1"] <= r["anchor"]["x0"]])

    # Kalibrasyon: dönemin sağındaki 8 sütunun merkezleri
    full = [t for t in (_right_tokens(r) for r in records) if len(t) == len(RIGHT_COLS)]
    centers = [sum((t[i]["x0"] + t[i]["x1"]) / 2 for t in full) / len(full)
               for i in range(len(RIGHT_COLS))] if full else None

    sonuc = []
    for r in records:
        a = r["anchor"]
        row = dict.fromkeys(COLUMNS, "")
        row["Vergi Dönemi"] = a["text"]
        uyarilar, sorunlu = [], []

        plaka = []
        for w in r["first"]:
            t = w["text"]
            if w["x0"] >= n0 - 2:
                continue
            if row["Sıra No"] == "" and INT.match(t):
                row["Sıra No"] = int(t)
            elif VKN.match(t):
                row["Vergi No"] = t
            elif TCKN.match(t):
                row["TC Kimlik No"] = t
            else:
                plaka.append(w)
        row["Plaka No"] = _join(plaka)

        text = [w for w in r["words"] + r["cont"] if n0 - 2 <= w["x0"] and w["x1"] <= a["x0"] + 1]
        split = a0 - 2 if a0 is not None else float("inf")
        row["Soyad Ad/Unvanı"] = _join([w for w in text if w["x0"] < split])
        row["Adres"] = _join([w for w in text if w["x0"] >= split])

        toks = _right_tokens(r)
        cells = {c: [] for c in RIGHT_COLS}
        if len(toks) == len(RIGHT_COLS) or not centers:
            for c, w in zip(RIGHT_COLS, toks):
                cells[c].append(w)
        else:
            for w in toks:
                cx = (w["x0"] + w["x1"]) / 2
                i = min(range(len(centers)), key=lambda i: abs(centers[i] - cx))
                cells[RIGHT_COLS[i]].append(w)
            uyarilar.append("Sağ tarafta {} değer var (beklenen {}); konuma göre yerleştirildi, "
                            "kontrol edin".format(len(toks), len(RIGHT_COLS)))
        for c in RIGHT_COLS:
            row[c] = " ".join(w["text"] for w in cells[c])

        for c in AMOUNT_COLS:
            ham = row[c]
            row[c] = tutar_oku(ham)
            if row[c] is None:
                sorunlu.append(c)
                uyarilar.append("{}: {}".format(c, "değer yok" if not ham else "sayı okunamadı ({!r})".format(ham)))
        tutarlar = [row[c] for c in AMOUNT_COLS]
        if None not in tutarlar:
            asli, kgz, ceza, top = tutarlar
            if abs(asli + kgz + ceza - top) > 0.005:
                sorunlu.append("Toplam Borç")
                uyarilar.append("Toplam Borç ({:.2f}) ≠ Aslı+KGZ+Ceza ({:.2f})".format(top, asli + kgz + ceza))
        if not row["Vergi No"] and not row["TC Kimlik No"]:
            sorunlu += ["Vergi No", "TC Kimlik No"]
            uyarilar.append("Vergi No / TC Kimlik No bulunamadı")
        for c in ("Sıra No", "Soyad Ad/Unvanı", "Ana Takip Dosya No", "Takip Dosya No"):
            if row[c] == "":
                sorunlu.append(c)
                uyarilar.append("{} boş".format(c))

        sonuc.append({"degerler": [row[c] for c in COLUMNS], "uyarilar": uyarilar,
                      "sorunlu": sorunlu, "sayfa": r["page"]})
    return sonuc


def pdf_ayristir(veri):
    return ayristir(pdf_kelimeleri(veri))
