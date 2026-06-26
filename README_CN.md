# weread-brain — 微信读书笔记 → 本地知识库

> 将微信读书的划线和想法自动同步为本地 Markdown 文件，构建个人知识库，可直接用于 Obsidian。

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python 3.9+](https://img.shields.io/badge/Python-3.9%2B-blue)](https://python.org)

## 功能

- 接入[微信读书 Skills API](https://weread.qq.com/r/weread-skills)（2026-05-17 官方发布）
- 自动同步**划线**和**个人想法**到本地 Markdown
- 按书名分文件，YAML frontmatter + Obsidian 兼容
- 每小时增量同步，仅更新有变化的书籍
- AI Agent 可直接调用：一行命令完成同步

## 快速开始

### 1. 安装 Skill

```bash
npx skills add Tencent/WeChatReading -g
```

### 2. 获取 API Key

访问 [https://weread.qq.com/r/weread-skills](https://weread.qq.com/r/weread-skills)，微信扫码登录，复制 API Key（`wrk-` 开头）。

### 3. 克隆并配置

```bash
git clone https://github.com/FistHeart/weread-brain.git
cd weread-brain
cp config/.env.example config/.env
# 编辑 config/.env，粘贴你的 API Key
```

### 4. 同步

```bash
python src/weread_sync.py
```

输出在 `output/` 目录，可直接用 Obsidian 打开。

## AI Agent 调用

任何 AI Agent（Claude Code / ChatGPT / Cursor）可直接执行：

```bash
cd /path/to/weread-brain && python src/weread_sync.py
```

## CLI 命令

| 命令 | 说明 |
|------|------|
| `python src/weread_sync.py` | 全量同步 |
| `python src/weread_sync.py --incremental` | 增量同步 |
| `python src/weread_sync.py --output ~/ObsidianVault/` | 自定义输出目录 |
| `python src/weread_sync.py --setup` | 交互式安装向导 |

## 每小时自动同步

```bash
crontab -e
7 * * * * cd /path/to/weread-brain && python src/weread_sync.py --incremental >> sync.log 2>&1
```

## 输出格式

每本书生成一个 Markdown 文件，包含划线、内联想法和独立想法：

```markdown
---
title: "人类简史"
author: "尤瓦尔·赫拉利"
tags: [weread, book-notes]
---

# 人类简史

## Highlights & Notes
> 文化倾向于主张它只禁止不自然的事物。
  — 第六章

## My Thoughts
> 生物学提供可能性，文化禁止某些可能性。
**Thought:** 生物学与文化的张力是历史的引擎。
```

## 安全

- API Key **零硬编码**——从环境变量或 `config/.env` 加载
- `config/.env` 和 `output/` 已被 `.gitignore` 排除
- API Key 不写入日志或输出文件

## 依赖

- Python 3.9+
- `requests`（`pip install requests`）
- 微信读书账号 + API Key

## 项目结构

```
weread-brain/
├── README.md              # English
├── README_CN.md           # 中文
├── setup.sh               # 一键安装
├── config/.env.example    # 密钥模板
├── src/weread_sync.py     # 核心引擎
└── output/                # 同步输出 (gitignored)
```

## 相关

- [微信读书 Skills](https://weread.qq.com/r/weread-skills) — 官方 API
- [Obsidian](https://obsidian.md) — 推荐的知识库工具
- [Karpathy LLM Wiki](https://github.com/Astro-Han/karpathy-llm-wiki-bootstrap) — 知识库方法论
