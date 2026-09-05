#!/bin/bash
# =====================================================================
#  Beyanname Dokumu Al  -  macOS baslaticisi
#
#  CIFT TIKLAYIN. Bir dosya secme penceresi acilir; beyanname PDF'ini
#  secersiniz. Yaninda "dokum.txt" olusur ve kendiliginden acilir.
#
#  Terminal komutu yazmaniza gerek yok. macOS'ta .command dosyalari
#  cift tiklaninca Terminal'de calisir; .sh dosyalari calismaz - bu
#  yuzden uzanti .command.
# =====================================================================

# Cift tiklamada calisma klasoru ev dizini olur; betigin yanina gec.
KLASOR="$(cd "$(dirname "$0")" && pwd)"
cd "$KLASOR" || exit 1

echo "Beyanname Dokumu Al"
echo "-------------------"
echo

# --- Python 3 var mi -------------------------------------------------
if ! command -v python3 >/dev/null 2>&1; then
    echo "Python 3 bulunamadi."
    echo
    echo "macOS'ta Python 3, Xcode Komut Satiri Araclari ile gelir."
    echo "Kurmak icin Terminal'de:"
    echo
    echo "    xcode-select --install"
    echo
    echo "Kurulum bitince bu dosyaya yeniden cift tiklayin."
    echo
    read -r -p "Kapatmak icin Enter'a basin..."
    exit 1
fi

# --- PDF'i sistemin kendi penceresinden sec --------------------------
# osascript macOS'un yerlesik betik aracidir; Finder'in dosya secme
# penceresini acar. Boylece dosya yolu yazmak gerekmez.
PDF=$(osascript -e 'try
    POSIX path of (choose file with prompt "Beyanname PDF dosyasini secin:" of type {"pdf", "com.adobe.pdf"})
on error
    return ""
end try' 2>/dev/null)

if [ -z "$PDF" ]; then
    echo "Dosya secilmedi, vazgecildi."
    echo
    read -r -p "Kapatmak icin Enter'a basin..."
    exit 0
fi

echo "Secilen dosya: $PDF"
CIKTI="$KLASOR/dokum.txt"
HATA="$KLASOR/dokum_hata.txt"
EK_GIZLE=""

# Dokumu uret, sonra "kisisel bilgi kaldi mi" diye sor. Kaldiysa kullanici
# metni girer ve dokum yeniden uretilir; liste temizlenene kadar surer.
while true; do
    echo "Okunuyor..."
    if [ -n "$EK_GIZLE" ]; then
        # Virgulle ayrilan her parca ayri bir --ek-gizle olarak gecirilir
        ESKI_IFS="$IFS"; IFS=','
        # shellcheck disable=SC2086
        set --
        for parca in $EK_GIZLE; do
            kirp="$(echo "$parca" | sed 's/^ *//; s/ *$//')"
            [ -n "$kirp" ] && set -- "$@" --ek-gizle "$kirp"
        done
        IFS="$ESKI_IFS"
        python3 "beyanname_maskele.py" "$PDF" "$@" > "$CIKTI" 2>"$HATA"
        SONUC=$?
    else
        python3 "beyanname_maskele.py" "$PDF" > "$CIKTI" 2>"$HATA"
        SONUC=$?
    fi

    if [ "$SONUC" -ne 0 ]; then
        echo
        echo "Dokum uretilemedi. Hata:"
        echo
        cat "$HATA"
        echo
        read -r -p "Kapatmak icin Enter'a basin..."
        exit 1
    fi
    rm -f "$HATA"

    SATIR=$(wc -l < "$CIKTI" | tr -d ' ')
    echo "Bitti: $SATIR satir  ->  $CIKTI"
    open "$CIKTI" 2>/dev/null

    # Dokumun basindaki "GOZDEN GECIRIN" listesinde kisisel bilgi kaldi mi
    CEVAP=$(osascript -e 'try
        set y to display dialog "Dökümün başındaki listede isim, ünvan gibi kişisel bir bilgi kaldıysa buraya yazın (virgülle ayırın).

Temizse boş bırakıp Bitti deyin." default answer "" buttons {"Bitti", "Yeniden üret"} default button "Bitti" with title "Gözden geçirme"
        if button returned of y is "Yeniden üret" then
            return text returned of y
        else
            return "__BITTI__"
        end if
    on error
        return "__BITTI__"
    end try' 2>/dev/null)

    if [ "$CEVAP" = "__BITTI__" ] || [ -z "$CEVAP" ]; then
        break
    fi
    EK_GIZLE="$EK_GIZLE,$CEVAP"
done

echo
echo "Hazir. dokum.txt dosyasinin TAMAMINI kopyalayip sohbete yapistirin."
echo
read -r -p "Kapatmak icin Enter'a basin..." || true
exit 0
