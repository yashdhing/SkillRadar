"use client";

import Link from "next/link";
import { use, useEffect, useState, useTransition } from "react";

import { LessonContent } from "../../components/lesson-content";
import {
  fetchLessonDetail,
  parseLessonMarkdown,
  saveLesson,
  type LessonDetail,
} from "../../lib/lessons-api";

type LessonReaderPageProps = {
  params: Promise<{
    lessonId: string;
  }>;
};

export default function LessonReaderPage({ params }: LessonReaderPageProps) {
  const { lessonId } = use(params);
  const [lesson, setLesson] = useState<LessonDetail | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [notFound, setNotFound] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const [saveError, setSaveError] = useState<string | null>(null);
  const [saveMessage, setSaveMessage] = useState<string | null>(null);
  const [isSaving, startSaveTransition] = useTransition();

  useEffect(() => {
    let isMounted = true;

    const load = async () => {
      try {
        const detail = await fetchLessonDetail(lessonId);
        if (isMounted) {
          setLesson(detail);
          setError(null);
          setNotFound(false);
        }
      } catch (loadError) {
        if (!isMounted) {
          return;
        }
        const message =
          loadError instanceof Error
            ? loadError.message
            : "Failed to load the lesson.";
        if (message === "Lesson not found.") {
          setNotFound(true);
        } else {
          setError(message);
        }
      } finally {
        if (isMounted) {
          setIsLoading(false);
        }
      }
    };

    void load();

    return () => {
      isMounted = false;
    };
  }, [lessonId]);

  const handleSave = () => {
    if (!lesson) {
      return;
    }
    setSaveError(null);
    setSaveMessage(null);
    startSaveTransition(async () => {
      try {
        const updated = await saveLesson(lesson.lessonId);
        setLesson(updated);
        setSaveMessage("Lesson saved to your library.");
      } catch (saveErr) {
        setSaveError(
          saveErr instanceof Error ? saveErr.message : "Failed to save lesson.",
        );
      }
    });
  };

  if (isLoading) {
    return (
      <main className="page-shell">
        <p className="lede compact">Loading lesson.</p>
      </main>
    );
  }

  if (notFound) {
    return (
      <main className="page-shell">
        <p className="inline-note">
          That lesson could not be found. It may have been removed.
        </p>
        <p>
          <Link href="/library" className="text-link">
            Back to library
          </Link>
        </p>
      </main>
    );
  }

  if (error || !lesson) {
    return (
      <main className="page-shell">
        <p className="error-text">{error ?? "Failed to load the lesson."}</p>
        <p>
          <Link href="/library" className="text-link">
            Back to library
          </Link>
        </p>
      </main>
    );
  }

  const parsed = parseLessonMarkdown(lesson.contentMarkdown, lesson.toc);
  const isSaved = lesson.status === "saved";

  return (
    <main className="page-shell">
      <div className="reader-grid">
        <aside className="reader-sidebar panel">
          <p className="eyebrow">Lesson Index</p>
          <h2>{lesson.title}</h2>
          <p className="lede compact">{lesson.whyThisMatters}</p>

          <nav aria-label="Lesson table of contents">
            <ul className="toc-list">
              {lesson.toc.map((entry) => (
                <li key={entry.anchor}>
                  <a href={`#${entry.anchor}`} className="text-link">
                    {entry.title}
                  </a>
                </li>
              ))}
            </ul>
          </nav>

          <div className="sidebar-actions">
            <Link href="/library" className="secondary-button">
              Back to library
            </Link>
            <button
              type="button"
              className="primary-button"
              onClick={handleSave}
              disabled={isSaving || isSaved}
            >
              {isSaved ? "Saved" : isSaving ? "Saving..." : "Save lesson"}
            </button>
          </div>
          {saveMessage ? (
            <p className="success-text">{saveMessage}</p>
          ) : null}
          {saveError ? <p className="error-text">{saveError}</p> : null}
        </aside>

        <article className="reader-content panel">
          <div className="reader-meta">
            <span className="pill">{lesson.mode}</span>
            <span className="muted-inline">
              {lesson.estimatedStudyMinutes} min
            </span>
            <span className="muted-inline">
              {lesson.isActive ? "Current active lesson" : "Available lesson"}
            </span>
            <span className="muted-inline">
              {isSaved ? "Saved" : "Generated"}
            </span>
          </div>

          <p className="eyebrow">Lesson Reader</p>
          <h2>{lesson.title}</h2>
          <p className="lede">{lesson.summary}</p>

          {parsed.intro.length > 0 ? (
            <section className="reader-section">
              <LessonContent blocks={parsed.intro} />
            </section>
          ) : null}

          {parsed.sections.map((section) => (
            <section
              key={section.anchor}
              id={section.anchor}
              className="reader-section"
            >
              <h3>{section.heading}</h3>
              <LessonContent blocks={section.blocks} />
            </section>
          ))}

          <section className="reader-section" id="grounding-sources">
            <h3>Grounding Sources</h3>
            {lesson.sources.length > 0 ? (
              <ul className="source-list">
                {lesson.sources.map((source) => (
                  <li key={source.sourceId}>
                    <a
                      href={source.url}
                      target="_blank"
                      rel="noreferrer"
                      className="text-link"
                    >
                      {source.title}
                    </a>
                    {source.domain ? (
                      <span className="muted-inline">
                        {" "}
                        — {source.domain}
                      </span>
                    ) : null}
                    {source.author ? (
                      <span className="muted-inline">
                        {" by "}
                        {source.author}
                      </span>
                    ) : null}
                  </li>
                ))}
              </ul>
            ) : (
              <p className="muted-inline">
                No grounded sources are attached to this lesson yet.
              </p>
            )}
          </section>
        </article>
      </div>
    </main>
  );
}
