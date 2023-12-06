echo Checking for updated files...

.vmbvenv\scripts\python update.py

echo Updating dependencies...

.vmbvenv\scripts\python -m pip install -r requirements.txt

pause