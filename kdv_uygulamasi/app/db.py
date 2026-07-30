"""SQLite veritabani katmani: sema, CRUD ve yedekleme.

Veri modeli:
    mukellefler       -> incelenen mukellef
    incelemeler       -> bir mukellefe ait KDV inceleme dosyasi
    inceleme_yillari  -> dosyanin kapsadigi her yil
    beyan_degerleri   -> yil basina 52 satir x 12 ay beyan verisi
    elestiri_degerleri-> yil basina donem donem inceleme tespitleri
"""
import json
import os
import shutil
import sqlite3
from datetime import datetime

from .satirlar import VERI_KODLARI, varsayilan_kdv_orani

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_DIR = os.path.join(BASE_DIR, "veritabani")
DB_PATH = os.path.join(DB_DIR, "kdv.db")
YEDEK_DIR = os.path.join(BASE_DIR, "yedekler")

SCHEMA = """
CREATE TABLE IF NOT EXISTS mukellefler (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ad_unvan TEXT NOT NULL,
    vkn_tckn TEXT,
    adres TEXT,
    vergi_dairesi TEXT
);
CREATE INDEX IF NOT EXISTS idx_mukellef_ad ON mukellefler(ad_unvan);

CREATE TABLE IF NOT EXISTS incelemeler (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    mukellef_id INTEGER NOT NULL REFERENCES mukellefler(id),
    ad TEXT NOT NULL,
    notlar TEXT,
    devreden_baslangic REAL,
    olusturma_tarihi TEXT,
    guncelleme_tarihi TEXT
);
CREATE INDEX IF NOT EXISTS idx_inceleme_mukellef ON incelemeler(mukellef_id);

CREATE TABLE IF NOT EXISTS inceleme_yillari (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    inceleme_id INTEGER NOT NULL REFERENCES incelemeler(id) ON DELETE CASCADE,
    yil INTEGER NOT NULL,
    ay_sayisi INTEGER NOT NULL DEFAULT 12,
    rapor_tarihi TEXT,
    UNIQUE (inceleme_id, yil)
);

CREATE TABLE IF NOT EXISTS beyan_degerleri (
    yil_id INTEGER NOT NULL REFERENCES inceleme_yillari(id) ON DELETE CASCADE,
    satir_kodu TEXT NOT NULL,
    degerler TEXT NOT NULL,
    PRIMARY KEY (yil_id, satir_kodu)
);

CREATE TABLE IF NOT EXISTS elestiri_degerleri (
    yil_id INTEGER NOT NULL REFERENCES inceleme_yillari(id) ON DELETE CASCADE,
    alan TEXT NOT NULL,
    degerler TEXT NOT NULL,
    PRIMARY KEY (yil_id, alan)
);
"""

ELESTIRI_ALAN_KODLARI = ["matrah_ilave", "hesaplanan_kdv_ilave", "devir_cikar",
                         "indirim_cikar", "yuklenilen_cikar", "kdv_orani",
                         "hesaplanan_otomatik"]

# Mukellef bilgisi girilmeden calisilabilmesi icin kullanilan yer tutucu ad
ADSIZ_MUKELLEF = "(Adsız Mükellef)"


def _baglan():
    os.makedirs(DB_DIR, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


# Sema sonradan genisletildiginde eski veritabanlarina eklenecek kolonlar
_EK_KOLONLAR = [
    ("mukellefler", "vergi_dairesi", "TEXT"),
    ("inceleme_yillari", "rapor_tarihi", "TEXT"),
]


def init_db():
    conn = _baglan()
    try:
        conn.executescript(SCHEMA)
        # Onceki surumlerde olusmus veritabanlari icin eksik kolonlari ekle
        for tablo, kolon, tur in _EK_KOLONLAR:
            mevcut = {r["name"] for r in conn.execute(f"PRAGMA table_info({tablo})")}
            if kolon not in mevcut:
                conn.execute(f"ALTER TABLE {tablo} ADD COLUMN {kolon} {tur}")
        conn.commit()
    finally:
        conn.close()


def _simdi():
    return datetime.now().strftime("%d.%m.%Y %H:%M")


# ---------------------------------------------------------------- mukellefler
def mukellef_ekle(ad_unvan, vkn_tckn="", adres=""):
    conn = _baglan()
    try:
        cur = conn.execute(
            "INSERT INTO mukellefler (ad_unvan, vkn_tckn, adres) VALUES (?, ?, ?)",
            (ad_unvan.strip(), (vkn_tckn or "").strip(), (adres or "").strip()))
        conn.commit()
        return cur.lastrowid
    finally:
        conn.close()


def mukellefleri_listele():
    conn = _baglan()
    try:
        return [dict(r) for r in conn.execute(
            "SELECT * FROM mukellefler ORDER BY ad_unvan COLLATE NOCASE")]
    finally:
        conn.close()


def mukellef_guncelle(mukellef_id, ad_unvan=None, vkn_tckn=None, adres=None,
                      vergi_dairesi=None):
    """Mukellef bilgilerini gunceller; bos birakilan alanlara dokunulmaz."""
    conn = _baglan()
    try:
        if ad_unvan is not None:
            ad = ad_unvan.strip() or ADSIZ_MUKELLEF
            conn.execute("UPDATE mukellefler SET ad_unvan = ? WHERE id = ?", (ad, mukellef_id))
        if vkn_tckn is not None:
            conn.execute("UPDATE mukellefler SET vkn_tckn = ? WHERE id = ?",
                         (vkn_tckn.strip(), mukellef_id))
        if adres is not None:
            conn.execute("UPDATE mukellefler SET adres = ? WHERE id = ?",
                         (adres.strip(), mukellef_id))
        if vergi_dairesi is not None:
            conn.execute("UPDATE mukellefler SET vergi_dairesi = ? WHERE id = ?",
                         (vergi_dairesi.strip(), mukellef_id))
        conn.commit()
    finally:
        conn.close()


def mukellef_sil(mukellef_id):
    conn = _baglan()
    try:
        adet = conn.execute("SELECT COUNT(*) FROM incelemeler WHERE mukellef_id = ?",
                            (mukellef_id,)).fetchone()[0]
        if adet:
            raise ValueError("Bu mükellefe ait inceleme dosyaları var; önce onları silin.")
        conn.execute("DELETE FROM mukellefler WHERE id = ?", (mukellef_id,))
        conn.commit()
    finally:
        conn.close()


# ---------------------------------------------------------------- incelemeler
def inceleme_ekle(mukellef_id, ad, notlar=""):
    conn = _baglan()
    try:
        cur = conn.execute(
            "INSERT INTO incelemeler (mukellef_id, ad, notlar, olusturma_tarihi, "
            "guncelleme_tarihi) VALUES (?, ?, ?, ?, ?)",
            (mukellef_id, ad.strip(), (notlar or "").strip(), _simdi(), _simdi()))
        conn.commit()
        return cur.lastrowid
    finally:
        conn.close()


def incelemeleri_listele(mukellef_id=None):
    conn = _baglan()
    try:
        sorgu = ("SELECT i.*, m.ad_unvan, m.vkn_tckn FROM incelemeler i "
                 "JOIN mukellefler m ON m.id = i.mukellef_id")
        params = ()
        if mukellef_id:
            sorgu += " WHERE i.mukellef_id = ?"
            params = (mukellef_id,)
        sorgu += " ORDER BY i.id DESC"
        kayitlar = []
        for r in conn.execute(sorgu, params):
            kayit = dict(r)
            kayit["yillar"] = [row["yil"] for row in conn.execute(
                "SELECT yil FROM inceleme_yillari WHERE inceleme_id = ? ORDER BY yil",
                (kayit["id"],))]
            kayitlar.append(kayit)
        return kayitlar
    finally:
        conn.close()


def inceleme_sil(inceleme_id):
    conn = _baglan()
    try:
        yil_idleri = [r["id"] for r in conn.execute(
            "SELECT id FROM inceleme_yillari WHERE inceleme_id = ?", (inceleme_id,))]
        for yid in yil_idleri:
            conn.execute("DELETE FROM beyan_degerleri WHERE yil_id = ?", (yid,))
            conn.execute("DELETE FROM elestiri_degerleri WHERE yil_id = ?", (yid,))
        conn.execute("DELETE FROM inceleme_yillari WHERE inceleme_id = ?", (inceleme_id,))
        conn.execute("DELETE FROM incelemeler WHERE id = ?", (inceleme_id,))
        conn.commit()
    finally:
        conn.close()


def inceleme_guncelle(inceleme_id, ad=None, notlar=None, devreden_baslangic=None):
    conn = _baglan()
    try:
        if ad is not None:
            conn.execute("UPDATE incelemeler SET ad = ? WHERE id = ?", (ad.strip(), inceleme_id))
        if notlar is not None:
            conn.execute("UPDATE incelemeler SET notlar = ? WHERE id = ?", (notlar, inceleme_id))
        if devreden_baslangic is not None:
            conn.execute("UPDATE incelemeler SET devreden_baslangic = ? WHERE id = ?",
                         (devreden_baslangic, inceleme_id))
        conn.execute("UPDATE incelemeler SET guncelleme_tarihi = ? WHERE id = ?",
                     (_simdi(), inceleme_id))
        conn.commit()
    finally:
        conn.close()


# --------------------------------------------------------------------- yillar
def yil_ekle(inceleme_id, yil, ay_sayisi=12):
    conn = _baglan()
    try:
        var = conn.execute("SELECT id FROM inceleme_yillari WHERE inceleme_id = ? AND yil = ?",
                           (inceleme_id, yil)).fetchone()
        if var:
            return var["id"]
        cur = conn.execute(
            "INSERT INTO inceleme_yillari (inceleme_id, yil, ay_sayisi) VALUES (?, ?, ?)",
            (inceleme_id, yil, ay_sayisi))
        yil_id = cur.lastrowid
        # Bos beyan ve elestiri satirlarini olustur
        for kod in VERI_KODLARI:
            conn.execute("INSERT INTO beyan_degerleri (yil_id, satir_kodu, degerler) "
                         "VALUES (?, ?, ?)", (yil_id, kod, json.dumps([0.0] * 12)))
        for alan in ELESTIRI_ALAN_KODLARI:
            if alan == "kdv_orani":
                varsayilan = [varsayilan_kdv_orani(yil, ay + 1) for ay in range(12)]
            elif alan == "hesaplanan_otomatik":
                varsayilan = [True] * 12
            else:
                varsayilan = [0.0] * 12
            conn.execute("INSERT INTO elestiri_degerleri (yil_id, alan, degerler) "
                         "VALUES (?, ?, ?)", (yil_id, alan, json.dumps(varsayilan)))
        conn.commit()
        return yil_id
    finally:
        conn.close()


def yil_guncelle(yil_id, yeni_yil):
    """Bir yil kaydinin yilini degistirir (otomatik eklenen yili duzeltmek icin).

    KDV orani varsayilanlari yila bagli oldugundan, kullanici orani elle
    degistirmemisse oranlar yeni yila gore tazelenir.
    """
    yeni_yil = int(yeni_yil)
    if not 2000 <= yeni_yil <= 2100:
        raise ValueError("Yıl 2000-2100 aralığında olmalıdır.")
    conn = _baglan()
    try:
        kayit = conn.execute("SELECT inceleme_id, yil FROM inceleme_yillari WHERE id = ?",
                             (yil_id,)).fetchone()
        if kayit is None:
            raise ValueError("Yıl kaydı bulunamadı.")
        if kayit["yil"] == yeni_yil:
            return
        cakisma = conn.execute(
            "SELECT id FROM inceleme_yillari WHERE inceleme_id = ? AND yil = ? AND id != ?",
            (kayit["inceleme_id"], yeni_yil, yil_id)).fetchone()
        if cakisma:
            raise ValueError(f"{yeni_yil} yılı bu dosyada zaten var.")
        eski_varsayilan = [varsayilan_kdv_orani(kayit["yil"], a + 1) for a in range(12)]
        satir = conn.execute("SELECT degerler FROM elestiri_degerleri WHERE yil_id = ? AND "
                             "alan = 'kdv_orani'", (yil_id,)).fetchone()
        conn.execute("UPDATE inceleme_yillari SET yil = ? WHERE id = ?", (yeni_yil, yil_id))
        # Oranlar elle degistirilmemisse yeni yilin varsayilanina cek
        if satir and json.loads(satir["degerler"]) == eski_varsayilan:
            yeni = [varsayilan_kdv_orani(yeni_yil, a + 1) for a in range(12)]
            conn.execute("UPDATE elestiri_degerleri SET degerler = ? WHERE yil_id = ? AND "
                         "alan = 'kdv_orani'", (json.dumps(yeni), yil_id))
        conn.commit()
    finally:
        conn.close()


def varsayilan_calisma():
    """Uygulama acilir acilmaz kullanilabilecek bir calisma dondurur.

    Kayit yoksa adsiz bir mukellef, "Çalışma" adli bir dosya ve bir yil
    olusturur. Boylece kullanici once mukellef/dosya/yil tanimlamak zorunda
    kalmadan dogrudan beyan yapistirabilir; bu bilgileri sonradan
    doldurabilir veya degistirebilir.
    """
    conn = _baglan()
    try:
        son = conn.execute("SELECT id FROM incelemeler ORDER BY id DESC LIMIT 1").fetchone()
        if son:
            return son["id"]
    finally:
        conn.close()
    mukellef_id = mukellef_ekle(ADSIZ_MUKELLEF)
    # Yil olusturulmaz: yil, yapistirilan sorgunun kunyesinden ya da kullanicinin
    # sectigi degerden belirlenir. Bos bir yil kaydi, devir zinciri denetiminde
    # yanlis bulgu uretirdi.
    return inceleme_ekle(mukellef_id, "Çalışma")


def yil_sil(yil_id):
    conn = _baglan()
    try:
        conn.execute("DELETE FROM beyan_degerleri WHERE yil_id = ?", (yil_id,))
        conn.execute("DELETE FROM elestiri_degerleri WHERE yil_id = ?", (yil_id,))
        conn.execute("DELETE FROM inceleme_yillari WHERE id = ?", (yil_id,))
        conn.commit()
    finally:
        conn.close()


def ay_sayisi_ayarla(yil_id, ay_sayisi):
    conn = _baglan()
    try:
        conn.execute("UPDATE inceleme_yillari SET ay_sayisi = ? WHERE id = ?",
                     (max(1, min(int(ay_sayisi), 12)), yil_id))
        conn.commit()
    finally:
        conn.close()


# ------------------------------------------------------------- beyan/elestiri
def beyan_kaydet(yil_id, degerler):
    """degerler: {satir_kodu: [12 deger]}"""
    conn = _baglan()
    try:
        for kod, dizi in degerler.items():
            if kod not in VERI_KODLARI:
                continue
            temiz = [float(d or 0) for d in (list(dizi) + [0.0] * 12)[:12]]
            conn.execute("INSERT INTO beyan_degerleri (yil_id, satir_kodu, degerler) "
                         "VALUES (?, ?, ?) ON CONFLICT(yil_id, satir_kodu) DO UPDATE "
                         "SET degerler = excluded.degerler", (yil_id, kod, json.dumps(temiz)))
        conn.commit()
    finally:
        conn.close()


def beyan_hucre_guncelle(yil_id, satir_kodu, ay, deger):
    """Tek bir hucreyi gunceller (ay: 0-11)."""
    if satir_kodu not in VERI_KODLARI:
        raise ValueError(f"Bilinmeyen satır kodu: {satir_kodu}")
    if not 0 <= int(ay) <= 11:
        raise ValueError("Ay 1-12 aralığında olmalıdır.")
    conn = _baglan()
    try:
        row = conn.execute("SELECT degerler FROM beyan_degerleri WHERE yil_id = ? AND "
                           "satir_kodu = ?", (yil_id, satir_kodu)).fetchone()
        dizi = json.loads(row["degerler"]) if row else [0.0] * 12
        dizi = (dizi + [0.0] * 12)[:12]
        dizi[int(ay)] = float(deger or 0)
        conn.execute("INSERT INTO beyan_degerleri (yil_id, satir_kodu, degerler) "
                     "VALUES (?, ?, ?) ON CONFLICT(yil_id, satir_kodu) DO UPDATE "
                     "SET degerler = excluded.degerler", (yil_id, satir_kodu, json.dumps(dizi)))
        conn.commit()
    finally:
        conn.close()


def beyan_satir_guncelle(yil_id, satir_kodu, dizi):
    """Bir satirin 12 aylik degerini birden gunceller (tek satir yapistirma)."""
    if satir_kodu not in VERI_KODLARI:
        raise ValueError(f"Bilinmeyen satır kodu: {satir_kodu}")
    beyan_kaydet(yil_id, {satir_kodu: dizi})


def elestiri_kaydet(yil_id, alanlar):
    conn = _baglan()
    try:
        for alan, dizi in alanlar.items():
            if alan not in ELESTIRI_ALAN_KODLARI:
                continue
            liste = (list(dizi) + [None] * 12)[:12]
            if alan == "hesaplanan_otomatik":
                temiz = [bool(d) for d in liste]
            elif alan == "kdv_orani":
                temiz = [None if d in (None, "") else float(d) for d in liste]
            else:
                temiz = [float(d or 0) for d in liste]
            conn.execute("INSERT INTO elestiri_degerleri (yil_id, alan, degerler) "
                         "VALUES (?, ?, ?) ON CONFLICT(yil_id, alan) DO UPDATE "
                         "SET degerler = excluded.degerler", (yil_id, alan, json.dumps(temiz)))
        conn.commit()
    finally:
        conn.close()


def rapor_tarihi_ayarla(yil_id, rapor_tarihi):
    """Sistem sorgusunun uretildigi tarihi yil kaydina yazar."""
    conn = _baglan()
    try:
        conn.execute("UPDATE inceleme_yillari SET rapor_tarihi = ? WHERE id = ?",
                     ((rapor_tarihi or "").strip(), yil_id))
        conn.commit()
    finally:
        conn.close()


def beyan_temizle(yil_id):
    """Bir yilin tum beyan satirlarini sifirlar; satirlar silinmez, bosaltilir."""
    conn = _baglan()
    try:
        bos = json.dumps([0.0] * 12)
        for kod in VERI_KODLARI:
            conn.execute("INSERT INTO beyan_degerleri (yil_id, satir_kodu, degerler) "
                         "VALUES (?, ?, ?) ON CONFLICT(yil_id, satir_kodu) DO UPDATE "
                         "SET degerler = excluded.degerler", (yil_id, kod, bos))
        conn.commit()
    finally:
        conn.close()


def elestiri_temizle(yil_id):
    """Bir yilin inceleme tespitlerini sifirlar; KDV oranlari yila gore tazelenir."""
    conn = _baglan()
    try:
        kayit = conn.execute("SELECT yil FROM inceleme_yillari WHERE id = ?",
                             (yil_id,)).fetchone()
        yil = kayit["yil"] if kayit else datetime.now().year
        for alan in ELESTIRI_ALAN_KODLARI:
            if alan == "kdv_orani":
                deger = [varsayilan_kdv_orani(yil, a + 1) for a in range(12)]
            elif alan == "hesaplanan_otomatik":
                deger = [True] * 12
            else:
                deger = [0.0] * 12
            conn.execute("INSERT INTO elestiri_degerleri (yil_id, alan, degerler) "
                         "VALUES (?, ?, ?) ON CONFLICT(yil_id, alan) DO UPDATE "
                         "SET degerler = excluded.degerler", (yil_id, alan, json.dumps(deger)))
        conn.commit()
    finally:
        conn.close()


def inceleme_yil_idleri(inceleme_id):
    conn = _baglan()
    try:
        return [r["id"] for r in conn.execute(
            "SELECT id FROM inceleme_yillari WHERE inceleme_id = ? ORDER BY yil",
            (inceleme_id,))]
    finally:
        conn.close()


def inceleme_verisi(inceleme_id):
    """Bir incelemenin tum yillarini hesaplamaya hazir bicimde dondurur."""
    conn = _baglan()
    try:
        inceleme = conn.execute(
            "SELECT i.*, m.ad_unvan, m.vkn_tckn, m.adres, m.vergi_dairesi "
            "FROM incelemeler i "
            "JOIN mukellefler m ON m.id = i.mukellef_id WHERE i.id = ?",
            (inceleme_id,)).fetchone()
        if inceleme is None:
            raise ValueError("İnceleme bulunamadı.")
        yillar = []
        for y in conn.execute("SELECT * FROM inceleme_yillari WHERE inceleme_id = ? "
                              "ORDER BY yil", (inceleme_id,)):
            beyan = {r["satir_kodu"]: json.loads(r["degerler"]) for r in conn.execute(
                "SELECT satir_kodu, degerler FROM beyan_degerleri WHERE yil_id = ?", (y["id"],))}
            for kod in VERI_KODLARI:
                beyan.setdefault(kod, [0.0] * 12)
            elestiri = {r["alan"]: json.loads(r["degerler"]) for r in conn.execute(
                "SELECT alan, degerler FROM elestiri_degerleri WHERE yil_id = ?", (y["id"],))}
            for alan in ELESTIRI_ALAN_KODLARI:
                if alan == "hesaplanan_otomatik":
                    elestiri.setdefault(alan, [True] * 12)
                elif alan == "kdv_orani":
                    elestiri.setdefault(alan, [varsayilan_kdv_orani(y["yil"], a + 1)
                                               for a in range(12)])
                else:
                    elestiri.setdefault(alan, [0.0] * 12)
            yillar.append({"yil_id": y["id"], "yil": y["yil"], "ay_sayisi": y["ay_sayisi"],
                           "rapor_tarihi": y["rapor_tarihi"],
                           "beyan": beyan, "elestiri": elestiri})
        return {"inceleme": dict(inceleme), "yillar": yillar}
    finally:
        conn.close()


# ------------------------------------------------------------------- yedekler
def yedek_al():
    os.makedirs(YEDEK_DIR, exist_ok=True)
    hedef = os.path.join(YEDEK_DIR, f"kdv_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db")
    shutil.copy2(DB_PATH, hedef)
    return hedef


def yedekleri_listele():
    if not os.path.isdir(YEDEK_DIR):
        return []
    return sorted((d for d in os.listdir(YEDEK_DIR) if d.endswith(".db")), reverse=True)


def yedekten_geri_yukle(dosya_adi):
    kaynak = os.path.join(YEDEK_DIR, os.path.basename(dosya_adi))
    if not os.path.isfile(kaynak):
        raise ValueError("Yedek dosyası bulunamadı.")
    shutil.copy2(kaynak, DB_PATH)
