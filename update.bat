@echo off

echo Checking for updated files...

.lydienv\scripts\python update.py

echo Updating dependencies, if needed...

choice /m "Update dependencies? "
goto option-%errorlevel%

:option-1 doupdate
.lydienv\scripts\python -m pip install -r requirements.txt
goto end

:option-2 noupdate
echo Dependencies were not updated automatically.
goto end

:end
pause
