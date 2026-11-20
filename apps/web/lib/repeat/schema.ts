import { z } from "zod";

/* ───────────────────────── Founder input ───────────────────────── */

const text = (max = 1200) => z.string().trim().max(max).optional().default("");

export const CompanySchema = z.object({
  name: text(120),
  website: text(300),
  sells: text(),
  targetCustomer: text(),
  payingCustomers: text(40),
  dealSize: text(120),
  salesCycle: text(120),
  channels: text(),
});

export const WinSchema = z.object({
  label: text(60),
  segment: text(300),
  companySize: text(120),
  discovery: text(),
  problem: text(),
  trigger: text(),
  buyers: text(),
  objection: text(),
  whyChose: text(),
  timeToClose: text(120),
});

export const MotionSchema = z.object({
  leadSources: text(),
  qualification: text(),
  firstCallToClose: text(),
  stalls: text(),
  founderDependent: text(),
  biggestObstacle: text(),
});

export const IntakeSchema = z.object({
  company: CompanySchema,
  wins: z.array(WinSchema).max(5),
  motion: MotionSchema,
});

export type Company = z.infer<typeof CompanySchema>;
export type Win = z.infer<typeof WinSchema>;
export type Motion = z.infer<typeof MotionSchema>;
export type Intake = z.infer<typeof IntakeSchema>;

export const WIN_FIELDS: (keyof Win)[] = [
  "segment",
  "companySize",
  "discovery",
  "problem",
  "trigger",
  "buyers",
  "objection",
  "whyChose",
  "timeToClose",
];

export function filledCount(obj: Record<string, string>, keys?: string[]) {
  return (keys ?? Object.keys(obj)).filter((k) => (obj[k] ?? "").trim().length > 0).length;
}

/** A win counts as usable when at least 3 substantive fields are filled in. */
export function usableWins(intake: Intake) {
  return intake.wins.filter((w) => filledCount(w as Record<string, string>, WIN_FIELDS as string[]) >= 3);
}

export type Readiness = { ok: true } | { ok: false; reason: string };

export function checkReadiness(intake: Intake): Readiness {
  if (!intake.company.sells.trim()) {
    return { ok: false, reason: "Tell us what the company sells so the analysis has something to anchor on." };
  }
  if (usableWins(intake).length < 1) {
    return {
      ok: false,
      reason: "Describe at least one customer win with three or more details (for example the problem, the trigger, and why they chose you).",
    };
  }
  return { ok: true };
}

/* ───────────────────────── Diagnostic output ───────────────────────── */
// Kept free of length/count constraints so it works with structured outputs.

const Support = z.enum(["observed", "hypothesis"]);
const Sources = z
  .array(z.string())
  .describe('Where the evidence came from. Use only: "Win 1".."Win 5", "Company profile", "Sales motion".');

const Finding = z.object({
  statement: z.string(),
  support: Support,
  evidence: z.string().describe("Quote or paraphrase the founder's input that supports this. Say 'none' for hypotheses with no direct evidence."),
  sources: Sources,
});

export const ReportSchema = z.object({
  headline: z.string().describe("One sentence: the single most important takeaway for this founder."),
  data_quality: z.object({
    level: z.enum(["thin", "partial", "solid"]),
    note: z.string(),
  }),
  current_motion: z.object({
    summary: z.string(),
    observations: z.array(Finding),
  }),
  icp: z.object({
    statement: z.string().describe("Draft ICP in one or two sentences, phrased as a hypothesis to test."),
    traits: z.array(Finding),
    exclusions: z.array(Finding).describe("Signals that a prospect is probably NOT a fit, if the evidence suggests any."),
  }),
  triggers: z.array(Finding),
  process: z.object({
    steps: z.array(
      z.object({
        name: z.string(),
        description: z.string(),
        support: Support,
        founder_dependent: z.boolean(),
        sources: Sources,
      }),
    ),
    typical_cycle: z.string(),
  }),
  gaps: z.array(
    z.object({
      category: z.enum(["qualification", "undocumented_step", "founder_dependency", "handoff", "measurement", "other"]),
      gap: z.string(),
      consequence: z.string(),
      evidence: z.string(),
    }),
  ),
  next_ten: z.object({
    hypothesis: z.string(),
    who: z.string(),
    trigger_to_watch: z.string(),
    channel: z.string(),
    opening_angle: z.string(),
    rationale: z.string().describe("Why this follows from the evidence, citing specific wins."),
    how_to_test: z.string(),
    disconfirming_signal: z.string().describe("What result would show this hypothesis is wrong."),
  }),
  plan: z.array(
    z.object({
      week: z.number().int(),
      title: z.string(),
      owner: z.string(),
      actions: z.array(z.string()),
      success_metric: z.string(),
      rationale: z.string(),
    }),
  ),
  confidence: z.object({
    observed: z.array(z.string()),
    hypotheses: z.array(z.string()),
    missing: z.array(z.object({ item: z.string(), why_it_matters: z.string() })),
  }),
});

export type Report = z.infer<typeof ReportSchema>;
export type FindingT = z.infer<typeof Finding>;

export type StoredReport = {
  id: string;
  createdAt: string;
  model: string;
  mock?: boolean;
  example?: boolean;
  intake: Intake;
  report: Report;
};

/* ───────────────────────── Feedback ───────────────────────── */

export const FeedbackSchema = z.object({
  reportId: z.string().max(64).optional().default(""),
  useful: z.enum(["very", "somewhat", "not", ""]).optional().default(""),
  mostValuable: text(1000),
  missing: text(2000),
  useAgain: z.enum(["yes", "maybe", "no", ""]).optional().default(""),
  interview: z.boolean().optional().default(false),
  email: z
    .string()
    .trim()
    .max(254)
    .optional()
    .default("")
    .refine((v) => v === "" || /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(v), "Enter a valid email address or leave it blank."),
  consent: z.boolean().optional().default(false),
  shareInputs: z.boolean().optional().default(false),
  intake: IntakeSchema.optional(),
  example: z.boolean().optional().default(false),
  hp: z.string().max(500).optional().default(""), // honeypot: real users never fill this; route drops these silently
});

export type Feedback = z.infer<typeof FeedbackSchema>;
