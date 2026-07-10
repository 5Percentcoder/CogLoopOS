# AI Engineer Personal Learning OS

## Purpose

This project turns AI-engineering topics into tested, reusable engineering judgment.
It is not a bookmark collection or an AI-generated encyclopedia.

## Required learning loop

For each topic:

1. Capture the concrete problem or trigger.
2. Write a falsifiable hypothesis.
3. Define a metric and pass/fail threshold before testing.
4. Build the smallest useful experiment.
5. Run it and preserve the command, data, and raw result.
6. Separate observation from interpretation.
7. Record one engineering decision with scope and limitations.
8. Link the loop from `vault/00_Index/Learning Loops.md`.

Use `vault/90_System/Templates/learning-loop.md` for the record. Store runnable artifacts under
`experiments/<loop-id>/`.

Before reporting a loop as complete, run:

```bash
python3 scripts/os.py sync-index
python3 scripts/os.py validate
```

## Evidence rules

- Never invent experiment results, sources, dates, or project experience.
- Label statements as `Fact`, `Hypothesis`, `Observation`, or `Decision`.
- Prefer official documentation, source code, papers, and reproducible local evidence.
- Treat toy data as workflow validation, not production evidence.
- A failed hypothesis is a valid outcome; do not tune the conclusion after seeing results.

## Scope control

- Create one learning-loop note per topic until repeated use proves a need for more object types.
- Do not add databases, vector stores, automation, Anki export, or extra Skills without observed friction.
- AI may draft changes, but durable knowledge and destructive merges require human review.
- Treat loop frontmatter as the status source of truth. Never hand-edit content between the generated
  markers in `vault/00_Index/Learning Loops.md`.
- Keep weekly review manual in v1. Generate it with `python3 scripts/os.py weekly-review`.

## Definition of done

A loop is complete only when its note contains:

- the original question;
- a falsifiable hypothesis;
- metric and threshold;
- a reproducible experiment command;
- observed result;
- decision and limitations;
- at least one future reuse trigger;
- an index link.

When inputs are missing, mark the loop `blocked` or `experiment-ready`; never fabricate completion.

## Repository verification

Run the full local verification suite after changing the kernel, templates, Skills, or contracts:

```bash
python3 -m unittest discover -s tests -v
python3 scripts/os.py sync-index
python3 scripts/os.py validate
```
