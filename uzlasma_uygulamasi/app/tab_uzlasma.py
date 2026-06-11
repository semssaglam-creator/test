"""Uzlasma Islemi sekmesi: mukellef arama, ihbarname secimi, tutanak olusturma."""
import os
import tkinter as tk
from tkinter import ttk

from . import db
from .excel_export import tutanak_olustur_excel
from .ui_widgets import AramaKutusu, DuzenlenebilirTablo, bilgi_goster, hata_goster, onay_iste
from .sayi_yaziya import tl_formatla
from .tarih_util import simdi_tr, tr_to_iso

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TUTANAK_DIR = os.path.join(BASE_DIR, "tutanaklar")

KOLONLAR = ("sec", "fis_no", "vergi_turu_kod", "ceza_kodu", "ceza_nedeni", "donem", "miktar",
            "indirim_orani", "kalan_tutar")
BASLIKLAR = {
    "sec": "Sec",
    "fis_no": "Ihbarname Fis No",
    "vergi_turu_kod": "Vergi Turu",
    "ceza_kodu": "Ceza Kodu",
    "ceza_nedeni": "Ceza Nedeni",
    "donem": "Donem",
    "miktar": "Miktar (TL)",
    "indirim_orani": "Indirim %",
    "kalan_tutar": "Kalan Tutar (TL)",
}

SEC_ISARETLI = "☑"
SEC_BOS = "☐"

SONUC_ETIKETLERI = {
    "uzlasildi": "Uzlasildi",
    "uzlasilamadi": "Uzlasilamadi",
    "gelmedi": "Gelmedi",
}


class UzlasmaSekmesi(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent, padding=10)
        self.secili_mukellef_id = None
        self.satir_bilgisi = {}  # tree item id -> {ceza_satiri_id, ihbarname_id, fis_no, miktar, ...}
        self._olustur()

    def _olustur(self):
        ust = ttk.LabelFrame(self, text="Mukellef Ara", padding=10)
        ust.pack(fill="x")
        ttk.Label(ust, text="Ad/Unvan, VKN/TCKN veya Ihbarname Fis No (en az 3 karakter):").pack(anchor="w")
        self.arama = AramaKutusu(ust, self._mukellef_ara, self._mukellef_secildi, genislik=70)
        self.arama.pack(fill="x")
        self.secili_mukellef_etiketi = ttk.Label(ust, text="Secili mukellef: -", font=("", 10, "bold"))
        self.secili_mukellef_etiketi.pack(anchor="w", pady=(5, 0))

        # --- bekleyen ihbarnameler tablosu ---
        tablo_cerceve = ttk.LabelFrame(self, text="Uzlasilmamis Ihbarnameler / Ceza Satirlari", padding=10)
        tablo_cerceve.pack(fill="both", expand=True, pady=(10, 0))

        self.tablo = DuzenlenebilirTablo(
            tablo_cerceve, columns=KOLONLAR, show="headings", height=10,
            duzenlenebilir_kolonlar={"indirim_orani"},
            degisti_callback=self._indirim_degisti,
        )
        for k in KOLONLAR:
            self.tablo.heading(k, text=BASLIKLAR[k])
            genislik = {"sec": 40, "vergi_turu_kod": 80, "ceza_kodu": 70, "donem": 90,
                         "miktar": 100, "indirim_orani": 80, "kalan_tutar": 110}.get(k, 160)
            anchor = "center" if k in ("sec", "vergi_turu_kod", "ceza_kodu", "donem", "indirim_orani") else "w"
            self.tablo.column(k, width=genislik, anchor=anchor)
        self.tablo.pack(fill="both", expand=True)
        self.tablo.bind("<Button-1>", self._tablo_tiklandi, add="+")

        oran_cerceve = ttk.Frame(tablo_cerceve)
        oran_cerceve.pack(fill="x", pady=(5, 0))
        ttk.Label(oran_cerceve, text="Varsayilan Indirim Orani %:").pack(side="left")
        self.varsayilan_oran = tk.StringVar(value="80")
        ttk.Entry(oran_cerceve, textvariable=self.varsayilan_oran, width=6).pack(side="left", padx=5)
        ttk.Button(oran_cerceve, text="Secililere Uygula", command=self._orani_uygula).pack(side="left")

        # --- tutanak bilgileri ---
        alt = ttk.LabelFrame(self, text="Tutanak Bilgileri", padding=10)
        alt.pack(fill="x", pady=(10, 0))

        ttk.Label(alt, text="Sonuc:").grid(row=0, column=0, sticky="w")
        self.sonuc = tk.StringVar(value="uzlasildi")
        sonuc_cerceve = ttk.Frame(alt)
        sonuc_cerceve.grid(row=0, column=1, sticky="w")
        for deger, metin in SONUC_ETIKETLERI.items():
            ttk.Radiobutton(sonuc_cerceve, text=metin, value=deger, variable=self.sonuc,
                            command=self._sonuc_degisti).pack(side="left", padx=(0, 10))

        ttk.Label(alt, text="Toplanti Tarih/Saat:").grid(row=1, column=0, sticky="w", pady=4)
        self.toplanti_tarih_saat = tk.StringVar(value=simdi_tr())
        ttk.Entry(alt, textvariable=self.toplanti_tarih_saat, width=20).grid(row=1, column=1, sticky="w")

        self.davet_etiketi = ttk.Label(alt, text="Davet Edilen Tarih/Saat (Gelmedi icin):")
        self.davet_etiketi.grid(row=2, column=0, sticky="w", pady=4)
        self.davet_tarih_saat = tk.StringVar(value="")
        self.davet_entry = ttk.Entry(alt, textvariable=self.davet_tarih_saat, width=20)
        self.davet_entry.grid(row=2, column=1, sticky="w")

        ttk.Label(alt, text="Imzalayacak Komisyon Uyeleri:").grid(row=0, column=2, sticky="nw", padx=(20, 0))
        self.komisyon_listesi = tk.Listbox(alt, selectmode="multiple", height=4, exportselection=False)
        self.komisyon_listesi.grid(row=1, column=2, rowspan=3, sticky="we", padx=(20, 0))
        self._komisyon_doldur()

        alt.columnconfigure(1, weight=0)

        ttk.Button(self, text="Tutanak Olustur", command=self._tutanak_olustur).pack(anchor="e", pady=(10, 0))

        self._sonuc_degisti()

    # ------------------------------------------------------------------
    def _komisyon_doldur(self):
        self.komisyon_listesi.delete(0, tk.END)
        self._komisyon_uyeleri = db.komisyon_uyeleri_listele()
        for u in self._komisyon_uyeleri:
            unvan = f" ({u['unvan']})" if u["unvan"] else ""
            self.komisyon_listesi.insert(tk.END, f"{u['ad_soyad']}{unvan}")

    def _sonuc_degisti(self):
        if self.sonuc.get() == "gelmedi":
            self.davet_entry.configure(state="normal")
        else:
            self.davet_entry.configure(state="disabled")

    # ------------------------------------------------------------------
    def _mukellef_ara(self, metin):
        sonuclar = db.mukellef_ara(metin)
        return [(f"{m['ad_unvan']} - {m['vkn_tckn'] or ''}", m["id"]) for m in sonuclar]

    def _mukellef_secildi(self, mukellef_id, etiket):
        self.secili_mukellef_id = mukellef_id
        self.secili_mukellef_etiketi.configure(text=f"Secili mukellef: {etiket}")
        self._tabloyu_doldur()

    def _tabloyu_doldur(self):
        for item in self.tablo.get_children():
            self.tablo.delete(item)
        self.satir_bilgisi.clear()
        if not self.secili_mukellef_id:
            return
        veri = db.bekleyen_ihbarnameler(self.secili_mukellef_id)
        try:
            varsayilan = float(self.varsayilan_oran.get())
        except ValueError:
            varsayilan = 80.0
        for grup in veri:
            ih = grup["ihbarname"]
            for satir in grup["satirlar"]:
                miktar = satir["miktar"]
                kalan = round(miktar * (1 - varsayilan / 100), 2)
                item = self.tablo.insert("", tk.END, values=(
                    SEC_BOS, ih["fis_no"], satir["vergi_turu_kod"], satir["ceza_kodu"],
                    satir["ceza_nedeni"], satir["donem"] or "", tl_formatla(miktar),
                    f"{varsayilan:g}", tl_formatla(kalan),
                ))
                self.satir_bilgisi[item] = {
                    "ceza_satiri_id": satir["id"],
                    "ihbarname_id": ih["id"],
                    "fis_no": ih["fis_no"],
                    "miktar": miktar,
                    "secili": False,
                }

    # ------------------------------------------------------------------
    def _tablo_tiklandi(self, event):
        bolge = self.tablo.identify("region", event.x, event.y)
        if bolge != "cell":
            return
        kolon = self.tablo.identify_column(event.x)
        item = self.tablo.identify_row(event.y)
        if not item:
            return
        if self.tablo.column(kolon, "id") != "sec" and kolon != "#1":
            return
        # Ayni fis_no'ya sahip tum satirlari birlikte sec/birak
        fis_no = self.satir_bilgisi[item]["fis_no"]
        yeni_durum = not self.satir_bilgisi[item]["secili"]
        for it, bilgi in self.satir_bilgisi.items():
            if bilgi["fis_no"] == fis_no:
                bilgi["secili"] = yeni_durum
                isaret = SEC_ISARETLI if yeni_durum else SEC_BOS
                self.tablo.set(it, "sec", isaret)

    def _indirim_degisti(self, item, kolon, yeni_deger):
        if kolon != "indirim_orani" or item not in self.satir_bilgisi:
            return
        try:
            oran = float(yeni_deger.replace(",", "."))
        except ValueError:
            oran = 80.0
            self.tablo.set(item, "indirim_orani", "80")
        miktar = self.satir_bilgisi[item]["miktar"]
        kalan = round(miktar * (1 - oran / 100), 2)
        self.tablo.set(item, "kalan_tutar", tl_formatla(kalan))

    def _orani_uygula(self):
        try:
            oran = float(self.varsayilan_oran.get())
        except ValueError:
            hata_goster(self, "Gecerli bir oran girin.")
            return
        for item, bilgi in self.satir_bilgisi.items():
            if bilgi["secili"]:
                self.tablo.set(item, "indirim_orani", f"{oran:g}")
                kalan = round(bilgi["miktar"] * (1 - oran / 100), 2)
                self.tablo.set(item, "kalan_tutar", tl_formatla(kalan))

    # ------------------------------------------------------------------
    def _tutanak_olustur(self):
        if not self.secili_mukellef_id:
            hata_goster(self, "Once bir mukellef secin.")
            return

        secili_itemler = [it for it, b in self.satir_bilgisi.items() if b["secili"]]
        if not secili_itemler:
            hata_goster(self, "Uzlasmaya konu en az bir ihbarname secmelisiniz.")
            return

        secilen_uye_idx = self.komisyon_listesi.curselection()
        if not secilen_uye_idx:
            hata_goster(self, "En az bir komisyon uyesi secmelisiniz.")
            return
        imzalayanlar = [self._komisyon_uyeleri[i] for i in secilen_uye_idx]

        sonuc = self.sonuc.get()
        if sonuc == "gelmedi" and not self.davet_tarih_saat.get().strip():
            hata_goster(self, "Gelmedi sonucunda 'Davet Edilen Tarih/Saat' bos olamaz.")
            return

        kalemler_db = []
        kalemler_excel = []
        for item in secili_itemler:
            bilgi = self.satir_bilgisi[item]
            satir_db = db.ihbarname_satirlarini_getir(bilgi["ihbarname_id"])
            satir = next(s for s in satir_db if s["id"] == bilgi["ceza_satiri_id"])
            try:
                oran = float(self.tablo.set(item, "indirim_orani").replace(",", "."))
            except ValueError:
                oran = 80.0
            uzlasilan_tutar = 0.0 if sonuc == "gelmedi" else round(satir["miktar"] * (1 - oran / 100), 2)
            kalemler_db.append((satir["id"], bilgi["ihbarname_id"], oran, uzlasilan_tutar))
            kalemler_excel.append({
                "fis_no": bilgi["fis_no"],
                "vergi_turu_kod": satir["vergi_turu_kod"],
                "ceza_kodu": satir["ceza_kodu"],
                "donem": satir["donem"],
                "miktar": satir["miktar"],
                "uzlasilan_tutar": uzlasilan_tutar,
            })

        if not onay_iste(self, f"{len(kalemler_excel)} ihbarname kalemi icin "
                                f"'{SONUC_ETIKETLERI[sonuc]}' tutanagi olusturulacak. Onaylıyor musunuz?"):
            return

        kurum = db.get_kurum_bilgileri()
        mukellef = db.mukellef_getir(self.secili_mukellef_id)
        tutanak_no = db.sonraki_tutanak_no()

        toplanti_tr = self.toplanti_tarih_saat.get().strip()
        davet_tr = self.davet_tarih_saat.get().strip()

        os.makedirs(TUTANAK_DIR, exist_ok=True)
        guvenli_isim = "".join(c if c.isalnum() else "_" for c in mukellef["ad_unvan"])[:40]
        guvenli_no = tutanak_no.replace("/", "_")
        dosya_adi = f"{guvenli_no}_{guvenli_isim}_{sonuc}.xlsx"
        dosya_yolu = os.path.join(TUTANAK_DIR, dosya_adi)

        try:
            tutanak_olustur_excel(
                dosya_yolu, kurum, tutanak_no, toplanti_tr, davet_tr, mukellef, kalemler_excel,
                imzalayanlar, sonuc,
            )
        except Exception as exc:  # noqa: BLE001
            hata_goster(self, f"Excel dosyasi olusturulamadi: {exc}")
            return

        komisyon_uye_idleri = [u["id"] for u in imzalayanlar]
        db.tutanak_olustur(
            tutanak_no, self.secili_mukellef_id, sonuc, tr_to_iso(toplanti_tr), tr_to_iso(davet_tr),
            "", kalemler_db, komisyon_uye_idleri, dosya_yolu,
        )

        bilgi_goster(self, f"Tutanak olusturuldu:\n{dosya_yolu}")
        self._tabloyu_doldur()

    def sekme_gosterildi(self):
        """Diger sekmelerde komisyon uyesi/oran degisikligi olduysa listeleri tazeler."""
        self._komisyon_doldur()
