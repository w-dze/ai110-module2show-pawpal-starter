"""Tests for PawPal+ core behaviors.

Organized by concern:
    * Task/Pet basics
    * Sorting correctness (priority order and duration/"chronological" order)
    * Recurrence logic (completing a daily task spawns the next day's copy)
    * Plan generation (greedy packing within the time budget)
    * Conflict detection (overlapping scheduled times are flagged)
    * Filtering
"""

from datetime import date, time, timedelta

from pawpal_system import (
    Frequency,
    Owner,
    Pet,
    Priority,
    Scheduler,
    Task,
)


# --------------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------------- #
def make_scheduler(*pets: Pet, minutes: int = 1000) -> Scheduler:
    """Build an Owner holding ``pets`` and return a Scheduler over it."""
    owner = Owner("Test Owner", total_available_minutes=minutes)
    for pet in pets:
        owner.add_pet(pet)
    return Scheduler(owner)


# --------------------------------------------------------------------------- #
# Task / Pet basics
# --------------------------------------------------------------------------- #
def test_mark_complete_changes_status():
    """Calling mark_complete() flips a task from not-done to done."""
    task = Task("Feed Rex", 10, priority=Priority.HIGH)

    assert task.completed is False  # tasks start incomplete
    task.mark_complete()
    assert task.completed is True


def test_mark_incomplete_resets_status():
    """mark_incomplete() flips a done task back to not-done."""
    task = Task("Feed Rex", 10)
    task.mark_complete()

    task.mark_incomplete()
    assert task.completed is False


def test_adding_task_increases_pet_task_count():
    """Adding a task to a Pet grows that pet's task list by one."""
    rex = Pet("Rex", "Beagle")

    assert len(rex.tasks) == 0
    rex.add_task(Task("Walk Rex", 30, priority=Priority.MEDIUM))
    assert len(rex.tasks) == 1


def test_pending_tasks_excludes_completed():
    """pending_tasks() drops tasks that are already done."""
    rex = Pet("Rex", "Beagle")
    done = Task("Feed Rex", 10)
    done.mark_complete()
    rex.add_task(done)
    rex.add_task(Task("Walk Rex", 30))

    pending = rex.pending_tasks()
    assert len(pending) == 1
    assert pending[0].description == "Walk Rex"


# --------------------------------------------------------------------------- #
# Sorting correctness
# --------------------------------------------------------------------------- #
def test_sort_tasks_orders_by_priority_then_duration():
    """sort_tasks(): highest priority first, then shortest duration first."""
    rex = Pet("Rex", "Beagle")
    low = Task("Low/short", 5, priority=Priority.LOW)
    high_long = Task("High/long", 60, priority=Priority.HIGH)
    high_short = Task("High/short", 15, priority=Priority.HIGH)
    med = Task("Medium", 20, priority=Priority.MEDIUM)
    for t in (low, high_long, high_short, med):
        rex.add_task(t)

    result = make_scheduler(rex).sort_tasks()

    # HIGH before MEDIUM before LOW; within HIGH, shorter (15) before longer (60).
    assert [t.description for t in result] == [
        "High/short",
        "High/long",
        "Medium",
        "Low/short",
    ]


def test_sort_tasks_is_stable_on_full_tie():
    """Equal priority AND equal duration keep insertion order (stable sort)."""
    rex = Pet("Rex", "Beagle")
    first = Task("first", 10, priority=Priority.MEDIUM)
    second = Task("second", 10, priority=Priority.MEDIUM)
    rex.add_task(first)
    rex.add_task(second)

    result = make_scheduler(rex).sort_tasks()

    assert [t.description for t in result] == ["first", "second"]


def test_sort_tasks_excludes_completed():
    """Completed tasks never appear in the sorted pending list."""
    rex = Pet("Rex", "Beagle")
    done = Task("done", 5, priority=Priority.HIGH)
    done.mark_complete()
    rex.add_task(done)
    rex.add_task(Task("todo", 30, priority=Priority.LOW))

    result = make_scheduler(rex).sort_tasks()

    assert [t.description for t in result] == ["todo"]


def test_sort_tasks_empty_returns_empty_list():
    """No pending tasks -> empty list, not an error."""
    assert make_scheduler(Pet("Rex", "Beagle")).sort_tasks() == []


def test_sort_by_time_returns_ascending_duration_order():
    """sort_by_time(): shortest-duration task first, longest last.

    This is PawPal's "chronological"/time-based ordering: tasks come back in
    increasing order of the time they take, so quick wins surface first.
    """
    rex = Pet("Rex", "Beagle")
    for minutes in (45, 5, 30, 10):
        rex.add_task(Task(f"{minutes}min", minutes))

    result = make_scheduler(rex).sort_by_time()

    durations = [t.duration_minutes for t in result]
    assert durations == sorted(durations)  # strictly ascending
    assert durations == [5, 10, 30, 45]


def test_sort_by_time_does_not_mutate_underlying_lists():
    """Sorting returns a new list and leaves each pet's task order intact."""
    rex = Pet("Rex", "Beagle")
    rex.add_task(Task("long", 60))
    rex.add_task(Task("short", 5))

    make_scheduler(rex).sort_by_time()

    # Original insertion order preserved on the pet.
    assert [t.description for t in rex.tasks] == ["long", "short"]


# --------------------------------------------------------------------------- #
# Recurrence logic
# --------------------------------------------------------------------------- #
def test_daily_next_occurrence_advances_one_day():
    """A daily task's next occurrence is due exactly one day later, incomplete."""
    today = date(2026, 7, 8)
    task = Task("Walk", 30, frequency=Frequency.DAILY, due_date=today)
    task.mark_complete()

    nxt = task.next_occurrence()

    assert nxt is not None
    assert nxt.due_date == today + timedelta(days=1)
    assert nxt.completed is False
    assert task.completed is True  # original is left marked done


def test_weekly_next_occurrence_advances_one_week():
    """A weekly task's next occurrence is due seven days later."""
    today = date(2026, 7, 8)
    task = Task("Bath", 45, frequency=Frequency.WEEKLY, due_date=today)

    nxt = task.next_occurrence()

    assert nxt is not None
    assert nxt.due_date == today + timedelta(weeks=1)


def test_monthly_task_has_no_next_occurrence():
    """Monthly frequency does not spawn a next occurrence (known limitation)."""
    task = Task("Flea meds", 5, frequency=Frequency.MONTHLY)
    assert task.next_occurrence() is None


def test_complete_daily_task_creates_following_day_copy_on_same_pet():
    """Completing a daily task appends the next-day copy to the same pet."""
    today = date(2026, 7, 8)
    rex = Pet("Rex", "Beagle")
    walk = Task("Walk Rex", 30, frequency=Frequency.DAILY, due_date=today)
    rex.add_task(walk)
    scheduler = make_scheduler(rex)

    assert len(rex.tasks) == 1
    spawned = scheduler.complete_task(walk)

    assert len(rex.tasks) == 2
    assert spawned is not None
    assert spawned in rex.tasks
    assert spawned.completed is False
    assert spawned.due_date == today + timedelta(days=1)
    assert spawned.description == "Walk Rex"


def test_complete_monthly_task_spawns_nothing():
    """A non-recurring (monthly) task is marked done but spawns no copy."""
    rex = Pet("Rex", "Beagle")
    meds = Task("Flea meds", 5, frequency=Frequency.MONTHLY)
    rex.add_task(meds)
    scheduler = make_scheduler(rex)

    result = scheduler.complete_task(meds)

    assert result is None
    assert meds.completed is True
    assert len(rex.tasks) == 1


def test_complete_uses_identity_not_equality():
    """Value-equal tasks on two pets: the copy lands on the pet that owns it."""
    today = date(2026, 7, 8)
    rex = Pet("Rex", "Beagle")
    max_ = Pet("Max", "Beagle")
    # Two independent but value-equal tasks.
    rex_walk = Task("Walk", 30, frequency=Frequency.DAILY, due_date=today)
    max_walk = Task("Walk", 30, frequency=Frequency.DAILY, due_date=today)
    rex.add_task(rex_walk)
    max_.add_task(max_walk)
    scheduler = make_scheduler(rex, max_)

    scheduler.complete_task(rex_walk)

    # Only Rex gains the next occurrence; Max is untouched.
    assert len(rex.tasks) == 2
    assert len(max_.tasks) == 1


def test_recurrence_date_compounds_across_completions():
    """Completing the spawned copy advances the date again (+2 days total)."""
    today = date(2026, 7, 8)
    rex = Pet("Rex", "Beagle")
    walk = Task("Walk", 30, frequency=Frequency.DAILY, due_date=today)
    rex.add_task(walk)
    scheduler = make_scheduler(rex)

    tomorrow_task = scheduler.complete_task(walk)
    day_after_task = scheduler.complete_task(tomorrow_task)

    assert day_after_task.due_date == today + timedelta(days=2)


# --------------------------------------------------------------------------- #
# Plan generation (greedy packing)
# --------------------------------------------------------------------------- #
def test_generate_plan_packs_in_priority_order_within_budget():
    """Plan takes highest-priority tasks first until the budget is spent."""
    rex = Pet("Rex", "Beagle")
    rex.add_task(Task("High", 30, priority=Priority.HIGH))
    rex.add_task(Task("Medium", 30, priority=Priority.MEDIUM))
    rex.add_task(Task("Low", 30, priority=Priority.LOW))
    scheduler = make_scheduler(rex, minutes=60)  # room for two 30-min tasks

    plan = scheduler.generate_plan(on=date(2026, 7, 8))

    assert [t.description for t in plan] == ["High", "Medium"]


def test_generate_plan_skips_oversized_but_keeps_scanning():
    """A task that doesn't fit is skipped; a later smaller task can still fit."""
    rex = Pet("Rex", "Beagle")
    rex.add_task(Task("Big high", 90, priority=Priority.HIGH))
    rex.add_task(Task("Small low", 30, priority=Priority.LOW))
    scheduler = make_scheduler(rex, minutes=60)

    plan = scheduler.generate_plan(on=date(2026, 7, 8))

    # The 90-min HIGH task can't fit in 60 min, but the 30-min LOW one still does.
    assert [t.description for t in plan] == ["Small low"]


def test_generate_plan_fits_task_equal_to_budget():
    """A task whose duration exactly equals remaining minutes still fits (<=)."""
    rex = Pet("Rex", "Beagle")
    rex.add_task(Task("Exact", 60, priority=Priority.HIGH))
    scheduler = make_scheduler(rex, minutes=60)

    plan = scheduler.generate_plan(on=date(2026, 7, 8))

    assert [t.description for t in plan] == ["Exact"]


def test_generate_plan_excludes_future_dated_tasks():
    """Tasks due after the plan date are not scheduled."""
    today = date(2026, 7, 8)
    rex = Pet("Rex", "Beagle")
    rex.add_task(Task("Today", 30, priority=Priority.HIGH, due_date=today))
    rex.add_task(
        Task("Tomorrow", 30, priority=Priority.HIGH, due_date=today + timedelta(days=1))
    )
    scheduler = make_scheduler(rex)

    plan = scheduler.generate_plan(on=today)

    assert [t.description for t in plan] == ["Today"]


def test_generate_plan_with_zero_budget_is_empty():
    """A zero-minute budget yields an empty plan."""
    rex = Pet("Rex", "Beagle")
    rex.add_task(Task("Walk", 30, priority=Priority.HIGH))
    scheduler = make_scheduler(rex, minutes=0)

    assert scheduler.generate_plan(on=date(2026, 7, 8)) == []


# --------------------------------------------------------------------------- #
# Conflict detection
# --------------------------------------------------------------------------- #
def test_detect_conflicts_flags_overlapping_times_same_pet():
    """Two overlapping timed tasks on one pet produce a conflict warning."""
    rex = Pet("Rex", "Beagle")
    rex.add_task(Task("Walk", 60, scheduled_time=time(9, 0)))   # 09:00-10:00
    rex.add_task(Task("Vet", 60, scheduled_time=time(9, 30)))   # 09:30-10:30
    scheduler = make_scheduler(rex)

    warnings = scheduler.detect_conflicts()

    assert len(warnings) == 1
    assert "Rex" in warnings[0]


def test_detect_conflicts_flags_duplicate_times():
    """Two tasks scheduled at the exact same time are flagged as a conflict."""
    rex = Pet("Rex", "Beagle")
    rex.add_task(Task("Feed", 15, scheduled_time=time(8, 0)))
    rex.add_task(Task("Meds", 15, scheduled_time=time(8, 0)))
    scheduler = make_scheduler(rex)

    warnings = scheduler.detect_conflicts()

    assert len(warnings) == 1


def test_detect_conflicts_flags_across_pets():
    """Overlapping times on two different pets are flagged (owner can't be both)."""
    rex = Pet("Rex", "Beagle")
    max_ = Pet("Max", "Corgi")
    rex.add_task(Task("Walk Rex", 60, scheduled_time=time(9, 0)))
    max_.add_task(Task("Walk Max", 60, scheduled_time=time(9, 30)))
    scheduler = make_scheduler(rex, max_)

    warnings = scheduler.detect_conflicts()

    assert len(warnings) == 1
    assert "Rex" in warnings[0] and "Max" in warnings[0]


def test_detect_conflicts_touching_endpoints_do_not_conflict():
    """Back-to-back tasks (one ends as the next begins) are NOT a conflict."""
    rex = Pet("Rex", "Beagle")
    rex.add_task(Task("Walk", 60, scheduled_time=time(9, 0)))   # 09:00-10:00
    rex.add_task(Task("Feed", 30, scheduled_time=time(10, 0)))  # 10:00-10:30
    scheduler = make_scheduler(rex)

    assert scheduler.detect_conflicts() == []


def test_detect_conflicts_ignores_untimed_tasks():
    """Tasks with no scheduled_time never conflict."""
    rex = Pet("Rex", "Beagle")
    rex.add_task(Task("Walk", 60))  # no scheduled_time
    rex.add_task(Task("Feed", 60))  # no scheduled_time
    scheduler = make_scheduler(rex)

    assert scheduler.detect_conflicts() == []


def test_detect_conflicts_ignores_completed_tasks():
    """A completed task cannot collide with anything."""
    rex = Pet("Rex", "Beagle")
    done = Task("Walk", 60, scheduled_time=time(9, 0))
    done.mark_complete()
    rex.add_task(done)
    rex.add_task(Task("Vet", 60, scheduled_time=time(9, 30)))
    scheduler = make_scheduler(rex)

    assert scheduler.detect_conflicts() == []


def test_detect_conflicts_three_way_overlap_reports_each_pair():
    """Three mutually overlapping tasks yield one warning per pair (3 total)."""
    rex = Pet("Rex", "Beagle")
    rex.add_task(Task("A", 60, scheduled_time=time(9, 0)))
    rex.add_task(Task("B", 60, scheduled_time=time(9, 15)))
    rex.add_task(Task("C", 60, scheduled_time=time(9, 30)))
    scheduler = make_scheduler(rex)

    assert len(scheduler.detect_conflicts()) == 3


# --------------------------------------------------------------------------- #
# Filtering
# --------------------------------------------------------------------------- #
def test_filter_by_pet_name():
    """filter_tasks(pet_name=...) returns only that pet's tasks."""
    rex = Pet("Rex", "Beagle")
    max_ = Pet("Max", "Corgi")
    rex.add_task(Task("Walk Rex", 30))
    max_.add_task(Task("Walk Max", 30))
    scheduler = make_scheduler(rex, max_)

    result = scheduler.filter_tasks(pet_name="Rex")

    assert [t.description for t in result] == ["Walk Rex"]


def test_filter_by_completion_status():
    """filter_tasks(completed=True) returns only done tasks."""
    rex = Pet("Rex", "Beagle")
    done = Task("done", 10)
    done.mark_complete()
    rex.add_task(done)
    rex.add_task(Task("todo", 10))
    scheduler = make_scheduler(rex)

    assert [t.description for t in scheduler.filter_tasks(completed=True)] == ["done"]
    assert [t.description for t in scheduler.filter_tasks(completed=False)] == ["todo"]


def test_filter_combines_filters_with_and():
    """Passing both filters keeps only tasks matching both."""
    rex = Pet("Rex", "Beagle")
    max_ = Pet("Max", "Corgi")
    rex_done = Task("Rex done", 10)
    rex_done.mark_complete()
    rex.add_task(rex_done)
    rex.add_task(Task("Rex todo", 10))
    max_done = Task("Max done", 10)
    max_done.mark_complete()
    max_.add_task(max_done)
    scheduler = make_scheduler(rex, max_)

    result = scheduler.filter_tasks(completed=True, pet_name="Rex")

    assert [t.description for t in result] == ["Rex done"]


def test_filter_no_args_returns_all_tasks():
    """No filters returns every task, completed or not."""
    rex = Pet("Rex", "Beagle")
    done = Task("done", 10)
    done.mark_complete()
    rex.add_task(done)
    rex.add_task(Task("todo", 10))
    scheduler = make_scheduler(rex)

    assert len(scheduler.filter_tasks()) == 2


def test_filter_unknown_pet_returns_empty():
    """Filtering by a name no pet has returns an empty list."""
    rex = Pet("Rex", "Beagle")
    rex.add_task(Task("Walk", 30))
    scheduler = make_scheduler(rex)

    assert scheduler.filter_tasks(pet_name="Nobody") == []
