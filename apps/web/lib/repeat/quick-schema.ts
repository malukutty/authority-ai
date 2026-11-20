import { z } from "zod";

/* Shared by the server (analysis) and the browser (UI). No Node-only imports here. */

export const CUSTOMER_BANDS = ["0-4", "5-20", "21-50", "50+"] as const;
export type CustomerBand = (typeof CUSTOMER_BANDS)[number];
export const BAND_LABEL: Record<CustomerBand, string> = {
  "0-4": "0–4",
  "5-20": "5–20",
  "21-50": "21–50",
  "50+": "50+",
};

/**
 * Optional follow-up questions, asked one at a time after the first report.
 * `intake` maps each answer into the detailed diagnostic so nothing has to be typed twice.
 */
export const QUESTIONS = [
  {
    id: "lead_sources",
    prompt: "Where did your last three customers come from?",
    hint: "e.g. a referral from an investor, a LinkedIn post, a conference, cold email",
    intake: "motion.leadSources",
  },
  {
    id: "trigger",
    prompt: "What made your most recent customer buy when they did?",
    hint: "An event, deadline, failure, new hire, funding round…",
    intake: "wins.0.trigger",
  },
  {
    id: "why_chose",
    prompt: "Why do customers choose you over the alternative?",
    hint: "Including 'a spreadsheet' or 'doing nothing'",
    intake: "wins.0.whyChose",
  },
  {
    id: "buyers",
    prompt: "Who usually signs off on buying, and who uses the product day to day?",
    hint: "Roles, not names",
    intake: "wins.0.buyers",
  },
  {
    id: "stalls",
    prompt: "Where do deals usually stall or die?",
    hint: "",
    intake: "motion.stalls",
  },
  {
    id: "objection",
    prompt: "What's the most common objection you hear?",
    hint: "",
    intake: "wins.0.objection",
  },
  {
    id: "cycle",
    prompt: "Roughly how long does a deal take, and what does it cost the customer?",
    hint: "e.g. '4–6 weeks, about $10k a year'. Rough is fine.",
    intake: "company.salesCycle",
  },
  {
    id: "founder_only",
    prompt: "Which parts of selling only you can do today?",
    hint: "",
    intake: "motion.founderDependent",
  },
] as const;

export type QuestionId = (typeof QUESTIONS)[number]["id"];
const QUESTION_IDS = QUESTIONS.map((q) => q.id) as [QuestionId, ...QuestionId[]];

const short = (max: number) => z.string().trim().max(max).optional().default("");

export const QuickInputSchema = z
  .object({
    url: short(300),
    band: z.enum(CUSTOMER_BANDS),
    /** Used when the website can't be read. */
    manual: z.object({ sells: short(600), serves: short(600) }).optional(),
    answers: z.partialRecord(z.enum(QUESTION_IDS), z.string().trim().max(1000)).optional().default({}),
    /** Headline of the previous version, so the model can say what changed. */
    previousHeadline: short(600),
  })
  .refine((v) => v.url || (v.manual && v.manual.sells), { message: "Enter your website, or describe what you sell." });

export type QuickInput = z.infer<typeof QuickInputSchema>;

/* ── Report ── */

// website = stated on the company's own site; founder = from the founder's answers; inferred = a hypothesis.
const Basis = z.enum(["website", "founder", "inferred"]);
export type BasisT = z.infer<typeof Basis>;

const Claim = z.object({ text: z.string(), basis: Basis });

export const QuickReportSchema = z.object({
  headline: z.string().describe("One or two sentences: the most useful takeaway, framed honestly given how little is known."),
  company: z.object({
    name: z.string(),
    sells: Claim,
    serves: Claim,
    value_prop: Claim,
  }),
  icp: z.object({
    statement: z.string().describe("Draft ideal customer profile, phrased as a hypothesis to test."),
    traits: z.array(z.object({ statement: z.string(), basis: Basis, evidence: z.string() })),
  }),
  obstacles: z
    .array(
      z.object({
        title: z.string(),
        why_likely: z.string(),
        basis: Basis,
        evidence: z.string().describe("Quote or paraphrase the website or the founder's answer. 'none' if purely inferred."),
        how_to_check: z.string(),
      }),
    )
    .describe("Exactly three."),
  experiment: z.object({
    name: z.string(),
    hypothesis: z.string(),
    target: z.string(),
    steps: z.array(z.string()),
    success_metric: z.string(),
    timeframe: z.string(),
    why: z.string(),
  }),
  needed: z
    .array(
      z.object({
        question_id: z.enum([...QUESTION_IDS, "other"]),
        item: z.string(),
        why_it_matters: z.string(),
      }),
    )
    .describe("Most valuable missing information first."),
  changes: z.array(z.string()).describe("What changed from the previous version because of new answers. Empty on the first version."),
  confidence: z.object({ level: z.enum(["low", "medium", "high"]), note: z.string() }),
});

export type QuickReport = z.infer<typeof QuickReportSchema>;

/** What the browser keeps between visits (localStorage), never sent to our database unless shared with feedback. */
export type QuickSession = {
  id: string;
  url: string;
  band: CustomerBand;
  manual?: { sells: string; serves: string };
  answers: Partial<Record<QuestionId, string>>;
  skipped: QuestionId[];
  site?: { url: string; title: string; pagesRead: number };
  report: QuickReport;
  version: number;
  updatedAt: string;
  model: string;
  mock?: boolean;
};

/** Below this much readable website text, Repeat asks the founder for a one-line description instead. */
export const MIN_READABLE_CHARS = 300;
