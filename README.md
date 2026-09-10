# Civic Issue Matchmaker

## Getting Started

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

- enter into the `backend` folder 
- check that Python 3.12 is installed
- create a local Python virtual environment named `.venv` if one does not already exist
- install the correct Python packages that are listed in `backend/requirements.txt`

### 3. Activate the virtual environment

After the setup script finishes, enter this to activate the environment manually:

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

