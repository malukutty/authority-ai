"use client";

import { useId, useState } from "react";
import Link from "next/link";
import type { Intake } from "@/lib/repeat/schema";

function Choice({ name, legend, options, value, onChange }: { name: string; legend: string; options: [string, string][]; value: string; onChange: (v: string) => void }) {
  return (
    <fieldset>
      <legend className="text-[0.9375rem] font-medium">{legend}</legend>
      <div className="mt-2.5 flex flex-wrap gap-2">
        {options.map(([v, l]) => (
          <label key={v} className={`cursor-pointer border px-3.5 py-2 text-sm ${value === v ? "border-ink bg-ink text-paper" : "border-rule hover:border-ink"}`}>
            <input type="radio" name={name} value={v} checked={value === v} onChange={() => onChange(v)} className="sr-only" />
            {l}
          </label>
        ))}
      </div>
    </fieldset>
  );
}

export function FeedbackForm({ reportId, intake, example }: { reportId: string; intake: Intake; example: boolean }) {
  const id = useId();
  const [f, setF] = useState({ useful: "", mostValuable: "", missing: "", useAgain: "", interview: false, email: "", consent: false, shareInputs: false, hp: "" });
  const [state, setState] = useState<{ status: "idle" | "sending" | "done" | "error"; msg?: string }>({ status: "idle" });
  const set = <K extends keyof typeof f>(k: K) => (v: (typeof f)[K]) => setF((s) => ({ ...s, [k]: v }));

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    if (f.email && !f.consent) {
      setState({ status: "error", msg: "Please tick the consent box if you'd like us to keep your email." });
      return;
    }
    setState({ status: "sending" });
    try {
      const res = await fetch("/api/repeat/feedback", {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({ ...f, reportId, example, intake: f.shareInputs && !example ? intake : undefined }),
      });
      const data = await res.json().catch(() => ({}));
      if (!res.ok) throw new Error(data.error || "We couldn't send your feedback.");
      setState({ status: "done" });
    } catch (err) {
      setState({ status: "error", msg: (err as Error).message });
    }
  }

  if (state.status === "done") {
    return (
      <section className="mt-6 border border-rule bg-paper-deep p-6 sm:p-8" role="status">
        <p className="display text-2xl">Thank you.</p>
        <p className="mt-2 text-sm leading-relaxed text-muted">
          Your feedback goes directly to the founders building Repeat.
          {f.interview && f.email ? " We'll email you about a short interview." : ""}
        </p>
      </section>
    );
  }

  return (
    <section aria-labelledby={`${id}-h`} className="mt-6 border border-rule bg-paper-deep p-6 sm:p-8">
      <p className="eyebrow">Help us improve Repeat</p>
      <h2 id={`${id}-h`} className="display mt-2 text-3xl">Was this useful?</h2>
      <p className="mt-2 text-sm text-muted">Every question is optional. Two minutes at most.</p>
      <form onSubmit={submit} className="mt-8 space-y-7" noValidate>
        <Choice name={`${id}-useful`} legend="Was this diagnostic useful?" value={f.useful} onChange={set("useful")} options={[["very", "Very useful"], ["somewhat", "Somewhat"], ["not", "Not useful"]]} />
        <div className="space-y-1.5">
          <label htmlFor={`${id}-mv`} className="block text-[0.9375rem] font-medium">Which recommendation was most valuable?</label>
          <textarea id={`${id}-mv`} className="field" rows={2} maxLength={1000} value={f.mostValuable} onChange={(e) => set("mostValuable")(e.target.value)} />
        </div>
        <div className="space-y-1.5">
          <label htmlFor={`${id}-ms`} className="block text-[0.9375rem] font-medium">What was missing or wrong?</label>
          <textarea id={`${id}-ms`} className="field" rows={3} maxLength={2000} value={f.missing} onChange={(e) => set("missing")(e.target.value)} />
        </div>
        <Choice name={`${id}-again`} legend="Would you use Repeat again?" value={f.useAgain} onChange={set("useAgain")} options={[["yes", "Yes"], ["maybe", "Maybe"], ["no", "No"]]} />

        <div className="space-y-4 border-t border-rule pt-7">
          <label className="flex items-start gap-3 text-sm">
            <input type="checkbox" className="mt-1 size-4 accent-[var(--ink)]" checked={f.interview} onChange={(e) => set("interview")(e.target.checked)} />
            <span>I&apos;d be willing to do a short (20-minute) founder interview.</span>
          </label>
          <div className="space-y-1.5">
            <label htmlFor={`${id}-em`} className="block text-[0.9375rem] font-medium">Email <span className="font-normal text-muted">(optional)</span></label>
            <input id={`${id}-em`} type="email" autoComplete="email" className="field" maxLength={254} value={f.email} onChange={(e) => set("email")(e.target.value)} />
          </div>
          {f.email && (
            <label className="flex items-start gap-3 text-sm">
              <input type="checkbox" className="mt-1 size-4 accent-[var(--ink)]" checked={f.consent} onChange={(e) => set("consent")(e.target.checked)} />
              <span>Authority AI may store my email and contact me about Repeat and this feedback. I can ask for it to be deleted at any time.</span>
            </label>
          )}
          {!example && (
            <label className="flex items-start gap-3 text-sm">
              <input type="checkbox" className="mt-1 size-4 accent-[var(--ink)]" checked={f.shareInputs} onChange={(e) => set("shareInputs")(e.target.checked)} />
              <span>Include my answers with this feedback so the team can see what the report was based on. (Off by default.)</span>
            </label>
          )}
          <div className="hidden" aria-hidden>
            <label>Leave empty<input tabIndex={-1} autoComplete="off" value={f.hp} onChange={(e) => set("hp")(e.target.value)} /></label>
          </div>
        </div>

        {state.status === "error" && <p role="alert" className="text-sm text-danger">{state.msg}</p>}
        <div className="flex flex-wrap items-center gap-4">
          <button type="submit" className="btn btn-primary" disabled={state.status === "sending"}>
            {state.status === "sending" ? "Sending…" : "Send feedback"}
          </button>
          <Link href="/privacy" className="link text-xs text-muted">How we handle your data</Link>
        </div>
      </form>
    </section>
  );
}
