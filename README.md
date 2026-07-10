# AI Engineer Personal Learning OS

一个本地优先的 AI 工程学习系统：

```text
真实问题 → 可证伪假设 → 最小实验 → 原始证据
→ 工程判断 → 知识关联 → 未来复用
```

它不是资料收藏夹。系统的核心产物是经过验证、有适用边界、以后能够重新调用的
工程判断。

## Architecture

```text
用户
├── Codex：推理、实验设计、工作流执行
└── Obsidian：阅读、链接、人工审查

Repository
├── AGENTS.md：长期政策与完成定义
├── .agents/skills/：Codex 工作流
├── scripts/os.py：确定性校验、索引和周报内核
├── vault/：Obsidian Vault、Markdown 知识、模板与派生视图
├── experiments/：代码、数据与原始结果
└── specs/：需求、设计与实施记录
```

Markdown learning loops 是知识来源；中央索引和周报是可重建的视图。
Obsidian 可以增强使用体验，但不是运行时依赖。

## Open in Obsidian

把 `vault/` 作为 Obsidian Vault 打开。首页是 `Home.md`，模板目录是
`90_System/Templates`。v1 只使用 Obsidian 内置的 Templates 核心插件，
不需要安装第三方插件。Obsidian 里的操作入口是
`vault/90_System/Operating Guide.md`。

## Daily workflow

在 Codex 中使用：

```text
使用 $run-learning-loop，把“一个真实技术问题”跑成学习闭环。
```

该 Skill 会：

1. 搜索已有 loops，避免重复学习。
2. 冻结假设、指标和通过阈值。
3. 创建并运行最小实验，或诚实标记阻塞状态。
4. 保存原始结果并形成有边界的工程判断。
5. 同步索引并运行结构校验。

手动运行内核：

```bash
python3 scripts/os.py sync-index
python3 scripts/os.py validate
```

## Weekly workflow

在 Codex 中使用：

```text
使用 $review-learning-os 审查本周学习系统。
```

或直接运行：

```bash
python3 scripts/os.py weekly-review --date 2026-07-09
```

报告生成到 `vault/20_Reviews/<year>-W<week>.md`。重新生成会保留
`Human Decision` 部分。周报只提出建议，不会自动改写 completed loops。

## Status model

- `captured`：已记录真实问题，尚未冻结实验契约。
- `experiment-ready`：实验契约已完成，等待运行或外部证据。
- `blocked`：缺少明确的数据、环境或决策。
- `complete`：证据、判断、限制和复用触发器齐全。

实验否定假设仍然可以 `complete`；没有运行证据不能假装完成。

## Verification

```bash
python3 -m unittest discover -s tests -v
python3 scripts/os.py sync-index
python3 scripts/os.py validate
```

现有实验可以独立复现：

```bash
python3 experiments/2026-07-09-controlled-query-expansion/evaluate.py
python3 experiments/2026-07-09-sql-query-crash-causes/evaluate.py
```

## Deliberate limits

v1 暂不包含：

- 批量资料摄取；
- 向量数据库或独立 RAG 服务；
- 多 Agent 编排；
- 后台自动调度；
- 自动合并或删除稳定知识；
- 外部付费服务和第三方 Python 依赖。

只有真实使用反复暴露同一种摩擦时，系统才增加下一层结构。

## Specifications

- [Requirements](specs/personal-learning-os-v1/requirements.md)
- [Design](specs/personal-learning-os-v1/design.md)
- [Implementation Plan](specs/personal-learning-os-v1/tasks.md)
