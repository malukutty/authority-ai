"use client";

import { useEffect, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { Field } from "./Field";
import { checkReadiness, filledCount, WIN_FIELDS, type Company, type Intake, type Motion, type Win } from "@/lib/repeat/schema";
import { emptyIntake, emptyWin, loadDraft, saveDraft, saveReport, clearAll } from "@/lib/repeat/local";
import { requestAnalysis } from "@/lib/repeat/client";

const STEPS = ["Company", "Customer wins", "Sales motion", "Review"] as const;

type Extracted = { url: string; title: string; description: string; headings: string[] };

export function IntakeFlow() {
  const router = useRouter();
  const [intake, setIntake] = useState<Intake>(emptyIntake);
  const [step, setStep] = useState(0);
  const [loaded, setLoaded] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const headingRef = useRef<HTMLHeadingElement>(null);

  useEffect(() => {
    const d = loadDraft();
    if (d?.intake) {
      setIntake(d.intake);
      setStep(Math.min(d.step ?? 0, STEPS.length - 1));
    }
    setLoaded(true);
  }, []);

  useEffect(() => {
    if (loaded) saveDraft(intake, step);
  }, [intake, step, loaded]);

  const go = (n: number) => {
    setError(null);
    setStep(n);
    window.scrollTo({ top: 0 });
    requestAnimationFrame(() => headingRef.current?.focus());
  };

  const setCompany = (k: keyof Company) => (v: string) => setIntake((s) => ({ ...s, company: { ...s.company, [k]: v } }));
  const setMotion = (k: keyof Motion) => (v: string) => setIntake((s) => ({ ...s, motion: { ...s.motion, [k]: v } }));
  const setWin = (i: number, k: keyof Win) => (v: string) =>
    setIntake((s) => ({ ...s, wins: s.wins.map((w, j) => (j === i ? { ...w, [k]: v } : w)) }));

  async function analyze() {
    const ready = checkReadiness(intake);
    if (!ready.ok) {
      setError(ready.reason);
      return;
    }
    setBusy(true);
    setError(null);
    try {
      const report = await requestAnalysis(intake);
      saveReport(report);
      router.push("/repeat/report");
    } catch (e) {
      setError((e as Error).message);
      setBusy(false);
    }
  }

  if (!loaded) return <div className="min-h-[60vh]" aria-busy="true" />;
  if (busy) return <Analyzing />;

  return (
    <div className="mx-auto max-w-2xl px-4 pb-16 pt-10 sm:px-6 sm:pt-14">
      <ol className="flex gap-1.5" aria-label="Progress">
        {STEPS.map((s, i) => (
          <li key={s} className="flex-1">
            <button
              type="button"
              onClick={() => go(i)}
              className="w-full text-left"
              aria-current={i === step ? "step" : undefined}
              aria-label={`Step ${i + 1}: ${s}`}
            >
              <span className={`block h-[3px] ${i <= step ? "bg-ink" : "bg-rule"}`} />
              <span className={`mt-2 hidden text-xs sm:block ${i === step ? "text-ink" : "text-muted"}`}>
                {i + 1}. {s}
              </span>
            </button>
          </li>
        ))}
      </ol>
      <p className="mt-3 text-xs text-muted sm:hidden">
        Step {step + 1} of {STEPS.length} · {STEPS[step]}
      </p>

      <h1 ref={headingRef} tabIndex={-1} className="display mt-10 text-4xl leading-tight outline-none sm:text-5xl">
        {["Your company", "Three recent wins", "How you sell today", "Review and analyze"][step]}
      </h1>
      <p className="mt-3 leading-relaxed text-muted">
        {
          [
            "The basics. Skip anything you don't know — every question is optional.",
            "Describe three recent customers you won. No names needed. Rough answers are fine; leave blanks where you're unsure.",
            "Six short questions about how deals move today.",
            "Check your answers. The analysis uses only what you've written here.",
          ][step]
        }
      </p>

      <div className="mt-10">
        {step === 0 && <CompanyStep company={intake.company} set={setCompany} onFill={(v) => setCompany("sells")(v)} />}
        {step === 1 && <WinsStep intake={intake} setWin={setWin} setIntake={setIntake} />}
        {step === 2 && (
          <div className="space-y-7">
            <Field multiline label="Where do most qualified leads come from?" value={intake.motion.leadSources} onChange={setMotion("leadSources")} />
            <Field multiline label="How do you decide a prospect is worth pursuing?" hint="Even 'gut feel' is a useful answer." value={intake.motion.qualification} onChange={setMotion("qualification")} />
            <Field multiline label="What usually happens between the first conversation and closing?" placeholder="e.g. intro call → demo → trial → proposal" value={intake.motion.firstCallToClose} onChange={setMotion("firstCallToClose")} />
            <Field multiline label="Where do deals commonly stall?" value={intake.motion.stalls} onChange={setMotion("stalls")} />
            <Field multiline label="Which parts of selling depend entirely on you?" value={intake.motion.founderDependent} onChange={setMotion("founderDependent")} />
            <Field multiline label="What's the biggest obstacle to winning your next 10 customers?" value={intake.motion.biggestObstacle} onChange={setMotion("biggestObstacle")} />
          </div>
        )}
        {step === 3 && <Review intake={intake} go={go} />}
      </div>

      {error && (
        <p role="alert" className="mt-8 border-l-2 border-danger pl-4 text-sm text-danger">
          {error}
        </p>
      )}

      <div className="mt-12 flex flex-wrap items-center justify-between gap-4 border-t border-rule pt-6">
        {step > 0 ? (
          <button type="button" className="btn btn-secondary" onClick={() => go(step - 1)}>
            Back
          </button>
        ) : (
          <span />
        )}
        {step < STEPS.length - 1 ? (
          <button type="button" className="btn btn-primary" onClick={() => go(step + 1)}>
            Continue
          </button>
        ) : (
          <button type="button" className="btn btn-primary" onClick={analyze} disabled={!checkReadiness(intake).ok}>
            Generate my diagnostic
          </button>
        )}
      </div>
      <p className="mt-6 text-xs leading-relaxed text-muted">
        Your answers are saved in this browser only. They are sent to our server and to our AI provider (Anthropic) to
        generate the report, and are not stored by us unless you choose to share them with feedback.{" "}
        <Link href="/privacy" className="link">Privacy</Link> ·{" "}
        <button
          type="button"
          className="link"
          onClick={() => {
            if (confirm("Clear all answers saved in this browser?")) {
              clearAll();
              setIntake(emptyIntake());
              go(0);
            }
          }}
        >
          Clear my answers
        </button>
      </p>
    </div>
  );
}

function CompanyStep({ company, set, onFill }: { company: Company; set: (k: keyof Company) => (v: string) => void; onFill: (v: string) => void }) {
  const [state, setState] = useState<{ loading: boolean; data?: Extracted; error?: string }>({ loading: false });

  async function lookup() {
    setState({ loading: true });
    try {
      const res = await fetch("/api/repeat/extract", {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({ url: company.website }),
      });
      const data = await res.json().catch(() => ({}));
      if (!res.ok) throw new Error(data.error || "We couldn't read that website.");
      setState({ loading: false, data });
    } catch (e) {
      setState({ loading: false, error: `${(e as Error).message} You can fill in the details yourself.` });
    }
  }

  const d = state.data;
  return (
    <div className="space-y-7">
      <Field label="Company name" value={company.name} onChange={set("name")} maxLength={120} />
      <div className="space-y-3">
        <Field label="Company website" hint="Optional. We can read your public homepage to help you describe what you sell." value={company.website} onChange={set("website")} maxLength={300} inputMode="url" placeholder="example.com" />
        <button type="button" className="btn btn-secondary" disabled={!company.website.trim() || state.loading} onClick={lookup}>
          {state.loading ? "Reading website…" : "Read my website"}
        </button>
        {state.error && (
          <p role="status" className="text-sm text-muted">
            {state.error}
          </p>
        )}
        {d && (
          <div className="border border-rule bg-paper-deep p-4 text-sm" role="status">
            <p className="eyebrow">Found on {new URL(d.url).hostname} — please verify</p>
            {d.title && <p className="mt-3 font-medium">{d.title}</p>}
            {d.description && <p className="mt-1 leading-relaxed text-muted">{d.description}</p>}
            {d.headings.length > 0 && (
              <ul className="mt-2 list-disc space-y-0.5 pl-5 text-muted">
                {d.headings.map((h) => (
                  <li key={h}>{h}</li>
                ))}
              </ul>
            )}
            {(d.description || d.title) && (
              <button
                type="button"
                className="link mt-3 text-sm"
                onClick={() => onFill([d.title, d.description].filter(Boolean).join(" — "))}
              >
                Use this as a starting point for &ldquo;What you sell&rdquo;
              </button>
            )}
          </div>
        )}
      </div>
      <Field multiline label="What do you sell?" hint="In plain words: the product, and the problem it solves." value={company.sells} onChange={set("sells")} />
      <Field multiline label="Who is your target customer?" value={company.targetCustomer} onChange={set("targetCustomer")} />
      <div className="grid gap-7 sm:grid-cols-3">
        <Field label="Paying customers" value={company.payingCustomers} onChange={set("payingCustomers")} maxLength={40} inputMode="numeric" placeholder="e.g. 8" />
        <Field label="Typical deal size" value={company.dealSize} onChange={set("dealSize")} maxLength={120} placeholder="e.g. $12k/yr" />
        <Field label="Sales cycle" value={company.salesCycle} onChange={set("salesCycle")} maxLength={120} placeholder="e.g. 6 weeks" />
      </div>
      <Field multiline label="Current main acquisition channels" value={company.channels} onChange={set("channels")} placeholder="e.g. founder network, referrals, LinkedIn" />
    </div>
  );
}

const WIN_QUESTIONS: { k: keyof Win; label: string; hint?: string; short?: boolean }[] = [
  { k: "segment", label: "Industry or segment", short: true },
  { k: "companySize", label: "Company size", hint: "If known.", short: true },
  { k: "discovery", label: "How did they find you?" },
  { k: "problem", label: "What problem did they want solved?" },
  { k: "trigger", label: "What made them act now?", hint: "The buying trigger: an event, deadline, failure, new hire…" },
  { k: "buyers", label: "Who was involved in the decision?", hint: "Roles, not names." },
  { k: "objection", label: "Main objection or obstacle" },
  { k: "whyChose", label: "Why do you think they chose you?" },
  { k: "timeToClose", label: "Roughly how long to close?", short: true },
];

function WinsStep({
  intake,
  setWin,
  setIntake,
}: {
  intake: Intake;
  setWin: (i: number, k: keyof Win) => (v: string) => void;
  setIntake: React.Dispatch<React.SetStateAction<Intake>>;
}) {
  const [active, setActive] = useState(0);
  const w = intake.wins[active] ?? emptyWin();
  return (
    <div>
      <div role="tablist" aria-label="Customer wins" className="flex flex-wrap gap-2">
        {intake.wins.map((win, i) => {
          const n = filledCount(win as Record<string, string>, WIN_FIELDS as string[]);
          return (
            <button
              key={i}
              role="tab"
              type="button"
              aria-selected={i === active}
              onClick={() => setActive(i)}
              className={`border px-4 py-2 text-sm ${i === active ? "border-ink bg-ink text-paper" : "border-rule hover:border-ink"}`}
            >
              Win {i + 1}
              <span className={`ml-2 text-xs ${i === active ? "opacity-70" : "text-muted"}`}>
                {n}/{WIN_FIELDS.length}
              </span>
            </button>
          );
        })}
        {intake.wins.length < 5 && (
          <button
            type="button"
            className="border border-dashed border-rule px-4 py-2 text-sm text-muted hover:border-ink hover:text-ink"
            onClick={() => {
              setIntake((s) => ({ ...s, wins: [...s.wins, emptyWin()] }));
              setActive(intake.wins.length);
            }}
          >
            + Add a win
          </button>
        )}
      </div>
      <div role="tabpanel" className="mt-8 space-y-7">
        <Field label="A label for you (optional)" hint="Something like 'Logistics co. in Ohio'. Please don't use a customer's real name." value={w.label} onChange={setWin(active, "label")} maxLength={60} />
        <div className="grid gap-7 sm:grid-cols-2">
          {WIN_QUESTIONS.filter((q) => q.short && q.k !== "timeToClose").map((q) => (
            <Field key={q.k} label={q.label} hint={q.hint} value={w[q.k]} onChange={setWin(active, q.k)} maxLength={q.k === "segment" ? 300 : 120} />
          ))}
        </div>
        {WIN_QUESTIONS.filter((q) => !q.short).map((q) => (
          <Field key={q.k} multiline label={q.label} hint={q.hint} value={w[q.k]} onChange={setWin(active, q.k)} />
        ))}
        <Field label="Roughly how long to close?" value={w.timeToClose} onChange={setWin(active, "timeToClose")} maxLength={120} placeholder="e.g. 5 weeks" />
        <div className="flex flex-wrap justify-between gap-3 text-sm">
          {intake.wins.length > 1 ? (
            <button
              type="button"
              className="link text-muted"
              onClick={() => {
                setIntake((s) => ({ ...s, wins: s.wins.filter((_, j) => j !== active) }));
                setActive(Math.max(0, active - 1));
              }}
            >
              Remove this win
            </button>
          ) : (
            <span />
          )}
          {active < intake.wins.length - 1 && (
            <button type="button" className="link" onClick={() => setActive(active + 1)}>
              Next: Win {active + 2} →
            </button>
          )}
        </div>
      </div>
    </div>
  );
}

function Review({ intake, go }: { intake: Intake; go: (n: number) => void }) {
  const ready = checkReadiness(intake);
  const winCounts = intake.wins.map((w) => filledCount(w as Record<string, string>, WIN_FIELDS as string[]));
  const rows: [string, string, number][] = [
    ["Company", `${filledCount(intake.company as Record<string, string>)} of 8 answered`, 0],
    ["Customer wins", winCounts.map((n, i) => `Win ${i + 1}: ${n}/${WIN_FIELDS.length}`).join(" · "), 1],
    ["Sales motion", `${filledCount(intake.motion as Record<string, string>)} of 6 answered`, 2],
  ];
  return (
    <div className="space-y-8">
      <dl className="divide-y divide-rule border-y border-rule">
        {rows.map(([k, v, s]) => (
          <div key={k} className="flex flex-wrap items-baseline justify-between gap-3 py-4">
            <dt className="font-medium">{k}</dt>
            <dd className="flex items-baseline gap-4 text-sm text-muted">
              <span>{v}</span>
              <button type="button" className="link text-ink" onClick={() => go(s)}>
                Edit
              </button>
            </dd>
          </div>
        ))}
      </dl>
      {ready.ok ? (
        <div className="text-sm leading-relaxed text-muted">
          <p>
            The diagnostic separates what your answers show from what is still a hypothesis. The more detail you give
            about triggers and why customers chose you, the more specific it gets.
          </p>
          {winCounts.filter((n) => n >= 3).length < 3 && (
            <p className="mt-3 text-ink">
              Fewer than three wins have much detail. You can still run it — the report will tell you what&apos;s missing.
            </p>
          )}
        </div>
      ) : (
        <p className="border-l-2 border-mark pl-4 text-sm">{ready.reason}</p>
      )}
    </div>
  );
}

function Analyzing() {
  const lines = [
    "Reading your three wins…",
    "Looking for what your customers share…",
    "Separating patterns from hunches…",
    "Reconstructing your sales process…",
    "Drafting a 30-day plan…",
  ];
  const [i, setI] = useState(0);
  useEffect(() => {
    const t = setInterval(() => setI((n) => Math.min(n + 1, lines.length - 1)), 9000);
    return () => clearInterval(t);
  }, [lines.length]);
  return (
    <div className="mx-auto flex min-h-[60vh] max-w-xl flex-col justify-center px-4 py-20 sm:px-6" role="status" aria-live="polite">
      <p className="eyebrow">Building your diagnostic</p>
      <p className="display mt-5 text-3xl leading-snug">{lines[i]}</p>
      <div className="mt-8 h-px w-full overflow-hidden bg-rule">
        <div className="h-px bg-ink transition-all duration-[9000ms] ease-linear" style={{ width: `${((i + 1) / lines.length) * 100}%` }} />
      </div>
      <p className="mt-6 text-sm text-muted">This usually takes under a minute. Please keep this tab open.</p>
    </div>
  );
}
