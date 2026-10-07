#!/usr/bin/env bash
# Takip PDF -> Excel kurulum: sanal ortam + uygulama menüsü kısayolu
set -e
DIR="$(cd "$(dirname "$0")" && pwd)"
APP="$HOME/.local/share/takip2excel"

if ! python3 -c "import tkinter" 2>/dev/null; then
  echo "tkinter eksik. Kurun:  Debian/Ubuntu/Pardus: sudo apt install python3-tk python3-venv"
  echo "                       Fedora: sudo dnf install python3-tkinter | openSUSE: sudo zypper in python3-tk"
  exit 1
fi

mkdir -p "$APP"
cp "$DIR/takip2excel.py" "$DIR/requirements.txt" "$APP/"
python3 -m venv "$APP/venv"
"$APP/venv/bin/pip" install -q --upgrade pip
"$APP/venv/bin/pip" install -q -r "$APP/requirements.txt"

mkdir -p "$HOME/.local/bin" "$HOME/.local/share/applications"
cat > "$HOME/.local/bin/takip2excel" <<SH
#!/usr/bin/env bash
exec "$APP/venv/bin/python" "$APP/takip2excel.py" "\$@"
SH
chmod +x "$HOME/.local/bin/takip2excel"

cat > "$HOME/.local/share/applications/takip2excel.desktop" <<DT
[Desktop Entry]
Type=Application
Name=Takip PDF → Excel
Comment=Takip listesi PDF'ini sütunlara ayırıp Excel'e aktarır
Exec=$HOME/.local/bin/takip2excel
Icon=x-office-spreadsheet
Terminal=false
Categories=Office;
DT
echo "Kuruldu. Uygulama menüsünde 'Takip PDF → Excel' olarak bulabilirsiniz."
echo "Komut satırı: takip2excel dosya.pdf  (çıktı: dosya.xlsx)"
