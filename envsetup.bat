@echo off

echo (py -m venv .vmbvenv) Creating virtual enviornment...

py -m venv .vmbvenv

echo (.vmbvenv\scripts\python -m pip install -r requirements.txt) Installing required packages...

.vmbvenv\scripts\python -m pip install -r requirements.txt

echo Enviornment setup complete.

pause