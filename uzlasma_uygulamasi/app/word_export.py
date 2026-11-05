"""Harici paket olmadan minimal Word (.docx) uretimi.

.docx = icinde XML bulunan bir ZIP paketidir (OOXML). Bu modul, yalnizca
standart kutuphane (zipfile) ile gecerli bir Word belgesi uretir; uzlasma
"bolum notu" ic yazismasi icin kullanilir.
"""
import io
import zipfile


def _esc(s):
    return (str(s if s is not None else "")
            .replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))


_CONTENT_TYPES = (
    '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
    '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
    '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
    '<Default Extension="xml" ContentType="application/xml"/>'
    '<Override PartName="/word/document.xml" '
    'ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>'
    '</Types>'
)

_RELS = (
    '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
    '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
    '<Relationship Id="rId1" '
    'Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" '
    'Target="word/document.xml"/>'
    '</Relationships>'
)

# A4 dikey + 2 cm kenar bosluklari (twip)
_SECTPR = ('<w:sectPr><w:pgSz w:w="11906" w:h="16838"/>'
           '<w:pgMar w:top="1134" w:right="1134" w:bottom="1134" w:left="1134" '
           'w:header="720" w:footer="720" w:gutter="0"/></w:sectPr>')

_KENAR = "".join(
    f'<w:{y} w:val="single" w:sz="4" w:space="0" w:color="000000"/>'
    for y in ("top", "left", "bottom", "right")
)


def _run(metin, bold=False, size=22):
    """size: yarim punto (22 = 11 punto). Metindeki \\n -> satir sonu."""
    rpr = '<w:rPr><w:rFonts w:ascii="Times New Roman" w:hAnsi="Times New Roman"/>'
    if bold:
        rpr += "<w:b/>"
    rpr += f'<w:sz w:val="{size}"/><w:szCs w:val="{size}"/></w:rPr>'
    govde = ""
    for i, parca in enumerate(_esc(metin).split("\n")):
        if i:
            govde += "<w:br/>"
        govde += f'<w:t xml:space="preserve">{parca}</w:t>'
    return f"<w:r>{rpr}{govde}</w:r>"


def _para(metin="", bold=False, hiza=None, size=22):
    if metin == "":
        return "<w:p/>"
    ppr = "<w:pPr>"
    if hiza:
        ppr += f'<w:jc w:val="{hiza}"/>'
    ppr += "</w:pPr>"
    return f"<w:p>{ppr}{_run(metin, bold, size)}</w:p>"


def _hucre(metin, genislik, bold=False, hiza="left", size=22):
    tcpr = (f'<w:tcPr><w:tcW w:w="{genislik}" w:type="dxa"/>'
            '<w:vAlign w:val="center"/></w:tcPr>')
    return f"<w:tc>{tcpr}{_para(metin, bold=bold, hiza=hiza, size=size)}</w:tc>"


def _tablo(basliklar, satir, genislikler):
    toplam = sum(genislikler)
    tbl = ('<w:tbl><w:tblPr>'
           f'<w:tblW w:w="{toplam}" w:type="dxa"/>'
           '<w:tblLayout w:type="fixed"/>'
           '<w:tblBorders>' + _KENAR
           + '<w:insideH w:val="single" w:sz="4" w:space="0" w:color="000000"/>'
             '<w:insideV w:val="single" w:sz="4" w:space="0" w:color="000000"/>'
           '</w:tblBorders></w:tblPr>')
    tbl += "<w:tblGrid>" + "".join(f'<w:gridCol w:w="{g}"/>' for g in genislikler) + "</w:tblGrid>"
    tbl += "<w:tr>" + "".join(
        _hucre(b, g, bold=True, hiza="center", size=20) for b, g in zip(basliklar, genislikler)
    ) + "</w:tr>"
    tbl += "<w:tr>" + "".join(
        _hucre(d, g, hiza="center", size=20) for d, g in zip(satir, genislikler)
    ) + "</w:tr>"
    tbl += "</w:tbl>"
    return tbl


def _paketle(body_xml):
    belge = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
             '<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">'
             f"<w:body>{body_xml}{_SECTPR}</w:body></w:document>")
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("[Content_Types].xml", _CONTENT_TYPES)
        z.writestr("_rels/.rels", _RELS)
        z.writestr("word/document.xml", belge)
    return buf.getvalue()


def bolum_notu_olustur(kurum, veri):
    """Bir tutanak icin 'bölüm notu' Word belgesi (bytes) uretir.

    veri: {vkn_tckn, ad_unvan, tutanak_bilgi, ihbarnameler:[...], davet_tarih}
    """
    g = []
    g.append(_para("T.C.", bold=True, hiza="center"))
    g.append(_para("GELİR İDARESİ BAŞKANLIĞI", bold=True, hiza="center"))
    if kurum.get("defterdarlik"):
        g.append(_para(kurum.get("defterdarlik", ""), bold=True, hiza="center"))
    if kurum.get("vergi_dairesi"):
        g.append(_para("(" + kurum.get("vergi_dairesi", "") + ")", bold=True, hiza="center"))
    g.append(_para())
    g.append(_para("BÖLÜM NOTU", bold=True, hiza="center", size=26))
    g.append(_para())
    g.append(_para(
        "Dairemiz Uzlaşma Komisyonunca tanzim edilen uzlaşma komisyon kararı "
        "yazımız ekinde gönderilmiştir.", hiza="both"))
    g.append(_para())

    basliklar = ["Mükellefin VKN/TCKN", "Adı Soyadı / Ünvanı",
                 "Tutanak Tarihi ve Sayısı", "Uzlaşmaya Konu İhbarnameler",
                 "Davetiye Tebliğ Tarihi"]
    genislikler = [1600, 2100, 1650, 2950, 1300]  # dxa, toplam 9600 (A4'e sigar)
    ihbarnameler = "\n".join(veri.get("ihbarnameler") or []) or "-"
    satir = [
        veri.get("vkn_tckn") or "-",
        veri.get("ad_unvan") or "-",
        veri.get("tutanak_bilgi") or "-",
        ihbarnameler,
        veri.get("davet_tarih") or "-",
    ]
    g.append(_tablo(basliklar, satir, genislikler))
    return _paketle("".join(g))
