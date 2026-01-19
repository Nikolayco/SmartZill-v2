@echo off
if "%1"=="min" goto :start
start /min cmd /c "%~f0" min
exit /b

:start
REM NikolayCo SmartZill v2.0 - Windows Boot Script

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
set "VLC_PATH=%ProgramFiles%\VideoLAN\VLC\vlc.exe"
if exist "%VLC_PATH%" goto :vlc_ok
set "VLC_PATH=%ProgramFiles(x86)%\VideoLAN\VLC\vlc.exe"
if exist "%VLC_PATH%" goto :vlc_ok

echo [!] VLC Player bulunamadi! Indiriliyor...
powershell -Command "Invoke-WebRequest -Uri 'https://download.videolan.org/pub/videolan/vlc/3.0.21/win64/vlc-3.0.21-win64.exe' -OutFile 'vlc-installer.exe'"
echo [*] VLC Player kuruluyor...
vlc-installer.exe /L=1055 /S
del vlc-installer.exe
:vlc_ok

REM Install dependencies
echo [*] Bagimliliklar kontrol ediliyor...
pip install -r requirements.txt

REM Start App
echo [!] Uygulama baslatiliyor...
python smartzill.py

pause
