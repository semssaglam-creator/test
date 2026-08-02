@echo off
rem TANI - sorun giderme raporu uretir.
rem Cift tiklayin; ekranda cikan metni ve olusan baslatma_kaydi.txt
rem dosyasini bildirin.
cd /d "%~dp0"
call "KDV Duzenleme.bat" --tani
