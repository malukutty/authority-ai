"use client";

import { useEffect, useId, useMemo, useRef, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { QUESTIONS, type BasisT, type QuestionId, type QuickReport, type QuickSession } from "@/lib/repeat/quick-schema";
import { loadDraft, mergeIntake, quickToIntake, saveDraft, saveQuick } from "@/lib/repeat/local";
import { FeedbackForm } from "./Feedback";
import { hostOf } from "./QuickStart";

const BASIS: Record<BasisT, { label: string; cls: string }> = {
  website: { label: "On your website", cls: "border-ok text-ok" },
  founder: { label: "From you", cls: "border-ink text-ink" },
  inferred: { label: "Inferred", cls: "border-dashed border-mark text-mark" },
};

function Basis({ b }: { b: BasisT }) {
  return (
    <span className={`inline-block whitespace-nowrap border px-1.5 py-px text-[0.625rem] uppercase tracking-[0.14em] ${BASIS[b].cls}`}>
      {BASIS[b].label}
    </span>
  );
}

function Section({ title, children, id }: { title: string; children: React.ReactNode; id?: string }) {
  return (
    <section id={id} className="scroll-mt-6 border-t border-rule py-8">
      <h2 className="display text-2xl leading-tight">{title}</h2>
      <div className="mt-4">{children}</div>
    </section>
  );
}

export function quickAsText(s: QuickSession) {
  const r = s.report;
  return [
    `Repeat — first read for ${r.company.name}${s.url ? ` (${hostOf(s.url)})` : ""}`,
    "",
    r.headline,
    "",
    `Draft ICP (hypothesis): ${r.icp.statement}`,
    "",
    "Three likely obstacles:",
    ...r.obstacles.map((o, i) => `${i + 1}. ${o.title} [${BASIS[o.basis].label}] — ${o.why_likely} Check: ${o.how_to_check}`),
    "",
    `Experiment: ${r.experiment.name}`,
    `Hypothesis: ${r.experiment.hypothesis}`,
    `Target: ${r.experiment.target}`,
    ...r.experiment.steps.map((st, i) => `  ${i + 1}. ${st}`),
    `Success: ${r.experiment.success_metric} (${r.experiment.timeframe})`,
  ].join("\n");
}

/** The next optional question: what the report says it needs most, then the rest of the bank. */
function nextQuestion(s: QuickSession): QuestionId | null {
  const done = (q: QuestionId) => !!s.answers[q]?.trim() || s.skipped.includes(q);
  for (const n of s.report.needed) if (n.question_id !== "other" && !done(n.question_id)) return n.question_id;
  for (const q of QUESTIONS) if (!done(q.id)) return q.id;
  return null;
}

export function QuickReportView({ initial }: { initial: QuickSession }) {
  const router = useRouter();
  const [s, setS] = useState(initial);
  const [current, setCurrent] = useState<QuestionId | null>(() => nextQuestion(initial));
  const [draft, setDraft] = useState("");
  const [updating, setUpdating] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [copied, setCopied] = useState(false);
  const [panelOpen, setPanelOpen] = useState(true);
  const id = useId();
  const answerRef = useRef<HTMLTextAreaElement>(null);
  const r = s.report;
  const answeredCount = useMemo(() => QUESTIONS.filter((q) => s.answers[q.id]?.trim()).length, [s.answers]);
  const question = QUESTIONS.find((q) => q.id === current);

  useEffect(() => saveQuick(s), [s]);

  function ask(q: QuestionId) {
    setCurrent(q);
    setDraft(s.answers[q] ?? "");
    setPanelOpen(true);
    setError(null);
    document.getElementById("improve")?.scrollIntoView({ behavior: "smooth", block: "start" });
    setTimeout(() => answerRef.current?.focus({ preventScroll: true }), 350);
  }

  function skip() {
    if (!current) return;
    const next = { ...s, skipped: [...s.skipped, current] };
    setS(next);
    setCurrent(nextQuestion(next));
    setDraft("");
    setError(null);
  }

  async function submitAnswer(e: React.FormEvent) {
    e.preventDefault();
    if (!current || !draft.trim()) return;
    setUpdating(true);
    setError(null);
    const answers = { ...s.answers, [current]: draft.trim() };
    try {
      const res = await fetch("/api/repeat/quick", {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({ url: s.url, band: s.band, manual: s.manual, answers, previousHeadline: r.headline }),
        signal: AbortSignal.timeout(110_000),
      });
      const data = await res.json().catch(() => ({}));
      if (!res.ok) throw new Error(data.error || "We couldn't update your report. Your answer is saved — try again.");
      const next: QuickSession = {
        ...s,
        answers,
        skipped: s.skipped.filter((q) => q !== current),
        report: data.report,
        model: data.model,
        mock: data.mock,
        version: s.version + 1,
        updatedAt: new Date().toISOString(),
      };
      setS(next);
      setCurrent(nextQuestion(next));
      setDraft("");
      window.scrollTo({ top: 0, behavior: "smooth" });
    } catch (err) {
      // Keep the answer so nothing typed is lost.
      setS((prev) => ({ ...prev, answers }));
      setError((err as Error).name === "TimeoutError" ? "That took too long. Your answer is saved — try again." : (err as Error).message);
    } finally {
      setUpdating(false);
    }
  }

  async function copy() {
    const text = quickAsText(s);
    try {
      await navigator.clipboard.writeText(text);
    } catch {
      const ta = document.createElement("textarea");
      ta.value = text;
      document.body.appendChild(ta);
      ta.select();
      document.execCommand("copy");
      ta.remove();
    }
    setCopied(true);
    setTimeout(() => setCopied(false), 2500);
  }

  function goDeep() {
    const fromQuick = quickToIntake(s);
    const existing = loadDraft();
    saveDraft(existing ? mergeIntake(existing.intake, fromQuick) : fromQuick, existing?.step ?? 0);
    router.push("/repeat/deep");
  }

  return (
    <div className="mx-auto max-w-6xl px-4 pb-10 pt-10 sm:px-6 sm:pt-14">
      {s.mock && (
        <div className="mb-8 border border-danger p-4 text-sm text-danger" role="note">
          Development mock: no AI model was called. This is placeholder content.
        </div>
      )}

      <div className="grid gap-10 lg:grid-cols-[minmax(0,1fr)_22rem]">
        {/* ── Report ── */}
        <article className={updating ? "opacity-60 transition-opacity" : "transition-opacity"} aria-busy={updating}>
          <p className="eyebrow">First read · {r.confidence.level} confidence</p>
          <h1 className="display mt-3 text-4xl leading-tight sm:text-5xl">{r.company.name}</h1>
          {s.site && (
            <p className="mt-2 text-sm text-muted">
              Based on {s.site.pagesRead} page{s.site.pagesRead === 1 ? "" : "s"} of {hostOf(s.site.url)}
              {answeredCount > 0 && ` and ${answeredCount} answer${answeredCount === 1 ? "" : "s"} from you`}.
            </p>
          )}
          {!s.site && <p className="mt-2 text-sm text-muted">Based on your description{answeredCount > 0 && ` and ${answeredCount} answer${answeredCount === 1 ? "" : "s"}`}.</p>}

          <p className="display mt-6 text-2xl leading-snug">{r.headline}</p>

          {r.changes.length > 0 && (
            <div className="mt-6 border-l-2 border-ok pl-4 text-sm" role="status">
              <p className="font-medium">Updated with your answer</p>
              <ul className="mt-1 list-disc space-y-0.5 pl-5 text-muted">
                {r.changes.map((c, i) => (
                  <li key={i}>{c}</li>
                ))}
              </ul>
            </div>
          )}

          <p className="mt-6 flex flex-wrap items-center gap-2 text-xs text-muted">
            Every point is labelled: <Basis b="website" /> <Basis b="founder" /> <Basis b="inferred" />
          </p>

          <div className="no-print mt-6 flex flex-wrap gap-2">
            <button type="button" className="btn btn-secondary" onClick={copy}>
              {copied ? "Copied" : "Copy report"}
            </button>
            <button type="button" className="btn btn-secondary" onClick={() => window.print()}>
              Print / save PDF
            </button>
            <a href="#improve" className="btn btn-primary lg:hidden">
              Improve my analysis
            </a>
            <span className="sr-only" aria-live="polite">{copied ? "Report copied to clipboard" : ""}</span>
          </div>

          <Section title="What we found">
            <dl className="space-y-4">
              {(
                [
                  ["What you sell", r.company.sells],
                  ["Who you appear to serve", r.company.serves],
                  ["Your stated value proposition", r.company.value_prop],
                ] as const
              ).map(([k, c]) => (
                <div key={k}>
                  <dt className="flex flex-wrap items-center gap-2 text-sm font-medium">
                    {k} <Basis b={c.basis} />
                  </dt>
                  <dd className="mt-1 leading-relaxed text-muted">{c.text}</dd>
                </div>
              ))}
            </dl>
          </Section>

          <Section title="Draft ideal customer profile">
            <p className="border-l-2 border-ink pl-4 leading-relaxed">{r.icp.statement}</p>
            <ul className="mt-4 divide-y divide-rule border-y border-rule">
              {r.icp.traits.map((t, i) => (
                <li key={i} className="py-3">
                  <div className="flex flex-wrap items-start justify-between gap-2">
                    <p className="leading-relaxed">{t.statement}</p>
                    <Basis b={t.basis} />
                  </div>
                  {t.evidence && t.evidence.toLowerCase() !== "none" && <p className="mt-1 text-sm text-muted">{t.evidence}</p>}
                </li>
              ))}
            </ul>
          </Section>

          <Section title="Three likely obstacles to repeatable revenue">
            <ol className="space-y-5">
              {r.obstacles.map((o, i) => (
                <li key={i} className="grid grid-cols-[1.75rem_1fr] gap-2">
                  <span className="display text-xl text-muted">{i + 1}</span>
                  <div>
                    <div className="flex flex-wrap items-center gap-2">
                      <p className="font-medium">{o.title}</p>
                      <Basis b={o.basis} />
                    </div>
                    <p className="mt-1 text-sm leading-relaxed">{o.why_likely}</p>
                    {o.evidence && o.evidence.toLowerCase() !== "none" && <p className="mt-1 text-sm text-muted">Evidence: {o.evidence}</p>}
                    <p className="mt-1 text-sm text-muted">
                      <span className="text-ink">How to check: </span>
                      {o.how_to_check}
                    </p>
                  </div>
                </li>
              ))}
            </ol>
          </Section>

          <Section title="One experiment to try next">
            <div className="border border-rule p-5">
              <p className="display text-xl">{r.experiment.name}</p>
              <p className="mt-2 text-sm leading-relaxed">{r.experiment.hypothesis}</p>
              <p className="mt-3 text-sm">
                <span className="text-muted">Who: </span>
                {r.experiment.target}
              </p>
              <ol className="mt-3 list-decimal space-y-1 pl-5 text-sm leading-relaxed">
                {r.experiment.steps.map((st, i) => (
                  <li key={i}>{st}</li>
                ))}
              </ol>
              <p className="mt-4 border-t border-rule pt-3 text-sm">
                <span className="font-medium">Success: </span>
                {r.experiment.success_metric} <span className="text-muted">({r.experiment.timeframe})</span>
              </p>
              <p className="mt-1 text-sm text-muted">Why this fits: {r.experiment.why}</p>
            </div>
          </Section>

          <Section title="What would make this sharper">
            <ul className="space-y-3">
              {r.needed.map((n, i) => (
                <li key={i} className="flex flex-wrap items-start justify-between gap-3 text-sm">
                  <div className="min-w-0 flex-1">
                    <p className="font-medium">{n.item}</p>
                    <p className="text-muted">{n.why_it_matters}</p>
                  </div>
                  {n.question_id !== "other" && !s.answers[n.question_id] && (
                    <button type="button" className="link no-print shrink-0 text-ink" onClick={() => ask(n.question_id as QuestionId)}>
                      Answer
                    </button>
                  )}
                </li>
              ))}
            </ul>
            <p className="mt-6 text-sm text-muted">Confidence: {r.confidence.note}</p>
            <p className="mt-2 text-xs leading-relaxed text-muted">
              Written by an AI model from your public website{answeredCount > 0 ? " and your answers" : ""}. Anything marked
              Inferred is a hypothesis to test, not a fact. It does not predict revenue.
            </p>
          </Section>
        </article>

        {/* ── Improve my analysis ── */}
        <aside id="improve" className="no-print scroll-mt-6 lg:sticky lg:top-6 lg:self-start">
          <div className="border border-rule bg-paper-deep p-5 sm:p-6">
            <div className="flex items-baseline justify-between gap-3">
              <p className="eyebrow">Improve my analysis</p>
              <button type="button" className="text-xs text-muted hover:text-ink lg:hidden" onClick={() => setPanelOpen((o) => !o)} aria-expanded={panelOpen}>
                {panelOpen ? "Hide" : "Show"}
              </button>
            </div>
            {panelOpen && (
              <>
                <p className="mt-2 text-sm text-muted">
                  Optional. Answer one at a time; each answer updates this report. Stop whenever you like.
                </p>

                {question ? (
                  <form onSubmit={submitAnswer} className="mt-5 space-y-3">
                    <label htmlFor={`${id}-a`} className="display block text-xl leading-snug">
                      {question.prompt}
                    </label>
                    {question.hint && <p className="text-xs text-muted">{question.hint}</p>}
                    <textarea
                      ref={answerRef}
                      id={`${id}-a`}
                      className="field"
                      rows={3}
                      maxLength={1000}
                      value={draft}
                      disabled={updating}
                      onChange={(e) => setDraft(e.target.value)}
                    />
                    {error && (
                      <p role="alert" className="text-sm text-danger">
                        {error}
                      </p>
                    )}
                    <div className="flex flex-wrap items-center gap-3">
                      <button type="submit" className="btn btn-primary" disabled={updating || !draft.trim()}>
                        {updating ? "Updating…" : "Update my report"}
                      </button>
                      <button type="button" className="link text-sm text-muted" onClick={skip} disabled={updating}>
                        Skip
                      </button>
                    </div>
                    {updating && (
                      <p role="status" className="text-xs text-muted">
                        Updating your report with this answer. About 20–30 seconds.
                      </p>
                    )}
                  </form>
                ) : (
                  <p className="mt-5 text-sm">You&apos;ve been through all the quick questions. Thank you.</p>
                )}

                {answeredCount > 0 && (
                  <details className="mt-6 border-t border-rule pt-4 text-sm">
                    <summary className="cursor-pointer text-muted">Your answers ({answeredCount})</summary>
                    <ul className="mt-3 space-y-3">
                      {QUESTIONS.filter((q) => s.answers[q.id]?.trim()).map((q) => (
                        <li key={q.id}>
                          <p className="text-muted">{q.prompt}</p>
                          <p className="mt-0.5">{s.answers[q.id]}</p>
                          <button type="button" className="link mt-1 text-xs" onClick={() => ask(q.id)} disabled={updating}>
                            Edit
                          </button>
                        </li>
                      ))}
                    </ul>
                  </details>
                )}

                <div className="mt-6 border-t border-rule pt-4 text-sm">
                  <p className="font-medium">Want the full diagnostic?</p>
                  <p className="mt-1 text-muted">
                    Walk through three recent customer wins for a detailed ICP, buying triggers, sales process and 30-day
                    plan. About 15 minutes; your answers here carry over.
                  </p>
                  <button type="button" className="link mt-2 text-ink" onClick={goDeep}>
                    Start the full diagnostic →
                  </button>
                </div>
              </>
            )}
          </div>
          <p className="mt-4 text-xs text-muted">
            <Link href="/repeat/start" className="link">
              Analyze a different website
            </Link>
          </p>
        </aside>
      </div>

      <div className="no-print mt-4">
        <FeedbackForm reportId={s.id} intake={quickToIntake(s)} example={false} />
      </div>
    </div>
  );
}
