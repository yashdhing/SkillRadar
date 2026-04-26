export type LessonListItem = {
  id: string;
  title: string;
  summary: string;
  status: "saved" | "generated";
  mode:
    | "continue_active_lesson"
    | "discover_new_topic"
    | "phrase_seeded";
  estimatedStudyMinutes: number;
  topicLabel: string;
  isActive: boolean;
  updatedAtLabel: string;
};

export type TocEntry = {
  title: string;
  anchor: string;
  depth: number;
};

export type LessonDetail = LessonListItem & {
  whyThisMatters: string;
  sourceLinks: Array<{
    label: string;
    href: string;
  }>;
  sections: Array<{
    heading: string;
    anchor: string;
    body: string[];
  }>;
  toc: TocEntry[];
};

export const mockLessons: LessonDetail[] = [
  {
    id: "jvm-latency-investigation",
    title: "JVM Latency Investigation Patterns",
    summary:
      "A practical study path for diagnosing long-tail latency in Java services under real production pressure.",
    status: "saved",
    mode: "continue_active_lesson",
    estimatedStudyMinutes: 60,
    topicLabel: "Java / Reliability",
    isActive: true,
    updatedAtLabel: "Updated today",
    whyThisMatters:
      "This connects directly to senior backend ownership, on-call investigation depth, and performance tradeoffs in Java-heavy systems.",
    sourceLinks: [
      {
        label: "JDK Documentation",
        href: "https://docs.oracle.com/en/java/",
      },
      {
        label: "Netflix Tech Blog",
        href: "https://netflixtechblog.com/",
      },
      {
        label: "OpenTelemetry Java Docs",
        href: "https://opentelemetry.io/docs/instrumentation/java/",
      },
    ],
    toc: [
      { title: "Context", anchor: "context", depth: 1 },
      { title: "Signals To Capture", anchor: "signals", depth: 1 },
      { title: "Failure Modes", anchor: "failure-modes", depth: 1 },
      { title: "Applied Exercises", anchor: "applied-exercises", depth: 1 },
    ],
    sections: [
      {
        heading: "Context",
        anchor: "context",
        body: [
          "Latency work at SDE3 level is rarely about a single knob. The real task is building a reliable investigation sequence that separates CPU saturation, allocator pressure, lock contention, downstream dependencies, and traffic-shape anomalies.",
          "A useful lesson reader should make that context easy to scan in-app before we wire real generated markdown and citations.",
        ],
      },
      {
        heading: "Signals To Capture",
        anchor: "signals",
        body: [
          "Capture request latency percentiles, thread-pool queue depth, GC pause distribution, allocation rate, hot endpoints, and top downstream waits before touching configuration.",
          "The ordering matters: first confirm whether the tail is systemic, bursty, or route-specific, then decide whether to inspect JVM internals or distributed-system dependencies.",
        ],
      },
      {
        heading: "Failure Modes",
        anchor: "failure-modes",
        body: [
          "Common traps include blaming GC for downstream stalls, reading averages instead of tails, and overfitting one incident into a permanent tuning rule.",
          "A lesson structure that highlights tradeoffs and anti-patterns will matter later when generated content becomes much richer.",
        ],
      },
      {
        heading: "Applied Exercises",
        anchor: "applied-exercises",
        body: [
          "Compare one incident from your own systems against the investigation checklist and note which signals would have shortened time-to-root-cause.",
          "Sketch how you would instrument one Java service to make the next JVM latency incident easier to debug.",
        ],
      },
    ],
  },
  {
    id: "ai-coding-agents-backend-teams",
    title: "AI Coding Agents For Backend Teams",
    summary:
      "An exploratory lesson on where coding agents add leverage for design review, incident follow-up, and delivery workflows.",
    status: "generated",
    mode: "phrase_seeded",
    estimatedStudyMinutes: 55,
    topicLabel: "AI Workflows",
    isActive: false,
    updatedAtLabel: "Generated recently",
    whyThisMatters:
      "This is adjacent to platform leverage and engineering leadership, especially for standardizing high-signal workflows across teams.",
    sourceLinks: [
      {
        label: "Anthropic Engineering",
        href: "https://www.anthropic.com/engineering",
      },
      {
        label: "OpenAI Research",
        href: "https://openai.com/research/",
      },
    ],
    toc: [
      { title: "Adoption Criteria", anchor: "adoption-criteria", depth: 1 },
      { title: "Risks", anchor: "risks", depth: 1 },
    ],
    sections: [
      {
        heading: "Adoption Criteria",
        anchor: "adoption-criteria",
        body: [
          "The most durable backend-team uses tend to be bounded: test generation, migration drafting, investigation scaffolds, review assistance, and documentation refreshes.",
        ],
      },
      {
        heading: "Risks",
        anchor: "risks",
        body: [
          "Low-trust usage patterns often come from weak grounding, hidden assumptions, and lack of ownership boundaries. The product architecture should keep those concerns visible.",
        ],
      },
    ],
  },
];

export function getLessonById(id: string): LessonDetail | undefined {
  return mockLessons.find((lesson) => lesson.id === id);
}

export const libraryLessons: LessonListItem[] = mockLessons.map((lesson) => ({
  id: lesson.id,
  title: lesson.title,
  summary: lesson.summary,
  status: lesson.status,
  mode: lesson.mode,
  estimatedStudyMinutes: lesson.estimatedStudyMinutes,
  topicLabel: lesson.topicLabel,
  isActive: lesson.isActive,
  updatedAtLabel: lesson.updatedAtLabel,
}));
