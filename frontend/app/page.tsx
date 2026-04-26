import Link from "next/link";

import { GenerateLessonPanel } from "./components/generate-lesson-panel";
import { libraryLessons } from "./data/mock-lessons";

export default function HomePage() {
  const activeLesson = libraryLessons.find((lesson) => lesson.isActive);

  return (
    <main className="page-shell">
      <div className="content-grid home-grid">
        <GenerateLessonPanel />

        <section className="section-stack">
          <article className="panel">
            <p className="eyebrow">Current Active Lesson</p>
            {activeLesson ? (
              <>
                <h2>{activeLesson.title}</h2>
                <p className="lede compact">{activeLesson.summary}</p>
                <div className="inline-actions">
                  <span className="pill">{activeLesson.topicLabel}</span>
                  <Link
                    href={`/lessons/${activeLesson.id}`}
                    className="secondary-button"
                  >
                    Open reader
                  </Link>
                </div>
              </>
            ) : (
              <p className="lede compact">
                No active lesson yet. Later tasks will connect this state to
                persistence and explicit activation flows.
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
