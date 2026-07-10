---
name: run-learning-loop
description: Turn one AI-engineering question, unfamiliar technology, project failure, course insight, or architecture claim into a falsifiable hypothesis, minimal reproducible experiment, evidence-backed engineering decision, and indexed Obsidian learning asset. Use when the user asks to learn, validate, compare, investigate, or retain a technical topic through the Personal Learning OS. Do not use for simple factual answers or bulk note ingestion.
---

# Run Learning Loop

Run exactly one topic through the repository's learning loop. Keep the work small enough to
finish or mark honestly as blocked.

## Workflow

1. Read `AGENTS.md`, `vault/90_System/Templates/learning-loop.md`, and
   `vault/00_Index/Learning Loops.md`.
2. Search existing loop titles, tags, full text, and experiments before creating a record. Reuse or
   link relevant prior evidence; explain why a similar loop is not reusable before creating a
   duplicate.
3. Create a loop ID in `YYYY-MM-DD-topic-slug` form.
4. Create one note in `vault/10_Loops/<loop-id>.md` from the template.
5. Capture the real trigger and distinguish facts from unknowns.
6. Write a falsifiable hypothesis. State what observation would disprove it.
7. Freeze an experiment contract before execution:
   - primary metric;
   - numeric or unambiguous pass threshold;
   - at least one guardrail when regressions are plausible;
   - fixed variables;
   - minimal data;
   - exact reproduction command.
8. Put executable artifacts in `experiments/<loop-id>/`.
9. Run the experiment when local inputs and permissions allow it. Preserve raw output in the
   experiment directory. Never invent a run.
10. Write observations without interpretation, then a separate decision with scope, limitations,
    and production-validation needs.
11. Add at least one future reuse trigger and useful Obsidian links.
12. Run `python3 scripts/os.py sync-index`; never hand-edit the generated index region.
13. Run `python3 scripts/os.py validate`. Do not report completion while validation fails.

## Status rules

- Use `captured` when the question exists but the experiment contract does not.
- Use `experiment-ready` when the contract and runnable plan exist but have not run.
- Use `complete` only when the note satisfies `AGENTS.md`'s definition of done.
- Use `blocked` when a named missing input, environment, or user decision prevents progress.

## Guardrails

- Prefer one note and one minimal experiment over a new taxonomy.
- Do not create standalone concept pages merely to satisfy links; allow unresolved Obsidian links.
- Treat toy or synthetic data as mechanism evidence only.
- Do not introduce dependencies when the standard library or existing project tools suffice.
- Do not broaden the loop into a production implementation unless the user explicitly asks.
- If external technical claims matter, verify them with primary sources and record source dates.

## Completion report

Report the tested hypothesis, command, measured result, decision, limitations, and clickable paths
to the loop note and experiment. Include the repository validation result. If incomplete, report
the exact blocker and the next executable step.
