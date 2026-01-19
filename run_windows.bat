@echo off
setlocal EnableDelayedExpansion

REM NikolayCo SmartZill v2.0 - Windows Boot Script
chcp 65001 > nul

if "%1"=="min" goto :start
start /min cmd /c "%~f0" min
exit /b

:start
title SmartZill v2.0

cd /d "%~dp0"

echo ==================================================
echo   NikolayCo SmartZill v2.0 baslatiliyor...
echo ==================================================

REM Virtual environment check
if exist ".venv" goto :venv_exists
echo [*] Sanal ortam (venv) olusturuluyor...
python -m venv .venv
:venv_exists

REM Activate
call .venv\Scripts\activate.bat

REM Update Pip
echo [*] Paket aracları guncelleniyor...
python -m pip install --upgrade pip setuptools wheel -q

REM VLC Check
set "VLC_LOCAL=%~dp0bin\vlc\libvlc.dll"
if exist "%VLC_LOCAL%" (
    set "SMARTZILL_VLC_PATH=%~dp0bin\vlc"
    goto :vlc_ok
)

REM Standart yollari kontrol et (oncelik portatifte)
set "VLC_PATH=%ProgramFiles%\VideoLAN\VLC\vlc.exe"
if exist "%VLC_PATH%" goto :vlc_ok
set "VLC_PATH=%ProgramFiles(x86)%\VideoLAN\VLC\vlc.exe"
if exist "%VLC_PATH%" goto :vlc_ok

echo [!] VLC Player bulunamadi! Portatif surum indiriliyor (Admin gerekmez)...
if not exist "bin" mkdir "bin"
powershell -Command "Invoke-WebRequest -Uri 'https://download.videolan.org/pub/videolan/vlc/3.0.21/win64/vlc-3.0.21-win64.zip' -OutFile 'vlc.zip'"
echo [*] Dosyalar cikariliyor...
powershell -Command "Expand-Archive -Path 'vlc.zip' -DestinationPath 'bin' -Force"
del vlc.zip

REM Klasor ismini bul ve duzelt (vlc-3.0.21 gibi degisken olabilir)
for /d %%i in (bin\vlc-*) do (
    if exist "bin\vlc" rd /s /q "bin\vlc"
    move "%%i" "bin\vlc"
)

if exist "bin\vlc\libvlc.dll" (
    set "SMARTZILL_VLC_PATH=%~dp0bin\vlc"
    echo [OK] Portatif VLC hazir.
) else (
    echo [!] HATA: VLC dosyalari cikarilamadi.
)

:vlc_ok

REM Install dependencies
echo [*] Bagimliliklar kontrol ediliyor...
pip install -r requirements.txt
if errorlevel 1 (
    echo [!] HATA: Bagimliliklar yuklenemedi. 
    echo [!] Lutfen internet baglantinizi ve Python surumunuzu kontrol edin.
    pause
    exit /b
)

REM Start App
echo [!] Uygulama baslatiliyor...
python smartzill.py

pause
