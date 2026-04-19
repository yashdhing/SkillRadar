# Project Agent Guidelines

## Purpose
This file contains general operating rules for any agent working on this project.

Read this file before making changes.
Also read:
- `docs/requirements.md`
- `docs/solution.md`
- `docs/implementation-backlog.md`

## Core Rules
- Do not assume anything.
- Ask for clarity whenever required.
- If creating or running the service may require installation, ask whether anything should be installed first.
- For each task, test completely and keep correcting until the task is 100% complete.

## Working Style
- Treat `docs/requirements.md` as the source of truth for user requirements.
- Treat `docs/solution.md` as the recommended implementation baseline, not unquestionable truth.
- Treat `docs/implementation-backlog.md` as a living execution plan that must be updated after every completed task.
- Only work on one backlog task at a time.
- Do not silently hardcode unresolved product decisions as facts.
- Record new insights and missed requirements back into the backlog.

## Git Workflow
- This project is tracked in git.
- Each completed backlog task must conclude with one or more intentional commits as needed.
- Do not batch many unrelated backlog tasks into a single commit.
- The executor should prefer clean, reviewable commits with clear messages.
- After making commits for a completed task, stop for user review before any push.
- Do not push to `main` without explicit user approval after review.
- If the user gives review feedback or change requests on a commit, incorporate those changes and create follow-up commits as needed.

## Before Starting Any Task
- Read the current task in `docs/implementation-backlog.md`.
- Confirm dependencies for that task are satisfied.
- Mark only one task as `IN_PROGRESS`.
- Check whether the task requires any new package, runtime, SDK, database, browser tool, or external service.
- If installation or setup is needed, ask first before proceeding.

## Testing Expectations
- Do not mark a task complete until it is verified.
- Run all relevant tests for the scope of the task.
- Include type checks, linting, unit tests, integration tests, and manual verification when appropriate.
- If something fails, fix it before considering the task done.
- If full verification is blocked, document exactly what was tested, what remains untested, and why.

## Quality Bar
- Prefer correctness and clarity over speed.
- Keep the UI simple unless requirements say otherwise.
- Prioritize lesson quality, grounded sourcing, and reliable flows.
- Preserve source traceability for generated lessons.
- Avoid broad refactors unless required by the current task.

## Requirements Discipline
- Keep all confirmed requirements intact.
- Surface ambiguities instead of guessing.
- If implementation uncovers a missing requirement or hidden dependency, update the backlog and note it explicitly.

## Expected Deliverable Behavior
- A task is only done when implementation, testing, and backlog update are all complete.
- A task is only ready for handoff after the related commits are created.
- After each task, update:
  - status
  - implementation notes
  - verification notes
  - new insights
  - any new follow-up tasks

## Current Recommended Tech Direction
- Frontend: Next.js with TypeScript
- Backend: Python 3 with FastAPI
- Database: PostgreSQL
- AI integration: provider-abstracted Python agent layer
- Retrieval: grounded multi-step pipeline with search, fetch, extract, rank, and lesson composition stages
- Lesson content: Markdown with structured JSON metadata

## If There Is A Conflict
- User message wins over everything else.
- `docs/requirements.md` wins over `docs/solution.md`.
- If a conflict remains unresolved, pause and ask for clarification.
