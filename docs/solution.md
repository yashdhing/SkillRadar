# SkillRadar Solution Design

## Document Status
- Status: Proposed implementation baseline
- Audience: Coding agents and engineers
- Relationship to requirements: This document recommends a concrete v1 while keeping unresolved product questions visible

## Design Principles
- Prioritize lesson quality over UI polish.
- Keep the UI minimal and operational.
- Separate retrieval from lesson authoring so the AI agent works from grounded evidence.
- Preserve source links and evidence for every generated lesson.
- Personalize by using the user's profile, lesson history, and current active lesson.
- Avoid hidden assumptions by making defaults explicit and configurable.

## Recommended V1 Product Shape

### Core Screens
- `Home / Generate`
  - Trigger controls
  - Current active lesson summary
  - Quick phrase input
- `Lesson Reader`
  - Title
  - Metadata
  - Hierarchical table of contents
  - Rendered lesson content
  - Source references
  - Save button
  - Mark active button
- `Lesson Library`
  - List of old lessons
  - Filters such as saved/all/mode/topic
  - Search by title/topic/phrase

### Trigger UX
- Keep the UI simple with a single primary `Generate Lesson` action.
- Pair it with a required mode selector:
  - `Continue Current`
  - `Discover Something New`
  - `From Phrase`
- Show phrase input only when `From Phrase` is selected.

This satisfies the user's trigger requirement without investing in advanced UI.

## Recommended Technical Baseline

### Suggested Stack
- Frontend: Next.js with TypeScript
- Backend: Python 3 with FastAPI
- Database: PostgreSQL with SQLAlchemy and Alembic
- Background execution: Python worker process with queue-ready step orchestration
- Lesson content format: Markdown plus structured JSON metadata
- AI execution: Provider-abstracted agent layer in Python
- Retrieval: Multi-step grounded search + fetch + extraction + ranking pipeline, not a broad unrestricted crawler for v1

### Why This Baseline
- Python is the strongest fit for AI orchestration, web retrieval, content extraction, ranking, and pipeline experimentation.
- FastAPI keeps the backend simple while exposing clean APIs to the UI.
- Next.js with TypeScript remains a strong fit for a minimal but solid frontend.
- PostgreSQL is a better long-term fit than SQLite for pipeline state, richer metadata, and future concurrency, while remaining straightforward for local development via Docker.
- The split frontend/backend architecture keeps pipeline internals independently evolvable from the UI.

### Why Not Java 21 Or Golang For V1
- Java 21 is excellent for production backend systems, but it is less ergonomic than Python for rapid iteration across AI tooling, parsing, and retrieval workflows.
- Golang is strong for concurrency and service performance, but it has a weaker ecosystem for LLM-oriented orchestration and content-processing libraries compared with Python.
- Either could become a future runtime for selected subsystems, but Python is the best overall fit for the first implementation of this product.

## Important Architectural Recommendation
Do not start with a full web crawler that recursively explores the internet.

For v1, prefer a **grounded modular pipeline**:
1. Topic planner chooses search intents.
2. Search layer finds candidate sources.
3. Fetch layer retrieves selected URLs and source artifacts.
4. Extraction layer converts raw pages into clean readable content.
5. Ranking layer scores sources for relevance, quality, recency, and novelty.
6. Evidence packager prepares the grounded bundle for generation.
7. Lesson composer AI agent writes a lesson from those grounded inputs.

This still satisfies the user's need for web-based lesson creation, but is much cheaper, safer, and easier to control than a true crawler.

Later, this can evolve into scheduled source monitoring or domain-specific crawling.

## Proposed High-Level Architecture

### Components
- `Web UI`
  - Minimal screens for generation, reading, saving, history
- `Lesson Orchestrator`
  - Entry point for all generation requests
- `Topic Planner`
  - Decides whether to continue, branch, or explore
- `Search & Discovery`
  - Finds candidate web sources
- `Content Fetcher`
  - Retrieves source documents and pages
- `Content Extractor`
  - Converts fetched data into normalized readable content
- `Source Ranker`
  - Scores relevance, recency, credibility, novelty
- `Evidence Packager`
  - Prepares source bundles for the lesson composer
- `Lesson Composer Agent`
  - Produces the final lesson with citations
- `Lesson Store`
  - Persists lessons, sources, metadata, state
- `Profile & Memory Layer`
  - Stores user profile, interests, and prior lesson context

### Logical Flow
1. User selects generation mode and optionally enters a phrase.
2. Orchestrator builds a lesson request.
3. Topic planner creates a lesson brief.
4. Search/discovery gathers candidate sources from the web.
5. Fetcher retrieves the top candidate URLs and artifacts.
6. Extractor produces normalized readable content from fetched sources.
7. Ranker filters duplicates and low-quality items and chooses evidence.
8. Evidence packager creates the grounded source bundle for generation.
9. Lesson composer agent generates:
   - title
   - learning goals
   - hierarchical outline
   - full lesson body
   - practical takeaways
   - references
10. Lesson is stored as a generated draft.
11. UI renders the lesson.
12. User can save it and/or mark it active.

### Pipeline Design Requirements
- Each pipeline stage should have a clear interface and its own input/output contract.
- Each stage should be replaceable without forcing major rewrites in adjacent stages.
- Each stage should be testable independently.
- Each stage should allow custom policies and tuning.
- The orchestrator should record intermediate outputs for debugging and future refinement.

## Personalization Model

### User Profile Inputs
- Resume-derived skills and experience
- Preferred depth: senior backend/distributed-systems level
- Current tools and ecosystems:
  - Java
  - Dropwizard
  - MySQL
  - Kafka
  - HBase
  - Kubernetes
  - fraud/embeddings/vector search
  - reliability/platform work

### Topic Categories To Support
- Deep dive into an existing known topic
- Follow-up from current lesson
- Adjacent topic that broadens current expertise
- New but career-useful topic
- Tooling/workflow improvement topic
- Case study / postmortem / architecture teardown
- Leadership or engineering effectiveness topic relevant to seniority

### Ranking Heuristics
- Strong relevance to current role or next-level growth
- Novelty relative to previous lessons
- Practicality over purely superficial news
- Recency when the topic is fast-moving
- Credibility of source
- Diversity across lessons to avoid repetition

## Detailed Lesson Contract

### Lesson Output Requirements
Every generated lesson should contain:
- `title`
- `slug`
- `mode`
- `seed_phrase` if any
- `summary`
- `estimated_study_minutes` targeting about 60
- `why_this_matters_for_you`
- `learning_objectives`
- `table_of_contents`
- `sections`
- `practical_takeaways`
- `further_reading`
- `citations`

### Recommended Section Shape
- Introduction / context
- Why it matters
- Core concepts
- Detailed walkthrough
- Real-world case studies or examples
- Tradeoffs / failure modes / anti-patterns
- How it connects to your current work
- Suggested exercises or reflection prompts
- External references

### Suggested Render Format
- Store canonical lesson content as Markdown
- Store table of contents and metadata as structured JSON
- Render Markdown in-app with anchored headings
- Generate sidebar TOC from the heading tree

## Data Model Proposal

### `user_profile`
- `id`
- `name`
- `role_title`
- `bio`
- `skills_json`
- `experience_json`
- `topic_preferences_json`
- `created_at`
- `updated_at`

### `lessons`
- `id`
- `title`
- `slug`
- `status` (`generated`, `saved`, `archived`)
- `mode` (`continue_active_lesson`, `discover_new_topic`, `phrase_seeded`)
- `seed_phrase`
- `summary`
- `estimated_study_minutes`
- `why_this_matters`
- `content_markdown`
- `toc_json`
- `metadata_json`
- `is_active`
- `parent_lesson_id` (nullable for follow-up chains)
- `created_at`
- `updated_at`
- `saved_at`

### `lesson_sources`
- `id`
- `lesson_id`
- `url`
- `title`
- `domain`
- `author`
- `published_at`
- `retrieved_at`
- `relevance_score`
- `quality_score`
- `novelty_score`
- `content_snapshot`
- `metadata_json`

### `generation_requests`
- `id`
- `mode`
- `seed_phrase`
- `input_context_json`
- `status` (`queued`, `running`, `completed`, `failed`)
- `error_message`
- `created_at`
- `updated_at`

### `lesson_feedback` (optional but useful)
- `id`
- `lesson_id`
- `feedback_type` (`liked`, `saved`, `completed`, `too_basic`, `too_advanced`, `not_relevant`)
- `notes`
- `created_at`

## API / Server Action Design

### `POST /api/lessons/generate`
Request:
```json
{
  "mode": "continue_active_lesson",
  "seedPhrase": null
}
```

Response:
```json
{
  "generationRequestId": "req_123",
  "lessonId": "lesson_123",
  "status": "completed"
}
```

### `POST /api/lessons/:id/save`
- Marks lesson as saved

### `POST /api/lessons/:id/activate`
- Marks selected lesson as active
- Unsets prior active lesson

### `GET /api/lessons`
- List lessons with filters

### `GET /api/lessons/:id`
- Return full lesson with sources

## AI Agent Design

### Agent Responsibilities
- Accept a grounded lesson brief and source bundle
- Build a 60-minute lesson plan
- Write content in structured, readable language
- Tie lesson relevance back to the user's background
- Include citations and source links
- Avoid unsupported claims not grounded in sources

### Recommended Agent Interfaces

#### `TopicPlannerAgent`
Input:
- generation mode
- user profile
- active lesson summary
- phrase seed
- recent lesson history

Output:
- lesson intent
- target topic
- search queries
- desired lesson shape
- novelty target

#### `LessonComposerAgent`
Input:
- user profile summary
- lesson brief
- ranked sources

Output:
- structured lesson payload

### Provider Abstraction
Implement interfaces such as:
```python
class TopicPlannerAgent(Protocol):
    async def plan_topic(self, input: TopicPlannerInput) -> TopicPlannerOutput: ...

class LessonComposerAgent(Protocol):
    async def compose_lesson(self, input: ComposeLessonInput) -> ComposedLesson: ...
```

This keeps model/vendor choice open.

## Retrieval Design

### Recommended V1 Retrieval Strategy
- Use search queries instead of blind crawling
- Fetch only top relevant URLs
- Extract readable text in a dedicated stage
- Deduplicate by canonical URL/domain/title/content similarity
- Rank and retain a small high-quality evidence set

### Pipeline Stages
- `Topic Planning`
  - chooses lesson intent, target topic, and search strategy
- `Search`
  - discovers candidate URLs and source records
- `Fetch`
  - retrieves page bodies, feeds, or document artifacts
- `Extract`
  - converts fetched content into normalized text and metadata
- `Rank`
  - scores quality, relevance, recency, credibility, and novelty
- `Compose`
  - generates the final lesson from the grounded evidence bundle

### Stage Contracts
- Each stage should define:
  - typed input
  - typed output
  - failure modes
  - retry behavior
  - stage-level configuration
- Stage outputs should be persisted where useful for replay, debugging, and independent improvement.

### Source Types To Support
- Engineering blogs
- Official docs
- Incident writeups / postmortems
- Architecture articles
- Conference talks with transcripts or companion articles
- GitHub project docs or release notes
- High-signal AI tooling writeups

### Source Quality Heuristics
- Official or reputable engineering sources score higher
- Very thin or SEO-driven pages score lower
- Duplicate summaries without substance score lower
- Pages lacking enough detail for lesson grounding score lower

### Freshness Strategy
- For rapidly changing topics such as AI tooling, prioritize recency
- For evergreen engineering topics, balance recency with timeless quality

## Minimal UI Design

### Generate Panel
- Mode selector
- Phrase input when needed
- Generate button
- Small context box showing active lesson

### Lesson Reader
- Header with lesson title and summary
- Save button
- Mark Active button
- Left sidebar or top accordion TOC
- Main content area rendering Markdown
- Source references section at bottom

### Library
- Simple table or list
- Filter chips:
  - `Saved`
  - `All`
  - `Generated`
  - `Follow-up`
  - `New`
  - `Phrase`

This matches the user's request to avoid investing much in UI detail.

## State Machine Proposal

### Generation Request
- `queued`
- `running`
- `completed`
- `failed`

### Lesson
- `generated`
- `saved`
- `archived`

### Active Lesson Rule
- At most one lesson is active at a time
- `continue_active_lesson` requires either:
  - an active lesson
  - or a graceful fallback that asks the user to choose a lesson or auto-switches to discover mode

## Suggested Implementation Phases

### Phase 1: Usable MVP
- Next.js app shell
- FastAPI backend shell
- PostgreSQL schema and migration setup
- User profile seeded from the provided resume
- Generate lesson in all three modes
- Store lesson content and source references
- Save lesson
- Mark lesson active
- View old lessons

### Phase 2: Better Content Quality
- Better source ranking
- Source allowlist/denylist
- Duplicate-topic reduction
- Feedback loop from saves/completions
- Better lesson templates for different content types

### Phase 3: Automation / Continuous Learning
- Scheduled lesson generation
- Topic streams
- RSS and release-note ingestion
- Weekly study plans
- Progress tracking

## Recommended Defaults For V1
These are implementation defaults, not product truth.

- Single-user app
- Python 3 + FastAPI backend
- Next.js frontend
- PostgreSQL database
- One active lesson at a time
- Generated lessons remain visible in history even if unsaved
- Save means bookmarked/explicitly retained
- Markdown-based lesson rendering
- Multi-step grounded pipeline instead of a general crawler

## Risks And Mitigations

### Risk: Low-quality web content pollutes lessons
- Mitigation: quality scoring, domain filters, evidence review, source cap

### Risk: Lessons feel repetitive
- Mitigation: novelty scoring, lesson history awareness, parent/child lesson chains

### Risk: AI hallucinates beyond sources
- Mitigation: grounded prompts, explicit citations, reject unsupported sections

### Risk: Full crawl scope becomes complex too early
- Mitigation: start with targeted retrieval; treat generalized crawling as future work

### Risk: 1-hour lessons become too long or too shallow
- Mitigation: enforce lesson template and section-level depth checks

## Suggested Repo Structure
```text
docs/
  requirements.md
  solution.md
backend/
  app/
  alembic/
frontend/
  app/
  components/
  lib/
app/
docker-compose.yml
```

## Coding Guidance For Claude Executor
- Treat `docs/requirements.md` as the authoritative user requirement source.
- Treat this file as the recommended implementation baseline.
- Preserve unresolved product questions rather than silently hardcoding them as business truth.
- Build the simplest UI that cleanly supports:
  - generation
  - reading
  - saving
  - active lesson tracking
  - history access
- Keep lesson generation grounded in retrieved sources.
- Prefer clear boundaries between:
  - topic planning
  - retrieval
  - extraction
  - ranking
  - evidence packaging
  - lesson composition
  - persistence

## Recommended Next Step
The next coding step should be to scaffold the app with:
- Prisma schema
- seeded user profile
- lesson data model
- minimal UI screens
- stubbed agent/retrieval interfaces

After that, wire in the real retrieval and AI provider.
