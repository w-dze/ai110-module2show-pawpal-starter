"""Tests for PawPal+ core behaviors."""

from pawpal_system import Pet, Priority, Task


def test_mark_complete_changes_status():
    """Calling mark_complete() flips a task from not-done to done."""
    task = Task("Feed Rex", 10, priority=Priority.HIGH)

    assert task.completed is False  # tasks start incomplete
    task.mark_complete()
    assert task.completed is True


def test_adding_task_increases_pet_task_count():
    """Adding a task to a Pet grows that pet's task list by one."""
    rex = Pet("Rex", "Beagle")

    assert len(rex.tasks) == 0
    rex.add_task(Task("Walk Rex", 30, priority=Priority.MEDIUM))
    assert len(rex.tasks) == 1
