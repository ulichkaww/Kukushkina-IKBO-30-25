@echo off
chcp 65001 > nul
cd /d "%~dp0"

set EMU_DIR=home/alex
echo === Стартовый скрипт этапов 1-3 (VFS demo)
python src\emulator.py --vfs vfs\demo.xml --script tests\scripts\stage3_start.txt

echo.
echo === Ошибки команд в интерактивном режиме: диалог не прерывается
(echo foo & echo cd a b & echo exit 5 & echo ls ^"unclosed & echo vfs-info 1 & echo exit) | python src\emulator.py --vfs vfs\demo.xml

pause
