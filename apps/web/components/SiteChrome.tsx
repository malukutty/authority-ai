import Link from "next/link";
import Image from "next/image";
import { companyHref } from "@/lib/site";

export function AuthorityLogo() {
  return (
    <Link href={companyHref("/")} className="flex items-center gap-2.5" aria-label="Authority AI home">
      <Image src="/authority-mark.png" alt="" width={22} height={22} className="dark:invert" priority />
      <span className="display text-[1.05rem] tracking-tight">Authority AI</span>
    </Link>
  );
}

export function SiteHeader() {
  return (
    <header className="no-print border-b border-rule">
      <div className="mx-auto flex max-w-6xl items-center justify-between gap-4 px-4 py-4 sm:px-6">
        <AuthorityLogo />
        <nav aria-label="Primary" className="flex items-center gap-4 text-[0.8125rem] sm:gap-7">
          <Link href={companyHref("/#philosophy")} className="hidden text-muted hover:text-ink sm:inline">Philosophy</Link>
          <Link href={companyHref("/#products")} className="hidden text-muted hover:text-ink sm:inline">Products</Link>
          <Link href={companyHref("/about")} className="text-muted hover:text-ink">About</Link>
          <Link href="/repeat" className="whitespace-nowrap border-b border-ink pb-0.5">Explore Repeat</Link>
        </nav>
      </div>
    </header>
  );
}

export function RepeatWordmark({ size = "md", href = "/repeat" }: { size?: "md" | "lg"; href?: string | null }) {
  const word = (
    <span className={`display font-normal tracking-tight ${size === "lg" ? "text-5xl sm:text-6xl" : "text-[1.35rem]"}`}>
      repeat<span className="text-mark">.</span>
    </span>
  );
  return href ? <Link href={href} aria-label="Repeat home">{word}</Link> : word;
}

export function RepeatHeader() {
  return (
    <header className="no-print border-b border-rule">
      <div className="mx-auto flex max-w-6xl items-center justify-between gap-4 px-4 py-3.5 sm:px-6">
        <div className="flex items-baseline gap-2.5">
          <RepeatWordmark />
          <Link href={companyHref("/")} className="hidden text-[0.6875rem] uppercase tracking-[0.2em] text-muted hover:text-ink sm:inline">
            by authority ai
          </Link>
        </div>
        <nav aria-label="Repeat" className="flex items-center gap-4 text-[0.8125rem] sm:gap-6">
          <Link href="/repeat/example" className="whitespace-nowrap text-muted hover:text-ink">
            Example<span className="hidden sm:inline"> report</span>
          </Link>
          <Link href="/repeat/start" className="whitespace-nowrap border-b border-ink pb-0.5">
            <span className="sm:hidden">Start</span>
            <span className="hidden sm:inline">Analyze my sales motion</span>
          </Link>
        </nav>
      </div>
    </header>
  );
}

export function SiteFooter() {
  return (
    <footer className="no-print mt-24 border-t border-rule">
      <div className="mx-auto flex max-w-6xl flex-col gap-6 px-4 py-10 text-[0.8125rem] text-muted sm:flex-row sm:items-center sm:justify-between sm:px-6">
        <div className="flex items-center gap-3">
          <span className="display text-ink">Authority AI</span>
          <span aria-hidden>·</span>
          <span>Intelligence should lead to action.</span>
        </div>
        <nav aria-label="Footer" className="flex flex-wrap gap-5">
          <Link href="/repeat" className="hover:text-ink">Repeat</Link>
          <Link href={companyHref("/about")} className="hover:text-ink">About</Link>
          <Link href="/privacy" className="hover:text-ink">Privacy</Link>
        </nav>
      </div>
    </footer>
  );
}
