import json
import os
from pathlib import Path

DEFAULTS = {
    "provider": "anthropic",
    "model": "claude-haiku-4-5",
    "base_url": "",
    "api_key": "",
    # Notion sync
    "notion_token": "",
    "notion_databases": [],
    "notion_pages": [],
    # Zotero sync
    "zotero_api_key": "",
    "zotero_user_id": "",
    "zotero_group_id": "",
    "zotero_collections": [],
    # Dream
    "dream_schedule": "0 23 * * *",
    "dream_interval_min": 45,
    "dream_token_budget": 30000,
    "dream_concepts_count": 7,
}

_LLM_FIELDS = ("provider", "model", "base_url", "api_key")
_SYNC_FIELDS = (
    "notion_token", "notion_databases", "notion_pages",
    "zotero_api_key", "zotero_user_id", "zotero_group_id", "zotero_collections",
)
_DREAM_FIELDS = (
    "dream_schedule", "dream_interval_min",
    "dream_token_budget", "dream_concepts_count",
)
_FIELDS = _LLM_FIELDS + _SYNC_FIELDS + _DREAM_FIELDS


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
    """Return config safe for API response — mask secrets."""
    c = dict(cfg)
    for secret_key in ("api_key", "notion_token", "zotero_api_key"):
        val = c.get(secret_key, "")
        c[secret_key] = f"...{val[-4:]}" if len(val) > 4 else ("****" if val else "")
    return c


def resolve_api_key(cfg: dict) -> str:
    """Config api_key takes priority; fall back to env var."""
    if cfg.get("api_key"):
        return cfg["api_key"]
    provider = cfg.get("provider", "anthropic")
    if provider == "anthropic":
        return os.environ.get("ANTHROPIC_API_KEY", "")
    return os.environ.get("OPENAI_API_KEY", "")
