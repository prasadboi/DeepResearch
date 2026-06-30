# Copilot / Claude Code task prompt template

Copy this template for each implementation task. Fill it using the matching task in `docs/04_TASK_SPECS.md`.

```text
You are implementing exactly one task in the LitGraph repository.

Active task:
  Stage: <stage number and name>
  Task: <task id and name>

Product goal:
  <closed product goal from task spec>

Inputs:
  <existing modules, fixtures, config files, services>

Outputs to create or modify:
  <files, modules, commands, reports>

Explicit non-goals:
  <copy non-goals exactly>

Programming invariants:
  <copy invariants exactly>

Construction tests required:
  <copy tests exactly>

Evaluation gate:
  <copy evaluation gate exactly>

Implementation instructions:
  - Keep the implementation minimal and stage-local.
  - Do not implement future-stage components.
  - Do not change global invariants without an ADR.
  - Add fixtures instead of using live network calls in construction tests.
  - Update docs only when the task changes a documented contract.

Before finishing:
  - Run construction tests.
  - Report which tests passed.
  - Report whether the evaluation gate was run.
  - If the evaluation gate was not run, explain exactly what resource is missing.
  - Do not mark the task complete if construction tests fail.
```

## Required final response from coding agent

```text
Implemented:
  - ...

Files changed:
  - ...

Construction tests:
  - passed/failed/not run with reason

Evaluation gate:
  - passed/failed/not run with reason

Non-goals preserved:
  - ...

Risks or follow-up:
  - ...
```
