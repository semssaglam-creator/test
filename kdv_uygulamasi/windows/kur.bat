@echo off
rem ===========================================================
rem  KDV Inceleme Calismasi - masaustu kisayolu olusturur
rem
rem  "Kurulum" degildir: sisteme hicbir sey yazilmaz, kayit defterine
rem  dokunulmaz, yonetici yetkisi istenmez. Yalnizca masaustune bir
rem  kisayol konur ve ilk calistirma icin gereken Python hazirlanir.
rem ===========================================================

setlocal
cd /d "%~dp0"
title KDV Inceleme Calismasi - kurulum
chcp 65001 >nul 2>&1

if exist "main.py" goto klasorTamam
echo.
echo   Bu dosya uygulama klasorunun icinde degil.
echo   ZIP'i once "Tumunu ayikla" ile bir klasore cikarin.
echo.
pause
exit /b 1
:klasorTamam

echo.
echo   KDV Inceleme Calismasi hazirlaniyor...
echo.

rem --- 1) Python'u simdiden hazirla ki ilk acilis hizli olsun
call "%~dp0_python_bul.bat"
if not defined PY (
    echo   Python hazirlanamadi. Yukaridaki aciklamaya bakin.
    pause
    exit /b 1
)
echo   Python hazir: %PY%

rem --- 2) Masaustu kisayolu
set "HEDEF=%~dp0calistir.bat"
set "IKON=%~dp0ikon.ico"
if not exist "%IKON%" set "IKON=%HEDEF%"

powershell -NoProfile -ExecutionPolicy Bypass -Command "$ErrorActionPreference='Stop'; try { $m=New-Object -ComObject WScript.Shell; $k=$m.CreateShortcut([IO.Path]::Combine($m.SpecialFolders('Desktop'),'KDV Inceleme Calismasi.lnk')); $k.TargetPath='%HEDEF%'; $k.WorkingDirectory='%~dp0'; $k.IconLocation='%IKON%'; $k.Description='KDV inceleme calismasi - beyan, hesap, tutanak ve rapor'; $k.Save(); exit 0 } catch { Write-Host ('   ' + $_.Exception.Message); exit 1 }"

if errorlevel 1 goto kisayolYok

echo   Masaustune kisayol kondu: KDV Inceleme Calismasi
echo.
echo   Kurulum tamam. Masaustundeki kisayola cift tiklayarak
echo   uygulamayi baslatabilirsiniz.
echo.
pause
exit /b 0

:kisayolYok
echo.
echo   Kisayol olusturulamadi (kurum ilkesi engelliyor olabilir).
echo   Sorun degil: uygulamayi bu klasordeki
echo     calistir.bat
echo   dosyasina cift tiklayarak acabilirsiniz. Isterseniz o dosyaya
echo   sag tiklayip "Kisayol olustur" diyerek masaustune tasiyin.
echo.
pause
exit /b 0
