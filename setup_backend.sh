#!/bin/bash

echo "Setting up Civic Issue Matchmaker backend..."

cd backend || exit 1

if ! command -v python3.12 >/dev/null 2>&1; then
    echo "Python 3.12 is required but was not found."
    echo "Please install Python 3.12 and run this script again."
    exit 1
fi

if [ ! -d ".venv" ]; then
    echo "Creating Python virtual environment..."
    python3.12 -m venv .venv
fi

source .venv/bin/activate

python -m pip install -r requirements.txt

echo "Backend setup complete."
echo "To activate the environment later, run:"
echo "source backend/.venv/bin/activate"