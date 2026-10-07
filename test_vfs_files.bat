@echo off
chcp 65001 > nul
cd /d "%~dp0"

echo === VFS: files
python src\emulator.py --vfs vfs\files.xml --script tests\scripts\vfs_info.txt

pause
