from dataclasses import dataclass


@dataclass
class RepositoryTask:
    source: str
    source_id: str
    title: str
    description: str
    url: str
    status: str