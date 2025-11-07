@echo off
REM Script to run LoadTester tests on Windows
REM This script ensures the testing environment is properly set up

echo ==========================================
echo LoadTester - Test Runner (Windows)
echo ==========================================
echo.

REM Check if we're in the backend directory
if not exist "pytest.ini" (
    echo Error: Please run this script from the backend directory
    exit /b 1
)

REM Check if virtual environment exists
if not exist "..\..venv" (
    echo Warning: Virtual environment not found at ..\.venv
    echo Creating virtual environment...
    python -m venv ..\.venv
)

REM Activate virtual environment
call ..\.venv\Scripts\activate.bat
echo Virtual environment activated
echo.

REM Install dependencies
echo Installing dependencies...
pip install -q -r requirements.txt
pip install -q -r requirements-test.txt
echo Dependencies installed
echo.

REM Run tests
echo Running tests...
echo ==========================================
python -m pytest tests/test_infrastructure_validation.py -v --tb=short

if %ERRORLEVEL% EQU 0 (
    echo.
    echo ==========================================
    echo All tests passed!
    echo ==========================================
) else (
    echo.
    echo ==========================================
    echo Some tests failed
    echo ==========================================
)

exit /b %ERRORLEVEL%
