<div align="center">
  <img src="logo.svg" width="120" alt="山海经">

  # 山海经 Shanhaijing

  联邦知识网络。编译个人知识库，公开分享，发现和查询他人的知识和经验。

  ![License](https://img.shields.io/badge/license-MIT-gray?style=flat-square)
  ![Python](https://img.shields.io/badge/python-3.11+-blue?style=flat-square)
  ![Phase](https://img.shields.io/badge/phase-1%20core-brightgreen?style=flat-square)
</div>

---

## 愿景

每个人的大脑都不一样。你的阅读、工作经验、研究成果、人生教训都是独特的知识。但它们被困在你的脑子里。

**山海经**是一套系统，让你能够：
1. **提取**你的知识——从论文、博客、笔记、个人经验转换成结构化内容
2. **编译**成可查询的 wiki——包括摘要、概念、交叉引用
3. **公开分享**——或者保持私密——在一个去中心化的注册表里
4. **发现**和**查询**他人的知识——就像查询自己大脑里的东西一样

想象一下能搜索几千个人的大脑——提一个问题，得到由全球集体经验支撑的答案。

## 怎样工作

### Phase 1: 个人知识库（当前）

```
你的原始文档               你的结构化 wiki
  论文.md         →          _index.md（可搜索）
  博客.md         →          summaries/（每篇文档）
  笔记.md         →          concepts/（自动提取）
  zotero 同步     →          raw/zotero-*.md
  notion 同步     →          raw/notion-*.md
```

**四种喂入知识库的方式：**

1. **直接放文件** — 把任意 `.md` 拷进 `raw/` 然后编译
2. **蒸馏** — 把一个想法、一句话、一段碎片直接结构化进 wiki
3. **同步 Notion** — 拉取你 Notion 工作区的页面和数据库
4. **同步 Zotero** — 拉取论文 + 笔记（无笔记的条目自动读取 PDF 全文）

**三种使用方式：**

1. **CLI 模式**（无需 Claude Code）
   ```bash
   uv run main.py compile ./myknowledge
   uv run main.py query "什么是注意力机制？"
   uv run main.py distill "注意力和记忆检索本质上是一回事" --kb ./myknowledge
   uv run main.py sync --kb ./myknowledge
   ```

2. **Claude Code skill**（`/shj` 命令）
   ```
   /shj compile ./myknowledge
   /shj query "什么是注意力机制？"
   ```

3. **Web UI**（流式、模型配置、知识图谱）
   ```bash
   uv run web/server.py --kb ./myknowledge
   # 打开 http://127.0.0.1:8000
   ```

### Phase 2: 公开注册表 + 分享（短期）

- 标记文章为"公开"或"私密"
- 发布你的 wiki 为静态网站
- 在中央索引中注册你的 wiki
- 一次查询多个 wiki

### Phase 3: 联邦查询网络（长期）

- 搜索所有注册表里的公开 wiki
- 回答可以从任何人的 wiki 中拉取知识
- 你的概念被链接，可追溯来源
- 分布式，没有中央权力

## 安装和快速开始

```bash
git clone https://github.com/cslsolow/shanhaijing.git
cd shanhaijing
uv sync

# 配置 API（Anthropic 或任何 OpenAI-compatible）
export OPENAI_API_KEY=sk-...

# 初始化知识库
uv run main.py init ./myknowledge

# 导入文档
cp ./my-research-notes.md ./myknowledge/raw/

# 编译成 wiki
uv run main.py compile ./myknowledge

# 查询
uv run main.py query "我关于 transformer 学了什么？" --kb ./myknowledge
```

## 功能特性

### 编译

- **增量处理**：SHA-256 哈希跟踪变化，只重编译变更部分
- **自动摘要**：LLM 为每篇文档生成 150-400 字的摘要
- **概念提取**：自动从文档中发现 2-8 个核心概念
- **语义概念合并**：LLM 跨文档去重概念——`"transformer model"` 会合并进 `"transformer"` 而不是创建重复条目
- **交叉引用**：生成带 `[[wikilinks]]` 的概念文章
- **状态追踪**：`.wiki_state.json` 支持断点续传

### 蒸馏

把任意碎片输入一条命令变成结构化知识条目：

```bash
uv run main.py distill "注意力和记忆检索本质上是一回事" --kb ./myknowledge
```

LLM 把它结构化成带标题、带链接的 wiki 条目，并自动连接到已有概念。

### 同步

从外部来源自动拉取到 `raw/`：

```bash
uv run main.py sync --kb ./myknowledge          # 所有已配置来源
uv run main.py sync --source zotero --kb ./myknowledge
uv run main.py sync --source notion --kb ./myknowledge
```

**Zotero 同步策略**：
- 有笔记的条目 → abstract + 笔记 → markdown
- 无笔记 + 有 PDF 附件 → LLM 读取 PDF 全文 → 结构化 markdown
- 无笔记 + 无 PDF → 仅 abstract

**Notion 同步**：页面和数据库，增量（跳过未变更页面）。

在 `.shj.config.json` 中配置：
```json
{
  "zotero_api_key": "...",
  "zotero_user_id": "...",
  "notion_token": "...",
  "notion_databases": ["db-id-1"]
}
```

### 查询

- **轻量级检索**：LLM 只读摘要索引（~10K tokens）
- **选择性阅读**：根据需要拉取 3-7 篇相关全文
- **引用追踪**：回答包含 `[[wikilink]]` 指向源文章
- **流式输出**：实时 token 传输

### 私人知识库

把个人想法、科研方向、假设、开放问题放进 `private/`——自由格式的 markdown，没有固定结构：

```
myknowledge/
├── raw/          # 原始文档 → 编译进 wiki
├── private/      # 你的私人想法 → 作为背景知识加载
│   ├── 科研方向.md
│   └── 开放问题.md
└── wiki/         # _index.md 同时列出 wiki 文章和 private 路径
```

`private/` 永远不会被 LLM 编译。但在查询时，`private/` 下的所有文件会作为背景知识加载——回答时 LLM 已了解你的研究背景，给出的建议更贴合你的方向。

### 知识图谱

在 Web UI 中打开 `/graph`，把你的 wiki 以交互式力导向图展示——节点是摘要和概念，边是 `[[wikilinks]]`。

### 模型灵活性

| Provider | API Key 环境变量 | 说明 |
|----------|----------------|------|
| **Anthropic** | `ANTHROPIC_API_KEY` | 默认：claude-haiku-4-5 |
| **OpenAI** | `OPENAI_API_KEY` | gpt-4o、gpt-4 turbo 等 |
| **Ollama**（本地） | 不需要 | `base_url=http://localhost:11434/v1` |
| **DeepSeek** | `OPENAI_API_KEY` | 支持私有端点 |

通过 CLI 或 Web UI 设置面板配置。配置文件（`.shj.config.json`）被 git 忽略。

## raw 目录

`raw/` 是输入层——你读过的、写过的、想过的所有东西。这里的文件是真正的原始资料，`wiki/` 永远可以从 `raw/` 重新生成。

每个文件的 frontmatter 里应该有 `source_url` 指向原文（DOI、URL、Notion 链接等）。没有外部来源的文件（如蒸馏的想法）本身就是原文。

## 输出格式

标准 markdown + `[[wikilinks]]`——完全兼容 Obsidian。把 `wiki/` 目录作为 vault 打开，可以：
- 可视化概念图
- 反向链接导航
- 全文搜索
- 在编译内容旁边直接记笔记

## 示例

`examples/` 包含一个从研究论文编译出的示例知识库。查询它：

```bash
uv run main.py query "什么是 agent-computer interface？" --kb ./examples
```

## 项目哲学

- **不用向量数据库，不用 RAG**：LLM 直读索引——更简单、更便宜、更透明
- **增量式**：只重新处理变更的文件
- **Obsidian 原生**：打开 `wiki/` 目录作为 vault 开箱即用
- **去中心化**：每个人拥有自己的知识库；分享是可选的
- **可迁移**：markdown 到处都是——没有锁定
- **你的知识，不是论文的镜像**：`raw/` 应该反映你的理解——笔记、批注、蒸馏的想法——而不只是原文复制

## 路线图

| Phase | 重点 | 预期 |
|-------|------|------|
| **1** | 核心编译/查询 + 同步（Notion/Zotero）+ 蒸馏 | ✅ 完成 |
| **2** | 公开/私密分离、发布命令、静态站点导出 | 2026 Q2 |
| **3** | 联邦注册表、跨库查询、全局发现 | 2026 Q3+ |

## 未来：联邦知识网络

```
你的 Wiki         Alice 的 Wiki      Bob 的 Wiki
 （公开）          （公开）          （公开）
    ↓               ↓                 ↓
  [中央注册表] ← 自动注册
    ↓
  [全局查询]
  "什么是自注意力？"
    ↓
  返回来自三个 wiki 的答案，带引用
```

## 命名

山海经——古代中国的万物知识图谱。这个项目是现代、协作的人类知识百科全书，由大模型编译，由所有人共同拥有。

## License

MIT

---

**从你自己的知识开始。到达全世界的知识。**
