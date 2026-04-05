#!/usr/bin/env python3
"""
Shanhaijing CLI — LLM-compiled personal knowledge base.

Commands:
  init    [path]                  Create directory scaffold
  compile [path]                  Process new/changed raw docs into wiki
  query   "question" [--model M]  Answer question from wiki
  lint    [path]                  Health check: broken links, orphans, gaps
  config  [path]                  Show or set model config

API key via env: ANTHROPIC_API_KEY or OPENAI_API_KEY
Config file: <kb>/.shj.config.json
"""

import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))


def cmd_init(args):
    from shanhaijing import init_cmd, compile
    kb = os.path.abspath(args.path or ".")
    init_cmd.run(kb)
    # Auto-compile if raw/ has .md files
    raw = os.path.join(kb, "raw")
    if os.path.isdir(raw) and any(f.endswith(".md") for f in os.listdir(raw)):
        print("raw/ has content — compiling…")
        compile.run(kb)


def cmd_compile(args):
    from shanhaijing import compile
    kb = os.path.abspath(args.path or ".")
    compile.run(kb)


def cmd_query(args):
    from shanhaijing import query
    kb = os.path.abspath(args.kb or ".")
    for event in query.stream(kb, args.question, args.model or ""):
        if "chunk" in event:
            print(event["chunk"], end="", flush=True)
        elif "error" in event:
            print(f"\nError: {event['error']}", file=sys.stderr)
            sys.exit(1)
    print()


def cmd_lint(args):
    from shanhaijing import lint
    kb = os.path.abspath(args.path or ".")
    issues = lint.run(kb)
    if not issues:
        print("No issues found.")
        return
    by_type = {}
    for issue in issues:
        by_type.setdefault(issue["type"], []).append(issue)
    for t, items in by_type.items():
        print(f"\n## {t.replace('_', ' ').title()} ({len(items)})")
        for item in items:
            detail = " ".join(f"{k}={v}" for k, v in item.items() if k != "type")
            print(f"  - {detail}")


def cmd_config(args):
    import json
    from shanhaijing import config
    kb = os.path.abspath(args.path or ".")
    if args.set:
        cfg = config.load(kb)
        for pair in args.set:
            k, _, v = pair.partition("=")
            cfg[k.strip()] = v.strip()
        config.save(kb, cfg)
        print("Config saved.")
    else:
        print(json.dumps(config.load(kb), indent=2))



def cmd_sync(args):
    from shanhaijing import sync
    kb = os.path.abspath(args.kb or ".")
    sources = [args.source] if getattr(args, "source", None) else None
    results = sync.run(kb, sources=sources, auto_compile=not args.no_compile)
    for src, r in results.items():
        if src == "compile":
            print(f"compile: {r.get('new',0)} new, {r.get('changed',0)} changed")
        elif "error" in r and r["error"] and not r.get("synced"):
            print(f"{src}: {r['error']}")
        else:
            print(f"{src}: {r.get('synced',0)} synced, {r.get('skipped',0)} skipped"
                  + (f", {r['errors']} errors" if r.get("errors") else ""))


def cmd_distill(args):
    from shanhaijing import distill
    kb = os.path.abspath(args.kb or ".")
    text = args.text
    if not text:
        print("Enter text (Ctrl+D to finish):")
        text = sys.stdin.read().strip()
    if not text:
        print("No input.", file=sys.stderr)
        sys.exit(1)
    result = distill.run(kb, text, auto_compile=not args.no_compile)
    print(f"Distilled: {result['title']}")
    print(f"File: {result['file']}")
    if result['compiled']:
        print("Auto-compiled into wiki.")


def main():
    parser = argparse.ArgumentParser(
        prog="shj",
        description="Shanhaijing — LLM-compiled personal knowledge base",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    p_init = sub.add_parser("init", help="Create kb scaffold")
    p_init.add_argument("path", nargs="?", default="")

    p_compile = sub.add_parser("compile", help="Compile raw docs into wiki")
    p_compile.add_argument("path", nargs="?", default="")

    p_query = sub.add_parser("query", help="Answer a question from the wiki")
    p_query.add_argument("question")
    p_query.add_argument("--model", default="")
    p_query.add_argument("--kb", default="")

    p_lint = sub.add_parser("lint", help="Health check")
    p_lint.add_argument("path", nargs="?", default="")

    p_cfg = sub.add_parser("config", help="Show or set model config")
    p_cfg.add_argument("path", nargs="?", default="")
    p_cfg.add_argument("--set", nargs="*", metavar="key=value",
                       help="e.g. --set provider=openai model=gpt-4o")

    p_distill = sub.add_parser("distill", help="Structure a fragment into knowledge")
    p_distill.add_argument("text", nargs="?", default="")
    p_distill.add_argument("--kb", default="")
    p_distill.add_argument("--no-compile", action="store_true",
                           help="Skip auto-compile after distilling")

    # sync subparser
    p_sync = sub.add_parser("sync", help="Pull from Notion/Zotero into raw/ and compile")
    p_sync.add_argument("--kb", default="", help="Knowledge base path")
    p_sync.add_argument("--source", choices=["notion", "zotero"],
                        help="Sync only one source (default: all configured)")
    p_sync.add_argument("--no-compile", action="store_true",
                        help="Skip compile after sync")
    p_sync.set_defaults(command="sync")

    args = parser.parse_args()
    {
        "init": cmd_init,
        "compile": cmd_compile,
        "query": cmd_query,
        "lint": cmd_lint,
        "config": cmd_config,
        "distill": cmd_distill,
        "sync": cmd_sync,
    }[args.command](args)


if __name__ == "__main__":
    main()
