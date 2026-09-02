"""SQLite veritabani katmani: kaydedilmis calismalar ve yedekleme.

Uygulama, uzerinde calisilan veriyi kendiliginden saklamaz. Hesaplama tamamen
bellekte yapilir; veritabanina yalnizca kullanici "Kaydet" dediginde yazilir.
Bu nedenle sema tek bir tabloya indirgenmistir: her kayit, bir calismanin
tamamini (mukellef bilgisi, yillar, beyan verisi ve tespitler) JSON olarak
tasir.

Onceki surumlerde iliskisel bir sema kullaniliyordu; o semadaki kayitlar ilk
acilista otomatik olarak bu tabloya tasinir (bkz. `_eski_semayi_tasi`).
"""
import json
import os
import shutil
import sqlite3
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_DIR = os.path.join(BASE_DIR, "veritabani")
DB_PATH = os.path.join(DB_DIR, "kdv.db")
YEDEK_DIR = os.path.join(BASE_DIR, "yedekler")

SCHEMA = """
CREATE TABLE IF NOT EXISTS calismalar (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ad TEXT NOT NULL,
    mukellef_ad TEXT,
    vkn_tckn TEXT,
    olusturma_tarihi TEXT,
    guncelleme_tarihi TEXT,
    veri TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_calisma_ad ON calismalar(ad);

CREATE TABLE IF NOT EXISTS gocler (
    ad TEXT PRIMARY KEY,
    tarih TEXT
);
"""

ADSIZ_MUKELLEF = "(Adsız Mükellef)"


def _semayi_guvenceye_al(conn):
    """Tablolar yoksa olusturur.

    Sema acilista da kurulur (bkz. `init_db`), ama yalnizca oraya guvenmek
    yetmiyor: uygulama acikken veritabani dosyasi degisebiliyor. Yeni bir
    surum klasorun uzerine kopyalandiginda, dosya elle degistirildiginde ya
    da bir yedek geri yuklendiginde acilistaki sema kayboluyor ve sonraki
    her yazma "no such table: calismalar" ile basarisiz oluyordu.

    Once ucuz bir okuma yapilir; yalnizca tablo gercekten yoksa yazilir.
    Boylece salt okunur bir veritabaninda gereksiz yazma denenmez.
    """
    var = conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = 'calismalar'"
    ).fetchone()
    if var:
        return
    conn.executescript(SCHEMA)
    conn.commit()


def _baglan():
    os.makedirs(DB_DIR, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    _semayi_guvenceye_al(conn)
    return conn


def _simdi():
    return datetime.now().strftime("%d.%m.%Y %H:%M")


def init_db():
    conn = _baglan()
    try:
        conn.executescript(SCHEMA)
        conn.commit()
        _eski_semayi_tasi(conn)
    finally:
        conn.close()


# ------------------------------------------------------------------ calismalar
def calismalari_listele():
    """Kaydedilmis calismalarin ozetini dondurur (veri govdesi haric)."""
    conn = _baglan()
    try:
        kayitlar = []
        for r in conn.execute(
                "SELECT id, ad, mukellef_ad, vkn_tckn, olusturma_tarihi, guncelleme_tarihi, "
                "veri FROM calismalar ORDER BY guncelleme_tarihi DESC, id DESC"):
            try:
                veri = json.loads(r["veri"])
                yillar = sorted(y.get("yil") for y in veri.get("yillar") or [])
            except (ValueError, TypeError):
                yillar = []
            kayitlar.append({
                "id": r["id"], "ad": r["ad"], "mukellef_ad": r["mukellef_ad"],
                "vkn_tckn": r["vkn_tckn"], "olusturma_tarihi": r["olusturma_tarihi"],
                "guncelleme_tarihi": r["guncelleme_tarihi"], "yillar": yillar,
            })
        return kayitlar
    finally:
        conn.close()


def calisma_getir(calisma_id):
    conn = _baglan()
    try:
        r = conn.execute("SELECT * FROM calismalar WHERE id = ?", (calisma_id,)).fetchone()
        if r is None:
            raise ValueError("Kayıtlı çalışma bulunamadı.")
        veri = json.loads(r["veri"])
        veri["id"] = r["id"]
        veri["ad"] = r["ad"]
        veri["olusturma_tarihi"] = r["olusturma_tarihi"]
        veri["guncelleme_tarihi"] = r["guncelleme_tarihi"]
        return veri
    finally:
        conn.close()


def calisma_kaydet(calisma, calisma_id=None):
    """Calismayi kaydeder. calisma_id verilirse uzerine yazar, yoksa yeni olusturur."""
    mukellef = calisma.get("mukellef") or {}
    ad = (calisma.get("ad") or "").strip() or _varsayilan_ad(calisma)
    govde = json.dumps(calisma, ensure_ascii=False)
    conn = _baglan()
    try:
        if calisma_id:
            var = conn.execute("SELECT id FROM calismalar WHERE id = ?", (calisma_id,)).fetchone()
            if var is None:
                raise ValueError("Güncellenecek çalışma bulunamadı.")
            conn.execute(
                "UPDATE calismalar SET ad = ?, mukellef_ad = ?, vkn_tckn = ?, "
                "guncelleme_tarihi = ?, veri = ? WHERE id = ?",
                (ad, mukellef.get("ad_unvan"), mukellef.get("vkn_tckn"), _simdi(),
                 govde, calisma_id))
            conn.commit()
            return calisma_id
        cur = conn.execute(
            "INSERT INTO calismalar (ad, mukellef_ad, vkn_tckn, olusturma_tarihi, "
            "guncelleme_tarihi, veri) VALUES (?, ?, ?, ?, ?, ?)",
            (ad, mukellef.get("ad_unvan"), mukellef.get("vkn_tckn"), _simdi(), _simdi(), govde))
        conn.commit()
        return cur.lastrowid
    finally:
        conn.close()


def calisma_sil(calisma_id):
    conn = _baglan()
    try:
        cur = conn.execute("DELETE FROM calismalar WHERE id = ?", (calisma_id,))
        conn.commit()
        if not cur.rowcount:
            raise ValueError("Silinecek çalışma bulunamadı.")
    finally:
        conn.close()


def _varsayilan_ad(calisma):
    mukellef = calisma.get("mukellef") or {}
    ad = (mukellef.get("ad_unvan") or "").strip()
    yillar = sorted(y.get("yil") for y in calisma.get("yillar") or [] if y.get("yil"))
    if yillar:
        aralik = str(yillar[0]) if len(yillar) == 1 else f"{yillar[0]}-{yillar[-1]}"
    else:
        aralik = ""
    if ad and ad != ADSIZ_MUKELLEF:
        return f"{ad} {aralik}".strip()
    return f"KDV çalışması {aralik}".strip()


# --------------------------------------------------------------------- yedekler
def yedek_al():
    os.makedirs(YEDEK_DIR, exist_ok=True)
    if not os.path.isfile(DB_PATH):
        init_db()
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


# ------------------------------------------------------------------------ goc
def _kolon_var(conn, tablo, kolon):
    return kolon in {r["name"] for r in conn.execute(f"PRAGMA table_info({tablo})")}


def _eski_semayi_tasi(conn):
    """Onceki iliskisel semadaki kayitlari `calismalar` tablosuna tasir.

    Yalnizca bir kez calisir; sonucu `gocler` tablosunda isaretlenir. Eski
    tablolar silinmez, oldugu gibi birakilir.
    """
    isaret = conn.execute("SELECT ad FROM gocler WHERE ad = 'iliskisel_v1'").fetchone()
    if isaret:
        return
    tablolar = {r["name"] for r in conn.execute(
        "SELECT name FROM sqlite_master WHERE type = 'table'")}
    if not {"incelemeler", "inceleme_yillari", "beyan_degerleri"} <= tablolar:
        conn.execute("INSERT INTO gocler (ad, tarih) VALUES ('iliskisel_v1', ?)", (_simdi(),))
        conn.commit()
        return

    rapor_kolonu = _kolon_var(conn, "inceleme_yillari", "rapor_tarihi")
    tasinan = 0
    for inc in conn.execute(
            "SELECT i.*, m.ad_unvan, m.vkn_tckn, m.adres, "
            + ("m.vergi_dairesi" if _kolon_var(conn, "mukellefler", "vergi_dairesi")
               else "'' AS vergi_dairesi")
            + " FROM incelemeler i JOIN mukellefler m ON m.id = i.mukellef_id"):
        yillar = []
        for y in conn.execute("SELECT * FROM inceleme_yillari WHERE inceleme_id = ? ORDER BY yil",
                              (inc["id"],)):
            beyan = {r["satir_kodu"]: json.loads(r["degerler"]) for r in conn.execute(
                "SELECT satir_kodu, degerler FROM beyan_degerleri WHERE yil_id = ?", (y["id"],))}
            elestiri = {r["alan"]: json.loads(r["degerler"]) for r in conn.execute(
                "SELECT alan, degerler FROM elestiri_degerleri WHERE yil_id = ?", (y["id"],))}
            kayit = {"yil": y["yil"], "ay_sayisi": y["ay_sayisi"],
                     "beyan": beyan, "elestiri": elestiri, "kaynaklar": []}
            rapor_tarihi = y["rapor_tarihi"] if rapor_kolonu else None
            if rapor_tarihi:
                kayit["kaynaklar"].append({"vergi_dairesi": "", "aylar": [],
                                           "rapor_tarihi": rapor_tarihi})
            yillar.append(kayit)
        if not yillar:
            continue
        vergi_dairesi = inc["vergi_dairesi"] or ""
        calisma = {
            "mukellef": {"ad_unvan": inc["ad_unvan"], "vkn_tckn": inc["vkn_tckn"],
                         "adres": inc["adres"], "vergi_dairesi": vergi_dairesi},
            "devreden_baslangic": inc["devreden_baslangic"],
            "notlar": inc["notlar"], "yillar": yillar,
        }
        conn.execute(
            "INSERT INTO calismalar (ad, mukellef_ad, vkn_tckn, olusturma_tarihi, "
            "guncelleme_tarihi, veri) VALUES (?, ?, ?, ?, ?, ?)",
            (inc["ad"] or _varsayilan_ad(calisma), inc["ad_unvan"], inc["vkn_tckn"],
             inc["olusturma_tarihi"] or _simdi(), _simdi(),
             json.dumps(calisma, ensure_ascii=False)))
        tasinan += 1
    conn.execute("INSERT INTO gocler (ad, tarih) VALUES ('iliskisel_v1', ?)", (_simdi(),))
    conn.commit()
    if tasinan:
        print(f"Onceki surumden {tasinan} calisma tasindi.")
