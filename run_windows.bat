@echo off
rem NikolayCo SmartZill v2.0 - Windows Boot Script
chcp 65001 > nul

if "%1"=="min" goto :start
start /min cmd /c "%~f0" min
exit /b

:start
title SmartZill v2.0
cd /d "%~dp0"

:: VLC Configuration
:: We use a specific version to ensure compatibility with python-vlc
set "VLC_VERSION=3.0.21"
set "VLC_URL=https://download.videolan.org/pub/videolan/vlc/%VLC_VERSION%/win64/vlc-%VLC_VERSION%-win64.zip"

echo ==================================================
echo   NikolayCo SmartZill v2.0 baslatiliyor...
echo ==================================================

rem Virtual environment check
if exist ".venv" goto :venv_exists
echo [*] Sanal ortam (venv) olusturuluyor...
python -m venv .venv
:venv_exists

rem Activate
call .venv\Scripts\activate.bat

rem Update Pip
echo [*] Paket araclari guncelleniyor...
python -m pip install --upgrade pip setuptools wheel -q

rem VLC Check
set "VLC_LOCAL=%~dp0bin\vlc\libvlc.dll"
if exist "%VLC_LOCAL%" (
    set "SMARTZILL_VLC_PATH=%~dp0bin\vlc"
    goto :vlc_ok
)

rem Standart paths
set "VLC_PATH=%ProgramFiles%\VideoLAN\VLC\vlc.exe"
if exist "%VLC_PATH%" goto :vlc_ok
set "VLC_PATH=%ProgramFiles(x86)%\VideoLAN\VLC\vlc.exe"
if exist "%VLC_PATH%" goto :vlc_ok

echo [!] VLC Player bulunamadi! Portatif surum indiriliyor...
if not exist "bin" mkdir "bin"
echo [*] VLC v%VLC_VERSION% indiriliyor...
powershell -Command "Invoke-WebRequest -Uri '%VLC_URL%' -OutFile 'vlc.zip'"
echo [*] Dosyalar cikariliyor...
powershell -Command "Expand-Archive -Path 'vlc.zip' -DestinationPath 'bin' -Force"
del vlc.zip

rem Find and rename extraction folder
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

rem Install dependencies
echo [*] Bagimliliklar kontrol ediliyor...
pip install -r requirements.txt
if errorlevel 1 (
    echo [!] HATA: Bagimliliklar yuklenemedi. 
    echo [!] Lutfen internet baglantinizi ve Python surumunuzu kontrol edin.
    pause
    exit /b
)

rem Start App
echo [!] Uygulama baslatiliyor...
python smartzill.py

pause
