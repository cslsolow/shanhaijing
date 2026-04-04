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

    args = parser.parse_args()
    {
        "init": cmd_init,
        "compile": cmd_compile,
        "query": cmd_query,
        "lint": cmd_lint,
        "config": cmd_config,
    }[args.command](args)


if __name__ == "__main__":
    main()
