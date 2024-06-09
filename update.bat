echo Checking for updated files...

.lydienv\scripts\python updater.py

echo Updating dependencies, if needed...

.lydienv\scripts\python -m pip install -r requirements.txt

pause
