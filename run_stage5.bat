@echo off
chcp 65001 > nul
cd /d "%~dp0"

echo === Этап 5: chmod во всех режимах (VFS demo)
python src\emulator.py --vfs vfs\demo.xml --script tests\scripts\stage5_start.txt

echo.
echo === Ошибки chmod: диалог не прерывается (VFS demo)
(echo chmod & echo chmod 644 & echo chmod 999 readme.txt & echo chmod u+q readme.txt & echo chmod 644 nofile & echo chmod -R & echo ls -l readme.txt & echo exit) | python src\emulator.py --vfs vfs\demo.xml

echo.
echo === Скрипт останавливается на первой ошибке chmod
echo chmod 600 readme.txt> tests\scripts\tmp_error.txt
echo chmod 999 readme.txt>> tests\scripts\tmp_error.txt
echo chmod 777 readme.txt>> tests\scripts\tmp_error.txt
python src\emulator.py --vfs vfs\demo.xml --script tests\scripts\tmp_error.txt
del tests\scripts\tmp_error.txt

pause
