"""Dilekce Kaydi sekmesi: mukellef + ihbarname/ceza satiri kaydi (elle veya yapistir)."""
import tkinter as tk
from tkinter import ttk

from . import db
from .paste_parser import dilekce_ayristir
from .ui_widgets import AramaKutusu, DuzenlenebilirTablo, bilgi_goster, hata_goster, onay_iste

KOLONLAR = ("fis_no", "vergi_turu_kod", "ceza_kodu", "ceza_nedeni", "donem", "miktar",
            "duzenleme_tarihi", "teblig_tarihi")
BASLIKLAR = {
    "fis_no": "Ihbarname Fis No",
    "vergi_turu_kod": "Vergi Turu",
    "ceza_kodu": "Ceza Kodu",
    "ceza_nedeni": "Ceza Nedeni",
    "donem": "Donem",
    "miktar": "Miktar (TL)",
    "duzenleme_tarihi": "Duzenleme Tarihi",
    "teblig_tarihi": "Teblig Tarihi",
}


class DilekceKayitSekmesi(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent, padding=10)
        self.secili_mukellef_id = None
        self._olustur()

    def _olustur(self):
        # --- Mukellef bilgileri ---
        mukellef_cerceve = ttk.LabelFrame(self, text="Mukellef Bilgileri", padding=10)
        mukellef_cerceve.pack(fill="x")

        ttk.Label(mukellef_cerceve, text="Mevcut mukellef ara (ad/VKN/TCKN/ihbarname no):").grid(
            row=0, column=0, sticky="w", columnspan=2)
        self.arama = AramaKutusu(mukellef_cerceve, self._mukellef_ara, self._mukellef_secildi, genislik=60)
        self.arama.grid(row=1, column=0, columnspan=2, sticky="we", pady=(0, 8))

        ttk.Label(mukellef_cerceve, text="Ad Soyad / Unvan:").grid(row=2, column=0, sticky="w")
        self.ad_unvan = tk.StringVar()
        ttk.Entry(mukellef_cerceve, textvariable=self.ad_unvan, width=60).grid(row=2, column=1, sticky="we", pady=2)

        ttk.Label(mukellef_cerceve, text="VKN / TCKN:").grid(row=3, column=0, sticky="w")
        self.vkn_tckn = tk.StringVar()
        ttk.Entry(mukellef_cerceve, textvariable=self.vkn_tckn, width=30).grid(row=3, column=1, sticky="w", pady=2)

        ttk.Label(mukellef_cerceve, text="Adres:").grid(row=4, column=0, sticky="w")
        self.adres = tk.StringVar()
        ttk.Entry(mukellef_cerceve, textvariable=self.adres, width=60).grid(row=4, column=1, sticky="we", pady=2)

        ttk.Label(mukellef_cerceve, text="Telefon:").grid(row=5, column=0, sticky="w")
        self.telefon = tk.StringVar()
        ttk.Entry(mukellef_cerceve, textvariable=self.telefon, width=30).grid(row=5, column=1, sticky="w", pady=2)

        ttk.Button(mukellef_cerceve, text="Formu Temizle (Yeni Mukellef)", command=self._formu_temizle).grid(
            row=6, column=1, sticky="e", pady=(8, 0))

        mukellef_cerceve.columnconfigure(1, weight=1)

        # --- Yapistir ---
        yapistir_cerceve = ttk.LabelFrame(
            self, text="Dilekceden Kopyala-Yapistir (Dijital Vergi Dairesi PDF metni)", padding=10)
        yapistir_cerceve.pack(fill="x", pady=(10, 0))

        self.yapistir_metni = tk.Text(yapistir_cerceve, height=6, wrap="word")
        self.yapistir_metni.pack(fill="x")
        ttk.Button(yapistir_cerceve, text="Metni Ayristir ve Forma Aktar", command=self._yapistir_ayristir).pack(
            anchor="e", pady=(5, 0))

        # --- Tablo ---
        tablo_cerceve = ttk.LabelFrame(self, text="Ihbarname / Ceza Satirlari", padding=10)
        tablo_cerceve.pack(fill="both", expand=True, pady=(10, 0))

        vergi_turleri = [v["kod"] for v in db.vergi_turleri_listele()]
        ceza_kodlari = [c["kod"] for c in db.ceza_kodlari_listele()]

        self.tablo = DuzenlenebilirTablo(
            tablo_cerceve, columns=KOLONLAR, show="headings", height=10,
            duzenlenebilir_kolonlar=set(KOLONLAR),
            combo_degerleri={"vergi_turu_kod": vergi_turleri, "ceza_kodu": ceza_kodlari},
        )
        for k in KOLONLAR:
            self.tablo.heading(k, text=BASLIKLAR[k])
            genislik = 90 if k in ("vergi_turu_kod", "ceza_kodu", "donem", "miktar") else 150
            self.tablo.column(k, width=genislik, anchor="w")
        self.tablo.pack(fill="both", expand=True)

        buton_cerceve = ttk.Frame(tablo_cerceve)
        buton_cerceve.pack(fill="x", pady=(5, 0))
        ttk.Button(buton_cerceve, text="Satir Ekle", command=self._satir_ekle).pack(side="left")
        ttk.Button(buton_cerceve, text="Secili Satiri Sil", command=self._satir_sil).pack(side="left", padx=5)
        ttk.Button(buton_cerceve, text="Kaydet", command=self._kaydet).pack(side="right")

        # Saklanan ek alanlar (onay zamani vb. kayit aninda yazilir)
        self._dilekce_onay_zamani = ""

    def sekme_gosterildi(self):
        """Vergi turleri/ceza kodlari sekmesinde degisiklik olduysa combo listelerini tazeler."""
        self.tablo.combo_degerleri["vergi_turu_kod"] = [v["kod"] for v in db.vergi_turleri_listele()]
        self.tablo.combo_degerleri["ceza_kodu"] = [c["kod"] for c in db.ceza_kodlari_listele()]

    # -- mukellef arama --
    def _mukellef_ara(self, metin):
        sonuclar = db.mukellef_ara(metin)
        return [(f"{m['ad_unvan']} - {m['vkn_tckn'] or ''}", m["id"]) for m in sonuclar]

    def _mukellef_secildi(self, mukellef_id, _etiket):
        m = db.mukellef_getir(mukellef_id)
        if not m:
            return
        self.secili_mukellef_id = mukellef_id
        self.ad_unvan.set(m["ad_unvan"] or "")
        self.vkn_tckn.set(m["vkn_tckn"] or "")
        self.adres.set(m["adres"] or "")
        self.telefon.set(m["telefon"] or "")

    def _formu_temizle(self):
        self.secili_mukellef_id = None
        self.ad_unvan.set("")
        self.vkn_tckn.set("")
        self.adres.set("")
        self.telefon.set("")
        self.arama.temizle()
        for item in self.tablo.get_children():
            self.tablo.delete(item)
        self._dilekce_onay_zamani = ""

    # -- yapistir --
    def _yapistir_ayristir(self):
        metin = self.yapistir_metni.get("1.0", tk.END)
        if not metin.strip():
            hata_goster(self, "Once dilekce metnini yapistirin.")
            return
        veri = dilekce_ayristir(metin)
        m = veri["mukellef"]
        if m["ad_unvan"]:
            self.secili_mukellef_id = None
            self.arama.temizle()
            self.ad_unvan.set(m["ad_unvan"])
            self.vkn_tckn.set(m["vkn_tckn"])
            self.adres.set(m["adres"])
            self.telefon.set(m["telefon"])
        self._dilekce_onay_zamani = m.get("onay_zamani", "")

        eklenen = 0
        for ih in veri["ihbarnameler"]:
            satirlar = ih["ceza_satirlari"] or [{"vergi_turu_kod": "", "ceza_kodu": "", "ceza_nedeni": "", "miktar": 0}]
            for satir in satirlar:
                self.tablo.insert("", tk.END, values=(
                    ih["fis_no"], satir.get("vergi_turu_kod", ""), satir.get("ceza_kodu", ""),
                    satir.get("ceza_nedeni", ""), "", satir.get("miktar", 0),
                    ih.get("duzenleme_tarihi", ""), ih.get("teblig_tarihi", ""),
                ))
                eklenen += 1

        if eklenen == 0:
            hata_goster(self, "Yapistirilan metinden ihbarname/ceza satiri bulunamadi. "
                               "Satirlari elle ekleyebilirsiniz.")
        else:
            bilgi_goster(self, f"{eklenen} satir tabloya eklendi. 'Donem' alanlarini doldurmayi unutmayin.")

    # -- tablo --
    def _satir_ekle(self):
        self.tablo.insert("", tk.END, values=("", "", "", "", "", 0, "", ""))

    def _satir_sil(self):
        for item in self.tablo.selection():
            self.tablo.delete(item)

    # -- kaydet --
    def _kaydet(self):
        if not self.ad_unvan.get().strip():
            hata_goster(self, "Mukellef Ad Soyad / Unvan alani bos olamaz.")
            return
        satirlar = [self.tablo.item(i, "values") for i in self.tablo.get_children()]
        if not satirlar:
            hata_goster(self, "Kaydedilecek ihbarname/ceza satiri yok.")
            return

        for s in satirlar:
            if not str(s[0]).strip():
                hata_goster(self, "Bos 'Ihbarname Fis No' alani olan satir var.")
                return
            try:
                float(str(s[5]).replace(",", "."))
            except ValueError:
                hata_goster(self, f"Gecersiz miktar: {s[5]}")
                return

        if not onay_iste(self, f"{len(satirlar)} satir kaydedilecek. Onayliyor musunuz?"):
            return

        mukellef_id = db.mukellef_bul_veya_olustur(
            self.ad_unvan.get().strip(), self.vkn_tckn.get().strip(),
            self.adres.get().strip(), self.telefon.get().strip(),
        )

        # Ayni fis_no'ya sahip satirlari tek bir ihbarname altinda topla
        ihbarname_id_cache = {}
        for s in satirlar:
            fis_no, vergi_turu, ceza_kodu, ceza_nedeni, donem, miktar, duzenleme, teblig = s
            fis_no = str(fis_no).strip()
            if fis_no not in ihbarname_id_cache:
                ihbarname_id_cache[fis_no] = db.ihbarname_ekle(
                    mukellef_id, fis_no, str(duzenleme).strip(), str(teblig).strip(),
                    self._dilekce_onay_zamani,
                )
            db.ceza_satiri_ekle(
                ihbarname_id_cache[fis_no], str(vergi_turu).strip(), str(ceza_kodu).strip(),
                str(ceza_nedeni).strip(), str(donem).strip(), float(str(miktar).replace(",", ".")),
            )

        bilgi_goster(self, f"Kayit tamamlandi. {len(ihbarname_id_cache)} ihbarname, "
                            f"{len(satirlar)} ceza satiri eklendi.")
        self._formu_temizle()
