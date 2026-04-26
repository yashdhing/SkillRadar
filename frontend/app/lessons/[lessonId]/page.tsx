import Link from "next/link";
import { notFound } from "next/navigation";

import { getLessonById } from "../../data/mock-lessons";

type LessonReaderPageProps = {
  params: Promise<{
    lessonId: string;
  }>;
};

export default async function LessonReaderPage({
  params,
}: LessonReaderPageProps) {
  const { lessonId } = await params;
  const lesson = getLessonById(lessonId);

  if (!lesson) {
    notFound();
  }

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
            <button type="button" className="primary-button" disabled>
              Save lesson
            </button>
          </div>
        </aside>

        <article className="reader-content panel">
          <div className="reader-meta">
            <span className="pill">{lesson.topicLabel}</span>
            <span className="muted-inline">
              {lesson.estimatedStudyMinutes} min
            </span>
            <span className="muted-inline">
              {lesson.isActive ? "Current active lesson" : "Available lesson"}
            </span>
          </div>

          <p className="eyebrow">Lesson Reader</p>
          <h2>{lesson.title}</h2>
          <p className="lede">{lesson.summary}</p>

          {lesson.sections.map((section) => (
            <section
              key={section.anchor}
              id={section.anchor}
              className="reader-section"
            >
              <h3>{section.heading}</h3>
              {section.body.map((paragraph) => (
                <p key={paragraph}>{paragraph}</p>
              ))}
            </section>
          ))}

          <section className="reader-section">
            <h3>Source References</h3>
            <ul className="source-list">
              {lesson.sourceLinks.map((source) => (
                <li key={source.href}>
                  <a
                    href={source.href}
                    target="_blank"
                    rel="noreferrer"
                    className="text-link"
                  >
                    {source.label}
                  </a>
                </li>
              ))}
            </ul>
          </section>
        </article>
      </div>
    </main>
  );
}

