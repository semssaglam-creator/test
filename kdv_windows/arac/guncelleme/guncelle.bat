@echo off
rem ===========================================================
rem  KDV Inceleme Calismasi - GUNCELLEME
rem
rem  Kurulu uygulamanin yalnizca PROGRAM dosyalarini yeniler
rem  (main.py, app\, web\). Veritabani, ciktilar ve yedekler
rem  ELLENMEZ; yenilenen dosyalar once yedeklenir.
rem
rem  Kurulu uygulamayi kendisi arar. Bulamazsa klasoru bu
rem  pencereye surukleyip birakmanizi ister.
rem ===========================================================

setlocal
cd /d "%~dp0"
title KDV Inceleme Calismasi - Guncelleme
chcp 65001 >nul 2>&1

rem Ne olup bittigi bir dosyaya da yazilir: bir sey ters giderse
rem kullanici ekrani aktarmak yerine tek dosyayi gonderir.
rem Yazma HER ZAMAN hatasi yutularak yapilir: salt okunur bir
rem klasorde bile guncelleme bundan dolayi durmamali.
set "KAYIT=%~dp0GUNCELLEME KAYDI.txt"
>"%KAYIT%" echo KDV Inceleme Calismasi - guncelleme kaydi 2>nul
>>"%KAYIT%" echo Tarih  : %DATE% %TIME% 2>nul
>>"%KAYIT%" echo Klasor : %~dp0 2>nul
>>"%KAYIT%" echo. 2>nul

echo.
echo   KDV INCELEME CALISMASI - GUNCELLEME
echo   ===================================
echo.
echo   Bu islem kurulu uygulamanin program dosyalarini yeniler.
echo   Calismalariniz, veritabaniniz ve ciktilariniz ELLENMEZ.
echo.

rem --- 0) Yeni dosyalar bu betigin yaninda mi?
rem Zip'in ICINDEN cift tiklanirsa Windows yalnizca bu dosyayi gecici bir
rem klasore cikarir; yeni\ klasoru yanina gelmez.
if exist "%~dp0yeni\main.py" goto kaynakTamam
echo   HATA: "yeni" klasoru bulunamadi.
echo.
echo   Buyuk olasilikla ZIP dosyasinin ICINDEN cift tiklandi.
echo   COZUM: Zip dosyasina sag tiklayin ^> "Tumunu ayikla" deyin,
echo   sonra CIKAN KLASORDEKI bu dosyaya cift tiklayin.
echo.
>>"%KAYIT%" echo HATA: yeni\ klasoru yok - zip icinden calistirilmis. 2>nul
pause
exit /b 1
:kaynakTamam

rem --- 1) Kurulu uygulamayi bul
rem Sirasiyla: uzerine birakilan klasor, bu betigin bulundugu ve bir ust
rem klasor, yanindaki uygulama klasoru, sonra alisilmis konumlar.
rem Turkce Windows'ta da klasorlerin DISKTEKI adi Ingilizcedir
rem (Desktop / Downloads / Documents); goruntulenen ad yerellestirilmistir.
set "HEDEF="
call :dene "%~1"
call :dene "%~dp0."
call :dene "%~dp0.."
call :dene "%~dp0..\KDV Inceleme Calismasi"
call :dene "%USERPROFILE%\Desktop\KDV Inceleme Calismasi"
call :dene "%USERPROFILE%\Downloads\KDV Inceleme Calismasi"
call :dene "%USERPROFILE%\Documents\KDV Inceleme Calismasi"
call :dene "%USERPROFILE%\KDV Inceleme Calismasi"
call :dene "%OneDrive%\Desktop\KDV Inceleme Calismasi"
call :dene "%OneDrive%\Documents\KDV Inceleme Calismasi"
call :dene "%OneDrive%\Belgeler\KDV Inceleme Calismasi"
if defined HEDEF goto hedefTamam

echo   Kurulu uygulama klasoru kendiliginden bulunamadi.
echo.
echo   Uygulama klasorunu bu pencereye SURUKLEYIP birakin, sonra
echo   Enter tusuna basin. Klasorun adi genellikle soyledir:
echo     KDV Inceleme Calismasi
echo.
set "ELLE="
set /p "ELLE=Klasor: "
if not defined ELLE goto hedefYok
rem Surukle-birak yolu tirnak icinde yapistirir; tirnaklar atilir.
set "ELLE=%ELLE:"=%"
call :dene "%ELLE%"
if defined HEDEF goto hedefTamam

:hedefYok
echo.
echo   HATA: Verilen yerde uygulama bulunamadi.
echo   Klasorun icinde main.py ve calistir.bat dosyalari olmali.
echo.
>>"%KAYIT%" echo HATA: uygulama klasoru bulunamadi. 2>nul
pause
exit /b 1

:hedefTamam
>>"%KAYIT%" echo Hedef  : %HEDEF% 2>nul
echo   Guncellenecek klasor:
echo     %HEDEF%
echo.
echo   UYGULAMA ACIKSA SIMDI KAPATIN. Acik kalirsa dosyalar
echo   yenilenir ama uygulama eski surumu calistirmaya devam eder.
echo.
pause

rem --- 2) Once yedek. Yedek alinamiyorsa guncelleme YAPILMAZ:
rem geri donusu olmayan bir degisiklik, kacirilan bir guncellemeden
rem daha kotudur. Iki kusak tutulur.
echo.
echo   [1/3] Su anki surum yedekleniyor...
set "YEDEK=%HEDEF%\yedekler\guncelleme_oncesi"
if exist "%YEDEK%_eski" rd /s /q "%YEDEK%_eski" 2>nul
if exist "%YEDEK%" move /y "%YEDEK%" "%YEDEK%_eski" >nul 2>&1
mkdir "%HEDEF%\yedekler" 2>nul
mkdir "%YEDEK%" 2>nul
if not exist "%YEDEK%" goto yedekOlmadi
set "YHATA=0"
xcopy "%HEDEF%\app" "%YEDEK%\app\" /E /I /Y /Q >nul 2>&1 || set "YHATA=1"
xcopy "%HEDEF%\web" "%YEDEK%\web\" /E /I /Y /Q >nul 2>&1 || set "YHATA=1"
copy /y "%HEDEF%\main.py" "%YEDEK%\main.py" >nul 2>&1 || set "YHATA=1"
if "%YHATA%"=="1" goto yedekOlmadi
>>"%KAYIT%" echo [1] Yedek alindi: %YEDEK% 2>nul
echo         Yedek: %YEDEK%

rem --- 3) Yeni dosyalari koy
echo   [2/3] Yeni dosyalar kopyalaniyor...
set "HATA=0"
xcopy "%~dp0yeni\app" "%HEDEF%\app\" /E /I /Y /Q >nul 2>&1 || set "HATA=1"
xcopy "%~dp0yeni\web" "%HEDEF%\web\" /E /I /Y /Q >nul 2>&1 || set "HATA=1"
copy /y "%~dp0yeni\main.py" "%HEDEF%\main.py" >nul 2>&1 || set "HATA=1"
if "%HATA%"=="1" goto kopyaOlmadi

rem --- 4) Gercekten yenilendi mi
rem Yalnizca yeni surumde bulunan bir isaret aranir. Kopyalama "basarili"
rem donup dosyanin eski kalmasi (kilitli dosya, yarim kopya) boylece
rem sessizce gecmez.
echo   [3/3] Denetleniyor...
findstr /m /c:"YENI_BICIM_SIFIRLAR" "%HEDEF%\app\pdf_beyanname.py" >nul 2>&1
if errorlevel 1 goto denetimOlmadi

>>"%KAYIT%" echo [2] Kopyalandi ve denetlendi. Guncelleme TAMAM. 2>nul
echo.
echo   GUNCELLEME TAMAM.
echo.
echo   Uygulamayi her zamanki gibi acabilirsiniz:
echo     %HEDEF%\calistir.bat
echo.
pause
endlocal
exit /b 0

:yedekOlmadi
>>"%KAYIT%" echo HATA: yedek alinamadi. Hicbir dosya degistirilmedi. 2>nul
echo.
echo   HATA: Yedek alinamadi. Guvenlik icin HICBIR dosya degistirilmedi.
echo.
echo   Sebebi genellikle yazma izni olmayan bir klasordur.
echo   Uygulama klasorunu Masaustune tasiyip yeniden deneyin.
echo.
echo   Bu dosyayi gonderin: GUNCELLEME KAYDI.txt
echo.
pause
exit /b 1

:kopyaOlmadi
>>"%KAYIT%" echo HATA: kopyalama basarisiz. Yedek: %YEDEK% 2>nul
echo.
echo   HATA: Dosyalar kopyalanamadi.
echo.
echo   Uygulama acik olabilir. Kapatip yeniden deneyin.
echo   Eski surum su klasorde duruyor:
echo     %YEDEK%
echo.
echo   Bu dosyayi gonderin: GUNCELLEME KAYDI.txt
echo.
pause
exit /b 1

:denetimOlmadi
>>"%KAYIT%" echo HATA: kopya sonrasi denetim tutmadi. Yedek: %YEDEK% 2>nul
echo.
echo   HATA: Dosyalar kopyalandi ama yeni surum taninmadi.
echo.
echo   Uygulama acik olabilir ve dosyalari kilitliyor olabilir.
echo   Kapatip yeniden deneyin. Eski surum su klasorde duruyor:
echo     %YEDEK%
echo.
echo   Bu dosyayi gonderin: GUNCELLEME KAYDI.txt
echo.
pause
exit /b 1

rem --- Aday klasor gecerli mi: icinde main.py ve calistir.bat olmali.
rem Ilk gecerli aday secilir; sonrakiler bakilmadan gecilir.
:dene
if defined HEDEF goto :eof
if "%~1"=="" goto :eof
if not exist "%~1\main.py" goto :eof
if not exist "%~1\calistir.bat" goto :eof
set "HEDEF=%~f1"
goto :eof
