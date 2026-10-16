@echo off
rem Builds dist\CS108FirmwareUpgrade\: the standalone one-click exe plus the FW folders.
rem Needs 32-bit Python 3.14 (the bundled SLABHIDDevice.dll is 32-bit): py install 3.14-32
setlocal
cd /d "%~dp0"
set PY=py -V:3.14-32

%PY% -m pip install --upgrade pyinstaller || goto :error
%PY% -m PyInstaller --noconfirm --clean --onefile --windowed --name CS108FirmwareUpgrade ^
    --distpath build\exe --workpath build\work --specpath build ^
    --add-binary "%CD%\USBDriver\SLABHIDDevice.dll;USBDriver" ^
    OneClickUpgrade.py || goto :error

set OUT=dist\CS108FirmwareUpgrade
if exist "%OUT%" rmdir /s /q "%OUT%"
mkdir "%OUT%" || goto :error
copy /y build\exe\CS108FirmwareUpgrade.exe "%OUT%\" >nul || goto :error
xcopy /e /i /y /q FW "%OUT%\FW" >nul || goto :error

echo.
echo Built %OUT% - copy this whole folder to the target PC and double-click CS108FirmwareUpgrade.exe
exit /b 0

:error
echo.
echo Build failed.
exit /b 1
