"""PawPal+ core system.

Class skeletons generated from diagrams/uml.mmd, now with core logic.

Design:
    Task    -- a single care activity (the atomic unit of work).
    Pet     -- pet details + the list of tasks that pet needs.
    Owner   -- manages multiple pets and exposes their tasks.
    Scheduler -- the brain: retrieves, organizes, and plans tasks across pets.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, time, timedelta
from enum import Enum, IntEnum
from itertools import combinations


class Priority(IntEnum):
    """Task priority. IntEnum so tasks sort naturally (HIGH first)."""

    LOW = 1
    MEDIUM = 2
    HIGH = 3


class Frequency(Enum):
    """How often a task recurs."""

    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"


@dataclass
class Task:
    """A single care activity (walk, feeding, meds, etc.)."""

    description: str
    duration_minutes: int
    frequency: Frequency = Frequency.DAILY
    priority: Priority = Priority.MEDIUM
    completed: bool = False
    due_date: date = field(default_factory=date.today)
    scheduled_time: time | None = None

    def mark_complete(self) -> None:
        """Mark this task as done for the day."""
        self.completed = True

    def mark_incomplete(self) -> None:
        """Reset this task back to not-done (e.g. for a new day)."""
        self.completed = False

    def next_occurrence(self) -> Task | None:
        """Return a fresh, incomplete copy of this task for its next recurrence.

        Looks up a recurrence step by frequency (daily -> +1 day, weekly ->
        +7 days) and, if one applies, builds a new ``Task`` with the same
        description, duration, frequency, and priority but ``completed=False``
        and ``due_date`` advanced by that step. The original task is left
        untouched.

        Returns:
            A new ``Task`` for the next occurrence, or ``None`` for
            frequencies that don't repeat on this cadence (monthly, one-off).
        """
        step = {
            Frequency.DAILY: timedelta(days=1),
            Frequency.WEEKLY: timedelta(weeks=1),
        }.get(self.frequency)
        if step is None:
            return None
        return Task(
            description=self.description,
            duration_minutes=self.duration_minutes,
            frequency=self.frequency,
            priority=self.priority,
            due_date=self.due_date + step,
        )


@dataclass
class Pet:
    """A pet the owner cares for, plus the tasks that pet needs."""

    name: str
    breed: str
    care_needs: list[str] = field(default_factory=list)
    tasks: list[Task] = field(default_factory=list)

    def add_task(self, task: Task) -> None:
        """Attach a care task to this pet."""
        self.tasks.append(task)

    def pending_tasks(self) -> list[Task]:
        """Return this pet's tasks that are not yet completed."""
        return [task for task in self.tasks if not task.completed]


@dataclass
class Owner:
    """The pet owner: manages multiple pets and their daily time budget."""

    name: str
    total_available_minutes: int
    pets: list[Pet] = field(default_factory=list)

    def add_pet(self, pet: Pet) -> None:
        """Register a pet under this owner."""
        self.pets.append(pet)

    def all_tasks(self) -> list[Task]:
        """Return every task across all of this owner's pets."""
        return [task for pet in self.pets for task in pet.tasks]


@dataclass
class Scheduler:
    """Orders tasks and builds a daily plan within the owner's time budget.

    The scheduler owns no tasks itself — it retrieves them from the owner's
    pets, so the plan always reflects the current state of every pet.
    """

    owner: Owner

    def all_tasks(self) -> list[Task]:
        """Gather every task across all of the owner's pets."""
        return self.owner.all_tasks()

    def pending_tasks(self) -> list[Task]:
        """Gather only the not-yet-completed tasks across all pets."""
        return [task for task in self.all_tasks() if not task.completed]

    def sort_tasks(self) -> list[Task]:
        """Return pending tasks by priority (highest first), then shortest first."""
        return sorted(
            self.pending_tasks(),
            key=lambda task: (-task.priority, task.duration_minutes),
        )

    def sort_by_time(self) -> list[Task]:
        """Return pending tasks ordered by duration (shortest first).

        Sorts the pending tasks by ``duration_minutes`` ascending (a stable
        O(n log n) sort). Sorting by time lets the owner knock out quick tasks
        first and see how many fit before committing to the longer ones.

        Returns:
            A new list of the pending tasks, shortest duration first. Does not
            mutate the underlying pet task lists.
        """
        return sorted(self.pending_tasks(), key=lambda task: task.duration_minutes)

    def filter_tasks(
        self, *, completed: bool | None = None, pet_name: str | None = None
    ) -> list[Task]:
        """Return tasks narrowed by completion status and/or pet name.

        Walks every pet's task list once, keeping a task only if it satisfies
        each supplied filter. Both filters are optional and independent and are
        combined with AND: pass ``completed`` to keep only done/not-done tasks,
        ``pet_name`` to keep only one pet's tasks, both to combine them, or
        neither to return every task. A filter left as ``None`` is ignored
        rather than matched against ``None``.

        Args:
            completed: If set, keep only tasks whose ``completed`` flag equals
                this value.
            pet_name: If set, keep only tasks belonging to a pet with this
                exact name (matched by name, so same-named pets both match).

        Returns:
            A new list of the matching tasks in pet-then-insertion order.
        """
        tasks: list[Task] = []
        for pet in self.owner.pets:
            if pet_name is not None and pet.name != pet_name:
                continue
            for task in pet.tasks:
                if completed is not None and task.completed != completed:
                    continue
                tasks.append(task)
        return tasks

    def complete_task(self, task: Task) -> Task | None:
        """Mark ``task`` done and, if it recurs, spawn its next occurrence.

        Marks the task complete, then asks it for a ``next_occurrence()``. If
        the task recurs (daily or weekly), the scheduler locates the owning pet
        by identity — scanning each pet's list with ``is`` rather than ``==`` so
        two pets holding value-equal tasks aren't confused — and appends the
        fresh copy there, so tomorrow's (or next week's) version is already
        waiting.

        Args:
            task: The task to complete. Expected to belong to one of this
                owner's pets; it is mutated in place to ``completed=True``.

        Returns:
            The newly appended next-occurrence ``Task``, or ``None`` if the
            task doesn't recur or isn't owned by any of this owner's pets (in
            which case it is still marked complete).
        """
        task.mark_complete()
        next_task = task.next_occurrence()
        if next_task is None:
            return None
        for pet in self.owner.pets:
            # Identity, not equality: two pets can hold value-equal tasks.
            if any(existing is task for existing in pet.tasks):
                pet.add_task(next_task)
                return next_task
        return None

    def generate_plan(self, on: date | None = None) -> list[Task]:
        """Return the priority-sorted tasks that fit within the owner's time budget.

        A greedy pack: walk the pending tasks in priority order (highest first,
        then shortest, via :meth:`sort_tasks`) and take each one whose duration
        still fits the remaining minutes, skipping any that don't. Only tasks
        due on or before ``on`` are considered, so a next occurrence spawned by
        :meth:`complete_task` waits for its own day instead of being
        re-scheduled the moment its predecessor is completed. Greedy is optimal
        for "fit the most important tasks first" but does not maximize total
        minutes used the way a full knapsack search would.

        Args:
            on: The date to plan for; defaults to today. Tasks with a
                ``due_date`` after this are excluded.

        Returns:
            A new list of the chosen tasks in the order they were packed. May
            be empty if nothing is due or fits the budget.
        """
        on = on or date.today()
        remaining = self.owner.total_available_minutes
        plan: list[Task] = []
        for task in self.sort_tasks():
            if task.due_date > on:
                continue
            if task.duration_minutes <= remaining:
                plan.append(task)
                remaining -= task.duration_minutes
        return plan

    @staticmethod
    def _window(task: Task) -> tuple[int, int]:
        """Return a task's occupied time as a half-open ``[start, end)`` window.

        Converts ``scheduled_time`` to minutes since midnight and adds the
        duration. Working in integer minutes lets conflict checks use plain
        comparisons instead of ``datetime`` arithmetic.

        Args:
            task: A task whose ``scheduled_time`` is set (not ``None``).

        Returns:
            A ``(start, end)`` pair of minutes since midnight, end exclusive.
        """
        start = task.scheduled_time.hour * 60 + task.scheduled_time.minute
        return start, start + task.duration_minutes

    @staticmethod
    def _fmt(minutes: int) -> str:
        """Format a minutes-since-midnight value as a ``HH:MM`` string.

        Args:
            minutes: Minutes since midnight (may exceed 1440 for windows that
                run past midnight; the hours field simply grows).

        Returns:
            A zero-padded ``"HH:MM"`` string.
        """
        return f"{minutes // 60:02d}:{minutes % 60:02d}"

    def detect_conflicts(self) -> list[str]:
        """Return warning messages for tasks whose scheduled times overlap.

        Collects the pending, timed tasks (completed tasks are done and can't
        collide; untimed tasks have no window), then compares every pair once
        with :func:`itertools.combinations`. Two tasks conflict when their
        half-open ``[start, start + duration)`` windows overlap — tested as
        ``start_a < end_b and start_b < end_a``, so tasks that merely touch at
        an endpoint don't count. A conflict is reported whether the tasks
        belong to the same pet or to two different pets, with wording tailored
        to each case. This is a lightweight O(n^2) pairwise scan; it never
        raises, so callers can surface the warnings without crashing.

        Returns:
            A list of human-readable warning strings, one per overlapping pair.
            Empty when no pending timed tasks overlap.
        """
        timed = [
            (pet.name, task)
            for pet in self.owner.pets
            for task in pet.tasks
            if task.scheduled_time is not None and not task.completed
        ]

        warnings: list[str] = []
        for (pet_a, task_a), (pet_b, task_b) in combinations(timed, 2):
            start_a, end_a = self._window(task_a)
            start_b, end_b = self._window(task_b)
            # Half-open intervals: touching (one ends exactly as the other
            # starts) is fine; only genuine overlap is a conflict.
            if start_a < end_b and start_b < end_a:
                window_a = f"{self._fmt(start_a)}-{self._fmt(end_a)}"
                window_b = f"{self._fmt(start_b)}-{self._fmt(end_b)}"
                if pet_a == pet_b:
                    warnings.append(
                        f"⚠️ Conflict for {pet_a}: "
                        f"'{task_a.description}' ({window_a}) overlaps "
                        f"'{task_b.description}' ({window_b})."
                    )
                else:
                    warnings.append(
                        f"⚠️ Conflict: {pet_a}'s '{task_a.description}' ({window_a}) "
                        f"overlaps {pet_b}'s '{task_b.description}' ({window_b})."
                    )
        return warnings
