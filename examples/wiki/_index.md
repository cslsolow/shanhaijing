# Wiki Index

compiled: 2026-04-04  |  summaries: 2  |  concepts: 10

## Summaries

- [SWE-agent: Agent-Computer Interfaces Enable Automated Software Engineering](summaries/2405.15793v3.md) — Proposes ACI concept; SWE-agent achieves 12.47% pass@1 on SWE-bench with GPT-4 Turbo.  `paper  |  raw/2405.15793v3.pdf`
- [Shanhaijing — LLM-compiled Personal Knowledge Base](summaries/README.md) — LLM-compiled PKB with incremental compile, no vector DB, Obsidian-compatible wikilinks.  `note  |  raw/README.md`

## Concepts

- [ACI Design Principles](concepts/aci-design-principles.md) — SWE-agent 论文总结的四条 agent 接口设计原则：  `src:[summaries/2405.15793v3]`
- [Agent-Computer Interface (ACI)](concepts/agent-computer-interface.md) — LM agent 与计算机之间的抽象层，定义 agent 可用的命令集、命令文档，以及环境状态如何反馈给 agent。类比于人类使用 IDE（VSCode…  `src:[summaries/2405.15793v3]`
- [Incremental Compile](concepts/incremental-compile.md) — A compilation strategy where only new or changed files are processed. Files a…  `src:[summaries/README]`
- [LLM-Compiled Wiki](concepts/llm-compiled-wiki.md) — A knowledge base architecture where an LLM acts as the compiler: it reads raw…  `src:[summaries/README]`
- [LM Agent](concepts/lm-agent.md) — 以语言模型为核心的自主决策系统，通过迭代执行动作、接收环境反馈来完成复杂任务（ReAct 框架）。LM agent 有别于单次推理的 LM：它维护历史状态…  `src:[summaries/2405.15793v3]`
- [Personal Knowledge Base](concepts/personal-knowledge-base.md) — A structured collection of notes, summaries, and concepts owned by one person…  `src:[summaries/README]`
- [ReAct Framework](concepts/react-framework.md) — LM agent 的经典交互范式：每步生成 **Reasoning**（思考）+ **Acting**（动作），接收执行结果后进入下一步。将推理过程显式化…  `src:[summaries/2405.15793v3]`
- [Software Engineering Automation](concepts/software-engineering-automation.md) — 用 LM agent 自动完成软件工程任务，包括 bug 定位、代码修改、测试执行。挑战在于真实代码仓库规模大、任务需要多步推理、错误代价高。SWE-ag…  `src:[summaries/2405.15793v3]`
- [SWE-bench](concepts/swe-bench.md) — 评测 LM agent 解决真实软件工程任务能力的基准。任务来自真实 GitHub issue，要求 agent 在代码仓库中定位并修复 bug，通过对应…  `src:[summaries/2405.15793v3]`
- [Wikilinks](concepts/wikilinks.md) — A link format (`[[article-name]]`) popularized by Obsidian and other plain-te…  `src:[summaries/README]`
