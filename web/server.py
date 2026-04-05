#!/usr/bin/env python3
"""Shanhaijing Web Server - query your knowledge base from the browser."""

import argparse
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from shanhaijing.config import load as load_config, save as save_config, masked as mask_config
from shanhaijing.query import stream as _stream_query
from shanhaijing.distill import run as run_distill
from shanhaijing.sync import run as run_sync

def stream_query(kb_path, question, model=""):
    return _stream_query(kb_path, question, model)

try:
    from flask import Flask, request, jsonify, send_file, Response, stream_with_context
except ImportError:
    print("Flask not installed. Run: uv sync")
    raise SystemExit(1)

app = Flask(__name__)
KB_PATH = "."


@app.route("/")
def index():
    return send_file(Path(__file__).parent / "index.html")


@app.route("/api/index")
def wiki_index():
    p = Path(KB_PATH) / "wiki" / "_index.md"
    if not p.exists():
        return jsonify({"error": "wiki/_index.md not found. Run /shj compile first."}), 404
    return jsonify({"content": p.read_text(encoding="utf-8")})


@app.route("/api/articles")
def list_articles():
    wiki = Path(KB_PATH) / "wiki"
    if not wiki.exists():
        return jsonify({"articles": []})

    def parse_title(path):
        try:
            text = path.read_text(encoding="utf-8")
            if text.startswith("---"):
                end = text.find("\n---", 3)
                if end != -1:
                    for line in text[3:end].splitlines():
                        if line.startswith("title:"):
                            return line.split(":", 1)[1].strip().strip('"')
        except Exception:
            pass
        return path.stem

    articles = []
    for md in sorted(wiki.rglob("*.md")):
        rel = md.relative_to(wiki)
        if rel.name.startswith("_"):
            continue
        articles.append({
            "path": str(rel),
            "name": parse_title(md),
            "category": rel.parts[0] if len(rel.parts) > 1 else "root",
        })
    return jsonify({"articles": articles})


@app.route("/api/article")
def get_article():
    path = request.args.get("path", "")
    if not path or ".." in path:
        return jsonify({"error": "invalid path"}), 400
    p = Path(KB_PATH) / "wiki" / path
    if not p.exists():
        return jsonify({"error": "not found"}), 404
    return jsonify({"content": p.read_text(encoding="utf-8"), "path": path})


@app.route("/api/config", methods=["GET"])
def get_config():
    return jsonify(mask_config(load_config(KB_PATH)))


@app.route("/api/config", methods=["POST"])
def set_config():
    data = request.get_json(force=True)
    current = load_config(KB_PATH)
    # empty api_key in request = keep existing
    if not data.get("api_key"):
        data["api_key"] = current.get("api_key", "")
    current.update(data)
    save_config(KB_PATH, current)
    return jsonify({"ok": True})


@app.route("/api/sync", methods=["POST"])
def sync():
    data = request.get_json(force=True) or {}
    source = data.get("source")  # "notion" | "zotero" | None (all)
    auto_compile = data.get("auto_compile", True)
    sources = [source] if source else None
    try:
        result = run_sync(KB_PATH, sources=sources, auto_compile=auto_compile, verbose=False)
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/distill", methods=["POST"])
def distill():
    data = request.get_json(force=True)
    text = data.get("input", "").strip()
    auto_compile = data.get("auto_compile", True)
    if not text:
        return jsonify({"error": "empty input"}), 400
    try:
        result = run_distill(KB_PATH, text, auto_compile=auto_compile)
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/graph")
def graph_page():
    return send_file(Path(__file__).parent / "graph.html")


@app.route("/api/graph")
def graph_data():
    wiki = Path(KB_PATH) / "wiki"
    if not wiki.exists():
        return jsonify({"nodes": [], "links": []})

    import re
    nodes = {}
    links = []

    def parse_frontmatter(text):
        if not text.startswith("---"):
            return {}
        end = text.find("\n---", 3)
        if end == -1:
            return {}
        fm = {}
        for line in text[3:end].splitlines():
            if ":" in line:
                k, _, v = line.partition(":")
                fm[k.strip()] = v.strip().strip('"')
        return fm

    # Build node registry from actual wiki files (with correct category)
    slug_to_category = {}
    for md in wiki.rglob("*.md"):
        rel = md.relative_to(wiki)
        if rel.name.startswith("_"):
            continue
        category = rel.parts[0] if len(rel.parts) > 1 else "root"
        slug_to_category[rel.stem] = category

    def add_node(slug, fallback_cat, title=None, desc=None):
        if slug not in nodes:
            category = slug_to_category.get(slug, fallback_cat)
            nodes[slug] = {"id": slug, "category": category,
                           "title": title or slug, "desc": desc or ""}

    seen_links = set()
    # Known placeholder wikilinks to skip
    skip_slugs = {"article-name", "wikilink", "concept-name"}

    for md in wiki.rglob("*.md"):
        rel = md.relative_to(wiki)
        if rel.name.startswith("_"):
            continue
        text = md.read_text(encoding="utf-8")
        fm = parse_frontmatter(text)
        slug = rel.stem
        category = rel.parts[0] if len(rel.parts) > 1 else "root"
        add_node(slug, category,
                 title=fm.get("title", slug),
                 desc=fm.get("desc", ""))

        for target_raw in re.findall(r"\[\[([^\]]+)\]\]", text):
            target_slug = target_raw.split("/")[-1].strip("`")
            if target_slug == slug or target_slug in skip_slugs:
                continue
            # Only link to nodes that exist in the wiki
            if target_slug not in slug_to_category:
                continue
            add_node(target_slug, "concepts")
            key = tuple(sorted([slug, target_slug]))
            if key not in seen_links:
                seen_links.add(key)
                links.append({"source": slug, "target": target_slug})

    return jsonify({"nodes": list(nodes.values()), "links": links})


@app.route("/api/query", methods=["POST"])
def query():
    data = request.get_json(force=True)
    question = data.get("question", "").strip()
    model = data.get("model", "").strip()
    if not question:
        return jsonify({"error": "empty question"}), 400

    @stream_with_context
    def generate():
        try:
            for event in stream_query(KB_PATH, question, model):
                yield f"data: {json.dumps(event)}\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'error': str(e)})}\n\n"
            yield 'data: {"done": true}\n\n'

    return Response(generate(), mimetype="text/event-stream",
                    headers={"X-Accel-Buffering": "no", "Cache-Control": "no-cache"})


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Shanhaijing Web UI")
    parser.add_argument("--kb", default=".", help="knowledge base directory (default: cwd)")
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument("--host", default="127.0.0.1")
    args = parser.parse_args()

    KB_PATH = os.path.abspath(args.kb)
    print(f"Knowledge base: {KB_PATH}")
    print(f"Config:         {KB_PATH}/.shj.config.json")
    print(f"Server:         http://{args.host}:{args.port}")
    app.run(host=args.host, port=args.port, debug=True, threaded=True)
