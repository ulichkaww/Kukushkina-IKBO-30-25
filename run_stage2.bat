@echo off
chcp 65001 > nul
cd /d "%~dp0"

echo === 1. Параметры командной строки: --vfs и --script
python src\emulator.py --vfs vfs\minimal.xml --script tests\scripts\stage2_ok.txt

echo.
echo === 2. Только конфигурационный файл: --config
python src\emulator.py --config tests\configs\valid.json

echo.
echo === 3. Приоритет: --script из командной строки важнее файла
python src\emulator.py --config tests\configs\script_only.json --vfs vfs\demo.xml --script tests\scripts\stage2_ok.txt

echo.
echo === 4. Без скрипта: интерактивный режим, команды подаются через pipe
echo exit | python src\emulator.py --vfs vfs\demo.xml

echo.
echo === 5. Ошибка: конфигурационный файл не найден
python src\emulator.py --config tests\configs\nofile.json

echo.
echo === 6. Ошибка: неверный JSON
python src\emulator.py --config tests\configs\broken.json

echo.
echo === 7. Ошибка: неверный тип параметра в конфигурации
python src\emulator.py --config tests\configs\bad_type.json

echo.
echo === 8. Ошибка: стартовый скрипт не найден
python src\emulator.py --script tests\scripts\nofile.txt

echo.
echo === 9. Ошибка при выполнении скрипта: остановка на первой ошибке
python src\emulator.py --script tests\scripts\stage2_error.txt

pause
