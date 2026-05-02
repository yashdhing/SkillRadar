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
- Current active task: None - awaiting review for TASK-011

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
- Status: DONE
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
  - Added backend configuration settings with a PostgreSQL default connection string and a checked-in `.env.example` for local environment setup.
  - Added a SQLAlchemy persistence layer with explicit models for `user_profile`, `lessons`, `lesson_sources`, and `generation_requests`, including enums, relationships, and a database-level single-active-lesson constraint.
  - Added session management and repository utilities so later orchestration tasks can persist entities without coupling directly to raw engine setup.
  - Added Alembic configuration plus an initial migration that creates the core schema and supports both live upgrades and offline SQL generation.
  - Added a `docker-compose.yml` PostgreSQL service definition and a `backend-migrate` make target to establish the local developer migration flow.
- Verification:
  - `make backend-install`
  - `make backend-lint`
  - `make backend-test`
  - `SKILLRADAR_DATABASE_URL=sqlite+pysqlite:////tmp/skillradar-task-002.db make backend-migrate`
  - Verified Alembic online migration execution against SQLite for schema creation.
  - Verified Alembic offline SQL generation for PostgreSQL syntax, including enum creation and the partial unique active-lesson index.
  - Verified repository-level persistence for user profile, lesson, lesson source, and generation request entities.
  - Verified the database constraint that prevents more than one active lesson at a time.
- Commits:
  - `8dc13f9` - Add persistence schema and migration flow
- New Insights / Plan Updates:
  - Docker is not installed in this environment, so the checked-in PostgreSQL compose setup was added but not boot-verified locally.
  - Enforcing the single active lesson at the schema layer reduces future application-level drift before `TASK-006` adds the explicit active-lesson workflow.

### TASK-003 - Seed User Profile From Provided Resume Context
- Status: DONE
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
  - Added a dedicated profile seed module that captures only the confirmed resume and topic-priority context from `docs/requirements.md`, without inventing extra preferences or product decisions.
  - Added an idempotent profile-seeding service and CLI entrypoint so the personalization profile can be inserted or refreshed without duplicating rows.
  - Added a follow-up Alembic data migration that seeds the default user profile immediately after the core schema migration, so personalization data exists from the first database setup.
  - Added a `backend-seed-profile` make target for local reseeding during development.
- Verification:
  - `make backend-lint`
  - `make backend-test`
  - `SKILLRADAR_DATABASE_URL=sqlite+pysqlite:////tmp/skillradar-task-003.db make backend-seed-profile`
  - Verified the seeded row exists with id `2d0f4bfe-9e8f-4c5d-97f2-4b1f53f5231d`, name `Yash Dhing`, and role `SDE3` in the temporary SQLite database.
  - Verified the seed service stores confirmed skills, career themes, and topic-priority entries.
  - Verified reseeding is idempotent and refreshes stale profile values rather than creating duplicates.
  - Verified Alembic online and offline migrations now include the profile seed step.
- Commits:
  - `eb95b10` - Seed the default user profile
- New Insights / Plan Updates:
  - Offline Alembic SQL generation for PostgreSQL required explicit JSON-safe rendering in the data migration; generic JSON bind rendering was not sufficient.
  - Keeping the confirmed profile in a dedicated seed-data module gives later personalization tasks a single source to extend without coupling that logic to migrations or request handlers.

### TASK-004 - Build Minimal Application Shell And Navigation
- Status: DONE
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
  - Added a shared app shell with top-level navigation so the frontend now has a stable layout for generate, library, and reader flows.
  - Turned the home route into a dedicated generate-focused screen with active-lesson summary and library entry points, while keeping generation behavior intentionally non-functional until the request-flow task.
  - Added a lesson library route and a lesson reader route backed by lightweight mock lesson data so the UI now has the required navigation surfaces before backend wiring.
  - Added reusable mock lesson data structures to keep the shell reviewable and to avoid hardcoding route-specific JSX blobs.
- Verification:
  - `npm run frontend:typecheck`
  - `npm run frontend:lint`
  - `npm run frontend:build`
  - Booted the frontend with `npm run frontend:dev` and verified `GET /`, `GET /library`, and `GET /lessons/jvm-latency-investigation` each returned `HTTP/1.1 200 OK`.
- Commits:
  - `a1f33bb` - Build the minimal application shell
- New Insights / Plan Updates:
  - A small shared mock-lesson module is enough to establish the reader and library UX without prematurely coupling the frontend shell to unfinished generation APIs.
  - The dedicated generate view can accept real mode selection and request submission later without changing the route structure introduced in this task.

### TASK-005 - Implement Lesson Generation Request Flow
- Status: DONE
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
  - Added a backend lesson-generation request endpoint that validates the three required modes, persists a `generation_requests` row, and creates a placeholder generated lesson draft for later pipeline replacement.
  - Kept the request workflow modular by isolating request schemas, API routes, and draft-generation service logic from the future retrieval and agent stages.
  - Added a client-side generate panel on the home screen with mode selection, conditional phrase input, submit handling, and result-state rendering from the live backend response.
  - Updated the local backend developer workflow so `make backend-dev` applies migrations before booting, and switched the default dev database to a repo-local SQLite file to keep the flow runnable without requiring local PostgreSQL installation.
- Verification:
  - `make backend-lint`
  - `make backend-test`
  - `npm run frontend:typecheck`
  - `npm run frontend:lint`
  - `npm run frontend:build`
  - Booted the backend with `make backend-dev` and the frontend with `npm run frontend:dev`.
  - Verified `POST /api/v1/lessons/generate` returned a persisted completed result for `phrase_seeded` mode with request id and lesson id.
  - Verified `GET /` returned `HTTP/1.1 200 OK` while exercising the generate flow locally.
- Commits:
  - `f8e8c70` - Implement the lesson generation request flow
- New Insights / Plan Updates:
  - The original PostgreSQL default prevented local request-flow verification in this environment because no Postgres service was running; using a repo-local SQLite default for dev keeps the app runnable without blocking the PostgreSQL-backed schema and migration path.
  - A synchronous placeholder lesson creation step is enough to validate the request lifecycle now, while leaving retrieval, topic planning, and composition as explicit future stages instead of collapsing them into this task.

### TASK-006 - Add Active Lesson State Management
- Status: DONE
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
  - Added dedicated active-lesson service logic and API routes so activation and active-lesson lookup are explicit backend capabilities instead of being folded into generation or reader code.
  - Extended the generation response contract with an explicit `fallbackReason` so `continue_active_lesson` can report when it had to fall back because no lesson was active yet.
  - Added repository helpers that clear prior active flags before marking a new lesson active, preserving the single-active-lesson invariant already enforced at the schema layer.
  - Updated the home screen to load the persisted active lesson from the backend, handle the intentional no-active 404 state, and show activation controls directly on generated lesson results.
  - Added lightweight UI messaging for no-active fallback and successful activation without changing the broader multi-step lesson pipeline architecture.
- Verification:
  - `make backend-lint`
  - `make backend-test`
  - `npm run frontend:typecheck`
  - `npm run frontend:lint`
  - `npm run frontend:build`
  - Booted the backend with `make backend-dev` and verified `GET /health` returned `{"status":"ok"}`.
  - Booted the frontend with `npm run frontend:dev` and verified `GET /` returned `HTTP/1.1 200 OK`.
  - Verified `GET /api/v1/lessons/active` returned `404` before activation, `POST /api/v1/lessons/generate` in `continue_active_lesson` mode returned `fallbackReason: "no_active_lesson"`, and `POST /api/v1/lessons/{lesson_id}/activate` followed by `GET /api/v1/lessons/active` returned the activated lesson summary.
  - Verified backend tests cover the no-active 404 case, activation, clearing previous active flags, and continue-current generation both with and without an active parent lesson.
- Commits:
  - `9c5e5a7` - Add active lesson state management
- New Insights / Plan Updates:
  - Treating `GET /lessons/active` returning `404` as the intentional no-active state keeps the active-lesson workflow explicit without inventing synthetic placeholder records.
  - Keeping activation as a dedicated endpoint preserves the modular pipeline shape: generation can report fallback conditions now, while later tasks can build richer continuation planning on top of the persisted active-lesson anchor.
  - `TASK-007` should keep replacing mock lesson-library data with persisted lesson records, but the active-lesson summary on the home screen is now already sourced from the backend and should stay that way.

### TASK-007 - Implement Lesson Save And Library Access
- Status: DONE
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
  - Added `LessonRepository.list_all`, `get_with_sources`, and `mark_saved` helpers so persistence-driven library and save flows have explicit query and mutation entry points without leaking SQLAlchemy details into routes.
  - Added `LessonListResponse`, `LessonDetailResponse`, and `LessonSourceItem` schemas so the library and reader surfaces consume a stable typed contract distinct from generation and active-lesson schemas.
  - Added `list_lessons`, `get_lesson_detail`, and `save_lesson` service functions and matching `GET /lessons`, `GET /lessons/{id}`, and `POST /lessons/{id}/save` API routes, registered after the static `/active` route so dynamic id matching never shadows it.
  - Save is idempotent at the service layer: it leaves `saved_at` untouched if it was already set and only flips `status` to `SAVED` when needed, preserving the first-save timestamp on repeat calls.
  - Replaced the frontend mock-lessons module with a backend-backed `app/lib/lessons-api.ts` that exposes typed list/detail/save fetchers, a small markdown-to-sections parser to feed the existing reader UI, and a relative timestamp helper for the library list.
  - Rewrote the library page as a client view backed by `GET /api/v1/lessons` with empty-state, loading, and error handling.
  - Rewrote the lesson reader page as a client view backed by `GET /api/v1/lessons/{id}` with TOC anchors, source links, a save action that hits `POST /lessons/{id}/save`, and dedicated 404/error fallbacks.
  - Extended the generate panel with a save action next to the activate action and a reader deep link, keeping result-state transitions self-contained.
  - Removed the hardcoded reader entry from the top nav now that the reader is reached from the library or active-lesson summary, and deleted the obsolete `frontend/app/data/mock-lessons.ts` module.
- Verification:
  - `make backend-install` (worktree-local venv create + editable install of existing deps)
  - `make backend-lint`
  - `make backend-test` — 23 passed including 7 new tests in `backend/tests/test_lesson_library.py`
  - `npm run frontend:typecheck`
  - `npm run frontend:lint`
  - `npm run frontend:build`
  - Booted backend on port 8765 and frontend on port 3765 and verified end-to-end:
    - `GET /api/v1/lessons` returned `{"items": []}` on a fresh database.
    - Generated two lessons via `POST /api/v1/lessons/generate` (`discover_new_topic` and `phrase_seeded`).
    - `GET /api/v1/lessons` returned both lessons with correct status, mode, seedPhrase, and timestamps.
    - `POST /api/v1/lessons/{id}/save` flipped status to `saved` and populated `savedAt`; a repeat call left the original `savedAt` unchanged in the DB.
    - `GET /api/v1/lessons/{id}` returned full detail including TOC entries and source list (zero sources for placeholder lessons), with status reflecting the save action.
    - `GET /api/v1/lessons/does-not-exist` and `POST /api/v1/lessons/does-not-exist/save` both returned `404`.
    - `GET /`, `GET /library`, `GET /lessons/{id}`, and `GET /lessons/does-not-exist` all returned `HTTP/1.1 200 OK` from `next dev`, with the routes wired to the live backend via `NEXT_PUBLIC_SKILLRADAR_API_BASE_URL`.
- Commits:
  - `7576c85` - Add lesson save and library backend endpoints
  - `58ff7d2` - Wire frontend library and reader to backend with save action
- New Insights / Plan Updates:
  - SQLite's `DateTime(timezone=True)` round-trips drop tz info on read, so JSON responses for the same lesson can render `savedAt` differently before vs. after a session expire. Idempotency is asserted at the persisted-row level rather than the JSON-string level; later tasks running on PostgreSQL will see consistent ISO-8601 with offsets.
  - The reader currently uses a small inline markdown-to-sections splitter so the existing structured layout keeps working. TASK-011 should replace this with a proper markdown renderer and respect the full heading tree, not just `##` boundaries.
  - The library list intentionally shows generated and saved lessons together (status pill differentiates them); confirming `docs/requirements.md` Open Question about whether unsaved lessons remain in history was deferred per requirements discipline rather than silently filtered.
  - `frontend/app/lib/lessons-api.ts` is the natural home for follow-up frontend fetchers (generation, active-lesson) so the home/page client code can be slimmed in a later refactor.

### TASK-008 - Define Agent Abstractions For Topic Planning And Lesson Composition
- Status: DONE
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
  - Added a dedicated `skillradar_api.agents` package split into `types`, `protocols`, `mock`, and `factory` modules so data contracts, structural interfaces, deterministic implementations, and provider selection each live behind a separate seam.
  - Defined frozen-dataclass data contracts (`UserProfileSummary`, `RecentLessonSummary`, `TopicPlannerInput`, `LessonBrief`, `RankedSource`, `ComposeLessonInput`, `ComposedLessonSection`, `ComposedLessonReference`, `ComposedLesson`) plus `LessonShape` and `NoveltyTarget` enums so pipeline stages exchange typed payloads without leaking SQLAlchemy or Pydantic types.
  - Defined `TopicPlannerAgent` and `LessonComposerAgent` as `@runtime_checkable` async `Protocol`s so the factory can validate any future provider adapter without forcing inheritance and so pipeline code can depend purely on the interface.
  - Implemented `MockTopicPlannerAgent` with deterministic mode-aware briefs: phrase-seeded uses the seed phrase, continue-active uses the active lesson title, discover falls back to the user's first topic priority, and recent-lesson overlaps surface a novelty hint in the brief notes.
  - Implemented `MockLessonComposerAgent` that derives sections, anchors, references, learning objectives, and metadata from the brief and source bundle, and disambiguates duplicate section anchors deterministically.
  - Added `get_default_topic_planner` and `get_default_lesson_composer` factory entrypoints so future providers (hosted models in TASK-010+) swap in without touching call sites.
  - Did not wire the agents into the existing `generation/service.py`; that orchestration is intentionally deferred to TASK-009 (retrieval) and TASK-010 (composition wiring) so this task remains an interface-only contribution and preserves modular pipeline boundaries.
- Verification:
  - `make backend-lint`
  - `make backend-test` — 35 passed (12 new agent tests in `backend/tests/test_agents.py`).
  - Verified protocol conformance via `isinstance(planner, TopicPlannerAgent)` / `isinstance(composer, LessonComposerAgent)`.
  - Verified planner determinism (same input -> same `LessonBrief`).
  - Verified mode-specific planner behavior across all three `LessonMode`s, novelty hint on recent-lesson overlap, and search-query non-emptiness.
  - Verified composer output preserves required `ComposedLesson` fields, anchor uniqueness on duplicate section titles, citation flow when sources are present, and graceful degradation when no sources are provided.
- Commits:
  - `1670191` - Add agent abstractions for topic planning and lesson composition
- New Insights / Plan Updates:
  - The data contracts now formalize `LessonShape` and `NoveltyTarget`. TASK-010 should map these onto the persisted `Lesson` row's `metadata_json` so library, ranking, and personalization (TASK-012, TASK-013) can read them later without re-deriving from the brief.
  - `RankedSource` deliberately mirrors but does not import `LessonSource`, keeping the agent layer free of SQLAlchemy. TASK-009 (retrieval pipeline) will own the conversion at its boundary.
  - Mock agents are async; current call sites (`generation/service.create_generation_request`) are sync. TASK-010 will need to either run the agent in an async route or use `asyncio.run(...)` at a clear boundary; the factory keeps that decision local rather than smearing it through the codebase.
  - `MockLessonComposerAgent` produces complete structured output even with zero sources so retrieval-disabled fallbacks still hit the same contract; the real composer in later phases is expected to refuse unsupported claims when sources are missing — keep this difference explicit in TASK-010.

### TASK-009 - Implement Modular Retrieval Pipeline Skeleton
- Status: DONE
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
  - Added a dedicated `skillradar_api.retrieval` package split into `types`, `protocols`, `mock`, `pipeline`, and `factory` modules so each stage stays independently replaceable behind its own seam, mirroring the agent layer's split.
  - Defined retrieval-local frozen-dataclass contracts (`SearchQuery`, `SearchHit`, `FetchedDocument`, `ExtractedContent`, `RankedExtract`) plus `SourceKind` and `FetchStatus` enums. The pipeline converts these into the agent layer's `RankedSource` only at the outer boundary, so persistence and AI providers never see retrieval internals.
  - Defined runtime-checkable async `Protocol`s for all five stages (`SearchProvider`, `ContentFetcher`, `ContentExtractor`, `SourceRanker`, `EvidencePackager`) so providers can plug in without inheritance.
  - Implemented deterministic mocks for every stage in `retrieval/mock.py`: synthesized hits per query with stable URLs, a fetcher that simulates blocklisted hosts returning `FetchStatus.BLOCKED` without raising, an HTML-tag stripper as the extractor, a lexical-overlap ranker that combines relevance/quality/novelty, and a packager that dedupes by URL and caps at `max_sources`.
  - Added a `RetrievalPipeline` orchestrator that runs search -> fetch -> extract -> rank -> package using `asyncio.gather` per stage, deduplicates hits across queries, drops failed fetches before extraction, and records every intermediate output plus fetch failures on the returned `RetrievalResult` for debugging and replay (per `solution.md`).
  - Added `factory.build_default_retrieval_pipeline()` and per-stage default getters as the single seam future real backends (search APIs, headless fetchers, hosted rankers) plug through.
  - Did not wire the pipeline into `generation/service.py`; that orchestration belongs to TASK-010 so this task remains an interface-only contribution that preserves modular pipeline boundaries.
- Verification:
  - `make backend-lint`
  - `make backend-test` — 46 passed (11 new retrieval tests in `backend/tests/test_retrieval.py`).
  - Verified protocol conformance for every stage via `isinstance(...)` against each `Protocol`.
  - Verified determinism of `MockSearchProvider`, blank-query short-circuit, and blocklisted URL handling without raising.
  - Verified the extractor strips HTML, normalizes whitespace, and skips failed fetches.
  - Verified the ranker orders relevant extracts above unrelated ones and the packager dedupes by URL and respects `max_sources` (including `max_sources=0`).
  - Verified the end-to-end pipeline produces a non-empty `RankedSource` tuple for a populated brief, returns an empty `RetrievalResult` (with all stage traces empty) when the brief has no queries, and surfaces blocked hits via `fetch_failures` while still composing healthy sources from the rest of the trace.
- Commits:
  - `4bfc1ec` - Add modular retrieval pipeline skeleton
- New Insights / Plan Updates:
  - The orchestrator returns `RetrievalResult` with full stage traces. TASK-013 (basic source quality) can extend the ranker and packager without touching this orchestrator, and a future debugging UI can render these traces.
  - `RankedSource.metadata` already carries `combined_score`, `rationale`, `source_kind`, and `brief_target_topic`. TASK-010 should persist these into `lesson_sources.metadata_json` when storing evidence so retrieval decisions are auditable from the lesson reader, not only at run time.
  - Stage protocols are async; tests use `asyncio.run` per call. For TASK-010 wiring inside the sync `generation/service.py` request path, prefer running `RetrievalPipeline.run` plus the agent calls together inside one `asyncio.run` boundary to avoid event-loop churn.
  - `MockEvidencePackager.package` accepts `max_sources=0` as "produce no sources". Production packagers should keep this behavior so the orchestrator can disable evidence injection without code changes.
  - Solution.md mentions allowlist/denylist filtering as a quality control. TASK-013 should add that as an explicit `EvidencePackager` policy parameter rather than hard-coding into the mock — the protocol seam already supports this.

### TASK-010 - Generate Structured Lesson Drafts From Grounded Inputs
- Status: DONE
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
  - Added `generation/orchestrator.py` with a pure async `run_generation_pipeline` that drives `TopicPlannerAgent.plan_topic` → `RetrievalPipeline.run` → `LessonComposerAgent.compose_lesson` and returns a `GenerationOutcome` carrying the brief, full retrieval trace, and composed lesson. The orchestrator deliberately knows nothing about SQLAlchemy so each stage stays independently testable and replaceable.
  - Refactored `generation/service.py` to call the orchestrator across one `asyncio.run` boundary (per the TASK-009 insight to avoid event-loop churn), translate the persisted profile + active lesson + recent lessons into agent-layer summaries, and persist the composed output into `lessons` + `lesson_sources` rows with full metadata.
  - Added typed seam parameters (`planner`, `composer`, `retrieval_pipeline`) to `create_generation_request` so future feature flags or tests can swap stages without monkey-patching the factory module; defaults still resolve through `agents.factory` and `retrieval.factory`.
  - Markdown assembly + TOC generation are split helpers (`_assemble_markdown`, `_toc_entries`) with a documented invariant: TOC entries and `## ` blocks emit in the same order so the frontend reader's anchor parser keeps resolving sections correctly. Sections include "Why this matters", optional learning objectives, every composer-produced section, optional practical takeaways, and optional references.
  - Lesson `metadata_json` now records the planner brief (target topic, shape, novelty, intent, search queries, desired sections, notes), composer metadata, learning objectives, practical takeaways, and a retrieval trace summary (hit/fetch/failure/extract/ranked/source counts) so debugging and TASK-013 quality work can read pipeline decisions from the persisted lesson.
  - `lesson_sources.metadata_json` carries the agent-layer `RankedSource.source_id`, `combined_score`, `rationale`, `source_kind`, and `brief_target_topic`; per-stage scores (relevance/quality/novelty) populate the dedicated columns. Snippet text from the extractor lands in `content_snapshot`.
  - `generation_requests.input_context_json` now also records `recentLessonIds` so the planner's input context is auditable, and `fallbackReason` is preserved in both the request row and the resulting lesson metadata.
  - Updated the existing detail-with-sources library test to acknowledge that lessons now ship with grounded sources by default; assertions check for the manually attached row alongside the retrieval-grounded ones rather than expecting an exact count.
- Verification:
  - `make backend-lint`
  - `make backend-test` — 53 passed (7 new orchestration tests in `backend/tests/test_generation_orchestration.py` plus refreshed library + generation tests).
  - Verified composed title and summary land on the persisted `Lesson` row instead of the previous static placeholder.
  - Verified `metadata_json.briefShape`, `briefNovelty`, `briefSearchQueries`, `briefDesiredSections`, `learningObjectives`, `practicalTakeaways`, `composerMetadata`, and `retrieval` trace fields are all populated and consistent with the planner+retrieval stage outputs.
  - Verified `lesson_sources` rows are persisted with `agentSourceId`, `combined_score`, `relevance_score`, `quality_score`, `novelty_score`, and the original URL/title/domain so per-stage scores survive into persistence for later auditability and personalization work.
  - Verified `## ` markdown headings match the TOC titles and order, including the "Why this matters", "Learning objectives", "Practical takeaways", and "References" wrapper sections, so the frontend reader can resolve every TOC anchor.
  - Verified continue-mode generation links `parent_lesson_id` to the active lesson and clears `fallbackReason`; without an active lesson, both the response and persisted metadata flag `no_active_lesson` and `parent_lesson_id` stays `NULL`.
  - Verified `generation_requests.input_context_json.recentLessonIds` includes prior lesson IDs so the planner's history input is auditable from the request row.
- Commits:
  - `baceacc` - Wire planner + retrieval + composer into lesson generation
- New Insights / Plan Updates:
  - The orchestration boundary ended up clean: service does persistence + request lifecycle, orchestrator does the async pipeline, neither leaks into the other. That keeps the seam open for TASK-012 (personalization) to operate purely on `TopicPlannerInput` construction without touching persistence.
  - Sources are persisted as plain `LessonSource` rows even when the mock retrieval emits placeholder `https://*.example.com` URLs. TASK-013 should add an evidence-packager policy hook (allowlist/denylist) before any non-mock backend lands so the seam stays clean.
  - The composer is invoked even when retrieval returns zero sources. Solution.md flags this as a risk (AI hallucinating beyond sources). The mock currently produces structured output regardless; the real composer in TASK-013/14 should refuse unsupported sections, and the orchestrator should already be able to surface that as a `GenerationRequestStatus.FAILED` via the existing `try/except` boundary.
  - Reader-side markdown rendering still uses the lightweight in-app splitter from TASK-007. With richer composer output now flowing in, TASK-011 has a real motivation to land — a proper markdown renderer would unlock list rendering for learning objectives and references rather than relying on raw paragraphs.
  - The mock retrieval pipeline fakes all I/O. Latency is irrelevant today, but real backends will need timeout/rate-limit policy. The single `asyncio.run` boundary in the service is the natural place to wrap that with a deadline.

### TASK-011 - Render Hierarchical Lesson Reader
- Status: DONE
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
  - Replaced `parseLessonMarkdown`'s flat string-paragraph contract with a typed `LessonBlock` model: paragraphs carry inline nodes (`text` / `link` / `bold` / `code`), lists carry one `InlineNode[]` per item, and `subheading` blocks render `### ` headings inside a section. Sections expose `blocks: LessonBlock[]` instead of `body: string[]` so the renderer never has to guess whether a string is a list or a paragraph.
  - Added `parseInline` for `[text](href)`, `**bold**`, and `` `code` `` tokens and `blocksFromBuffer` for paragraph + list segmentation, both intentionally bounded to the markdown shape the composer emits today; out-of-scope markdown features (tables, nested lists, code blocks, images) deliberately stay unsupported until either the composer needs them or the dependency tradeoff changes.
  - Added `frontend/app/components/lesson-content.tsx` as the only consumer of the block model. The component renders paragraphs, ordered/unordered lists, and inline links/bold/code into proper React JSX and is the seam to swap for `react-markdown` later if the composer's output ever exceeds this scope.
  - Updated `app/lessons/[lessonId]/page.tsx` to render intro and section content through `LessonContent`, replacing the previous `body.map(p => <p>{p}</p>)`. Renamed the source list section to "Grounding Sources", surfaced author when present, and made the empty-source copy clearer about the retrieval pipeline state.
  - Added CSS support for `.content-list`, `.inline-code`, sticky-header `scroll-margin-top` on `.reader-section`, and tightened `<h3>` / `<h4>` sizing so long lessons render with consistent rhythm. Existing TOC sticky behaviour, source-list spacing, and mobile responsiveness all preserved.
  - Did NOT add a markdown library (e.g. `react-markdown`). The composer's emitted markdown is bounded and we control its shape, so the dependency was not justified. The renderer is one self-contained module ready to be swapped if/when we widen the markdown contract.
- Verification:
  - `npm run frontend:typecheck`
  - `npm run frontend:lint`
  - `npm run frontend:build` — all routes built; reader bundle ~2.85 kB.
  - Booted backend (uvicorn :8765) + frontend (`next dev` :3765) and exercised end-to-end:
    - `POST /api/v1/lessons/generate` (phrase_seeded "Kafka exactly-once in practice") returned a lesson whose `contentMarkdown` contained `## Learning objectives` with `- ...` bullets, per-section `## ` blocks with `[link](url)` inline links, `## Practical takeaways` with `- ...` bullets, and `## References` with `- [title](url)` items.
    - `GET /lessons/{lessonId}` returned `HTTP/1.1 200 OK`; client-side hydration runs `parseLessonMarkdown` and drives `LessonContent`.
    - TOC titles match the `## ` headings in the composer markdown one-for-one (`Why this matters`, `Learning objectives`, planner sections, `Practical takeaways`, `References`), confirming the TASK-010 ordering invariant still holds with the richer block model.
- Commits:
  - `30f4fc5` - Render lesson markdown through a typed block model
- New Insights / Plan Updates:
  - The block model now has room for `subheading` (`###`) blocks even though the current composer never emits them. Keeping the case in the renderer means TASK-014/15 quality work can introduce sub-section structure without another renderer rewrite.
  - The `Grounding Sources` panel at the bottom of the reader is the natural surface for surfacing per-source relevance/quality/novelty scores from `lesson_sources` once we want to expose them; the seam exists, but actually rendering them is intentionally out of scope here.
  - Solution.md flags potential code blocks and tables as future content. When that lands, swap the inline parser + block parser for `react-markdown` + `remark-gfm`. The single touchpoint is `frontend/app/components/lesson-content.tsx` plus the parser exports in `lib/lessons-api.ts`.
  - The current reader markup still calls the section "Source References" in earlier comments; renamed to "Grounding Sources" in the TASK-011 update to better reflect the retrieval pipeline's evidence framing. If a future task brings back human-curated reading lists, that distinction matters and should not collapse back into one section.

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
