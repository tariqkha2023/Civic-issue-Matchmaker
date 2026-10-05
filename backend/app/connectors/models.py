from dataclasses import dataclass, field


@dataclass
class RepositoryTask:
    source: str
    source_id: str
    repository: str
    title: str
    description: str
    url: str
    status: str
    labels: list[str] = field(default_factory=list)