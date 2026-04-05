"""Sync workflow — pull from Notion and Zotero into raw/."""

import hashlib
import json
import re
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path


# ── helpers ──────────────────────────────────────────────────────────────────

def _slugify(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")[:60]


def _write_if_changed(path: Path, content: str) -> bool:
    """Write file only if content changed. Returns True if written."""
    path.parent.mkdir(parents=True, exist_ok=True)
    new_hash = hashlib.sha256(content.encode()).hexdigest()
    if path.exists():
        old_hash = hashlib.sha256(path.read_text(encoding="utf-8").encode()).hexdigest()
        if old_hash == new_hash:
            return False
    path.write_text(content, encoding="utf-8")
    return True


def _load_sync_state(kb_path: str) -> dict:
    p = Path(kb_path) / ".shj.sync.json"
    if p.exists():
        return json.loads(p.read_text())
    return {"notion": {}, "zotero": {}}


def _save_sync_state(kb_path: str, state: dict):
    p = Path(kb_path) / ".shj.sync.json"
    p.write_text(json.dumps(state, indent=2, ensure_ascii=False))


# ── Notion ────────────────────────────────────────────────────────────────────

def _notion_block_to_md(block: dict, client) -> str:
    """Recursively convert a Notion block to markdown."""
    t = block.get("type", "")
    data = block.get(t, {})

    def rich_text(arr):
        out = ""
        for seg in arr:
            s = seg.get("plain_text", "")
            ann = seg.get("annotations", {})
            if ann.get("code"):
                s = f"`{s}`"
            if ann.get("bold"):
                s = f"**{s}**"
            if ann.get("italic"):
                s = f"*{s}*"
            if ann.get("strikethrough"):
                s = f"~~{s}~~"
            out += s
        return out

    def children_md(block_id):
        try:
            kids = client.blocks.children.list(block_id=block_id, page_size=100)
            return "\n".join(_notion_block_to_md(b, client) for b in kids.get("results", []))
        except Exception:
            return ""

    lines = []
    if t == "paragraph":
        lines.append(rich_text(data.get("rich_text", [])))
    elif t in ("heading_1", "heading_2", "heading_3"):
        level = {"heading_1": "#", "heading_2": "##", "heading_3": "###"}[t]
        lines.append(f"{level} {rich_text(data.get('rich_text', []))}")
    elif t == "bulleted_list_item":
        lines.append(f"- {rich_text(data.get('rich_text', []))}")
        if block.get("has_children"):
            lines.append(children_md(block["id"]))
    elif t == "numbered_list_item":
        lines.append(f"1. {rich_text(data.get('rich_text', []))}")
        if block.get("has_children"):
            lines.append(children_md(block["id"]))
    elif t == "code":
        lang = data.get("language", "")
        code = rich_text(data.get("rich_text", []))
        lines.append(f"```{lang}\n{code}\n```")
    elif t == "quote":
        lines.append(f"> {rich_text(data.get('rich_text', []))}")
    elif t == "callout":
        lines.append(f"> {rich_text(data.get('rich_text', []))}")
    elif t == "divider":
        lines.append("---")
    elif t == "toggle":
        lines.append(rich_text(data.get("rich_text", [])))
        if block.get("has_children"):
            lines.append(children_md(block["id"]))
    elif t == "image":
        url = (data.get("external") or data.get("file") or {}).get("url", "")
        caption = rich_text(data.get("caption", []))
        lines.append(f"![{caption}]({url})")
    elif t == "child_page":
        pass  # handled separately as its own page

    return "\n".join(lines)


def _notion_page_to_md(page: dict, client) -> str:
    """Convert a full Notion page to markdown string."""
    props = page.get("properties", {})

    # Extract title
    title = ""
    for prop in props.values():
        if prop.get("type") == "title":
            segs = prop.get("title", [])
            title = "".join(s.get("plain_text", "") for s in segs)
            break
    if not title:
        title = page.get("id", "untitled")

    # Metadata
    created = page.get("created_time", "")[:10]
    edited = page.get("last_edited_time", "")[:10]
    url = page.get("url", "")

    # Blocks → markdown
    blocks = []
    cursor = None
    while True:
        kwargs = {"block_id": page["id"], "page_size": 100}
        if cursor:
            kwargs["start_cursor"] = cursor
        resp = client.blocks.children.list(**kwargs)
        blocks.extend(resp.get("results", []))
        if not resp.get("has_more"):
            break
        cursor = resp.get("next_cursor")

    body = "\n\n".join(
        _notion_block_to_md(b, client) for b in blocks
        if _notion_block_to_md(b, client).strip()
    )

    today = datetime.now(timezone.utc).date().isoformat()
    return f"""---
title: "{title}"
source: notion
notion_url: {url}
created: {created}
edited: {edited}
ingested: {today}
visibility: private
type: note
---

# {title}

{body}
""".strip()


def sync_notion(kb_path: str, cfg: dict, verbose: bool = True) -> dict:
    token = cfg.get("notion_token", "")
    database_ids = cfg.get("notion_databases", [])
    page_ids = cfg.get("notion_pages", [])

    if not token:
        return {"error": "notion_token not configured", "synced": 0, "skipped": 0}

    try:
        from notion_client import Client
    except ImportError:
        return {"error": "notion-client not installed: uv add notion-client", "synced": 0, "skipped": 0}

    client = Client(auth=token)
    raw_dir = Path(kb_path) / "raw" / "notion"
    raw_dir.mkdir(parents=True, exist_ok=True)

    state = _load_sync_state(kb_path)
    notion_state = state.get("notion", {})

    synced = skipped = errors = 0
    pages_to_sync = []

    # Collect pages from databases
    for db_id in database_ids:
        try:
            cursor = None
            while True:
                kwargs = {"database_id": db_id, "page_size": 100}
                if cursor:
                    kwargs["start_cursor"] = cursor
                resp = client.databases.query(**kwargs)
                pages_to_sync.extend(resp.get("results", []))
                if not resp.get("has_more"):
                    break
                cursor = resp.get("next_cursor")
        except Exception as e:
            if verbose:
                print(f"  [notion] DB {db_id} error: {e}")
            errors += 1

    # Individual pages
    for page_id in page_ids:
        try:
            pages_to_sync.append(client.pages.retrieve(page_id=page_id))
        except Exception as e:
            if verbose:
                print(f"  [notion] page {page_id} error: {e}")
            errors += 1

    for page in pages_to_sync:
        page_id = page["id"]
        edited = page.get("last_edited_time", "")

        # Skip if not changed since last sync
        if notion_state.get(page_id) == edited:
            skipped += 1
            continue

        try:
            md = _notion_page_to_md(page, client)

            # filename from title
            props = page.get("properties", {})
            title = ""
            for prop in props.values():
                if prop.get("type") == "title":
                    title = "".join(s.get("plain_text", "") for s in prop.get("title", []))
                    break
            filename = f"notion-{_slugify(title) or page_id[:8]}.md"
            path = raw_dir / filename

            written = _write_if_changed(path, md)
            if written:
                synced += 1
                if verbose:
                    print(f"  [notion] ✓ {filename}")
            else:
                skipped += 1

            notion_state[page_id] = edited
        except Exception as e:
            if verbose:
                print(f"  [notion] error on {page_id}: {e}")
            errors += 1

    state["notion"] = notion_state
    _save_sync_state(kb_path, state)

    return {"synced": synced, "skipped": skipped, "errors": errors}


# ── Zotero ────────────────────────────────────────────────────────────────────

def _zotero_item_to_md(item: dict, notes: list[str]) -> str:
    data = item.get("data", {})
    item_type = data.get("itemType", "journalArticle")
    title = data.get("title", "Untitled")

    authors = []
    for creator in data.get("creators", []):
        if creator.get("creatorType") in ("author", "editor"):
            last = creator.get("lastName", "")
            first = creator.get("firstName", "")
            authors.append(f"{last}, {first}".strip(", "))
    authors_str = "; ".join(authors) if authors else ""

    year = data.get("date", "")[:4] if data.get("date") else ""
    abstract = data.get("abstractNote", "")
    doi = data.get("DOI", "")
    url = data.get("url", "")
    publication = data.get("publicationTitle") or data.get("bookTitle") or data.get("conferenceName") or ""
    tags = [t.get("tag", "") for t in data.get("tags", [])]
    today = datetime.now(timezone.utc).date().isoformat()

    # canonical source link: prefer DOI, fallback to url
    source_url = f"https://doi.org/{doi}" if doi else url

    notes_md = ""
    if notes:
        notes_md = "\n\n## Notes\n\n" + "\n\n".join(notes)

    meta_lines = [f"- **Authors**: {authors_str}"] if authors_str else []
    if year:
        meta_lines.append(f"- **Year**: {year}")
    if publication:
        meta_lines.append(f"- **Published in**: {publication}")
    if doi:
        meta_lines.append(f"- **DOI**: [{doi}](https://doi.org/{doi})")
    if url:
        meta_lines.append(f"- **URL**: {url}")
    if tags:
        meta_lines.append(f"- **Tags**: {', '.join(tags)}")

    meta_block = "\n".join(meta_lines)

    return f"""---
title: "{title}"
source: zotero
type: {item_type}
authors: "{authors_str}"
year: "{year}"
ingested: {today}
visibility: private
source_url: {source_url}
---

# {title}

{meta_block}

## Abstract

{abstract or "(no abstract)"}
{notes_md}
""".strip()


def _pdf_to_md(pdf_path: Path, item: dict, cfg: dict, notes: list[str] = None) -> str:
    """Extract full text from PDF via pymupdf4llm and use LLM to write structured markdown."""
    try:
        import pymupdf4llm
    except ImportError:
        return ""

    from . import llm as llm_mod
    import pymupdf

    # Read only first 50% of pages
    doc = pymupdf.open(str(pdf_path))
    total_pages = len(doc)
    doc.close()
    half_pages = max(1, total_pages // 2)
    pages = list(range(half_pages))

    full_text = pymupdf4llm.to_markdown(str(pdf_path), pages=pages)
    # cap at ~12000 chars to stay within context
    if len(full_text) > 12000:
        full_text = full_text[:12000] + "\n\n[truncated]"

    data = item.get("data", {})
    title = data.get("title", "Untitled")
    authors = []
    for creator in data.get("creators", []):
        if creator.get("creatorType") in ("author", "editor"):
            last = creator.get("lastName", "")
            first = creator.get("firstName", "")
            authors.append(f"{last}, {first}".strip(", "))
    authors_str = "; ".join(authors) if authors else ""
    year = data.get("date", "")[:4] if data.get("date") else ""
    doi = data.get("DOI", "")
    url = data.get("url", "")
    source_url = f"https://doi.org/{doi}" if doi else url
    today = datetime.now(timezone.utc).date().isoformat()

    system = """\
You are a research paper analyst. Given the full text of a paper, write a structured markdown document capturing:
- Key contributions and claims
- Methodology (briefly)
- Main results / findings
- Limitations or open questions

Output ONLY the markdown body (no frontmatter), starting from ## Summary.
Write in the same language as the paper. Be thorough but concise — aim for 400-800 words.\
"""
    notes_block = ""
    if notes:
        notes_block = "\n\nReader notes:\n" + "\n\n".join(notes)

    body = llm_mod.call(
        cfg, system,
        f"Title: {title}\nAuthors: {authors_str}\nYear: {year}\n\nFull text:\n{full_text}{notes_block}",
        max_tokens=1200,
    )

    return f"""---
title: "{title}"
source: zotero
type: {data.get('itemType', 'journalArticle')}
authors: "{authors_str}"
year: "{year}"
ingested: {today}
visibility: private
source_url: {source_url}
fulltext: true
---

# {title}

- **Authors**: {authors_str}
- **Year**: {year}
{f'- **DOI**: [{doi}](https://doi.org/{doi})' if doi else ''}
{f'- **URL**: {url}' if url else ''}

{body}
""".strip()


def sync_zotero(kb_path: str, cfg: dict, verbose: bool = True) -> dict:
    api_key = cfg.get("zotero_api_key", "")
    user_id = cfg.get("zotero_user_id", "")
    group_id = cfg.get("zotero_group_id", "")
    collection_keys = cfg.get("zotero_collections", [])  # [] = all

    if not api_key:
        return {"error": "zotero_api_key not configured", "synced": 0, "skipped": 0}
    if not user_id and not group_id:
        return {"error": "zotero_user_id or zotero_group_id required", "synced": 0, "skipped": 0}

    try:
        from pyzotero import zotero as pyz
    except ImportError:
        return {"error": "pyzotero not installed: uv add pyzotero", "synced": 0, "skipped": 0}

    if group_id:
        zot = pyz.Zotero(group_id, "group", api_key)
    else:
        zot = pyz.Zotero(user_id, "user", api_key)

    raw_dir = Path(kb_path) / "raw" / "zotero"
    raw_dir.mkdir(parents=True, exist_ok=True)

    state = _load_sync_state(kb_path)
    zotero_state = state.get("zotero", {})

    synced = skipped = errors = 0

    try:
        if collection_keys:
            items = []
            for col_key in collection_keys:
                items.extend(zot.collection_items(col_key))
        else:
            items = zot.everything(zot.items())
    except Exception as e:
        return {"error": str(e), "synced": 0, "skipped": 0}

    # Filter to actual papers/books (not attachments/notes)
    skip_types = {"attachment", "note"}
    items = [i for i in items if i.get("data", {}).get("itemType") not in skip_types]

    for item in items:
        key = item.get("key", "")
        version = str(item.get("version", ""))

        if zotero_state.get(key) == version:
            skipped += 1
            continue

        try:
            # Fetch children (notes + attachments)
            child_notes = []
            pdf_attachment = None
            try:
                children = zot.children(key)
                for child in children:
                    child_type = child.get("data", {}).get("itemType")
                    if child_type == "note":
                        note_html = child["data"].get("note", "")
                        note_text = re.sub(r"<[^>]+>", "", note_html).strip()
                        if note_text:
                            child_notes.append(note_text)
                    elif child_type == "attachment" and child.get("data", {}).get("contentType") == "application/pdf":
                        if pdf_attachment is None:
                            pdf_attachment = child
            except Exception:
                pass

            # Strategy: PDF full text (Zotero attachment → arxiv fallback); notes as supplement; abstract as last resort
            md = None
            title = item["data"].get("title", "")

            def _try_pdf(pdf_source: str):
                """Download PDF from url or use Zotero attachment, extract and call LLM."""
                with tempfile.TemporaryDirectory() as tmp:
                    pdf_path = Path(tmp) / "paper.pdf"
                    if pdf_source == "zotero":
                        zot.dump(pdf_attachment["key"], str(pdf_path.name), tmp)
                    else:
                        import urllib.request
                        urllib.request.urlretrieve(pdf_source, pdf_path)
                    if pdf_path.exists() and pdf_path.stat().st_size > 1000:
                        return _pdf_to_md(pdf_path, item, cfg, notes=child_notes)
                return None

            # 1. Try Zotero attachment
            if pdf_attachment:
                try:
                    if verbose:
                        print(f"  [zotero] 📄 reading PDF (zotero): {title[:60]}...")
                    md = _try_pdf("zotero")
                    if md and verbose:
                        print(f"  [zotero] ✓ fulltext (zotero): {title[:60]}")
                except Exception as e:
                    if verbose:
                        print(f"  [zotero] ✗ Zotero PDF failed ({e}), trying arxiv...")

            # 2. Fallback: download from arxiv/URL
            if not md:
                data = item.get("data", {})
                doi = data.get("DOI", "")
                url = data.get("url", "")
                pdf_url = None

                # arxiv DOI pattern: 10.48550/arXiv.XXXX.XXXXX
                if "arxiv" in doi.lower():
                    arxiv_id = doi.split("arXiv.")[-1]
                    pdf_url = f"https://arxiv.org/pdf/{arxiv_id}"
                elif "arxiv.org" in url:
                    # e.g. https://arxiv.org/abs/2301.00001
                    arxiv_id = url.rstrip("/").split("/")[-1]
                    pdf_url = f"https://arxiv.org/pdf/{arxiv_id}"

                if pdf_url:
                    try:
                        if verbose:
                            print(f"  [zotero] 📄 reading PDF (arxiv): {title[:60]}...")
                        md = _try_pdf(pdf_url)
                        if md and verbose:
                            print(f"  [zotero] ✓ fulltext (arxiv): {title[:60]}")
                    except Exception as e:
                        if verbose:
                            print(f"  [zotero] ✗ arxiv PDF failed ({e}), using abstract")

            # 3. Final fallback: abstract + notes
            if not md:
                md = _zotero_item_to_md(item, child_notes)

            title = item.get("data", {}).get("title", key)
            filename = f"zotero-{_slugify(title) or key}.md"
            path = raw_dir / filename

            written = _write_if_changed(path, md)
            if written:
                synced += 1
                if verbose:
                    print(f"  [zotero] ✓ {filename}")
            else:
                skipped += 1

            zotero_state[key] = version
        except Exception as e:
            if verbose:
                print(f"  [zotero] error on {key}: {e}")
            errors += 1

    state["zotero"] = zotero_state
    _save_sync_state(kb_path, state)

    return {"synced": synced, "skipped": skipped, "errors": errors}


# ── main entry ────────────────────────────────────────────────────────────────

def run(kb_path: str, sources: list[str] = None, auto_compile: bool = True,
        verbose: bool = True) -> dict:
    """
    Pull from configured sources into raw/, optionally compile.
    sources: ["notion", "zotero"] or None (all configured)
    """
    from . import config as cfg_mod, compile as compile_mod

    cfg = cfg_mod.load(kb_path)
    results = {}

    do_notion = not sources or "notion" in sources
    do_zotero = not sources or "zotero" in sources

    if do_notion:
        if cfg.get("notion_token"):
            if verbose:
                print("Syncing Notion…")
            results["notion"] = sync_notion(kb_path, cfg, verbose)
        else:
            results["notion"] = {"skipped": 0, "synced": 0, "error": "not configured"}

    if do_zotero:
        if cfg.get("zotero_api_key"):
            if verbose:
                print("Syncing Zotero…")
            results["zotero"] = sync_zotero(kb_path, cfg, verbose)
        else:
            results["zotero"] = {"skipped": 0, "synced": 0, "error": "not configured"}

    total_synced = sum(r.get("synced", 0) for r in results.values())

    if auto_compile and total_synced > 0:
        if verbose:
            print(f"\n{total_synced} new/updated files → compiling…")
        compile_result = compile_mod.run(kb_path, verbose=verbose)
        results["compile"] = compile_result
    elif auto_compile and verbose:
        print("Nothing new to compile.")

    return results
