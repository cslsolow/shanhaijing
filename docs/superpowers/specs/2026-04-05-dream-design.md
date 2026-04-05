# Dream 功能设计文档

**日期**: 2026-04-05  
**状态**: 待实现（Phase X）

---

## 概述

Dream 是一个定时自动运行的创意功能：每天深夜从知识库中随机选取高摩擦概念组合，以随机叙事角度生成多轮演化的「梦境文章」，发现人类不容易注意到的跨概念隐藏连接。

---

## 执行模式

**模式：CLI（Python 后台执行）**

```bash
uv run main.py dream ./kb              # 立即触发一次
uv run main.py dream ./kb --schedule   # 注册系统 cron，默认 23:00 本地时间
uv run main.py dream ./kb --unschedule # 取消 cron
```

`/shj dream` 是 Claude Code skill 快捷方式，内部执行 `uv run main.py dream ./kb`。

定时和多轮 sleep 由 Python 进程处理，不依赖 Claude Code session。

---

## 执行流程

### 1. 概念选取（摩擦度优先）

- 扫描 `wiki/concepts/` 所有概念文章
- 计算**摩擦度**：两个概念在所有 summaries 里共现次数越少 = 摩擦度越高
- 优先选高摩擦概念对，共选 5-10 个
- 按概念来源论文/文章的发布时间排序（从 frontmatter `ingested` 或 DOI 年份提取）

### 2. 角度选取

从角度池随机选一个：

| slug | 描述 |
|------|------|
| `contrarian` | 找出知识库里最确信的结论，然后反驳它 |
| `analogy` | 把两个不同领域概念强行类比，找荒谬但成立的共同点 |
| `hypothesis` | 提出 3 个知识库里隐含但未被明说的假设 |
| `genealogy` | 追溯概念思想来源，编一段虚构但合理的思想史 |
| `critique` | 以不同学派视角批判知识库的主流观点 |

### 3. 多轮演化

- **第一轮**：只用第一个概念 + 角度生成初始梦境
- **等待**：sleep 30-60min（可在 config 配置，默认 45min）
- **后续轮**：加入下一个概念，LLM 改写上一版：
  - 时间轴叙事：概念按发布时间排序，梦境像思想演化史
  - 梦境衰减：每轮随机「遗忘」前一轮 1-2 个论点，记录在 frontmatter
  - 新概念扭曲已有论点，可能面目全非
- 重复直到所有概念用完

### 4. Token 预算

每轮上限 30K tokens（可配）：
- 概念文章 5-10 篇 ≈ 5-10K
- 关联 summaries 5-10 篇 ≈ 10-15K
- system prompt + output ≈ 5K
- 超出预算时自动减少 summaries 数量

---

## 输出结构

```
dream/
└── 2026-04-06/
    ├── v1-attention-mechanism.md   # 初始梦境
    ├── v2-+memory.md               # 加入 memory 后的扭曲版
    ├── v3-+transformer.md          # 再被 transformer 扭曲
    └── final.md                    # 最终版 + 演化注记
```

每篇文章 frontmatter：

```yaml
---
date: 2026-04-06
round: 2
angle: contrarian
seed: 8a3f
concepts_so_far: [attention-mechanism, memory]
concept_added: memory
forgotten: ["注意力是计算瓶颈"]
---
```

`final.md` 额外包含演化注记：每轮加入了什么概念、推翻了什么论点。

---

## Config 参数

在 `.shj.config.json` 中可配：

```json
{
  "dream_schedule": "0 23 * * *",
  "dream_interval_min": 45,
  "dream_token_budget": 30000,
  "dream_concepts_count": 7
}
```

---

## 实现模块

- `shanhaijing/dream.py` — 主逻辑（摩擦度计算、角度选取、多轮生成、cron 注册）
- `main.py` — 新增 `dream` 子命令
- `skill/SKILL.md` — 新增 `/shj dream` 条目

---

## 非目标

- Dream 文章不自动进入 `raw/` 触发 compile（用户可手动移入）
- 不做跨 KB 的 dream（只用当前 KB）
