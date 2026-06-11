"""Tkinter icin paylasilan yardimci widget'lar."""
import tkinter as tk
from tkinter import ttk


class AramaKutusu(ttk.Frame):
    """3+ karakter yazildiginda canli oneri listesi gosteren arama kutusu.

    arama_fn(metin) -> liste of (etiket, deger)
    secim_callback(deger, etiket) -> secim yapildiginda cagrilir
    """

    def __init__(self, parent, arama_fn, secim_callback, esik=3, genislik=50, **kwargs):
        super().__init__(parent, **kwargs)
        self.arama_fn = arama_fn
        self.secim_callback = secim_callback
        self.esik = esik

        self.degisken = tk.StringVar()
        self.entry = ttk.Entry(self, textvariable=self.degisken, width=genislik)
        self.entry.pack(fill="x")
        self.degisken.trace_add("write", self._degisti)

        self.liste = tk.Listbox(self, height=6)
        self.liste.bind("<<ListboxSelect>>", self._secildi)
        self._oneriler = []
        self._gosteriliyor = False

    def _degisti(self, *_):
        metin = self.degisken.get().strip()
        if len(metin) < self.esik:
            self._gizle()
            return
        self._oneriler = self.arama_fn(metin)
        if not self._oneriler:
            self._gizle()
            return
        self.liste.delete(0, tk.END)
        for etiket, _deger in self._oneriler:
            self.liste.insert(tk.END, etiket)
        if not self._gosteriliyor:
            self.liste.pack(fill="x")
            self._gosteriliyor = True

    def _secildi(self, _event=None):
        secim = self.liste.curselection()
        if not secim:
            return
        etiket, deger = self._oneriler[secim[0]]
        self.degisken.set(etiket)
        self._gizle()
        self.secim_callback(deger, etiket)

    def _gizle(self):
        if self._gosteriliyor:
            self.liste.pack_forget()
            self._gosteriliyor = False

    def temizle(self):
        self.degisken.set("")
        self._gizle()


class DuzenlenebilirTablo(ttk.Treeview):
    """Cift tiklamayla hucre duzenlemeye izin veren Treeview.

    duzenlenebilir_kolonlar: kolon id'lerinin kumesi
    combo_degerleri: {kolon_id: liste-of-str} -> Combobox olarak duzenlenir
    degisti_callback(item_id, kolon_id, yeni_deger)
    """

    def __init__(self, parent, duzenlenebilir_kolonlar=None, combo_degerleri=None,
                 degisti_callback=None, **kwargs):
        super().__init__(parent, **kwargs)
        self.duzenlenebilir_kolonlar = duzenlenebilir_kolonlar or set()
        self.combo_degerleri = combo_degerleri or {}
        self.degisti_callback = degisti_callback
        self.bind("<Double-1>", self._cift_tiklama)
        self._duzenleyici = None

    def _cift_tiklama(self, event):
        if self._duzenleyici is not None:
            self._duzenleyici.destroy()
            self._duzenleyici = None

        bolge = self.identify("region", event.x, event.y)
        if bolge != "cell":
            return
        satir_id = self.identify_row(event.y)
        kolon_id = self.identify_column(event.x)
        if not satir_id or not kolon_id:
            return
        kolon_adi = self.column(kolon_id, "id") or self["columns"][int(kolon_id[1:]) - 1]
        if kolon_adi not in self.duzenlenebilir_kolonlar:
            return

        x, y, genislik, yukseklik = self.bbox(satir_id, kolon_id)
        mevcut_deger = self.set(satir_id, kolon_adi)

        if kolon_adi in self.combo_degerleri:
            widget = ttk.Combobox(self, values=self.combo_degerleri[kolon_adi], state="readonly")
            widget.set(mevcut_deger)
        else:
            widget = ttk.Entry(self)
            widget.insert(0, mevcut_deger)
            widget.select_range(0, tk.END)

        widget.place(x=x, y=y, width=genislik, height=yukseklik)
        widget.focus_set()
        self._duzenleyici = widget

        def kaydet(_event=None):
            yeni_deger = widget.get()
            self.set(satir_id, kolon_adi, yeni_deger)
            widget.destroy()
            self._duzenleyici = None
            if self.degisti_callback:
                self.degisti_callback(satir_id, kolon_adi, yeni_deger)

        widget.bind("<Return>", kaydet)
        widget.bind("<FocusOut>", kaydet)
        if isinstance(widget, ttk.Combobox):
            widget.bind("<<ComboboxSelected>>", kaydet)


def hata_goster(parent, mesaj):
    from tkinter import messagebox
    messagebox.showerror("Hata", mesaj, parent=parent)


def bilgi_goster(parent, mesaj):
    from tkinter import messagebox
    messagebox.showinfo("Bilgi", mesaj, parent=parent)


def onay_iste(parent, mesaj):
    from tkinter import messagebox
    return messagebox.askyesno("Onay", mesaj, parent=parent)
