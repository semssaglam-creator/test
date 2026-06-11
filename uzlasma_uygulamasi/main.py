#!/usr/bin/env python3
"""Uzlasma Takip Uygulamasi - giris noktasi."""
import os
import sys
import tkinter as tk
from tkinter import ttk

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(BASE_DIR, "lib"))
sys.path.insert(0, BASE_DIR)

from app import db
from app.tab_kayit import DilekceKayitSekmesi
from app.tab_uzlasma import UzlasmaSekmesi
from app.tab_gecmis import GecmisSekmesi
from app.tab_turler import TurlerSekmesi
from app.tab_istatistik import IstatistikSekmesi
from app.tab_ayarlar import AyarlarSekmesi


class AnaPencere(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Uzlasma Takip Uygulamasi")
        self.geometry("1200x750")

        notebook = ttk.Notebook(self)
        notebook.pack(fill="both", expand=True)

        self.kayit_sekmesi = DilekceKayitSekmesi(notebook)
        self.uzlasma_sekmesi = UzlasmaSekmesi(notebook)
        self.gecmis_sekmesi = GecmisSekmesi(notebook)
        self.turler_sekmesi = TurlerSekmesi(notebook)
        self.istatistik_sekmesi = IstatistikSekmesi(notebook)
        self.ayarlar_sekmesi = AyarlarSekmesi(notebook)

        notebook.add(self.kayit_sekmesi, text="Dilekce Kaydi")
        notebook.add(self.uzlasma_sekmesi, text="Uzlasma Islemi")
        notebook.add(self.gecmis_sekmesi, text="Tutanak Gecmisi")
        notebook.add(self.turler_sekmesi, text="Vergi/Ceza Turleri")
        notebook.add(self.istatistik_sekmesi, text="Istatistikler")
        notebook.add(self.ayarlar_sekmesi, text="Ayarlar")

        notebook.bind("<<NotebookTabChanged>>", self._sekme_degisti)

    def _sekme_degisti(self, event):
        notebook = event.widget
        secili = notebook.nametowidget(notebook.select())
        if secili is self.kayit_sekmesi:
            self.kayit_sekmesi.sekme_gosterildi()
        elif secili is self.uzlasma_sekmesi:
            self.uzlasma_sekmesi.sekme_gosterildi()
        elif secili is self.gecmis_sekmesi:
            self.gecmis_sekmesi.yenile()
        elif secili is self.turler_sekmesi:
            self.turler_sekmesi.yenile()
        elif secili is self.istatistik_sekmesi:
            self.istatistik_sekmesi._hesapla()
        elif secili is self.ayarlar_sekmesi:
            self.ayarlar_sekmesi.yenile()


def main():
    db.init_db()
    app = AnaPencere()
    app.mainloop()


if __name__ == "__main__":
    main()
