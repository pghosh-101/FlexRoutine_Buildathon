---
name: flexroutine-planner
description: "Turn a student's habits, priorities, and available time into a feasible adjusted routine. Use when a schedule change requires the student to adapt a recurring routine."
---

# FlexRoutine Planner

## User inputs

The user supplies the facts that may change on each run:

- `available_minutes`: total time currently available; required, nonnegative integer.
- `schedule_change`: optional description of the class, work shift, event, or other change.
- `habits`: required list of habits. Each habit should include:
  - `name`: habit or routine activity.
  - `priority`: the user's ranking or label, such as essential, important, or optional.
  - `full_minutes`: time needed for the normal version.
  - `minimum_minutes`: shortest acceptable version, when one exists.
  - `details`: optional constraints or context, such as a deadline, time window, location, energy level, dependency, or preference.
- `preferences`: optional user preferences, such as a desired order, buffer time, or a habit that must not be shortened.

Treat the user's priority labels and explicit constraints as authoritative. Ask for missing essential information instead of inventing durations, priorities, or schedule facts.

## Procedure

1. Validate that `available_minutes` is a nonnegative whole number and that every habit has a name, priority, and valid full duration. Check minimum durations when provided.
2. If an essential input is missing or contradictory, stop and return the `needs_input` JSON format. State exactly what the user needs to provide or clarify.
3. Interpret the schedule change and relevant habit details, but do not override an explicit user priority without explaining the conflict.
4. Rank habits using the user's priority order. If no order is supplied, use `essential`/`critical`, then `high`/`important`, then `medium`/`normal`, then `optional`/`low`. Preserve the original input order for ties.
5. For each habit from highest to lowest priority, schedule the full version when it fits in the remaining time.
6. If the full version does not fit, schedule the provided minimum or shortened version when it fits and label it `shortened`.
7. If neither version fits, skip the habit and record a clear reason.
8. Run a correction loop before responding: if the draft total exceeds the available time, shorten or remove lower-priority items, recalculate the total, and recheck the plan. This is the potential Level 3 behavior.
9. Confirm that all scheduled durations are nonnegative whole numbers and that `total_minutes` never exceeds `available_minutes`.
10. Return only the required JSON output. Use supportive language: a shortened or skipped habit is an adaptation to the day's constraints, not a failure.

## Output

For a valid plan, return JSON only, with no Markdown fences or extra commentary:

```json
{
  "status": "ok",
  "adjusted_routine": [
    {
      "habit": "string",
      "priority": "string or number",
      "minutes": 0,
      "version": "full or shortened",
      "reason": "short explanation"
    }
  ],
  "skipped_habits": [
    {
      "habit": "string",
      "priority": "string or number",
      "reason": "short explanation"
    }
  ],
  "total_minutes": 0,
  "available_minutes": 0,
  "remaining_minutes": 0,
  "explanation": "short supportive summary"
}
```

`total_minutes` must equal the sum of scheduled minutes. `remaining_minutes` must equal `available_minutes - total_minutes`. All duration values must be nonnegative integers.

If required input is missing or invalid, return JSON only in this form:

```json
{
  "status": "needs_input",
  "missing_fields": ["available_minutes"],
  "adjusted_routine": [],
  "skipped_habits": [],
  "total_minutes": 0,
  "available_minutes": 0,
  "remaining_minutes": 0,
  "explanation": "Please provide the missing information so I can adjust the routine."
}
```

## Boundaries

- Do not invent missing durations, priorities, deadlines, or schedule details.
- Do not schedule more time than the user has available.
- Do not make calendar changes, send messages, or take other external actions.
- Keep the user in control of the final routine and mention important assumptions or conflicts.
- Never shame the user for shortening or skipping a habit.
