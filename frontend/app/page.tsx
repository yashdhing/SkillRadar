import Link from "next/link";

import { libraryLessons } from "./data/mock-lessons";

const generationModes = [
  {
    title: "Continue current",
    description: "Follow the active lesson into the next practical layer.",
  },
  {
    title: "Discover something new",
    description: "Branch into a fresh, career-useful topic.",
  },
  {
    title: "From phrase",
    description: "Start from a phrase such as Kafka exactly-once in practice.",
  },
];

export default function HomePage() {
  const activeLesson = libraryLessons.find((lesson) => lesson.isActive);

  return (
    <main className="page-shell">
      <div className="content-grid home-grid">
        <section className="hero-card">
          <p className="eyebrow">Generate</p>
          <h2>Use one focused control surface for the next lesson.</h2>
          <p className="lede">
            This view is now the dedicated generate surface. Later tasks can
            wire real request submission into the same structure.
          </p>

          <div className="mode-list">
            {generationModes.map((mode) => (
              <article key={mode.title} className="mode-card">
                <h3>{mode.title}</h3>
                <p>{mode.description}</p>
              </article>
            ))}
          </div>
        </section>

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

