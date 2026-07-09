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
from enum import Enum, IntEnum


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

    def mark_complete(self) -> None:
        """Mark this task as done for the day."""
        self.completed = True

    def mark_incomplete(self) -> None:
        """Reset this task back to not-done (e.g. for a new day)."""
        self.completed = False


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

    def generate_plan(self) -> list[Task]:
        """Return the priority-sorted tasks that fit within the owner's time budget."""
        remaining = self.owner.total_available_minutes
        plan: list[Task] = []
        for task in self.sort_tasks():
            if task.duration_minutes <= remaining:
                plan.append(task)
                remaining -= task.duration_minutes
        return plan
