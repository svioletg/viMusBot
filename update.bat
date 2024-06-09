@echo off

echo Checking for updated files...

.lydienv\scripts\python update.py

echo Updating dependencies, if needed...

@REM .lydienv\scripts\python -m pip install -r requirements.txt

pause
