# Knowledge Base Index

Last compiled: 2026-04-03
Articles: 2 summaries, 10 concepts

## Summaries

- [README](summaries/README.md) — Shanhaijing skill overview: LLM-compiled personal knowledge base with incremental compile, no vector DB, Obsidian-compatible wikilink output.
- [2405.15793v3](summaries/2405.15793v3.md) — SWE-agent (NeurIPS 2024): proposes Agent-Computer Interface (ACI) concept, achieves 12.47% pass@1 on SWE-bench with GPT-4 Turbo via LM-tailored interface design.

## Concepts

- [llm-compiled-wiki](concepts/llm-compiled-wiki.md) — Architecture where an LLM acts as compiler, reading raw docs and outputting structured summaries and concept articles without embeddings or vector DBs.
- [incremental-compile](concepts/incremental-compile.md) — Compile strategy using SHA-256 hashes to process only new/changed files, keeping compile time proportional to change volume.
- [wikilinks](concepts/wikilinks.md) — [[article-name]] link format connecting summaries to concepts, forming a knowledge graph navigable by humans and LLMs.
- [personal-knowledge-base](concepts/personal-knowledge-base.md) — Structured personal collection of notes and concepts compiled automatically from raw URLs, PDFs, and notes.
- [agent-computer-interface](concepts/agent-computer-interface.md) — Abstraction layer between LM agent and computer defining available commands and feedback format; LM agents are a new category of end user requiring purpose-built interfaces.
- [aci-design-principles](concepts/aci-design-principles.md) — Four principles for effective ACI design: simple commands, compact actions, concise feedback, and guardrails for error recovery.
- [swe-bench](concepts/swe-bench.md) — Benchmark for LM agents solving real GitHub issues in code repositories; SWE-agent achieved 12.47% pass@1 at time of publication.
- [lm-agent](concepts/lm-agent.md) — LM-based autonomous system that iteratively takes actions and receives environment feedback (ReAct) to complete complex multi-step tasks.
- [software-engineering-automation](concepts/software-engineering-automation.md) — Using LM agents to autonomously locate bugs, edit code, and run tests in real repositories without modifying model weights.
- [react-framework](concepts/react-framework.md) — Agent interaction paradigm combining Reasoning and Acting: each step outputs thought + command, receives execution feedback, iterates toward goal.
