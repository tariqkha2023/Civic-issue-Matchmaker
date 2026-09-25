#!/bin/bash

echo "Updating Civic Issue Matchmaker backend..."

# Make sure Docker exists
# Check Docker CLI
if ! command -v docker >/dev/null 2>&1; then
    if [ -x "$HOME/.docker/bin/docker" ]; then
        echo "Docker CLI found in $HOME/.docker/bin."
        echo "Adding Docker CLI to PATH..."

        export PATH="$HOME/.docker/bin:$PATH"

        if [ -f "$HOME/.zshrc" ]; then
            if ! grep -q 'export PATH="$HOME/.docker/bin:$PATH"' "$HOME/.zshrc"; then
                echo 'export PATH="$HOME/.docker/bin:$PATH"' >> "$HOME/.zshrc"
                echo "Docker CLI path added to ~/.zshrc."
            fi
        else
            echo 'export PATH="$HOME/.docker/bin:$PATH"' >> "$HOME/.zshrc"
            echo "Created ~/.zshrc and added Docker CLI path."
        fi
    else
        echo "Docker is required but was not found."
        echo "Please install Docker Desktop, start it, and run this script again."
        exit 1
    fi
fi


# Activate existing virtual environment
if [ ! -d "backend/.venv" ]; then
    echo "Existing backend virtual environment was not found."
    echo "Run ./setup_backend.sh first."
    exit 1
fi

source backend/.venv/bin/activate

# Install any new Python dependencies
python -m pip install -r backend/requirements.txt

echo "Python dependencies updated."

# Create local environment file if it does not exist
if [ ! -f "backend/.env" ]; then
    echo "Creating backend/.env..."

    cat > backend/.env <<'EOF'
DATABASE_URL=postgresql://civic_user:civic_password@localhost:5432/civic_matchmaker
EOF

    echo "backend/.env created."
else
    echo "backend/.env already exists. Leaving it unchanged."
fi

# Start PostgreSQL with Docker Compose
echo "Starting PostgreSQL container..."

docker compose up -d

if [ $? -ne 0 ]; then
    echo "Docker Compose failed to start PostgreSQL."
    exit 1
fi

echo "PostgreSQL container started."

# Run backend checks
echo "Running backend checks..."

ruff check backend

if [ $? -ne 0 ]; then
    echo "Ruff checks failed."
    exit 1
fi

cd backend || exit 1
python -m pytest

if [ $? -ne 0 ]; then
    echo "Backend tests failed."
    exit 1
fi

cd ..

echo ""
echo "Backend update complete."
echo "Docker PostgreSQL is running and backend tests passed."