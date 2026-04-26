"use client";

import { useState, useTransition } from "react";

type GenerationMode =
  | "continue_active_lesson"
  | "discover_new_topic"
  | "phrase_seeded";

type GenerationResult = {
  generationRequestId: string;
  lessonId: string;
  lessonTitle: string;
  lessonSummary: string;
  status: string;
  mode: GenerationMode;
  seedPhrase: string | null;
};

const generationModes: Array<{
  value: GenerationMode;
  label: string;
  description: string;
}> = [
  {
    value: "continue_active_lesson",
    label: "Continue current",
    description: "Follow the active lesson into the next practical layer.",
  },
  {
    value: "discover_new_topic",
    label: "Discover something new",
    description: "Branch into a fresh, career-useful topic.",
  },
  {
    value: "phrase_seeded",
    label: "From phrase",
    description: "Start from a phrase such as Kafka exactly-once in practice.",
  },
];

function getApiBaseUrl() {
  return process.env.NEXT_PUBLIC_SKILLRADAR_API_BASE_URL ?? "http://127.0.0.1:8000";
}

export function GenerateLessonPanel() {
  const [mode, setMode] = useState<GenerationMode>("continue_active_lesson");
  const [phrase, setPhrase] = useState("");
  const [result, setResult] = useState<GenerationResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isPending, startTransition] = useTransition();

  const isPhraseMode = mode === "phrase_seeded";

  const handleSubmit = (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setError(null);

    if (isPhraseMode && !phrase.trim()) {
      setError("Enter a phrase to generate a phrase-seeded lesson.");
      return;
    }

    startTransition(async () => {
      try {
        const response = await fetch(`${getApiBaseUrl()}/api/v1/lessons/generate`, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            mode,
            seedPhrase: isPhraseMode ? phrase.trim() : null,
          }),
        });

        if (!response.ok) {
          const fallbackMessage = "Generation request failed.";
          const payload = (await response.json().catch(() => null)) as
            | { detail?: string }
            | null;
          throw new Error(payload?.detail ?? fallbackMessage);
        }

        const payload = (await response.json()) as GenerationResult;
        setResult(payload);
      } catch (submissionError) {
        setError(
          submissionError instanceof Error
            ? submissionError.message
            : "Generation request failed.",
        );
      }
    });
  };

  return (
    <section className="hero-card">
      <p className="eyebrow">Generate</p>
      <h2>Use one focused control surface for the next lesson.</h2>
      <p className="lede">
        This view now submits real generation requests to the backend while the
        deeper retrieval and composition pipeline is still under construction.
      </p>

      <form className="generate-form" onSubmit={handleSubmit}>
        <fieldset className="mode-list">
          <legend className="sr-only">Generation mode</legend>
          {generationModes.map((option) => (
            <label key={option.value} className="mode-card selectable-card">
              <input
                type="radio"
                name="generation-mode"
                value={option.value}
                checked={mode === option.value}
                onChange={() => setMode(option.value)}
              />
              <div>
                <h3>{option.label}</h3>
                <p>{option.description}</p>
              </div>
            </label>
          ))}
        </fieldset>

        {isPhraseMode ? (
          <label className="input-stack">
            <span className="input-label">Seed phrase</span>
            <input
              className="text-input"
              value={phrase}
              onChange={(event) => setPhrase(event.target.value)}
              placeholder="Kafka exactly-once in practice"
            />
          </label>
        ) : null}

        <div className="inline-actions">
          <button type="submit" className="primary-button" disabled={isPending}>
            {isPending ? "Generating..." : "Generate lesson"}
          </button>
          <span className="muted-inline">
            Backend request records are persisted even though lesson quality is
            still placeholder-level at this stage.
          </span>
        </div>

        {error ? <p className="error-text">{error}</p> : null}

        {result ? (
          <article className="panel result-panel">
            <p className="eyebrow">Generation Result</p>
            <h3>{result.lessonTitle}</h3>
            <p>{result.lessonSummary}</p>
            <div className="result-grid">
              <div>
                <span className="result-label">Status</span>
                <p>{result.status}</p>
              </div>
              <div>
                <span className="result-label">Mode</span>
                <p>{result.mode}</p>
              </div>
              <div>
                <span className="result-label">Request ID</span>
                <p>{result.generationRequestId}</p>
              </div>
              <div>
                <span className="result-label">Lesson ID</span>
                <p>{result.lessonId}</p>
              </div>
            </div>
          </article>
        ) : null}
      </form>
    </section>
  );
}

