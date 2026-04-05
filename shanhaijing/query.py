"""Query workflow — answer questions from the wiki using LLM."""

import json
from pathlib import Path
from typing import Generator

from . import config as cfg_mod
from . import llm

SELECTION_SYSTEM = (
    "You are a retrieval assistant. Given a wiki index and a question, "
    "return a JSON array of 3-7 article filenames (relative to wiki/) most relevant. "
    "Return ONLY the JSON array. Example: [\"summaries/foo.md\", \"concepts/bar.md\"]"
)

ANSWER_SYSTEM = (
    "You are a knowledge base assistant. Answer the user's question based on the provided wiki articles. "
    "Include [[wikilink]] citations. End with a ## Sources section listing articles consulted."
)


def _select_articles(cfg: dict, index: str, question: str) -> list[str]:
    raw = llm.call(cfg, SELECTION_SYSTEM,
                   f"Wiki index:\n{index}\n\nQuestion: {question}",
                   max_tokens=256)
    try:
        start, end = raw.index("["), raw.rindex("]") + 1
        return json.loads(raw[start:end])
    except (ValueError, json.JSONDecodeError):
        return []


def stream(kb_path: str, question: str, model_override: str = "") -> Generator[dict, None, None]:
    cfg = cfg_mod.load(kb_path)
    if model_override:
        cfg["model"] = model_override

    wiki = Path(kb_path) / "wiki"
    index_path = wiki / "_index.md"
    if not index_path.exists():
        yield {"error": "wiki/_index.md not found. Run compile first."}
        return

    index = index_path.read_text(encoding="utf-8")
    selected = _select_articles(cfg, index, question)

    parts = []
    for rel in selected[:7]:
        p = wiki / rel
        if p.exists():
            parts.append(f"### {rel}\n\n{p.read_text(encoding='utf-8')}")
    if not parts:
        parts = [f"### _index.md\n\n{index}"]

    context = "\n\n---\n\n".join(parts)

    # Load private/ as background knowledge for better context
    private_context = ""
    private_dir = Path(kb_path) / "private"
    if private_dir.exists():
        private_files = sorted(private_dir.glob("*.md"))
        if private_files:
            private_parts = []
            for p in private_files:
                content = p.read_text(encoding="utf-8")
                private_parts.append(f"### {p.name}\n\n{content}")
            private_context = "\n\n---\n\n".join(private_parts)

    if private_context:
        user_msg = f"Background Knowledge (Your Research):\n\n{private_context}\n\n---\n\nArticles:\n\n{context}\n\nQuestion: {question}"
    else:
        user_msg = f"Articles:\n\n{context}\n\nQuestion: {question}"

    for chunk in llm.stream(cfg, ANSWER_SYSTEM, user_msg):
        yield {"chunk": chunk}
    yield {"done": True}


def ask(kb_path: str, question: str, model_override: str = "") -> str:
    """Non-streaming version — returns full answer string."""
    parts = []
    for event in stream(kb_path, question, model_override):
        if "chunk" in event:
            parts.append(event["chunk"])
        elif "error" in event:
            raise RuntimeError(event["error"])
    return "".join(parts)
