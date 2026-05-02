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

/**
 * Lesson markdown is rendered through a small typed block model rather than
 * a full markdown library: the composer's output is bounded (paragraphs,
 * bullet lists, inline links/bold/code) and we control its shape, so a
 * dependency-free parser keeps the frontend minimal while still rendering
 * structured content correctly.
 *
 * If the composer ever needs to emit code blocks, tables, or nested lists,
 * swap this for `react-markdown` + `remark-gfm` — the LessonContent component
 * is the only consumer.
 */
export type InlineNode =
  | { kind: "text"; text: string }
  | { kind: "link"; text: string; href: string }
  | { kind: "bold"; text: string }
  | { kind: "code"; text: string };

export type LessonBlock =
  | { kind: "paragraph"; inline: InlineNode[] }
  | { kind: "list"; items: InlineNode[][] }
  | { kind: "subheading"; text: string };

export type MarkdownSection = {
  heading: string;
  anchor: string;
  blocks: LessonBlock[];
};

export type ParsedMarkdownLesson = {
  intro: LessonBlock[];
  sections: MarkdownSection[];
};

const INLINE_TOKEN_RE = /(\[[^\]]+\]\([^)]+\))|(\*\*[^*]+\*\*)|(`[^`]+`)/g;

function parseInline(raw: string): InlineNode[] {
  const nodes: InlineNode[] = [];
  let cursor = 0;
  for (const match of raw.matchAll(INLINE_TOKEN_RE)) {
    const matchIndex = match.index ?? 0;
    if (matchIndex > cursor) {
      nodes.push({ kind: "text", text: raw.slice(cursor, matchIndex) });
    }
    const token = match[0];
    if (token.startsWith("[")) {
      const linkMatch = /^\[([^\]]+)\]\(([^)]+)\)$/.exec(token);
      if (linkMatch) {
        nodes.push({ kind: "link", text: linkMatch[1], href: linkMatch[2] });
      } else {
        nodes.push({ kind: "text", text: token });
      }
    } else if (token.startsWith("**")) {
      nodes.push({ kind: "bold", text: token.slice(2, -2) });
    } else if (token.startsWith("`")) {
      nodes.push({ kind: "code", text: token.slice(1, -1) });
    }
    cursor = matchIndex + token.length;
  }
  if (cursor < raw.length) {
    nodes.push({ kind: "text", text: raw.slice(cursor) });
  }
  return nodes.length > 0 ? nodes : [{ kind: "text", text: raw }];
}

function blocksFromBuffer(buffer: string[]): LessonBlock[] {
  const blocks: LessonBlock[] = [];
  let paragraphLines: string[] = [];
  let listItems: InlineNode[][] | null = null;

  const flushParagraph = () => {
    if (paragraphLines.length === 0) {
      return;
    }
    const text = paragraphLines.join(" ").trim();
    paragraphLines = [];
    if (text.length === 0) {
      return;
    }
    blocks.push({ kind: "paragraph", inline: parseInline(text) });
  };

  const flushList = () => {
    if (listItems === null) {
      return;
    }
    if (listItems.length > 0) {
      blocks.push({ kind: "list", items: listItems });
    }
    listItems = null;
  };

  for (const rawLine of buffer) {
    const line = rawLine.replace(/\s+$/, "");
    if (line.trim().length === 0) {
      flushParagraph();
      flushList();
      continue;
    }
    if (line.startsWith("### ")) {
      flushParagraph();
      flushList();
      blocks.push({ kind: "subheading", text: line.slice(4).trim() });
      continue;
    }
    const listMatch = /^[-*]\s+(.+)$/.exec(line.trim());
    if (listMatch) {
      flushParagraph();
      if (listItems === null) {
        listItems = [];
      }
      listItems.push(parseInline(listMatch[1]));
      continue;
    }
    flushList();
    paragraphLines.push(line.trim());
  }

  flushParagraph();
  flushList();

  return blocks;
}

export function parseLessonMarkdown(
  contentMarkdown: string,
  toc: TocEntry[],
): ParsedMarkdownLesson {
  const lines = contentMarkdown.split("\n");
  const sections: MarkdownSection[] = [];
  let mode: "intro" | "section" = "intro";
  const introBuffer: string[] = [];
  let currentHeading = "";
  let currentBuffer: string[] = [];
  let sectionIndex = 0;
  let titleSeen = false;

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
      blocks: blocksFromBuffer(currentBuffer),
    });
    sectionIndex += 1;
    currentBuffer = [];
    currentHeading = "";
  };

  for (const line of lines) {
    if (!titleSeen && line.startsWith("# ")) {
      // Drop the lesson title line — the page chrome already shows it.
      titleSeen = true;
      continue;
    }
    if (line.startsWith("## ")) {
      if (mode === "intro") {
        mode = "section";
      } else {
        flushSection();
      }
      currentHeading = line.slice(3).trim();
      continue;
    }
    if (mode === "intro") {
      introBuffer.push(line);
    } else {
      currentBuffer.push(line);
    }
  }

  if (mode === "section") {
    flushSection();
  }

  return {
    intro: blocksFromBuffer(introBuffer),
    sections,
  };
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
