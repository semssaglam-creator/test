"""Basit ODS (OpenDocument Spreadsheet) ureticisi.

Yalnizca standart kutuphane kullanir: ODS dosyasi, icinde content.xml
bulunan bir ZIP arsividir. Tek sayfalik duz tablo dokumleri icin yeterlidir.
"""
import io
import zipfile
from xml.sax.saxutils import escape

_MIMETYPE = "application/vnd.oasis.opendocument.spreadsheet"

_MANIFEST = """<?xml version="1.0" encoding="UTF-8"?>
<manifest:manifest xmlns:manifest="urn:oasis:names:tc:opendocument:xmlns:manifest:1.0" manifest:version="1.2">
 <manifest:file-entry manifest:full-path="/" manifest:media-type="application/vnd.oasis.opendocument.spreadsheet"/>
 <manifest:file-entry manifest:full-path="content.xml" manifest:media-type="text/xml"/>
</manifest:manifest>
"""

_GOVDE = """<?xml version="1.0" encoding="UTF-8"?>
<office:document-content
 xmlns:office="urn:oasis:names:tc:opendocument:xmlns:office:1.0"
 xmlns:table="urn:oasis:names:tc:opendocument:xmlns:table:1.0"
 xmlns:text="urn:oasis:names:tc:opendocument:xmlns:text:1.0"
 xmlns:style="urn:oasis:names:tc:opendocument:xmlns:style:1.0"
 xmlns:fo="urn:oasis:names:tc:opendocument:xmlns:xsl-fo-compatible:1.0"
 office:version="1.2">
 <office:automatic-styles>
  <style:style style:name="baslik" style:family="table-cell">
   <style:table-cell-properties fo:background-color="#dddddd"/>
   <style:text-properties fo:font-weight="bold"/>
  </style:style>
 </office:automatic-styles>
 <office:body><office:spreadsheet>
 <table:table table:name="{sayfa_adi}">
{satirlar}
 </table:table>
 </office:spreadsheet></office:body>
</office:document-content>
"""


def _hucre(deger, stil=""):
    stil_attr = f' table:style-name="{stil}"' if stil else ""
    if isinstance(deger, (int, float)) and not isinstance(deger, bool):
        return (f'<table:table-cell office:value-type="float" office:value="{deger}"{stil_attr}>'
                f"<text:p>{deger}</text:p></table:table-cell>")
    metin = escape("" if deger is None else str(deger))
    return f'<table:table-cell office:value-type="string"{stil_attr}><text:p>{metin}</text:p></table:table-cell>'


def ods_olustur(basliklar, satirlar, sayfa_adi="Dokum"):
    """Baslik listesi + satir listelerinden ODS dosya icerigi (bytes) uretir."""
    parcalar = []
    parcalar.append("<table:table-row>"
                    + "".join(_hucre(b, "baslik") for b in basliklar)
                    + "</table:table-row>")
    for satir in satirlar:
        parcalar.append("<table:table-row>"
                        + "".join(_hucre(h) for h in satir)
                        + "</table:table-row>")

    icerik = _GOVDE.format(sayfa_adi=escape(sayfa_adi), satirlar="\n".join(parcalar))

    tampon = io.BytesIO()
    with zipfile.ZipFile(tampon, "w", zipfile.ZIP_DEFLATED) as z:
        # mimetype girdisi sikistirilmadan ve ilk sirada yazilmalidir
        z.writestr(zipfile.ZipInfo("mimetype"), _MIMETYPE, zipfile.ZIP_STORED)
        z.writestr("META-INF/manifest.xml", _MANIFEST)
        z.writestr("content.xml", icerik)
    return tampon.getvalue()
