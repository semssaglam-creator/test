@echo off
rem ===========================================================
rem  {{UYGULAMA_ADI}} - kaldirma
rem
rem  Yalnizca masaustu kisayolunu siler. Uygulamanin kendisi bu
rem  klasorde durur; klasoru silmek uygulamayi tamamen kaldirir.
rem  Verileriniz de bu klasorde oldugu icin silmeden once yedek alin.
rem ===========================================================

setlocal
cd /d "%~dp0"
title {{UYGULAMA_ADI}} - kaldirma
chcp 65001 >nul 2>&1

echo.
powershell -NoProfile -ExecutionPolicy Bypass -Command "$m=New-Object -ComObject WScript.Shell; $p=[IO.Path]::Combine($m.SpecialFolders('Desktop'),'{{UYGULAMA_ADI}}.lnk'); if (Test-Path $p) { Remove-Item $p -Force; Write-Host '   Masaustu kisayolu silindi.' } else { Write-Host '   Masaustunde kisayol yoktu.' }"

echo.
echo   Uygulamayi tamamen kaldirmak icin su klasoru silin:
echo     %~dp0
echo.
echo   DIKKAT: kaydettiginiz veriler de bu klasorun icindedir.
echo   Silmeden once gerekiyorsa yedek alin.
echo.
pause
endlocal
