Write-Host "Setting up Civic Issue Matchmaker backend..."

Push-Location backend

if (Get-Command py -ErrorAction SilentlyContinue) {
    $pythonVersion = & py -3.12 --version 2>$null

    if ($LASTEXITCODE -ne 0) {
        Write-Host "Python 3.12 is required but was not found."
        Write-Host "Please install Python 3.12 and run this script again."
        Pop-Location
        exit 1
    }

    $PYTHON_CMD = "py"
}
elseif (Get-Command python -ErrorAction SilentlyContinue) {
    $pythonVersion = & python --version 2>&1

    if ($pythonVersion -notmatch "Python 3\.12") {
        Write-Host "Python 3.12 is required but was not found."
        Write-Host "Please install Python 3.12 and run this script again."
        Pop-Location
        exit 1
    }

    $PYTHON_CMD = "python"
}
else {
    Write-Host "Python 3.12 is required but was not found."
    Write-Host "Please install Python 3.12 and run this script again."
    Pop-Location
    exit 1
}

if (-not (Test-Path ".venv")) {
    Write-Host "Creating Python virtual environment..."

    if ($PYTHON_CMD -eq "py") {
        & py -3.12 -m venv .venv
    }
    else {
        & python -m venv .venv
    }
}

& ".\.venv\Scripts\Activate.ps1"

python -m pip install -r requirements.txt

Pop-Location

Write-Host "Backend setup complete."
Write-Host "To activate the environment later, run:"
Write-Host ".\backend\.venv\Scripts\Activate.ps1"