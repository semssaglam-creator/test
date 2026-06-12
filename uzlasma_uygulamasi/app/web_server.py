"""Yerel web sunucusu: JSON API + tek sayfalik arayuz.

Yalnizca Python standart kutuphanesi kullanilir (http.server, json).
"""
import json
import os
import posixpath
import urllib.parse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from . import db
from .excel_export import puantaj_cetveli_olustur, tutanak_olustur_excel
from .paste_parser import dilekce_ayristir
from .tarih_util import simdi_tr, tr_to_iso, tr_tarih_to_iso_gun

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WEB_DIR = os.path.join(BASE_DIR, "web")
TUTANAK_DIR = os.path.join(BASE_DIR, "tutanaklar")
PUANTAJ_DIR = os.path.join(BASE_DIR, "puantajlar")


class ApiHata(Exception):
    """Kullaniciya gosterilecek hata mesaji."""


def _tutanak_uret(veri):
    mukellef_id = veri.get("mukellef_id")
    sonuc = veri.get("sonuc")
    kalemler = veri.get("kalemler") or []
    uye_idleri = veri.get("komisyon_uye_idleri") or []
    toplanti_tr = (veri.get("toplanti_tarih_saat") or "").strip()
    davet_tr = (veri.get("davet_tarih_saat") or "").strip()

    if not mukellef_id:
        raise ApiHata("Once bir mukellef secin.")
    if sonuc not in ("uzlasildi", "uzlasilamadi", "gelmedi"):
        raise ApiHata("Gecersiz sonuc.")
    if not kalemler:
        raise ApiHata("Uzlasmaya konu en az bir ihbarname secmelisiniz.")
    if not uye_idleri:
        raise ApiHata("En az bir komisyon uyesi secmelisiniz.")
    if not toplanti_tr:
        raise ApiHata("Toplanti tarih/saat bos olamaz.")
    if sonuc == "gelmedi" and not davet_tr:
        raise ApiHata("Gelmedi sonucunda 'Davet Edilen Tarih/Saat' bos olamaz.")

    tum_uyeler = {u["id"]: u for u in db.komisyon_uyeleri_listele()}
    imzalayanlar = [tum_uyeler[i] for i in uye_idleri if i in tum_uyeler]
    if not imzalayanlar:
        raise ApiHata("Secilen komisyon uyeleri bulunamadi.")

    kalemler_db = []
    kalemler_excel = []
    ihbarname_idleri = set()
    for k in kalemler:
        satirlar = db.ihbarname_satirlarini_getir(k["ihbarname_id"])
        satir = next((s for s in satirlar if s["id"] == k["ceza_satiri_id"]), None)
        if satir is None:
            raise ApiHata(f"Ceza satiri bulunamadi: {k['ceza_satiri_id']}")
        try:
            oran = float(str(k.get("indirim_orani", 80)).replace(",", "."))
        except ValueError:
            oran = 80.0
        uzlasilan = 0.0 if sonuc == "gelmedi" else round(satir["miktar"] * (1 - oran / 100), 2)
        kalemler_db.append((satir["id"], k["ihbarname_id"], oran, uzlasilan))
        kalemler_excel.append({
            "fis_no": k.get("fis_no", ""),
            "vergi_turu_kod": satir["vergi_turu_kod"],
            "ceza_kodu": satir["ceza_kodu"],
            "donem": satir["donem"],
            "miktar": satir["miktar"],
            "uzlasilan_tutar": uzlasilan,
        })
        ihbarname_idleri.add(k["ihbarname_id"])

    kurum = db.get_kurum_bilgileri()
    mukellef = db.mukellef_getir(mukellef_id)
    tutanak_no = db.sonraki_tutanak_no()

    os.makedirs(TUTANAK_DIR, exist_ok=True)
    guvenli_isim = "".join(c if c.isalnum() else "_" for c in mukellef["ad_unvan"])[:40]
    guvenli_no = tutanak_no.replace("/", "_")
    dosya_adi = f"{guvenli_no}_{guvenli_isim}_{sonuc}.xlsx"
    dosya_yolu = os.path.join(TUTANAK_DIR, dosya_adi)

    tutanak_olustur_excel(
        dosya_yolu, kurum, tutanak_no, toplanti_tr, davet_tr, mukellef, kalemler_excel,
        imzalayanlar, sonuc,
    )

    db.tutanak_olustur(
        tutanak_no, mukellef_id, sonuc, tr_to_iso(toplanti_tr), tr_to_iso(davet_tr),
        veri.get("notlar", ""), kalemler_db, [u["id"] for u in imzalayanlar], dosya_yolu,
    )

    return {"tutanak_no": tutanak_no, "dosya_adi": dosya_adi}


def _miktar_coz(deger):
    """'1.234,56' / '1234.56' / 1234.56 -> float."""
    if isinstance(deger, (int, float)):
        return float(deger)
    s = str(deger or "0").strip()
    if "," in s:
        s = s.replace(".", "").replace(",", ".")
    return float(s or 0)


def _dilekce_kaydet(veri):
    m = veri.get("mukellef") or {}
    satirlar = veri.get("satirlar") or []
    if not (m.get("ad_unvan") or "").strip():
        raise ApiHata("Mukellef Ad Soyad / Unvan alani bos olamaz.")
    if not satirlar:
        raise ApiHata("Kaydedilecek ihbarname/ceza satiri yok.")
    for s in satirlar:
        if not str(s.get("fis_no", "")).strip():
            raise ApiHata("Bos 'Ihbarname Fis No' alani olan satir var.")
        try:
            _miktar_coz(s.get("miktar"))
        except ValueError:
            raise ApiHata(f"Gecersiz miktar: {s.get('miktar')}")

    # Mukerrer kayit kontrolu: ayni fis no daha once kaydedildiyse kaydetme
    fisler = {str(s["fis_no"]).strip() for s in satirlar}
    mevcutlar = db.mevcut_fis_nolar(fisler)
    if mevcutlar:
        raise ApiHata(
            "Bu ihbarname(ler) daha önce kaydedilmiş, kayıt yapılmadı: "
            + ", ".join(sorted(mevcutlar))
        )

    mukellef_id = db.mukellef_bul_veya_olustur(
        m.get("ad_unvan", "").strip(), m.get("vkn_tckn", "").strip(),
        m.get("adres", "").strip(), m.get("telefon", "").strip(),
    )

    onay_zamani = veri.get("dilekce_onay_zamani", "")
    ihbarname_id_cache = {}
    for s in satirlar:
        fis_no = str(s["fis_no"]).strip()
        if fis_no not in ihbarname_id_cache:
            ihbarname_id_cache[fis_no] = db.ihbarname_ekle(
                mukellef_id, fis_no, str(s.get("duzenleme_tarihi", "")).strip(),
                str(s.get("teblig_tarihi", "")).strip(), onay_zamani,
            )
        miktar = _miktar_coz(s.get("miktar"))
        db.ceza_satiri_ekle(
            ihbarname_id_cache[fis_no], str(s.get("vergi_turu_kod", "")).strip(),
            str(s.get("ceza_kodu", "")).strip(), str(s.get("ceza_nedeni", "")).strip(),
            str(s.get("donem", "")).strip(), miktar,
        )
    return {"ihbarname_sayisi": len(ihbarname_id_cache), "satir_sayisi": len(satirlar),
            "mukellef_id": mukellef_id}


def _pdf_dilekceleri_ayristir(veri):
    """Yuklenen PDF dosyalarini (base64) metne cevirip ayristirir."""
    import base64

    from .paste_parser import pdf_metni_cikar

    dosyalar = veri.get("dosyalar") or []
    if not dosyalar:
        raise ApiHata("PDF dosyasi gonderilmedi.")
    if len(dosyalar) > 50:
        raise ApiHata("Tek seferde en fazla 50 dosya yuklenebilir.")

    sonuclar = []
    for d in dosyalar:
        ad = d.get("ad", "dosya.pdf")
        try:
            icerik = base64.b64decode(d.get("icerik", ""), validate=True)
            if not icerik.startswith(b"%PDF"):
                raise ApiHata("Dosya bir PDF degil.")
            metin = pdf_metni_cikar(icerik)
            ayrisan = dilekce_ayristir(metin)
            if not ayrisan["mukellef"]["ad_unvan"] and not ayrisan["ihbarnameler"]:
                raise ApiHata("Dilekce alanlari bulunamadi (beklenen Dijital VD bicimi degil).")
            sonuclar.append({"ad": ad, "tamam": True, "veri": ayrisan})
        except ApiHata as exc:
            sonuclar.append({"ad": ad, "tamam": False, "hata": str(exc)})
        except Exception as exc:  # noqa: BLE001 - tek dosya hatasi digerlerini durdurmasin
            sonuclar.append({"ad": ad, "tamam": False, "hata": f"PDF okunamadi: {exc}"})
    return {"sonuclar": sonuclar}


def _tutanak_sonuc_degistir(veri):
    from .tarih_util import iso_to_tr

    tutanak_id = int(veri.get("id", 0))
    yeni_sonuc = veri.get("sonuc")
    if yeni_sonuc not in ("uzlasildi", "uzlasilamadi", "gelmedi"):
        raise ApiHata("Gecersiz sonuc.")

    t = next((x for x in db.tutanak_gecmisi() if x["id"] == tutanak_id), None)
    if t is None:
        raise ApiHata("Tutanak bulunamadi.")

    davet_tr = (veri.get("davet_tarih_saat") or "").strip()
    davet_iso = tr_to_iso(davet_tr) if davet_tr else None
    mevcut_davet_tr = iso_to_tr(t["davet_tarih_saat"] or "")
    if yeni_sonuc == "gelmedi" and not davet_tr and not mevcut_davet_tr:
        raise ApiHata("Gelmedi sonucu icin davetiye teblig tarih/saati gerekli.")

    try:
        db.tutanak_sonuc_guncelle(tutanak_id, yeni_sonuc, davet_iso)
    except ValueError as exc:
        raise ApiHata(str(exc))

    # Excel'i yeni sonuca gore yeniden uret
    kurum = db.get_kurum_bilgileri()
    mukellef = db.mukellef_getir(t["mukellef_id"])
    imzalayanlar = db.tutanak_imzalayanlari_getir(tutanak_id)
    kalemler_excel = []
    for k in db.tutanak_kalemlerini_getir(tutanak_id):
        kalemler_excel.append({
            "fis_no": k["fis_no"],
            "vergi_turu_kod": k["vergi_turu_kod"],
            "ceza_kodu": k["ceza_kodu"],
            "donem": k.get("donem", ""),
            "miktar": k["miktar"],
            "uzlasilan_tutar": k["uzlasilan_tutar"],
        })

    toplanti_tr = iso_to_tr(t["toplanti_tarih_saat"] or "")
    yeni_davet_tr = davet_tr or mevcut_davet_tr

    os.makedirs(TUTANAK_DIR, exist_ok=True)
    guvenli_isim = "".join(c if c.isalnum() else "_" for c in mukellef["ad_unvan"])[:40]
    guvenli_no = (t["tutanak_no"] or "").replace("/", "_")
    dosya_adi = f"{guvenli_no}_{guvenli_isim}_{yeni_sonuc}.xlsx"
    dosya_yolu = os.path.join(TUTANAK_DIR, dosya_adi)

    tutanak_olustur_excel(dosya_yolu, kurum, t["tutanak_no"], toplanti_tr, yeni_davet_tr,
                          mukellef, kalemler_excel, imzalayanlar, yeni_sonuc)

    eski_dosya = t["dosya_yolu"]
    if eski_dosya and os.path.abspath(eski_dosya) != os.path.abspath(dosya_yolu) \
            and os.path.isfile(eski_dosya):
        try:
            os.remove(eski_dosya)
        except OSError:
            pass
    db.tutanak_dosya_yolu_guncelle(tutanak_id, dosya_yolu)
    return {"tamam": True, "dosya_adi": dosya_adi}


class Istekci(BaseHTTPRequestHandler):
    server_version = "UzlasmaApp/1.0"

    # ------------------------------------------------------------------
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
        return json.loads(self.rfile.read(uzunluk).decode("utf-8"))

    def _istek_guvenli_mi(self, yazma=False):
        """Tarayicidaki baska sitelerden gelen istekleri reddeder.

        Host kontrolu DNS rebinding'i, Origin kontrolu siteler arasi
        POST'lari (CSRF) engeller. Sunucu yalnizca 127.0.0.1'i dinler;
        bu kontroller tarayici uzerinden dolayli erisime karsidir.
        """
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
            if yol == "/" or yol == "/index.html":
                self._dosya_gonder(os.path.join(WEB_DIR, "index.html"), "text/html; charset=utf-8")
            elif yol == "/api/kurum":
                self._json_yanit(db.get_kurum_bilgileri())
            elif yol == "/api/mukellef/ara":
                q = (params.get("q", [""])[0]).strip()
                self._json_yanit(db.mukellef_ara(q) if len(q) >= 3 else [])
            elif yol == "/api/mukellef":
                self._json_yanit(db.mukellef_getir(int(params["id"][0])))
            elif yol == "/api/bekleyen":
                self._json_yanit(db.bekleyen_ihbarnameler(int(params["mukellef_id"][0])))
            elif yol == "/api/ihbarnameler":
                self._json_yanit(db.tum_ihbarnameler(int(params["mukellef_id"][0])))
            elif yol == "/api/vergi_turleri":
                self._json_yanit(db.vergi_turleri_listele())
            elif yol == "/api/ceza_kodlari":
                self._json_yanit(db.ceza_kodlari_listele())
            elif yol == "/api/komisyon":
                sadece_aktif = params.get("tum", ["0"])[0] != "1"
                self._json_yanit(db.komisyon_uyeleri_listele(sadece_aktif=sadece_aktif))
            elif yol == "/api/tutanaklar":
                self._json_yanit(db.tutanak_gecmisi())
            elif yol == "/api/imza_gecmisi":
                self._json_yanit(db.komisyon_uyesi_imza_gecmisi(int(params["uye_id"][0])))
            elif yol == "/api/istatistik":
                baslangic = tr_tarih_to_iso_gun(params.get("baslangic", [""])[0]) or None
                bitis = tr_tarih_to_iso_gun(params.get("bitis", [""])[0]) or None
                self._json_yanit(db.istatistikler(baslangic, bitis))
            elif yol == "/api/yedekler":
                self._json_yanit(db.yedekleri_listele())
            elif yol == "/api/simdi":
                self._json_yanit({"simdi": simdi_tr()})
            elif yol == "/tutanak":
                self._tutanak_indir(params.get("dosya", [""])[0])
            elif yol == "/puantaj":
                self._puantaj_indir(params)
            elif yol == "/dokum":
                self._dokum_indir()
            else:
                self._hata("Bulunamadi", 404)
        except ApiHata as exc:
            self._hata(str(exc))
        except Exception as exc:  # noqa: BLE001
            self._hata(f"Sunucu hatasi: {exc}", 500)

    def do_POST(self):
        if not self._istek_guvenli_mi(yazma=True):
            return
        parsed = urllib.parse.urlparse(self.path)
        yol = parsed.path
        try:
            veri = self._govdeyi_oku()
            if yol == "/api/kurum":
                db.set_kurum_bilgileri(veri.get("defterdarlik", "").strip(),
                                        veri.get("vergi_dairesi", "").strip())
                self._json_yanit({"tamam": True})
            elif yol == "/api/dilekce/ayristir":
                self._json_yanit(dilekce_ayristir(veri.get("metin", "")))
            elif yol == "/api/dilekce/pdf":
                self._json_yanit(_pdf_dilekceleri_ayristir(veri))
            elif yol == "/api/kayit":
                self._json_yanit(_dilekce_kaydet(veri))
            elif yol == "/api/tutanak":
                self._json_yanit(_tutanak_uret(veri))
            elif yol == "/api/vergi_turleri":
                kod = (veri.get("kod") or "").strip()
                if not kod:
                    raise ApiHata("Kod bos olamaz.")
                db.vergi_turu_ekle(kod, (veri.get("ad") or "").strip())
                self._json_yanit({"tamam": True})
            elif yol == "/api/vergi_turleri/sil":
                db.vergi_turu_sil(int(veri["id"]))
                self._json_yanit({"tamam": True})
            elif yol == "/api/ceza_kodlari":
                kod = (veri.get("kod") or "").strip()
                if not kod:
                    raise ApiHata("Kod bos olamaz.")
                db.ceza_kodu_ekle(kod, (veri.get("aciklama") or "").strip())
                self._json_yanit({"tamam": True})
            elif yol == "/api/ceza_kodlari/sil":
                db.ceza_kodu_sil(int(veri["id"]))
                self._json_yanit({"tamam": True})
            elif yol == "/api/komisyon":
                ad_soyad = (veri.get("ad_soyad") or "").strip()
                if not ad_soyad:
                    raise ApiHata("Ad Soyad bos olamaz.")
                gorev = (veri.get("gorev") or "Üye").strip()
                if gorev not in ("Başkan", "Üye"):
                    raise ApiHata("Gorev 'Başkan' veya 'Üye' olmalidir.")
                db.komisyon_uyesi_ekle(ad_soyad, (veri.get("unvan") or "").strip(), gorev)
                self._json_yanit({"tamam": True})
            elif yol == "/api/komisyon/sil":
                db.komisyon_uyesi_sil(int(veri["id"]))
                self._json_yanit({"tamam": True})
            elif yol == "/api/ceza_satiri/guncelle":
                try:
                    db.ceza_satiri_guncelle(
                        int(veri["id"]), (veri.get("vergi_turu_kod") or "").strip(),
                        (veri.get("ceza_kodu") or "").strip(), _miktar_coz(veri.get("miktar")),
                    )
                except ValueError as exc:
                    raise ApiHata(str(exc))
                self._json_yanit({"tamam": True})
            elif yol == "/api/ihbarname/sil":
                try:
                    db.ihbarname_sil(int(veri["id"]))
                except ValueError as exc:
                    raise ApiHata(str(exc))
                self._json_yanit({"tamam": True})
            elif yol == "/api/tutanak/sil":
                try:
                    dosya = db.tutanak_sil(int(veri["id"]))
                except ValueError as exc:
                    raise ApiHata(str(exc))
                if dosya and os.path.isfile(dosya):
                    try:
                        os.remove(dosya)
                    except OSError:
                        pass
                self._json_yanit({"tamam": True})
            elif yol == "/api/tutanak/sonuc":
                self._json_yanit(_tutanak_sonuc_degistir(veri))
            elif yol == "/api/tutanak_sayaci":
                try:
                    db.tutanak_sayaci_ayarla(veri.get("sonraki", 0))
                except (ValueError, TypeError) as exc:
                    raise ApiHata(f"Gecersiz tutanak sayisi: {exc}")
                self._json_yanit({"tamam": True})
            elif yol == "/api/yedek_al":
                hedef = db.yedek_al()
                self._json_yanit({"dosya": os.path.basename(hedef)})
            elif yol == "/api/geri_yukle":
                # Dizin atlamaya karsi yalnizca yedek klasorundeki .db dosya adlari
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
        except FileNotFoundError as exc:
            self._hata(f"Dosya bulunamadi: {exc}")
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

    def _puantaj_indir(self, params):
        try:
            yil = int(params.get("yil", [""])[0])
            ay = int(params.get("ay", [""])[0])
            if not (1 <= ay <= 12 and 2000 <= yil <= 2100):
                raise ValueError
        except (ValueError, IndexError):
            self._hata("Gecersiz yil/ay.")
            return
        uyeler = db.puantaj_verisi(yil, ay)
        if not uyeler:
            self._hata("Kayitli aktif komisyon uyesi yok.")
            return
        os.makedirs(PUANTAJ_DIR, exist_ok=True)
        dosya_adi = f"puantaj_{yil}_{ay:02d}.xlsx"
        dosya_yolu = os.path.join(PUANTAJ_DIR, dosya_adi)
        puantaj_cetveli_olustur(dosya_yolu, db.get_kurum_bilgileri(), yil, ay, uyeler)
        with open(dosya_yolu, "rb") as f:
            govde = f.read()
        self.send_response(200)
        self.send_header("Content-Type",
                         "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
        self.send_header("Content-Disposition",
                         f'attachment; filename="{urllib.parse.quote(dosya_adi)}"')
        self.send_header("Content-Length", str(len(govde)))
        self.end_headers()
        self.wfile.write(govde)

    def _dokum_indir(self):
        from datetime import datetime

        from .ods_export import ods_olustur

        basliklar = ["VKN/TCKN", "Mükellef Adı/Ünvanı", "İhbarname Numarası", "Vergi Kodu",
                     "Ceza Kodu", "Vergi/Ceza Tutarı (TL)", "Uzlaşılan Tutar (TL)",
                     "Uzlaşma Durumu"]
        durum_adlari = {"beklemede": "Bekliyor", "uzlasildi": "Uzlaşıldı",
                        "uzlasilamadi": "Uzlaşılamadı", "gelmedi": "Gelmedi"}
        satirlar = []
        for r in db.tum_kayitlar_dokum():
            satirlar.append([
                r["vkn_tckn"] or "", r["ad_unvan"], r["fis_no"],
                r["vergi_turu_kod"] or "", r["ceza_kodu"] or "",
                round(r["miktar"] or 0, 2),
                round(r["uzlasilan_tutar"], 2) if r["uzlasilan_tutar"] is not None else "",
                durum_adlari.get(r["durum"], r["durum"]),
            ])
        govde = ods_olustur(basliklar, satirlar, sayfa_adi="Uzlasma Kayitlari")
        dosya_adi = f"uzlasma_dokum_{datetime.now().strftime('%Y%m%d_%H%M')}.ods"
        self.send_response(200)
        self.send_header("Content-Type", "application/vnd.oasis.opendocument.spreadsheet")
        self.send_header("Content-Disposition",
                         f'attachment; filename="{urllib.parse.quote(dosya_adi)}"')
        self.send_header("Content-Length", str(len(govde)))
        self.end_headers()
        self.wfile.write(govde)

    def _tutanak_indir(self, dosya_adi):
        # Yol gezinme saldirisina karsi yalnizca dosya adini kabul et
        dosya_adi = posixpath.basename(dosya_adi or "")
        if not dosya_adi.endswith(".xlsx"):
            self._hata("Gecersiz dosya", 400)
            return
        dosya_yolu = os.path.join(TUTANAK_DIR, dosya_adi)
        if not os.path.isfile(dosya_yolu):
            self._hata("Dosya bulunamadi", 404)
            return
        with open(dosya_yolu, "rb") as f:
            govde = f.read()
        self.send_response(200)
        self.send_header("Content-Type",
                         "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
        self.send_header("Content-Disposition",
                         f'attachment; filename="{urllib.parse.quote(dosya_adi)}"')
        self.send_header("Content-Length", str(len(govde)))
        self.end_headers()
        self.wfile.write(govde)


def sunucu_baslat(port=8765):
    db.init_db()
    sunucu = ThreadingHTTPServer(("127.0.0.1", port), Istekci)
    return sunucu
