"""Bounded public GitHub research; no AI calls, arbitrary hosts or redirects."""

import base64
import re
import time
from urllib.parse import quote, unquote, urlparse

import httpx

from app.research_schema import MAX_AGE, VERSION, source_hash
from app.store import ResearchDocument

MAX_BYTES = 128000
MAX_TEXT = 12000
MAX_SOURCES = 8
API = "https://api.github.com/repos/"


class CollectionError(ValueError):
    pass


class Collector:
    def __init__(self, db, client, refresh=False):
        self.db, self.client, self.refresh = db, client, refresh
        self.seen = {}
        self.public_repos = set()

    def read(self, endpoint):
        # All endpoints are constructed below, never supplied by an issue verbatim.
        with self.client.stream(
            "GET",
            API + endpoint,
            follow_redirects=False,
            headers={"Accept": "application/vnd.github+json"},
        ) as response:
            if response.status_code != 200:
                raise CollectionError(f"GitHub returned HTTP {response.status_code}")
            body = bytearray()
            for chunk in response.iter_bytes():
                body.extend(chunk)
                if len(body) > MAX_BYTES:
                    raise CollectionError("Source exceeds collection size limit")
            import json

            return json.loads(body)

    def public(self, repo):
        if not re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", repo):
            raise CollectionError("Invalid GitHub repository")
        if repo not in self.public_repos:
            data = self.read(repo)
            if (
                data.get("private") is not False
                or data.get("full_name", "").lower() != repo.lower()
            ):
                raise CollectionError(
                    "Public repository identity could not be verified"
                )
            self.public_repos.add(repo)

    def document(self, repo, suffix, url, kind):
        if url in self.seen:
            return self.seen[url]
        old = self.db.get(ResearchDocument, url)
        if (
            old
            and not self.refresh
            and old.fields["fetched_at"] + MAX_AGE > time.time()
        ):
            self.seen[url] = old.fields
            return old.fields
        data = self.read(repo + suffix)
        if kind == "file":
            if (
                not isinstance(data, dict)
                or data.get("encoding") != "base64"
                or data.get("type") != "file"
            ):
                raise CollectionError("Source is not a text file")
            text = base64.b64decode(data["content"], validate=False).decode("utf-8")
        elif kind == "comments":
            if not isinstance(data, list):
                raise CollectionError("Invalid discussion response")
            text = "\n\n".join(str(c.get("body") or "") for c in data)
        else:
            text = str(data.get("title") or "") + "\n" + str(data.get("body") or "")
        if "\x00" in text:
            raise CollectionError("Source is not readable text")
        fields = {
            "url": url,
            "text": text[:MAX_TEXT],
            "fetched_at": time.time(),
            "truncated": len(text) > MAX_TEXT,
            "kind": kind,
        }
        if old is None:
            old = ResearchDocument(url=url)
            self.db.add(old)
        old.fields = fields
        self.seen[url] = fields
        return fields

    def collect(self, task, repo, project):
        self.public(repo)
        base = "https://github.com/" + repo
        if not re.fullmatch(re.escape(base) + r"/issues/[0-9]+", task.url):
            raise CollectionError("Issue URL does not match the public repository")
        now = time.time()
        original = task.title + "\n" + task.description
        sources = [
            {
                "url": task.url,
                "text": original[:MAX_TEXT],
                "kind": "issue",
                "fetched_at": now,
                "truncated": len(original) > MAX_TEXT,
            }
        ]
        limitations = [
            "Collection is bounded; external websites, images, attachments and unlinked code are not inspected.",
            "Discussion collection includes at most the first 20 comments; later decisions may be missing.",
        ]
        number = task.url.rsplit("/", 1)[1]
        requests = [
            ("/readme", base + "#readme", "file"),
            ("/contents/CONTRIBUTING.md", base + "/blob/HEAD/CONTRIBUTING.md", "file"),
            (
                f"/issues/{number}/comments?per_page=20",
                task.url + "#comments",
                "comments",
            ),
        ]
        # Only direct, same-repository GitHub links. No crawling or URL-provided credentials.
        links = list(
            dict.fromkeys(re.findall(r'https://[^\s<>"\)]+', task.description))
        )
        for link in links:
            parsed = urlparse(link)
            if parsed.netloc != "github.com" or parsed.query:
                continue
            path = unquote(parsed.path)
            if not path.startswith("/" + repo + "/"):
                continue
            tail = path[len(repo) + 2 :]
            if re.fullmatch(r"issues/[0-9]+", tail):
                requests.append(("/" + tail, base + "/" + tail, "issue"))
            elif tail.startswith("blob/"):
                parts = tail.split("/", 2)
                if len(parts) == 3 and not any(
                    p in (".", "..") for p in parts[2].split("/")
                ):
                    ref, filename = parts[1:]
                    requests.append(
                        (
                            "/contents/"
                            + quote(filename, safe="/")
                            + "?ref="
                            + quote(ref, safe=""),
                            base + "/" + tail,
                            "file",
                        )
                    )
        seen = {task.url}
        attempted = 0
        for suffix, url, kind in requests:
            if url in seen:
                continue
            if attempted >= MAX_SOURCES - 1:
                limitations.append(
                    "Additional linked sources exceeded the collection limit."
                )
                break
            seen.add(url)
            attempted += 1
            try:
                doc = self.document(repo, suffix, url, kind)
                if doc["text"].strip():
                    sources.append(doc)
            except (CollectionError, httpx.HTTPError, ValueError, KeyError, TypeError):
                limitations.append(
                    "Could not collect " + url + "; this source was not used."
                )
        if any(s["truncated"] for s in sources):
            limitations.append("One or more sources were truncated at the text limit.")
        return {
            "version": VERSION,
            "source_hash": source_hash(task, project),
            "issue_url": task.url,
            "project": project,
            "sources": sources,
            "collected_at": now,
            "expires_at": min(s["fetched_at"] for s in sources) + MAX_AGE,
            "limitations": limitations,
        }
