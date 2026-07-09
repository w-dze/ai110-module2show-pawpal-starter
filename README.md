# PawPal+ (Module 2 Project)

You are building **PawPal+**, a Streamlit app that helps a pet owner plan care tasks for their pet.

## Scenario

A busy pet owner needs help staying consistent with pet care. They want an assistant that can:

- Track pet care tasks (walks, feeding, meds, enrichment, grooming, etc.)
- Consider constraints (time available, priority, owner preferences)
- Produce a daily plan and explain why it chose that plan

Your job is to design the system first (UML), then implement the logic in Python, then connect it to the Streamlit UI.

## What you will build

Your final app should:

- Let a user enter basic owner + pet info
- Let a user add/edit tasks (duration + priority at minimum)
- Generate a daily schedule/plan based on constraints and priorities
- Display the plan clearly (and ideally explain the reasoning)
- Include tests for the most important scheduling behaviors

## Getting started

### Setup

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### Suggested workflow

1. Read the scenario carefully and identify requirements and edge cases.
2. Draft a UML diagram (classes, attributes, methods, relationships).
3. Convert UML into Python class stubs (no logic yet).
4. Implement scheduling logic in small increments.
5. Add tests to verify key behaviors.
6. Connect your logic to the Streamlit UI in `app.py`.
7. Refine UML so it matches what you actually built.

## 🖥️ Sample Output

Running `python main.py` prints a daily plan to the terminal:

```
Daily plan for Wendy:
  08:00 — Feed Bella (5 min) [priority: high]
  08:05 — Feed Rex (10 min) [priority: high]
  08:15 — Play with Bella (15 min) [priority: medium]
  08:30 — Play with Rex (20 min) [priority: medium]

  Total planned time: 50 of 60 minutes
```

## 🧪 Testing PawPal+

```bash
# Run the full test suite:
pytest

# Run with coverage:
pytest --cov
```

Sample test output:

```
# Paste your pytest output here
```

## 📐 Smarter Scheduling

Beyond the basic daily plan, `Scheduler` (in [`pawpal_system.py`](pawpal_system.py)) adds four
"smarter" behaviors. Each is summarized below and documented in full in the method docstrings.

| Feature | Method(s) | Notes |
|---------|-----------|-------|
| Task sorting | `Scheduler.sort_tasks()`, `Scheduler.sort_by_time()` | Priority-then-duration for planning; duration-only for a shortest-first view |
| Filtering | `Scheduler.filter_tasks()` | Narrow tasks by completion status and/or pet name |
| Conflict handling | `Scheduler.detect_conflicts()` | Warn (don't crash) on overlapping time slots |
| Recurring tasks | `Task.next_occurrence()`, `Scheduler.complete_task()` | Completing a daily/weekly task spawns its next occurrence |

### Sorting behavior — `sort_tasks()` and `sort_by_time()`

- **`sort_tasks()`** orders the pending tasks by **priority (highest first), then shortest
  duration** as a tiebreaker. This is the order `generate_plan()` packs tasks in, so the most
  important care happens first.
- **`sort_by_time()`** orders the pending tasks purely by **duration, shortest first**, giving the
  owner a "quick wins" view of how many small tasks fit before committing to a long one.

Both return a new list and leave each pet's task list untouched.

### Filtering behavior — `filter_tasks()`

`filter_tasks(*, completed=None, pet_name=None)` returns tasks narrowed by two optional,
independent filters combined with AND:

- `filter_tasks(pet_name="Rex")` → only Rex's tasks
- `filter_tasks(completed=False)` → only pending tasks, across all pets
- `filter_tasks(pet_name="Rex", completed=False)` → Rex's pending tasks
- `filter_tasks()` → every task

A filter left as `None` is ignored rather than matched against `None`.

### Conflict detection logic — `detect_conflicts()`

`detect_conflicts()` compares every pair of **pending, time-scheduled** tasks and returns a list of
human-readable warning strings for any that overlap — for the **same pet or across different pets**.

- Only tasks with a `scheduled_time` are checked; completed and untimed tasks are skipped.
- Overlap uses half-open `[start, start + duration)` windows, so tasks that merely touch at an
  endpoint (one ends exactly as the next begins) are **not** flagged.
- It **returns warnings instead of raising**, so the app can surface conflicts and keep running
  rather than crashing. An empty list means the day is clear.

### Recurring task logic — `next_occurrence()` and `complete_task()`

- **`Task.next_occurrence()`** returns a fresh, incomplete copy of a task dated to its next
  recurrence — **+1 day** for daily, **+7 days** for weekly — or `None` for tasks that don't repeat
  on that cadence (monthly, one-off).
- **`Scheduler.complete_task(task)`** marks the task done and, if it recurs, appends that next
  occurrence to the owning pet, so tomorrow's (or next week's) version is already waiting.
- `generate_plan(on=...)` only considers tasks **due on or before** the planning date, so a spawned
  occurrence waits for its own day instead of being re-scheduled the moment its predecessor is
  completed.

## 📸 Demo Walkthrough

Describe your app in numbered steps so a reader can follow along without watching a video:

1. <!-- Describe this step -->
2. <!-- Describe this step -->
3. <!-- Describe this step -->
4. <!-- Describe this step -->
5. <!-- Add more steps as needed -->

**Screenshot or video** *(optional)*: <!-- Insert a screenshot or link to a demo video here -->
