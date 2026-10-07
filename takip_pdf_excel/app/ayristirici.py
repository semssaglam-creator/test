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


def _sira_kolonu(pages):
    """Sıra No sütununun yatay aralığı: satırın en solundaki tamsayı + hemen sağında
    VKN/TCKN olan satırlardan. Aralık (en küçük x0, en büyük x1) kullanılır, en sık
    değer değil: sütun ORTALI ya da sola yaslıysa 1-2 haneli numaralar 4 haneli
    çoğunluktan kayık durur ve 1.1'de 1-99 arası kayıtlar hiç tanınmadı."""
    x0s, x1s = [], []
    for _, words in pages:
        for line in _lines(words):
            if len(line) > 1 and INT.match(line[0]["text"]) and \
                    (VKN.match(line[1]["text"]) or TCKN.match(line[1]["text"])):
                x0s.append(line[0]["x0"])
                x1s.append(line[0]["x1"])
    if not x0s:
        return None, None
    return min(x0s), max(x1s)


def _collect_records(sayfalar):
    """Kayıtları topla. Çapa: Sıra No hücresi (her kaydın ilk satırında, en solda).

    Bir kayıt sayfa sonunda bölünebilir: sonraki sayfada başlığın altında, ilk
    Sıra No'dan önce kalan satırlar önceki kaydın devamıdır. Devam parçasında Sıra
    No tekrar yazılmışsa o parça ayrı kayıt olarak toplanır, ayristir() aynı Sıra
    No'lu ardışık kayıtları birleştirir.
    """
    pages = [(no, _split_fused(words)) for no, _, words in sayfalar]
    sx0, sx1 = _sira_kolonu(pages)
    if sx0 is None:
        return []
    records = []
    for page_no, words in pages:
        anchors = []
        for line in _lines(words):
            w = line[0]
            if INT.match(w["text"]) and len(line) > 1 and sx0 - 2 <= w["x0"] and w["x1"] <= sx1 + 2:
                anchors.append(w)
        h = (anchors[0]["bottom"] - anchors[0]["top"]) if anchors else \
            (records[-1]["h"] if records else 8.0)
        eps = h * 0.5
        ilk_top = anchors[0]["top"] - eps if anchors else float("inf")

        # Sayfa başı: başlık bloğunun altında, ilk Sıra No'dan önceki satırlar.
        pre = [w for w in words if w["top"] < ilk_top]
        header_bottom = max((l[-1]["bottom"] for l in _lines(pre) if _is_header_line(l)), default=None)
        if records and pre:
            cont = [w for w in pre if header_bottom is None or w["top"] > header_bottom]
            if header_bottom is None:   # başlık yoksa yalnızca ilk kayda bitişik satırlar
                cont = list(reversed(_cut_at_gap_up(cont, ilk_top, h * 2.5)))
            for w in _cut_at_gap(cont, h * 2.5):
                records[-1]["cont"].append(dict(w, page=page_no))

        for i, a in enumerate(anchors):
            top = a["top"] - eps
            bottom = anchors[i + 1]["top"] - eps if i + 1 < len(anchors) else float("inf")
            body = [w for w in words if top <= w["top"] < bottom]
            records.append({"anchor": a, "h": h, "words": _cut_at_gap(body, h * 2.5),
                            "cont": [], "page": page_no})
    return records


def _cut_at_gap_up(words, alt, max_gap):
    """alt sınırdan yukarı doğru, aralarında max_gap'ten büyük boşluk olmayan satırlar."""
    out, prev = [], alt
    for line in reversed(_lines(words)):
        if prev - line[-1]["bottom"] > max_gap:
            break
        out.extend(line)
        prev = line[0]["top"]
    return out


def _metin(ana, devam):
    """Ana parça + sonraki sayfadaki devam parçası; satır sırası korunur."""
    return " ".join(t for t in (_join(ana), _join(devam)) if t)


def _bolumle(r, n0, a0, p0, p1):
    """Kaydın kelimelerini sütun bölgelerine ayır."""
    split = a0 - 2 if a0 is not None else float("inf")
    sonuc = {"ad": ([], []), "adres": ([], []), "donem": [], "sag": []}
    for parca, kume in ((0, r["words"]), (1, r["cont"])):
        for w in kume:
            if w is r["anchor"]:
                continue
            if PERIOD.match(w["text"]) and w["x0"] > n0:
                sonuc["donem"].append(w)
            elif w["x0"] > p1 - 1:
                sonuc["sag"].append(w)
            elif n0 - 2 <= w["x0"] and w["x1"] <= p0 + 1:
                sonuc["ad" if w["x0"] < split else "adres"][parca].append(w)
    sonuc["sag"].sort(key=lambda w: w["x0"])
    return sonuc


def _birlestir(a, b):
    """Aynı Sıra No'lu iki parçayı tek kayıtta birleştir (b, a'nın devamı)."""
    for i, c in enumerate(COLUMNS):
        va, vb = a["satir"][c], b["satir"][c]
        if va in ("", None):
            a["satir"][c] = vb
        elif vb in ("", None) or va == vb:
            continue
        elif c in ("Soyad Ad/Unvanı", "Adres"):
            if vb not in va:
                a["satir"][c] = va + " " + vb
        else:
            a["uyarilar"].append("Sayfa bölünmesinde {} iki farklı değer: {!r} / {!r}".format(c, va, vb))
            a["sorunlu"].append(c)
    a["uyarilar"] += [u for u in b["uyarilar"] if u.startswith("Sayfa bölünmesinde")]


def ayristir(sayfalar):
    """Kelime listesinden kayıtları çıkar.

    Dönüş: [{"degerler": [COLUMNS sırasında], "uyarilar": [str], "sorunlu": [sütun adı]}]
    Tutarlar float, okunamayanlar None.
    """
    records = _collect_records(sayfalar)
    if not records:
        raise PdfHata("PDF'te takip kaydı bulunamadı. Metni seçilebilen bir takip listesi "
                      "PDF'i mi? (Taranmış/görüntü PDF okunamaz.)")

    # Kalibrasyon: dönem sütunu (p0-p1), ad sütunu sol kenarı (n0), adres sol kenarı (a0)
    donemler = [w for r in records for w in r["words"] + r["cont"] if PERIOD.match(w["text"])]
    if not donemler:
        raise PdfHata("Vergi Dönemi sütunu bulunamadı; PDF biçimi beklenenden farklı.")
    p0 = _mode([w["x0"] for w in donemler])
    p1 = max(w["x1"] for w in donemler if abs(w["x0"] - p0) <= 3)

    name_starts = []
    for r in records:
        a = r["anchor"]
        first = sorted((w for w in r["words"] if abs(w["top"] - a["top"]) <= r["h"] * 0.6
                        and w["x1"] < p0 and w is not a), key=lambda w: w["x0"])
        text = [w for w in first if not (INT.match(w["text"]) or VKN.match(w["text"])
                                         or TCKN.match(w["text"]) or PLAKA.match(w["text"]))]
        if text:
            name_starts.append(text[0]["x0"])
        r["first"] = first
    n0 = _mode(name_starts)
    if n0 is None:
        raise PdfHata("Ad/Unvan sütunu tespit edilemedi; PDF biçimi beklenenden farklı.")
    a0 = _mode([w["x0"] for r in records for w in r["words"] + r["cont"]
                if n0 + 15 < w["x0"] and w["x1"] <= p0 + 1])

    bolumler = [_bolumle(r, n0, a0, p0, p1) for r in records]
    full = [b["sag"] for b in bolumler if len(b["sag"]) == len(RIGHT_COLS)]
    centers = [sum((t[i]["x0"] + t[i]["x1"]) / 2 for t in full) / len(full)
               for i in range(len(RIGHT_COLS))] if full else None

    parcalar = []
    for r, b in zip(records, bolumler):
        row = dict.fromkeys(COLUMNS, "")
        uyarilar = []
        row["Sıra No"] = int(r["anchor"]["text"])
        plaka = []
        for w in r["first"]:
            t = w["text"]
            if w["x0"] >= n0 - 2:
                continue
            if VKN.match(t):
                row["Vergi No"] = t
            elif TCKN.match(t):
                row["TC Kimlik No"] = t
            else:
                plaka.append(w)
        row["Plaka No"] = _join(plaka)
        row["Soyad Ad/Unvanı"] = _metin(*b["ad"])
        row["Adres"] = _metin(*b["adres"])
        if b["donem"]:
            row["Vergi Dönemi"] = " ".join(w["text"] for w in b["donem"])

        toks = b["sag"]
        cells = {c: [] for c in RIGHT_COLS}
        cok_degerli = []
        if len(toks) == len(RIGHT_COLS) or not centers:
            for c, w in zip(RIGHT_COLS, toks):
                cells[c].append(w)
        else:
            for w in toks:
                cx = (w["x0"] + w["x1"]) / 2
                i = min(range(len(centers)), key=lambda i: abs(centers[i] - cx))
                cells[RIGHT_COLS[i]].append(w)
        for c in RIGHT_COLS:
            row[c] = " ".join(w["text"] for w in cells[c])
            if len(cells[c]) > 1:
                cok_degerli.append(c)
                uyarilar.append("{}: birden çok değer ({}); iki kayıt karışmış olabilir, PDF ile "
                                "karşılaştırın".format(c, row[c]))
        parcalar.append({"satir": row, "uyarilar": uyarilar, "sorunlu": cok_degerli,
                         "sayfa": r["page"], "sag_sayisi": len(toks)})

    # Sayfa bölünmesinde Sıra No tekrar yazılmışsa parçaları birleştir.
    kayitlar = []
    for p in parcalar:
        if kayitlar and kayitlar[-1]["satir"]["Sıra No"] == p["satir"]["Sıra No"]:
            _birlestir(kayitlar[-1], p)
            kayitlar[-1]["sag_sayisi"] += p["sag_sayisi"]
        else:
            kayitlar.append(p)

    sonuc = []
    onceki = None
    for k in kayitlar:
        row, uyarilar, sorunlu = k["satir"], k["uyarilar"], k["sorunlu"]
        if k["sag_sayisi"] != len(RIGHT_COLS):
            uyarilar.append("Sağ tarafta {} değer var (beklenen {}); konuma göre yerleştirildi, "
                            "kontrol edin".format(k["sag_sayisi"], len(RIGHT_COLS)))
        if onceki is not None and row["Sıra No"] != onceki + 1:
            uyarilar.append("Sıra No {} → {}: arada kayıt eksik ya da fazla olabilir".format(onceki, row["Sıra No"]))
            sorunlu.append("Sıra No")
        onceki = row["Sıra No"]

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
        for c in ("Soyad Ad/Unvanı", "Vergi Dönemi", "Ana Takip Dosya No", "Takip Dosya No"):
            if row[c] == "":
                sorunlu.append(c)
                uyarilar.append("{} boş".format(c))

        sonuc.append({"degerler": [row[c] for c in COLUMNS], "uyarilar": uyarilar,
                      "sorunlu": sorunlu, "sayfa": k["sayfa"]})
    return sonuc


def pdf_ayristir(veri):
    return ayristir(pdf_kelimeleri(veri))
