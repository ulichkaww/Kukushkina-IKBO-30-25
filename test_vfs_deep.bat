@echo off
chcp 65001 > nul
cd /d "%~dp0"

echo === VFS: deep
python src\emulator.py --vfs vfs\deep.xml --script tests\scripts\vfs_info.txt

pause
