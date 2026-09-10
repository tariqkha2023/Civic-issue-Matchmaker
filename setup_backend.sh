#!/bin/bash

echo "Setting up Civic Issue Matchmaker backend..."

cd backend || exit 1

if command -v python3.12 >/dev/null 2>&1; then
    PYTHON_CMD=python3.12
elif command -v python3 >/dev/null 2>&1; then
    PYTHON_CMD=python3
else
    echo "Python 3 is not installed."
    exit 1
fi

if [ ! -d ".venv" ]; then
    $PYTHON_CMD -m venv .venv
fi

source .venv/bin/activate

pip install -r requirements.txt

echo "Backend setup complete."
echo "To activate the environment later, run:"
echo "source backend/.venv/bin/activate"