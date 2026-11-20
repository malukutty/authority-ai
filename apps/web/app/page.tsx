import Link from "next/link";
import { SiteFooter, SiteHeader } from "@/components/SiteChrome";

export default function Home() {
  return (
    <>
      <SiteHeader />
      <main id="main">
        <section className="mx-auto max-w-6xl px-4 pb-20 pt-20 sm:px-6 sm:pt-28">
          <p className="eyebrow">Authority AI</p>
          <h1 className="display mt-6 max-w-4xl text-5xl leading-[1.02] sm:text-7xl">
            Intelligence should lead to action.
          </h1>
          <p className="mt-8 max-w-2xl text-lg leading-relaxed text-muted">
            We believe the next generation of companies will operate through intelligent systems that turn knowledge
            into execution and measurable outcomes.
          </p>
          <div className="mt-10 flex flex-wrap items-center gap-5">
            <Link href="/repeat" className="btn btn-primary">Explore Repeat</Link>
            <Link href="#philosophy" className="link text-sm">Read our philosophy</Link>
          </div>
        </section>

        <section id="philosophy" className="scroll-mt-8 border-t border-rule">
          <div className="mx-auto grid max-w-6xl gap-10 px-4 py-20 sm:px-6 md:grid-cols-[1fr_2fr]">
            <p className="eyebrow">Philosophy</p>
            <div className="space-y-12">
              <div>
                <h2 className="display text-3xl leading-tight sm:text-4xl">Knowing is not the bottleneck. Acting on it is.</h2>
                <p className="mt-5 max-w-2xl leading-relaxed text-muted">
                  Most companies already hold the intelligence they need: why customers buy, where deals stall, what
                  worked last quarter. It lives in the founder&apos;s head, in scattered notes, in instinct. Very little
                  of it becomes a system someone else can run.
                </p>
              </div>
              <ol className="grid gap-px border border-rule bg-rule sm:grid-cols-3">
                {[
                  ["01", "Understand", "Capture what actually happened, from the evidence a company already has."],
                  ["02", "Systematize", "Turn recurring patterns into explicit rules, steps, and owners."],
                  ["03", "Improve", "Run the system, measure the outcome, and learn from what changes."],
                ].map(([n, t, d]) => (
                  <li key={n} className="bg-paper p-6">
                    <span className="eyebrow">{n}</span>
                    <p className="display mt-3 text-2xl">{t}</p>
                    <p className="mt-2 text-sm leading-relaxed text-muted">{d}</p>
                  </li>
                ))}
              </ol>
              <div>
                <p className="eyebrow">Mission</p>
                <p className="display mt-3 text-3xl leading-snug sm:text-4xl">Make business execution repeatable.</p>
              </div>
            </div>
          </div>
        </section>

        <section id="products" className="scroll-mt-8 border-t border-rule bg-paper-deep">
          <div className="mx-auto grid max-w-6xl gap-10 px-4 py-20 sm:px-6 md:grid-cols-[1fr_2fr]">
            <p className="eyebrow">Our first product</p>
            <div>
              <p className="display text-6xl tracking-tight sm:text-7xl">
                repeat<span className="text-mark">.</span>
              </p>
              <p className="display mt-6 text-2xl leading-snug sm:text-3xl">Turn your first customers into repeatable revenue.</p>
              <p className="mt-5 max-w-2xl leading-relaxed text-muted">
                For B2B founders with their first handful of paying customers. Repeat looks at how those customers were
                actually won, separates real patterns from hunches, and turns them into a sales motion you can test
                over the next 30 days.
              </p>
              <div className="mt-8 flex flex-wrap items-center gap-5">
                <Link href="/repeat" className="btn btn-primary">Explore Repeat</Link>
                <Link href="/repeat/example" className="link text-sm">See an example report</Link>
              </div>
            </div>
          </div>
        </section>
      </main>
      <SiteFooter />
    </>
  );
}
