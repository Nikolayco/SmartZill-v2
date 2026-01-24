#!/bin/bash

# Renkler
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${BLUE}==========================================${NC}"
echo -e "${BLUE} SmartZill Linux Kısayol Oluşturucu${NC}"
echo -e "${BLUE}==========================================${NC}"

# Mevcut dizini al
CURRENT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
ICON_PATH="$CURRENT_DIR/ikon/smartzill_icon.png"
EXEC_CMD="python3 $CURRENT_DIR/smartzill.py"

# İkon kontrolü
if [ ! -f "$ICON_PATH" ]; then
    echo -e "${RED}[HATA] İkon dosyası bulunamadı: $ICON_PATH${NC}"
    echo "Lütfen önce ikon/smartzill_icon.png dosyasının varlığından emin olun."
    exit 1
fi

# .desktop içeriği
cat > smartzill.desktop << EOL
[Desktop Entry]
Version=1.0
Type=Application
Name=SmartZill v2.0
Comment=SmartZill Okul Zil Sistemi
Exec=$EXEC_CMD
Icon=$ICON_PATH
Path=$CURRENT_DIR
Terminal=true
StartupNotify=true
Categories=Utility;Application;
EOL

# 1. Masaüstüne kopyala
DESKTOP_DIR="$HOME/Masaüstü"
if [ ! -d "$DESKTOP_DIR" ]; then
    DESKTOP_DIR="$HOME/Desktop"
fi

if [ -d "$DESKTOP_DIR" ]; then
    cp smartzill.desktop "$DESKTOP_DIR/smartzill.desktop"
    chmod +x "$DESKTOP_DIR/smartzill.desktop"
    echo -e "${GREEN}[BAŞARILI] Masaüstü kısayolu oluşturuldu: $DESKTOP_DIR/smartzill.desktop${NC}"
else
    echo -e "${RED}[UYARI] Masaüstü klasörü bulunamadı, sadece uygulama menüsüne ekleniyor.${NC}"
fi

# 2. Uygulama menüsüne ekle
APP_DIR="$HOME/.local/share/applications"
mkdir -p "$APP_DIR"
mv smartzill.desktop "$APP_DIR/smartzill.desktop"
chmod +x "$APP_DIR/smartzill.desktop"

echo -e "${GREEN}[BAŞARILI] Uygulama menüsüne eklendi: $APP_DIR/smartzill.desktop${NC}"
echo -e "${BLUE}Artık sistem menüsünde 'SmartZill' aratarak veya masaüstünden başlatabilirsiniz.${NC}"
echo ""
read -p "Çıkmak için Enter'a basın..."
