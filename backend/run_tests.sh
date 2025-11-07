#!/bin/bash
# Script to run LoadTester tests
# This script ensures the testing environment is properly set up

echo "=========================================="
echo "LoadTester - Test Runner"
echo "=========================================="
echo ""

# Check if we're in the backend directory
if [ ! -f "pytest.ini" ]; then
    echo "Error: Please run this script from the backend directory"
    exit 1
fi

# Check if virtual environment exists
if [ ! -d "../.venv" ]; then
    echo "⚠ Virtual environment not found at ../.venv"
    echo "Creating virtual environment..."
    python -m venv ../.venv
fi

# Activate virtual environment (Windows)
if [ -f "../.venv/Scripts/activate" ]; then
    source ../.venv/Scripts/activate
# Activate virtual environment (Linux/Mac)
elif [ -f "../.venv/bin/activate" ]; then
    source ../.venv/bin/activate
fi

echo "✓ Virtual environment activated"
echo ""

# Install dependencies
echo "Installing dependencies..."
pip install -q -r requirements.txt
pip install -q -r requirements-test.txt
echo "✓ Dependencies installed"
echo ""

# Run tests
echo "Running tests..."
echo "=========================================="
python -m pytest tests/test_infrastructure_validation.py -v --tb=short
TEST_EXIT_CODE=$?

echo ""
echo "=========================================="
if [ $TEST_EXIT_CODE -eq 0 ]; then
    echo "✅ All tests passed!"
else
    echo "❌ Some tests failed"
fi
echo "=========================================="

exit $TEST_EXIT_CODE
