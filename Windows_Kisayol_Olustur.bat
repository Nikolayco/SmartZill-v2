@echo off
chcp 65001 > nul
setlocal

echo ==========================================
echo  SmartZill Masaustu Kisayolu Olusturucu
echo ==========================================

:: Yollari ayarla
set "CURRENT_DIR=%~dp0"
:: Sondaki ters slashi kaldir (varsa)
if "%CURRENT_DIR:~-1%"=="\" set "CURRENT_DIR=%CURRENT_DIR:~0,-1%"

set "VBS_FILE=%TEMP%\CreateSmartZillShortcut.vbs"
set "TARGET_BAT=%CURRENT_DIR%\run_windows.bat"
set "ICON_FILE=%CURRENT_DIR%\ikon\smartzill.ico"
set "SHORTCUT_NAME=SmartZill v2.0"

:: Ikon kontrolu
if not exist "%ICON_FILE%" (
    echo [HATA] Ikon dosyasi bulunamadi: %ICON_FILE%
    echo Lutfen once ikon klasorunun varligindan emin olun.
    pause
    exit /b
)

:: VBScript olustur
echo Set oWS = WScript.CreateObject("WScript.Shell") > "%VBS_FILE%"
echo sLinkFile = oWS.SpecialFolders("Desktop") ^& "\%SHORTCUT_NAME%.lnk" >> "%VBS_FILE%"
echo Set oLink = oWS.CreateShortcut(sLinkFile) >> "%VBS_FILE%"
echo oLink.TargetPath = "%TARGET_BAT%" >> "%VBS_FILE%"
echo oLink.WorkingDirectory = "%CURRENT_DIR%" >> "%VBS_FILE%"
echo oLink.IconLocation = "%ICON_FILE%" >> "%VBS_FILE%"
echo oLink.Description = "SmartZill Okul Zil Sistemi" >> "%VBS_FILE%"
echo oLink.Save >> "%VBS_FILE%"

:: VBScripti calistir
echo Kisayol olusturuluyor...
cscript //nologo "%VBS_FILE%"

:: Temizlik
if exist "%VBS_FILE%" del "%VBS_FILE%"

echo.
echo [BASARILI] SmartZill ikonu ile kisayol masaustune eklendi!
echo.
pause
