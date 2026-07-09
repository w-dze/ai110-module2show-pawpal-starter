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

    # Three tasks per pet: food, bath, and play — each a different length.
    rex.add_task(Task("Feed Rex", 10, Frequency.DAILY, Priority.HIGH))
    rex.add_task(Task("Play with Rex", 20, Frequency.DAILY, Priority.MEDIUM))
    rex.add_task(Task("Bathe Rex", 30, Frequency.WEEKLY, Priority.LOW))

    bella.add_task(Task("Feed Bella", 5, Frequency.DAILY, Priority.HIGH))
    bella.add_task(Task("Play with Bella", 15, Frequency.DAILY, Priority.MEDIUM))
    bella.add_task(Task("Bathe Bella", 25, Frequency.WEEKLY, Priority.LOW))

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


if __name__ == "__main__":
    main()
