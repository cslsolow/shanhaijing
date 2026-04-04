import json
import os
from pathlib import Path


SELECTION_PROMPT = (
    "You are a retrieval assistant. Given a wiki index and a question, "
    "return a JSON array of 3-7 article filenames (relative to wiki/) most relevant to answering the question. "
    "Return ONLY the JSON array, nothing else. Example: [\"summaries/foo.md\", \"concepts/bar.md\"]"
)

ANSWER_PROMPT = (
    "You are a knowledge base assistant. Answer the user's question based on the provided wiki articles. "
    "Include [[wikilink]] citations. End with a ## Sources section listing articles consulted."
)

DEFAULT_CONFIG = {
    "provider": "anthropic",
    "model": "claude-haiku-4-5",
    "base_url": "",
}


def load_config(kb_path: str) -> dict:
    p = Path(kb_path) / ".shj.config.json"
    if p.exists():
        return {**DEFAULT_CONFIG, **json.loads(p.read_text())}
    return dict(DEFAULT_CONFIG)


def save_config(kb_path: str, config: dict):
    p = Path(kb_path) / ".shj.config.json"
    safe = {k: config[k] for k in ("provider", "model", "base_url") if k in config}
    p.write_text(json.dumps(safe, indent=2, ensure_ascii=False))


def _make_client(config: dict):
    provider = config.get("provider", "anthropic")
    base_url = config.get("base_url", "").strip()

    if provider == "anthropic":
        import anthropic
        kwargs = {}
        if base_url:
            kwargs["base_url"] = base_url
        return "anthropic", anthropic.Anthropic(
            api_key=os.environ.get("ANTHROPIC_API_KEY", ""),
            **kwargs,
        )

    if provider == "openai":
        import openai
        kwargs = {}
        if base_url:
            kwargs["base_url"] = base_url
        return "openai", openai.OpenAI(
            api_key=os.environ.get("OPENAI_API_KEY", "ollama"),
            **kwargs,
        )

    raise ValueError(f"Unknown provider: {provider!r}. Use 'anthropic' or 'openai'.")


def _select_articles(client, provider: str, model: str, index: str, question: str) -> list:
    user_msg = f"Wiki index:\n{index}\n\nQuestion: {question}"
    if provider == "anthropic":
        resp = client.messages.create(
            model=model, max_tokens=256,
            system=SELECTION_PROMPT,
            messages=[{"role": "user", "content": user_msg}],
        )
        text = resp.content[0].text.strip()
    else:
        resp = client.chat.completions.create(
            model=model, max_tokens=256,
            messages=[
                {"role": "system", "content": SELECTION_PROMPT},
                {"role": "user", "content": user_msg},
            ],
        )
        text = resp.choices[0].message.content.strip()

    try:
        start, end = text.index("["), text.rindex("]") + 1
        return json.loads(text[start:end])
    except (ValueError, json.JSONDecodeError):
        return []


def stream_query(kb_path: str, question: str, model_override: str = ""):
    config = load_config(kb_path)
    model = model_override or config.get("model", DEFAULT_CONFIG["model"])
    provider, client = _make_client(config)

    wiki = Path(kb_path) / "wiki"
    index_path = wiki / "_index.md"
    if not index_path.exists():
        yield {"error": "wiki/_index.md not found. Run /shj compile first."}
        return

    index = index_path.read_text(encoding="utf-8")
    selected = _select_articles(client, provider, model, index, question)

    parts = []
    for rel in selected[:7]:
        p = wiki / rel
        if p.exists():
            parts.append(f"### {rel}\n\n{p.read_text(encoding='utf-8')}")

    if not parts:
        parts = [f"### _index.md\n\n{index}"]

    context = "\n\n---\n\n".join(parts)
    user_msg = f"Articles:\n\n{context}\n\nQuestion: {question}"

    if provider == "anthropic":
        with client.messages.stream(
            model=model, max_tokens=2048,
            system=ANSWER_PROMPT,
            messages=[{"role": "user", "content": user_msg}],
        ) as s:
            for chunk in s.text_stream:
                yield {"chunk": chunk}
    else:
        s = client.chat.completions.create(
            model=model, max_tokens=2048, stream=True,
            messages=[
                {"role": "system", "content": ANSWER_PROMPT},
                {"role": "user", "content": user_msg},
            ],
        )
        for chunk in s:
            delta = chunk.choices[0].delta.content
            if delta:
                yield {"chunk": delta}

    yield {"done": True}
