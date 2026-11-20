import type { Metadata } from "next";
import Link from "next/link";
import { SiteFooter, SiteHeader } from "@/components/SiteChrome";

export const metadata: Metadata = {
  title: "About",
  description: "Authority AI exists to make business execution repeatable. Why we started, and what we are building first.",
};

// Earlier essays, published while the company explored decision infrastructure.
// Kept as an archive; their full text still lives in the previous site and needs migrating.
const PAPERS = [
  "Why Every Founder Eventually Becomes the Company's Search Engine",
  "The Hidden Cost of Searching Before Every Important Decision",
  "Dashboards Don't Help Companies Understand Themselves",
  "Companies Don't Need More Information. They Need Better Structure.",
  "Every Company Already Has Rules. Most Just Haven't Written Them Down.",
  "A Brain Is Not Where Knowledge Lives. It Is How Decisions Are Made.",
  "Growth Doesn't Make Companies Slow. Fragmented Understanding Does.",
  "Every Decision Is a Reflection of What a Company Understands",
  "Most Companies Don't Know What They Know",
  "Every Company Already Has a Brain",
];

export default function About() {
  return (
    <>
      <SiteHeader />
      <main id="main" className="mx-auto max-w-6xl px-4 sm:px-6">
        <section className="pb-16 pt-20 sm:pt-28">
          <p className="eyebrow">About</p>
          <h1 className="display mt-6 max-w-4xl text-5xl leading-[1.04] sm:text-6xl">
            Companies already know more than they act on.
          </h1>
        </section>

        <section className="grid gap-10 border-t border-rule py-16 md:grid-cols-[1fr_2fr]">
          <p className="eyebrow">What we believe</p>
          <div className="max-w-2xl space-y-5 leading-relaxed">
            <p>
              The first years of a company run on one person&apos;s judgment. The founder knows which customers are a
              fit, which objections matter, which deals are worth chasing. That judgment works, and it does not scale.
            </p>
            <p className="text-muted">
              Authority AI builds focused products that turn that kind of intelligence into systems: explicit, testable,
              and improvable by people other than the founder. Each product addresses one problem well.
            </p>
            <p className="text-muted">
              We started by studying how companies understand themselves. The lesson we kept arriving at was that
              understanding only matters when it changes what happens next. Intelligence should lead to action.
            </p>
          </div>
        </section>

        <section className="grid gap-10 border-t border-rule py-16 md:grid-cols-[1fr_2fr]">
          <p className="eyebrow">What we are building first</p>
          <div className="max-w-2xl space-y-5 leading-relaxed">
            <p>
              <span className="display text-2xl">repeat<span className="text-mark">.</span></span> helps early-stage B2B
              founders turn how they won their first customers into a sales motion they can test and hand off.
            </p>
            <p className="text-muted">
              It is early. Repeat is a working product built to test a hypothesis: that founders with five to twenty
              customers can get a useful, evidence-based plan from what they already know. We are learning from every
              founder who tries it.
            </p>
            <Link href="/repeat" className="btn btn-primary">Explore Repeat</Link>
          </div>
        </section>

        <section id="writing" className="grid scroll-mt-8 gap-10 border-t border-rule py-16 md:grid-cols-[1fr_2fr]">
          <div>
            <p className="eyebrow">Writing</p>
            <p className="mt-3 text-sm text-muted">Earlier essays on how companies understand themselves.</p>
          </div>
          <ol className="divide-y divide-rule border-y border-rule">
            {PAPERS.map((title, i) => (
              <li key={title} className="flex gap-6 py-4">
                <span className="eyebrow pt-1">{String(i + 1).padStart(3, "0")}</span>
                <span className="display text-lg leading-snug">{title}</span>
              </li>
            ))}
          </ol>
        </section>
      </main>
      <SiteFooter />
    </>
  );
}
