"""Create deterministic browser fixtures in a disposable database."""
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'backend'))
fixture_path = Path(__file__).resolve().parents[1] / '.e2e'
fixture_path.mkdir(exist_ok=True)
expected_url = 'sqlite:///' + str(fixture_path / 'civic.db').replace('\\', '/')
if os.environ.get('DATABASE_URL') != expected_url:
    raise SystemExit('Browser fixtures may only reset the disposable .e2e/civic.db database.')
from app.store import Base, Repository, Task, engine  # noqa: E402
from app.demo import seed_demo  # noqa: E402
from app.matching import derive_metadata  # noqa: E402
from sqlalchemy.orm import Session  # noqa: E402

Base.metadata.drop_all(engine)
Base.metadata.create_all(engine)
with Session(engine) as db:
    repo = Repository(source='github', path='civic/transit', last_success=1700000000)
    db.add(repo)
    db.flush()
    for i, title, labels in [(1, 'Improve Python transit API', ['python', 'topic:Transportation', 'beginner', 'effort:2h']),
                              (2, 'Design React dashboard', ['react', 'topic:Government data', 'advanced', 'effort:30h'])]:
        db.add(Task(repository_id=repo.id, source_id=str(i), title=title, description='Make public services more accessible.',
                    url=f'https://github.com/civic/transit/issues/{i}', status='open', labels=labels,
                    metadata_fields=derive_metadata(labels)))
    db.commit()

with Session(engine) as db:
    seed_demo(db)

from app.bootstrap import seed_accounts
with Session(engine) as db:
    for email, password in seed_accounts(db):
        # Test-only fixed credentials in the guarded disposable fixture database.
        from app.store import User
        from app.security import hash_password
        from sqlalchemy import select
        db.scalar(select(User).where(User.email == email)).password_hash = hash_password('fixture demo password')
    db.commit()
