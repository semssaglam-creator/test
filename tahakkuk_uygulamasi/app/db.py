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
    # timeout: kilitliyse hata vermek yerine bu kadar saniye bekle.
    conn = sqlite3.connect(DB_PATH, timeout=30)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    # WAL: okuyucular yazaru, yazar okuyuculari kilitlemez -> "database is locked"
    # hatalarini buyuk olcude onler. busy_timeout: kilit varsa bekle (ms).
    conn.execute("PRAGMA busy_timeout = 30000")
    try:
        conn.execute("PRAGMA journal_mode = WAL")
    except sqlite3.OperationalError:
        pass  # WAL desteklenmeyen (ag) dosya sisteminde sessizce gec
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
# Grup bazli siralamalar: (gruplama_kolonu, grup_metrigi) eslemesi.
#   'fis'            -> fis bazinda, fisin EN YUKSEK satir tutarina gore azalan
#   'mukellef_toplam'-> mukellef bazinda, mukellefin TOPLAM tutarina gore azalan
_GRUP_SIRALAMA = {
    "fis": ("tahakkuk_fis_no", "max"),
    "mukellef_toplam": ("vergi_kimlik_no", "sum"),
}


def kayitlari_sorgula(yukleme_id, vkn="", vergi_kodu="", tutar_min=None,
                      tutar_max=None, siralama="fis"):
    """Bir yuklemedeki kayitlari filtreleyip siralar. Satir sayisi sinirsizdir.

    siralama:
      'fis'            -> fis bazinda grupli, fisin en yuksek tutarina gore azalan
      'mukellef_toplam'-> mukellef bazinda grupli, toplam tutara gore azalan
      'tutar_azalan'   -> satir tutari azalan
      'tutar_artan'    -> satir tutari artan
      'vkn'            -> vergi kimlik no'ya gore

    Tutar filtresi satir bazinda uygulanir. Grup siralamalarinda sonuc grup
    butunlugu korunarak gelir: filtreye uyan satiri olan her grubun (fis ya da
    mukellef) TUM satirlari dahil edilir ve gruplar metriklerine gore siralanir.
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

        if siralama in _GRUP_SIRALAMA:
            grup_kol, metrik = _GRUP_SIRALAMA[siralama]
            # Filtreye uyan gruplari bul, sonra o gruplarin TUM satirlarini getir.
            eslesenler = conn.execute(
                f"SELECT DISTINCT {grup_kol} FROM kayitlar WHERE {nere}", param
            ).fetchall()
            anahtarlar = [r[grup_kol] for r in eslesenler]
            if not anahtarlar:
                return []
            isaret = ",".join("?" * len(anahtarlar))
            satirlar = conn.execute(
                f"SELECT * FROM kayitlar WHERE yukleme_id = ? "
                f"AND {grup_kol} IN ({isaret})",
                [yukleme_id, *anahtarlar],
            ).fetchall()
            # Her grubun metrigini hesapla (en yuksek tutar veya toplam).
            grup_deger = {}
            for s in satirlar:
                a = s[grup_kol]
                t = s["odenecek_tutar"] or 0
                if metrik == "sum":
                    grup_deger[a] = grup_deger.get(a, 0) + t
                else:
                    grup_deger[a] = max(grup_deger.get(a, float("-inf")), t)
            satirlar = sorted(
                satirlar,
                key=lambda s: (-grup_deger.get(s[grup_kol], 0),
                               s[grup_kol] or "",
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


def karsilastir(a_id, b_id, bazda="vkn"):
    """Iki yuklemeyi (gun) karsilastirir.

    bazda: 'vkn' -> vergi kimlik no bazinda, 'fis' -> tahakkuk fis no bazinda.
    Her anahtar icin iki yuklemedeki toplam tutarlari, farki ve durumu dondurur.
    durum: 'yeni' (yalniz B'de), 'cikan' (yalniz A'da), 'degisti', 'ayni'.
    """
    grup_kol = "tahakkuk_fis_no" if bazda == "fis" else "vergi_kimlik_no"
    conn = get_connection()
    try:
        def topla(yid):
            sonuc = {}
            for r in conn.execute(
                f"SELECT {grup_kol} AS anahtar, "
                f"COALESCE(SUM(odenecek_tutar), 0) AS toplam, "
                f"MAX(vergi_kimlik_no) AS vkn "
                f"FROM kayitlar WHERE yukleme_id = ? GROUP BY {grup_kol}",
                (yid,),
            ):
                sonuc[r["anahtar"]] = {"toplam": r["toplam"], "vkn": r["vkn"]}
            return sonuc

        a = topla(a_id)
        b = topla(b_id)
        satirlar = []
        for anahtar in sorted(set(a) | set(b)):
            ta = a.get(anahtar, {}).get("toplam")
            tb = b.get(anahtar, {}).get("toplam")
            va = ta if ta is not None else 0
            vb = tb if tb is not None else 0
            fark = round(vb - va, 2)
            if ta is None:
                durum = "yeni"
            elif tb is None:
                durum = "cikan"
            elif abs(fark) > 0.005:
                durum = "degisti"
            else:
                durum = "ayni"
            satirlar.append({
                "anahtar": anahtar,
                "vkn": (b.get(anahtar) or a.get(anahtar) or {}).get("vkn", ""),
                "tutar_a": round(va, 2),
                "tutar_b": round(vb, 2),
                "fark": fark,
                "durum": durum,
            })
        # En buyuk mutlak farktan kucuge sirala.
        satirlar.sort(key=lambda s: -abs(s["fark"]))
        return satirlar
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
