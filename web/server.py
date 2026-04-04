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
    articles = []
    for md in sorted(wiki.rglob("*.md")):
        rel = md.relative_to(wiki)
        if rel.name.startswith("_"):
            continue
        articles.append({
            "path": str(rel),
            "name": rel.stem,
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
