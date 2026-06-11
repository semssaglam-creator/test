"""SQLite veritabani katmani: sema olusturma, varsayilan veriler ve CRUD yardimcilari."""
import os
import sqlite3
import shutil
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_DIR = os.path.join(BASE_DIR, "veritabani")
DB_PATH = os.path.join(DB_DIR, "uzlasma.db")
YEDEK_DIR = os.path.join(BASE_DIR, "yedekler")

SCHEMA = """
CREATE TABLE IF NOT EXISTS kurum_bilgileri (
    id INTEGER PRIMARY KEY CHECK (id = 1),
    defterdarlik TEXT NOT NULL DEFAULT '....... Defterdarligi',
    vergi_dairesi TEXT NOT NULL DEFAULT '....... Vergi Dairesi Mudurlugu',
    tutanak_yili INTEGER NOT NULL DEFAULT 0,
    tutanak_sayac INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS mukellefler (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ad_unvan TEXT NOT NULL,
    vkn_tckn TEXT,
    adres TEXT,
    telefon TEXT
);
CREATE INDEX IF NOT EXISTS idx_mukellef_ad ON mukellefler(ad_unvan);
CREATE INDEX IF NOT EXISTS idx_mukellef_vkn ON mukellefler(vkn_tckn);

CREATE TABLE IF NOT EXISTS vergi_turleri (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    kod TEXT NOT NULL UNIQUE,
    ad TEXT,
    aktif INTEGER NOT NULL DEFAULT 1
);

CREATE TABLE IF NOT EXISTS ceza_kodlari (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    kod TEXT NOT NULL UNIQUE,
    aciklama TEXT,
    aktif INTEGER NOT NULL DEFAULT 1
);

CREATE TABLE IF NOT EXISTS ihbarnameler (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    mukellef_id INTEGER NOT NULL REFERENCES mukellefler(id),
    fis_no TEXT NOT NULL,
    duzenleme_tarihi TEXT,
    teblig_tarihi TEXT,
    dilekce_onay_zamani TEXT,
    durum TEXT NOT NULL DEFAULT 'beklemede',
    olusturma_tarihi TEXT
);
CREATE INDEX IF NOT EXISTS idx_ihbarname_fis ON ihbarnameler(fis_no);
CREATE INDEX IF NOT EXISTS idx_ihbarname_mukellef ON ihbarnameler(mukellef_id);

CREATE TABLE IF NOT EXISTS ceza_satirlari (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ihbarname_id INTEGER NOT NULL REFERENCES ihbarnameler(id),
    vergi_turu_kod TEXT,
    ceza_kodu TEXT,
    ceza_nedeni TEXT,
    donem TEXT,
    miktar REAL NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS komisyon_uyeleri (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ad_soyad TEXT NOT NULL,
    unvan TEXT,
    aktif INTEGER NOT NULL DEFAULT 1
);

CREATE TABLE IF NOT EXISTS uzlasma_tutanaklari (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    tutanak_no TEXT,
    mukellef_id INTEGER NOT NULL REFERENCES mukellefler(id),
    sonuc TEXT NOT NULL,
    toplanti_tarih_saat TEXT,
    davet_tarih_saat TEXT,
    notlar TEXT,
    dosya_yolu TEXT,
    olusturma_tarihi TEXT
);

CREATE TABLE IF NOT EXISTS tutanak_kalemleri (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    tutanak_id INTEGER NOT NULL REFERENCES uzlasma_tutanaklari(id),
    ceza_satiri_id INTEGER NOT NULL REFERENCES ceza_satirlari(id),
    indirim_orani REAL NOT NULL DEFAULT 80,
    uzlasilan_tutar REAL NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS tutanak_imzalari (
    tutanak_id INTEGER NOT NULL REFERENCES uzlasma_tutanaklari(id),
    komisyon_uye_id INTEGER NOT NULL REFERENCES komisyon_uyeleri(id),
    PRIMARY KEY (tutanak_id, komisyon_uye_id)
);
"""

VARSAYILAN_VERGI_TURLERI = [
    ("0001", "Gelir Vergisi"),
    ("0003", "Gelir Vergisi (Stopaj)"),
    ("0015", "Katma Deger Vergisi"),
    ("0032", "Damga Vergisi"),
]

VARSAYILAN_CEZA_KODLARI = [
    ("3073", "213 Sayili VUK Ilgili Maddesi Geregince Kesilen Ceza"),
    ("3074", "213 Sayili VUK 353/1 Maddesi Geregince"),
    ("3080", "213 Sayili VUK 341. Maddede Yazili Hallerle Vergi Ziyaina Sebebiyet Verilmesi"),
]


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
        cur = conn.execute("SELECT COUNT(*) FROM kurum_bilgileri")
        if cur.fetchone()[0] == 0:
            conn.execute(
                "INSERT INTO kurum_bilgileri (id, defterdarlik, vergi_dairesi, tutanak_yili, tutanak_sayac) "
                "VALUES (1, ?, ?, ?, 0)",
                ("....... Defterdarligi", "....... Vergi Dairesi Mudurlugu", datetime.now().year),
            )
        cur = conn.execute("SELECT COUNT(*) FROM vergi_turleri")
        if cur.fetchone()[0] == 0:
            conn.executemany(
                "INSERT INTO vergi_turleri (kod, ad) VALUES (?, ?)", VARSAYILAN_VERGI_TURLERI
            )
        cur = conn.execute("SELECT COUNT(*) FROM ceza_kodlari")
        if cur.fetchone()[0] == 0:
            conn.executemany(
                "INSERT INTO ceza_kodlari (kod, aciklama) VALUES (?, ?)", VARSAYILAN_CEZA_KODLARI
            )
        conn.commit()
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# Kurum bilgileri
# ---------------------------------------------------------------------------

def get_kurum_bilgileri():
    conn = get_connection()
    try:
        row = conn.execute("SELECT * FROM kurum_bilgileri WHERE id = 1").fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


def set_kurum_bilgileri(defterdarlik, vergi_dairesi):
    conn = get_connection()
    try:
        conn.execute(
            "UPDATE kurum_bilgileri SET defterdarlik = ?, vergi_dairesi = ? WHERE id = 1",
            (defterdarlik, vergi_dairesi),
        )
        conn.commit()
    finally:
        conn.close()


def sonraki_tutanak_no():
    """Yil bazli sirali tutanak numarasi uretir, ornek '2026/30'."""
    conn = get_connection()
    try:
        row = conn.execute("SELECT tutanak_yili, tutanak_sayac FROM kurum_bilgileri WHERE id = 1").fetchone()
        yil = datetime.now().year
        sayac = row["tutanak_sayac"] if row and row["tutanak_yili"] == yil else 0
        sayac += 1
        conn.execute(
            "UPDATE kurum_bilgileri SET tutanak_yili = ?, tutanak_sayac = ? WHERE id = 1",
            (yil, sayac),
        )
        conn.commit()
        return f"{yil}/{sayac}"
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# Mukellefler
# ---------------------------------------------------------------------------

def mukellef_ara(metin, limit=30):
    """Ad/unvan, VKN/TCKN veya ihbarname fis no icinde gecen mukellefleri bulur."""
    conn = get_connection()
    try:
        like = f"%{metin}%"
        rows = conn.execute(
            """
            SELECT DISTINCT m.* FROM mukellefler m
            LEFT JOIN ihbarnameler i ON i.mukellef_id = m.id
            WHERE m.ad_unvan LIKE ? OR m.vkn_tckn LIKE ? OR i.fis_no LIKE ?
            ORDER BY m.ad_unvan
            LIMIT ?
            """,
            (like, like, like, limit),
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def mukellef_getir(mukellef_id):
    conn = get_connection()
    try:
        row = conn.execute("SELECT * FROM mukellefler WHERE id = ?", (mukellef_id,)).fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


def mukellef_bul_veya_olustur(ad_unvan, vkn_tckn, adres="", telefon=""):
    conn = get_connection()
    try:
        row = None
        if vkn_tckn:
            row = conn.execute("SELECT * FROM mukellefler WHERE vkn_tckn = ?", (vkn_tckn,)).fetchone()
        if row is None:
            cur = conn.execute(
                "INSERT INTO mukellefler (ad_unvan, vkn_tckn, adres, telefon) VALUES (?, ?, ?, ?)",
                (ad_unvan, vkn_tckn, adres, telefon),
            )
            conn.commit()
            return cur.lastrowid
        else:
            # mevcut kaydi guncelle (adres/telefon degismis olabilir)
            conn.execute(
                "UPDATE mukellefler SET ad_unvan = ?, adres = COALESCE(NULLIF(?, ''), adres), "
                "telefon = COALESCE(NULLIF(?, ''), telefon) WHERE id = ?",
                (ad_unvan, adres, telefon, row["id"]),
            )
            conn.commit()
            return row["id"]
    finally:
        conn.close()


def mukellef_guncelle(mukellef_id, ad_unvan, vkn_tckn, adres, telefon):
    conn = get_connection()
    try:
        conn.execute(
            "UPDATE mukellefler SET ad_unvan = ?, vkn_tckn = ?, adres = ?, telefon = ? WHERE id = ?",
            (ad_unvan, vkn_tckn, adres, telefon, mukellef_id),
        )
        conn.commit()
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# Ihbarnameler ve ceza satirlari
# ---------------------------------------------------------------------------

def ihbarname_ekle(mukellef_id, fis_no, duzenleme_tarihi="", teblig_tarihi="", dilekce_onay_zamani=""):
    conn = get_connection()
    try:
        cur = conn.execute(
            "INSERT INTO ihbarnameler (mukellef_id, fis_no, duzenleme_tarihi, teblig_tarihi, "
            "dilekce_onay_zamani, durum, olusturma_tarihi) VALUES (?, ?, ?, ?, ?, 'beklemede', ?)",
            (mukellef_id, fis_no, duzenleme_tarihi, teblig_tarihi, dilekce_onay_zamani,
             datetime.now().strftime("%Y-%m-%d %H:%M:%S")),
        )
        conn.commit()
        return cur.lastrowid
    finally:
        conn.close()


def ceza_satiri_ekle(ihbarname_id, vergi_turu_kod, ceza_kodu, ceza_nedeni, donem, miktar):
    conn = get_connection()
    try:
        cur = conn.execute(
            "INSERT INTO ceza_satirlari (ihbarname_id, vergi_turu_kod, ceza_kodu, ceza_nedeni, donem, miktar) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (ihbarname_id, vergi_turu_kod, ceza_kodu, ceza_nedeni, donem, miktar),
        )
        conn.commit()
        return cur.lastrowid
    finally:
        conn.close()


def bekleyen_ihbarnameler(mukellef_id):
    """Mukellefe ait, henuz uzlasilmamis ihbarnameleri ve ceza satirlarini getirir."""
    conn = get_connection()
    try:
        ihbarnameler = conn.execute(
            "SELECT * FROM ihbarnameler WHERE mukellef_id = ? AND durum = 'beklemede' ORDER BY teblig_tarihi, fis_no",
            (mukellef_id,),
        ).fetchall()
        sonuc = []
        for ih in ihbarnameler:
            satirlar = conn.execute(
                "SELECT * FROM ceza_satirlari WHERE ihbarname_id = ? ORDER BY id", (ih["id"],)
            ).fetchall()
            sonuc.append({"ihbarname": dict(ih), "satirlar": [dict(s) for s in satirlar]})
        return sonuc
    finally:
        conn.close()


def ihbarname_durum_guncelle(ihbarname_id, durum):
    conn = get_connection()
    try:
        conn.execute("UPDATE ihbarnameler SET durum = ? WHERE id = ?", (durum, ihbarname_id))
        conn.commit()
    finally:
        conn.close()


def ihbarname_satirlarini_getir(ihbarname_id):
    conn = get_connection()
    try:
        rows = conn.execute(
            "SELECT * FROM ceza_satirlari WHERE ihbarname_id = ? ORDER BY id", (ihbarname_id,)
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# Vergi turleri / ceza kodlari
# ---------------------------------------------------------------------------

def vergi_turleri_listele(sadece_aktif=True):
    conn = get_connection()
    try:
        if sadece_aktif:
            rows = conn.execute("SELECT * FROM vergi_turleri WHERE aktif = 1 ORDER BY kod").fetchall()
        else:
            rows = conn.execute("SELECT * FROM vergi_turleri ORDER BY kod").fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def vergi_turu_ekle(kod, ad):
    conn = get_connection()
    try:
        conn.execute("INSERT OR IGNORE INTO vergi_turleri (kod, ad) VALUES (?, ?)", (kod, ad))
        conn.commit()
    finally:
        conn.close()


def vergi_turu_sil(vergi_turu_id):
    conn = get_connection()
    try:
        conn.execute("UPDATE vergi_turleri SET aktif = 0 WHERE id = ?", (vergi_turu_id,))
        conn.commit()
    finally:
        conn.close()


def ceza_kodlari_listele(sadece_aktif=True):
    conn = get_connection()
    try:
        if sadece_aktif:
            rows = conn.execute("SELECT * FROM ceza_kodlari WHERE aktif = 1 ORDER BY kod").fetchall()
        else:
            rows = conn.execute("SELECT * FROM ceza_kodlari ORDER BY kod").fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def ceza_kodu_ekle(kod, aciklama):
    conn = get_connection()
    try:
        conn.execute("INSERT OR IGNORE INTO ceza_kodlari (kod, aciklama) VALUES (?, ?)", (kod, aciklama))
        conn.commit()
    finally:
        conn.close()


def ceza_kodu_sil(ceza_kodu_id):
    conn = get_connection()
    try:
        conn.execute("UPDATE ceza_kodlari SET aktif = 0 WHERE id = ?", (ceza_kodu_id,))
        conn.commit()
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# Komisyon uyeleri
# ---------------------------------------------------------------------------

def komisyon_uyeleri_listele(sadece_aktif=True):
    conn = get_connection()
    try:
        if sadece_aktif:
            rows = conn.execute("SELECT * FROM komisyon_uyeleri WHERE aktif = 1 ORDER BY id").fetchall()
        else:
            rows = conn.execute("SELECT * FROM komisyon_uyeleri ORDER BY id").fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def komisyon_uyesi_ekle(ad_soyad, unvan):
    conn = get_connection()
    try:
        cur = conn.execute(
            "INSERT INTO komisyon_uyeleri (ad_soyad, unvan) VALUES (?, ?)", (ad_soyad, unvan)
        )
        conn.commit()
        return cur.lastrowid
    finally:
        conn.close()


def komisyon_uyesi_sil(uye_id):
    conn = get_connection()
    try:
        conn.execute("UPDATE komisyon_uyeleri SET aktif = 0 WHERE id = ?", (uye_id,))
        conn.commit()
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# Uzlasma tutanaklari
# ---------------------------------------------------------------------------

def tutanak_olustur(tutanak_no, mukellef_id, sonuc, toplanti_tarih_saat, davet_tarih_saat, notlar,
                     kalemler, komisyon_uye_idleri, dosya_yolu=""):
    """kalemler: liste of (ceza_satiri_id, ihbarname_id, indirim_orani, uzlasilan_tutar)."""
    conn = get_connection()
    try:
        cur = conn.execute(
            "INSERT INTO uzlasma_tutanaklari (tutanak_no, mukellef_id, sonuc, toplanti_tarih_saat, "
            "davet_tarih_saat, notlar, dosya_yolu, olusturma_tarihi) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (tutanak_no, mukellef_id, sonuc, toplanti_tarih_saat, davet_tarih_saat, notlar, dosya_yolu,
             datetime.now().strftime("%Y-%m-%d %H:%M:%S")),
        )
        tutanak_id = cur.lastrowid
        ihbarname_ids = set()
        for ceza_satiri_id, ihbarname_id, indirim_orani, uzlasilan_tutar in kalemler:
            conn.execute(
                "INSERT INTO tutanak_kalemleri (tutanak_id, ceza_satiri_id, indirim_orani, uzlasilan_tutar) "
                "VALUES (?, ?, ?, ?)",
                (tutanak_id, ceza_satiri_id, indirim_orani, uzlasilan_tutar),
            )
            ihbarname_ids.add(ihbarname_id)
        for uye_id in komisyon_uye_idleri:
            conn.execute(
                "INSERT INTO tutanak_imzalari (tutanak_id, komisyon_uye_id) VALUES (?, ?)",
                (tutanak_id, uye_id),
            )
        for ihbarname_id in ihbarname_ids:
            conn.execute("UPDATE ihbarnameler SET durum = ? WHERE id = ?", (sonuc, ihbarname_id))
        conn.commit()
        return tutanak_id
    finally:
        conn.close()


def tutanak_dosya_yolu_guncelle(tutanak_id, dosya_yolu):
    conn = get_connection()
    try:
        conn.execute("UPDATE uzlasma_tutanaklari SET dosya_yolu = ? WHERE id = ?", (dosya_yolu, tutanak_id))
        conn.commit()
    finally:
        conn.close()


def tutanak_gecmisi():
    conn = get_connection()
    try:
        rows = conn.execute(
            """
            SELECT t.*, m.ad_unvan, m.vkn_tckn
            FROM uzlasma_tutanaklari t
            JOIN mukellefler m ON m.id = t.mukellef_id
            ORDER BY t.toplanti_tarih_saat DESC, t.id DESC
            """
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def komisyon_uyesi_imza_gecmisi(uye_id):
    conn = get_connection()
    try:
        rows = conn.execute(
            """
            SELECT t.*, m.ad_unvan, m.vkn_tckn
            FROM tutanak_imzalari ti
            JOIN uzlasma_tutanaklari t ON t.id = ti.tutanak_id
            JOIN mukellefler m ON m.id = t.mukellef_id
            WHERE ti.komisyon_uye_id = ?
            ORDER BY t.toplanti_tarih_saat DESC, t.id DESC
            """,
            (uye_id,),
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def puantaj_verisi(yil, ay):
    """Verilen ay icin uye basina oturum gunleri.

    Bir uye, o gun en az bir tutanak imzaladiysa o gunde oturuma katilmis
    sayilir. Donus: [{ad_soyad, unvan, gunler: [int], oturum_sayisi}]
    (tum aktif uyeler, hic oturumu olmayanlar dahil).
    """
    ay_oneki = f"{yil:04d}-{ay:02d}-"
    conn = get_connection()
    try:
        rows = conn.execute(
            """
            SELECT ti.komisyon_uye_id AS uye_id,
                   CAST(substr(t.toplanti_tarih_saat, 9, 2) AS INTEGER) AS gun
            FROM tutanak_imzalari ti
            JOIN uzlasma_tutanaklari t ON t.id = ti.tutanak_id
            WHERE t.toplanti_tarih_saat LIKE ? || '%'
            GROUP BY ti.komisyon_uye_id, gun
            """,
            (ay_oneki,),
        ).fetchall()
    finally:
        conn.close()

    gunler = {}
    for r in rows:
        gunler.setdefault(r["uye_id"], set()).add(r["gun"])

    sonuc = []
    for u in komisyon_uyeleri_listele():
        uye_gunleri = sorted(gunler.get(u["id"], set()))
        sonuc.append({
            "ad_soyad": u["ad_soyad"],
            "unvan": u["unvan"],
            "gunler": uye_gunleri,
            "oturum_sayisi": len(uye_gunleri),
        })
    return sonuc


def tutanak_imzalayanlari_getir(tutanak_id):
    conn = get_connection()
    try:
        rows = conn.execute(
            """
            SELECT k.* FROM tutanak_imzalari ti
            JOIN komisyon_uyeleri k ON k.id = ti.komisyon_uye_id
            WHERE ti.tutanak_id = ?
            ORDER BY k.id
            """,
            (tutanak_id,),
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def tutanak_kalemlerini_getir(tutanak_id):
    conn = get_connection()
    try:
        rows = conn.execute(
            """
            SELECT tk.*, cs.vergi_turu_kod, cs.ceza_kodu, cs.ceza_nedeni, cs.donem, cs.miktar, ih.fis_no
            FROM tutanak_kalemleri tk
            JOIN ceza_satirlari cs ON cs.id = tk.ceza_satiri_id
            JOIN ihbarnameler ih ON ih.id = cs.ihbarname_id
            WHERE tk.tutanak_id = ?
            ORDER BY tk.id
            """,
            (tutanak_id,),
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# Istatistikler
# ---------------------------------------------------------------------------

def istatistikler(baslangic=None, bitis=None):
    """baslangic/bitis: 'YYYY-MM-DD' formatinda tarih (toplanti_tarih_saat uzerinde filtre)."""
    conn = get_connection()
    try:
        kosul = "1=1"
        params = []
        if baslangic:
            kosul += " AND t.toplanti_tarih_saat >= ?"
            params.append(baslangic)
        if bitis:
            kosul += " AND t.toplanti_tarih_saat <= ?"
            params.append(bitis + " 23:59:59")

        sonuc_dagilimi = conn.execute(
            f"""
            SELECT t.sonuc, COUNT(DISTINCT t.id) AS adet
            FROM uzlasma_tutanaklari t
            WHERE {kosul}
            GROUP BY t.sonuc
            """,
            params,
        ).fetchall()

        ceza_turu_bazinda = conn.execute(
            f"""
            SELECT cs.ceza_kodu, ck.aciklama, COUNT(*) AS basvuru_sayisi,
                   SUM(cs.miktar) AS toplam_basvuru_tutari,
                   SUM(CASE WHEN t.sonuc = 'uzlasildi' THEN tk.uzlasilan_tutar ELSE 0 END) AS toplam_uzlasilan_tutar,
                   SUM(CASE WHEN t.sonuc = 'uzlasildi' THEN 1 ELSE 0 END) AS uzlasilan_sayisi
            FROM tutanak_kalemleri tk
            JOIN ceza_satirlari cs ON cs.id = tk.ceza_satiri_id
            LEFT JOIN ceza_kodlari ck ON ck.kod = cs.ceza_kodu
            JOIN uzlasma_tutanaklari t ON t.id = tk.tutanak_id
            WHERE {kosul}
            GROUP BY cs.ceza_kodu, ck.aciklama
            ORDER BY cs.ceza_kodu
            """,
            params,
        ).fetchall()

        basvuran_sayisi = conn.execute(
            f"""
            SELECT COUNT(DISTINCT t.mukellef_id) FROM uzlasma_tutanaklari t WHERE {kosul}
            """,
            params,
        ).fetchone()[0]

        mukellef_bazinda = conn.execute(
            f"""
            SELECT m.ad_unvan, m.vkn_tckn,
                   COUNT(DISTINCT t.id) AS tutanak_sayisi,
                   COUNT(DISTINCT cs.ihbarname_id) AS ihbarname_sayisi,
                   COUNT(tk.id) AS kalem_sayisi,
                   SUM(CASE WHEN t.sonuc = 'uzlasildi' THEN 1 ELSE 0 END) > 0 AS uzlasti,
                   SUM(cs.miktar) AS toplam_basvuru_tutari,
                   SUM(CASE WHEN t.sonuc = 'uzlasildi' THEN tk.uzlasilan_tutar ELSE 0 END)
                       AS toplam_uzlasilan_tutar
            FROM uzlasma_tutanaklari t
            JOIN mukellefler m ON m.id = t.mukellef_id
            JOIN tutanak_kalemleri tk ON tk.tutanak_id = t.id
            JOIN ceza_satirlari cs ON cs.id = tk.ceza_satiri_id
            WHERE {kosul}
            GROUP BY t.mukellef_id
            ORDER BY m.ad_unvan COLLATE NOCASE
            """,
            params,
        ).fetchall()

        return {
            "sonuc_dagilimi": {r["sonuc"]: r["adet"] for r in sonuc_dagilimi},
            "ceza_turu_bazinda": [dict(r) for r in ceza_turu_bazinda],
            "mukellef_bazinda": [dict(r) for r in mukellef_bazinda],
            "basvuran_sayisi": basvuran_sayisi,
        }
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# Yedekleme / geri yukleme
# ---------------------------------------------------------------------------

def yedek_al():
    os.makedirs(YEDEK_DIR, exist_ok=True)
    zaman = datetime.now().strftime("%Y%m%d_%H%M%S")
    hedef = os.path.join(YEDEK_DIR, f"uzlasma_{zaman}.db")
    shutil.copy2(DB_PATH, hedef)
    return hedef


def yedekleri_listele():
    if not os.path.isdir(YEDEK_DIR):
        return []
    dosyalar = [f for f in os.listdir(YEDEK_DIR) if f.endswith(".db")]
    dosyalar.sort(reverse=True)
    return dosyalar


def yedekten_geri_yukle(dosya_adi):
    # Yalnizca yedek klasorunun icindeki dosya adlari kabul edilir
    dosya_adi = os.path.basename(dosya_adi)
    kaynak = os.path.join(YEDEK_DIR, dosya_adi)
    if not os.path.isfile(kaynak):
        raise FileNotFoundError(dosya_adi)
    # mevcut veritabaninin guvenlik kopyasini al
    if os.path.isfile(DB_PATH):
        zaman = datetime.now().strftime("%Y%m%d_%H%M%S")
        shutil.copy2(DB_PATH, os.path.join(YEDEK_DIR, f"geri_yukleme_oncesi_{zaman}.db"))
    shutil.copy2(kaynak, DB_PATH)
