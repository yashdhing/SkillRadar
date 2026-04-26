import Link from "next/link";

import { libraryLessons } from "../data/mock-lessons";

export default function LibraryPage() {
  return (
    <main className="page-shell">
      <section className="section-stack">
        <div className="section-heading">
          <p className="eyebrow">Lesson Library</p>
          <h2>Browse saved and recent lessons.</h2>
          <p className="lede">
            This route gives the app a real library surface for older lessons
            before persistence-backed queries arrive in later tasks.
          </p>
        </div>

        <div className="lesson-list">
          {libraryLessons.map((lesson) => (
            <article key={lesson.id} className="lesson-card">
              <div className="lesson-card-meta">
                <span className="pill">{lesson.topicLabel}</span>
                <span className="muted-inline">{lesson.updatedAtLabel}</span>
              </div>
              <h3>{lesson.title}</h3>
              <p>{lesson.summary}</p>
              <div className="lesson-card-footer">
                <span className="muted-inline">
                  {lesson.estimatedStudyMinutes} min study session
                </span>
                <span className="muted-inline">
                  {lesson.status === "saved" ? "Saved" : "Generated"}
                </span>
                <Link href={`/lessons/${lesson.id}`} className="text-link">
                  Open lesson
                </Link>
              </div>
            </article>
          ))}
        </div>
      </section>
    </main>
  );
}

