const generationModes = [
  "Continue current lesson",
  "Discover something new",
  "Generate from a phrase",
];

export default function HomePage() {
  return (
    <main className="page-shell">
      <section className="hero-card">
        <p className="eyebrow">SkillRadar</p>
        <h1>Grounded lesson generation for focused SDE3 study sessions.</h1>
        <p className="lede">
          The app skeleton is ready for generation flows, lesson reading, and
          library navigation without locking us into premature UI complexity.
        </p>
      </section>

      <section className="content-grid">
        <article className="panel">
          <h2>Planned Generate Flow</h2>
          <ul>
            {generationModes.map((mode) => (
              <li key={mode}>{mode}</li>
            ))}
          </ul>
        </article>

        <article className="panel">
          <h2>Backend Status</h2>
          <p>
            FastAPI is scaffolded with a health endpoint and API prefix so the
            next tasks can layer persistence and orchestration cleanly.
          </p>
        </article>
      </section>
    </main>
  );
}

