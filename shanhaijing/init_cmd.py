"""Init workflow — create directory scaffold."""

from pathlib import Path

from . import state


def run(kb_path: str, verbose: bool = True) -> bool:
    base = Path(kb_path)
    created = not base.exists()
    (base / "raw").mkdir(parents=True, exist_ok=True)
    (base / "wiki" / "summaries").mkdir(parents=True, exist_ok=True)
    (base / "wiki" / "concepts").mkdir(parents=True, exist_ok=True)

    state_path = base / ".wiki_state.json"
    if not state_path.exists():
        state.save(kb_path, dict(state.EMPTY))

    index_path = base / "wiki" / "_index.md"
    if not index_path.exists():
        index_path.write_text("# Wiki Index\n", encoding="utf-8")

    if verbose:
        action = "Created" if created else "Initialized"
        print(f"{action}: {base.resolve()}")

    return True
