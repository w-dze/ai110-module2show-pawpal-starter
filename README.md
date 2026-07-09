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

# Run just the PawPal+ tests, verbosely:
pytest tests/test_pawpal.py -v
```

### What the tests cover

The suite in [`tests/test_pawpal.py`](tests/test_pawpal.py) has **34 tests** across every core
scheduling behavior — happy paths *and* the tricky edge cases:

- **Task & pet basics** — completing/reopening tasks and `pending_tasks()` filtering.
- **Sorting** — priority-then-duration ordering, stable tie-breaking, duration-only ("shortest
  first") ordering, exclusion of completed tasks, empty lists, and no mutation of the source lists.
- **Recurrence** — completing a daily task spawns a fresh incomplete copy due the next day (+1 day);
  weekly advances +7 days; monthly/one-off spawns nothing; the copy lands on the owning pet by
  identity; dates compound across repeated completions.
- **Plan generation** — greedy packing in priority order within the time budget, skipping an
  oversized task while still fitting a smaller later one, the exact-budget boundary, exclusion of
  future-dated tasks, and a zero-minute budget.
- **Conflict detection** — overlapping times flagged for the same pet and across pets, duplicate
  start times flagged, back-to-back (touching) tasks *not* flagged, untimed/completed tasks ignored,
  and a three-way overlap reported as its three pairwise warnings.
- **Filtering** — by pet name, by completion status, both combined (AND), no filters, and an unknown
  pet name.

### Sample test output

```
$ pytest tests/test_pawpal.py
============================= test session starts ==============================
platform darwin -- Python 3.13.5, pytest-9.1.1, pluggy-1.5.0
rootdir: /Users/zhuoerdu/AI110/ai110-module2show-pawpal-starter
plugins: anyio-4.13.0
collected 34 items

tests/test_pawpal.py ..................................                  [100%]

============================== 34 passed in 0.08s ==============================
```

### Confidence level

**Moderate-to-high confidence in the core scheduling logic.** All 34 tests pass, and they exercise
the load-bearing behaviors (sorting, recurrence, greedy planning, conflict detection) at both their
happy paths and their boundaries, so the logic that ships today is well-pinned against regressions.

Two caveats keep this short of *high*:

- **Known gaps, not bugs found:** monthly/one-off tasks silently never recur, and completing an
  already-completed task spawns a duplicate occurrence. These are covered by tests that document the
  *current* behavior — they are product decisions still to be made, not verified-correct features.
- **Untested surface:** the Streamlit UI (`app.py`) and CLI (`main.py`) have no automated tests, and
  there is no input validation (e.g. negative or zero durations). Confidence applies to
  `pawpal_system.py`, not the app end-to-end.

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

### The interface

Launch the app with `streamlit run app.py`. The page is a single scrolling form, top to bottom:

- **Owner** — set the owner's name and a **daily time budget** (in minutes). The budget is the hard
  ceiling the scheduler packs tasks into.
- **Pets** — name a pet, pick a species, and **Add pet**. You can register as many pets as you like;
  a dropdown lets you switch which pet you're managing.
- **Tasks** — for the selected pet, enter a title, duration, and priority, then **Add task**. The
  pet's current tasks show in a table as you go.
- **📋 Browse Tasks** — sort every task across all pets by **Priority** or **Duration**, and filter
  by **pet** and by **status** (All / Pending / Completed). Results render as a clean table.
- **⚠️ Schedule Conflicts** — a live check that warns when two pending, time-scheduled tasks overlap.
- **🗓️ Build Schedule** — **Generate schedule** runs the greedy planner and shows the chosen tasks
  plus a progress bar of budget used.

### An example workflow

1. Set the owner to *Wendy* with a **60-minute** budget.
2. **Add a pet** — *Rex* (dog). Add a second pet — *Bella* (cat).
3. Select *Rex* and **add tasks**: "Feed Rex" (10 min, high), "Play with Rex" (20 min, medium),
   "Bathe Rex" (30 min, low). Switch to *Bella* and add her tasks the same way.
4. Open **📋 Browse Tasks**, sort by **Priority** — the high-priority feedings jump to the top,
   with shorter tasks breaking ties. Filter **Pet → Rex** to see just Rex's three tasks.
5. Click **Generate schedule**. The planner fills the 60-minute budget with the highest-priority
   tasks that fit and skips the two long baths, then shows a *50 / 60 min* progress bar.

### Key Scheduler behaviors shown

- **Priority-first sorting** — `sort_tasks()` orders by priority (highest first), then shortest
  duration, which is exactly the order the plan packs in.
- **Shortest-first sorting** — `sort_by_time()` gives a "quick wins" view ordered purely by duration.
- **Filtering** — `filter_tasks()` narrows by pet name and/or completion status (combined with AND).
- **Greedy planning within a budget** — `generate_plan()` takes the most important tasks that fit
  and skips oversized ones, so the 30- and 25-minute baths are dropped when only 60 minutes exist.
- **Conflict warnings** — `detect_conflicts()` flags overlapping time slots instead of crashing.

### Sample CLI output

Running `python main.py` exercises the same logic on the command line:

```
$ python main.py
Daily plan for Wendy:
  08:00 — Feed Bella (5 min) [priority: high]
  08:05 — Feed Rex (10 min) [priority: high]
  08:15 — Play with Bella (15 min) [priority: medium]
  08:30 — Play with Rex (20 min) [priority: medium]

  Total planned time: 50 of 60 minutes

All tasks sorted by time (shortest first):
   5 min — Feed Bella
  10 min — Feed Rex
  15 min — Play with Bella
  20 min — Play with Rex
  25 min — Bathe Bella
  30 min — Bathe Rex

Filtered to Rex's tasks only:
  Bathe Rex
  Play with Rex
  Feed Rex

Still pending across all pets:
  Bathe Rex
  Play with Rex
  Bathe Bella
  Play with Bella
  Feed Bella

Already completed:
  Feed Rex
```
