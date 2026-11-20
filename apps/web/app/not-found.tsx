import Link from "next/link";
import { SiteFooter, SiteHeader } from "@/components/SiteChrome";

export default function NotFound() {
  return (
    <>
      <SiteHeader />
      <main id="main" className="mx-auto max-w-xl px-4 py-28 sm:px-6">
        <p className="eyebrow">404</p>
        <h1 className="display mt-4 text-4xl">This page doesn&apos;t exist.</h1>
        <div className="mt-8 flex gap-4">
          <Link href="/" className="btn btn-primary">Home</Link>
          <Link href="/repeat" className="btn btn-secondary">Explore Repeat</Link>
        </div>
      </main>
      <SiteFooter />
    </>
  );
}
