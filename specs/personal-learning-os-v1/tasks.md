# Personal Learning OS v1 — Implementation Plan

## Execution rules

- Complete tasks in order unless a discovered dependency requires a documented change.
- Keep this checklist current during implementation.
- Finish each task with its listed verification before starting the next.
- Preserve the two existing loops and their raw experiment results.
- Use Python standard library only for the deterministic kernel and its tests.

## Tasks

- [x] 1. Establish executable file contracts and test fixtures
  - Add `vault/90_System/Templates/weekly-review.md` with the sections defined in the design.
  - Add representative test fixtures for `captured`, `experiment-ready`, `blocked`, and
    `complete` loops, including invalid and duplicate-ID cases.
  - Add the `scripts/os.py` CLI entry point with `validate`, `sync-index`, and `weekly-review`
    subcommands that can be imported safely by tests.
  - Add the initial `unittest` suite and confirm it can run without third-party packages.
  - Verify with `python3 -m unittest discover -s tests -v`.
  - _Requirements: R2, R3, R4, R6, R9, R10_

- [x] 2. Implement learning-loop parsing and structural validation
  - Parse the limited frontmatter contract without adding a YAML dependency.
  - Extract title, required body sections, next action, evidence paths, and placeholders.
  - Validate required fields, allowed statuses, unique IDs, required sections, and date formats.
  - For `complete` loops, validate the completion contract without judging technical truth.
  - Validate referenced local evidence paths and parse referenced JSON result files when present.
  - Return actionable errors containing file, violated rule, and remediation.
  - Add unit tests for valid, invalid, blocked, negative-result, placeholder, and duplicate cases.
  - Verify `python3 scripts/os.py validate` succeeds on the current repository.
  - _Requirements: R2, R3, R4, R8, R10_

- [x] 3. Make the operational index a deterministic derived view
  - Add generated-region markers to `vault/00_Index/Learning Loops.md` while preserving its
    human-authored introduction.
  - Implement `sync-index` using loop frontmatter and titles as the source of truth.
  - Group `captured` and `experiment-ready` under Active, `blocked` under Blocked, and
    `complete` under Complete.
  - Include the next action for active and blocked records.
  - Apply the specified update-date and ID ordering.
  - Make repeated `sync-index` runs idempotent.
  - Add tests for ordering, marker replacement, missing markers, and duplicate IDs.
  - Verify both existing completed loops remain linked after migration.
  - _Requirements: R1, R5, R6, R7, R10_

- [x] 4. Implement manual weekly health review
  - Implement `weekly-review --date YYYY-MM-DD` using ISO week naming.
  - Aggregate validation status, status counts, active next actions, blockers, recently completed
    loops, structural anomalies, and possible duplicates.
  - Generate a reviewable Markdown draft in `vault/20_Reviews/`.
  - Preserve a human-decision section and never modify completed loop conclusions.
  - Make regeneration for the same week deterministic unless the human section has been edited;
    in that case, preserve the human section.
  - Add tests for week boundaries, empty states, stale records, duplicate suggestions, and
    preservation of human decisions.
  - Verify a smoke-test weekly review can be generated from the real repository.
  - _Requirements: R6, R7, R8, R9_

- [x] 5. Integrate Codex workflows with the deterministic kernel
  - Update `$run-learning-loop` to search prior loops before creation and to run `sync-index`
    followed by `validate` before reporting completion.
  - Create the repository-level `$review-learning-os` Skill using the `skill-creator` workflow.
  - Keep both Skills focused on judgment and orchestration; do not duplicate parser logic.
  - Add accurate `agents/openai.yaml` metadata for the review Skill.
  - Validate both Skill frontmatters and metadata.
  - Confirm the Skills remain repository-scoped under `.agents/skills/`.
  - _Requirements: R1, R2, R3, R5, R6, R7, R8, R9, R10_

- [x] 6. Migrate project policy and documentation
  - Update `AGENTS.md` with the v1 validation commands and generated-index rule.
  - Update `README.md` with the final architecture, daily workflow, weekly workflow, and commands.
  - Keep `vault/` usable as an Obsidian Vault without plugins.
  - Preserve the two existing learning-loop notes, experiment code, and raw result values.
  - Run index synchronization and generate the first weekly review.
  - Review the resulting diff for unintended semantic changes to completed loops.
  - _Requirements: R5, R6, R7, R8, R9, R10_

- [x] 7. Run end-to-end acceptance verification
  - Run `python3 -m unittest discover -s tests -v`.
  - Run `python3 scripts/os.py sync-index` twice and confirm the second run makes no content change.
  - Run `python3 scripts/os.py validate`.
  - Rerun both existing experiment scripts and confirm their result contracts still pass.
  - Run `python3 scripts/os.py weekly-review --date 2026-07-09` and validate the generated report.
  - Confirm no vector database, background scheduler, external paid service, or third-party Python
    dependency was introduced.
  - Record verification evidence and any deferred limitations in this plan.
  - _Requirements: R1, R2, R3, R4, R5, R6, R7, R8, R9, R10_

## Completion evidence

- Unit tests: `13` tests passed with Python `unittest`.
- Repository validation: `PASS: 2 learning loops are structurally valid.`
- Index idempotence: two consecutive syncs reported already synchronized; SHA-1 remained
  `1ddc1ee7cd5004fe851241b9795901b4300c75e2`.
- Existing experiment regressions:
  - controlled query expansion passed with Recall@1 improvement `0.3333`;
  - SQL result consumption passed with peak-memory ratio `75.14`.
- Weekly review smoke test: `vault/20_Reviews/2026-W28.md` generated with repository health `PASS`.
- Obsidian integration: `vault/` registered in Obsidian 1.12.7, `Home.md` opened, the built-in
  Templates plugin enabled, and its folder configured as `90_System/Templates`.
- Dependency boundary: kernel, tests, and experiments import Python standard-library modules only;
  no vector database, scheduler, or external service was introduced.
- Skill validation: the official validator could not start because its environment lacks `PyYAML`;
  equivalent YAML/frontmatter/name/default-prompt checks passed for both repository Skills using
  the system YAML parser.
- Deferred limitations:
  - product-level v1 validation still requires three additional real learning loops;
  - Git remains compatible but is not initialized or automated by this implementation;
  - new repository Skills may require a Codex refresh if they do not appear immediately.
