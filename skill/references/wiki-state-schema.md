# Wiki State Schema

## File Location

`.wiki_state.json` lives at the knowledge base root (same level as `raw/` and `wiki/`).

## Schema

```json
{
  "version": 1,
  "lastCompiled": "2026-04-03T12:00:00Z",
  "files": {
    "paper-attention.md": {
      "hash": "a1b2c3d4e5f6...",
      "concepts": ["attention-mechanism", "transformer", "self-attention"],
      "title": "Attention Is All You Need",
      "description": "Introduces the Transformer architecture based on self-attention, eliminating recurrence and convolutions.",
      "lastCompiled": "2026-04-03T12:00:00Z"
    },
    "subdir/notes-2024-03.md": {
      "hash": "e5f6g7h8i9j0...",
      "concepts": ["prompt-engineering", "chain-of-thought"],
      "title": "March 2024 Research Notes",
      "description": "Notes on prompt engineering techniques and chain-of-thought reasoning experiments.",
      "lastCompiled": "2026-04-03T11:30:00Z"
    }
  },
  "concepts": {
    "attention-mechanism": {
      "sources": ["paper-attention.md"],
      "lastUpdated": "2026-04-03T12:00:00Z"
    },
    "transformer": {
      "sources": ["paper-attention.md"],
      "lastUpdated": "2026-04-03T12:00:00Z"
    },
    "prompt-engineering": {
      "sources": ["subdir/notes-2024-03.md"],
      "lastUpdated": "2026-04-03T11:30:00Z"
    }
  }
}
```

## Field Descriptions

### Top-level

| Field | Type | Description |
|-------|------|-------------|
| `version` | integer | Schema version for forward compatibility. Currently `1`. |
| `lastCompiled` | string (ISO 8601) | Timestamp of last compile run. |
| `files` | object | Map from raw file path (relative to `raw/`) to compilation state. |
| `concepts` | object | Map from concept slug to metadata. Denormalized from `files` for O(1) lookup. |

### files[path]

| Field | Type | Description |
|-------|------|-------------|
| `hash` | string | SHA-256 of file content at last compile. |
| `concepts` | string[] | Concept slugs extracted from this file. |
| `title` | string | Document title for index generation. |
| `description` | string | One-sentence description for index generation. |
| `lastCompiled` | string (ISO 8601) | When this specific file was last processed. |

### concepts[slug]

| Field | Type | Description |
|-------|------|-------------|
| `sources` | string[] | Raw file paths that contributed to this concept. |
| `lastUpdated` | string (ISO 8601) | When the concept article was last regenerated. |

## Corruption Handling

If `.wiki_state.json` is:
- **Missing**: treat as empty state, do full recompile
- **Malformed JSON**: print warning, treat as empty state
- **version > 1**: print warning about unknown version, treat as empty state

After any corruption recovery, the next compile will reprocess all raw files.

## Denormalization Note

The `concepts` map can be derived from `files` (by collecting all concepts across all files). It exists for performance during compile — when checking whether a concept article needs its Sources section updated, direct lookup is faster than scanning all files.
