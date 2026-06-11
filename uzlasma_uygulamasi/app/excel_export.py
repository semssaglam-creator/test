"""Uzlasma tutanagi Excel ciktilarini uretir (3 sablon).

Sablonlar, GIB Dijital Vergi Dairesi tarafindan uretilen ornek tutanak
dosyalarinin (UZLASMA TUTANAGI / UZLASMA KOMISYON KARAR TUTANAGI) yapisina
gore hazirlanmistir.
"""
import os
import sys

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LIB_DIR = os.path.join(BASE_DIR, "lib")
if LIB_DIR not in sys.path:
    sys.path.insert(0, LIB_DIR)

from openpyxl import Workbook
from openpyxl.styles import Alignment, Border, Font, Side
from openpyxl.utils import get_column_letter

from .sayi_yaziya import tutar_yaziya

COL_WIDTHS = [23.71, 20.71, 15.71, 20.71, 15.71, 23.71]

FONT_NORMAL = Font(name="Times New Roman", size=11)
FONT_BOLD = Font(name="Times New Roman", size=11, bold=True)
FONT_TITLE = Font(name="Times New Roman", size=12, bold=True)

THIN = Side(style="thin")
BORDER_ALL = Border(left=THIN, right=THIN, top=THIN, bottom=THIN)

WRAP_LEFT = Alignment(horizontal="left", vertical="center", wrap_text=True)
CENTER = Alignment(horizontal="center", vertical="center", wrap_text=True)
CENTER_TITLE = Alignment(horizontal="center", vertical="center")


def _kur_kolon_genislikleri(ws):
    for i, genislik in enumerate(COL_WIDTHS, start=1):
        ws.column_dimensions[get_column_letter(i)].width = genislik


def _baslik_blogu(ws, kurum, tutanak_basligi):
    """1-7. satirlar: kurum bilgileri ve tutanak basligi (A1:F7 birlesik)."""
    satirlar = [
        "T.C.",
        "GELİR İDARESİ BAŞKANLIĞI",
        kurum.get("defterdarlik", ""),
        f"({kurum.get('vergi_dairesi', '')})",
        "",
        "",
        tutanak_basligi,
    ]
    for i, deger in enumerate(satirlar, start=1):
        ws.merge_cells(start_row=i, start_column=1, end_row=i, end_column=6)
        c = ws.cell(row=i, column=1, value=deger)
        c.alignment = CENTER_TITLE
        c.font = FONT_TITLE if i == 7 else FONT_BOLD
    return 8  # sonraki bos satir


def _bilgi_satiri(ws, row, etiket, deger):
    ws.merge_cells(start_row=row, start_column=1, end_row=row, end_column=2)
    ws.merge_cells(start_row=row, start_column=3, end_row=row, end_column=6)
    c1 = ws.cell(row=row, column=1, value=etiket)
    c1.font = FONT_BOLD
    c1.alignment = WRAP_LEFT
    c2 = ws.cell(row=row, column=3, value=deger)
    c2.font = FONT_NORMAL
    c2.alignment = WRAP_LEFT
    return row + 1


def _ust_bilgi_blogu(ws, start_row, kurum, tutanak_no, tutanak_tarihi_metni, mukellef):
    row = start_row
    row = _bilgi_satiri(ws, row, "Tutanağın Tarihi / Davetiye T.Tarihi", tutanak_tarihi_metni)
    row = _bilgi_satiri(ws, row, "Tutanağın Sayısı", tutanak_no)
    row = _bilgi_satiri(ws, row, "Mükellefin Adı Soyadı / Ünvanı", mukellef.get("ad_unvan", ""))
    row = _bilgi_satiri(ws, row, "Mükellefin Adresi", mukellef.get("adres", ""))
    row = _bilgi_satiri(ws, row, "Bağlı Bulunduğu Vergi Dairesi", kurum.get("vergi_dairesi", ""))
    row = _bilgi_satiri(ws, row, "Vergi Kimlik Numarası", mukellef.get("vkn_tckn", ""))
    return row


def _paragraf(ws, row, metin, yukseklik=110):
    ws.merge_cells(start_row=row, start_column=1, end_row=row, end_column=6)
    c = ws.cell(row=row, column=1, value=metin)
    c.alignment = WRAP_LEFT
    c.font = FONT_NORMAL
    ws.row_dimensions[row].height = yukseklik
    return row + 1


def _hucre(ws, row, col, deger, font=None, align=None, border=True, num_format=None):
    c = ws.cell(row=row, column=col, value=deger)
    c.font = font or FONT_NORMAL
    c.alignment = align or CENTER
    if border:
        c.border = BORDER_ALL
    if num_format:
        c.number_format = num_format
    return c


def _vergi_ceza_turu(kalem):
    vt = (kalem.get("vergi_turu_kod") or "").strip()
    ck = (kalem.get("ceza_kodu") or "").strip()
    if vt and ck:
        return f"{vt}/{ck}"
    return vt or ck


def _imza_bloklari_4lu(ws, row, imzalayanlar, mukellef_adi):
    """Baskan | Uye | Uye | Mukellef seklinde 4 imza blogu."""
    aralik = [(1, 1), (2, 3), (4, 5), (6, 6)]
    unvanlar = ["Başkan", "Üye", "Üye", "Mükellef"]
    isimler = []
    for u in unvanlar[:3]:
        uygun = next((k["ad_soyad"] for k in imzalayanlar if (k.get("unvan") or "").strip() == u
                       and k["ad_soyad"] not in isimler), None)
        if uygun is None:
            uygun = next((k["ad_soyad"] for k in imzalayanlar if k["ad_soyad"] not in isimler), "")
        isimler.append(uygun)
    isimler.append(mukellef_adi)

    for (c1, c2), isim in zip(aralik, isimler):
        if c1 != c2:
            ws.merge_cells(start_row=row, start_column=c1, end_row=row, end_column=c2)
        cell = ws.cell(row=row, column=c1, value=isim)
        cell.alignment = CENTER
        cell.font = FONT_NORMAL

    for (c1, c2), unvan in zip(aralik, unvanlar):
        if c1 != c2:
            ws.merge_cells(start_row=row + 1, start_column=c1, end_row=row + 1, end_column=c2)
        cell = ws.cell(row=row + 1, column=c1, value=unvan)
        cell.alignment = CENTER
        cell.font = FONT_BOLD

    ws.merge_cells(start_row=row + 2, start_column=1, end_row=row + 2, end_column=2)
    cell = ws.cell(row=row + 2, column=1, value="Uzlaşma Komisyonu")
    cell.alignment = CENTER
    cell.font = FONT_NORMAL
    return row + 3


def _imza_bloklari_3lu(ws, row, imzalayanlar):
    """Baskan | Uye | Uye seklinde 3 imza blogu (Gelmedi tutanagi)."""
    aralik = [(1, 2), (3, 4), (5, 6)]
    unvanlar = ["Başkan", "Üye", "Üye"]
    isimler = []
    for u in unvanlar:
        uygun = next((k["ad_soyad"] for k in imzalayanlar if (k.get("unvan") or "").strip() == u
                       and k["ad_soyad"] not in isimler), None)
        if uygun is None:
            uygun = next((k["ad_soyad"] for k in imzalayanlar if k["ad_soyad"] not in isimler), "")
        isimler.append(uygun)

    for (c1, c2), isim in zip(aralik, isimler):
        ws.merge_cells(start_row=row, start_column=c1, end_row=row, end_column=c2)
        cell = ws.cell(row=row, column=c1, value=isim)
        cell.alignment = CENTER
        cell.font = FONT_NORMAL

    for (c1, c2), unvan in zip(aralik, unvanlar):
        ws.merge_cells(start_row=row + 1, start_column=c1, end_row=row + 1, end_column=c2)
        cell = ws.cell(row=row + 1, column=c1, value=unvan)
        cell.alignment = CENTER
        cell.font = FONT_BOLD

    ws.merge_cells(start_row=row + 2, start_column=1, end_row=row + 2, end_column=2)
    cell = ws.cell(row=row + 2, column=1, value="Uzlaşma Komisyonu")
    cell.alignment = CENTER
    cell.font = FONT_NORMAL
    return row + 3


# ---------------------------------------------------------------------------
# Sablon 1 ve 2: UZLASMA TUTANAGI (uzlasildi / uzlasilamadi)
# ---------------------------------------------------------------------------

def uzlasma_tutanagi_olustur(dosya_yolu, kurum, tutanak_no, toplanti_tarih_saat, mukellef,
                              kalemler, imzalayanlar, sonuc):
    """sonuc: 'uzlasildi' veya 'uzlasilamadi'."""
    wb = Workbook()
    ws = wb.active
    ws.title = "Tutanak"
    _kur_kolon_genislikleri(ws)

    row = _baslik_blogu(ws, kurum, "UZLAŞMA TUTANAĞI")
    row = _ust_bilgi_blogu(ws, row, kurum, tutanak_no, toplanti_tarih_saat, mukellef)

    tarih_str, saat_str = _tarih_saat_ayir(toplanti_tarih_saat)
    if sonuc == "uzlasildi":
        aciklama = (
            f"Aşağıda isim ve ünvanları yazılı Başkan ve üyelerinden teşekkül eden Uzlaşma "
            f"Komisyonumuz mükellefin iştirakiyle {tarih_str} tarihinde saat {saat_str}'da "
            f"toplanarak tabloda yazılı vergi ve cezalar ile önerilen tutarlar üzerinde "
            f"uzlaşma sağlanmıştır.\n"
            f"     İşbu Uzlaşma Komisyonu Tutanağı (3) nüsha tanzim edilerek okundu. Doğruluğu "
            f"anlaşılarak mükellefle birlikte müştereken imzalandı. Düzenlenen tutanağın bir "
            f"örneği mükellefe komisyonda verildi."
        )
        tutar_basligi = "UZLAŞILAN TUTAR"
    else:
        aciklama = (
            f"Aşağıda isim ve ünvanları yazılı Başkan ve üyelerinden teşekkül eden Uzlaşma "
            f"Komisyonumuz mükellefin iştirakiyle {tarih_str} tarihinde saat {saat_str}'da "
            f"toplanarak tabloda yazılı vergi ve cezalar ile önerilen tutarlar üzerinde "
            f"uzlaşma sağlanamamıştır.\n"
            f"     Uzlaşma yönetmeliğinin 10. maddesine göre mükellefin önerilen bu miktarları "
            f"dava açma süresinin son günü akşamına kadar kabul ettiğini bildiren bir dilekçe "
            f"ile başvurması halinde uzlaşma vaki olmuş sayılacaktır."
        )
        tutar_basligi = "ÖNERİLEN TUTAR"

    row = _paragraf(ws, row, aciklama, yukseklik=120)

    # Tablo basligi (2 satir, birlesik)
    baslik_satiri = row
    basliklar = ["İhbarname Numarası", "Vergi ve Cezanın Türü", "Dönemi", "Vergi ve Cezanın Miktarı"]
    for col, metin in enumerate(basliklar, start=1):
        ws.merge_cells(start_row=baslik_satiri, start_column=col, end_row=baslik_satiri + 1, end_column=col)
        _hucre(ws, baslik_satiri, col, metin, font=FONT_BOLD)
    ws.merge_cells(start_row=baslik_satiri, start_column=5, end_row=baslik_satiri, end_column=6)
    _hucre(ws, baslik_satiri, 5, tutar_basligi, font=FONT_BOLD)
    _hucre(ws, baslik_satiri + 1, 5, "Rakamla (TL)", font=FONT_BOLD)
    _hucre(ws, baslik_satiri + 1, 6, "Yazıyla (TL)", font=FONT_BOLD)
    row = baslik_satiri + 2

    toplam_miktar = 0.0
    toplam_uzlasilan = 0.0
    for kalem in kalemler:
        miktar = float(kalem["miktar"])
        uzlasilan = float(kalem["uzlasilan_tutar"])
        toplam_miktar += miktar
        toplam_uzlasilan += uzlasilan
        _hucre(ws, row, 1, kalem["fis_no"])
        _hucre(ws, row, 2, _vergi_ceza_turu(kalem))
        _hucre(ws, row, 3, kalem.get("donem", ""))
        _hucre(ws, row, 4, miktar, num_format="#,##0.00")
        _hucre(ws, row, 5, uzlasilan, num_format="#,##0.00")
        _hucre(ws, row, 6, tutar_yaziya(uzlasilan), align=WRAP_LEFT)
        row += 1

    toplam_miktar = round(toplam_miktar, 2)
    toplam_uzlasilan = round(toplam_uzlasilan, 2)
    ws.merge_cells(start_row=row, start_column=1, end_row=row, end_column=3)
    _hucre(ws, row, 1, "TOPLAM", font=FONT_BOLD)
    _hucre(ws, row, 4, toplam_miktar, font=FONT_BOLD, num_format="#,##0.00")
    _hucre(ws, row, 5, toplam_uzlasilan, font=FONT_BOLD, num_format="#,##0.00")
    _hucre(ws, row, 6, tutar_yaziya(toplam_uzlasilan), font=FONT_BOLD, align=WRAP_LEFT)
    row += 2

    row = _paragraf(
        ws, row,
        "     NOT: İşbu uzlaşılan vergiler için V.U.K.nun 112. maddesi 3. fıkrası gereğince "
        "normal vade tarihinden itibaren uzlaşma tutanağının imzalandığı tarihe kadar geçen "
        "zaman için ayrıca Vergi Dairesince gecikme faizi hesaplanacaktır.",
        yukseklik=50,
    )
    row += 1

    _imza_bloklari_4lu(ws, row, imzalayanlar, mukellef.get("ad_unvan", ""))

    os.makedirs(os.path.dirname(dosya_yolu), exist_ok=True)
    wb.save(dosya_yolu)
    return dosya_yolu


# ---------------------------------------------------------------------------
# Sablon 3: UZLASMA KOMISYON KARAR TUTANAGI (gelmedi)
# ---------------------------------------------------------------------------

def gelmeme_tutanagi_olustur(dosya_yolu, kurum, tutanak_no, toplanti_tarih_saat,
                              davet_tarih_saat, mukellef, kalemler, imzalayanlar):
    wb = Workbook()
    ws = wb.active
    ws.title = "Tutanak"
    _kur_kolon_genislikleri(ws)

    row = _baslik_blogu(ws, kurum, "UZLAŞMA KOMİSYON KARAR TUTANAĞI")

    tarih_metni = f"{toplanti_tarih_saat} / {davet_tarih_saat}"
    row = _ust_bilgi_blogu(ws, row, kurum, tutanak_no, tarih_metni, mukellef)

    ws.merge_cells(start_row=row, start_column=1, end_row=row, end_column=6)
    c = ws.cell(row=row, column=1, value="UZLAŞMA TALEP EDİLEN")
    c.font = FONT_BOLD
    c.alignment = CENTER_TITLE
    row += 1

    baslik_satiri = row
    basliklar = ["İhbarname Numarası", "Vergi ve Cezanın Türü", "Dönemi", "Vergi ve Cezanın Miktarı"]
    for col, metin in enumerate(basliklar, start=1):
        if col == 4:
            ws.merge_cells(start_row=baslik_satiri, start_column=4, end_row=baslik_satiri, end_column=6)
        _hucre(ws, baslik_satiri, col, metin, font=FONT_BOLD)
    row = baslik_satiri + 1

    toplam_miktar = 0.0
    for kalem in kalemler:
        miktar = float(kalem["miktar"])
        toplam_miktar += miktar
        _hucre(ws, row, 1, kalem["fis_no"])
        _hucre(ws, row, 2, _vergi_ceza_turu(kalem))
        _hucre(ws, row, 3, kalem.get("donem", ""))
        ws.merge_cells(start_row=row, start_column=4, end_row=row, end_column=6)
        _hucre(ws, row, 4, miktar, num_format="#,##0.00")
        row += 1

    ws.merge_cells(start_row=row, start_column=1, end_row=row, end_column=5)
    _hucre(ws, row, 1, "TOPLAM", font=FONT_BOLD)
    _hucre(ws, row, 6, toplam_miktar, font=FONT_BOLD, num_format="#,##0.00")
    row += 2

    toplanti_tarih, toplanti_saat = _tarih_saat_ayir(toplanti_tarih_saat)
    davet_tarih, davet_saat = _tarih_saat_ayir(davet_tarih_saat)
    vergi_dairesi = kurum.get("vergi_dairesi", "")
    aciklama = (
        f"Uzlaşma Komisyonumuz 22/10/2005 tarih ve 25974 sayılı Uzlaşma Yönetmeliğinde "
        f"Değişiklik Yapılmasına Dair Yönetmeliğin 6. maddesine uygun olarak aşağıda isim ve "
        f"unvanları yazılı Başkan ve üyelerinden teşekkül eden Uzlaşma Komisyonumuz "
        f"{toplanti_tarih} tarihinde saat {toplanti_saat}'da toplandı.\n\n"
        f"Ancak uzlaşma isteminde bulunan ve yukarıda açık kimliği belirtilen mükellefe "
        f"uzlaşma görüşmesinin {davet_tarih} tarihinde saat {davet_saat}'da {vergi_dairesi}'nde "
        f"yapılacağına ilişkin uzlaşma davetiyesi usulüne uygun tebliğ edildiği halde, uzlaşma "
        f"davetiyesinde tayin edilen gün ve saatte bizzat veya vekili vasıtasıyla Uzlaşma "
        f"Komisyonuna gelmediğinden uzlaşma temin edilememiştir. Durumu tespit eden bu tutanak "
        f"komisyon üyelerince okunduktan sonra müştereken imza altına alındı."
    )
    row = _paragraf(ws, row, aciklama, yukseklik=140)
    row += 1

    _imza_bloklari_3lu(ws, row, imzalayanlar)

    os.makedirs(os.path.dirname(dosya_yolu), exist_ok=True)
    wb.save(dosya_yolu)
    return dosya_yolu


def _tarih_saat_ayir(tarih_saat_str):
    """'DD.MM.YYYY HH:MM' -> ('DD.MM.YYYY', 'HH:MM')."""
    if not tarih_saat_str:
        return "", ""
    parcalar = tarih_saat_str.strip().split(" ")
    if len(parcalar) >= 2:
        return parcalar[0], parcalar[1]
    return parcalar[0], ""


def tutanak_olustur_excel(dosya_yolu, kurum, tutanak_no, toplanti_tarih_saat, davet_tarih_saat,
                           mukellef, kalemler, imzalayanlar, sonuc):
    """Sonuca gore uygun sablonu uretir."""
    if sonuc == "gelmedi":
        return gelmeme_tutanagi_olustur(
            dosya_yolu, kurum, tutanak_no, toplanti_tarih_saat, davet_tarih_saat,
            mukellef, kalemler, imzalayanlar,
        )
    return uzlasma_tutanagi_olustur(
        dosya_yolu, kurum, tutanak_no, toplanti_tarih_saat, mukellef, kalemler, imzalayanlar, sonuc
    )
