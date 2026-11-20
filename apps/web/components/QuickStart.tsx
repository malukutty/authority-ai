"use client";

import { useEffect, useId, useRef, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { BAND_LABEL, CUSTOMER_BANDS, type CustomerBand, type QuickReport, type QuickSession } from "@/lib/repeat/quick-schema";
import { loadQuick, saveQuick } from "@/lib/repeat/local";

type Phase =
  | { kind: "form" }
  | { kind: "reading" }
  | { kind: "writing"; site: { url: string; title: string; pagesRead: number } | null }
  | { kind: "manual"; reason: string };

type QuickResponse = {
  report: QuickReport;
  model: string;
  mock?: boolean;
  site: { url: string; title: string; pagesRead: number } | null;
};

async function post<T>(path: string, body: unknown, timeoutMs: number): Promise<{ ok: true; data: T } | { ok: false; error: string; code?: string }> {
  const ctrl = new AbortController();
  const timer = setTimeout(() => ctrl.abort(), timeoutMs);
  try {
    const res = await fetch(path, {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify(body),
      signal: ctrl.signal,
    });
    const data = await res.json().catch(() => ({}));
    if (!res.ok) return { ok: false, error: data.error || "Something went wrong. Please try again.", code: data.code };
    return { ok: true, data: data as T };
  } catch (e) {
    return {
      ok: false,
      error: (e as Error).name === "AbortError" ? "That took too long. Please try again." : "We couldn't reach the server. Check your connection.",
    };
  } finally {
    clearTimeout(timer);
  }
}

export const hostOf = (u: string) => {
  try {
    return new URL(/^https?:\/\//i.test(u) ? u : `https://${u}`).hostname.replace(/^www\./, "");
  } catch {
    return u;
  }
};

/**
 * The two-input start. `page`: the full /repeat/start screen. `card`: embedded in the landing page.
 */
export function QuickStart({ variant = "page" }: { variant?: "page" | "card" }) {
  const card = variant === "card";
  const router = useRouter();
  const id = useId();
  const [url, setUrl] = useState("");
  const [band, setBand] = useState<CustomerBand | "">("");
  const [manual, setManual] = useState({ sells: "", serves: "" });
  const [phase, setPhase] = useState<Phase>({ kind: "form" });
  const [error, setError] = useState<string | null>(null);
  const [existing, setExisting] = useState<QuickSession | null>(null);
  const statusRef = useRef<HTMLDivElement>(null);

  useEffect(() => setExisting(loadQuick()), []);

  async function writeReport(payload: { url: string; band: CustomerBand; manual?: { sells: string; serves: string } }) {
    const res = await post<QuickResponse>("/api/repeat/quick", { ...payload, answers: {} }, 110_000);
    if (!res.ok) {
      if (res.code === "site_unreadable") {
        setPhase({ kind: "manual", reason: res.error });
        return;
      }
      setError(res.error);
      setPhase(payload.manual ? { kind: "manual", reason: "" } : { kind: "form" });
      return;
    }
    const session: QuickSession = {
      id: crypto.randomUUID(),
      url: payload.url,
      band: payload.band,
      manual: payload.manual,
      answers: {},
      skipped: [],
      site: res.data.site ?? undefined,
      report: res.data.report,
      version: 1,
      updatedAt: new Date().toISOString(),
      model: res.data.model,
      mock: res.data.mock,
    };
    saveQuick(session);
    router.push("/repeat/snapshot");
  }

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    if (!url.trim()) return setError("Enter your company's website.");
    if (!band) return setError("Choose how many paying customers you have.");
    setPhase({ kind: "reading" });
    requestAnimationFrame(() => statusRef.current?.focus());

    const site = await post<{ url: string; title: string; pagesRead: number; readable: boolean }>("/api/repeat/site", { url }, 30_000);
    if (!site.ok) {
      setPhase({ kind: "manual", reason: site.error });
      return;
    }
    if (!site.data.readable) {
      setPhase({ kind: "manual", reason: `${hostOf(site.data.url)} doesn't have enough readable text for us to analyze. It may be built to render in the browser.` });
      return;
    }
    setPhase({ kind: "writing", site: { url: site.data.url, title: site.data.title, pagesRead: site.data.pagesRead } });
    await writeReport({ url, band });
  }

  async function submitManual(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    if (!manual.sells.trim()) return setError("Tell us in a sentence what you sell.");
    if (!band) return setError("Choose how many paying customers you have.");
    setPhase({ kind: "writing", site: null });
    await writeReport({ url, band, manual });
  }

  const busy = phase.kind === "reading" || phase.kind === "writing";

  return (
    <div className={card ? "" : "mx-auto max-w-xl px-4 pb-20 pt-12 sm:px-6 sm:pt-20"}>
      {card ? (
        <>
          <p className="eyebrow">Start here · free</p>
          <h2 className="display mt-3 text-[1.75rem] leading-tight">See your revenue motion in under a minute.</h2>
        </>
      ) : (
        <>
          <p className="eyebrow">Free · No account · No email</p>
          <h1 className="display mt-4 text-4xl leading-tight sm:text-5xl">See your revenue motion in under a minute.</h1>
          <p className="mt-4 leading-relaxed text-muted">
            Give us your website. We&apos;ll read it and send back a first read: who you seem to serve, three likely
            obstacles to repeatable revenue, and one experiment to try next.
          </p>
        </>
      )}

      {phase.kind !== "manual" && (
        <form onSubmit={submit} className={card ? "mt-6 space-y-5" : "mt-10 space-y-7"} noValidate aria-busy={busy}>
          <div className="space-y-1.5">
            <label htmlFor={`${id}-url`} className="block text-[0.9375rem] font-medium">
              Company website
            </label>
            <input
              id={`${id}-url`}
              className="field"
              type="text"
              inputMode="url"
              autoComplete="url"
              autoCapitalize="none"
              spellCheck={false}
              placeholder="yourcompany.com"
              maxLength={300}
              value={url}
              disabled={busy}
              onChange={(e) => setUrl(e.target.value)}
            />
          </div>

          <fieldset disabled={busy}>
            <legend className="text-[0.9375rem] font-medium">Paying customers today</legend>
            <div className="mt-2.5 grid grid-cols-4 gap-2">
              {CUSTOMER_BANDS.map((b) => (
                <label
                  key={b}
                  className={`cursor-pointer border py-2.5 text-center text-sm ${band === b ? "border-ink bg-ink text-paper" : "border-rule hover:border-ink"}`}
                >
                  <input type="radio" name={`${id}-band`} value={b} checked={band === b} onChange={() => setBand(b)} className="sr-only" />
                  {BAND_LABEL[b]}
                </label>
              ))}
            </div>
          </fieldset>

          {error && (
            <p role="alert" className="border-l-2 border-danger pl-4 text-sm text-danger">
              {error}
            </p>
          )}

          <button type="submit" className="btn btn-primary w-full sm:w-auto" disabled={busy}>
            {busy ? "Analyzing…" : "Analyze My Revenue Motion"}
          </button>

          {busy && (
            <div ref={statusRef} tabIndex={-1} role="status" aria-live="polite" className="border-l-2 border-ink pl-4 text-sm leading-relaxed outline-none">
              {phase.kind === "reading" ? (
                <p>Reading {hostOf(url)}…</p>
              ) : (
                <>
                  {phase.kind === "writing" && phase.site && (
                    <p>
                      Read {phase.site.pagesRead} page{phase.site.pagesRead === 1 ? "" : "s"} from{" "}
                      <span className="font-medium">{phase.site.title || hostOf(phase.site.url)}</span>.
                    </p>
                  )}
                  <p className="text-muted">Writing your first read. This usually takes 20–30 seconds.</p>
                </>
              )}
            </div>
          )}
        </form>
      )}

      {phase.kind === "manual" && (
        <form onSubmit={submitManual} className="mt-10 space-y-6" noValidate>
          <div className="border border-rule bg-paper-deep p-4 text-sm leading-relaxed" role="status">
            <p className="font-medium">We couldn&apos;t read enough from your website.</p>
            {phase.reason && <p className="mt-1 text-muted">{phase.reason}</p>}
            <p className="mt-1 text-muted">Two sentences will do instead.</p>
          </div>
          <div className="space-y-1.5">
            <label htmlFor={`${id}-sells`} className="block text-[0.9375rem] font-medium">
              What do you sell?
            </label>
            <textarea
              id={`${id}-sells`}
              className="field"
              rows={2}
              maxLength={600}
              placeholder="e.g. Scheduling software that replaces spreadsheets for on-call rotas"
              value={manual.sells}
              onChange={(e) => setManual((m) => ({ ...m, sells: e.target.value }))}
            />
          </div>
          <div className="space-y-1.5">
            <label htmlFor={`${id}-serves`} className="block text-[0.9375rem] font-medium">
              Who is it for? <span className="font-normal text-muted">(optional)</span>
            </label>
            <textarea
              id={`${id}-serves`}
              className="field"
              rows={2}
              maxLength={600}
              placeholder="e.g. Veterinary hospital groups with 3–15 locations"
              value={manual.serves}
              onChange={(e) => setManual((m) => ({ ...m, serves: e.target.value }))}
            />
          </div>
          {!band && (
            <fieldset>
              <legend className="text-[0.9375rem] font-medium">Paying customers today</legend>
              <div className="mt-2.5 grid grid-cols-4 gap-2">
                {CUSTOMER_BANDS.map((b) => (
                  <label key={b} className="cursor-pointer border border-rule py-2.5 text-center text-sm hover:border-ink">
                    <input type="radio" name={`${id}-band2`} value={b} onChange={() => setBand(b)} className="sr-only" />
                    {BAND_LABEL[b]}
                  </label>
                ))}
              </div>
            </fieldset>
          )}
          {error && (
            <p role="alert" className="border-l-2 border-danger pl-4 text-sm text-danger">
              {error}
            </p>
          )}
          <div className="flex flex-wrap items-center gap-4">
            <button type="submit" className="btn btn-primary">
              Analyze My Revenue Motion
            </button>
            <button type="button" className="link text-sm" onClick={() => { setError(null); setPhase({ kind: "form" }); }}>
              Try a different website
            </button>
          </div>
        </form>
      )}

      {phase.kind === "form" && existing && (
        <p className={`${card ? "mt-6" : "mt-10"} border-t border-rule pt-6 text-sm text-muted`}>
          You have a report for {hostOf(existing.url) || existing.report.company.name}.{" "}
          <Link href="/repeat/snapshot" className="link text-ink">
            Open it
          </Link>
        </p>
      )}

      {card ? (
        <p className="mt-5 text-xs leading-relaxed text-muted">
          No account or email. We read your public website, nothing else.{" "}
          <Link href="/privacy" className="link">
            Privacy
          </Link>
        </p>
      ) : (
        <p className="mt-10 text-xs leading-relaxed text-muted">
          We read only your public website. Your report is kept in this browser, not on our servers. The website text and
          any answers you add are sent to our AI provider (Anthropic) to write the report.{" "}
          <Link href="/privacy" className="link">
            Privacy
          </Link>
        </p>
      )}
    </div>
  );
}
