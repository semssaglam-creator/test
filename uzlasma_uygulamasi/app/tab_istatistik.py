"""Istatistikler sekmesi."""
import tkinter as tk
from tkinter import ttk

from . import db
from .sayi_yaziya import tl_formatla
from .tarih_util import tr_tarih_to_iso_gun
from .ui_widgets import hata_goster

SONUC_ETIKETLERI = {
    "uzlasildi": "Uzlasildi",
    "uzlasilamadi": "Uzlasilamadi",
    "gelmedi": "Gelmedi",
}


class IstatistikSekmesi(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent, padding=10)
        self._olustur()

    def _olustur(self):
        filtre = ttk.LabelFrame(self, text="Tarih Araligi (GG.AA.YYYY, bos birakilabilir)", padding=10)
        filtre.pack(fill="x")

        ttk.Label(filtre, text="Baslangic:").grid(row=0, column=0, sticky="w")
        self.baslangic = tk.StringVar()
        ttk.Entry(filtre, textvariable=self.baslangic, width=14).grid(row=0, column=1, padx=5)

        ttk.Label(filtre, text="Bitis:").grid(row=0, column=2, sticky="w")
        self.bitis = tk.StringVar()
        ttk.Entry(filtre, textvariable=self.bitis, width=14).grid(row=0, column=3, padx=5)

        ttk.Button(filtre, text="Hesapla", command=self._hesapla).grid(row=0, column=4, padx=10)

        ozet = ttk.LabelFrame(self, text="Genel Ozet", padding=10)
        ozet.pack(fill="x", pady=(10, 0))
        self.ozet_etiketi = ttk.Label(ozet, text="-", justify="left")
        self.ozet_etiketi.pack(anchor="w")

        tablo_cerceve = ttk.LabelFrame(self, text="Ceza Kodu Bazinda Istatistikler", padding=10)
        tablo_cerceve.pack(fill="both", expand=True, pady=(10, 0))

        kolonlar = ("ceza_kodu", "aciklama", "basvuru_sayisi", "uzlasilan_sayisi",
                    "toplam_basvuru_tutari", "toplam_uzlasilan_tutar")
        basliklar = {
            "ceza_kodu": "Ceza Kodu", "aciklama": "Aciklama", "basvuru_sayisi": "Basvuru Sayisi",
            "uzlasilan_sayisi": "Uzlasilan Sayisi", "toplam_basvuru_tutari": "Toplam Basvuru Tutari (TL)",
            "toplam_uzlasilan_tutar": "Toplam Uzlasilan Tutar (TL)",
        }
        self.tablo = ttk.Treeview(tablo_cerceve, columns=kolonlar, show="headings", height=10)
        for k in kolonlar:
            self.tablo.heading(k, text=basliklar[k])
            genislik = 320 if k == "aciklama" else 150
            anchor = "w" if k == "aciklama" else "center"
            self.tablo.column(k, width=genislik, anchor=anchor)
        self.tablo.pack(fill="both", expand=True)

        self._hesapla()

    def _hesapla(self):
        baslangic_iso = ""
        bitis_iso = ""
        if self.baslangic.get().strip():
            baslangic_iso = tr_tarih_to_iso_gun(self.baslangic.get().strip())
            if not baslangic_iso:
                hata_goster(self, "Baslangic tarihi GG.AA.YYYY formatinda olmalidir.")
                return
        if self.bitis.get().strip():
            bitis_iso = tr_tarih_to_iso_gun(self.bitis.get().strip())
            if not bitis_iso:
                hata_goster(self, "Bitis tarihi GG.AA.YYYY formatinda olmalidir.")
                return

        veri = db.istatistikler(baslangic_iso or None, bitis_iso or None)

        dagilim = veri["sonuc_dagilimi"]
        ozet_metni = f"Basvuran mukellef sayisi: {veri['basvuran_sayisi']}\n"
        for sonuc, etiket in SONUC_ETIKETLERI.items():
            ozet_metni += f"{etiket}: {dagilim.get(sonuc, 0)}\n"
        self.ozet_etiketi.configure(text=ozet_metni.strip())

        for item in self.tablo.get_children():
            self.tablo.delete(item)
        for satir in veri["ceza_turu_bazinda"]:
            self.tablo.insert("", tk.END, values=(
                satir["ceza_kodu"], satir["aciklama"] or "", satir["basvuru_sayisi"],
                satir["uzlasilan_sayisi"], tl_formatla(satir["toplam_basvuru_tutari"] or 0),
                tl_formatla(satir["toplam_uzlasilan_tutar"] or 0),
            ))
