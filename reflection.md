# PawPal+ Project Reflection

## 1. System Design

**a. Initial design**

- Briefly describe your initial UML design.
- What classes did you include, and what responsibilities did you assign to each?

- Add a pet
- See today's task
- Schedule a task

Classes: 
Pet (name, breed, what kind of care)
Owner (name, owned pets)
Task (name, duration, priority)
Scheduler (order of tasks, should be able to produce the ordered plan)

Owner → Pet (one-to-many): One owner cares for many pets. The owner has a list of pets. If the owner goes away, the pets go with them — they don't exist independently in this system.

Pet → Task (one-to-many): Each pet generates its own tasks (walk this dog, give this cat meds). One pet has many tasks; each task belongs to exactly one pet.

Owner → Task (indirect): The owner doesn't own tasks directly — they own pets, and pets have tasks. So the owner's full to-do list is "all the tasks across all my pets."

**b. Design changes**

- Did your design change during implementation?
- If yes, describe at least one change and why you made it.

Yes — I moved the task list off the Scheduler and into each Pet, so the Scheduler now retrieves tasks through Owner.all_tasks() instead of storing them itself. I did this because a task belongs to a specific pet, and it keeps each class reaching only one level down (Scheduler → Owner → Pet → Task).

---

## 2. Scheduling Logic and Tradeoffs

**a. Constraints and priorities**

- What constraints does your scheduler consider (for example: time, priority, preferences)?
- How did you decide which constraints mattered most?

My scheduler considers three constraints: the owner's daily time budget (total_available_minutes), each task's priority (LOW/MEDIUM/HIGH), and each task's duration. generate_plan() sorts pending tasks by priority first, then shortest duration as a tiebreaker, and greedily packs them until the budget runs out. There's also a due-date constraint — a plan only considers tasks due on or before the day being planned, so a recurring task's next occurrence waits for its own day.

I decided priority mattered most because the whole point is helping a busy owner do the important care first. Time budget is the hard limit that makes the problem interesting (you can't do everything), and duration is the tiebreaker so that when two tasks are equally important, doing the quicker one first fits more care into the day.

**b. Tradeoffs**

- Describe one tradeoff your scheduler makes.
- Why is that tradeoff reasonable for this scenario?

For conflict detection I scoped the check to *pending* tasks only, instead of scanning every task. The tradeoff is coverage versus relevance: checking all tasks would also flag overlaps involving tasks that are already done, but a completed task can't actually collide with anything, so those warnings would just be noise the owner can't act on. Limiting the scan to pending tasks means every conflict I surface is one the owner still has to resolve, which is reasonable here because the whole point of the warning is to help them fix a real, upcoming clash rather than review history.

---

## 3. AI Collaboration

**a. How you used AI**

- How did you use AI tools during this project (for example: design brainstorming, debugging, refactoring)?
- What kinds of prompts or questions were most helpful?

I used AI throughout, but for different jobs at different stages. Early on it helped me pressure-test my UML — talking through whether the task list belonged on the Scheduler or the Pet. During implementation I used it to write the greedy planner and the conflict-detection logic, and to add clear docstrings once the behavior was settled. Later I had it wire my Scheduler methods into the Streamlit UI (sorting, filtering, and conflict warnings shown with st.table and st.warning) and keep the README and UML in sync with the final code.

The most helpful prompts were specific and grounded in my actual files — "update the display logic to use the methods from Scheduler" or "based on the final implementation, what should change in my UML" — rather than vague "build me a scheduler" asks. Pointing at real code got answers I could actually check.

**b. Judgment and verification**

- Describe one moment where you did not accept an AI suggestion as-is.
- How did you evaluate or verify what the AI suggested?

When AI first suggested putting a tasks list on the Scheduler (matching my original UML), I didn't keep it. It duplicated state that really lived on the pets and would have let the Scheduler's copy drift out of sync with what each pet actually had. I moved the tasks onto Pet and made the Scheduler read them through Owner.all_tasks() instead.

I verified suggestions by running things rather than trusting them: I ran main.py to confirm the CLI plan matched what I expected (50 of 60 minutes, baths dropped), and I leaned on the pytest suite — 34 tests across sorting, planning, recurrence, filtering, and conflicts — to catch regressions. When the AI claimed a behavior, I looked for the test that pinned it, and wrote one if it was missing.

---

## 4. Testing and Verification

**a. What you tested**

- What behaviors did you test?
- Why were these tests important?

I tested the load-bearing scheduling behaviors: sorting (priority-then-duration, shortest-first, stable tie-breaking, no mutation of the source lists), greedy plan generation within the budget (including skipping an oversized task but still fitting a smaller one after it, the exact-budget boundary, and a zero-minute budget), recurrence (daily spawns +1 day, weekly +7, monthly/one-off spawns nothing, and the copy lands on the right pet by identity), filtering by pet and completion status, and conflict detection (same-pet and cross-pet overlaps, back-to-back tasks *not* flagged, completed/untimed tasks ignored).

These mattered because they're the parts a user actually relies on and the parts most likely to break silently — an off-by-one in the budget check or a sort that mutated the pet's real task list would produce a wrong plan without any error.

**b. Confidence**

- How confident are you that your scheduler works correctly?
- What edge cases would you test next if you had more time?

Moderate-to-high confidence in the core logic in pawpal_system.py — all 34 tests pass and they hit both the happy paths and the boundaries. I'm less confident about the app end-to-end, because app.py and main.py have no automated tests and there's no input validation yet.

If I had more time I'd test: negative or zero-duration tasks and negative budgets (right now nothing rejects them), completing an already-completed task (it currently spawns a duplicate occurrence, which I think is a bug), monthly recurrence (it silently never recurs), and tasks scheduled to run past midnight in conflict detection.

---

## 5. Reflection

**a. What went well**

- What part of this project are you most satisfied with?

I'm most satisfied with how clean the class relationships ended up. Moving tasks onto Pet and keeping the Scheduler stateless (reaching Owner → Pet → Task) meant the schedule always reflects the current state of every pet — there's no cached copy to keep in sync. Conflict detection returning warnings instead of raising is the other piece I like: the app can surface a real problem to the owner and keep running.

**b. What you would improve**

- If you had another iteration, what would you improve or redesign?

I'd add input validation (reject zero/negative durations and budgets) and fix the two known gaps — the duplicate spawn when you complete an already-completed task, and monthly recurrence never firing. I'd also reconsider the greedy planner: it fits the most *important* tasks first but doesn't maximize total minutes used, so a proper knapsack approach might fill the day better. And I'd add tests for app.py and main.py so my confidence covers the whole app, not just the core logic.

**c. Key takeaway**

- What is one important thing you learned about designing systems or working with AI on this project?

The biggest lesson was that where state *lives* shapes everything else. My first instinct was to give the Scheduler its own task list, and it took building it to see that made the Scheduler responsible for data that really belonged to the pets. Once I moved ownership to the right class, the sorting, filtering, and planning methods all got simpler. Working with AI reinforced this — it was fastest when I pointed it at real files and slowest (and occasionally wrong) when I let it guess at structure, so my job was to own the design decisions and use AI to execute and verify them.
