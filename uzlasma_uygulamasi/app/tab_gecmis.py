"""Tutanak Gecmisi sekmesi: tum tutanaklar ve komisyon uyesi imza gecmisi."""
import os
import subprocess
import sys
import tkinter as tk
from tkinter import ttk

from . import db
from .ui_widgets import bilgi_goster
from .tarih_util import iso_to_tr

SONUC_ETIKETLERI = {
    "uzlasildi": "Uzlasildi",
    "uzlasilamadi": "Uzlasilamadi",
    "gelmedi": "Gelmedi",
}


class GecmisSekmesi(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent, padding=10)
        self._olustur()

    def _olustur(self):
        ust = ttk.LabelFrame(self, text="Tum Tutanaklar", padding=10)
        ust.pack(fill="both", expand=True)

        kolonlar = ("tarih", "tutanak_no", "mukellef", "vkn_tckn", "sonuc", "dosya")
        self.tablo = ttk.Treeview(ust, columns=kolonlar, show="headings", height=10)
        basliklar = {"tarih": "Toplanti Tarih/Saat", "tutanak_no": "Tutanak No", "mukellef": "Mukellef",
                      "vkn_tckn": "VKN/TCKN", "sonuc": "Sonuc", "dosya": "Dosya"}
        for k in kolonlar:
            self.tablo.heading(k, text=basliklar[k])
            genislik = 300 if k == "dosya" else (180 if k == "mukellef" else 120)
            self.tablo.column(k, width=genislik, anchor="w")
        self.tablo.pack(fill="both", expand=True)
        self.tablo.bind("<Double-1>", self._dosya_ac)

        ttk.Button(ust, text="Yenile", command=self.yenile).pack(anchor="w", pady=(5, 0))
        ttk.Label(ust, text="(Dosyayi acmak icin satira cift tiklayin)").pack(anchor="w")

        alt = ttk.LabelFrame(self, text="Komisyon Uyesi Imza Gecmisi", padding=10)
        alt.pack(fill="both", expand=True, pady=(10, 0))

        ttk.Label(alt, text="Komisyon Uyesi:").pack(anchor="w")
        self.uye_secim = ttk.Combobox(alt, state="readonly", width=40)
        self.uye_secim.pack(anchor="w")
        self.uye_secim.bind("<<ComboboxSelected>>", self._uye_secildi)

        kolonlar2 = ("tarih", "tutanak_no", "mukellef", "sonuc")
        self.uye_tablosu = ttk.Treeview(alt, columns=kolonlar2, show="headings", height=8)
        basliklar2 = {"tarih": "Toplanti Tarih/Saat", "tutanak_no": "Tutanak No", "mukellef": "Mukellef", "sonuc": "Sonuc"}
        for k in kolonlar2:
            self.uye_tablosu.heading(k, text=basliklar2[k])
            self.uye_tablosu.column(k, width=180 if k == "mukellef" else 130, anchor="w")
        self.uye_tablosu.pack(fill="both", expand=True, pady=(5, 0))

        self.yenile()

    def yenile(self):
        for item in self.tablo.get_children():
            self.tablo.delete(item)
        for t in db.tutanak_gecmisi():
            self.tablo.insert("", tk.END, values=(
                iso_to_tr(t["toplanti_tarih_saat"]), t["tutanak_no"], t["ad_unvan"], t["vkn_tckn"] or "",
                SONUC_ETIKETLERI.get(t["sonuc"], t["sonuc"]), t["dosya_yolu"] or "",
            ), tags=(str(t["id"]),))

        self._uyeler = db.komisyon_uyeleri_listele()
        self.uye_secim["values"] = [f"{u['ad_soyad']} ({u['unvan']})" if u["unvan"] else u["ad_soyad"]
                                     for u in self._uyeler]
        for item in self.uye_tablosu.get_children():
            self.uye_tablosu.delete(item)

    def _uye_secildi(self, _event=None):
        idx = self.uye_secim.current()
        if idx < 0:
            return
        uye = self._uyeler[idx]
        for item in self.uye_tablosu.get_children():
            self.uye_tablosu.delete(item)
        for t in db.komisyon_uyesi_imza_gecmisi(uye["id"]):
            self.uye_tablosu.insert("", tk.END, values=(
                iso_to_tr(t["toplanti_tarih_saat"]), t["tutanak_no"], t["ad_unvan"],
                SONUC_ETIKETLERI.get(t["sonuc"], t["sonuc"]),
            ))

    def _dosya_ac(self, _event=None):
        secim = self.tablo.selection()
        if not secim:
            return
        dosya = self.tablo.set(secim[0], "dosya")
        if not dosya or not os.path.isfile(dosya):
            bilgi_goster(self, "Dosya bulunamadi.")
            return
        try:
            if sys.platform.startswith("linux"):
                subprocess.Popen(["xdg-open", dosya])
            else:
                os.startfile(dosya)  # type: ignore[attr-defined]
        except Exception as exc:  # noqa: BLE001
            bilgi_goster(self, f"Dosya acilamadi: {exc}\nKonum: {dosya}")
