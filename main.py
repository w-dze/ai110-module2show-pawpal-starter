"""Demo script for PawPal+.

Creates an owner with two pets, gives them a few tasks, and prints
today's schedule to the terminal.
"""

from datetime import datetime, timedelta

from pawpal_system import Frequency, Owner, Pet, Priority, Scheduler, Task


def main() -> None:
    # An owner with a 60-minute daily care budget.
    owner = Owner("Wendy", total_available_minutes=60)

    # One dog and one cat.
    rex = Pet("Rex", "Beagle", care_needs=["food", "exercise"])
    bella = Pet("Bella", "Tabby Cat", care_needs=["food", "grooming"])
    owner.add_pet(rex)
    owner.add_pet(bella)

    # Three tasks per pet: food, bath, and play. Added deliberately out of
    # order (long/low-priority first, quick/high-priority last) so the
    # sorting below has something real to reorder.
    rex.add_task(Task("Bathe Rex", 30, Frequency.WEEKLY, Priority.LOW))
    rex.add_task(Task("Play with Rex", 20, Frequency.DAILY, Priority.MEDIUM))
    rex.add_task(Task("Feed Rex", 10, Frequency.DAILY, Priority.HIGH))

    bella.add_task(Task("Bathe Bella", 25, Frequency.WEEKLY, Priority.LOW))
    bella.add_task(Task("Play with Bella", 15, Frequency.DAILY, Priority.MEDIUM))
    bella.add_task(Task("Feed Bella", 5, Frequency.DAILY, Priority.HIGH))

    # Build today's schedule.
    scheduler = Scheduler(owner)
    plan = scheduler.generate_plan()

    # Lay the plan out on a timeline starting at 08:00, back to back.
    clock = datetime(2026, 1, 1, 8, 0)

    print(f"Daily plan for {owner.name}:")
    total = 0
    for task in plan:
        start = clock.strftime("%H:%M")
        print(
            f"  {start} — {task.description} "
            f"({task.duration_minutes} min) [priority: {task.priority.name.lower()}]"
        )
        clock += timedelta(minutes=task.duration_minutes)
        total += task.duration_minutes

    print(f"\n  Total planned time: {total} of {owner.total_available_minutes} minutes")

    # Show tasks added out of order re-sorted shortest-first by duration.
    print("\nAll tasks sorted by time (shortest first):")
    for task in scheduler.sort_by_time():
        print(f"  {task.duration_minutes:>2} min — {task.description}")

    # Filter down to a single pet's tasks.
    print("\nFiltered to Rex's tasks only:")
    for task in scheduler.filter_tasks(pet_name="Rex"):
        print(f"  {task.description}")

    # Filter by completion status. Mark one task done first so the split shows.
    rex.tasks[-1].mark_complete()  # "Feed Rex"
    print("\nStill pending across all pets:")
    for task in scheduler.filter_tasks(completed=False):
        print(f"  {task.description}")
    print("\nAlready completed:")
    for task in scheduler.filter_tasks(completed=True):
        print(f"  {task.description}")


if __name__ == "__main__":
    main()
