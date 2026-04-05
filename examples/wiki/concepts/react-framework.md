---
title: ReAct Framework
visibility: private
type: concept
desc: LM agent 的经典交互范式：每步生成 **Reasoning**（思考）+ **Acting**（动作），接收执行结果后进入下一步。将推理过程显式化，使 agent 能根据环境反馈动态调整策略。SWE-agent 基于 ReAct 构建，每步 agent 输出 thought + command，接收终端反馈
sources: [summaries/2405.15793v3]
---

# ReAct Framework

LM agent 的经典交互范式：每步生成 **Reasoning**（思考）+ **Acting**（动作），接收执行结果后进入下一步。将推理过程显式化，使 agent 能根据环境反馈动态调整策略。SWE-agent 基于 ReAct 构建，每步 agent 输出 thought + command，接收终端反馈。

## Sources

- [[summaries/2405.15793v3]]

## Related Concepts

[[lm-agent]] [[agent-computer-interface]]
