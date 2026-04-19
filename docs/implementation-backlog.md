# SkillRadar Dynamic Implementation Backlog

## Purpose
This document is the execution control file for building the app.

It is intentionally designed to be:
- dynamic
- agent-friendly
- updated after every task
- safe for one-task-at-a-time execution

The executor must not treat this as a static checklist. It is a living plan.

## Execution Rules

### Rule 1: Only One Task In Progress At A Time
- Exactly one task may have status `IN_PROGRESS`.
- No second build task should start until the current task is:
  - implemented
  - tested
  - documented in this file

### Rule 2: Every Completed Task Must End With Verification
- A task is not `DONE` until the executor has run the relevant verification.
- Verification may include:
  - unit tests
  - integration tests
  - manual UI verification
  - schema validation
  - lint/typecheck
- If testing is partially blocked, the executor must record:
  - what was tested
  - what could not be tested
  - why

### Rule 3: The Executor Must Update This File After Every Task
- After finishing a task, the executor must update:
  - task status
  - implementation notes
  - verification notes
  - new insights
  - newly discovered tasks
  - changed priorities if needed

### Rule 3A: Every Finished Task Must End With Git Commits
- Each completed task must conclude with one or more commits as appropriate.
- Commits should be scoped so they are reviewable and map cleanly to the task outcome.
- Avoid mixing unrelated task work in the same commit.
- If the task is incomplete or unverified, do not create a misleading "done" commit.

### Rule 3B: User Review Happens Before Push
- After task completion and commits, the executor must stop for user review.
- The user will review commits before anything is pushed to `main`.
- The executor must incorporate user suggestions through follow-up changes and commits before any push is attempted.

### Rule 4: Missed Requirements Must Be Folded Back Into The Plan
- If the executor discovers:
  - a missed requirement
  - a hidden dependency
  - a better decomposition
  - a quality gap
  - a design mismatch with `docs/requirements.md`
- then the executor must update this backlog before stopping.

### Rule 5: Requirements Remain The Source Of Truth
- `docs/requirements.md` is the user-requirement authority.
- `docs/solution.md` is the recommended design baseline.
- If implementation reveals a conflict:
  - do not silently ignore it
  - record it here under `New Insights / Plan Updates`

### Rule 6: Preserve Momentum
- Prefer the smallest next task that creates a durable foundation.
- Avoid starting broad work that spans too many layers at once.
- Prefer vertical slices only when they are small and testable.

## Status Legend
- `TODO`: Not started
- `IN_PROGRESS`: Currently being executed
- `BLOCKED`: Cannot continue without resolving a dependency or decision
- `DONE`: Implemented and verified to the extent possible
- `CANCELLED`: No longer needed

## Executor Loop
The executor should follow this loop for every run:

1. Read:
   - `docs/requirements.md`
   - `docs/solution.md`
   - this file
2. Find the highest-priority task with status `TODO` that is unblocked.
3. Change that task to `IN_PROGRESS`.
4. Implement only that task's scope.
5. Test the task.
6. Update this file:
   - mark the task `DONE` or `BLOCKED`
   - record verification
   - record learnings
   - add or reorder tasks if new work was discovered
7. Create one or more clean commits for the task.
8. Stop cleanly and wait for user review before any push.

## Priority Model
- `P0`: Foundation or blocker for almost everything else
- `P1`: Core MVP capability
- `P2`: Important quality, usability, or maintainability improvement
- `P3`: Nice to have / later enhancement

## Backlog Structure
Each task should preserve this structure:

```md
### TASK-XXX - Title
- Status: TODO
- Priority: P1
- Depends on: TASK-AAA, TASK-BBB
- Goal: One sentence outcome
- Scope:
  - concrete item
  - concrete item
- Out of scope:
  - explicit non-goals
- Implementation Notes:
  - update after execution
- Verification:
  - update after execution
- Commits:
  - update after execution
- New Insights / Plan Updates:
  - update after execution
```

## Current Build Strategy
Build in this order:
- backend and frontend foundation first
- persistence next
- minimal UI shell next
- pipeline interfaces next
- lesson generation orchestration next
- retrieval and agent wiring next
- reader/library usability next
- quality hardening after that

This order is recommended, not immutable. If execution reveals a better sequence, the executor should update the plan.

## Active Task
- Current active task: None

## Tasks

### TASK-001 - Initialize App Skeleton
- Status: DONE
- Priority: P0
- Depends on: None
- Goal: Create the base frontend and backend application structure so future tasks have stable places to land.
- Scope:
  - scaffold the frontend project
  - scaffold the Python 3 FastAPI backend project
  - establish a minimal folder structure aligned with `docs/solution.md`
  - add package management and base scripts
  - ensure both services can boot locally
- Out of scope:
  - full feature implementation
  - real retrieval or AI integration
- Implementation Notes:
  - Added a minimal Next.js 15 App Router frontend scaffold under `frontend/` with a simple landing page and global styling that establishes the generate/read/library product direction without overinvesting in UI.
  - Added a FastAPI backend scaffold under `backend/` with package metadata, an application entrypoint, and starter health/API routes.
  - Added root-level workspace scripts in `package.json` and a `Makefile` for common frontend/backend install, dev, lint, build, and test flows.
  - Added a backend smoke test suite for the initial API routes.
- Verification:
  - `npm install`
  - `make backend-install`
  - `npm run frontend:typecheck`
  - `npm run frontend:lint`
  - `npm run frontend:build`
  - `make backend-lint`
  - `make backend-test`
  - Booted the backend with `uvicorn` and verified `GET /health` returned `{"status":"ok"}`.
  - Booted the frontend with `next dev` and verified `GET /` returned `HTTP/1.1 200 OK`.
- Commits:
  - `1b12061` - Initialize SkillRadar app skeleton
- New Insights / Plan Updates:
  - Dependency installation was required even for the initial skeleton, so user approval was needed before proceeding with package setup.
  - Root workspace `node_modules/` should be ignored because npm workspaces hoist dependencies there.

### TASK-002 - Define Data Schema And Persistence Layer
- Status: TODO
- Priority: P0
- Depends on: TASK-001
- Goal: Define durable storage for lessons, sources, generation requests, and user profile.
- Scope:
  - add PostgreSQL setup
  - define schema for `user_profile`, `lessons`, `lesson_sources`, `generation_requests`
  - add migration flow for the Python backend
  - add basic persistence utilities
- Out of scope:
  - full CRUD UI
  - feedback analytics unless it naturally fits the schema
- Implementation Notes:
  - Pending
- Verification:
  - Pending
- New Insights / Plan Updates:
  - Pending

### TASK-003 - Seed User Profile From Provided Resume Context
- Status: TODO
- Priority: P1
- Depends on: TASK-002
- Goal: Make personalization possible from the start by storing a first-pass user profile.
- Scope:
  - create a seed for the user profile using confirmed resume details
  - represent skills, experience themes, and topic affinities
  - avoid inventing preferences that were not stated
- Out of scope:
  - profile editing UI
- Implementation Notes:
  - Pending
- Verification:
  - Pending
- New Insights / Plan Updates:
  - Pending

### TASK-004 - Build Minimal Application Shell And Navigation
- Status: TODO
- Priority: P1
- Depends on: TASK-001
- Goal: Create a simple UI shell for generation, lesson reading, and lesson history.
- Scope:
  - add top-level layout
  - add generate view
  - add lesson reader route
  - add lesson library route
  - keep styling intentionally minimal
- Out of scope:
  - polished UI
  - advanced search UX
- Implementation Notes:
  - Pending
- Verification:
  - Pending
- New Insights / Plan Updates:
  - Pending

### TASK-005 - Implement Lesson Generation Request Flow
- Status: TODO
- Priority: P1
- Depends on: TASK-002, TASK-004
- Goal: Support submitting lesson-generation requests from the UI in the three required modes.
- Scope:
  - add mode selector
  - add phrase input for phrase-seeded generation
  - add generate action
  - create generation request records
  - show generated lesson or generation result state
- Out of scope:
  - high-quality lesson generation internals
- Implementation Notes:
  - Pending
- Verification:
  - Pending
- New Insights / Plan Updates:
  - Pending

### TASK-006 - Add Active Lesson State Management
- Status: TODO
- Priority: P1
- Depends on: TASK-002, TASK-004
- Goal: Support one active lesson at a time so follow-up generation has a reliable anchor.
- Scope:
  - persist active lesson selection
  - provide mark-active action
  - ensure only one lesson is active at a time
  - handle no-active-lesson fallback behavior
- Out of scope:
  - progress tracking within a lesson
- Implementation Notes:
  - Pending
- Verification:
  - Pending
- New Insights / Plan Updates:
  - Pending

### TASK-007 - Implement Lesson Save And Library Access
- Status: TODO
- Priority: P1
- Depends on: TASK-002, TASK-004
- Goal: Let the user save generated lessons and access old lessons from the app.
- Scope:
  - save action
  - library list view
  - display lesson status and metadata
  - support opening older lessons
- Out of scope:
  - complex filtering or pagination unless needed
- Implementation Notes:
  - Pending
- Verification:
  - Pending
- New Insights / Plan Updates:
  - Pending

### TASK-008 - Define Agent Abstractions For Topic Planning And Lesson Composition
- Status: TODO
- Priority: P1
- Depends on: TASK-001, TASK-002
- Goal: Create stable interfaces so the app can use an AI agent without coupling the whole app to a single provider.
- Scope:
  - define provider interfaces
  - define topic-planner input/output types
  - define lesson-composer input/output types
  - add mock implementation for development
- Out of scope:
  - production provider integration if not yet configured
- Implementation Notes:
  - Pending
- Verification:
  - Pending
- New Insights / Plan Updates:
  - Pending

### TASK-009 - Implement Modular Retrieval Pipeline Skeleton
- Status: TODO
- Priority: P1
- Depends on: TASK-008
- Goal: Create the grounded retrieval workflow as independently upgradable stages.
- Scope:
  - define search/discovery interface
  - define content fetching interface
  - define content extraction interface
  - define ranking interface
  - define evidence packaging interface
  - support a mocked or stubbed pipeline first if external integrations are unavailable
- Out of scope:
  - full generalized crawler
- Implementation Notes:
  - Pending
- Verification:
  - Pending
- New Insights / Plan Updates:
  - Pending

### TASK-010 - Generate Structured Lesson Drafts From Grounded Inputs
- Status: TODO
- Priority: P1
- Depends on: TASK-005, TASK-008, TASK-009
- Goal: Produce lessons in the required structured format with metadata and citations.
- Scope:
  - orchestrate topic planning, search, fetch, extract, rank, evidence packaging, and lesson composition
  - persist generated lessons
  - include summary, TOC, markdown content, and source references
  - target about 60 minutes of study depth
- Out of scope:
  - advanced scoring or personalization refinement
- Implementation Notes:
  - Pending
- Verification:
  - Pending
- New Insights / Plan Updates:
  - Pending

### TASK-011 - Render Hierarchical Lesson Reader
- Status: TODO
- Priority: P1
- Depends on: TASK-004, TASK-010
- Goal: Display generated lessons in-app in a readable format with a hierarchical index.
- Scope:
  - render markdown lesson content
  - render TOC from structured heading data
  - support source links section
  - ensure long lessons remain readable
- Out of scope:
  - advanced rich-text editing
- Implementation Notes:
  - Pending
- Verification:
  - Pending
- New Insights / Plan Updates:
  - Pending

### TASK-012 - Personalize Topic Selection Using Lesson History And User Profile
- Status: TODO
- Priority: P2
- Depends on: TASK-003, TASK-006, TASK-010
- Goal: Improve topic relevance so follow-up, adjacent, and exploratory lessons feel intentional.
- Scope:
  - use user profile in topic planning
  - use active lesson and prior lessons in topic selection
  - reduce repetitive topic generation
- Out of scope:
  - advanced reinforcement learning or analytics
- Implementation Notes:
  - Pending
- Verification:
  - Pending
- New Insights / Plan Updates:
  - Pending

### TASK-013 - Add Basic Source Quality Controls
- Status: TODO
- Priority: P2
- Depends on: TASK-009, TASK-010
- Goal: Reduce poor-quality source usage in generated lessons.
- Scope:
  - dedupe candidate sources
  - score basic credibility and content richness
  - limit thin or low-value pages
  - preserve source metadata for auditability
- Out of scope:
  - enterprise-grade trust scoring
- Implementation Notes:
  - Pending
- Verification:
  - Pending
- New Insights / Plan Updates:
  - Pending

### TASK-014 - Add End-To-End Smoke Tests For MVP Flows
- Status: TODO
- Priority: P2
- Depends on: TASK-005, TASK-006, TASK-007, TASK-010, TASK-011
- Goal: Ensure the main user flows work together reliably.
- Scope:
  - generation in three modes
  - save flow
  - activate flow
  - lesson history access
  - lesson reader rendering
- Out of scope:
  - exhaustive testing of every edge case
- Implementation Notes:
  - Pending
- Verification:
  - Pending
- New Insights / Plan Updates:
  - Pending

### TASK-015 - Backlog And Requirements Reconciliation Pass
- Status: TODO
- Priority: P2
- Depends on: TASK-014
- Goal: Review implemented MVP against the requirements and update the backlog with any misses or follow-up work.
- Scope:
  - compare product behavior to `docs/requirements.md`
  - compare implementation to `docs/solution.md`
  - identify requirement gaps
  - add corrective tasks if needed
- Out of scope:
  - shipping new enhancements unless required to close a gap
- Implementation Notes:
  - Pending
- Verification:
  - Pending
- New Insights / Plan Updates:
  - Pending

## Execution Notes
- The executor should update `Active Task` whenever a task starts.
- The executor should keep dependency relationships current if task breakdown changes.
- If a task turns out to be too large, the executor should split it into smaller tasks before continuing.
- If a task is completed with deviations from the original plan, those deviations must be recorded.
- The executor should preserve the modular multi-step pipeline shape and avoid collapsing stages into one opaque implementation unless explicitly required.
- After each completed task, the executor should record the resulting commit hash(es) in the task entry.
- Pushing is not part of normal task completion; it requires explicit user approval after commit review.

## Change Log
- 2026-04-19: Created initial dynamic backlog structure with single-task execution rules and feedback loop expectations.
- 2026-04-19: Added mandatory per-task commit workflow and user-review-before-push policy.
