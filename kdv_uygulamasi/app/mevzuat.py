"""Raporda atif yapilan kanun maddelerinin metinleri.

Metinler belgeye oldugu gibi alintilanir. Uygulama madde secmez; hangi
maddelerin rapora girecegini `sahte_belge_raporu` tespitin turune gore
belirler, kullanici da kunyeden re'sen takdir nedenini secer.
"""

MADDELER = {
    "vuk_3b": (
        "213 sayılı VUK md. 3/B — İspat",
        "Vergilendirmede vergiyi doğuran olay ve bu olaya ilişkin muamelelerin "
        "gerçek mahiyeti esastır. Vergiyi doğuran olay ve bu olaya ilişkin "
        "muamelelerin gerçek mahiyeti yemin hariç her türlü delille "
        "ispatlanabilir."),
    "vuk_30": (
        "213 sayılı VUK md. 30 — Re'sen Vergi Tarhı",
        "Re'sen vergi tarhı, vergi matrahının tamamen veya kısmen defter, kayıt "
        "ve belgelere veya kanuni ölçülere dayanılarak tespitine imkân "
        "bulunmayan hallerde takdir komisyonları tarafından takdir edilen veya "
        "vergi incelemesi yapmaya yetkili olanlarca düzenlenen vergi inceleme "
        "raporlarında belirtilen matrah veya matrah kısmı üzerinden vergi tarh "
        "olunmasıdır."),
    "vuk_30_4": (
        "213 sayılı VUK md. 30/4",
        "Defter kayıtları ve bunlarla ilgili vesikalar, vergi matrahının doğru "
        "ve kesin olarak tespitine imkân vermeyecek derecede noksan, usulsüz ve "
        "karışık olması dolayısıyla ihticaca salih bulunmaz ise re'sen takdir "
        "sebebi sayılır."),
    "vuk_30_6": (
        "213 sayılı VUK md. 30/6",
        "Tutulması zorunlu olan defterlerin veya verilen beyannamelerin gerçek "
        "durumu yansıtmadığına dair delil bulunursa re'sen takdir sebebi "
        "sayılır."),
    "vuk_30_7": (
        "213 sayılı VUK md. 30/7",
        "Diğer hallerde de vergi kanunlarına göre belirlenen matrah veya "
        "matrahın bir kısmının tespiti mümkün değilse bu kısım re'sen takdir "
        "sebebidir."),
    "vuk_112": (
        "213 sayılı VUK md. 112 — Gecikme Faizi",
        "İkmalen, re'sen veya idarece yapılan tarhiyatlarda; dava konusu "
        "yapılmaksızın kesinleşen vergilere, kendi vergi kanunlarında belirtilen "
        "ve tarhiyatın ilgili bulunduğu döneme ilişkin normal vade tarihinden "
        "itibaren, son yapılan tarhiyatın tahakkuk tarihine kadar geçen süre "
        "için 6183 sayılı Kanuna göre tespit edilen gecikme zammı oranında "
        "gecikme faizi uygulanır."),
    "vuk_134": (
        "213 sayılı VUK md. 134 — Vergi İncelemesinin Amacı",
        "Vergi incelemesinden maksat, ödenmesi gereken vergilerin doğruluğunu "
        "araştırmak, tespit etmek ve sağlamaktır."),
    "vuk_141": (
        "213 sayılı VUK md. 141 — İnceleme Tutanakları",
        "İnceleme esnasında lüzum görülen hallerde, vergilendirme ile ilgili "
        "olaylar ve hesap durumları ayrıca tutanaklar ile tespit ve tevsik "
        "olunabilir. İlgililerin itiraz ve mülahazaları varsa bunlar da "
        "tutanağa geçirilir."),
    "vuk_341": (
        "213 sayılı VUK md. 341 — Vergi Ziyaı",
        "Vergi ziyaı, mükellefin veya sorumlunun vergilendirme ile ilgili "
        "ödevlerini zamanında yerine getirmemesi veya eksik yerine getirmesi "
        "yüzünden verginin zamanında tahakkuk ettirilmemesini veya eksik "
        "tahakkuk ettirilmesini ifade eder."),
    "vuk_344": (
        "213 sayılı VUK md. 344 — Vergi Ziyaı Cezası",
        "341 inci maddede yazılı hallerde vergi ziyaına sebebiyet verildiği "
        "takdirde, mükellef veya vergi sorumlusu hakkında ziyaa uğratılan "
        "verginin bir katı tutarında vergi ziyaı cezası kesilir. Vergi ziyaına "
        "359 uncu maddede yazılı fiillerle sebebiyet verilmesi halinde bu ceza "
        "üç kat olarak uygulanır."),
    "vuk_359": (
        "213 sayılı VUK md. 359 — Kaçakçılık Suçları ve Cezaları",
        "Vergi kanunları uyarınca tutulan veya düzenlenen ve saklama ve ibraz "
        "mecburiyeti bulunan defter, kayıt ve belgeleri yok edenler veya defter "
        "sahifelerini yok ederek yerine başka yapraklar koyanlar veya hiç yaprak "
        "koymayanlar veya belgelerin asıl veya suretlerini tamamen veya kısmen "
        "sahte olarak düzenleyenler veya bu belgeleri kullananlar hakkında "
        "hapis cezası hükmolunur. Gerçek bir muamele veya durum olmadığı halde "
        "bunlar varmış gibi düzenlenen belge, sahte belgedir."),
    "kdv_29": (
        "3065 sayılı KDV Kanunu md. 29 — Vergi İndirimi",
        "Mükellefler, yaptıkları vergiye tabi işlemler üzerinden hesaplanan "
        "katma değer vergisinden, bu Kanunda aksine hüküm olmadıkça, "
        "faaliyetlerine ilişkin olarak kendilerine yapılan teslim ve hizmetler "
        "dolayısıyla hesaplayarak düzenledikleri fatura ve benzeri vesikalarda "
        "gösterilen katma değer vergisini indirebilirler."),
    "kdv_34": (
        "3065 sayılı KDV Kanunu md. 34 — İndirimin Belgelendirilmesi",
        "Yurt içinden sağlanan veya ithal olunan mal ve hizmetlere ait Katma "
        "Değer Vergisi, alış faturası veya benzeri vesikalar ve gümrük makbuzu "
        "üzerinden ayrıca gösterilmek ve bu vesikalar kanuni defterlere "
        "kaydedilmek şartıyla indirilebilir."),
    "kdv_teblig": (
        "KDV Genel Uygulama Tebliği (IV/E) — Sahte Belge",
        "Gerçek bir işleme dayanmayan, mal ya da hizmet teslimi olmaksızın "
        "düzenlenen belgeler (sahte belgeler) nedeniyle yüklenilen katma değer "
        "vergisinin indirim konusu yapılması mümkün değildir."),
}

MADDELER.update({
    "vuk_227": (
        "213 sayılı VUK md. 227 — Tevsik Zorunluluğu",
        "Bu kanunda aksine hüküm olmadıkça bu kanuna göre tutulan ve üçüncü "
        "şahıslarla olan münasebet ve muamelelere ait olan kayıtların tevsiki "
        "mecburidir."),
    "vuk_mk355": (
        "213 sayılı VUK mükerrer md. 355 — Bilgi Vermekten Çekinenler ile "
        "Tevsik Zorunluluğuna Uymayanlara Uygulanacak Ceza",
        "Tahsilat ve ödemelerini banka, benzeri finans kurumları veya posta "
        "idarelerince düzenlenen belgelerle tevsik etme zorunluluğuna uymayan "
        "mükelleflerden her birine, her bir işlem için bu maddeye göre "
        "uygulanan cezalardan az olmamak üzere işleme konu tutarın %5'i "
        "nispetinde özel usulsüzlük cezası kesilir. Bu şekilde ceza kesilen "
        "mükellefler hakkında bir takvim yılı içinde kesilecek toplam ceza "
        "ilgili yıl için belirlenen üst sınırı aşamaz."),
    "vuk_mk257": (
        "213 sayılı VUK mükerrer md. 257 — Yetki",
        "Maliye Bakanlığı, mükelleflere muameleleri ile ilgili tahsilat ve "
        "ödemelerini banka, benzeri finans kurumları veya posta idarelerince "
        "düzenlenen belgelerle tevsik etmeleri zorunluluğunu getirmeye ve bu "
        "zorunluluğun kapsamını ve uygulamaya ilişkin usul ve esaslarını "
        "belirlemeye yetkilidir."),
    "vuk_336": (
        "213 sayılı VUK md. 336 — Cezalarda Birleşme",
        "Cezayı istilzam eden tek bir fiil ile vergi ziyaı ve usulsüzlük "
        "birlikte işlenmiş olursa bunlara ait cezalardan sadece miktar "
        "itibariyle en ağırı kesilir."),
    "vuk_352": (
        "213 sayılı VUK md. 352 — Usulsüzlük Dereceleri ve Cezaları",
        "Usulsüzlükler, aşağıda yazılı derecelere ve bu kanuna bağlı cetvele "
        "göre cezalandırılır. Usulsüzlük fiili re'sen takdiri gerektirirse, "
        "bağlı cetvelde yazılı cezalar iki kat olarak kesilir."),
    "vuk_ek11": (
        "213 sayılı VUK Ek md. 11 — Tarhiyat Öncesi Uzlaşma",
        "Maliye Bakanlığı, vergi incelemesine dayanılarak tarh edilecek "
        "vergilerle bunlara ilişkin kesilecek vergi ziyaı cezalarında tarhiyat "
        "öncesi uzlaşma yapılmasına izin verebilir. Şu kadar ki, 359 uncu "
        "maddede yazılı fiillerle vergi ziyaına sebebiyet verilmesi halinde "
        "tarh edilecek vergi ve kesilecek ceza ile bu fiillere iştirak "
        "edenlere kesilecek ceza tarhiyat öncesi uzlaşma kapsamı dışındadır."),
    "vuk_teblig_306": (
        "306 Sıra No'lu VUK Genel Tebliği — Bilerek Kullanma Ölçütü",
        "Sahte veya muhteviyatı itibariyle yanıltıcı belgenin gerek "
        "düzenlenmesinin gerekse kullanılmasının kaçakçılık suçunun oluşması "
        "yönünden ayrı ayrı değerlendirilmesi gerekir. Kaçakçılık suçunun "
        "oluşması, sahte veya muhteviyatı itibariyle yanıltıcı belgenin "
        "bilerek kullanılıp kullanılmadığının, diğer bir anlatımla bu "
        "kullanımda kastın bulunup bulunmadığının değerlendirilmesine ve "
        "belirlenmesine bağlıdır. Bu belgeleri bilmeden kullandığı sonucuna "
        "varılan mükellefler adına vergi suçu raporu düzenlenmemesi ve "
        "haklarında cumhuriyet savcılıklarına suç duyurusunda bulunulmaması "
        "gerekir."),
    "danistay_indirim": (
        "Danıştay Kararları — Sahte Belgeye Dayalı KDV İndirimi",
        "Danıştay Vergi Dava Daireleri Genel Kurulu ile Danıştay 3., 4., 7., 9. "
        "ve 11. Daire kararlarında; yalnızca şekil şartları yerine getirilerek "
        "düzenlenen, gerçek bir mal teslimi veya hizmet ifasına dayanmayan "
        "faturalarda gösterilen katma değer vergisinin indirim konusu "
        "yapılamayacağı, indirim müessesesinin işleyebilmesi için verginin "
        "gerçekten yüklenilmiş olması gerektiği kabul edilmiştir."),
    "kdv_indirim_sartlari": (
        "KDV İndiriminin Üç Şartı (KDVK md. 29, 34 ve VUK md. 3)",
        "Bir mal teslimi veya hizmet ifasına ilişkin katma değer vergisinin "
        "indirim konusu yapılabilmesi için; gerçek bir mal tesliminin veya "
        "hizmet ifasının bulunması, indirim konusu yapılacak katma değer "
        "vergisinin fatura ve benzeri vesikalarda ayrıca gösterilmesi ve bu "
        "vesikaların yasal defterlere kaydedilmesi şarttır. İndirim "
        "mekanizmasının sağlıklı işlemesi bu üç şartın bir arada "
        "gerçekleşmesine bağlıdır."),
})

# Re'sen takdir nedeni koduna gore madde anahtari
RESEN_MADDELERI = {"30/4": "vuk_30_4", "30/6": "vuk_30_6", "30/7": "vuk_30_7"}

# Sahte belge kullanma raporunda her durumda yer alan maddeler
SAHTE_BELGE_MADDELERI = ["vuk_3b", "vuk_30", "kdv_29", "kdv_34", "kdv_teblig",
                         "vuk_341", "vuk_344"]


def madde(anahtar):
    """(baslik, metin) ciftini dondurur; bilinmeyen anahtarda None."""
    return MADDELER.get(anahtar)


def maddeler(anahtarlar):
    """Verilen sirada, var olan maddeleri dondurur."""
    return [MADDELER[a] for a in anahtarlar if a in MADDELER]
