@echo off
echo ====================================
echo   Budget Planner - Starting...
echo ====================================
echo.
echo Installing dependencies...
pip install -r requirements.txt
echo.
echo Starting Flask application...
echo Open your browser to: http://localhost:5000
echo.
echo Press CTRL+C to stop the server
echo ====================================
python app.py
