"""Ayarlar sekmesi: kurum bilgileri, komisyon uyeleri, yedekleme."""
import os
import tkinter as tk
from tkinter import ttk

from . import db
from .ui_widgets import bilgi_goster, hata_goster, onay_iste

UNVANLAR = ("Baskan", "Uye")


class AyarlarSekmesi(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent, padding=10)
        self._olustur()

    def _olustur(self):
        # --- Kurum bilgileri ---
        kurum = ttk.LabelFrame(self, text="Kurum Bilgileri", padding=10)
        kurum.pack(fill="x")

        ttk.Label(kurum, text="Defterdarlik:").grid(row=0, column=0, sticky="w", pady=4)
        self.defterdarlik = tk.StringVar()
        ttk.Entry(kurum, textvariable=self.defterdarlik, width=50).grid(row=0, column=1, sticky="w", padx=5)

        ttk.Label(kurum, text="Vergi Dairesi Mudurlugu:").grid(row=1, column=0, sticky="w", pady=4)
        self.vergi_dairesi = tk.StringVar()
        ttk.Entry(kurum, textvariable=self.vergi_dairesi, width=50).grid(row=1, column=1, sticky="w", padx=5)

        ttk.Button(kurum, text="Kaydet", command=self._kurum_kaydet).grid(row=2, column=1, sticky="w", pady=(8, 0))

        # --- Komisyon uyeleri ---
        komisyon = ttk.LabelFrame(self, text="Komisyon Uyeleri", padding=10)
        komisyon.pack(fill="both", expand=True, pady=(10, 0))

        self.uye_tablo = ttk.Treeview(komisyon, columns=("ad_soyad", "unvan", "durum"), show="headings", height=8)
        self.uye_tablo.heading("ad_soyad", text="Ad Soyad")
        self.uye_tablo.heading("unvan", text="Unvan")
        self.uye_tablo.heading("durum", text="Durum")
        self.uye_tablo.column("ad_soyad", width=250, anchor="w")
        self.uye_tablo.column("unvan", width=120, anchor="center")
        self.uye_tablo.column("durum", width=100, anchor="center")
        self.uye_tablo.pack(fill="both", expand=True)

        ekle_cerceve = ttk.Frame(komisyon)
        ekle_cerceve.pack(fill="x", pady=(5, 0))
        ttk.Label(ekle_cerceve, text="Ad Soyad:").pack(side="left")
        self.uye_ad_soyad = tk.StringVar()
        ttk.Entry(ekle_cerceve, textvariable=self.uye_ad_soyad, width=30).pack(side="left", padx=5)
        ttk.Label(ekle_cerceve, text="Unvan:").pack(side="left")
        self.uye_unvan = tk.StringVar(value=UNVANLAR[0])
        ttk.Combobox(ekle_cerceve, textvariable=self.uye_unvan, values=UNVANLAR, state="readonly",
                      width=10).pack(side="left", padx=5)
        ttk.Button(ekle_cerceve, text="Ekle", command=self._uye_ekle).pack(side="left", padx=(5, 0))
        ttk.Button(ekle_cerceve, text="Pasif Yap", command=self._uye_sil).pack(side="left", padx=5)

        # --- Yedekleme ---
        yedek = ttk.LabelFrame(self, text="Veritabani Yedekleme", padding=10)
        yedek.pack(fill="both", expand=True, pady=(10, 0))

        self.yedek_tablo = ttk.Treeview(yedek, columns=("dosya",), show="headings", height=6)
        self.yedek_tablo.heading("dosya", text="Yedek Dosyasi")
        self.yedek_tablo.column("dosya", width=300, anchor="w")
        self.yedek_tablo.pack(fill="both", expand=True)

        yedek_buton_cerceve = ttk.Frame(yedek)
        yedek_buton_cerceve.pack(fill="x", pady=(5, 0))
        ttk.Button(yedek_buton_cerceve, text="Yedek Al", command=self._yedek_al).pack(side="left")
        ttk.Button(yedek_buton_cerceve, text="Geri Yukle", command=self._geri_yukle).pack(side="left", padx=5)
        ttk.Button(yedek_buton_cerceve, text="Yenile", command=self._yedekleri_yenile).pack(side="left")

        self.yenile()

    # ------------------------------------------------------------------
    def yenile(self):
        kurum = db.get_kurum_bilgileri()
        if kurum:
            self.defterdarlik.set(kurum["defterdarlik"] or "")
            self.vergi_dairesi.set(kurum["vergi_dairesi"] or "")
        self._uyeleri_yenile()
        self._yedekleri_yenile()

    def _kurum_kaydet(self):
        db.set_kurum_bilgileri(self.defterdarlik.get().strip(), self.vergi_dairesi.get().strip())
        bilgi_goster(self, "Kurum bilgileri kaydedildi.")

    # ------------------------------------------------------------------
    def _uyeleri_yenile(self):
        for item in self.uye_tablo.get_children():
            self.uye_tablo.delete(item)
        for u in db.komisyon_uyeleri_listele(sadece_aktif=False):
            self.uye_tablo.insert("", tk.END, values=(
                u["ad_soyad"], u["unvan"] or "", "Aktif" if u["aktif"] else "Pasif",
            ), tags=(str(u["id"]),))

    def _uye_ekle(self):
        ad_soyad = self.uye_ad_soyad.get().strip()
        if not ad_soyad:
            hata_goster(self, "Ad Soyad bos olamaz.")
            return
        db.komisyon_uyesi_ekle(ad_soyad, self.uye_unvan.get())
        self.uye_ad_soyad.set("")
        self._uyeleri_yenile()

    def _uye_sil(self):
        secim = self.uye_tablo.selection()
        if not secim:
            return
        if not onay_iste(self, "Secili komisyon uyesi pasif yapilacak. Onayliyor musunuz?"):
            return
        for item in secim:
            db.komisyon_uyesi_sil(int(self.uye_tablo.item(item, "tags")[0]))
        self._uyeleri_yenile()

    # ------------------------------------------------------------------
    def _yedekleri_yenile(self):
        for item in self.yedek_tablo.get_children():
            self.yedek_tablo.delete(item)
        for dosya in db.yedekleri_listele():
            self.yedek_tablo.insert("", tk.END, values=(dosya,))

    def _yedek_al(self):
        try:
            hedef = db.yedek_al()
        except Exception as exc:  # noqa: BLE001
            hata_goster(self, f"Yedek alinamadi: {exc}")
            return
        bilgi_goster(self, f"Yedek alindi:\n{os.path.basename(hedef)}")
        self._yedekleri_yenile()

    def _geri_yukle(self):
        secim = self.yedek_tablo.selection()
        if not secim:
            hata_goster(self, "Geri yuklenecek yedegi secin.")
            return
        dosya_adi = self.yedek_tablo.set(secim[0], "dosya")
        if not onay_iste(self, f"'{dosya_adi}' yedegi geri yuklenecek ve mevcut veritabaninin "
                                f"yerini alacak. Onayliyor musunuz?"):
            return
        try:
            db.yedekten_geri_yukle(dosya_adi)
        except Exception as exc:  # noqa: BLE001
            hata_goster(self, f"Geri yukleme basarisiz: {exc}")
            return
        bilgi_goster(self, "Veritabani geri yuklendi. Uygulamayi yeniden baslatmaniz onerilir.")
        self._yedekleri_yenile()
