# Ingest Workflow — Per-Type Instructions

## Overview

Ingest takes a user-provided input (URL, file, or oral knowledge) and produces a clean markdown file in `raw/`. The preprocessing scripts handle format conversion; the LLM handles content structuring.

## Common Frontmatter

Every file saved to `raw/` must have this frontmatter:

```yaml
---
title: "<descriptive title>"
source: "<original URL or file path>"
ingested: "<YYYY-MM-DD>"
visibility: private
type: "<paper|blog|webpage|note|experience>"
---
```

## Type 1: ArXiv URL

Detection: URL contains `arxiv.org`

Steps:
1. Extract paper ID from URL (e.g., `2301.12345`)
2. Run: `Bash: python3 <skill-dir>/scripts/pdf_to_md.py "https://arxiv.org/pdf/<id>.pdf" raw/<slug>.md`
3. The script downloads the PDF and converts to raw markdown text
4. Read the raw output
5. Restructure into clean markdown:
   - Add frontmatter with title, authors, source URL
   - Clean up conversion artifacts (broken tables, garbled math, header/footer noise)
   - Preserve section structure (Abstract, Introduction, Method, Results, etc.)
   - Convert inline math notation to readable form where possible
6. Write final version to `raw/<slug>.md`

Naming: use `arxiv-<id>` as slug (e.g., `arxiv-2301.12345.md`)

## Type 2: Blog URL

Detection: URL is not arxiv, not PDF, appears to be an article/blog post

Steps:
1. Run: `Bash: python3 <skill-dir>/scripts/web_clip.py "<url>" raw/<slug>.md`
2. The script extracts main content via trafilatura
3. Read the raw output
4. Restructure:
   - Add frontmatter with title, source URL
   - Clean up extraction artifacts
   - Preserve code blocks, lists, headers
   - Remove navigation, ads, boilerplate that leaked through
5. Write final version to `raw/<slug>.md`

Naming: derive slug from URL path or page title, lowercase-hyphenated

## Type 3: General Webpage URL

Detection: URL that doesn't fit blog or arxiv patterns

Steps: Same as blog, but be more aggressive about extracting only the relevant content section. Webpages may have complex layouts — focus on the main content area.

## Type 4: Local PDF

Detection: file path ending in `.pdf`

Steps:
1. Run: `Bash: python3 <skill-dir>/scripts/pdf_to_md.py "<path>" raw/<slug>.md`
2. Read raw output
3. Restructure (same as arxiv)
4. Write to `raw/<slug>.md`

Naming: derive slug from PDF filename

## Type 5: Local Markdown

Detection: file path ending in `.md`

Steps:
1. Read the file
2. If it already has frontmatter, preserve it and add missing fields
3. If no frontmatter, add it
4. Copy to `raw/<slug>.md` (or move if user confirms)

Naming: use original filename as slug

## Type 6: Personal Experience / Oral Knowledge

Detection: user provides free-text knowledge, anecdotes, or asks to "write down" something

Steps:
1. Ask clarifying questions if the input is vague
2. Structure the knowledge into clean markdown with:
   - Descriptive title
   - Context section (when, where, why this knowledge was acquired)
   - Key insights or lessons
   - Related topics
3. Add frontmatter with `type: experience`
4. Write to `raw/<slug>.md`

Naming: derive from topic, e.g., `experience-debugging-cuda-oom.md`

## Post-Ingest

After any ingest:
1. Confirm the file was saved to `raw/`
2. Ask user if they want to compile immediately (`/shj compile`) or batch later
3. Ask if visibility should be `public` instead of the default `private`

## Script Directory Resolution

The scripts live in the skill's `scripts/` directory. To find the skill directory:
1. The skill knows its own path from the SKILL.md location
2. Scripts are at `<skill-dir>/scripts/web_clip.py` and `<skill-dir>/scripts/pdf_to_md.py`
3. Before first use, check if dependencies are installed: `Bash: pip3 list 2>/dev/null | grep -i trafilatura`
4. If not installed: `Bash: pip3 install -r <skill-dir>/scripts/requirements.txt`
