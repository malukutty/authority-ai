import Image from "next/image";
import Link from "next/link";
import { QuickStart } from "@/components/QuickStart";
import { FOUNDER, SHOW_PLACEHOLDERS, founderField } from "@/lib/founder";

/* Direction B: founder-led. A short note from the founder, the two-input start beside it. */

const PATTERNS = [
  {
    quote: "“We'll hire a salesperson.”",
    text: "But there's no playbook to hand them, so they spend months rediscovering what the founder already knew.",
  },
  {
    quote: "“Everyone could use this.”",
    text: "So the ideal customer is everyone, outreach is generic, and the specific reason your best customers bought gets lost.",
  },
  {
    quote: "“I just know when a deal is real.”",
    text: "Qualification is instinct. It works, and nobody else can use it.",
  },
];

const GIVES = [
  ["Who to chase", "A draft ideal customer profile, as a hypothesis to test."],
  ["What's in the way", "Three likely obstacles to repeatable revenue, and how to check each one."],
  ["What to try", "One experiment for your next customers, with a number to hit."],
];

function Signature() {
  const name = founderField(FOUNDER.name, "[YOUR NAME]");
  if (!name) return null;
  const background = founderField(FOUNDER.background, "[Your revenue-operations background, one line]");
  return (
    <div className="mt-10 flex items-center gap-4">
      {FOUNDER.photo ? (
        <Image src={FOUNDER.photo} alt={name} width={64} height={64} className="size-16 rounded-full object-cover" />
      ) : SHOW_PLACEHOLDERS ? (
        <div aria-hidden className="flex size-16 shrink-0 items-center justify-center rounded-full bg-paper-deep text-[0.625rem] text-muted">
          [PHOTO]
        </div>
      ) : null}
      <div>
        <p className="display text-[1.375rem]">{name}</p>
        <p className="mt-0.5 text-sm text-muted">
          {FOUNDER.title || "Founder, Authority AI"}
          {background ? ` · ${background}` : ""}
        </p>
      </div>
    </div>
  );
}

export default function RepeatLanding() {
  const calendar = founderField(FOUNDER.calendarUrl, "#");

  return (
    <>
      <section className="mx-auto max-w-6xl px-4 pb-20 pt-14 sm:px-6 sm:pt-20">
        <div className="grid items-start gap-12 lg:grid-cols-[minmax(0,1.35fr)_minmax(0,1fr)] lg:gap-16">
          <div>
            <p className="eyebrow">A note from the founder</p>
            <h1 className="display mt-5 text-5xl leading-[1.03] sm:text-6xl lg:text-[4rem]">
              Your first ten customers came from you.
            </h1>
            <p className="display mt-4 text-2xl italic leading-snug text-mark sm:text-3xl">That&apos;s the problem worth solving.</p>
            {/* On phones the form sits below the note: give an immediate way to it. */}
            <a href="#try" className="btn btn-primary mt-6 w-full lg:hidden">
              Analyze My Revenue Motion
            </a>
            <div className="mt-8 max-w-xl space-y-4 text-lg leading-relaxed">
              <p>
                Most founders win their first customers the same way: their network, their instinct, and a lot of late
                nights. It works. Then they try to win the next ten, and realise none of it is written down.
              </p>
              <p className="text-muted">
                Which customers to chase. What made the last three buy when they did. Where deals quietly die. It all
                lives in the founder&apos;s head, so it can&apos;t be tested, measured or handed to anyone else.
              </p>
              <p className="text-muted">Repeat is built to get it out of your head and into something you can run.</p>
            </div>
            <Signature />
          </div>

          <aside id="try" className="scroll-mt-6 border border-rule bg-paper p-6 shadow-[0_24px_48px_-32px_rgba(30,28,25,0.35)] sm:p-8 dark:bg-paper-deep">
            <QuickStart variant="card" />
          </aside>
        </div>
      </section>

      <section id="why" className="scroll-mt-6 border-t border-rule bg-paper-deep">
        <div className="mx-auto max-w-6xl px-4 py-20 sm:px-6">
          <p className="eyebrow">What keeps happening</p>
          <div className="mt-8 grid gap-10 md:grid-cols-3">
            {PATTERNS.map((p) => (
              <div key={p.quote}>
                <p className="display text-[1.625rem] leading-snug">{p.quote}</p>
                <p className="mt-3 leading-relaxed text-muted">{p.text}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      <section className="mx-auto max-w-6xl px-4 py-20 sm:px-6">
        <p className="eyebrow">What Repeat gives you</p>
        <h2 className="display mt-3 max-w-3xl text-4xl leading-tight">
          A first read in under a minute. A sharper one every time you answer a question.
        </h2>
        <ol className="mt-10 grid gap-px border border-rule bg-rule md:grid-cols-3">
          {GIVES.map(([t, d], i) => (
            <li key={t} className="bg-paper p-6 sm:p-8">
              <span className="display text-3xl text-mark">{i + 1}</span>
              <p className="mt-3 font-medium">{t}</p>
              <p className="mt-2 text-sm leading-relaxed text-muted">{d}</p>
            </li>
          ))}
        </ol>
        <p className="mt-6 max-w-3xl text-sm leading-relaxed text-muted">
          Every line is labelled as stated on your website, from you, or inferred. Nothing about your customers or numbers
          is invented. When you want more depth, the optional full diagnostic walks through three of your recent wins.{" "}
          <Link href="/repeat/example" className="link text-ink">
            See an example
          </Link>
        </p>
      </section>

      {calendar && (
        // -mb-24 cancels the footer's top margin so the dark band meets the footer directly.
        <section id="talk" className="-mb-24 scroll-mt-6 bg-ink text-paper">
          <div className="mx-auto flex max-w-6xl flex-wrap items-center justify-between gap-10 px-4 py-20 sm:px-6">
            <div className="max-w-2xl">
              <p className="text-[0.6875rem] uppercase tracking-[0.22em] opacity-70">Rather talk it through?</p>
              <h2 className="display mt-4 text-4xl leading-tight">
                Twenty minutes {FOUNDER.name.trim() ? `with ${FOUNDER.name.trim().split(/\s+/)[0]}` : "with the founder"}, on your
                last three wins.
              </h2>
              <p className="mt-4 leading-relaxed opacity-80">
                We&apos;ll go through how they actually closed, and you&apos;ll leave with the pattern written down. No
                pitch: we&apos;re learning what founders need.
              </p>
            </div>
            <div className="flex flex-col items-start gap-3">
              <a
                href={calendar}
                target={calendar.startsWith("http") ? "_blank" : undefined}
                rel="noopener noreferrer"
                className="inline-flex min-h-12 items-center bg-paper px-6 font-medium text-ink hover:opacity-90"
              >
                Book 20 minutes{SHOW_PLACEHOLDERS && !FOUNDER.calendarUrl ? " [CALENDAR LINK]" : ""}
              </a>
              <a href="#try" className="text-sm underline underline-offset-4 opacity-80 hover:opacity-100">
                Or try Repeat yourself first
              </a>
            </div>
          </div>
        </section>
      )}
    </>
  );
}
