"""SQLite veritabani katmani: sema, varsayilan vergi kodlari ve sorgular.

Her Excel yuklemesi 'yuklemeler' tablosunda bir kayit olur; o dosyadan okunan
satirlar 'kayitlar' tablosunda yukleme_id ile baglanir. Boylece gecmis hicbir
zaman silinmez; eski yuklemeler tekrar sorgulanabilir.
"""
import json
import os
import sqlite3

from .tarih_util import simdi_iso

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_DIR = os.path.join(BASE_DIR, "veritabani")
DB_PATH = os.path.join(DB_DIR, "tahakkuk.db")
VARSAYILAN_KOD_DOSYA = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                    "vergi_kodlari_varsayilan.json")

SCHEMA = """
CREATE TABLE IF NOT EXISTS yuklemeler (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    dosya_adi TEXT NOT NULL,
    yukleme_zamani TEXT NOT NULL,
    satir_sayisi INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS kayitlar (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    yukleme_id INTEGER NOT NULL REFERENCES yuklemeler(id) ON DELETE CASCADE,
    vergi_kimlik_no TEXT,
    tahakkuk_fis_no TEXT,
    islem_turu TEXT,
    thk_turu TEXT,
    vergi_donemi TEXT,
    vergi_kodu TEXT,
    plaka_sasi TEXT,
    odenecek_tutar REAL NOT NULL DEFAULT 0
);
CREATE INDEX IF NOT EXISTS idx_kayit_yukleme ON kayitlar(yukleme_id);
CREATE INDEX IF NOT EXISTS idx_kayit_vkn ON kayitlar(vergi_kimlik_no);
CREATE INDEX IF NOT EXISTS idx_kayit_kod ON kayitlar(vergi_kodu);
CREATE INDEX IF NOT EXISTS idx_kayit_fis ON kayitlar(tahakkuk_fis_no);

CREATE TABLE IF NOT EXISTS vergi_kodlari (
    kod TEXT PRIMARY KEY,
    ad TEXT
);
"""


def get_connection():
    os.makedirs(DB_DIR, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    conn = get_connection()
    try:
        conn.executescript(SCHEMA)
        # Vergi kodu adlari bos ise varsayilan listeyi yukle (kullanici sonradan
        # duzenleyebilir / ekleyebilir).
        var = conn.execute("SELECT COUNT(*) FROM vergi_kodlari").fetchone()[0]
        if var == 0 and os.path.isfile(VARSAYILAN_KOD_DOSYA):
            with open(VARSAYILAN_KOD_DOSYA, encoding="utf-8") as f:
                ciftler = json.load(f)
            conn.executemany(
                "INSERT OR IGNORE INTO vergi_kodlari (kod, ad) VALUES (?, ?)",
                [(str(k).strip(), str(a).strip()) for k, a in ciftler],
            )
        conn.commit()
    finally:
        conn.close()


# ---------------------------------------------------------------- vergi kodu
def vergi_kodu_adlari():
    conn = get_connection()
    try:
        return {r["kod"]: r["ad"] for r in conn.execute("SELECT kod, ad FROM vergi_kodlari")}
    finally:
        conn.close()


def vergi_kodu_ad_ekle(kod, ad):
    conn = get_connection()
    try:
        conn.execute(
            "INSERT INTO vergi_kodlari (kod, ad) VALUES (?, ?) "
            "ON CONFLICT(kod) DO UPDATE SET ad = excluded.ad",
            (str(kod).strip(), str(ad).strip()),
        )
        conn.commit()
    finally:
        conn.close()


# ---------------------------------------------------------------- yukleme
def yukleme_ekle(dosya_adi, satirlar):
    """Bir Excel yuklemesini ve satirlarini kaydeder. yukleme_id dondurur.

    satirlar: dict listesi; anahtarlar kayitlar tablosu kolonlariyla esler.
    """
    conn = get_connection()
    try:
        cur = conn.execute(
            "INSERT INTO yuklemeler (dosya_adi, yukleme_zamani, satir_sayisi) VALUES (?, ?, ?)",
            (dosya_adi, simdi_iso(), len(satirlar)),
        )
        yukleme_id = cur.lastrowid
        conn.executemany(
            "INSERT INTO kayitlar "
            "(yukleme_id, vergi_kimlik_no, tahakkuk_fis_no, islem_turu, thk_turu, "
            " vergi_donemi, vergi_kodu, plaka_sasi, odenecek_tutar) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            [
                (yukleme_id, s.get("vergi_kimlik_no"), s.get("tahakkuk_fis_no"),
                 s.get("islem_turu"), s.get("thk_turu"), s.get("vergi_donemi"),
                 s.get("vergi_kodu"), s.get("plaka_sasi"), s.get("odenecek_tutar", 0.0))
                for s in satirlar
            ],
        )
        conn.commit()
        return yukleme_id
    finally:
        conn.close()


def yuklemeleri_listele():
    conn = get_connection()
    try:
        return [dict(r) for r in conn.execute(
            "SELECT id, dosya_adi, yukleme_zamani, satir_sayisi "
            "FROM yuklemeler ORDER BY id DESC"
        )]
    finally:
        conn.close()


def son_yukleme_id():
    conn = get_connection()
    try:
        r = conn.execute("SELECT id FROM yuklemeler ORDER BY id DESC LIMIT 1").fetchone()
        return r["id"] if r else None
    finally:
        conn.close()


def yukleme_sil(yukleme_id):
    conn = get_connection()
    try:
        conn.execute("DELETE FROM kayitlar WHERE yukleme_id = ?", (yukleme_id,))
        conn.execute("DELETE FROM yuklemeler WHERE id = ?", (yukleme_id,))
        conn.commit()
    finally:
        conn.close()


# ---------------------------------------------------------------- sorgu
def kayitlari_sorgula(yukleme_id, vkn="", vergi_kodu="", tutar_min=None,
                      tutar_max=None, siralama="fis"):
    """Bir yuklemedeki kayitlari filtreleyip siralar.

    siralama:
      'fis'         -> fis bazinda grupli, fisin en yuksek tutarina gore azalan
      'tutar_azalan'-> satir tutari azalan
      'tutar_artan' -> satir tutari artan
      'vkn'         -> vergi kimlik no'ya gore

    Tutar filtresi satir bazinda uygulanir. 'fis' siralamasinda ise sonuc
    fis butunlugu korunarak gelir: filtreye uyan satiri olan her fisin TUM
    satirlari dahil edilir ve fisler en yuksek tutara gore siralanir.
    """
    conn = get_connection()
    try:
        kosul = ["yukleme_id = ?"]
        param = [yukleme_id]
        if vkn:
            kosul.append("vergi_kimlik_no LIKE ?")
            param.append(f"%{vkn.strip()}%")
        if vergi_kodu:
            kosul.append("vergi_kodu LIKE ?")
            param.append(f"%{vergi_kodu.strip()}%")
        if tutar_min is not None:
            kosul.append("odenecek_tutar >= ?")
            param.append(tutar_min)
        if tutar_max is not None:
            kosul.append("odenecek_tutar <= ?")
            param.append(tutar_max)
        nere = " AND ".join(kosul)

        if siralama == "fis":
            # Filtreye uyan fisleri bul, sonra o fislerin TUM satirlarini getir.
            eslesenler = conn.execute(
                f"SELECT DISTINCT tahakkuk_fis_no FROM kayitlar WHERE {nere}", param
            ).fetchall()
            fisler = [r["tahakkuk_fis_no"] for r in eslesenler]
            if not fisler:
                return []
            isaret = ",".join("?" * len(fisler))
            satirlar = conn.execute(
                f"SELECT * FROM kayitlar WHERE yukleme_id = ? "
                f"AND tahakkuk_fis_no IN ({isaret})",
                [yukleme_id, *fisler],
            ).fetchall()
            # Her fisin en yuksek tutarini hesapla, fisleri buna gore sirala.
            fis_max = {}
            for s in satirlar:
                f = s["tahakkuk_fis_no"]
                fis_max[f] = max(fis_max.get(f, float("-inf")), s["odenecek_tutar"] or 0)
            satirlar = sorted(
                satirlar,
                key=lambda s: (-fis_max.get(s["tahakkuk_fis_no"], 0),
                               s["tahakkuk_fis_no"] or "",
                               -(s["odenecek_tutar"] or 0)),
            )
            return [dict(s) for s in satirlar]

        sirala_sql = {
            "tutar_azalan": "odenecek_tutar DESC, tahakkuk_fis_no",
            "tutar_artan": "odenecek_tutar ASC, tahakkuk_fis_no",
            "vkn": "vergi_kimlik_no, tahakkuk_fis_no, odenecek_tutar DESC",
        }.get(siralama, "tahakkuk_fis_no, odenecek_tutar DESC")
        satirlar = conn.execute(
            f"SELECT * FROM kayitlar WHERE {nere} ORDER BY {sirala_sql}", param
        ).fetchall()
        return [dict(s) for s in satirlar]
    finally:
        conn.close()


def yukleme_ozeti(yukleme_id):
    """Bir yukleme icin toplam satir, fis, mukellef ve tutar ozeti."""
    conn = get_connection()
    try:
        r = conn.execute(
            "SELECT COUNT(*) AS satir, "
            "COUNT(DISTINCT tahakkuk_fis_no) AS fis, "
            "COUNT(DISTINCT vergi_kimlik_no) AS mukellef, "
            "COALESCE(SUM(odenecek_tutar), 0) AS toplam "
            "FROM kayitlar WHERE yukleme_id = ?",
            (yukleme_id,),
        ).fetchone()
        return dict(r) if r else {"satir": 0, "fis": 0, "mukellef": 0, "toplam": 0}
    finally:
        conn.close()
