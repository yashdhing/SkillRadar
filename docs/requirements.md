# SkillRadar Requirements

## Document Status
- Status: Draft based on user-provided requirements only
- Intent: Capture confirmed requirements without hiding assumptions
- Audience: Human reviewers and coding agents such as Claude

## Product Goal
Build `SkillRadar`, a personal study app that uses an AI agent plus web retrieval to generate high-value study lessons that keep Yash Dhing up to date and growing as an SDE3.

The app should help with:
- Staying current on relevant backend/distributed-systems topics
- Going deeper into topics already used in day-to-day work
- Branching into adjacent or new areas that are useful for career growth
- Surfacing practical tools, case studies, patterns, and engineering updates rather than only theory

## Primary User
- Name: Yash Dhing
- Role: SDE3
- Current company: Flipkart
- Preference: Minimal UI is acceptable; depth of lesson quality matters more than visual polish
- Technical background:
  - Java, Groovy, Python, SQL
  - Dropwizard, Kafka, Aerospike, HBase, MySQL, Qdrant, Spark, Elastic Search
  - Kubernetes, Docker, CI/CD
  - System design, microservices, async workflows
  - Reliability, incident response, infra modernization, fraud detection, platform tooling

## Confirmed Product Requirements

### 1. UI
- The product must have a UI.
- The user does not intend to go deep into UI sophistication.
- A simple, functional UI is preferred over a design-heavy UI.

### 2. Lesson Generation Trigger
- There must be a trigger button in the UI to generate a new lesson.
- Triggering a lesson should use web sources.
- A web crawler or web retrieval mechanism is likely needed.

### 3. Trigger Modes
- The app must support generating the next lesson by continuing from the currently active lesson.
- The app must support generating something totally new.
- The app must support taking a phrase from the user and generating lessons relevant to that phrase.

### 4. Lesson Content Requirements
- Each lesson must be readable inside the app itself.
- Each lesson must be structured with a hierarchical index.
- External links may be included when needed.
- Each lesson should be detailed enough for about 1 hour of dedicated study time.

### 5. Lesson Saving
- Each generated lesson must have a save button.
- Saved lessons must remain accessible later.

### 6. Old Lesson Access
- Old lessons must be accessible from the app.
- The app needs some concept of lesson history or library.

### 7. Lesson Scope
- Lessons should not be limited to theoretical updates.
- Lessons may include:
  - Practical engineering updates
  - Case studies of real problems solved
  - Useful AI tools or workflows
  - Backend/distributed-systems topics
  - Deeper dives into known topics
  - Related/adjacent topics
  - Completely different but career-useful topics

### 8. AI Executor
- The executor for generation should be an AI agent.

### 9. Backend Technology Direction
- Backend should use one of:
  - Java 21
  - Python 3
  - Golang
- The final choice should be whichever is best suited for this task.

### 10. Lesson Generation Pipeline Architecture
- The lesson generation pipeline must be multi-step.
- Each step should be performed properly, deeply, and independently.
- Pipeline steps should be independently upgradable.
- Pipeline steps should be independently customizable.
- The architecture should preserve clear boundaries between stages such as search, fetch, ranking, and lesson composition.

## User Context To Personalize Lesson Selection
This section is not a product requirement by itself, but it is confirmed context that should inform ranking and personalization.

### Current/Recent Career Themes
- Large-scale backend systems
- Returns, incident management, workflow redesign
- Reporting pipelines and near-real-time processing
- Fraud detection using embeddings and similarity search
- Trust and safety platforms
- Big-sale readiness and reliability engineering
- Infra modernization and platform migrations
- On-call ownership and RCA leadership
- Mentorship and engineering leadership

### Topics That Should Likely Rank Higher
- Java/JVM performance and modern backend practices
- Distributed systems design and failure handling
- Kafka/event-driven architecture
- Datastores and storage tradeoffs
- Reliability engineering, incident response, observability
- Kubernetes/platform engineering
- AI-assisted engineering workflows
- Production ML/embeddings/vector-search use cases
- Architecture and leadership topics relevant to an SDE3+

## Draft User Stories
- As a user, I want to click a button and get a fresh lesson generated from current web sources.
- As a user, I want the next lesson to continue from what I am currently studying.
- As a user, I want to request a lesson from a free-form phrase such as `Kafka exactly-once in practice` or `AI coding agents for backend teams`.
- As a user, I want to read the full lesson inside the app without jumping across tabs.
- As a user, I want a hierarchical index so I can navigate a long lesson quickly.
- As a user, I want to save useful lessons so I can return to them later.
- As a user, I want to browse past lessons.
- As a user, I want lessons to be substantial enough for a focused 1-hour study session.

## Functional Requirements

### FR-1 Lesson Generation
- The system shall create a lesson from web-discovered material.
- The system shall support three generation modes:
  - `continue_active_lesson`
  - `discover_new_topic`
  - `phrase_seeded`

### FR-2 Personalized Relevance
- The system shall use the user's background and prior lessons to bias topic selection.
- The system shall allow lessons to be:
  - follow-up
  - adjacent
  - exploratory
  - broadly career-useful

### FR-3 In-App Lesson Reading
- The system shall display the full lesson in the app.
- The system shall provide a hierarchical index for each lesson.
- The system shall show external references when relevant.

### FR-4 Lesson Persistence
- The system shall allow saving a generated lesson.
- The system shall store saved lessons for later access.

### FR-5 Lesson History
- The system shall allow access to previously generated or saved lessons.

### FR-6 Active Lesson State
- The system shall maintain the notion of a currently active lesson, because one trigger mode depends on it.

### FR-7 Modular Generation Pipeline
- The system shall implement lesson generation as a multi-step pipeline rather than a single opaque generation call.
- The system shall keep stage boundaries explicit so each stage can be improved independently.
- The system shall support independent customization and replacement of pipeline stages.

## Content Quality Expectations
- Lessons should be practical, not only academic.
- Lessons should connect ideas to engineering usefulness.
- Lessons should be concrete enough to support about 60 minutes of study.
- Lessons should include references/citations/links back to source material.
- Lessons should be internally structured, not a wall of text.

## Non-Functional Requirements Confirmed Or Strongly Implied
- Personal-use first is the safest current assumption, but this is not yet confirmed as a hard requirement.
- UI simplicity is preferred.
- Quality of retrieval, curation, and lesson structure matters more than heavy UI investment.
- The app should be usable for repeated study over time, not only one-off generation.
- The generation pipeline should be modular enough that individual stages can evolve without rewriting the whole system.

## Open Questions
These are intentionally left unresolved so the next implementation phase does not invent answers silently.

### Product Scope
- Is this single-user only, or should multi-user/auth ever matter?
- Should generated-but-unsaved lessons also remain in history, or only saved ones?
- Should there be lesson states such as `draft`, `saved`, `archived`, `completed`?
- Should the app track study progress within a lesson?

### Content & Curation
- Should lessons prefer recent updates by default, or balance recency with timeless depth?
- Should the user be able to configure preferred source types, for example blogs, papers, docs, GitHub posts, conference talks?
- Should the app avoid low-signal content farms and SEO-heavy sources with an allowlist/denylist?
- Should generated lessons include exercises, reflection prompts, or action items?
- Should lessons ever include code snippets or mini projects?

### Retrieval
- Is a true crawler required, or is a hybrid of search APIs + targeted page extraction sufficient for v1?
- Should the app ingest RSS/newsletters/GitHub release notes on a schedule later?
- Should source freshness windows be configurable?

### AI Agent
- Which model/provider should the executor use?
- Should the system support swapping model providers?
- Should the user be able to inspect source evidence used by the agent?

### UX
- Should there be one trigger button with a mode selector, or separate buttons per mode?
- How much lesson metadata should be shown in lists?
- Should the active lesson be chosen automatically or manually?

## Draft Acceptance Criteria For MVP
- A user can open the app and generate a lesson from at least one of the three trigger modes.
- A generated lesson renders in-app in a readable structured format.
- A generated lesson includes a hierarchical index.
- A generated lesson includes source links.
- A generated lesson is substantial enough to guide about 1 hour of study.
- A user can save a lesson.
- A user can view previously saved lessons.
- A user can trigger a follow-up lesson based on the current active lesson.
- A user can trigger a totally new lesson.
- A user can trigger a lesson from a user-provided phrase.

## Constraints For The Coding Agent
- Do not assume unresolved product decisions are final.
- Treat items under `Confirmed Product Requirements` as the source of truth.
- Treat `Open Questions` as explicit gaps to preserve or expose through config/defaults.
- Optimize for strong lesson generation and retrieval quality before sophisticated UI work.
