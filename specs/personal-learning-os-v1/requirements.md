# Personal Learning OS v1 — Requirements

## 1. Problem

一次性 AI 对话会产生答案，但不会稳定积累问题背景、实验过程、工程判断和后续复用条件。
普通知识库又容易把大量资料和 AI 摘要堆成高维护成本的“电子仓库”。

本系统需要让 AI 工程师以较低维护成本，把真实技术问题持续转化为：

- 可验证的假设；
- 可复现的实验；
- 有边界的工程判断；
- 能在后续项目中重新调用的知识资产。

## 2. Product goal

构建一个本地优先、由 Codex 执行工作流、由 Obsidian 承载知识、可用 Git
版本化的个人学习操作系统。

v1 的核心成功不是笔记数量，而是稳定运行以下闭环：

```text
真实问题 → 可证伪假设 → 最小实验 → 原始证据
→ 工程判断 → 知识关联 → 未来复用
```

## 3. Primary user

具备开发经验、持续学习 RAG、Agent、数据库、LLM 应用架构等主题的 AI 工程师。
用户负责目标、判断、实践和最终确认；Codex 负责结构化、执行、关联和维护草稿。

## 4. Scope

### 4.1 In scope for v1

- 单个技术问题的完整学习闭环。
- 闭环状态管理：`captured`、`experiment-ready`、`complete`、`blocked`。
- 本地 Markdown 知识记录与 Obsidian 链接。
- 本地代码、数据和原始实验结果。
- 一个统一入口，用于查看 active、blocked、complete 和下一步。
- 基于文件名、标签、全文搜索和显式链接的历史知识复用。
- 人工触发的周度维护检查。
- 仓库级 Codex Skill 和持久项目规则。
- 与 Git 兼容的纯文本资产；v1 不自动提交或合并。

### 4.2 Non-goals for v1

- 自动批量摄取网页、视频、论文或聊天记录。
- 向量数据库、GraphRAG 或独立 RAG 检索服务。
- 多 Agent 编排或后台自治循环。
- 自动合并、删除或重写稳定知识。
- Anki、Readwise、NotebookLM 等外部系统集成。
- 通用生活管理、日记、日程或任务管理。
- 面向多用户的 Web 产品、云同步或权限系统。

## 5. User stories and acceptance criteria

### Requirement 1 — Capture a real question

**User story:** 作为 AI 工程师，我希望能用自然语言提交一个真实技术问题，
以便系统保存原始动机，而不是直接生成脱离语境的百科答案。

- When the user submits a new learning topic, the system shall create one uniquely identified
  learning-loop record containing the original question and its source context.
- If a materially similar loop already exists, the system shall surface it before creating a
  duplicate.
- The initial capture shall require no manual taxonomy design from the user.

### Requirement 2 — Freeze a testable contract

**User story:** 作为学习者，我希望在实验前确定什么结果算成功，
避免看到结果后修改结论。

- Before executing an experiment, the system shall record a falsifiable hypothesis.
- Before executing an experiment, the system shall record a primary metric and pass/fail threshold.
- When regression is plausible, the system shall define at least one guardrail metric.
- If the topic cannot be tested locally, the system shall record the missing evidence and use
  `blocked` or `experiment-ready` rather than fabricate completion.

### Requirement 3 — Preserve reproducible evidence

**User story:** 作为工程师，我希望以后能重新运行实验并审查原始结果，
而不是只相信 AI 的总结。

- When an experiment runs, the system shall preserve the exact command, inputs, environment
  assumptions, and raw result.
- When the loop is marked `complete`, another Codex session shall be able to locate and rerun
  the experiment from repository files.
- The system shall distinguish facts, hypotheses, observations, and decisions.

### Requirement 4 — Produce bounded engineering judgment

**User story:** 作为 AI 工程师，我希望学习结果能指导项目决策，
同时明确它不能证明什么。

- When evidence is available, the system shall record a decision derived from that evidence.
- Every completed loop shall state its applicable scope, limitations, and production-validation needs.
- When evidence contradicts the hypothesis, the system shall preserve the failed hypothesis and
  record the negative result without redefining success.

### Requirement 5 — Retrieve and reuse prior learning

**User story:** 作为长期用户，我希望遇到相似问题时先调用旧实验和判断，
避免重新开始一次性对话。

- When a new topic overlaps an existing loop, the system shall link the prior loop or explain why
  it is not reusable.
- Every completed loop shall contain at least one future reuse trigger.
- The system shall support useful retrieval in v1 through the index, Obsidian links, tags, and
  full-text search without requiring embeddings.

### Requirement 6 — Provide an operational dashboard

**User story:** 作为系统负责人，我希望快速知道正在学习什么、哪里被阻塞、
以及下一步做什么。

- When a loop changes status, the system shall update the central index in the same change.
- The index shall separate active, blocked, and completed loops.
- Each active or blocked loop shall expose one concrete next action or named blocker.

### Requirement 7 — Keep maintenance cheaper than value

**User story:** 作为长期用户，我不希望系统维护本身变成第二份工作。

- For a normal new topic, the user shall interact primarily through one prompt and review one
  learning-loop record.
- The system shall not require manually maintaining duplicate content across concept, experiment,
  decision, and review notes in v1.
- The system shall add a new directory, object type, dependency, or Skill only after repeated
  usage demonstrates a concrete need.

### Requirement 8 — Maintain human control and safety

**User story:** 作为知识资产的所有者，我希望 AI 可以主动工作，但不能悄悄篡改结论。

- When Codex changes durable knowledge, the change shall remain reviewable as plain-text files.
- The system shall not automatically delete, merge, or overwrite completed loops.
- The system shall never invent sources, execution results, dates, or user project experience.
- When external technical claims materially affect a decision, the system shall prefer primary
  sources and record access dates.

### Requirement 9 — Run a manual weekly review

**User story:** 作为长期用户，我希望系统定期发现停滞和重复，但暂时不引入后台自动化。

- When the user invokes the weekly review, the system shall scan loop statuses, missing evidence,
  stale active items, unresolved blockers, and repeated topics.
- The review shall propose changes as a reviewable report rather than silently modifying completed
  conclusions.
- For up to 50 loops, the human review portion should be completable within 15 minutes.

### Requirement 10 — Preserve the validated MVP

**User story:** 作为现有系统用户，我希望架构升级不破坏已经完成的学习资产。

- When OS v1 is introduced, the system shall preserve the two existing completed loops,
  their experiments, and their raw results.
- Existing `$run-learning-loop` behavior shall remain usable or receive a documented migration.
- The repository shall remain usable without Obsidian plugins or external paid services.

## 6. Quality attributes

### Local-first and portable

- Knowledge shall remain readable as ordinary Markdown.
- Experiments shall remain runnable from the repository when their declared dependencies exist.
- Obsidian shall enhance navigation but shall not be required to read the knowledge.

### Traceable

- A completed decision shall be traceable to one loop and its evidence.
- A generated result shall not be treated as durable knowledge until represented in a reviewed note.

### Evolvable

- v1 shall favor stable file contracts over framework-specific orchestration.
- Later automation shall consume existing records instead of requiring a full rewrite.

## 7. Proposed success metrics

The v1 architecture is considered validated after:

1. At least three additional real learning topics complete the loop.
2. Every completed loop has a runnable or explicitly external evidence path.
3. A prior relevant loop can be located in under one minute using the index or text search.
4. A weekly review of up to 50 loops can be reviewed by the user in 15 minutes or less.
5. No completed loop contains fabricated execution evidence.

## 8. Assumptions requiring confirmation

1. v1 remains focused on AI-engineering learning rather than general personal knowledge management.
2. `vault/` remains the Obsidian Vault and experiments remain outside it.
3. Weekly review is manually invoked; no scheduled automation is added yet.
4. Git compatibility is required, but automatic commits, branches, and pull requests are deferred.
5. Architecture expansion begins only after three more real loops expose actual friction.
