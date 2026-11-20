import type { Metadata } from "next";
import { SiteFooter, SiteHeader } from "@/components/SiteChrome";
import { CONTACT_EMAIL } from "@/lib/site";

export const metadata: Metadata = { title: "Privacy", description: "How Authority AI and Repeat handle your data." };

// NOTE: plain-language summary written for the MVP. Have it reviewed before relying on it legally.
export default function Privacy() {
  return (
    <>
      <SiteHeader />
      <main id="main" className="mx-auto max-w-2xl px-4 py-20 sm:px-6">
        <p className="eyebrow">Privacy</p>
        <h1 className="display mt-5 text-5xl">How we handle your data</h1>
        <p className="mt-3 text-sm text-muted">Last updated November 2026</p>
        <div className="mt-10 space-y-8 leading-relaxed">
          <section>
            <h2 className="display text-2xl">Your Repeat answers</h2>
            <p className="mt-2 text-muted">
              Answers you type into Repeat are saved in your own browser (local storage) so you can come back to them.
              When you generate a diagnostic, they are sent to our server and to our AI provider, Anthropic, to produce
              the report. We do not keep your answers or your report on our servers unless you choose to include them
              when sending feedback. Please don&apos;t enter customer names or personal information; Repeat doesn&apos;t need them.
            </p>
            <p className="mt-2 text-muted">
              You can delete what&apos;s saved in your browser at any time with &ldquo;Clear my answers&rdquo; on the intake page.
            </p>
          </section>
          <section>
            <h2 className="display text-2xl">Feedback and email</h2>
            <p className="mt-2 text-muted">
              If you send feedback, we store your answers to the feedback questions. If you give your email and tick
              the consent box, we store it and may contact you about Repeat or a founder interview. We don&apos;t sell
              it or add it to marketing lists. Ask us to delete it at any time.
            </p>
          </section>
          <section>
            <h2 className="display text-2xl">Usage limits</h2>
            <p className="mt-2 text-muted">
              To prevent abuse we log each analysis request with a one-way hash of your IP address, the time, and
              whether it succeeded. We do not store your raw IP address.
            </p>
          </section>
          <section>
            <h2 className="display text-2xl">Website lookups</h2>
            <p className="mt-2 text-muted">
              If you ask Repeat to read your website, our server fetches that public page once and shows you its title,
              description and headings. Nothing is stored.
            </p>
          </section>
          <section>
            <h2 className="display text-2xl">Contact</h2>
            <p className="mt-2 text-muted">
              Questions or deletion requests: <a className="link text-ink" href={`mailto:${CONTACT_EMAIL}`}>{CONTACT_EMAIL}</a>
            </p>
          </section>
        </div>
      </main>
      <SiteFooter />
    </>
  );
}
