@echo off
chcp 65001 > nul
cd /d "%~dp0"

echo === Этап 4: ls, cd, du, find во всех режимах (VFS demo)
python src\emulator.py --vfs vfs\demo.xml --script tests\scripts\stage4_start.txt

echo.
echo === Ошибки ls, cd, du, find: диалог не прерывается (VFS demo)
(echo ls nofile & echo ls -z & echo ls --all & echo cd nofile & echo cd readme.txt & echo cd a b & echo du nofile & echo du -x & echo find nofile & echo find -name & echo find -type x & echo find -foo bar & echo exit) | python src\emulator.py --vfs vfs\demo.xml

echo.
echo === Права доступа: каталоги без чтения и без входа (VFS locked)
(echo ls -l & echo ls private & echo cd private & echo ls noexec & echo cd noexec & echo du private & echo find private & echo exit) | python src\emulator.py --vfs vfs\locked.xml

echo.
echo === Скрипт останавливается на первой ошибке команды
echo ls> tests\scripts\tmp_error.txt
echo cd nofile>> tests\scripts\tmp_error.txt
echo ls bin>> tests\scripts\tmp_error.txt
python src\emulator.py --vfs vfs\demo.xml --script tests\scripts\tmp_error.txt
del tests\scripts\tmp_error.txt

pause
