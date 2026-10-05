import { defineConfig } from '@playwright/test';
import { resolve } from 'node:path';

const python = process.env.E2E_PYTHON || (process.platform === 'win32' ? 'backend/.venv/Scripts/python.exe' : 'backend/.venv/bin/python');
const browserOrigin = 'http://localhost:5174';
const databaseUrl = 'sqlite:///' + resolve('.e2e/civic.db').replaceAll(String.fromCharCode(92), '/');

export default defineConfig({
  testDir: './e2e',
  fullyParallel: false,
  workers: 1,
  use: { baseURL: browserOrigin, trace: 'retain-on-failure' },
  projects: [
    { name: 'wide', use: { browserName: 'chromium', viewport: { width: 1920, height: 1080 } } },
    { name: 'desktop', use: { browserName: 'chromium', viewport: { width: 1440, height: 900 } } },
    { name: 'mobile', use: { browserName: 'chromium', viewport: { width: 360, height: 800 } } },
  ],
  webServer: [
    { command: `${python} e2e/prepare.py && ${python} -m uvicorn app.main:app --app-dir backend --port 8001`, url: 'http://127.0.0.1:8001/health', env: { DATABASE_URL: databaseUrl, APP_ORIGIN: browserOrigin, COOKIE_SECURE: 'false' }, reuseExistingServer: false },
    { command: 'npm run dev -- --host localhost --port 5174 --strictPort', url: browserOrigin, env: { API_TARGET: 'http://127.0.0.1:8001' }, reuseExistingServer: false },
  ],
});
