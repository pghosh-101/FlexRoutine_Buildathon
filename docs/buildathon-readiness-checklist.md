# BUS4498 Build-a-thon Readiness Checklist

## Required project evidence

- [x] Option 1 is implemented: maintain habits when schedules change.
- [x] A working local Streamlit app runs from `app.py`.
- [x] The workflow sketch shows trigger, task sequence, AI tasks, model/tool choices, Skill decision, Level 3 behavior, and endpoint.
- [x] The reusable `FlexRoutine Planner` Skill is included in `skills/flexroutine-planner/SKILL.md`.
- [x] Codex Skill metadata is included in `skills/flexroutine-planner/agents/openai.yaml`.
- [x] The Level 3 correction loop is documented in `docs/level-3-correction-loop.md` and implemented as an automatic correction pass plus final validation.
- [x] The Claude key is stored locally in `.env`; `.gitignore` excludes `.env`.
- [x] The app returns a useful dashboard and keeps raw JSON available for download.

## Three-minute showcase plan

1. Trigger: enter a changed schedule and a smaller number of available minutes.
2. Input: show habits with Essential, Important, and Optional priorities plus full/minimum minutes.
3. Run: click `Adjust my routine` and explain that Claude interprets the change and follows the reusable Skill.
4. Result: point to the dashboard totals, shortened habits, skipped habits, and supportive explanation.
5. Level 3: explain that the system checks the total and corrects an over-budget draft before display.
6. Design choices: Claude + Anthropic API, Streamlit local app, JSON contract, and `.env` secret handling.
7. Team roles: both partners explain a part of the workflow and participate in testing/revision.

## Test cases to rehearse

- Full-time case: enough minutes for every full habit.
- Limited-time case: some habits are shortened or skipped while priorities are preserved.
- Zero-time case: no habits are scheduled and the response remains supportive.
- Invalid-input case: missing names or minimum minutes greater than full minutes.
