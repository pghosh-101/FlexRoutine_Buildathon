# FlexRoutine Planner - Level 3 Correction Loop

## What makes this a potential Level 3 task

The app does more than generate a first answer. It checks the model's proposed routine against the student's time budget and corrects an infeasible plan before showing it.

## Sequence

1. Claude drafts a routine using the student's priority labels.
2. The program calculates the sum of the scheduled minutes and checks every returned total.
3. If the first response is over budget or internally inconsistent, the app sends a correction request containing the draft and validation issue.
4. Claude revises lower-priority habits by shortening or skipping them.
5. The program recalculates `total_minutes` and `remaining_minutes`.
6. The app rechecks the corrected plan and refuses to display a plan that exceeds the budget.
7. The dashboard presents the corrected routine, skipped habits, totals, and explanation.

## Why it matters

This correction loop is a meaningful agent behavior because the system evaluates its own first plan against a constraint, revises the plan, and verifies the revised result before presenting it to the student.

## Demo test

Use 25 available minutes with Study = essential (30/10), Exercise = important (30/10), and Meditation = optional (10/2). The result should stay at or below 25 minutes and should show at least one shortened or skipped habit when necessary.
