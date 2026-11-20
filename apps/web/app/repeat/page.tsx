import Link from "next/link";

const STEPS = [
  ["Describe three wins", "How each customer found you, what made them act, who decided, and why they chose you. No customer names needed."],
  ["Get a diagnostic", "Your draft ICP, buying triggers and sales process, with every finding marked as observed or still a hypothesis."],
  ["Run a 30-day plan", "Four weekly experiments with owners and measurable success criteria, built from your own evidence."],
];

export default function RepeatLanding() {
  return (
    <>
      <section className="mx-auto max-w-6xl px-4 pb-20 pt-20 sm:px-6 sm:pt-28">
        <p className="eyebrow">For B2B founders with their first 5–20 customers</p>
        <h1 className="display mt-6 max-w-4xl text-5xl leading-[1.03] sm:text-7xl">
          You won your first customers. Now make it repeatable.
        </h1>
        <p className="mt-8 max-w-2xl text-lg leading-relaxed text-muted">
          Repeat helps B2B founders understand how their first customers were won, identify patterns worth testing, and
          build a more structured approach to winning the next ones.
        </p>
        <div className="mt-10 flex flex-wrap items-center gap-4">
          <Link href="/repeat/start" className="btn btn-primary">Analyze My Sales Motion</Link>
          <Link href="/repeat/example" className="btn btn-secondary">See Example Report</Link>
        </div>
        <p className="mt-5 text-sm text-muted">Free · About 15 minutes · No account needed</p>
      </section>

      <section className="border-t border-rule">
        <div className="mx-auto grid max-w-6xl gap-10 px-4 py-20 sm:px-6 md:grid-cols-[1fr_2fr]">
          <p className="eyebrow">The problem</p>
          <div className="max-w-2xl space-y-5 leading-relaxed">
            <p className="display text-3xl leading-snug">Your first customers were won by you. That doesn&apos;t scale on its own.</p>
            <p className="text-muted">
              Early deals close through relationships, instinct and a lot of founder effort. You know why customers buy,
              but it isn&apos;t written down anywhere. Which accounts to chase, which triggers matter, what actually
              converts: it all lives in your head.
            </p>
            <p className="text-muted">
              Repeat turns what you already know about your wins into something you can test, measure, and eventually hand off.
            </p>
          </div>
        </div>
      </section>

      <section className="border-t border-rule">
        <div className="mx-auto max-w-6xl px-4 py-20 sm:px-6">
          <p className="eyebrow">How it works</p>
          <ol className="mt-8 grid gap-px border border-rule bg-rule md:grid-cols-3">
            {STEPS.map(([t, d], i) => (
              <li key={t} className="bg-paper p-6 sm:p-8">
                <span className="display text-3xl text-muted">{i + 1}</span>
                <p className="display mt-4 text-2xl">{t}</p>
                <p className="mt-3 text-sm leading-relaxed text-muted">{d}</p>
              </li>
            ))}
          </ol>
        </div>
      </section>

      <section className="border-t border-rule bg-paper-deep">
        <div className="mx-auto grid max-w-6xl gap-10 px-4 py-20 sm:px-6 md:grid-cols-[1fr_2fr]">
          <p className="eyebrow">What makes it different</p>
          <ul className="max-w-2xl space-y-6 leading-relaxed">
            <li>
              <p className="font-medium">Grounded in your evidence.</p>
              <p className="text-muted">Every finding cites the win it came from. Nothing is invented about your customers.</p>
            </li>
            <li>
              <p className="font-medium">Honest about uncertainty.</p>
              <p className="text-muted">Three customers can&apos;t prove a pattern. Repeat separates what you&apos;ve observed from what you still need to test, and says what&apos;s missing.</p>
            </li>
            <li>
              <p className="font-medium">Built to act on.</p>
              <p className="text-muted">You leave with one acquisition hypothesis and a 30-day plan, not a slide of generic advice.</p>
            </li>
          </ul>
        </div>
      </section>

      <section className="border-t border-rule">
        <div className="mx-auto max-w-6xl px-4 py-20 sm:px-6">
          <p className="display max-w-3xl text-3xl leading-snug sm:text-4xl">Start with what you already know.</p>
          <div className="mt-8 flex flex-wrap items-center gap-4">
            <Link href="/repeat/start" className="btn btn-primary">Analyze My Sales Motion</Link>
            <Link href="/repeat/example" className="link text-sm">See Example Report</Link>
          </div>
          <p className="mt-8 max-w-2xl text-xs leading-relaxed text-muted">
            Repeat is an early product. It produces a diagnostic and a plan to test; it does not guarantee results.
            Your answers stay in your browser and are only used to generate your report.{" "}
            <Link href="/privacy" className="link">Privacy</Link>
          </p>
        </div>
      </section>
    </>
  );
}
