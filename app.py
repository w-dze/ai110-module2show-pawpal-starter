import streamlit as st

from pawpal_system import Owner, Pet, Task, Priority, Scheduler

st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="centered")

st.title("🐾 PawPal+")

st.markdown(
    """
Welcome to the PawPal+ starter app.

This file is intentionally thin. It gives you a working Streamlit app so you can start quickly,
but **it does not implement the project logic**. Your job is to design the system and build it.

Use this app as your interactive demo once your backend classes/functions exist.
"""
)

with st.expander("Scenario", expanded=True):
    st.markdown(
        """
**PawPal+** is a pet care planning assistant. It helps a pet owner plan care tasks
for their pet(s) based on constraints like time, priority, and preferences.

You will design and implement the scheduling logic and connect it to this Streamlit UI.
"""
    )

with st.expander("What you need to build", expanded=True):
    st.markdown(
        """
At minimum, your system should:
- Represent pet care tasks (what needs to happen, how long it takes, priority)
- Represent the pet and the owner (basic info and preferences)
- Build a plan/schedule for a day that chooses and orders tasks based on constraints
- Explain the plan (why each task was chosen and when it happens)
"""
    )

st.divider()

st.subheader("Owner")
owner_name = st.text_input("Owner name", value="Jordan")
owner_budget = st.number_input(
    "Daily time budget (minutes)", min_value=5, max_value=1440, value=60, step=5
)

# Create the Owner once and keep it in the session vault so it (and its pets)
# persist across re-runs. On later runs we reuse the stored instance.
if "owner" not in st.session_state:
    st.session_state.owner = Owner(name=owner_name, total_available_minutes=60)

owner = st.session_state.owner
owner.name = owner_name  # keep the stored owner in step with the inputs
owner.total_available_minutes = int(owner_budget)

st.divider()

st.subheader("Pets")
col_p1, col_p2 = st.columns(2)
with col_p1:
    new_pet_name = st.text_input("Pet name", value="Mochi")
with col_p2:
    new_pet_species = st.selectbox("Species", ["dog", "cat", "other"])

if st.button("Add pet"):
    # Attach a new pet to the owner via Owner.add_pet(). Buttons fire only on
    # the click, so plain re-runs don't create duplicate pets.
    owner.add_pet(Pet(name=new_pet_name, breed=new_pet_species))

if not owner.pets:
    st.info("No pets yet. Add one above to start scheduling tasks.")
    st.stop()

# Pick which pet to manage. Select by index so pets with the same name stay
# distinct.
pet_index = st.selectbox(
    "Manage tasks for",
    options=list(range(len(owner.pets))),
    format_func=lambda i: f"{owner.pets[i].name} ({owner.pets[i].breed})",
)
pet = owner.pets[pet_index]

st.markdown(f"### Tasks for {pet.name}")
st.caption("Add a few tasks. These feed into the scheduler below.")

col1, col2, col3 = st.columns(3)
with col1:
    task_title = st.text_input("Task title", value="Morning walk")
with col2:
    duration = st.number_input("Duration (minutes)", min_value=1, max_value=240, value=20)
with col3:
    priority = st.selectbox("Priority", ["low", "medium", "high"], index=2)

if st.button("Add task"):
    # Build a real Task and attach it to the pet via Pet.add_task().
    pet.add_task(
        Task(
            description=task_title,
            duration_minutes=int(duration),
            priority=Priority[priority.upper()],
        )
    )

if pet.tasks:
    st.write("Current tasks:")
    st.table(
        [
            {
                "title": task.description,
                "duration_minutes": task.duration_minutes,
                "priority": task.priority.name.lower(),
                "done": task.completed,
            }
            for task in pet.tasks
        ]
    )
else:
    st.info("No tasks yet. Add one above.")

st.divider()

# One scheduler over ALL of the owner's pets, reused by every section below.
scheduler = Scheduler(owner)

# Map each task back to its pet so any view can say whose task it is.
task_to_pet = {id(task): p.name for p in owner.pets for task in p.tasks}


def rows_for(tasks):
    """Turn a list of Task objects into st.table-friendly dict rows."""
    return [
        {
            "Pet": task_to_pet.get(id(task), "—"),
            "Task": task.description,
            "Minutes": task.duration_minutes,
            "Priority": task.priority.name.title(),
            "Time": task.scheduled_time.strftime("%H:%M") if task.scheduled_time else "—",
            "Done": "✅" if task.completed else "⬜",
        }
        for task in tasks
    ]


st.subheader("📋 Browse Tasks")
st.caption("Sort and filter every task across all pets using the Scheduler.")

col_sort, col_pet, col_status = st.columns(3)
with col_sort:
    sort_choice = st.selectbox("Sort by", ["Priority", "Duration"])
with col_pet:
    pet_names = ["All pets"] + [p.name for p in owner.pets]
    pet_filter = st.selectbox("Pet", pet_names)
with col_status:
    status_filter = st.selectbox("Status", ["All", "Pending", "Completed"])

# Filter first (by pet + completion), using the Scheduler's own filter method.
completed_arg = {"All": None, "Pending": False, "Completed": True}[status_filter]
pet_arg = None if pet_filter == "All pets" else pet_filter
filtered = scheduler.filter_tasks(completed=completed_arg, pet_name=pet_arg)

# Then order the filtered set with the Scheduler's sort methods.
if sort_choice == "Priority":
    order = scheduler.sort_tasks()
else:
    order = scheduler.sort_by_time()
rank = {id(task): i for i, task in enumerate(order)}
# Tasks not in the pending sort order (e.g. completed) fall to the end.
view = sorted(filtered, key=lambda task: rank.get(id(task), len(order)))

if view:
    st.table(rows_for(view))
    st.caption(f"Showing {len(view)} task(s).")
else:
    st.info("No tasks match these filters.")

st.divider()

st.subheader("⚠️ Schedule Conflicts")
st.caption("Checks for pending tasks whose scheduled times overlap.")

conflicts = scheduler.detect_conflicts()
if conflicts:
    for message in conflicts:
        st.warning(message)
else:
    st.success("No scheduling conflicts detected.")

st.divider()

st.subheader("🗓️ Build Schedule")
st.caption("Greedily packs the highest-priority tasks that fit the time budget.")

if st.button("Generate schedule"):
    plan = scheduler.generate_plan()

    if not plan:
        st.warning("No tasks fit the schedule. Add tasks or increase the time budget.")
    else:
        total = sum(task.duration_minutes for task in plan)
        st.success(
            f"Planned {len(plan)} task(s) across {len(owner.pets)} pet(s) — "
            f"{total} of {owner.total_available_minutes} minutes used."
        )
        st.table(rows_for(plan))

        used_pct = min(total / owner.total_available_minutes, 1.0)
        st.progress(used_pct, text=f"{total} / {owner.total_available_minutes} min budget")
