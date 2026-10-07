"""PDF sayfalarından konumlu kelime listesi çıkarır (gömülü pypdf ile).

Her kelime: {"text", "x0", "x1", "top", "bottom"}; koordinatlar sayfanın sol
üst köşesine göre (top aşağı doğru artar).

pypdf'in "layout" modu iç fonksiyonları kullanılır: her Tj/TJ işlemi için
başlangıç x'i ve fontun gerçek glif genişliklerinden hesaplanan bitiş x'i
verir. Bu yüzden pypdf sürümü sabittir (lib/ altındaki 4.3.1); güncellenirse
tests/ altındaki gerileme testleri çalıştırılmalıdır.
"""
import io

from pypdf import PdfReader
from pypdf.errors import DependencyError, PdfReadError
from pypdf.generic import ContentStream
from pypdf._text_extraction._layout_mode._fixed_width_page import recurs_to_target_op
from pypdf._text_extraction._layout_mode._text_state_manager import TextStateManager


class PdfHata(Exception):
    """Kullanıcıya gösterilecek PDF okuma hatası."""


def _genislik_tamamla(font):
    """pypdf 4.3.1, /Encoding'i olmayan TrueType alt kümelerinde (/Widths var,
    kodlama 'charmap') genişlik tablosunu boş bırakır; o zaman her harf aynı
    genişlikte sayılır ve harf harf yazılmış metin kelimeye birleşemez.
    Tabloyu ToUnicode eşlemesinden kendimiz kuruyoruz."""
    fd = font.font_dictionary
    if font.width_map or "/Widths" not in fd:
        return
    ilk = int(fd.get("/FirstChar", 0))
    for i, w in enumerate(fd["/Widths"]):
        kod = ilk + i
        u = font.char_map.get(chr(kod))
        if u is None and isinstance(font.encoding, str) and kod < 256:
            try:
                u = bytes([kod]).decode(font.encoding)
            except (LookupError, UnicodeDecodeError):
                u = None
        if isinstance(u, str) and u:
            font.width_map[u] = float(w)


def _parcalar(page):
    """Sayfadaki her metin gösterme işlemini (TextStateParams) sırayla döndür."""
    contents = page.get("/Contents")
    if contents is None:
        return []
    fonts = page._layout_mode_fonts()
    for f in fonts.values():
        _genislik_tamamla(f)
    ops = iter(ContentStream(contents.get_object(), page.pdf, "bytes").operations)
    state = TextStateManager()
    tjs = []
    while True:
        try:
            operands, op = next(ops)
        except StopIteration:
            return tjs
        if op in (b"BT", b"q"):
            _, t = recurs_to_target_op(ops, state, b"ET" if op == b"BT" else b"Q", fonts, True)
            tjs.extend(t)
        else:
            state.set_state_param(op, operands)


def _kelimeler(page):
    ust = float(page.mediabox.top)
    parcalar = []
    for tj in _parcalar(page):
        if tj.rotated or not tj.txt.strip():
            continue
        olcek = tj.transform[0]
        h = tj.font_height or tj.font_size
        top = ust - tj.ty - h
        # İşlem içindeki boşluklardan kelimelere böl; her kelimenin x'i fontun
        # genişliklerinden hesaplanır.
        i, txt = 0, tj.txt
        while i < len(txt):
            if txt[i].isspace():
                i += 1
                continue
            j = i
            while j < len(txt) and not txt[j].isspace():
                j += 1
            x0 = tj.tx + tj.word_tx(txt[:i]) * olcek if i else tj.tx
            x1 = tj.tx + tj.word_tx(txt[:j]) * olcek
            parcalar.append({"text": txt[i:j], "x0": x0, "x1": x1,
                             "top": top, "bottom": top + h, "fs": h})
            i = j
    # Harf harf (ya da hece hece) konumlanmış metni birleştir: aynı satırda,
    # aralarında boşluk genişliğinden çok daha dar aralık olan parçalar tek kelimedir.
    parcalar.sort(key=lambda w: (round(w["top"]), w["x0"]))
    sonuc = []
    for w in parcalar:
        s = sonuc[-1] if sonuc else None
        if (s and abs(s["top"] - w["top"]) < 1 and -0.05 * w["fs"] < w["x0"] - s["x1"] < 0.12 * w["fs"]):
            s["text"] += w["text"]
            s["x1"] = w["x1"]
        else:
            sonuc.append(dict(w))
    return sonuc


def pdf_kelimeleri(veri):
    """PDF baytlarından [(sayfa_no, sayfa_yuksekligi, kelimeler), ...] döndür."""
    try:
        reader = PdfReader(io.BytesIO(veri))
        if reader.is_encrypted and not reader.decrypt(""):
            raise PdfHata("PDF parola korumalı; açılamadı.")
        sayfalar = []
        for no, page in enumerate(reader.pages, 1):
            yukseklik = float(page.mediabox.top) - float(page.mediabox.bottom)
            sayfalar.append((no, yukseklik, _kelimeler(page)))
    except PdfHata:
        raise
    except DependencyError:
        raise PdfHata("PDF şifreli (AES) ve bu bilgisayarda şifre çözücü paket yok. "
                      "PDF'i Okular'da açıp 'Farklı Yazdır → PDF'e yazdır' ile şifresiz kopya "
                      "alarak deneyin.")
    except PdfReadError as e:
        raise PdfHata("Dosya okunamadı, geçerli bir PDF değil: {}".format(e))
    except Exception as e:  # şifreleme sağlayıcısı yok vb.
        raise PdfHata("PDF işlenemedi: {}: {}".format(type(e).__name__, e))
    return sayfalar
