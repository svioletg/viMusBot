@echo off

echo Creating virtual enviornment, this can take a minute...

py -3 -m venv .lydienv

echo Installing required packages...

.lydienv\scripts\python -m pip install -r requirements.txt

echo Enviornment setup complete. Use "start.bat" to run the bot.

pause
