"""Deterministic read-only GitHub fixtures in a guarded disposable database."""
import os
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'backend'))
folder=Path(__file__).resolve().parents[1]/'.e2e'
folder.mkdir(exist_ok=True)
expected='sqlite:///'+str(folder/'civic.db').replace('\\','/')
if os.getenv('DATABASE_URL') != expected:
    raise SystemExit('Fixtures may only reset .e2e/civic.db.')
from app.store import Base, Repository, Task, SourceSettings, IssueInfo, IssueEnrichment, User, engine  # noqa: E402
from app.bootstrap import seed_accounts  # noqa: E402
from app.migrations import migrate  # noqa: E402
from app.enrichment import MODEL, fingerprint, interpret_requirements, project_context  # noqa: E402
from app.matching import derive_metadata  # noqa: E402
from app.security import hash_password  # noqa: E402
from sqlalchemy import select  # noqa: E402
from sqlalchemy.orm import Session  # noqa: E402
Base.metadata.drop_all(engine)
migrate(engine)
with Session(engine) as db:
    for email,password in seed_accounts(db):
        db.scalar(select(User).where(User.email==email)).password_hash=hash_password('fixture demo password')
    repo=db.scalar(select(Repository).where(Repository.path=='hotosm/tasking-manager'))
    settings=db.get(SourceSettings,repo.id)
    settings.fields={**settings.fields,'complete':True}
    repo.last_success=1700000000
    for number,title,labels,status in [(1,'Improve Python mapping API',['python','topic:Humanitarian mapping','beginner','effort:2h'],'open'),(2,'Improve map keyboard navigation',['javascript','accessibility'],'open'),(3,'Closed mapping issue',['python'],'closed')]:
        task=Task(repository_id=repo.id,source_id=str(number),title=title,description='Improve public-interest mapping software.',url=f'https://github.com/hotosm/tasking-manager/issues/{number}',status=status,labels=labels,metadata_fields=derive_metadata(labels))
        db.add(task);db.flush()
        if number == 1:
            fields=interpret_requirements(task, {'skills':[{'skill':'python','basis':'explicit','rationale':'The issue names Python.','source_quote':'Python'},{'skill':'testing','basis':'inferred','rationale':'The API change may require updating regression tests.','source_quote':None}],'difficulty':None,'difficulty_reason':None})
            db.add(IssueEnrichment(task_id=task.id,content_hash=fingerprint(task, project_context(settings.fields)),model=MODEL,fields=fields,updated_at=1700000000))
        db.add(IssueInfo(task_id=task.id,fields={'number':number,'assignees':[],'updated_at':'2026-10-28T12:00:00Z','available':True}))
    db.commit()
