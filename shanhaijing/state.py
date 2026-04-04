import hashlib
import json
from pathlib import Path

EMPTY = {"version": 1, "files": {}, "concepts": {}}


def load(kb_path: str) -> dict:
    p = Path(kb_path) / ".wiki_state.json"
    if p.exists():
        return json.loads(p.read_text())
    return dict(EMPTY)


def save(kb_path: str, state: dict):
    p = Path(kb_path) / ".wiki_state.json"
    p.write_text(json.dumps(state, indent=2, ensure_ascii=False))


def file_hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def diff(kb_path: str) -> tuple[list, list, list]:
    """Return (new, changed, deleted) raw/*.md paths relative to kb_path."""
    state = load(kb_path)
    tracked = state.get("files", {})
    raw = Path(kb_path) / "raw"

    current = {}
    for p in sorted(raw.rglob("*.md")):
        rel = str(p.relative_to(kb_path))
        current[rel] = file_hash(p)

    new = [k for k in current if k not in tracked]
    changed = [k for k in current if k in tracked and current[k] != tracked[k]["hash"]]
    deleted = [k for k in tracked if k not in current]
    return new, changed, deleted
