@echo off
chcp 65001 > nul
cd /d "%~dp0"

echo === Ошибка: файл VFS не найден
python src\emulator.py --vfs vfs\nofile.xml

for %%f in (vfs\invalid\*.xml) do (
    echo.
    echo === Ошибка: неверный формат %%f
    python src\emulator.py --vfs %%f
)

pause
