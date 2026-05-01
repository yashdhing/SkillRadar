"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import {
  ActiveLessonSummary,
  GenerateLessonPanel,
} from "./components/generate-lesson-panel";

function getApiBaseUrl() {
  return process.env.NEXT_PUBLIC_SKILLRADAR_API_BASE_URL ?? "http://127.0.0.1:8000";
}

export default function HomePage() {
  const [activeLesson, setActiveLesson] = useState<ActiveLessonSummary | null>(null);
  const [isLoadingActiveLesson, setIsLoadingActiveLesson] = useState(true);
  const [activeLessonError, setActiveLessonError] = useState<string | null>(null);

  useEffect(() => {
    let isMounted = true;

    const loadActiveLesson = async () => {
      try {
        const response = await fetch(`${getApiBaseUrl()}/api/v1/lessons/active`, {
          cache: "no-store",
        });

        if (response.status === 404) {
          if (isMounted) {
            setActiveLesson(null);
            setActiveLessonError(null);
          }
          return;
        }

        if (!response.ok) {
          const payload = (await response.json().catch(() => null)) as
            | { detail?: string }
            | null;
          throw new Error(payload?.detail ?? "Failed to load the active lesson.");
        }

        const payload = (await response.json()) as ActiveLessonSummary;
        if (isMounted) {
          setActiveLesson(payload);
          setActiveLessonError(null);
        }
      } catch (loadingError) {
        if (isMounted) {
          setActiveLessonError(
            loadingError instanceof Error
              ? loadingError.message
              : "Failed to load the active lesson.",
          );
        }
      } finally {
        if (isMounted) {
          setIsLoadingActiveLesson(false);
        }
      }
    };

    void loadActiveLesson();

    return () => {
      isMounted = false;
    };
  }, []);

  return (
    <main className="page-shell">
      <div className="content-grid home-grid">
        <GenerateLessonPanel
          activeLesson={activeLesson}
          onActiveLessonChange={setActiveLesson}
        />

        <section className="section-stack">
          <article className="panel">
            <p className="eyebrow">Current Active Lesson</p>
            {isLoadingActiveLesson ? (
              <p className="lede compact">
                Loading the persisted active lesson state.
              </p>
            ) : activeLessonError ? (
              <p className="error-text">{activeLessonError}</p>
            ) : activeLesson ? (
              <>
                <h2>{activeLesson.title}</h2>
                <p className="lede compact">{activeLesson.summary}</p>
                <div className="inline-actions">
                  <span className="pill">{activeLesson.mode}</span>
                  <span className="muted-inline">
                    {activeLesson.estimatedStudyMinutes} min read
                  </span>
                  <Link
                    href={`/lessons/${activeLesson.lessonId}`}
                    className="secondary-button"
                  >
                    Open reader
                  </Link>
                </div>
              </>
            ) : (
              <p className="lede compact">
                No active lesson yet. Continue current will fall back to a
                profile-guided draft until you mark one lesson active.
              </p>
            )}
          </article>

          <article className="panel">
            <p className="eyebrow">Library Access</p>
            <h2>Jump back into previous study sessions.</h2>
            <p className="lede compact">
              The library route is live with lesson summaries and reader links.
            </p>
            <Link href="/library" className="text-link">
              Browse lesson library
            </Link>
          </article>
        </section>
      </div>
    </main>
  );
}
