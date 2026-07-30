"""Vergi inceleme raporuna aktarilabilecek ozet metni uretir.

Uretilen metin bir taslaktir; hukuki nitelendirme, ceza uygulamasi ve
gerekcelendirme inceleme elemani tarafindan yazilir. Buradaki metin yalnizca
donem donem sayisal sonucu duzenli bicimde ifade eder.
"""
from .satirlar import AYLAR


def _tl(deger):
    return f"{deger:,.2f}".replace(",", "#").replace(".", ",").replace("#", ".")


def _donem_adi(d):
    return f"{d['yil']}/{d['ay_adi']}"


def matrah_farki_ozeti(inceleme, sonuc, bulgular=None):
    """Rapora yapistirilabilir duz metin uretir."""
    donemler = sonuc["donemler"]
    farkli = [d for d in donemler if abs(d["fark"]["matrah"]) > 0.005
              or abs(d["fark"]["odenecek"]) > 0.005
              or abs(d["fark"]["sonraki_devir"]) > 0.005]

    satirlar = []
    ad = inceleme.get("ad_unvan") or "Mükellef"
    vkn = inceleme.get("vkn_tckn") or ""
    kapsam = _kapsam_metni(donemler)

    satirlar.append("KATMA DEĞER VERGİSİ YÖNÜNDEN YAPILAN TESPİTLER")
    satirlar.append("")
    kimlik = f"{ad}" + (f" (VKN/TCKN: {vkn})" if vkn else "")
    satirlar.append(
        f"{kimlik} hakkında {kapsam} dönemlerine ilişkin katma değer vergisi "
        f"beyannameleri üzerinde yapılan inceleme sonucunda aşağıdaki hususlar tespit edilmiştir."
    )
    satirlar.append("")

    if not farkli:
        satirlar.append("İnceleme dönemlerinde beyan edilen tutarlarda değişiklik "
                        "gerektiren bir tespit bulunmamıştır.")
        return "\n".join(satirlar)

    satirlar.append("1. DÖNEMLER İTİBARIYLA TESPİT EDİLEN FARKLAR")
    satirlar.append("")
    for d in farkli:
        parcalar = []
        f = d["fark"]
        if abs(f["matrah"]) > 0.005:
            parcalar.append(f"matraha {_tl(abs(f['matrah']))} TL "
                            f"{'ilave edilmiş' if f['matrah'] > 0 else 'eksiltme yapılmış'}")
        if abs(f["toplam_kdv"]) > 0.005:
            parcalar.append(f"hesaplanan KDV {_tl(abs(f['toplam_kdv']))} TL "
                            f"{'artmış' if f['toplam_kdv'] > 0 else 'azalmış'}")
        if abs(f["bu_donem_indirim_toplam"]) > 0.005:
            parcalar.append(
                f"indirilecek KDV {_tl(abs(f['bu_donem_indirim_toplam']))} TL "
                f"{'azaltılmış' if f['bu_donem_indirim_toplam'] < 0 else 'artırılmış'}")
        satirlar.append(f"{_donem_adi(d)} dönemi: " + ", ".join(parcalar) + ".")
        if abs(f["odenecek"]) > 0.005:
            satirlar.append(
                f"    Bu dönemde beyan edilen ödenmesi gereken KDV "
                f"{_tl(d['beyan']['odenecek'])} TL iken, yeniden hesaplama sonucunda "
                f"{_tl(d['elestirili']['odenecek'])} TL'ye ulaşılmış; "
                f"{_tl(abs(f['odenecek']))} TL tutarında vergi farkı doğmuştur.")
        if abs(f["sonraki_devir"]) > 0.005:
            satirlar.append(
                f"    Sonraki döneme devreden KDV {_tl(d['beyan']['sonraki_devir'])} TL'den "
                f"{_tl(d['elestirili']['sonraki_devir'])} TL'ye "
                f"{'yükselmiştir' if f['sonraki_devir'] > 0 else 'düşmüştür'}; "
                f"bu tutar izleyen dönem hesaplarına yansıtılmıştır.")
        satirlar.append("")

    genel = sonuc["genel_toplam"]
    satirlar.append("2. TOPLAM SONUÇ")
    satirlar.append("")
    satirlar.append(
        f"İnceleme dönemleri toplamında beyan edilen matrah {_tl(genel['beyan']['matrah'])} TL, "
        f"inceleme sonucu bulunan matrah {_tl(genel['elestirili']['matrah'])} TL olup, "
        f"{_tl(abs(genel['fark']['matrah']))} TL tutarında matrah farkı tespit edilmiştir.")
    satirlar.append(
        f"Beyan edilen ödenmesi gereken KDV toplamı {_tl(genel['beyan']['odenecek'])} TL, "
        f"inceleme sonucu bulunan tutar {_tl(genel['elestirili']['odenecek'])} TL olup, "
        f"tarhı önerilen katma değer vergisi farkı {_tl(abs(genel['fark']['odenecek']))} TL'dir.")
    son = donemler[-1]
    satirlar.append(
        f"İnceleme döneminin son ayı olan {_donem_adi(son)} itibarıyla sonraki döneme devreden "
        f"KDV, beyana göre {_tl(son['beyan']['sonraki_devir'])} TL iken inceleme sonucunda "
        f"{_tl(son['elestirili']['sonraki_devir'])} TL olarak hesaplanmıştır.")

    tarhiyat = sonuc.get("tarhiyat_toplami") or {}
    if any(tarhiyat.get(k, 0) for k in ("resen_tarhi_gereken", "aranmasi_gereken",
                                        "haksiz_iade")):
        satirlar.append("")
        satirlar.append("3. TARHİYAT ÖZETİ")
        satirlar.append("")
        if tarhiyat.get("resen_tarhi_gereken"):
            satirlar.append(f"Re'sen tarhı gereken katma değer vergisi: "
                            f"{_tl(tarhiyat['resen_tarhi_gereken'])} TL")
        if tarhiyat.get("aranmasi_gereken"):
            satirlar.append(f"Haksız iade talebi nedeniyle aranması gereken katma değer "
                            f"vergisi: {_tl(tarhiyat['aranmasi_gereken'])} TL")
        if tarhiyat.get("haksiz_iade"):
            satirlar.append(f"İadesi gerçekleşmiş olması hâlinde haksız olarak iade edilen "
                            f"katma değer vergisi: {_tl(tarhiyat['haksiz_iade'])} TL")
        satirlar.append(f"Toplam fark: {_tl(tarhiyat.get('toplam_fark', 0))} TL")
        if tarhiyat.get("fazla_beyan_odenecek"):
            satirlar.append(f"(Mükellefin fazladan beyan ettiği {_tl(tarhiyat['fazla_beyan_odenecek'])} "
                            f"TL tutarındaki ödenecek KDV tarhiyata dahil edilmemiştir.)")

    analiz = sonuc.get("kaynak_analizi") or {}
    kaynaklar = analiz.get("kaynaklar") or []
    if len(kaynaklar) > 1:
        satirlar.append("")
        satirlar.append("4. TESPİTLERİN AYRI AYRI ETKİSİ")
        satirlar.append("")
        satirlar.append("Her tespit, girildiği dönemin yanı sıra devir zinciri yoluyla izleyen "
                        "dönemleri de etkilemektedir. Tespitlerin ayrı ayrı katkıları aşağıdadır:")
        satirlar.append("")
        for k in kaynaklar:
            parcalar = []
            if k["matrah_ilave"]:
                parcalar.append(f"matraha {_tl(k['matrah_ilave'])} TL ilave")
            if k["indirim_cikar"]:
                parcalar.append(f"indirilecek KDV'den {_tl(k['indirim_cikar'])} TL red")
            if k["devir_cikar"]:
                parcalar.append(f"devreden KDV'den {_tl(k['devir_cikar'])} TL çıkarma")
            if k["yuklenilen_cikar"]:
                parcalar.append(f"yüklenilen KDV'den {_tl(k['yuklenilen_cikar'])} TL red")
            satirlar.append(
                f"- {k['etiket']} dönemi ({', '.join(parcalar)}): "
                f"{k['etkilenen_donem_sayisi']} dönemi etkilemekte olup, ödenmesi gereken "
                f"KDV üzerindeki toplam etkisi {_tl(k['toplam_odenecek_etkisi'])} TL'dir.")
        if analiz.get("etkilesim_var"):
            satirlar.append("")
            satirlar.append("Not: Katma değer vergisi hesabı, ödenecek vergi ile devreden vergi "
                            "arasındaki eşikte alt ve üst sınır içerdiğinden doğrusal değildir. "
                            "Bu nedenle tespitlerin tek tek etkilerinin toplamı, tümü birlikte "
                            "uygulandığındaki farka eşit olmayabilir; aradaki bakiye çalışma "
                            "tablosunda ayrıca gösterilmiştir.")

    if bulgular:
        satirlar.append("")
        satirlar.append("5. BEYANNAMELERDE TESPİT EDİLEN TUTARSIZLIKLAR")
        satirlar.append("")
        for b in bulgular:
            satirlar.append(f"- {b['mesaj']}")

    satirlar.append("")
    satirlar.append("Not: Bu metin, çalışma tablosundaki sayısal sonuçlardan otomatik "
                    "üretilmiş taslaktır. Hukuki nitelendirme, ceza uygulaması ve "
                    "gerekçelendirme rapora inceleme elemanınca eklenmelidir.")
    return "\n".join(satirlar)


def _kapsam_metni(donemler):
    if not donemler:
        return "-"
    ilk, son = donemler[0], donemler[-1]
    if ilk["yil"] == son["yil"]:
        return f"{ilk['yil']}/{ilk['ay_adi']} - {son['ay_adi']}"
    return f"{ilk['yil']}/{ilk['ay_adi']} - {son['yil']}/{son['ay_adi']}"


__all__ = ["matrah_farki_ozeti", "AYLAR"]
