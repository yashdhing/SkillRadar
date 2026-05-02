"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import {
  fetchLessons,
  formatRelativeUpdatedAt,
  type LessonListItem,
} from "../lib/lessons-api";

export default function LibraryPage() {
  const [lessons, setLessons] = useState<LessonListItem[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    let isMounted = true;

    const load = async () => {
      try {
        const items = await fetchLessons();
        if (isMounted) {
          setLessons(items);
          setError(null);
        }
      } catch (loadError) {
        if (isMounted) {
          setError(
            loadError instanceof Error
              ? loadError.message
              : "Failed to load lessons.",
          );
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
  }, []);

  return (
    <main className="page-shell">
      <section className="section-stack">
        <div className="section-heading">
          <p className="eyebrow">Lesson Library</p>
          <h2>Browse generated and saved lessons.</h2>
          <p className="lede">
            This list is now backed by the persistence layer so old lessons stay
            accessible after they are generated.
          </p>
        </div>

        {isLoading ? (
          <p className="lede compact">Loading lessons.</p>
        ) : error ? (
          <p className="error-text">{error}</p>
        ) : lessons && lessons.length > 0 ? (
          <div className="lesson-list">
            {lessons.map((lesson) => (
              <article key={lesson.lessonId} className="lesson-card">
                <div className="lesson-card-meta">
                  <span className="pill">{lesson.mode}</span>
                  <span className="muted-inline">
                    {formatRelativeUpdatedAt(lesson.updatedAt)}
                  </span>
                  {lesson.isActive ? (
                    <span className="pill">Active</span>
                  ) : null}
                </div>
                <h3>{lesson.title}</h3>
                <p>{lesson.summary}</p>
                <div className="lesson-card-footer">
                  <span className="muted-inline">
                    {lesson.estimatedStudyMinutes} min study session
                  </span>
                  <span className="muted-inline">
                    {lesson.status === "saved"
                      ? "Saved"
                      : lesson.status === "archived"
                      ? "Archived"
                      : "Generated"}
                  </span>
                  {lesson.seedPhrase ? (
                    <span className="muted-inline">
                      Seed: {lesson.seedPhrase}
                    </span>
                  ) : null}
                  <Link
                    href={`/lessons/${lesson.lessonId}`}
                    className="text-link"
                  >
                    Open lesson
                  </Link>
                </div>
              </article>
            ))}
          </div>
        ) : (
          <p className="inline-note">
            No lessons yet. Generate one from the home view to see it here.
          </p>
        )}
      </section>
    </main>
  );
}
