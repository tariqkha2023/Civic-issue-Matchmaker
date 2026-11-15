import { execFileSync } from 'node:child_process';
import { resolve } from 'node:path';
import { test as base, expect } from '@playwright/test';

// Every browser repeats the same account journeys against a guarded disposable
// database. Isolate their auth-attempt history without weakening app throttling.
// One worker runs these fixtures sequentially.
export const test = base.extend({
  authHistory: [async ({}, use) => {
    const python = process.env.E2E_PYTHON || (process.platform === 'win32' ? 'backend/.venv/Scripts/python.exe' : 'backend/.venv/bin/python');
    execFileSync(python, ['-c', `
import pathlib,sqlite3,sys
path=pathlib.Path(sys.argv[1]).resolve()
expected=(pathlib.Path.cwd()/'.e2e'/'civic.db').resolve()
if path != expected or not path.is_file(): raise SystemExit('Refusing non-fixture database')
with sqlite3.connect('file:'+str(path)+'?mode=rw',uri=True) as db:
 db.execute('DELETE FROM auth_events')
`, resolve('.e2e/civic.db')]);
    await use();
  }, { auto: true }],
});
export { expect };
