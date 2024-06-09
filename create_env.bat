echo Creating virtual enviornment...

py -3 -m venv .lydienv

echo Installing required packages...

.lydienv\scripts\python -m pip install -r requirements.txt

echo Enviornment setup complete.

pause
