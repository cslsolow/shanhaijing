"""LLM client abstraction — Anthropic and OpenAI-compatible."""

import os
from typing import Generator


def _anthropic_client(cfg: dict):
    import anthropic
    from .config import resolve_api_key
    kwargs = {}
    if cfg.get("base_url"):
        kwargs["base_url"] = cfg["base_url"]
    return anthropic.Anthropic(api_key=resolve_api_key(cfg), **kwargs)


def _openai_client(cfg: dict):
    import openai
    from .config import resolve_api_key
    kwargs = {}
    if cfg.get("base_url"):
        kwargs["base_url"] = cfg["base_url"]
    api_key = resolve_api_key(cfg) or "ollama"
    return openai.OpenAI(api_key=api_key, **kwargs)


def call(cfg: dict, system: str, user: str, max_tokens: int = 1024) -> str:
    provider = cfg.get("provider", "anthropic")
    model = cfg.get("model", "claude-haiku-4-5")

    if provider == "anthropic":
        client = _anthropic_client(cfg)
        resp = client.messages.create(
            model=model, max_tokens=max_tokens,
            system=system,
            messages=[{"role": "user", "content": user}],
            timeout=60,
        )
        return resp.content[0].text

    if provider == "openai":
        client = _openai_client(cfg)
        resp = client.chat.completions.create(
            model=model, max_tokens=max_tokens,
            timeout=60,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
        )
        return resp.choices[0].message.content

    raise ValueError(f"Unknown provider: {provider!r}")


def stream(cfg: dict, system: str, user: str, max_tokens: int = 2048) -> Generator[str, None, None]:
    provider = cfg.get("provider", "anthropic")
    model = cfg.get("model", "claude-haiku-4-5")

    if provider == "anthropic":
        client = _anthropic_client(cfg)
        with client.messages.stream(
            model=model, max_tokens=max_tokens,
            system=system,
            messages=[{"role": "user", "content": user}],
        ) as s:
            yield from s.text_stream
        return

    if provider == "openai":
        client = _openai_client(cfg)
        s = client.chat.completions.create(
            model=model, max_tokens=max_tokens, stream=True,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
        )
        for chunk in s:
            delta = chunk.choices[0].delta.content
            if delta:
                yield delta
        return

    raise ValueError(f"Unknown provider: {provider!r}")
