"use client";

import { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import type { FindingT, StoredReport } from "@/lib/repeat/schema";
import { saveDraft, saveReport } from "@/lib/repeat/local";
import { requestAnalysis } from "@/lib/repeat/client";
import { FeedbackForm } from "./Feedback";

const GAP_LABEL: Record<string, string> = {
  qualification: "Qualification",
  undocumented_step: "Undocumented step",
  founder_dependency: "Founder dependency",
  handoff: "Handoff",
  measurement: "Measurement",
  other: "Other",
};

export function planAsText(r: StoredReport) {
  const { report: rep, intake } = r;
  const lines = [
    `Repeat — 30-day plan${intake.company.name ? ` for ${intake.company.name}` : ""}`,
    "",
    "NEXT 10 CUSTOMERS — HYPOTHESIS",
    rep.next_ten.hypothesis,
    `Who: ${rep.next_ten.who}`,
    `Trigger to watch: ${rep.next_ten.trigger_to_watch}`,
    `Channel: ${rep.next_ten.channel}`,
    `Opening angle: ${rep.next_ten.opening_angle}`,
    `How to test: ${rep.next_ten.how_to_test}`,
    `Wrong if: ${rep.next_ten.disconfirming_signal}`,
    "",
    "30-DAY PLAN",
  ];
  for (const p of rep.plan) {
    lines.push("", `Week ${p.week}: ${p.title} (owner: ${p.owner})`);
    p.actions.forEach((a) => lines.push(`  - ${a}`));
    lines.push(`  Success: ${p.success_metric}`, `  Why: ${p.rationale}`);
  }
  return lines.join("\n");
}

function Support({ s }: { s: "observed" | "hypothesis" }) {
  return s === "observed" ? (
    <span className="inline-block border border-ok px-1.5 py-px text-[0.625rem] uppercase tracking-[0.14em] text-ok">Observed</span>
  ) : (
    <span className="inline-block border border-dashed border-mark px-1.5 py-px text-[0.625rem] uppercase tracking-[0.14em] text-mark">Hypothesis</span>
  );
}

function Sources({ s }: { s: string[] }) {
  if (!s.length) return null;
  return <span className="text-xs text-muted">{s.join(" · ")}</span>;
}

function Findings({ items, empty }: { items: FindingT[]; empty?: string }) {
  if (!items.length) return <p className="text-sm text-muted">{empty ?? "Nothing identified from the information provided."}</p>;
  return (
    <ul className="divide-y divide-rule border-y border-rule">
      {items.map((f, i) => (
        <li key={i} className="py-4">
          <div className="flex flex-wrap items-center gap-x-3 gap-y-1">
            <Support s={f.support} />
            <Sources s={f.sources} />
          </div>
          <p className="mt-2 leading-relaxed">{f.statement}</p>
          {f.evidence && f.evidence.toLowerCase() !== "none" && (
            <p className="mt-1.5 text-sm leading-relaxed text-muted">
              <span className="text-ink/70">Evidence: </span>
              {f.evidence}
            </p>
          )}
        </li>
      ))}
    </ul>
  );
}

function Section({ letter, title, children, id }: { letter: string; title: string; children: React.ReactNode; id: string }) {
  return (
    <section id={id} className="grid scroll-mt-6 gap-4 border-t border-rule py-10 md:grid-cols-[12rem_1fr] md:gap-10">
      <div>
        <p className="eyebrow">{letter}</p>
        <h2 className="display mt-2 text-2xl leading-tight">{title}</h2>
      </div>
      <div className="min-w-0">{children}</div>
    </section>
  );
}

export function ReportView({ data, onReplace }: { data: StoredReport; onReplace?: (r: StoredReport) => void }) {
  const router = useRouter();
  const [copied, setCopied] = useState(false);
  const [regen, setRegen] = useState<{ busy: boolean; error?: string }>({ busy: false });
  const r = data.report;
  const isExample = !!data.example;

  async function copy() {
    const text = planAsText(data);
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

  function edit() {
    saveDraft(data.intake, 0);
    router.push("/repeat/start");
  }

  async function regenerate() {
    setRegen({ busy: true });
    try {
      const next = await requestAnalysis(data.intake);
      saveReport(next);
      onReplace?.(next);
      setRegen({ busy: false });
      window.scrollTo({ top: 0 });
    } catch (e) {
      setRegen({ busy: false, error: (e as Error).message });
    }
  }

  const created = new Date(data.createdAt);

  return (
    <div className="mx-auto max-w-5xl px-4 pb-10 pt-10 sm:px-6 sm:pt-14">
      {isExample && (
        <div className="mb-10 border border-mark bg-paper-deep p-4 text-sm leading-relaxed" role="note">
          <p className="font-medium">Illustrative example — fictional company and customers.</p>
          <p className="mt-1 text-muted">
            &ldquo;Dockett&rdquo; is invented to show what a Repeat diagnostic looks like. It is not a customer and these are not real results.{" "}
            <Link href="#inputs" className="link text-ink">See the inputs it was built from</Link>.
          </p>
        </div>
      )}
      {data.mock && (
        <div className="mb-10 border border-danger p-4 text-sm text-danger" role="note">
          Development mock: no AI model was called. This content is the example report, not an analysis of your answers.
        </div>
      )}

      <header>
        <p className="eyebrow">Repeat Revenue Diagnostic</p>
        <h1 className="display mt-4 text-4xl leading-tight sm:text-5xl">{data.intake.company.name || "Your company"}</h1>
        <p className="mt-2 text-sm text-muted">
          {isExample ? "Example" : `Generated ${created.toLocaleDateString(undefined, { dateStyle: "medium" })}`} · Based on{" "}
          {data.intake.wins.length} customer win{data.intake.wins.length === 1 ? "" : "s"} · Data:{" "}
          <span className="text-ink">{r.data_quality.level}</span>
        </p>
        <p className="display mt-8 max-w-3xl text-2xl leading-snug sm:text-[1.75rem]">{r.headline}</p>
        <p className="mt-4 max-w-3xl text-sm leading-relaxed text-muted">{r.data_quality.note}</p>
      </header>

      <div className="no-print top-0 z-10 sm:sticky -mx-4 mt-8 flex flex-wrap gap-2 border-y border-rule bg-paper/95 px-4 py-3 backdrop-blur sm:-mx-6 sm:px-6">
        <button type="button" className="btn btn-primary" onClick={copy}>
          {copied ? "Copied" : "Copy action plan"}
        </button>
        <button type="button" className="btn btn-secondary" onClick={() => window.print()}>
          Print / save PDF
        </button>
        {!isExample && (
          <>
            <button type="button" className="btn btn-secondary" onClick={edit}>
              Edit answers
            </button>
            <button type="button" className="btn btn-secondary" onClick={regenerate} disabled={regen.busy}>
              {regen.busy ? "Regenerating…" : "Regenerate"}
            </button>
          </>
        )}
        {isExample && (
          <Link href="/repeat/start" className="btn btn-secondary">
            Analyze my own sales motion
          </Link>
        )}
        <span className="sr-only" aria-live="polite">
          {copied ? "Action plan copied to clipboard" : ""}
        </span>
      </div>
      {regen.busy && (
        <p role="status" className="mt-4 text-sm text-muted">
          Regenerating from the same answers. This usually takes under a minute…
        </p>
      )}
      {regen.error && (
        <p role="alert" className="mt-4 border-l-2 border-danger pl-4 text-sm text-danger">
          {regen.error}
        </p>
      )}

      <div className={regen.busy ? "opacity-40" : ""}>
        <Section letter="A" title="Current revenue motion" id="motion">
          <p className="leading-relaxed">{r.current_motion.summary}</p>
          <div className="mt-6">
            <Findings items={r.current_motion.observations} />
          </div>
        </Section>

        <Section letter="B" title="Initial ideal customer profile" id="icp">
          <p className="border-l-2 border-ink pl-4 leading-relaxed">{r.icp.statement}</p>
          <h3 className="eyebrow mt-8 mb-3">Shared traits</h3>
          <Findings items={r.icp.traits} />
          {r.icp.exclusions.length > 0 && (
            <>
              <h3 className="eyebrow mt-8 mb-3">Possible poor fit</h3>
              <Findings items={r.icp.exclusions} />
            </>
          )}
        </Section>

        <Section letter="C" title="Buying triggers" id="triggers">
          <Findings items={r.triggers} empty="No clear buying triggers in the information provided. Ask your next customers: why now?" />
        </Section>

        <Section letter="D" title="Sales process" id="process">
          <ol className="space-y-0">
            {r.process.steps.map((s, i) => (
              <li key={i} className="relative grid grid-cols-[2rem_1fr] gap-3 pb-6">
                <span className="display text-xl text-muted">{i + 1}</span>
                <div>
                  <div className="flex flex-wrap items-center gap-x-3 gap-y-1">
                    <span className="font-medium">{s.name}</span>
                    {s.founder_dependent && (
                      <span className="bg-ink px-1.5 py-px text-[0.625rem] uppercase tracking-[0.14em] text-paper">Founder only</span>
                    )}
                    <Support s={s.support} />
                  </div>
                  <p className="mt-1 text-sm leading-relaxed text-muted">{s.description}</p>
                </div>
              </li>
            ))}
          </ol>
          <p className="mt-2 text-sm">
            <span className="text-muted">Cycle: </span>
            {r.process.typical_cycle}
          </p>
        </Section>

        <Section letter="E" title="Repeatability gaps" id="gaps">
          <ul className="divide-y divide-rule border-y border-rule">
            {r.gaps.map((g, i) => (
              <li key={i} className="py-4">
                <p className="eyebrow">{GAP_LABEL[g.category] ?? g.category}</p>
                <p className="mt-2 font-medium leading-relaxed">{g.gap}</p>
                <p className="mt-1 text-sm leading-relaxed">{g.consequence}</p>
                <p className="mt-1.5 text-sm leading-relaxed text-muted">Evidence: {g.evidence}</p>
              </li>
            ))}
          </ul>
        </Section>

        <Section letter="F" title="Your next 10 customers" id="next">
          <p className="display text-xl leading-snug">{r.next_ten.hypothesis}</p>
          <dl className="mt-6 grid gap-x-8 gap-y-5 sm:grid-cols-2">
            {(
              [
                ["Who", r.next_ten.who],
                ["Trigger to watch", r.next_ten.trigger_to_watch],
                ["Channel", r.next_ten.channel],
                ["Opening angle", r.next_ten.opening_angle],
              ] as const
            ).map(([k, v]) => (
              <div key={k}>
                <dt className="eyebrow">{k}</dt>
                <dd className="mt-1.5 text-sm leading-relaxed">{v}</dd>
              </div>
            ))}
          </dl>
          <div className="mt-6 space-y-4 border-t border-rule pt-6 text-sm leading-relaxed">
            <p><span className="font-medium">Why this follows from your wins. </span>{r.next_ten.rationale}</p>
            <p><span className="font-medium">How to test it. </span>{r.next_ten.how_to_test}</p>
            <p><span className="font-medium">It&apos;s wrong if: </span>{r.next_ten.disconfirming_signal}</p>
          </div>
        </Section>

        <Section letter="G" title="30-day execution plan" id="plan">
          <ol className="space-y-4">
            {r.plan.map((p, i) => (
              <li key={i} className="border border-rule p-5">
                <div className="flex flex-wrap items-baseline justify-between gap-2">
                  <p className="eyebrow">Week {p.week}</p>
                  <p className="text-xs text-muted">Owner: {p.owner}</p>
                </div>
                <p className="display mt-2 text-xl">{p.title}</p>
                <ul className="mt-3 list-disc space-y-1 pl-5 text-sm leading-relaxed">
                  {p.actions.map((a, j) => (
                    <li key={j}>{a}</li>
                  ))}
                </ul>
                <p className="mt-4 border-t border-rule pt-3 text-sm"><span className="font-medium">Success: </span>{p.success_metric}</p>
                <p className="mt-1 text-sm text-muted">Why: {p.rationale}</p>
              </li>
            ))}
          </ol>
        </Section>

        <Section letter="H" title="Evidence and confidence" id="confidence">
          <div className="grid gap-8 lg:grid-cols-3">
            <div>
              <h3 className="flex items-center gap-2"><Support s="observed" /><span className="text-sm">in your answers</span></h3>
              <ul className="mt-3 list-disc space-y-1.5 pl-5 text-sm leading-relaxed">{r.confidence.observed.map((x, i) => <li key={i}>{x}</li>)}</ul>
            </div>
            <div>
              <h3 className="flex items-center gap-2"><Support s="hypothesis" /><span className="text-sm">needs validation</span></h3>
              <ul className="mt-3 list-disc space-y-1.5 pl-5 text-sm leading-relaxed">{r.confidence.hypotheses.map((x, i) => <li key={i}>{x}</li>)}</ul>
            </div>
            <div>
              <h3 className="text-sm font-medium">Missing information</h3>
              <ul className="mt-3 space-y-3 text-sm leading-relaxed">
                {r.confidence.missing.map((m, i) => (
                  <li key={i}>
                    <span>{m.item}</span>
                    <span className="block text-muted">{m.why_it_matters}</span>
                  </li>
                ))}
              </ul>
            </div>
          </div>
          <p className="mt-8 text-xs leading-relaxed text-muted">
            This diagnostic is generated by an AI model from {isExample ? "fictional" : "your"} answers only. With a small
            number of customers, patterns are signals to test, not established facts. It does not predict revenue.
          </p>
        </Section>

        {isExample && <ExampleInputs data={data} />}
      </div>

      <div className="no-print">
        <FeedbackForm reportId={data.id} intake={data.intake} example={isExample} />
      </div>
    </div>
  );
}

function ExampleInputs({ data }: { data: StoredReport }) {
  const { company, wins, motion } = data.intake;
  return (
    <section id="inputs" className="scroll-mt-6 border-t border-rule py-10">
      <p className="eyebrow">Fictional inputs</p>
      <h2 className="display mt-2 text-2xl">What the founder entered</h2>
      <details className="mt-6 border border-rule p-4 text-sm leading-relaxed">
        <summary className="cursor-pointer font-medium">Show the example answers</summary>
        <div className="mt-4 space-y-5">
          <p><b>Sells:</b> {company.sells} <br /><b>Target:</b> {company.targetCustomer} · <b>Customers:</b> {company.payingCustomers} · <b>Deal size:</b> {company.dealSize}</p>
          {wins.map((w, i) => (
            <p key={i}>
              <b>Win {i + 1} — {w.label}.</b> Found us: {w.discovery}. Problem: {w.problem}. Trigger: {w.trigger}. Buyers: {w.buyers}. Objection: {w.objection}. Why us: {w.whyChose}. Close: {w.timeToClose}.
            </p>
          ))}
          <p><b>Sales motion.</b> Leads: {motion.leadSources} Qualification: {motion.qualification} Process: {motion.firstCallToClose}. Stalls: {motion.stalls} Founder-only: {motion.founderDependent} Obstacle: {motion.biggestObstacle}</p>
        </div>
      </details>
    </section>
  );
}
