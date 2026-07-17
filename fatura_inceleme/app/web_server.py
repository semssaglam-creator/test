"""Yerel web sunucusu: JSON API + tek sayfalik arayuz.

Yalnizca Python standart kutuphanesi kullanilir (http.server, json).
"""
import base64
import hashlib
import json
import os
import posixpath
import re
import urllib.parse
from datetime import datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from . import db, ocr
from .ayristirici import fatura_ayristir, sayi_coz, tarih_iso
from .excel_export import rapor_uret
from .pdf_okuma import pdf_oku

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WEB_DIR = os.path.join(BASE_DIR, "web")
BELGE_DIR = os.path.join(BASE_DIR, "belgeler")
RAPOR_DIR = os.path.join(BASE_DIR, "raporlar")

XLSX_MIME = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"


class ApiHata(Exception):
    """Kullaniciya gosterilecek hata mesaji."""


# ---------------------------------------------------------------- yukleme
def _belge_kaydet(ad, icerik):
    """PDF'i belgeler/ altina icerik ozetiyle kaydeder, goreli yol dondurur."""
    os.makedirs(BELGE_DIR, exist_ok=True)
    ozet = hashlib.sha1(icerik).hexdigest()[:12]
    guvenli = re.sub(r"[^A-Za-z0-9çğıöşüÇĞİÖŞÜ._-]+", "_", ad)[:80] or "belge.pdf"
    if not guvenli.lower().endswith(".pdf"):
        guvenli += ".pdf"
    dosya = f"{ozet}_{guvenli}"
    yol = os.path.join(BELGE_DIR, dosya)
    if not os.path.isfile(yol):
        with open(yol, "wb") as f:
            f.write(icerik)
    return dosya


def _fatura_isle(ad, icerik):
    """Tek PDF'i okur, ayristirir ve kaydeder; arayuz icin sonuc dondurur."""
    if not icerik.startswith(b"%PDF"):
        raise ApiHata("Dosya bir PDF degil.")

    metin, kaynak, hata = pdf_oku(icerik)
    belge = _belge_kaydet(ad, icerik)

    if not metin:
        # Buyuk olasilikla taranmis PDF ve OCR araclari eksik:
        # kaydi 'OCR bekliyor' olarak ac, PDF sakli kalsin
        fatura_id = db.fatura_ekle({
            "dosya_adi": ad, "belge_yolu": belge, "kaynak": "ocr",
            "durum": "ocr_bekliyor", "uyarilar": hata, "para_birimi": "TL",
        }, [])
        return {"id": fatura_id, "durum": "ocr_bekliyor", "uyari": hata}

    baslik, kalemler, uyarilar = fatura_ayristir(metin)

    mevcut = db.mukerrer_var_mi(baslik["fatura_no"], baslik["ettn"],
                                baslik["satici_vkn"])
    if mevcut:
        raise ApiHata(
            f"Bu fatura daha önce kaydedilmiş (No: {baslik['fatura_no'] or '?'}, "
            f"kayıt #{mevcut}); tekrar eklenmedi.")

    if kaynak == "ocr":
        uyarilar.insert(0, "OCR ile okundu; alanları asıl PDF ile karşılaştırın.")

    baslik.update({
        "dosya_adi": ad, "belge_yolu": belge, "kaynak": kaynak,
        "yon": db.yon_belirle(baslik["satici_vkn"], baslik["alici_vkn"]),
        "durum": "kontrol" if uyarilar else "tamam",
        "uyarilar": " | ".join(uyarilar), "ham_metin": metin[:200000],
    })
    fatura_id = db.fatura_ekle(baslik, kalemler)
    return {"id": fatura_id, "durum": baslik["durum"],
            "fatura_no": baslik["fatura_no"],
            "fatura_tarihi": baslik["fatura_tarihi"],
            "satici_unvan": baslik["satici_unvan"],
            "alici_unvan": baslik["alici_unvan"],
            "odenecek_tutar": baslik["odenecek_tutar"],
            "kalem_sayisi": len(kalemler),
            "uyari": " | ".join(uyarilar)}


def _pdfleri_yukle(veri):
    dosyalar = veri.get("dosyalar") or []
    if not dosyalar:
        raise ApiHata("PDF dosyasi gonderilmedi.")
    if len(dosyalar) > 25:
        raise ApiHata("Tek istekte en fazla 25 dosya islenebilir "
                      "(arayuz otomatik parcalar).")
    sonuclar = []
    for d in dosyalar:
        ad = d.get("ad", "dosya.pdf")
        try:
            icerik = base64.b64decode(d.get("icerik", ""), validate=True)
            sonuc = _fatura_isle(ad, icerik)
            sonuc.update({"ad": ad, "tamam": True})
        except ApiHata as exc:
            sonuc = {"ad": ad, "tamam": False, "hata": str(exc)}
        except Exception as exc:  # noqa: BLE001 - tek dosya digerlerini durdurmasin
            sonuc = {"ad": ad, "tamam": False, "hata": f"Islenemedi: {exc}"}
        sonuclar.append(sonuc)
    return {"sonuclar": sonuclar}


# ---------------------------------------------------------------- guncelleme
_SAYI_ALANLARI = ("mal_hizmet_toplam", "toplam_iskonto", "kdv_toplam",
                  "vergiler_dahil_toplam", "odenecek_tutar")
_METIN_ALANLARI = ("fatura_no", "ettn", "fatura_tipi", "satici_unvan", "satici_vkn",
                   "alici_unvan", "alici_vkn", "para_birimi", "notlar", "dosya_adi")


def _baslik_hazirla(veri):
    """Arayuzden gelen baslik alanlarini dogrular/donusturur."""
    b = {}
    for alan in _METIN_ALANLARI:
        if alan in veri:
            b[alan] = str(veri.get(alan) or "").strip()
    for alan in _SAYI_ALANLARI:
        if alan in veri:
            b[alan] = sayi_coz(veri.get(alan))
    if "fatura_tarihi" in veri:
        ham = str(veri.get("fatura_tarihi") or "").strip()
        b["fatura_tarihi"] = tarih_iso(ham)
        if ham and not b["fatura_tarihi"]:
            raise ApiHata(f"Tarih anlasilamadi: {ham} (GG.AA.YYYY yazin)")
    if "yon" in veri:
        if veri["yon"] not in db.GECERLI_YONLER:
            raise ApiHata("Gecersiz yon.")
        b["yon"] = veri["yon"]
    if "durum" in veri:
        if veri["durum"] not in db.GECERLI_DURUMLAR:
            raise ApiHata("Gecersiz durum.")
        b["durum"] = veri["durum"]
    return b


def _kalemleri_hazirla(veri):
    if "kalemler" not in veri:
        return None
    kalemler = []
    for i, k in enumerate(veri.get("kalemler") or [], 1):
        ad = str(k.get("mal_hizmet") or "").strip()
        if not ad:
            continue  # bos satirlar atlanir
        kalemler.append({
            "sira": int(k["sira"]) if str(k.get("sira") or "").strip().isdigit() else i,
            "mal_hizmet": ad[:300],
            "birim": str(k.get("birim") or "").strip(),
            "miktar": sayi_coz(k.get("miktar")),
            "birim_fiyat": sayi_coz(k.get("birim_fiyat")),
            "kdv_orani": sayi_coz(k.get("kdv_orani")),
            "kdv_tutari": sayi_coz(k.get("kdv_tutari")),
            "tutar": sayi_coz(k.get("tutar")),
        })
    return kalemler


def _fatura_guncelle(veri):
    fatura_id = int(veri.get("id", 0))
    mevcut = db.fatura_getir(fatura_id)
    if mevcut is None:
        raise ApiHata("Fatura bulunamadi.")
    baslik = _baslik_hazirla(veri)
    if not baslik.get("yon"):
        # Yon 'belirsiz' birakildiysa mukellef VKN'sinden yeniden hesapla
        baslik["yon"] = db.yon_belirle(
            baslik.get("satici_vkn", mevcut["satici_vkn"]),
            baslik.get("alici_vkn", mevcut["alici_vkn"]))
    if "durum" not in baslik:
        baslik["durum"] = "tamam"  # elle duzenlenen kayit onaylanmis sayilir
    baslik["uyarilar"] = str(veri.get("uyarilar") or "").strip()
    db.fatura_guncelle(fatura_id, baslik, _kalemleri_hazirla(veri))
    return {"tamam": True}


def _elle_fatura(veri):
    baslik = _baslik_hazirla(veri)
    if not baslik.get("fatura_no") and not baslik.get("satici_unvan"):
        raise ApiHata("En azindan Fatura No veya Satici Unvani girilmelidir.")
    mevcut = db.mukerrer_var_mi(baslik.get("fatura_no", ""), baslik.get("ettn", ""),
                                baslik.get("satici_vkn", ""))
    if mevcut:
        raise ApiHata(f"Bu fatura numarasi zaten kayitli (kayit #{mevcut}).")
    baslik.setdefault("para_birimi", "TL")
    baslik["kaynak"] = "elle"
    baslik["durum"] = "tamam"
    if not baslik.get("yon"):
        baslik["yon"] = db.yon_belirle(baslik.get("satici_vkn", ""),
                                       baslik.get("alici_vkn", ""))
    fatura_id = db.fatura_ekle(baslik, _kalemleri_hazirla(veri) or [])
    return {"tamam": True, "id": fatura_id}


def _ocr_yenile(veri):
    """OCR bekleyen (veya secilen) kaydi sakli PDF'inden yeniden okur."""
    fatura_id = int(veri.get("id", 0))
    kayit = db.fatura_getir(fatura_id)
    if kayit is None:
        raise ApiHata("Fatura bulunamadi.")
    yol = os.path.join(BELGE_DIR, posixpath.basename(kayit["belge_yolu"] or ""))
    if not kayit["belge_yolu"] or not os.path.isfile(yol):
        raise ApiHata("Bu kaydin sakli PDF'i yok; alanlari elle girin.")
    with open(yol, "rb") as f:
        icerik = f.read()

    metin, kaynak, hata = pdf_oku(icerik)
    if not metin:
        raise ApiHata(hata or "PDF yine okunamadi.")

    baslik, kalemler, uyarilar = fatura_ayristir(metin)
    if kaynak == "ocr":
        uyarilar.insert(0, "OCR ile okundu; alanları asıl PDF ile karşılaştırın.")
    baslik.update({
        "kaynak": kaynak,
        "yon": kayit["yon"] or db.yon_belirle(baslik["satici_vkn"], baslik["alici_vkn"]),
        "durum": "kontrol" if uyarilar else "tamam",
        "uyarilar": " | ".join(uyarilar), "ham_metin": metin[:200000],
    })
    db.fatura_guncelle(fatura_id, baslik, kalemler)
    return {"tamam": True, "durum": baslik["durum"], "uyari": " | ".join(uyarilar)}


def _ayarlari_kaydet(veri):
    vkn = re.sub(r"\D", "", str(veri.get("mukellef_vkn") or ""))
    if vkn and len(vkn) not in (10, 11):
        raise ApiHata("VKN 10, TCKN 11 haneli olmalidir.")
    db.ayar_kaydet("mukellef_vkn", vkn)
    db.ayar_kaydet("mukellef_ad", str(veri.get("mukellef_ad") or "").strip())
    guncellenen = 0
    if veri.get("yonleri_hesapla"):
        for f in db.faturalari_sorgula({}, limit=100000)["satirlar"]:
            yeni = db.yon_belirle(f["satici_vkn"], f["alici_vkn"])
            if yeni != f["yon"]:
                db.fatura_guncelle(f["id"], {"yon": yeni})
                guncellenen += 1
    return {"tamam": True, "yon_guncellenen": guncellenen}


def _filtreler(params):
    def deger(ad):
        return (params.get(ad, [""])[0] or "").strip()
    return {
        "urun": deger("urun"), "fatura_no": deger("fatura_no"),
        "taraf": deger("taraf"),
        "baslangic": tarih_iso(deger("baslangic")),
        "bitis": tarih_iso(deger("bitis")),
        "yon": deger("yon"), "durum": deger("durum"),
    }


# ---------------------------------------------------------------- sunucu
class Istekci(BaseHTTPRequestHandler):
    server_version = "FaturaInceleme/1.0"

    def log_message(self, format, *args):  # noqa: A002 - sessiz calis
        pass

    def _json_yanit(self, veri, durum=200):
        govde = json.dumps(veri, ensure_ascii=False).encode("utf-8")
        self.send_response(durum)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(govde)))
        self.end_headers()
        self.wfile.write(govde)

    def _hata(self, mesaj, durum=400):
        self._json_yanit({"hata": mesaj}, durum)

    def _govdeyi_oku(self):
        uzunluk = int(self.headers.get("Content-Length", 0))
        if uzunluk == 0:
            return {}
        if uzunluk > 300 * 1024 * 1024:
            raise ApiHata("Istek cok buyuk.")
        return json.loads(self.rfile.read(uzunluk).decode("utf-8"))

    def _istek_guvenli_mi(self, yazma=False):
        """DNS rebinding / siteler arasi POST (CSRF) korumasi."""
        host = (self.headers.get("Host") or "").split(":")[0].strip("[]").lower()
        if host not in ("127.0.0.1", "localhost", "::1"):
            self._hata("Gecersiz Host basligi.", 403)
            return False
        if yazma:
            origin = self.headers.get("Origin")
            if origin:
                o = urllib.parse.urlparse(origin)
                if (o.hostname or "").lower() not in ("127.0.0.1", "localhost", "::1"):
                    self._hata("Istek reddedildi (siteler arasi).", 403)
                    return False
        return True

    # ------------------------------------------------------------------
    def do_GET(self):
        if not self._istek_guvenli_mi():
            return
        parsed = urllib.parse.urlparse(self.path)
        yol = parsed.path
        params = urllib.parse.parse_qs(parsed.query)
        try:
            if yol in ("/", "/index.html"):
                self._dosya_gonder(os.path.join(WEB_DIR, "index.html"),
                                   "text/html; charset=utf-8")
            elif yol == "/api/durum":
                self._json_yanit({
                    "ocr": ocr.durum(), "istatistik": db.istatistik(),
                    "mukellef_vkn": db.ayar_getir("mukellef_vkn"),
                    "mukellef_ad": db.ayar_getir("mukellef_ad"),
                    "ocr_bekleyen": db.ocr_bekleyenler(),
                })
            elif yol == "/api/faturalar":
                sayfa = int(params.get("sayfa", ["0"])[0])
                self._json_yanit(db.faturalari_sorgula(_filtreler(params), sayfa=sayfa))
            elif yol == "/api/kalemler":
                sayfa = int(params.get("sayfa", ["0"])[0])
                self._json_yanit(db.kalemleri_sorgula(_filtreler(params), sayfa=sayfa))
            elif yol == "/api/fatura":
                f = db.fatura_getir(int(params["id"][0]))
                if f is None:
                    raise ApiHata("Fatura bulunamadi.")
                self._json_yanit(f)
            elif yol == "/pdf":
                self._pdf_gonder(int(params.get("id", ["0"])[0]))
            elif yol == "/rapor":
                self._rapor_indir(params)
            elif yol == "/api/yedekler":
                self._json_yanit(db.yedekleri_listele())
            else:
                self._hata("Bulunamadi", 404)
        except ApiHata as exc:
            self._hata(str(exc))
        except (KeyError, ValueError) as exc:
            self._hata(f"Gecersiz istek: {exc}")
        except Exception as exc:  # noqa: BLE001
            self._hata(f"Sunucu hatasi: {exc}", 500)

    def do_POST(self):
        if not self._istek_guvenli_mi(yazma=True):
            return
        yol = urllib.parse.urlparse(self.path).path
        try:
            veri = self._govdeyi_oku()
            if yol == "/api/fatura/yukle":
                self._json_yanit(_pdfleri_yukle(veri))
            elif yol == "/api/fatura/guncelle":
                self._json_yanit(_fatura_guncelle(veri))
            elif yol == "/api/fatura/sil":
                belge = db.fatura_sil(int(veri["id"]))
                # Ayni PDF'i kullanan baska kayit kalmadiysa diskten de sil
                if belge and db.belge_kullanim_sayisi(belge) == 0:
                    yolu = os.path.join(BELGE_DIR, posixpath.basename(belge))
                    if os.path.isfile(yolu):
                        try:
                            os.remove(yolu)
                        except OSError:
                            pass
                self._json_yanit({"tamam": True})
            elif yol == "/api/fatura/elle":
                self._json_yanit(_elle_fatura(veri))
            elif yol == "/api/ocr_yenile":
                self._json_yanit(_ocr_yenile(veri))
            elif yol == "/api/ayarlar":
                self._json_yanit(_ayarlari_kaydet(veri))
            elif yol == "/api/yedek_al":
                hedef = db.yedek_al()
                self._json_yanit({"dosya": os.path.basename(hedef)})
            elif yol == "/api/geri_yukle":
                dosya = posixpath.basename(veri.get("dosya", ""))
                if not dosya.endswith(".db"):
                    raise ApiHata("Gecersiz yedek dosyasi.")
                db.yedekten_geri_yukle(dosya)
                self._json_yanit({"tamam": True})
            else:
                self._hata("Bulunamadi", 404)
        except ApiHata as exc:
            self._hata(str(exc))
        except (KeyError, ValueError) as exc:
            self._hata(f"Gecersiz istek: {exc}")
        except Exception as exc:  # noqa: BLE001
            self._hata(f"Sunucu hatasi: {exc}", 500)

    # ------------------------------------------------------------------
    def _dosya_gonder(self, dosya_yolu, icerik_turu):
        if not os.path.isfile(dosya_yolu):
            self._hata("Dosya bulunamadi", 404)
            return
        with open(dosya_yolu, "rb") as f:
            govde = f.read()
        self.send_response(200)
        self.send_header("Content-Type", icerik_turu)
        self.send_header("Content-Length", str(len(govde)))
        self.end_headers()
        self.wfile.write(govde)

    def _pdf_gonder(self, fatura_id):
        kayit = db.fatura_getir(fatura_id)
        if kayit is None or not kayit["belge_yolu"]:
            self._hata("Bu kaydin sakli PDF'i yok.", 404)
            return
        yol = os.path.join(BELGE_DIR, posixpath.basename(kayit["belge_yolu"]))
        if not os.path.isfile(yol):
            self._hata("PDF dosyasi bulunamadi.", 404)
            return
        with open(yol, "rb") as f:
            govde = f.read()
        self.send_response(200)
        self.send_header("Content-Type", "application/pdf")
        self.send_header("Content-Disposition",
                         f'inline; filename="{urllib.parse.quote(kayit["dosya_adi"] or "fatura.pdf")}"')
        self.send_header("Content-Length", str(len(govde)))
        self.end_headers()
        self.wfile.write(govde)

    def _rapor_indir(self, params):
        basliklar, kalemler = db.fatura_disa_aktarim(_filtreler(params))
        if not basliklar:
            self._hata("Filtreye uyan fatura yok.")
            return
        govde = rapor_uret(basliklar, kalemler)
        dosya_adi = "fatura_raporu_" + datetime.now().strftime("%Y%m%d_%H%M") + ".xlsx"
        os.makedirs(RAPOR_DIR, exist_ok=True)
        try:
            with open(os.path.join(RAPOR_DIR, dosya_adi), "wb") as f:
                f.write(govde)
        except OSError:
            pass  # yerel kopya yazilamazsa indirme yine calissin
        self.send_response(200)
        self.send_header("Content-Type", XLSX_MIME)
        self.send_header("Content-Disposition",
                         f'attachment; filename="{urllib.parse.quote(dosya_adi)}"')
        self.send_header("Content-Length", str(len(govde)))
        self.end_headers()
        self.wfile.write(govde)


def sunucu_baslat(port=8766):
    db.init_db()
    return ThreadingHTTPServer(("127.0.0.1", port), Istekci)
