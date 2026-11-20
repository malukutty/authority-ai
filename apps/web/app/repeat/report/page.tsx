"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { ReportView } from "@/components/Report";
import { loadReport } from "@/lib/repeat/local";
import type { StoredReport } from "@/lib/repeat/schema";

export default function ReportPage() {
  const [data, setData] = useState<StoredReport | null | undefined>(undefined);
  useEffect(() => {
    setData(loadReport());
    document.title = "Your diagnostic | repeat. by Authority AI";
  }, []);

  if (data === undefined) return <div className="min-h-[60vh]" aria-busy="true" />;
  if (!data)
    return (
      <div className="mx-auto max-w-xl px-4 py-24 sm:px-6">
        <p className="eyebrow">No report yet</p>
        <h1 className="display mt-4 text-4xl">There&apos;s no diagnostic in this browser.</h1>
        <p className="mt-4 leading-relaxed text-muted">
          Reports are kept only in the browser where they were created. Start a new one, or look at the example.
        </p>
        <div className="mt-8 flex flex-wrap gap-4">
          <Link href="/repeat/start" className="btn btn-primary">Analyze my sales motion</Link>
          <Link href="/repeat/example" className="btn btn-secondary">See example report</Link>
        </div>
      </div>
    );
  return <ReportView data={data} onReplace={setData} />;
}
