import json
import os
from pathlib import Path

DEFAULTS = {
    "provider": "anthropic",
    "model": "claude-haiku-4-5",
    "base_url": "",
    "api_key": "",
}

_FIELDS = ("provider", "model", "base_url", "api_key")


def load(kb_path: str) -> dict:
    p = Path(kb_path) / ".shj.config.json"
    if p.exists():
        return {**DEFAULTS, **json.loads(p.read_text())}
    return dict(DEFAULTS)


def save(kb_path: str, cfg: dict):
    p = Path(kb_path) / ".shj.config.json"
    safe = {k: cfg[k] for k in _FIELDS if k in cfg}
    p.write_text(json.dumps(safe, indent=2, ensure_ascii=False))


def masked(cfg: dict) -> dict:
    """Return config safe for API response — mask api_key."""
    c = dict(cfg)
    key = c.get("api_key", "")
    c["api_key"] = f"...{key[-4:]}" if len(key) > 4 else ("****" if key else "")
    return c


def resolve_api_key(cfg: dict) -> str:
    """Config api_key takes priority; fall back to env var."""
    if cfg.get("api_key"):
        return cfg["api_key"]
    provider = cfg.get("provider", "anthropic")
    if provider == "anthropic":
        return os.environ.get("ANTHROPIC_API_KEY", "")
    return os.environ.get("OPENAI_API_KEY", "")
