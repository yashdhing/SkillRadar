export type LessonMode =
  | "continue_active_lesson"
  | "discover_new_topic"
  | "phrase_seeded";

export type LessonStatus = "generated" | "saved" | "archived";

export type LessonListItem = {
  lessonId: string;
  title: string;
  summary: string;
  mode: LessonMode;
  status: LessonStatus;
  seedPhrase: string | null;
  estimatedStudyMinutes: number;
  isActive: boolean;
  savedAt: string | null;
  createdAt: string;
  updatedAt: string;
};

export type TocEntry = {
  title: string;
  anchor: string;
  depth: number;
};

export type LessonSource = {
  sourceId: string;
  url: string;
  title: string;
  domain: string | null;
  author: string | null;
};

export type LessonDetail = {
  lessonId: string;
  title: string;
  slug: string;
  summary: string;
  whyThisMatters: string;
  mode: LessonMode;
  status: LessonStatus;
  seedPhrase: string | null;
  estimatedStudyMinutes: number;
  isActive: boolean;
  savedAt: string | null;
  createdAt: string;
  updatedAt: string;
  contentMarkdown: string;
  toc: TocEntry[];
  sources: LessonSource[];
};

export type LessonListResponse = {
  items: LessonListItem[];
};

export function getApiBaseUrl(): string {
  return (
    process.env.NEXT_PUBLIC_SKILLRADAR_API_BASE_URL ?? "http://127.0.0.1:8000"
  );
}

async function readErrorDetail(response: Response, fallback: string): Promise<string> {
  const payload = (await response.json().catch(() => null)) as
    | { detail?: string }
    | null;
  return payload?.detail ?? fallback;
}

export async function fetchLessons(): Promise<LessonListItem[]> {
  const response = await fetch(`${getApiBaseUrl()}/api/v1/lessons`, {
    cache: "no-store",
  });
  if (!response.ok) {
    throw new Error(await readErrorDetail(response, "Failed to load lessons."));
  }
  const payload = (await response.json()) as LessonListResponse;
  return payload.items;
}

export async function fetchLessonDetail(lessonId: string): Promise<LessonDetail> {
  const response = await fetch(
    `${getApiBaseUrl()}/api/v1/lessons/${encodeURIComponent(lessonId)}`,
    { cache: "no-store" },
  );
  if (!response.ok) {
    throw new Error(
      await readErrorDetail(response, "Failed to load the lesson."),
    );
  }
  return (await response.json()) as LessonDetail;
}

export async function saveLesson(lessonId: string): Promise<LessonDetail> {
  const response = await fetch(
    `${getApiBaseUrl()}/api/v1/lessons/${encodeURIComponent(lessonId)}/save`,
    { method: "POST" },
  );
  if (!response.ok) {
    throw new Error(
      await readErrorDetail(response, "Failed to save lesson."),
    );
  }
  return (await response.json()) as LessonDetail;
}

export type MarkdownSection = {
  heading: string;
  anchor: string;
  body: string[];
};

export type ParsedMarkdownLesson = {
  intro: string[];
  sections: MarkdownSection[];
};

function paragraphsFromBlock(block: string): string[] {
  return block
    .split(/\n{2,}/)
    .map((paragraph) => paragraph.trim())
    .filter((paragraph) => paragraph.length > 0);
}

export function parseLessonMarkdown(
  contentMarkdown: string,
  toc: TocEntry[],
): ParsedMarkdownLesson {
  const lines = contentMarkdown.split("\n");
  const intro: string[] = [];
  const sections: MarkdownSection[] = [];
  let mode: "intro" | "section" = "intro";
  let currentHeading = "";
  let currentBuffer: string[] = [];
  let sectionIndex = 0;

  const flushSection = () => {
    if (mode !== "section") {
      return;
    }
    const tocEntry = toc[sectionIndex];
    const slugFromHeading = currentHeading
      .toLowerCase()
      .replace(/[^a-z0-9]+/g, "-")
      .replace(/^-+|-+$/g, "");
    const anchor =
      tocEntry?.anchor ||
      slugFromHeading ||
      `section-${sectionIndex + 1}`;
    sections.push({
      heading: currentHeading || tocEntry?.title || `Section ${sectionIndex + 1}`,
      anchor,
      body: paragraphsFromBlock(currentBuffer.join("\n")),
    });
    sectionIndex += 1;
    currentBuffer = [];
    currentHeading = "";
  };

  for (const line of lines) {
    if (line.startsWith("# ") && mode === "intro" && intro.length === 0) {
      // Title line — drop, the UI already shows the lesson title.
      continue;
    }
    if (line.startsWith("## ")) {
      if (mode === "intro") {
        intro.push(...paragraphsFromBlock(currentBuffer.join("\n")));
        currentBuffer = [];
        mode = "section";
      } else {
        flushSection();
      }
      currentHeading = line.slice(3).trim();
      continue;
    }
    currentBuffer.push(line);
  }

  if (mode === "intro") {
    intro.push(...paragraphsFromBlock(currentBuffer.join("\n")));
  } else {
    flushSection();
  }

  return { intro, sections };
}

export function formatRelativeUpdatedAt(updatedAt: string): string {
  const updated = new Date(updatedAt);
  if (Number.isNaN(updated.getTime())) {
    return "Recently updated";
  }
  const diffMs = Date.now() - updated.getTime();
  const minutes = Math.floor(diffMs / 60_000);
  if (minutes < 1) {
    return "Just now";
  }
  if (minutes < 60) {
    return `${minutes} min ago`;
  }
  const hours = Math.floor(minutes / 60);
  if (hours < 24) {
    return `${hours} hr ago`;
  }
  const days = Math.floor(hours / 24);
  if (days < 30) {
    return `${days} day${days === 1 ? "" : "s"} ago`;
  }
  return updated.toLocaleDateString();
}
