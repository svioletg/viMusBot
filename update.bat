echo Checking for updated files...

.vmbvenv\scripts\python updater.py

echo Updating dependencies, if needed...

.vmbvenv\scripts\python -m pip install -r requirements.txt

pause
