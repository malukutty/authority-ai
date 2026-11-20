"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { QuickReportView } from "@/components/QuickReportView";
import { loadQuick } from "@/lib/repeat/local";
import type { QuickSession } from "@/lib/repeat/quick-schema";

export default function SnapshotPage() {
  const [session, setSession] = useState<QuickSession | null | undefined>(undefined);
  useEffect(() => {
    setSession(loadQuick());
    document.title = "Your first read | repeat. by Authority AI";
  }, []);

  if (session === undefined) return <div className="min-h-[60vh]" aria-busy="true" />;
  if (!session)
    return (
      <div className="mx-auto max-w-xl px-4 py-24 sm:px-6">
        <p className="eyebrow">No report yet</p>
        <h1 className="display mt-4 text-4xl">There&apos;s no report in this browser.</h1>
        <p className="mt-4 leading-relaxed text-muted">Reports are kept only in the browser where they were created.</p>
        <div className="mt-8 flex flex-wrap gap-4">
          <Link href="/repeat/start" className="btn btn-primary">Analyze My Revenue Motion</Link>
          <Link href="/repeat/example" className="btn btn-secondary">See Example Report</Link>
        </div>
      </div>
    );
  return <QuickReportView initial={session} />;
}
