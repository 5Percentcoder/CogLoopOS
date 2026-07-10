---
name: review-learning-os
description: Inspect the Personal Learning OS for structural health, stale or blocked learning loops, missing evidence, index drift, and possible duplicate topics, then generate a reviewable weekly maintenance report. Use when the user asks for a weekly review, knowledge-system health check, maintenance pass, learning backlog review, or OS audit. Do not use to learn one technical topic or silently rewrite completed conclusions.
---

# Review Learning OS

Generate one deterministic health review, then help the user interpret it without autonomously
rewriting durable knowledge.

## Workflow

1. Read `AGENTS.md`, `vault/90_System/Templates/weekly-review.md`, and
   `vault/00_Index/Learning Loops.md`.
2. Run `python3 scripts/os.py sync-index`.
3. Run `python3 scripts/os.py validate`.
   - Continue generating a report when validation fails so the anomalies are captured.
   - Do not conceal, hand-wave, or silently repair semantic issues.
4. Run `python3 scripts/os.py weekly-review --date YYYY-MM-DD` using the user's requested date or
   the current local date.
5. Read the generated `vault/20_Reviews/<year>-W<week>.md`.
6. Interpret the report for the user:
   - identify the highest-value next action;
   - separate mechanical anomalies from knowledge-quality concerns;
   - treat duplicate detection as a review candidate, not a merge decision;
   - call out stale loops that no longer justify their maintenance cost.
7. Update only the report's `Human Decision` section when the user explicitly accepts or edits
   recommendations.
8. Report the health result, status counts, top priority, unresolved anomalies, and clickable report
   path.

## Guardrails

- Never delete, merge, or semantically rewrite a completed loop during a review.
- Never create extra taxonomy merely to make the dashboard look organized.
- Do not run unrelated experiments.
- Preserve human decisions when regenerating the same weekly report.
- Propose a new Skill, dependency, object type, or automation only when repeated evidence shows a
  concrete maintenance problem.
- Keep weekly review manual in v1; do not create a schedule or automation.

## Follow-up actions

After the user approves a recommendation, perform it as a separate scoped task. Use
`$run-learning-loop` when the approved action is a new technical investigation.
