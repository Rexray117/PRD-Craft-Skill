# PRD Craft · 产品需求文档写作

[![DSH Skill](https://img.shields.io/badge/DeepSeek%20Harness-skill-4a7dff)](https://github.com/Rexray117/PRD-Craft-Skill)
[![version](https://img.shields.io/badge/version-2.0-brightgreen)](https://github.com/Rexray117/PRD-Craft-Skill/releases)
[![license](https://img.shields.io/badge/license-MIT-blue)](./LICENSE)

> 一个 **DeepSeek Harness（DSH）/ Agent Skill**：`prd-craft` v2.0。

Write product requirements documents (PRD) with two specializations — general software/systems (app, web, mini program, admin platform, SaaS, internal tool) and agent-type systems (agent, copilot, rule-engine automation, ops/inspection/scheduling automation). Use when the user wants to clarify a fuzzy product idea, structure requirements, write or review a PRD, or produce 需求文档 / 产品需求 / 功能规格 / 需求规格说明书. It runs a WHY-WHAT-HOW discovery pass, routes the requirement to one of five requirement types and one of two specializations, freezes scope, then produces a two-document pair — a requirement-body-only PRD carrying zero meta content and zero unresolved markers, plus a companion document carrying version info, terminology, background, open items, non-core details and companion index. Output is quality-gated for flows, state machines, field validation, copy rules, exception handling, metrics and acceptance criteria.

## 适用场景

把本仓库整体放进 agent 的技能目录即可按描述自动触发；也可以在对话里直接点名 `prd-craft`。

## 目录结构

```
`CHANGELOG.md`
`SKILL.md`
`LICENSE`
`.gitignore`
references/
scripts/
```

## 安装

### DSH（DeepSeek Harness）

技能目录放到用户级技能根：

```powershell
# Windows
git clone https://github.com/Rexray117/PRD-Craft-Skill.git "$env:USERPROFILE\.dsh\skills\prd-craft"
```

```bash
# macOS / Linux
git clone https://github.com/Rexray117/PRD-Craft-Skill.git ~/.dsh/skills/prd-craft
```

也可以用 DSH 的插件管理安装本地目录：

```
plugin_manager action=install_bundle target=<本仓库绝对路径>
```

### 其他 agent（Codex / WorkBuddy / Claude Code）

技能根分别位于 `~/.codex/skills`、`~/.workbuddy/skills`、`~/.claude/skills`，把本仓库克隆成其中的 `prd-craft` 子目录即可（技能名以 `SKILL.md` 的 `name: prd-craft` 为准）。

## 版本

- 当前版本：**v2.0**（与 `SKILL.md` 的 `version` 字段一致）
- 变更记录见仓库提交历史

## License

MIT © 2026 Rexray117
