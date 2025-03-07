@echo off

echo Creating a virtual python environment (venv)
@echo on
rmdir .\venv\ /S /Q
python -m venv .\venv\

@echo off
echo Installing dependencies
@echo on

.\venv\Scripts\pip.exe install -r requirements.txt
.\venv\Scripts\pip.exe install windows-curses
.\venv\Scripts\pip.exe install geopy


@echo off
echo Loading lp.sql
@echo on

"C:\Program Files\MariaDB 11.7\bin\mariadb.exe" -u metropolia --password=metropolia flight_game < ./data/lp.sql

@echo off
echo
echo
echo Setup has now finished.
pause
