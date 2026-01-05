@echo off
echo Generating ModelZoo Architecture Diagram...
echo.

REM Install requirements if needed
pip install requests pillow --quiet

REM Run the Python script
python generate_diagram.py

echo.
pause

