Write-Host "Updating Civic Issue Matchmaker backend..."

# Check Docker
if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
    Write-Host "Docker is required but was not found."
    Write-Host "Please install Docker Desktop, start it, and run this script again."
    exit 1
}

# Check existing virtual environment
if (-not (Test-Path "backend\.venv")) {
    Write-Host "Existing backend virtual environment was not found."
    Write-Host "Run setup_backend.ps1 first."
    exit 1
}

# Activate virtual environment
& "backend\.venv\Scripts\Activate.ps1"

# Install updated dependencies
python -m pip install -r backend\requirements.txt

if ($LASTEXITCODE -ne 0) {
    Write-Host "Python dependency installation failed."
    exit 1
}

Write-Host "Python dependencies updated."

# Create .env if missing
if (-not (Test-Path "backend\.env")) {
    Write-Host "Creating backend\.env..."

    "DATABASE_URL=postgresql://civic_user:civic_password@localhost:5432/civic_matchmaker" |
        Out-File -Encoding ascii backend\.env

    Write-Host "backend\.env created."
}
else {
    Write-Host "backend\.env already exists. Leaving it unchanged."
}

# Start PostgreSQL
Write-Host "Starting PostgreSQL container..."

docker compose up -d

if ($LASTEXITCODE -ne 0) {
    Write-Host "Docker Compose failed to start PostgreSQL."
    exit 1
}

Write-Host "PostgreSQL container started."

# Run Ruff
ruff check backend

if ($LASTEXITCODE -ne 0) {
    Write-Host "Ruff checks failed."
    exit 1
}

# Run tests
Push-Location backend
python -m pytest
$pytestResult = $LASTEXITCODE
Pop-Location

if ($pytestResult -ne 0) {
    Write-Host "Backend tests failed."
    exit 1
}

Write-Host ""
Write-Host "Backend update complete."
Write-Host "Docker PostgreSQL is running and backend tests passed."