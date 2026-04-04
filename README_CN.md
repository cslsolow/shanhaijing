<div align="center">
  <img src="logo.svg" width="120" alt="山海经">

  # 山海经 Shanhaijing

  用大模型把你读过的一切蒸馏成结构化的个人知识库。导入原始文档，编译成 markdown wiki，用自然语言检索记忆。

  ![License](https://img.shields.io/badge/license-MIT-gray?style=flat-square)
  ![Python](https://img.shields.io/badge/python-3.11+-blue?style=flat-square)
  ![Phase](https://img.shields.io/badge/phase-1%20core-brightgreen?style=flat-square)
</div>

---

## 做什么

```
raw/                        wiki/
  论文.md            →         _index.md          (总索引)
  博客.md            →         summaries/         (每篇文档的摘要)
  个人经验.md         →         concepts/          (自动提取的概念文章)
```

- **导入 (ingest)**：喂入 URL（博客、arxiv）、PDF、markdown 或个人经验。大模型负责理解内容并转换为结构化 markdown。
- **编译 (compile)**：增量构建 wiki——摘要、概念文章、交叉引用 (`[[wikilinks]]`)、总索引。只处理变更部分。
- **查询 (query)**：提问。大模型读索引、拉取相关文章、合成带引用的回答，流式输出。
- **检查 (lint)**：健康检查——断链、孤儿文章、过期摘要、概念缺口。

不用向量数据库，不用 RAG。大模型直读 `_index.md`，500 篇以内够用。

## 安装

需要 [uv](https://docs.astral.sh/uv/)。

```bash
git clone https://github.com/cslsolow/shanhaijing.git
cd shanhaijing
uv sync
```

同时作为 Claude Code skill 使用：

```bash
ln -s $(pwd)/skill ~/.claude/skills/shanhaijing
```

## 使用

### 直接 CLI 模式（不需要 Claude Code，支持任意模型）

```bash
export ANTHROPIC_API_KEY=sk-ant-...   # 或 OPENAI_API_KEY

uv run main.py init ./myknowledge
uv run main.py compile ./myknowledge
uv run main.py query "什么是自注意力机制？" --kb ./myknowledge
uv run main.py lint ./myknowledge
```

配置模型和 provider：

```bash
# 使用 Anthropic（默认）
uv run main.py config ./myknowledge --set provider=anthropic model=claude-sonnet-4-5

# 使用 OpenAI-compatible（Ollama、DeepSeek 等）
uv run main.py config ./myknowledge --set provider=openai model=llama3 base_url=http://localhost:11434/v1
```

配置保存在 `<kb>/.shj.config.json`，API key 始终从环境变量读取。

### Claude Code Skill 模式

```
/shj init ./myknowledge
/shj ingest https://arxiv.org/abs/2405.15793
/shj compile ./myknowledge
/shj query "什么是 SWE-agent？"
/shj lint ./myknowledge
```

### Web UI

```bash
uv run web/server.py --kb ./myknowledge
# 打开 http://127.0.0.1:8000
```

Web UI 直接调用模型 API，流式输出。左下角 ⚙ 可配置 provider / model / base URL。

## 工作原理

### 编译

1. 对 `raw/` 中所有文件算 SHA-256 哈希
2. 与 `.wiki_state.json` 比对 → 找出新增/变更/删除
3. 对变更文件：生成摘要 + 提取概念
4. 生成/更新概念文章
5. 重建 `_index.md`
6. 保存状态

只处理增量。状态文件支持断点续传。

### 查询

1. 读 `_index.md`（轻量——每篇文章一行描述）
2. 大模型选出 3-7 篇相关文章
3. 读文章，合成带 `[[wikilink]]` 引用的回答

### 模型支持

| Provider | 配置 | API Key 环境变量 |
|----------|------|----------------|
| Anthropic | `provider=anthropic` | `ANTHROPIC_API_KEY` |
| OpenAI | `provider=openai` | `OPENAI_API_KEY` |
| Ollama / 本地模型 | `provider=openai`, `base_url=http://localhost:11434/v1` | 不需要 |
| DeepSeek 等 | `provider=openai`, `base_url=<endpoint>` | `OPENAI_API_KEY` |

## 输出格式

标准 markdown + `[[wikilinks]]`。用 Obsidian 打开 `wiki/` 目录——图谱视图、反向链接、搜索全都能用。

## 示例

`examples/` 目录里有一个示例知识库：论文编译后的完整 wiki。

## 路线图

- [x] Phase 1：核心功能（init / ingest / compile / query / lint）+ Web UI + 直接 API 模式
- [ ] Phase 2：`distill` 命令（任意输入 → 结构化知识条目），公开/私有分离，静态站点导出
- [ ] Phase 3：联邦公开 wiki registry，跨库链接，全局搜索

## 命名

山海经——古代中国的万物知识图谱。这个项目是你的个人百科全书，由大模型编译。

## License

MIT
