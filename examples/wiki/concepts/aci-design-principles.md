---
title: ACI Design Principles
visibility: private
type: concept
desc: SWE-agent 论文总结的四条 agent 接口设计原则：
sources: [summaries/2405.15793v3]
---

# ACI Design Principles

SWE-agent 论文总结的四条 agent 接口设计原则：

1. **简单易用**：命令选项少，文档简洁，agent 无需 few-shot 示例即可使用
2. **紧凑高效**：单条命令覆盖高阶操作，减少多轮交互完成一个任务
3. **反馈精炼**：环境反馈信息密度高但不冗余，避免无关上下文干扰 agent
4. **Guardrail 防护**：内置错误检测（如语法检查）帮助 agent 快速识别并恢复错误

这些原则来源于对 agent 行为的人工检查 + grid search 实验，与 HCI 领域的用户研究方法类似。

## Sources

- [[summaries/2405.15793v3]]

## Related Concepts

[[agent-computer-interface]] [[lm-agent]]
