@echo off
chcp 65001 > nul
cd /d "%~dp0"

echo === VFS: minimal
python src\emulator.py --vfs vfs\minimal.xml --script tests\scripts\vfs_info.txt

pause
