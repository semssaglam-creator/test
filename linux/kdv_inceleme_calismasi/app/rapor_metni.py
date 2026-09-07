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


# Beyannamenin sonuc hesaplari; farklarin hangisini nasil etkiledigi raporlanir
SONUC_HESAPLARI = [
    ("odenecek", "Ödenmesi gereken KDV"),
    ("sonraki_devir", "Sonraki döneme devreden KDV"),
    ("iade", "İade edilmesi gereken KDV"),
    ("tecil_edilecek", "Tecil edilecek KDV"),
]
SONUC_ALANLARI = [alan for alan, _ad in SONUC_HESAPLARI]


class _BolumSayaci:
    """Kosullu bolumler nedeniyle basliklari sirali numaralandirir."""

    def __init__(self):
        self.sira = 0

    def basla(self, baslik):
        self.sira += 1
        return f"{self.sira}. {baslik}"


def _degisiklik_ozeti(d):
    """Bu donemde neyin degistigini (matrah, indirim vb.) cumleye cevirir."""
    f = d["fark"]
    parcalar = []
    if abs(f["matrah"]) > 0.005:
        parcalar.append(f"matraha {_tl(abs(f['matrah']))} TL "
                        f"{'ilave edilmiş' if f['matrah'] > 0 else 'eksiltme yapılmış'}")
    if abs(f["toplam_kdv"]) > 0.005:
        parcalar.append(f"hesaplanan KDV {_tl(abs(f['toplam_kdv']))} TL "
                        f"{'artmış' if f['toplam_kdv'] > 0 else 'azalmış'}")
    if abs(f["bu_donem_indirim_toplam"]) > 0.005:
        parcalar.append(f"indirilecek KDV {_tl(abs(f['bu_donem_indirim_toplam']))} TL "
                        f"{'azaltılmış' if f['bu_donem_indirim_toplam'] < 0 else 'artırılmış'}")
    if abs(f["onceki_devir"]) > 0.005:
        parcalar.append(f"önceki dönemden devreden KDV {_tl(abs(f['onceki_devir']))} TL "
                        f"{'artmış' if f['onceki_devir'] > 0 else 'azalmış'}")
    return parcalar


def _donem_paragrafi(d):
    """Bir donemin degisikligini ve sonuc hesaplarina etkisini yazar."""
    satirlar = []
    parcalar = _degisiklik_ozeti(d)
    if parcalar:
        satirlar.append(f"{_donem_adi(d)} dönemi: " + ", ".join(parcalar) + ".")
    else:
        satirlar.append(f"{_donem_adi(d)} dönemi:")

    # Sonuc hesaplarindan hangileri, ne kadar degisti
    etkilenen = [(alan, ad) for alan, ad in SONUC_HESAPLARI
                 if abs(d["fark"].get(alan, 0)) > 0.005]
    if etkilenen:
        satirlar.append("    Bu değişikliğin beyannamenin sonuç hesaplarına etkisi:")
        for alan, ad in etkilenen:
            once = d["beyan"][alan]
            sonra = d["elestirili"][alan]
            sapma = d["fark"][alan]
            satirlar.append(
                f"      - {ad}: {_tl(once)} TL iken {_tl(sonra)} TL olarak "
                f"hesaplanmış; {_tl(abs(sapma))} TL "
                f"{'artmıştır' if sapma > 0 else 'azalmıştır'}.")
    else:
        satirlar.append("    Bu değişiklik dönemin sonuç hesaplarını değiştirmemiş, "
                        "yalnızca indirim ve devir tutarlarına yansımıştır.")

    # Farkin kaynagi: bu donemin tespiti / devir / beyan hatasi
    satirlar.extend(_kaynak_cumlesi(d, etkilenen))
    satirlar.append("")
    return satirlar


def _kaynak_cumlesi(d, etkilenen):
    """Odenecek KDV farkinin bilesenlerini acikca yazar."""
    if not etkilenen:
        return []
    ana = "odenecek" if any(a == "odenecek" for a, _ in etkilenen) else etkilenen[0][0]
    tespit = d["fark_tespit"].get(ana, 0)
    devir = d["fark_devir"].get(ana, 0)
    hata = d["fark_beyan_hatasi"].get(ana, 0)
    ad = dict(SONUC_HESAPLARI)[ana]
    bilesenler = [
        (tespit, "bu dönemde yapılan tespitten"),
        (devir, "önceki dönemlerden devir yoluyla"),
        (hata, "beyannamenin kendi aritmetik tutarsızlığından"),
    ]
    dolu = [(tutar, kaynak) for tutar, kaynak in bilesenler if abs(tutar) > 0.005]
    if not dolu:
        return []
    if len(dolu) == 1:
        return [f"    {ad} farkının tamamı {dolu[0][1]} kaynaklanmaktadır."]
    # Birden cok bilesen varsa yon de yazilir; aksi halde tutarlar toplanmiyormus
    # gibi gorunur (ornegin -144.000 ile +180.000 net +36.000 eder).
    parcalar = [f"{_tl(abs(tutar))} TL'lik {'artış' if tutar > 0 else 'azalış'} {kaynak}"
                for tutar, kaynak in dolu]
    return [f"    {ad} farkında " + ", ".join(parcalar) + " kaynaklanmaktadır; "
            f"net etki {_tl(abs(d['fark'][ana]))} TL "
            f"{'artıştır' if d['fark'][ana] > 0 else 'azalıştır'}."]


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

    bolum = _BolumSayaci()
    satirlar.append(bolum.basla("DÖNEMLER İTİBARIYLA TESPİT EDİLEN FARKLAR"))
    satirlar.append("")

    # Kendi tespiti olan donemler ayrintili yazilir; yalnizca devir yoluyla
    # etkilenenler asagida toplu listelenir (uzun serilerde tekrari onler)
    tespitli = [d for d in farkli if d["elestiri_var"]
                or any(abs(d["fark_beyan_hatasi"].get(a, 0)) > 0.005 for a in SONUC_ALANLARI)]
    devirli = [d for d in farkli if d not in tespitli]

    for d in tespitli:
        satirlar.extend(_donem_paragrafi(d))

    if devirli:
        satirlar.append("Yukarıdaki tespitlerin devir zinciriyle yansıdığı diğer dönemler "
                        "ve bu dönemlerin sonuç hesaplarındaki değişim:")
        satirlar.append("")
        for d in devirli:
            etkiler = []
            for alan, hesap_adi in SONUC_HESAPLARI:
                sapma = d["fark"].get(alan, 0)
                if abs(sapma) <= 0.005:
                    continue
                etkiler.append(f"{hesap_adi} {_tl(d['beyan'][alan])} TL'den "
                               f"{_tl(d['elestirili'][alan])} TL'ye "
                               f"{'yükselmiş' if sapma > 0 else 'düşmüş'}")
            if etkiler:
                satirlar.append(f"    - {_donem_adi(d)}: " + "; ".join(etkiler) + ".")
        satirlar.append("")

    genel = sonuc["genel_toplam"]
    hatali = [d for d in donemler
              if any(abs(d["fark_beyan_hatasi"].get(a, 0)) > 0.005 for a in SONUC_ALANLARI)]
    if hatali:
        satirlar.append(bolum.basla(
            "BEYANNAMEDEKİ ARİTMETİK HATALARIN SONUÇ HESAPLARINA ETKİSİ"))
        satirlar.append("")
        satirlar.append(
            "Aşağıdaki dönemlerde beyannamenin kendi rakamları içinde tutarsızlık "
            "bulunmaktadır. Bu tutarsızlıklar, inceleme tespitlerinden bağımsız olarak "
            "sonuç hesaplarını etkilemektedir:")
        satirlar.append("")
        for d in hatali:
            satirlar.append(f"{_donem_adi(d)} dönemi:")
            for alan, hesap_adi in SONUC_HESAPLARI:
                sapma = d["fark_beyan_hatasi"].get(alan, 0)
                if abs(sapma) <= 0.005:
                    continue
                satirlar.append(
                    f"    - {hesap_adi}: beyanda {_tl(d['beyan'][alan])} TL gösterilmiş; "
                    f"beyandaki diğer rakamlara göre {_tl(d['beyan_hesap'][alan])} TL "
                    f"olması gerekirdi ({_tl(abs(sapma))} TL "
                    f"{'fazla' if sapma < 0 else 'eksik'} gösterilmiş).")
            satirlar.append("")

    satirlar.append(bolum.basla("TOPLAM SONUÇ"))
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
        satirlar.append(bolum.basla("TARHİYAT ÖZETİ"))
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
        satirlar.append(bolum.basla("TESPİTLERİN AYRI AYRI ETKİSİ"))
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
        satirlar.append(bolum.basla("BEYANNAMELERDE TESPİT EDİLEN TUTARSIZLIKLAR"))
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
