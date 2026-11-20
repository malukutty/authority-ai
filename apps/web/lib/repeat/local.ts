"use client";

import type { Intake, StoredReport } from "./schema";

/** Founder data stays in this browser unless they choose to share it with feedback. */

const DRAFT_KEY = "repeat.draft.v1";
const REPORT_KEY = "repeat.report.v1";

export const emptyWin = () => ({
  label: "",
  segment: "",
  companySize: "",
  discovery: "",
  problem: "",
  trigger: "",
  buyers: "",
  objection: "",
  whyChose: "",
  timeToClose: "",
});

export const emptyIntake = (): Intake => ({
  company: { name: "", website: "", sells: "", targetCustomer: "", payingCustomers: "", dealSize: "", salesCycle: "", channels: "" },
  wins: [emptyWin(), emptyWin(), emptyWin()],
  motion: { leadSources: "", qualification: "", firstCallToClose: "", stalls: "", founderDependent: "", biggestObstacle: "" },
});

function read<T>(key: string): T | null {
  try {
    const raw = localStorage.getItem(key);
    return raw ? (JSON.parse(raw) as T) : null;
  } catch {
    return null;
  }
}
function write(key: string, value: unknown) {
  try {
    localStorage.setItem(key, JSON.stringify(value));
  } catch {
    /* storage unavailable (private mode); the flow still works for this visit */
  }
}

export const loadDraft = () => read<{ intake: Intake; step: number }>(DRAFT_KEY);
export const saveDraft = (intake: Intake, step: number) => write(DRAFT_KEY, { intake, step });
export const loadReport = () => read<StoredReport>(REPORT_KEY);
export const saveReport = (r: StoredReport) => write(REPORT_KEY, r);

export function clearAll() {
  try {
    localStorage.removeItem(DRAFT_KEY);
    localStorage.removeItem(REPORT_KEY);
  } catch {}
}
