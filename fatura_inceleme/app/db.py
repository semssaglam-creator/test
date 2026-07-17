"""SQLite veritabani katmani.

Tablolar:
  faturalar : fatura basligi (no, tarih, taraflar, tutarlar, durum)
  kalemler  : faturadaki mal/hizmet satirlari
  ayarlar   : anahtar-deger (incelenen mukellef VKN vb.)
"""
import os
import shutil
import sqlite3
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_DIR = os.path.join(BASE_DIR, "veritabani")
DB_PATH = os.path.join(DB_DIR, "faturalar.db")
YEDEK_DIR = os.path.join(BASE_DIR, "yedekler")

GECERLI_YONLER = ("alis", "satis", "")
GECERLI_DURUMLAR = ("tamam", "kontrol", "ocr_bekliyor")
GECERLI_KAYNAKLAR = ("metin", "ocr", "elle")


def _tr_kucuk(s):
    """Turkce'ye duyarli kucuk harf donusumu (I -> ı, İ -> i)."""
    return (s or "").replace("İ", "i").replace("I", "ı").lower()


def _baglanti():
    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    con.execute("PRAGMA foreign_keys = ON")
    con.create_function("trl", 1, _tr_kucuk, deterministic=True)
    return con


def init_db():
    os.makedirs(DB_DIR, exist_ok=True)
    con = _baglanti()
    con.executescript(
        """
        CREATE TABLE IF NOT EXISTS faturalar (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            dosya_adi TEXT DEFAULT '',
            belge_yolu TEXT DEFAULT '',
            fatura_no TEXT DEFAULT '',
            fatura_tarihi TEXT DEFAULT '',      -- ISO: YYYY-MM-DD
            ettn TEXT DEFAULT '',
            fatura_tipi TEXT DEFAULT '',        -- SATIS / IADE / TEVKIFAT ...
            yon TEXT DEFAULT '',                -- alis / satis / '' (belirsiz)
            satici_unvan TEXT DEFAULT '',
            satici_vkn TEXT DEFAULT '',
            alici_unvan TEXT DEFAULT '',
            alici_vkn TEXT DEFAULT '',
            para_birimi TEXT DEFAULT 'TL',
            mal_hizmet_toplam REAL,
            toplam_iskonto REAL,
            kdv_toplam REAL,
            vergiler_dahil_toplam REAL,
            odenecek_tutar REAL,
            kaynak TEXT DEFAULT 'metin',        -- metin / ocr / elle
            durum TEXT DEFAULT 'tamam',         -- tamam / kontrol / ocr_bekliyor
            uyarilar TEXT DEFAULT '',
            ham_metin TEXT DEFAULT '',
            notlar TEXT DEFAULT '',
            eklenme_zamani TEXT DEFAULT ''
        );
        CREATE TABLE IF NOT EXISTS kalemler (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            fatura_id INTEGER NOT NULL REFERENCES faturalar(id) ON DELETE CASCADE,
            sira INTEGER,
            mal_hizmet TEXT DEFAULT '',
            miktar REAL,
            birim TEXT DEFAULT '',
            birim_fiyat REAL,
            kdv_orani REAL,
            kdv_tutari REAL,
            tutar REAL
        );
        CREATE TABLE IF NOT EXISTS ayarlar (
            anahtar TEXT PRIMARY KEY,
            deger TEXT DEFAULT ''
        );
        CREATE INDEX IF NOT EXISTS ix_fatura_no ON faturalar(fatura_no);
        CREATE INDEX IF NOT EXISTS ix_fatura_tarih ON faturalar(fatura_tarihi);
        CREATE INDEX IF NOT EXISTS ix_fatura_satici ON faturalar(satici_vkn);
        CREATE INDEX IF NOT EXISTS ix_fatura_alici ON faturalar(alici_vkn);
        CREATE INDEX IF NOT EXISTS ix_kalem_fatura ON kalemler(fatura_id);
        CREATE INDEX IF NOT EXISTS ix_kalem_mal ON kalemler(mal_hizmet);
        """
    )
    con.commit()
    con.close()


# ---------------------------------------------------------------- ayarlar
def ayar_getir(anahtar, varsayilan=""):
    con = _baglanti()
    row = con.execute("SELECT deger FROM ayarlar WHERE anahtar=?", (anahtar,)).fetchone()
    con.close()
    return row["deger"] if row else varsayilan


def ayar_kaydet(anahtar, deger):
    con = _baglanti()
    con.execute(
        "INSERT INTO ayarlar(anahtar, deger) VALUES(?, ?) "
        "ON CONFLICT(anahtar) DO UPDATE SET deger=excluded.deger",
        (anahtar, str(deger or "")),
    )
    con.commit()
    con.close()


# ---------------------------------------------------------------- yardimci
def yon_belirle(satici_vkn, alici_vkn):
    """Incelenen mukellef VKN'sine gore faturanin alis/satis yonunu bulur."""
    mukellef_vkn = (ayar_getir("mukellef_vkn") or "").strip()
    if not mukellef_vkn:
        return ""
    if (satici_vkn or "").strip() == mukellef_vkn:
        return "satis"
    if (alici_vkn or "").strip() == mukellef_vkn:
        return "alis"
    return ""


def mukerrer_var_mi(fatura_no, ettn, satici_vkn):
    """Ayni fatura daha once kaydedilmis mi? Kayit id'sini dondurur, yoksa None."""
    con = _baglanti()
    row = None
    if (ettn or "").strip():
        row = con.execute("SELECT id FROM faturalar WHERE ettn=? AND ettn<>''",
                          ((ettn or "").strip(),)).fetchone()
    if row is None and (fatura_no or "").strip():
        row = con.execute(
            "SELECT id FROM faturalar WHERE fatura_no=? AND satici_vkn=?",
            ((fatura_no or "").strip(), (satici_vkn or "").strip()),
        ).fetchone()
    con.close()
    return row["id"] if row else None


# ---------------------------------------------------------------- kayit
_FATURA_ALANLAR = (
    "dosya_adi", "belge_yolu", "fatura_no", "fatura_tarihi", "ettn", "fatura_tipi",
    "yon", "satici_unvan", "satici_vkn", "alici_unvan", "alici_vkn", "para_birimi",
    "mal_hizmet_toplam", "toplam_iskonto", "kdv_toplam", "vergiler_dahil_toplam",
    "odenecek_tutar", "kaynak", "durum", "uyarilar", "ham_metin", "notlar",
)

_KALEM_ALANLAR = ("sira", "mal_hizmet", "miktar", "birim", "birim_fiyat",
                  "kdv_orani", "kdv_tutari", "tutar")


_SAYISAL_ALANLAR = {"mal_hizmet_toplam", "toplam_iskonto", "kdv_toplam",
                    "vergiler_dahil_toplam", "odenecek_tutar"}


def fatura_ekle(veri, kalemler):
    """Fatura basligi + kalemleri kaydeder, fatura id dondurur."""
    degerler = [veri.get(a) if a in _SAYISAL_ALANLAR else (veri.get(a) or "")
                for a in _FATURA_ALANLAR]
    con = _baglanti()
    cur = con.execute(
        f"INSERT INTO faturalar({', '.join(_FATURA_ALANLAR)}, eklenme_zamani) "
        f"VALUES({', '.join('?' * len(_FATURA_ALANLAR))}, ?)",
        degerler + [datetime.now().strftime("%Y-%m-%d %H:%M:%S")],
    )
    fatura_id = cur.lastrowid
    _kalemleri_yaz(con, fatura_id, kalemler)
    con.commit()
    con.close()
    return fatura_id


def _kalemleri_yaz(con, fatura_id, kalemler):
    for k in kalemler or []:
        con.execute(
            f"INSERT INTO kalemler(fatura_id, {', '.join(_KALEM_ALANLAR)}) "
            f"VALUES(?, {', '.join('?' * len(_KALEM_ALANLAR))})",
            [fatura_id] + [k.get(a) for a in _KALEM_ALANLAR],
        )


def fatura_guncelle(fatura_id, veri, kalemler=None):
    """Basligi gunceller; kalemler None degilse tumunu yeniden yazar."""
    duzenlenebilir = [a for a in _FATURA_ALANLAR if a in veri]
    con = _baglanti()
    if duzenlenebilir:
        con.execute(
            f"UPDATE faturalar SET {', '.join(a + '=?' for a in duzenlenebilir)} WHERE id=?",
            [veri[a] for a in duzenlenebilir] + [fatura_id],
        )
    if kalemler is not None:
        con.execute("DELETE FROM kalemler WHERE fatura_id=?", (fatura_id,))
        _kalemleri_yaz(con, fatura_id, kalemler)
    con.commit()
    con.close()


def fatura_sil(fatura_id):
    con = _baglanti()
    row = con.execute("SELECT belge_yolu FROM faturalar WHERE id=?", (fatura_id,)).fetchone()
    con.execute("DELETE FROM faturalar WHERE id=?", (fatura_id,))
    con.commit()
    con.close()
    return row["belge_yolu"] if row else ""


def belge_kullanim_sayisi(belge_yolu):
    con = _baglanti()
    row = con.execute("SELECT COUNT(*) AS n FROM faturalar WHERE belge_yolu=?",
                      (belge_yolu,)).fetchone()
    con.close()
    return row["n"]


def fatura_getir(fatura_id):
    con = _baglanti()
    f = con.execute("SELECT * FROM faturalar WHERE id=?", (fatura_id,)).fetchone()
    if f is None:
        con.close()
        return None
    kalemler = con.execute(
        "SELECT * FROM kalemler WHERE fatura_id=? ORDER BY sira, id", (fatura_id,)
    ).fetchall()
    con.close()
    sonuc = dict(f)
    sonuc["kalemler"] = [dict(k) for k in kalemler]
    return sonuc


# ---------------------------------------------------------------- sorgu
def _filtre_sql(f):
    """Ortak filtre kosullarini (sql parcasi, parametreler) uretir."""
    kosullar, params = [], []
    if f.get("urun"):
        kosullar.append(
            "EXISTS (SELECT 1 FROM kalemler k WHERE k.fatura_id = fa.id "
            "AND trl(k.mal_hizmet) LIKE trl(?))")
        params.append("%" + f["urun"] + "%")
    if f.get("fatura_no"):
        kosullar.append("trl(fa.fatura_no) LIKE trl(?)")
        params.append("%" + f["fatura_no"] + "%")
    if f.get("taraf"):
        kosullar.append(
            "(trl(fa.satici_unvan) LIKE trl(?) OR trl(fa.alici_unvan) LIKE trl(?) "
            "OR fa.satici_vkn LIKE ? OR fa.alici_vkn LIKE ?)")
        params.extend(["%" + f["taraf"] + "%"] * 4)
    if f.get("baslangic"):
        kosullar.append("fa.fatura_tarihi >= ? AND fa.fatura_tarihi <> ''")
        params.append(f["baslangic"])
    if f.get("bitis"):
        kosullar.append("fa.fatura_tarihi <= ? AND fa.fatura_tarihi <> ''")
        params.append(f["bitis"])
    if f.get("yon") in ("alis", "satis"):
        kosullar.append("fa.yon = ?")
        params.append(f["yon"])
    if f.get("durum") in GECERLI_DURUMLAR:
        kosullar.append("fa.durum = ?")
        params.append(f["durum"])
    sql = (" WHERE " + " AND ".join(kosullar)) if kosullar else ""
    return sql, params


def faturalari_sorgula(filtreler, limit=200, sayfa=0):
    """Fatura ozet satirlari + toplam sayi + tutar toplamlari."""
    kosul, params = _filtre_sql(filtreler)
    con = _baglanti()
    ozet = con.execute(
        "SELECT COUNT(*) AS adet, "
        "COALESCE(SUM(fa.mal_hizmet_toplam),0) AS matrah_toplam, "
        "COALESCE(SUM(fa.kdv_toplam),0) AS kdv_toplam, "
        "COALESCE(SUM(fa.odenecek_tutar),0) AS odenecek_toplam "
        "FROM faturalar fa" + kosul, params).fetchone()
    satirlar = con.execute(
        "SELECT fa.id, fa.dosya_adi, fa.fatura_no, fa.fatura_tarihi, fa.yon, "
        "fa.satici_unvan, fa.satici_vkn, fa.alici_unvan, fa.alici_vkn, "
        "fa.mal_hizmet_toplam, fa.kdv_toplam, fa.odenecek_tutar, "
        "fa.kaynak, fa.durum, fa.uyarilar, "
        "(SELECT COUNT(*) FROM kalemler k WHERE k.fatura_id = fa.id) AS kalem_sayisi "
        "FROM faturalar fa" + kosul +
        " ORDER BY fa.fatura_tarihi DESC, fa.id DESC LIMIT ? OFFSET ?",
        params + [limit, sayfa * limit]).fetchall()
    con.close()
    return {"toplam": dict(ozet), "satirlar": [dict(r) for r in satirlar],
            "limit": limit, "sayfa": sayfa}


def kalemleri_sorgula(filtreler, limit=500, sayfa=0):
    """Kalem (urun) bazli satirlar; urun filtresi dogrudan kaleme uygulanir."""
    kosul, params = _filtre_sql({**filtreler, "urun": ""})
    kalem_kosul = ""
    kalem_params = []
    if filtreler.get("urun"):
        kalem_kosul = (" AND " if kosul else " WHERE ") + \
            "trl(k.mal_hizmet) LIKE trl(?)"
        kalem_params = ["%" + filtreler["urun"] + "%"]
    govde = (
        "FROM kalemler k JOIN faturalar fa ON fa.id = k.fatura_id" +
        kosul + kalem_kosul)
    con = _baglanti()
    ozet = con.execute(
        "SELECT COUNT(*) AS adet, COALESCE(SUM(k.miktar),0) AS miktar_toplam, "
        "COALESCE(SUM(k.kdv_tutari),0) AS kdv_toplam, "
        "COALESCE(SUM(k.tutar),0) AS tutar_toplam " + govde,
        params + kalem_params).fetchone()
    satirlar = con.execute(
        "SELECT k.id, k.fatura_id, fa.fatura_no, fa.fatura_tarihi, fa.yon, "
        "fa.satici_unvan, fa.alici_unvan, k.sira, k.mal_hizmet, k.miktar, k.birim, "
        "k.birim_fiyat, k.kdv_orani, k.kdv_tutari, k.tutar, fa.durum " + govde +
        " ORDER BY fa.fatura_tarihi DESC, fa.id DESC, k.sira LIMIT ? OFFSET ?",
        params + kalem_params + [limit, sayfa * limit]).fetchall()
    con.close()
    return {"toplam": dict(ozet), "satirlar": [dict(r) for r in satirlar],
            "limit": limit, "sayfa": sayfa}


def fatura_disa_aktarim(filtreler):
    """Excel icin: filtreye uyan tum baslik + kalem satirlari (limitsiz)."""
    kosul, params = _filtre_sql(filtreler)
    con = _baglanti()
    basliklar = con.execute("SELECT fa.* FROM faturalar fa" + kosul +
                            " ORDER BY fa.fatura_tarihi, fa.id", params).fetchall()
    idler = [r["id"] for r in basliklar]
    kalemler = []
    if idler:
        # SQLite degisken siniri icin parcalara bol
        for i in range(0, len(idler), 500):
            parca = idler[i:i + 500]
            kalemler.extend(con.execute(
                "SELECT k.*, fa.fatura_no, fa.fatura_tarihi, fa.yon, "
                "fa.satici_unvan, fa.satici_vkn, fa.alici_unvan, fa.alici_vkn "
                "FROM kalemler k JOIN faturalar fa ON fa.id = k.fatura_id "
                f"WHERE k.fatura_id IN ({', '.join('?' * len(parca))}) "
                "ORDER BY fa.fatura_tarihi, fa.id, k.sira", parca).fetchall())
    con.close()
    urun = _tr_kucuk((filtreler.get("urun") or "").strip())
    if urun:
        kalemler = [k for k in kalemler if urun in _tr_kucuk(k["mal_hizmet"])]
    return [dict(r) for r in basliklar], [dict(r) for r in kalemler]


def ocr_bekleyenler():
    con = _baglanti()
    rows = con.execute(
        "SELECT id, dosya_adi, belge_yolu FROM faturalar WHERE durum='ocr_bekliyor' "
        "ORDER BY id").fetchall()
    con.close()
    return [dict(r) for r in rows]


def istatistik():
    con = _baglanti()
    genel = con.execute(
        "SELECT COUNT(*) AS fatura, "
        "(SELECT COUNT(*) FROM kalemler) AS kalem, "
        "SUM(CASE WHEN durum='kontrol' THEN 1 ELSE 0 END) AS kontrol, "
        "SUM(CASE WHEN durum='ocr_bekliyor' THEN 1 ELSE 0 END) AS ocr_bekliyor, "
        "SUM(CASE WHEN yon='alis' THEN 1 ELSE 0 END) AS alis, "
        "SUM(CASE WHEN yon='satis' THEN 1 ELSE 0 END) AS satis "
        "FROM faturalar").fetchone()
    con.close()
    return {k: (genel[k] or 0) for k in genel.keys()}


# ---------------------------------------------------------------- yedek
def yedek_al():
    os.makedirs(YEDEK_DIR, exist_ok=True)
    hedef = os.path.join(
        YEDEK_DIR, "faturalar_" + datetime.now().strftime("%Y%m%d_%H%M%S") + ".db")
    con = _baglanti()
    yedek_con = sqlite3.connect(hedef)
    con.backup(yedek_con)
    yedek_con.close()
    con.close()
    return hedef


def yedekleri_listele():
    if not os.path.isdir(YEDEK_DIR):
        return []
    dosyalar = sorted((d for d in os.listdir(YEDEK_DIR) if d.endswith(".db")), reverse=True)
    return [{"dosya": d,
             "boyut_kb": round(os.path.getsize(os.path.join(YEDEK_DIR, d)) / 1024)}
            for d in dosyalar]


def yedekten_geri_yukle(dosya):
    kaynak = os.path.join(YEDEK_DIR, dosya)
    if not os.path.isfile(kaynak):
        raise ValueError("Yedek dosyasi bulunamadi: " + dosya)
    shutil.copy2(kaynak, DB_PATH)
