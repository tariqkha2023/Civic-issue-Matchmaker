# Civic Issue Matchmaker 

## Getting Started (MAC INSTALLATION) - (WINDOWS -see below)

### Requirements

Before beginning, make sure you have:

- Git

### 1. Clone the project from GitHub

Open a terminal and run:

```bash
git clone https://github.com/tariqkha2023/Civic-issue-Matchmaker.git
```

This downloads the project to your computer and automatically connects your local Git repository to the shared GitHub repository.

Then enter the project folder which already has the following name, and call terminal:

```bash
cd Civic-issue-Matchmaker
```

You can VERIFY the GitHub connection with:

```bash
git remote -v
```

You should see the shared GitHub repository listed as `origin`.

### 2. Run the backend setup script

From the project root (Civic-issue-Matchmaker), run:

```bash
./setup_backend.sh
```

At the end this will:

- check that Python 3.12 is installed
- create a local Python virtual environment named `.venv` if one does not already exist
- install the correct Python packages that are listed in `backend/requirements.txt`

### 3. Activate the virtual environment

After the setup script finishes, (you will be back at the root) enter this to activate the environment manually:

```bash
source backend/.venv/bin/activate
```

Once activated, your terminal should show something such as:

```text
(.venv)
```

This means Python and `pip` (the Python package installer) are now using the project's isolated virtual environment.

### 4. Start the FastAPI backend

Move into the backend folder with this command:

```bash
cd backend
```

Then start the development server using this:

```bash
uvicorn app.main:app --reload
```

You should see a some kind of message showing that Uvicorn is running at:

```text
http://127.0.0.1:8000
```

### 5. Verify that the backend is working

Open this address in your browser:

```text
http://127.0.0.1:8000/health
```

You should receive:

```json
{
  "status": "ok"
}
```

### 6. After every session working on the project: 

To leave the virtual environment, run:

```bash
deactivate
```

## For Future Sessions working on the project

Before starting work, enter the project master folder and get the latest changes from GitHub,
(that is, any updates from everyone collaborating):

```bash
cd Civic-issue-Matchmaker
git pull
```

Then activate the backend environment:

```bash
source backend/.venv/bin/activate
```

Start the backend:

```bash
cd backend
uvicorn app.main:app --reload
```


## Basic Git Workflow

Before starting work:

```bash
git pull
```

After making changes:

```bash
git add .
git commit -m "Describe your changes"
git push
```





--------------------------------------------





## Windows Backend Setup

### 1. Clone the project from GitHub

Open PowerShell and run:

```powershell
git clone https://github.com/tariqkha2023/Civic-issue-Matchmaker.git
```

Then enter the project root folder with:

```powershell
cd Civic-issue-Matchmaker
```

You can verify the GitHub connection with:

```powershell
git remote -v
```

You should see the shared GitHub repository listed as `origin`.

### 2. Run the Windows backend setup script

From the project root, run:

```powershell
.\setup_backend.ps1
```

This will:

- check that Python 3.12 is installed
- create a local Python virtual environment named `.venv` if one does not already exist
- install the required Python packages listed in `backend\requirements.txt`

### If PowerShell blocks the setup script

If PowerShell reports that script execution is disabled, run this and then try the setup script again:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
```

This change only applies to the current PowerShell session.

Then try again, run:

```powershell
.\setup_backend.ps1
```

### 3. Activate the virtual environment

After the setup script finishes, (back at the root folder) activate the environment manually:

```powershell
.\backend\.venv\Scripts\Activate.ps1
```

Once activated, your PowerShell prompt should show something such as:

```text
(.venv)
```

This means Python and `pip` (pythong package installer) are now using the project's isolated virtual environment.

### 4. Start the FastAPI backend

Move into the backend folder with:

```powershell
cd backend
```

Then start the development server with:

```powershell
uvicorn app.main:app --reload
```

Uvicorn should start and display an address such as:

```text
http://127.0.0.1:8000
```

### 5. Verify that the backend is working

Open this address in your browser:

```text
http://127.0.0.1:8000/health
```

You should receive:

```json
{
  "status": "ok"
}
```

### 6. Everytime you are finished with a session working on the project

To leave the virtual environment, run:

```powershell
deactivate
```

## For Future working sessions

Before starting work, enter the project root folder and get the latest changes from GitHub:

```powershell
cd Civic-issue-Matchmaker
git pull
```

Then activate the virtual environment:

```powershell
.\backend\.venv\Scripts\Activate.ps1
```

Start the backend:

```powershell
cd backend
uvicorn app.main:app --reload
```