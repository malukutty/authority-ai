"use client";

import type { Intake, StoredReport } from "./schema";
import { BAND_LABEL, QUESTIONS, type QuickSession } from "./quick-schema";

/** Founder data stays in this browser unless they choose to share it with feedback. */

const DRAFT_KEY = "repeat.draft.v1";
const REPORT_KEY = "repeat.report.v1";
const QUICK_KEY = "repeat.quick.v1";

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

// In-memory copy so the flow still works within a visit when localStorage is unavailable (private mode, blocked storage).
const memory = new Map<string, string>();

function read<T>(key: string): T | null {
  try {
    const raw = localStorage.getItem(key) ?? memory.get(key) ?? null;
    return raw ? (JSON.parse(raw) as T) : null;
  } catch {
    const raw = memory.get(key);
    return raw ? (JSON.parse(raw) as T) : null;
  }
}
function write(key: string, value: unknown) {
  const raw = JSON.stringify(value);
  memory.set(key, raw);
  try {
    localStorage.setItem(key, raw);
  } catch {
    /* storage unavailable; the in-memory copy keeps this visit working */
  }
}
function remove(key: string) {
  memory.delete(key);
  try {
    localStorage.removeItem(key);
  } catch {}
}

export const loadDraft = () => read<{ intake: Intake; step: number }>(DRAFT_KEY);
export const saveDraft = (intake: Intake, step: number) => write(DRAFT_KEY, { intake, step });
export const loadReport = () => read<StoredReport>(REPORT_KEY);
export const saveReport = (r: StoredReport) => write(REPORT_KEY, r);
export const loadQuick = () => read<QuickSession>(QUICK_KEY);
export const saveQuick = (s: QuickSession) => write(QUICK_KEY, s);

export function clearAll() {
  remove(DRAFT_KEY);
  remove(REPORT_KEY);
  remove(QUICK_KEY);
}

/** Turn what the founder told the quick flow into a starting point for the detailed diagnostic. */
export function quickToIntake(s: QuickSession): Intake {
  const intake = emptyIntake();
  intake.company.website = s.url;
  intake.company.name = s.report.company.name;
  intake.company.payingCustomers = BAND_LABEL[s.band];
  // Only carry over what the founder said themselves; website-derived text is shown as a suggestion in the report instead.
  if (s.manual?.sells) intake.company.sells = s.manual.sells;
  if (s.manual?.serves) intake.company.targetCustomer = s.manual.serves;
  for (const q of QUESTIONS) {
    const answer = s.answers[q.id]?.trim();
    if (!answer) continue;
    const [section, a, b] = q.intake.split(".");
    if (section === "wins") (intake.wins[Number(a)] as Record<string, string>)[b] = answer;
    else (intake[section as "company" | "motion"] as Record<string, string>)[a] = answer;
  }
  return intake;
}

/** Fill blank fields of `base` from `extra`, never overwriting what the founder already typed. */
export function mergeIntake(base: Intake, extra: Intake): Intake {
  const fill = <T extends Record<string, string>>(a: T, b: T): T =>
    Object.fromEntries(Object.entries(a).map(([k, v]) => [k, v?.trim() ? v : b[k] ?? ""])) as T;
  return {
    company: fill(base.company, extra.company),
    motion: fill(base.motion, extra.motion),
    wins: base.wins.map((w, i) => (extra.wins[i] ? fill(w, extra.wins[i]) : w)),
  };
}
