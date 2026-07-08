"""PawPal+ core system.

Class skeletons generated from diagrams/uml.mmd.
No scheduling logic yet — fill in the method bodies incrementally.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import IntEnum


class Priority(IntEnum):
    """Task priority. IntEnum so tasks sort naturally (HIGH first)."""

    LOW = 1
    MEDIUM = 2
    HIGH = 3


@dataclass
class Pet:
    """A pet the owner cares for."""

    name: str
    breed: str
    care_needs: list[str] = field(default_factory=list)


@dataclass
class Owner:
    """The pet owner and their daily time budget."""

    name: str
    total_available_minutes: int


@dataclass
class Task:
    """A single care task (walk, feeding, meds, etc.)."""

    name: str
    duration_minutes: int
    priority: Priority


@dataclass
class Scheduler:
    """Orders tasks and builds a daily plan within the owner's time budget."""

    owner: Owner
    tasks: list[Task] = field(default_factory=list)

    def add_task(self, task: Task) -> None:
        """Add a task to the list to be scheduled."""
        raise NotImplementedError

    def sort_tasks(self) -> list[Task]:
        """Return tasks ordered by priority (highest first)."""
        raise NotImplementedError

    def generate_plan(self) -> list[Task]:
        """Return the ordered tasks that fit within the owner's available time."""
        raise NotImplementedError
