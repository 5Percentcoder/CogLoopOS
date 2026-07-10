# Operating Guide

这页是 Obsidian 里的使用说明。它回答一个问题：看到一个技术问题时，下一步到底做什么。

## What is connected

- Obsidian 打开的是本仓库的 `vault/`。
- 系统首页是 [[Home]]。
- 学习闭环索引是 [[00_Index/Learning Loops|Learning Loops Dashboard]]。
- 模板目录是 [[90_System/Templates/learning-loop|90_System/Templates]]。
- 可运行实验和校验仍由 Codex / terminal 执行，结果回写到 Markdown note 和 `experiments/`。

Obsidian 负责阅读、链接、人工判断；Codex 负责把问题推进成假设、实验、证据和工程决策。

## Daily flow

### 1. Quick capture in Obsidian

如果只是突然想到一个主题，先新建一个普通 note，写下：

- 原始问题；
- 触发场景；
- 你担心的工程风险；
- 你希望以后复用的判断。

这个阶段不要求完整，也不要急着写结论。

### 2. Promote to a learning loop in Codex

当这个问题值得验证时，在 Codex 里说：

```text
使用 $run-learning-loop，把“这里粘贴原始问题或 Obsidian note 内容”跑成学习闭环。
```

Codex 应该创建或更新 `vault/10_Loops/<loop-id>.md`，并把可运行实验放到
`experiments/<loop-id>/`。

### 3. Read and judge in Obsidian

完成后回到 Obsidian，从 [[Home]] 或 [[00_Index/Learning Loops|Learning Loops Dashboard]]
进入 loop note，重点看三块：

- `Observation`：实验实际看到了什么；
- `Interpretation`：这些现象说明什么；
- `Decision`：以后遇到类似场景，怎么做。

### 4. Weekly review

每周或积累了几个主题后，在 Codex 里说：

```text
使用 $review-learning-os 审查本周学习系统。
```

或手动运行：

```bash
python3 scripts/os.py weekly-review
```

周报会生成到 `vault/20_Reviews/`。它只做健康检查和建议，不自动改写 completed loops。

## Template use

Obsidian 已配置内置 Templates 插件，模板目录是：

```text
90_System/Templates
```

如果你手动创建 loop note，可以从 [[90_System/Templates/learning-loop|learning-loop template]]
插入结构。但默认推荐让 Codex 创建 loop，因为它会同时建立实验目录、同步索引并运行校验。

## Commands

```bash
python3 scripts/os.py sync-index
python3 scripts/os.py validate
python3 scripts/os.py weekly-review
python3 -m unittest discover -s tests -v
```

## Rules of thumb

- 普通 Obsidian note 可以很松；learning loop 必须可验证。
- 不要把资料摘抄当成完成；完成必须有证据、判断、限制和复用触发器。
- 不要手动编辑 [[00_Index/Learning Loops|Learning Loops Dashboard]] 的 generated 区域。
- 如果缺数据、环境或明确目标，把 loop 标成 `blocked`，不要编造结果。
- 只有真实使用反复暴露摩擦时，才给系统增加新结构。

