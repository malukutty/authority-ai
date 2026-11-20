"use client";

import type { Intake, StoredReport } from "./schema";

export async function requestAnalysis(intake: Intake): Promise<StoredReport> {
  const ctrl = new AbortController();
  const timer = setTimeout(() => ctrl.abort(), 280_000);
  let res: Response;
  try {
    res = await fetch("/api/repeat/analyze", {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify(intake),
      signal: ctrl.signal,
    });
  } catch (e) {
    throw new Error(
      (e as Error).name === "AbortError"
        ? "The analysis took too long. Your answers are saved — please try again."
        : "We couldn't reach the server. Check your connection and try again.",
    );
  } finally {
    clearTimeout(timer);
  }
  const data = await res.json().catch(() => null);
  if (!res.ok || !data?.report) {
    throw new Error(data?.error || "Something went wrong. Your answers are saved — please try again.");
  }
  return data as StoredReport;
}
