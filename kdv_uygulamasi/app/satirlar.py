"""KDV beyannamesi satir tanimlari.

Excel calismasindaki 45-96 arasi satir duzeni burada kod olarak tutulur.
`BEYAN_SATIRLARI` sirasi, kullanicinin sistemden yapistirdigi blogun satir
sirasiyla birebir aynidir; yapistirma ayristirmasi bu siraya dayanir.

Alanlar:
    kod     : veritabaninda ve hesaplamalarda kullanilan kalici anahtar
    etiket  : ekranda ve Excel ciktisinda gorunen metin
    baslik  : True ise veri tasimayan grup basligidir (bos satir)
"""

BEYAN_SATIRLARI = [
    ("matrah_toplami", "MATRAH TOPLAMI", False),
    ("hesaplanan_kdv", "HESAPLANAN KDV", False),
    ("ilave_edilecek_kdv", "İLAVE EDİLECEK KDV", False),
    ("toplam_kdv", "TOPLAM KDV", False),
    ("g_indirimler", "İNDİRİMLER", True),
    ("onceki_donemden_indirilecek", "ÖNCEKİ DÖNEMDEN İNDİRİLECEK KDV", False),
    ("satistan_iade_kdv",
     "SATIŞTAN İADE EDİLEN, İŞLEMİ GERÇEKLEŞMEYEN VEYA İŞLEMİNDEN VAZGEÇİLEN "
     "MAL VE HİZMETLER NEDENİYLE İNDİRİLMESİ GEREKEN KDV", False),
    ("ikamet_etmeyenlere_iade", "TÜRKİYE'DE İKAMET ETMEYENLERE BU DÖNEMDE İADE EDİLEN KDV", False),
    ("indirimli_oran_mahsuben",
     "İNDİRİMLİ ORANA TABİ İŞLEMLERLE İLGİLİ YILI İÇERİSİNDE MAHSUBEN İADESİ "
     "GERÇEKLEŞMEYEN", False),
    ("gecici_17_indirim",
     "KANUNUN (11/1-c) VE GEÇİCİ 17. MADDELERİNDEN DOĞAN İADELERİN İNDİRİM YOLUYLA", False),
    ("yurtici_alim_kdv", "YURTİÇİ ALIMLARA İLİŞKİN KDV", False),
    ("sorumlu_sifatiyla_kdv", "SORUMLU SIFATIYLA BEYAN EDİLEREK ÖDENEN KDV", False),
    ("ithalde_odenen_kdv", "İTHALDE ÖDENEN KDV", False),
    ("degersiz_alacak_kdv",
     "DEĞERSİZ HALE GELEN ALACAKLARA İLİŞKİN İNDİRİLECEK KDV SATIRLARI EKLENMELİDİR", False),
    ("onceki_donem_devreden", "ÖNCEKİ DÖN. DEVR. İND. KDV", False),
    ("bu_donem_indirilecek",
     "BU DÖN. AİT İND. KDV (2019/Ocak ve öncesi için 102; 2019/Şubat ve sonrası için "
     "108+109+110)", False),
    ("diger_indirimler_toplami", "103+104+105 TOP.", False),
    ("indirimler_toplami", "İNDİRİMLER TOPLAMI", False),
    ("g_ihrac_kayitli", "İHRAÇ KAYDIYLA TESLİMLER", True),
    ("ihrac_teslim_bedeli", "TOPLAM TESLİM BEDELİ", False),
    ("ihrac_hesaplanan_kdv", "TOP. HESAPLANAN KDV", False),
    ("ihrac_yuklenilen_kdv", "TOP. YUKLENİLEN KDV", False),
    ("tecil_edilebilir_kdv", "TECİL EDİLEBİLİR KDV", False),
    ("ihracat_tecil_edilemeyen",
     "İHRACATIN GERÇ. DÖN. İADE EDİLECEK TECİL EDİLEMEYEN KDV", False),
    ("indirimli_oran_yuklenim_farki",
     "İND. OR. TABİ MAL. İHR. KAYD. TES. İHR. GERÇ. DÖN. İADE EDİLECEK YÜK. KDV FARKI", False),
    ("g_kismi_istisna", "KISMİ İSTİSNA KAP. GİREN İŞLEMLER", True),
    ("kismi_istisna_teslim", "TOP. TESLİM VE HİZ. TUTARI", False),
    ("kismi_istisna_yuklenilen", "TOP. YÜKLENİLEN KDV", False),
    ("g_tam_istisna", "TAM İSTİSNA KAP. GİREN İŞLEMLER", True),
    ("tam_istisna_teslim", "TOP. TESLİM VE HİZ. TUTARI", False),
    ("tam_istisna_yuklenilen", "TOP. YÜKLENİLEN KDV", False),
    ("istisna_toplam_teslim",
     "İSTİSNA KAPSAM. GİREN İŞLEMLERE AİT TOP. TESLİM VE HİZ. TUTARI", False),
    ("g_kismi_tevkifat", "KISMİ TEVKİFAT KAPSAMINA GİREN İŞLEMLER", True),
    ("tevkifat_teslim", "TOP. TESLİM VE HİZ. TUTARI", False),
    ("tevkifat_iade_kdv", "TOP. İADEYE KONU OLAN KDV", False),
    ("g_diger_iade", "DİĞER İADE HAKKI DOĞURAN İŞLEMLER", True),
    ("kdv_odenmeksizin_temin", "YURTİÇİ VE YURTDIŞI KDV ÖDENMEKSİZİN TEMİN EDİLEN MAL BEDELİ",
     False),
    ("ihracat_doneminde_iade", "İHRACATIN GERÇEKLEŞTİĞİ DÖNEMDE İADE EDİLECEK KDV", False),
    ("diger_iade_teslim", "TOP. TESLİM VE HİZ. TUTARI", False),
    ("diger_iade_kdv", "TOP. İADEYE KONU OLAN KDV", False),
    ("iade_edilebilir_kdv", "İADE EDİLEBİLİR KDV", False),
    ("g_sonuc", "SONUÇ HESAPLARI", True),
    ("tecil_edilecek_kdv", "TECİL EDİLECEK KDV", False),
    ("odenmesi_gereken_kdv", "ÖDENMESİ GEREKEN KDV", False),
    ("iade_edilmesi_gereken_kdv", "İADE EDİLMESİ GEREKEN KDV", False),
    ("sonraki_donem_devreden", "SONRAKİ DÖN. DEVREDEN KDV", False),
    ("g_diger_bilgiler", "DİĞER BİLGİLER", True),
    ("ozel_matrah_bedel", "ÖZEL MATRAH ŞEKLİNE TABİ İŞL. MATR. DAHİL OLM. BEDEL", False),
    ("teslim_bedel_aylik", "TESLİM VE HİZ. KARŞ. TEŞKİL EDEN BEDEL (AYLIK)", False),
    ("teslim_bedel_kumulatif", "TESLİM VE HİZ. KARŞ. TEŞKİL EDEN BEDEL (KÜMÜLATİF)", False),
    ("kredi_karti_tahsilat", "KREDİ KARTI İLE TAHS. EDİL. TES. HİZ. KDV DAHİL BEDELİ", False),
]

# Yalnizca veri tasiyan satirlarin kodlari (grup basliklari haric)
VERI_KODLARI = [kod for kod, _etiket, baslik in BEYAN_SATIRLARI if not baslik]
ETIKETLER = {kod: etiket for kod, etiket, _b in BEYAN_SATIRLARI}

AYLAR = ["Ocak", "Şubat", "Mart", "Nisan", "Mayıs", "Haziran",
         "Temmuz", "Ağustos", "Eylül", "Ekim", "Kasım", "Aralık"]
AYLAR_BUYUK = [a.upper() for a in AYLAR]

# Elestiri (inceleme tespiti) alanlari: Excel'deki 23-27 satirlarinin karsiligi
ELESTIRI_ALANLARI = [
    ("matrah_ilave", "KDV MATRAHINA İLAVE"),
    ("hesaplanan_kdv_ilave", "HESAPLANAN KDV İLAVE"),
    ("devir_cikar", "ÖNCEKİ DÖNEM DEVREDEN KDV'DEN ÇIKARILACAK"),
    ("indirim_cikar", "İNDİRİLECEK KDV'DEN ÇIKARILACAK"),
    ("yuklenilen_cikar", "YÜKLENİLEN KDV'DEN ÇIKARILACAK"),
]

# Ozet tablo kolonlari (Excel'deki 30-43 / 100-113 / 134-146 bloklari)
OZET_KOLONLARI = [
    ("matrah", "KDV Matrahı"),
    ("toplam_kdv", "Toplam KDV"),
    ("onceki_devir", "Önc. Dön. Dev. KDV"),
    ("bu_donem_indirim_toplam", "Bu Dön. İndl. KDV"),
    ("indirimler", "İndirimler Toplamı"),
    ("odenecek", "Ödenecek KDV"),
    ("sonraki_devir", "Son. Dön. Dev. KDV"),
    ("iade", "İade Edil. KDV"),
]


# Ozet tablosunun beyan satirlarina geri yazilmasi.
#
# Sonuc ve Fark sekmesindeki (ve Excel ciktisindaki) ozet tablo rapora
# yapistiriliyor; dava sonucunda mahkeme bu tablodaki tutarlari degistirebiliyor.
# Degismis tablo uygulamaya geri yapistirildiginda asagidaki eslemeye gore beyan
# satirlarina yazilir.
#
#   ozet_kod : ozet tablosundaki kolon
#   hedefler : bu degerin yazilacagi beyan satirlari
#   sifirlar : ayni buyuklugun parcasi olan ve artik bilinmeyen satirlar
#              (ornegin yalnizca Toplam KDV verildiginde ilave edilecek KDV)
# Ozet tablo sutun basliklarinin beyan satirlarina karsiligi. Anahtarlar
# normalize edilmis (buyuk harf, noktalama ve bosluk atilmis) bicimdedir; ayni
# buyukluk icin kullanilan farkli yazimlar birlikte tanimlanir.
OZET_BASLIK_ESLEMESI = {
    "MATRAHTOPLAMI": "matrah_toplami",
    "KDVMATRAHI": "matrah_toplami",
    "HESAPLANANKDV": "hesaplanan_kdv",
    "HSPLKDV": "hesaplanan_kdv",
    "ILAVEEDILECEKKDV": "ilave_edilecek_kdv",
    "TOPLAMKDV": "toplam_kdv",
    "ONCEKIDONDEVRINDKDV": "onceki_donem_devreden",
    "ONCEKIDONEMDEVREDENINDKDV": "onceki_donem_devreden",
    "ONCEKIDONEMDENINDIRILECEKKDV": "onceki_donem_devreden",
    "ONCDONDEVKDV": "onceki_donem_devreden",
    "BUDONAITINDKDV": "bu_donem_indirilecek",
    "BUDONEMEAITINDIRILECEKKDV": "bu_donem_indirilecek",
    "BUDONINDLKDV": "bu_donem_indirilecek",
    "103104105TOP": "diger_indirimler_toplami",
    "INDIRIMLERTOPLAMI": "indirimler_toplami",
    "ODENMESIGEREKENKDV": "odenmesi_gereken_kdv",
    "ODENECEKKDV": "odenmesi_gereken_kdv",
    "SONRAKIDONDEVREDENKDV": "sonraki_donem_devreden",
    "SONRAKIDONEMEDEVREDENKDV": "sonraki_donem_devreden",
    "SONDONDEVKDV": "sonraki_donem_devreden",
    "IADEEDILMESIGEREKENKDV": "iade_edilmesi_gereken_kdv",
    "IADEEDILKDV": "iade_edilmesi_gereken_kdv",
    "TECILEDILECEKKDV": "tecil_edilecek_kdv",
}

# Basliklar rapordan rapora degistigi icin tam eslesme yeterli olmaz. Asagidaki
# kurallar sirayla denenir: baslikta gecmesi gereken parcalar (hepsi) ve
# gecmemesi gereken parcalar (hicbiri). Sira onemlidir; ozel olan once gelir.
OZET_BASLIK_KURALLARI = [
    (["ILAVE"], [], "ilave_edilecek_kdv"),
    (["MATRAH"], [], "matrah_toplami"),
    (["HESAPLANAN"], ["TOPLAM"], "hesaplanan_kdv"),
    (["TOPLAMKDV"], [], "toplam_kdv"),
    (["ONCEKI"], [], "onceki_donem_devreden"),
    (["SONRAKI"], [], "sonraki_donem_devreden"),
    (["DEVREDEN"], ["ONCEKI", "SONRAKI"], "sonraki_donem_devreden"),
    (["103"], [], "diger_indirimler_toplami"),
    (["INDIRIMLER", "TOPLAM"], [], "indirimler_toplami"),
    (["IND"], ["TOPLAM", "ONCEKI", "SONRAKI"], "bu_donem_indirilecek"),
    (["ODEN"], [], "odenmesi_gereken_kdv"),
    (["TECIL"], [], "tecil_edilecek_kdv"),
    (["IADE"], [], "iade_edilmesi_gereken_kdv"),
]

# Elle eslestirme ekraninda sunulan hedefler
OZET_HEDEF_SECENEKLERI = [
    ("matrah_toplami", "Matrah Toplamı"),
    ("hesaplanan_kdv", "Hesaplanan KDV"),
    ("ilave_edilecek_kdv", "İlave Edilecek KDV"),
    ("toplam_kdv", "Toplam KDV"),
    ("onceki_donem_devreden", "Önceki Dönemden Devreden KDV"),
    ("bu_donem_indirilecek", "Bu Döneme Ait İndirilecek KDV"),
    ("diger_indirimler_toplami", "103+104+105 Toplamı"),
    ("indirimler_toplami", "İndirimler Toplamı"),
    ("odenmesi_gereken_kdv", "Ödenmesi Gereken KDV"),
    ("iade_edilmesi_gereken_kdv", "İade Edilmesi Gereken KDV"),
    ("tecil_edilecek_kdv", "Tecil Edilecek KDV"),
    ("sonraki_donem_devreden", "Sonraki Döneme Devreden KDV"),
]

# Tarhiyat ozeti tablosunun kolon duzeni (elde kullanilan tablonun karsiligi).
# grup : ust baslik, kod : hesap.py'deki alan adi, vurgu : renk sinifi
TARHIYAT_KOLONLARI = [
    ("Ödenecek KDV", "odenecek_olmasi_gereken", "Olması Gereken", ""),
    ("Ödenecek KDV", "odenecek_beyan", "Beyan Edilen", ""),
    ("1", "resen_tarhi_gereken", "Re'sen Tarhı Gereken KDV", "vurgu1"),
    ("İade Edil. KDV", "iade_olmasi_gereken", "Olması Gereken", ""),
    ("İade Edil. KDV", "iade_beyan", "Beyan Edilen", ""),
    ("2", "aranmasi_gereken", "Aranması Ger. KDV", "vurgu1"),
    ("1+2", "resen_toplam", "Re'sen Tarhı Ger. Toplam", "vurgu2"),
    ("İhr. Gerç. Dön. İade Edil. KDV", "ihracat_iade_olmasi_gereken", "Olması Gereken", ""),
    ("İhr. Gerç. Dön. İade Edil. KDV", "ihracat_iade_beyan", "Beyan Edilen", ""),
    ("3", "haksiz_iade", "Haksız Olarak İade Edilen KDV", "vurgu1"),
    ("1+2+3", "toplam_fark", "Toplam Fark", "vurgu2"),
]

# Fark ayristirmasinda gosterilen bilesenler
AYRISTIRMA_BLOKLARI = [
    ("fark_tespit", "Tespitlerimin Etkisi",
     "Bu dönemde girdiğiniz matrah ilavesi / indirim reddi gibi tespitlerin "
     "doğrudan sonucu"),
    ("fark_devir", "Devirden Gelen Etki",
     "Önceki dönemlerdeki tespitlerin devir zinciriyle bu döneme taşınan etkisi"),
    ("fark_beyan_hatasi", "Beyan Aritmetik Farkı",
     "Beyannamenin kendi rakamları içinde tutmayan kısım; tespitten bağımsızdır"),
    ("fark", "Toplam Fark", "Üç bileşenin toplamı: eleştirili − beyan edilen"),
]


def varsayilan_kdv_orani(yil, ay):
    """Genel KDV oranini donemine gore verir.

    3065 sayili Kanuna iliskin Bakanlar Kurulu/Cumhurbaskani kararlari uyarinca
    genel oran 10.07.2023 tarihine kadar %18, bu tarihten itibaren %20'dir.
    Temmuz 2023 ay icinde degistigi icin o donemde %20 varsayilir; farkli
    oranli teslimlerde deger ekranda elle duzeltilebilir.
    """
    if yil > 2023:
        return 20.0
    if yil < 2023:
        return 18.0
    return 20.0 if ay >= 7 else 18.0
