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
        # Eski surumden gecis: komisyon uyelerine 'gorev' kolonu (Baskan/Uye).
        # 'unvan' artik gercek unvani tutar (Mudur, Mudur Yrd., Gelir Uzmani...).
        kolonlar = [r[1] for r in conn.execute("PRAGMA table_info(komisyon_uyeleri)")]
        if "gorev" not in kolonlar:
            conn.execute("ALTER TABLE komisyon_uyeleri ADD COLUMN gorev TEXT")
            for row in conn.execute("SELECT id, unvan FROM komisyon_uyeleri").fetchall():
                eski = (row["unvan"] or "").strip()
                duz = eski.lower().replace("ş", "s").replace("ü", "u")
                if duz.startswith("ba"):
                    conn.execute("UPDATE komisyon_uyeleri SET gorev = 'Başkan', unvan = '' WHERE id = ?",
                                 (row["id"],))
                else:
                    conn.execute("UPDATE komisyon_uyeleri SET gorev = 'Üye', "
                                 "unvan = CASE WHEN unvan IN ('Uye', 'Üye') THEN '' ELSE unvan END "
                                 "WHERE id = ?", (row["id"],))
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


def tutanak_sayaci_ayarla(sonraki_sayi):
    """Bir sonraki tutanagin alacagi sira numarasini belirler (yil icinde).

    Yil ortasinda uygulamaya gecildiginde kaldigi yerden devam edebilmek
    icindir; ornegin 45 verilirse siradaki tutanak 'YIL/45' olur.
    """
    sonraki_sayi = int(sonraki_sayi)
    if sonraki_sayi < 1:
        raise ValueError("Tutanak sayisi 1'den kucuk olamaz.")
    conn = get_connection()
    try:
        conn.execute(
            "UPDATE kurum_bilgileri SET tutanak_yili = ?, tutanak_sayac = ? WHERE id = 1",
            (datetime.now().year, sonraki_sayi - 1),
        )
        conn.commit()
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

def mevcut_fis_nolar(fis_listesi):
    """Verilen fis numaralarindan veritabaninda zaten kayitli olanlari dondurur."""
    fisler = [str(f).strip() for f in fis_listesi if str(f).strip()]
    if not fisler:
        return []
    conn = get_connection()
    try:
        soru = ",".join("?" * len(fisler))
        rows = conn.execute(
            f"SELECT DISTINCT fis_no FROM ihbarnameler WHERE fis_no IN ({soru})", fisler
        ).fetchall()
        return [r["fis_no"] for r in rows]
    finally:
        conn.close()


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


def tum_ihbarnameler(mukellef_id):
    """Mukellefe ait tum ihbarnameleri (durumuyla birlikte) ve satirlarini getirir.

    Bekleyenler once gelir; gecmis sonuclar bilgi amacli listelenir.
    """
    conn = get_connection()
    try:
        ihbarnameler = conn.execute(
            """
            SELECT * FROM ihbarnameler WHERE mukellef_id = ?
            ORDER BY CASE durum WHEN 'beklemede' THEN 0 ELSE 1 END, teblig_tarihi, fis_no
            """,
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


def ceza_satiri_guncelle(ceza_satiri_id, vergi_turu_kod, ceza_kodu, miktar):
    """Yalniz bekleyen (tutanaga girmemis) ihbarnamelerin satirlari duzenlenebilir."""
    conn = get_connection()
    try:
        row = conn.execute(
            """
            SELECT ih.durum FROM ceza_satirlari cs
            JOIN ihbarnameler ih ON ih.id = cs.ihbarname_id WHERE cs.id = ?
            """,
            (ceza_satiri_id,),
        ).fetchone()
        if row is None:
            raise ValueError("Ceza satiri bulunamadi.")
        if row["durum"] != "beklemede":
            raise ValueError("Yalniz bekleyen ihbarnameler duzenlenebilir.")
        conn.execute(
            "UPDATE ceza_satirlari SET vergi_turu_kod = ?, ceza_kodu = ?, miktar = ? WHERE id = ?",
            (vergi_turu_kod, ceza_kodu, float(miktar), ceza_satiri_id),
        )
        conn.commit()
    finally:
        conn.close()


def ihbarname_sil(ihbarname_id):
    """Ihbarnameyi ve ceza satirlarini siler (uzlasmadan vazgecme durumu).

    Bir tutanaga girmis ihbarnameler silinemez; once tutanak silinmelidir.
    """
    conn = get_connection()
    try:
        kullanim = conn.execute(
            """
            SELECT COUNT(*) FROM tutanak_kalemleri tk
            JOIN ceza_satirlari cs ON cs.id = tk.ceza_satiri_id
            WHERE cs.ihbarname_id = ?
            """,
            (ihbarname_id,),
        ).fetchone()[0]
        if kullanim:
            raise ValueError("Bu ihbarname bir tutanaga bagli; once tutanagi silin.")
        conn.execute("DELETE FROM ceza_satirlari WHERE ihbarname_id = ?", (ihbarname_id,))
        conn.execute("DELETE FROM ihbarnameler WHERE id = ?", (ihbarname_id,))
        conn.commit()
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


def komisyon_uyesi_ekle(ad_soyad, unvan, gorev="Üye"):
    conn = get_connection()
    try:
        cur = conn.execute(
            "INSERT INTO komisyon_uyeleri (ad_soyad, unvan, gorev) VALUES (?, ?, ?)",
            (ad_soyad, unvan, gorev),
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
        gorev = (u["gorev"] or u["unvan"] or "").strip()
        # Puantajda komisyon baskani, gercek unvani ne olursa olsun (ornegin
        # Mudur Yardimcisi) "Mudur" olarak yazilir; uyeler gercek unvaniyla.
        if gorev.lower().replace("ş", "s").startswith("ba"):
            unvan = "Müdür"
        else:
            unvan = (u["unvan"] or "").strip() or "Üye"
        sonuc.append({
            "ad_soyad": u["ad_soyad"],
            "unvan": unvan,
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
    """baslangic/bitis: 'YYYY-MM-DD' bicimli tarih.

    - Basvuru sayilari DILEKCE bazindadir: ayni dilekceyle (ayni onay
      zamani) kaydedilen ihbarnameler tek basvuru sayilir. Tarih filtresi
      basvurular icin kayit tarihine (ihbarnameler.olusturma_tarihi) uygulanir.
    - Uzlasilan sayilari TUTANAK bazindadir; tarih filtresi toplanti
      tarihine uygulanir.
    """
    conn = get_connection()
    try:
        # Tutanak tarafi filtresi (toplanti tarihi)
        kosul_t = "1=1"
        params_t = []
        if baslangic:
            kosul_t += " AND t.toplanti_tarih_saat >= ?"
            params_t.append(baslangic)
        if bitis:
            kosul_t += " AND t.toplanti_tarih_saat <= ?"
            params_t.append(bitis + " 23:59:59")

        # Basvuru (dilekce) tarafi filtresi (kayit tarihi)
        kosul_b = "1=1"
        params_b = []
        if baslangic:
            kosul_b += " AND ih.olusturma_tarihi >= ?"
            params_b.append(baslangic)
        if bitis:
            kosul_b += " AND ih.olusturma_tarihi <= ?"
            params_b.append(bitis + " 23:59:59")

        # Ayni dilekceyi tanimlayan anahtar: mukellef + dilekce onay zamani
        # (onay zamani bos olan elle girisler ihbarname basina sayilir)
        dilekce_anahtari = ("ih.mukellef_id || '|' || "
                            "COALESCE(NULLIF(ih.dilekce_onay_zamani, ''), 'IH' || ih.id)")

        sonuc_dagilimi = conn.execute(
            f"""
            SELECT t.sonuc, COUNT(DISTINCT t.id) AS adet
            FROM uzlasma_tutanaklari t
            WHERE {kosul_t}
            GROUP BY t.sonuc
            """,
            params_t,
        ).fetchall()

        def _tur_bazinda(kod_kolonu, ad_tablosu, ad_kolonu, ad_eslesme):
            # Basvurular: tum kayitli ceza satirlari (dilekce bazinda sayim)
            basvurular = conn.execute(
                f"""
                SELECT cs.{kod_kolonu} AS kod, MAX(ad.{ad_kolonu}) AS aciklama,
                       COUNT(DISTINCT {dilekce_anahtari}) AS basvuru_sayisi,
                       SUM(cs.miktar) AS toplam_basvuru_tutari
                FROM ceza_satirlari cs
                JOIN ihbarnameler ih ON ih.id = cs.ihbarname_id
                LEFT JOIN {ad_tablosu} ad ON ad.kod = cs.{kod_kolonu}
                WHERE {kosul_b}
                GROUP BY cs.{kod_kolonu}
                """,
                params_b,
            ).fetchall()
            # Uzlasilanlar: tutanak bazinda sayim ve tutar
            uzlasilanlar = conn.execute(
                f"""
                SELECT cs.{kod_kolonu} AS kod,
                       COUNT(DISTINCT CASE WHEN t.sonuc = 'uzlasildi' THEN t.id END) AS uzlasilan_sayisi,
                       SUM(CASE WHEN t.sonuc = 'uzlasildi' THEN tk.uzlasilan_tutar ELSE 0 END) AS toplam_uzlasilan_tutar
                FROM tutanak_kalemleri tk
                JOIN ceza_satirlari cs ON cs.id = tk.ceza_satiri_id
                JOIN uzlasma_tutanaklari t ON t.id = tk.tutanak_id
                WHERE {kosul_t}
                GROUP BY cs.{kod_kolonu}
                """,
                params_t,
            ).fetchall()
            uz = {r["kod"]: r for r in uzlasilanlar}
            sonuc = []
            kodlar = {r["kod"] for r in basvurular} | set(uz)
            basv = {r["kod"]: r for r in basvurular}
            for kod in sorted(kodlar, key=lambda k: str(k or "")):
                b = basv.get(kod)
                u = uz.get(kod)
                sonuc.append({
                    ad_eslesme: kod or "",
                    "aciklama" if ad_tablosu == "ceza_kodlari" else "ad":
                        (b["aciklama"] if b else "") or "",
                    "basvuru_sayisi": b["basvuru_sayisi"] if b else 0,
                    "toplam_basvuru_tutari": (b["toplam_basvuru_tutari"] if b else 0) or 0,
                    "uzlasilan_sayisi": (u["uzlasilan_sayisi"] if u else 0) or 0,
                    "toplam_uzlasilan_tutar": (u["toplam_uzlasilan_tutar"] if u else 0) or 0,
                })
            return sonuc

        # Iki tablo:
        # - Ceza turu bazinda: 3080 DISINDAKI cezalar (3073, 3074... ayri satirlar)
        # - Vergi turu bazinda: 3080 (vergi ziyai) satirlari vergi turuyle birlikte
        def _grup_istatistik(grup_sql, kosul_ek):
            basvurular = conn.execute(
                f"""
                SELECT {grup_sql} AS kod,
                       COUNT(DISTINCT {dilekce_anahtari}) AS basvuru_sayisi,
                       SUM(cs.miktar) AS toplam_basvuru_tutari
                FROM ceza_satirlari cs
                JOIN ihbarnameler ih ON ih.id = cs.ihbarname_id
                WHERE {kosul_b} AND {kosul_ek}
                GROUP BY {grup_sql}
                """,
                params_b,
            ).fetchall()
            uzlasilanlar = conn.execute(
                f"""
                SELECT {grup_sql} AS kod,
                       COUNT(DISTINCT CASE WHEN t.sonuc = 'uzlasildi' THEN t.id END) AS uzlasilan_sayisi,
                       COUNT(DISTINCT CASE WHEN t.sonuc = 'uzlasilamadi' THEN t.id END) AS uzlasilamayan_sayisi,
                       COUNT(DISTINCT CASE WHEN t.sonuc = 'gelmedi' THEN t.id END) AS gelmeyen_sayisi,
                       SUM(CASE WHEN t.sonuc = 'uzlasildi' THEN tk.uzlasilan_tutar ELSE 0 END) AS toplam_uzlasilan_tutar,
                       SUM(CASE
                               WHEN t.sonuc = 'uzlasilamadi' THEN tk.uzlasilan_tutar
                               WHEN t.sonuc = 'gelmedi' THEN ROUND(cs.miktar * (1 - tk.indirim_orani / 100.0), 2)
                               ELSE 0
                           END) AS toplam_uzlasilamayan_tutar
                FROM tutanak_kalemleri tk
                JOIN ceza_satirlari cs ON cs.id = tk.ceza_satiri_id
                JOIN uzlasma_tutanaklari t ON t.id = tk.tutanak_id
                WHERE {kosul_t} AND {kosul_ek}
                GROUP BY {grup_sql}
                """,
                params_t,
            ).fetchall()
            uz = {r["kod"]: r for r in uzlasilanlar}
            basv = {r["kod"]: r for r in basvurular}
            birlesik = []
            for kod in sorted(set(basv) | set(uz), key=str):
                b = basv.get(kod)
                u = uz.get(kod)
                birlesik.append({
                    "kod": kod or "",
                    "basvuru_sayisi": b["basvuru_sayisi"] if b else 0,
                    "toplam_basvuru_tutari": (b["toplam_basvuru_tutari"] if b else 0) or 0,
                    "uzlasilan_sayisi": (u["uzlasilan_sayisi"] if u else 0) or 0,
                    "uzlasilamayan_sayisi": (u["uzlasilamayan_sayisi"] if u else 0) or 0,
                    "gelmeyen_sayisi": (u["gelmeyen_sayisi"] if u else 0) or 0,
                    "toplam_uzlasilan_tutar": (u["toplam_uzlasilan_tutar"] if u else 0) or 0,
                    "toplam_uzlasilamayan_tutar": (u["toplam_uzlasilamayan_tutar"] if u else 0) or 0,
                })
            return birlesik

        vergi_adlari = {v["kod"]: (v["ad"] or "") for v in vergi_turleri_listele(sadece_aktif=False)}
        ceza_aciklamalari = {c["kod"]: (c["aciklama"] or "")
                              for c in ceza_kodlari_listele(sadece_aktif=False)}

        # Ceza tablosu: 3080 haric, her ceza kodu ayri satir (3073, 3074...)
        ceza_turu_bazinda = []
        for r in _grup_istatistik("COALESCE(cs.ceza_kodu, '')",
                                   "COALESCE(cs.ceza_kodu, '') != '3080'"):
            r["ceza_kodu"] = r.pop("kod")
            r["aciklama"] = ceza_aciklamalari.get(r["ceza_kodu"], "")
            ceza_turu_bazinda.append(r)

        # Vergi tablosu: 3080 satirlari vergi turuyle birlikte ("0015/3080")
        vergi_turu_bazinda = []
        for r in _grup_istatistik("COALESCE(NULLIF(cs.vergi_turu_kod, ''), '????')",
                                   "cs.ceza_kodu = '3080'"):
            vt = r.pop("kod")
            r["vergi_turu_kod"] = f"{vt}/3080"
            vt_ad = vergi_adlari.get(vt, "")
            r["ad"] = (vt_ad + " - " if vt_ad else "") + "Vergi Ziyaı Cezası"
            vergi_turu_bazinda.append(r)

        basvuran_sayisi = conn.execute(
            f"""
            SELECT COUNT(DISTINCT t.mukellef_id) FROM uzlasma_tutanaklari t WHERE {kosul_t}
            """,
            params_t,
        ).fetchone()[0]

        dilekce_sayisi = conn.execute(
            f"""
            SELECT COUNT(DISTINCT {dilekce_anahtari})
            FROM ihbarnameler ih
            WHERE {kosul_b}
            """,
            params_b,
        ).fetchone()[0]

        return {
            "sonuc_dagilimi": {r["sonuc"]: r["adet"] for r in sonuc_dagilimi},
            "ceza_turu_bazinda": ceza_turu_bazinda,
            "vergi_turu_bazinda": vergi_turu_bazinda,
            "basvuran_sayisi": basvuran_sayisi,
            "dilekce_sayisi": dilekce_sayisi,
        }
    finally:
        conn.close()


def tutanak_sil(tutanak_id):
    """Tutanagi siler; bagli ihbarnameler yeniden 'beklemede' olur.

    Donus: silinen tutanagin dosya yolu (Excel dosyasini silmek icin).
    """
    conn = get_connection()
    try:
        t = conn.execute("SELECT * FROM uzlasma_tutanaklari WHERE id = ?", (tutanak_id,)).fetchone()
        if t is None:
            raise ValueError("Tutanak bulunamadi.")
        ihbarnameler = [r[0] for r in conn.execute(
            """
            SELECT DISTINCT cs.ihbarname_id FROM tutanak_kalemleri tk
            JOIN ceza_satirlari cs ON cs.id = tk.ceza_satiri_id
            WHERE tk.tutanak_id = ?
            """,
            (tutanak_id,),
        ).fetchall()]
        conn.execute("DELETE FROM tutanak_imzalari WHERE tutanak_id = ?", (tutanak_id,))
        conn.execute("DELETE FROM tutanak_kalemleri WHERE tutanak_id = ?", (tutanak_id,))
        conn.execute("DELETE FROM uzlasma_tutanaklari WHERE id = ?", (tutanak_id,))
        for ih_id in ihbarnameler:
            conn.execute("UPDATE ihbarnameler SET durum = 'beklemede' WHERE id = ?", (ih_id,))
        conn.commit()
        return t["dosya_yolu"]
    finally:
        conn.close()


def tutanak_sonuc_guncelle(tutanak_id, yeni_sonuc, davet_tarih_saat=None):
    """Tutanagin sonucunu degistirir; kalem tutarlarini ve ihbarname
    durumlarini yeni sonuca gore gunceller. Excel'i yeniden uretmek
    cagiranin sorumlulugundadir."""
    if yeni_sonuc not in ("uzlasildi", "uzlasilamadi", "gelmedi"):
        raise ValueError("Gecersiz sonuc.")
    conn = get_connection()
    try:
        t = conn.execute("SELECT * FROM uzlasma_tutanaklari WHERE id = ?", (tutanak_id,)).fetchone()
        if t is None:
            raise ValueError("Tutanak bulunamadi.")
        if davet_tarih_saat is not None:
            conn.execute("UPDATE uzlasma_tutanaklari SET davet_tarih_saat = ? WHERE id = ?",
                         (davet_tarih_saat, tutanak_id))
        conn.execute("UPDATE uzlasma_tutanaklari SET sonuc = ? WHERE id = ?",
                     (yeni_sonuc, tutanak_id))
        # Kalem tutarlari: gelmedi -> 0; digerleri kayitli orana gore yeniden hesap
        for k in conn.execute(
            """
            SELECT tk.id, tk.indirim_orani, cs.miktar, cs.ihbarname_id
            FROM tutanak_kalemleri tk JOIN ceza_satirlari cs ON cs.id = tk.ceza_satiri_id
            WHERE tk.tutanak_id = ?
            """,
            (tutanak_id,),
        ).fetchall():
            yeni_tutar = 0.0 if yeni_sonuc == "gelmedi" else round(
                k["miktar"] * (1 - k["indirim_orani"] / 100), 2)
            conn.execute("UPDATE tutanak_kalemleri SET uzlasilan_tutar = ? WHERE id = ?",
                         (yeni_tutar, k["id"]))
            conn.execute("UPDATE ihbarnameler SET durum = ? WHERE id = ?",
                         (yeni_sonuc, k["ihbarname_id"]))
        conn.commit()
    finally:
        conn.close()


def tum_kayitlar_dokum():
    """ODS dokumu icin tum ceza satirlarini duz liste olarak getirir."""
    conn = get_connection()
    try:
        rows = conn.execute(
            """
            SELECT m.vkn_tckn, m.ad_unvan, ih.fis_no, cs.vergi_turu_kod, cs.ceza_kodu,
                   cs.miktar, tk.uzlasilan_tutar, ih.durum
            FROM ceza_satirlari cs
            JOIN ihbarnameler ih ON ih.id = cs.ihbarname_id
            JOIN mukellefler m ON m.id = ih.mukellef_id
            LEFT JOIN tutanak_kalemleri tk ON tk.id = (
                SELECT MAX(tk2.id) FROM tutanak_kalemleri tk2 WHERE tk2.ceza_satiri_id = cs.id
            )
            ORDER BY m.ad_unvan COLLATE NOCASE, ih.fis_no, cs.id
            """
        ).fetchall()
        return [dict(r) for r in rows]
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
