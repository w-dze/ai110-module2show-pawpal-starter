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

**b. Tradeoffs**

- Describe one tradeoff your scheduler makes.
- Why is that tradeoff reasonable for this scenario?

---

## 3. AI Collaboration

**a. How you used AI**

- How did you use AI tools during this project (for example: design brainstorming, debugging, refactoring)?
- What kinds of prompts or questions were most helpful?

**b. Judgment and verification**

- Describe one moment where you did not accept an AI suggestion as-is.
- How did you evaluate or verify what the AI suggested?

---

## 4. Testing and Verification

**a. What you tested**

- What behaviors did you test?
- Why were these tests important?

**b. Confidence**

- How confident are you that your scheduler works correctly?
- What edge cases would you test next if you had more time?

---

## 5. Reflection

**a. What went well**

- What part of this project are you most satisfied with?

**b. What you would improve**

- If you had another iteration, what would you improve or redesign?

**c. Key takeaway**

- What is one important thing you learned about designing systems or working with AI on this project?
