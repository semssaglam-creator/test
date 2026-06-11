"""Vergi Turleri / Ceza Kodlari sekmesi."""
import tkinter as tk
from tkinter import ttk

from . import db
from .ui_widgets import bilgi_goster, hata_goster, onay_iste


class TurlerSekmesi(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent, padding=10)
        self._olustur()

    def _olustur(self):
        sol = ttk.LabelFrame(self, text="Vergi Turleri", padding=10)
        sol.pack(side="left", fill="both", expand=True, padx=(0, 5))

        self.vergi_tablo = ttk.Treeview(sol, columns=("kod", "ad"), show="headings", height=12)
        self.vergi_tablo.heading("kod", text="Kod")
        self.vergi_tablo.heading("ad", text="Aciklama")
        self.vergi_tablo.column("kod", width=80, anchor="center")
        self.vergi_tablo.column("ad", width=250, anchor="w")
        self.vergi_tablo.pack(fill="both", expand=True)

        ekle_cerceve = ttk.Frame(sol)
        ekle_cerceve.pack(fill="x", pady=(5, 0))
        self.vergi_kod = tk.StringVar()
        self.vergi_ad = tk.StringVar()
        ttk.Entry(ekle_cerceve, textvariable=self.vergi_kod, width=8).pack(side="left")
        ttk.Entry(ekle_cerceve, textvariable=self.vergi_ad, width=30).pack(side="left", padx=5)
        ttk.Button(ekle_cerceve, text="Ekle", command=self._vergi_ekle).pack(side="left")
        ttk.Button(ekle_cerceve, text="Sil", command=self._vergi_sil).pack(side="left", padx=5)

        sag = ttk.LabelFrame(self, text="Ceza Kodlari", padding=10)
        sag.pack(side="left", fill="both", expand=True, padx=(5, 0))

        self.ceza_tablo = ttk.Treeview(sag, columns=("kod", "aciklama"), show="headings", height=12)
        self.ceza_tablo.heading("kod", text="Kod")
        self.ceza_tablo.heading("aciklama", text="Aciklama (Ceza Nedeni)")
        self.ceza_tablo.column("kod", width=80, anchor="center")
        self.ceza_tablo.column("aciklama", width=350, anchor="w")
        self.ceza_tablo.pack(fill="both", expand=True)

        ekle_cerceve2 = ttk.Frame(sag)
        ekle_cerceve2.pack(fill="x", pady=(5, 0))
        self.ceza_kod = tk.StringVar()
        self.ceza_aciklama = tk.StringVar()
        ttk.Entry(ekle_cerceve2, textvariable=self.ceza_kod, width=8).pack(side="left")
        ttk.Entry(ekle_cerceve2, textvariable=self.ceza_aciklama, width=40).pack(side="left", padx=5)
        ttk.Button(ekle_cerceve2, text="Ekle", command=self._ceza_ekle).pack(side="left")
        ttk.Button(ekle_cerceve2, text="Sil", command=self._ceza_sil).pack(side="left", padx=5)

        self.yenile()

    def yenile(self):
        for item in self.vergi_tablo.get_children():
            self.vergi_tablo.delete(item)
        for v in db.vergi_turleri_listele():
            self.vergi_tablo.insert("", tk.END, values=(v["kod"], v["ad"] or ""), tags=(str(v["id"]),))

        for item in self.ceza_tablo.get_children():
            self.ceza_tablo.delete(item)
        for c in db.ceza_kodlari_listele():
            self.ceza_tablo.insert("", tk.END, values=(c["kod"], c["aciklama"] or ""), tags=(str(c["id"]),))

    def _vergi_ekle(self):
        kod = self.vergi_kod.get().strip()
        if not kod:
            hata_goster(self, "Kod bos olamaz.")
            return
        db.vergi_turu_ekle(kod, self.vergi_ad.get().strip())
        self.vergi_kod.set("")
        self.vergi_ad.set("")
        self.yenile()

    def _vergi_sil(self):
        secim = self.vergi_tablo.selection()
        if not secim:
            return
        if not onay_iste(self, "Secili vergi turu pasif yapilacak. Onayliyor musunuz?"):
            return
        for item in secim:
            db.vergi_turu_sil(int(self.vergi_tablo.item(item, "tags")[0]))
        self.yenile()

    def _ceza_ekle(self):
        kod = self.ceza_kod.get().strip()
        if not kod:
            hata_goster(self, "Kod bos olamaz.")
            return
        db.ceza_kodu_ekle(kod, self.ceza_aciklama.get().strip())
        self.ceza_kod.set("")
        self.ceza_aciklama.set("")
        self.yenile()

    def _ceza_sil(self):
        secim = self.ceza_tablo.selection()
        if not secim:
            return
        if not onay_iste(self, "Secili ceza kodu pasif yapilacak. Onayliyor musunuz?"):
            return
        for item in secim:
            db.ceza_kodu_sil(int(self.ceza_tablo.item(item, "tags")[0]))
        self.yenile()
