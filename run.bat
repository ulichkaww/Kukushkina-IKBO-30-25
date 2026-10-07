@echo off
chcp 65001 > nul
cd /d "%~dp0"

echo Эмулятор, VFS demo. Команды: ls, cd, du, find, chmod, vfs-info, exit
python src\emulator.py --vfs vfs\demo.xml
pause
