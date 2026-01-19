@echo off
chcp 65001 > nul
if not "%minimized%"=="" goto :minimized
set minimized=true
start /min cmd /C "%~dpnx0"
goto :EOF
:minimized
REM NikolayCo SmartZill v2.0 - Windows Başlatma Scripti
title NikolayCo SmartZill v2.0

cd /d "%~dp0"

echo ==================================================
echo   🔔 NikolayCo SmartZill v2.0 başlatılıyor...
echo ==================================================

REM Virtual environment kontrol
if not exist ".venv" (
    echo 📦 Virtual environment oluşturuluyor...
    python -m venv .venv
)

REM Aktive et
call .venv\Scripts\activate.bat

REM Pip ve araçları güncelle
echo 🆙 Bağımlılık araçları güncelleniyor...
python -m pip install --upgrade pip setuptools wheel -q

REM VLC Kontrolü (Gerekli)
if not exist "%ProgramFiles%\VideoLAN\VLC\vlc.exe" (
    if not exist "%ProgramFiles(x86)%\VideoLAN\VLC\vlc.exe" (
        echo ⚠️ VLC Player bulunamadı! Otomatik indiriliyor...
        echo ⏳ Lütfen bekleyin, bu işlem internet hızına göre zaman alabilir...
        
        powershell -Command "Invoke-WebRequest -Uri 'https://download.videolan.org/pub/videolan/vlc/3.0.21/win64/vlc-3.0.21-win64.exe' -OutFile 'vlc-installer.exe'"
        
        echo 📦 VLC Player kuruluyor...
        vlc-installer.exe /L=1055 /S
        
        echo ✅ Kurulum tamamlandı. Temizleniyor...
        del vlc-installer.exe
    )
)

REM Bağımlılıkları kontrol et
echo 📦 Bağımlılıklar kontrol ediliyor...
pip install -r requirements.txt


REM Uygulamayı başlat
echo 🚀 Uygulama başlatılıyor...
python smartzill.py

pause
